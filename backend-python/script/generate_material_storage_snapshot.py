# -*- coding: utf-8 -*-
"""
generate_material_storage_snapshot.py

一次性生成：
  1) material_storage_snapshot
  2) material_storage_size_detail_snapshot

口径（保持与原脚本一致）：
- 边界：当日结束（< DATE_ADD(:d, INTERVAL 1 DAY)）
- 数量：未审核进出库均计入 pending_inbound/pending_outbound。
    采购入库（inbound_type = 0）审核后计入 inbound_amount
    生产出库（outbound_type = 0）审核后计入 outbound_amount
    盘库入库（inbound_type = 4）审核后进入 make_inventory_inbound
    盘库出库（outbound_type = 5）审核后计入 make_inventory_outbound
    审核后材料退回出库（outbound_type = 4）扣减 inbound_amount
    current_amount = inbound_amount - outbound_amount + make_inventory_inbound - make_inventory_outbound
- 最新单价：截至当日最后一笔【已审核=1】入库单价
- 平均价：截至当日【已审核=1】入库加权平均(总金额/总数量)
- 尺码明细：严格以实时表 material_storage_size_detail 的 (msid, order_number, id) 为准
- size_detail_id = material_storage_size_detail.id 直接沿用主键
- 规则：
    (1) 若某 material_storage 在「首次入库(不限审核状态)」至 snapshot_date 期间完全没有任何入库记录，
        则本次不向两张快照表写入该 msid。
    (2) 如果 inbound_record.inbound_datetime <= snapshot_date 且 inbound_record.approval_datetime > snapshot_date，
        则入库数量计入 pending_inbound；如果 approval_datetime <= snapshot_date 则入库数量计入 inbound_amount。
        出库同理。
- 注意：只能看 display = 1 的 inbound_record, outbound_record, inbound_record_detail, outbound_record_detail

说明：
- 本文件只做“可读性重构”，不改变原有业务/SQL 逻辑与执行顺序。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from flask import Flask
from sqlalchemy import create_engine, text


# --------------------- DB CONFIG (standalone 可改) ---------------------
DB_USER = "root"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "jiancheng"
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


# --------------------- Constants ---------------------
SNAPSHOT_TABLE = "material_storage_snapshot"
SIZE_SNAPSHOT_TABLE = "material_storage_size_detail_snapshot"

SIZES: Tuple[int, ...] = (34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46)
# order_number: 0..12 -> size 34..46 (保持与原脚本一致)
ORDER_NUMBER_TO_SIZE: Dict[int, int] = {i: s for i, s in enumerate(SIZES)}

TMP_TABLES: Tuple[str, ...] = (
    "tmp_in_approved_all",
    "tmp_in_purchase",
    "tmp_in_mkinv",
    "tmp_out_production",
    "tmp_out_mkinv",
    "tmp_out_return",
    "tmp_in_pending",
    "tmp_out_pending",
    "tmp_latest_price",
    "tmp_keys",
    "tmp_size_keys",
    "tmp_size_in_purchase",
    "tmp_size_in_mkinv",
    "tmp_size_out_prod",
    "tmp_size_out_mkinv",
    "tmp_size_out_return",
    "tmp_size_in_pend",
    "tmp_size_out_pend",
)


# --------------------- Small helpers ---------------------
def _drop_temp_tables(conn) -> None:
    for tmp in TMP_TABLES:
        conn.execute(text(f"DROP TEMPORARY TABLE IF EXISTS {tmp}"))


def _exec(conn, sql: str, params: dict | None = None) -> None:
    conn.execute(text(sql), params or {})


def _build_size_sum_case(
    *,
    table_alias: str,
    column_prefix: str,
    column_suffix: str,
    order_number_alias: str = "t.order_number",
) -> str:
    """
    生成类似：
        SUM(
          CASE t.order_number
            WHEN 0 THEN COALESCE(ird.size_34_inbound_amount,0)
            ...
          END
        ) AS xxx
    逻辑不变，只把重复的 CASE 写法用代码生成，避免 7 段 SQL 手工重复。
    """
    lines: List[str] = []
    lines.append("SUM(")
    lines.append(f"  CASE {order_number_alias}")
    for order_number, size_value in ORDER_NUMBER_TO_SIZE.items():
        col = f"{table_alias}.{column_prefix}{size_value}{column_suffix}"
        lines.append(f"    WHEN {order_number} THEN COALESCE({col},0)")
    lines.append("  END")
    lines.append(")")
    return "\n".join(lines)


@dataclass(frozen=True)
class SnapshotArgs:
    snapshot_date: str
    upsert: bool = True
    cleanup_removed: bool = True


# --------------------- SQL blocks (总表) ---------------------
# 最新单价临时表
SQL_CREATE_TMP_LATEST_PRICE = """
    CREATE TEMPORARY TABLE tmp_latest_price AS
    WITH ranked AS (
    SELECT
        ird.material_storage_id,
        ird.unit_price,
        ROW_NUMBER() OVER (
        PARTITION BY ird.material_storage_id
        ORDER BY ir.approval_datetime DESC, ird.id DESC
        ) rn
    FROM inbound_record_detail ird
    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
    WHERE ir.approval_status = 1
        AND ir.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
        AND ir.display = 1
    )
    SELECT material_storage_id, unit_price AS latest_unit_price
    FROM ranked WHERE rn = 1;
    """

# 入库总量与总金额临时表，用于计算加权平均价
SQL_CREATE_TMP_IN_APPROVED_ALL = """
    CREATE TEMPORARY TABLE tmp_in_approved_all AS
    SELECT
    ird.material_storage_id,
    SUM(ird.inbound_amount) AS total_inbound,
    SUM(ird.inbound_amount * ird.unit_price) AS total_inbound_value
    FROM inbound_record_detail ird
    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
    WHERE ir.approval_status = 1
    AND ir.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND ir.display = 1
    GROUP BY ird.material_storage_id;
    """

# 采购入库临时表
SQL_CREATE_TMP_IN_PURCHASE = """
    CREATE TEMPORARY TABLE tmp_in_purchase AS
    SELECT
    ird.material_storage_id,
    SUM(ird.inbound_amount) AS purchase_inbound
    FROM inbound_record_detail ird
    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
    WHERE ir.approval_status = 1
    AND ir.inbound_type = 0
    AND ir.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND ir.display = 1
    GROUP BY ird.material_storage_id;
    """

# 盘库入库临时表
SQL_CREATE_TMP_IN_MKINV = """
    CREATE TEMPORARY TABLE tmp_in_mkinv AS
    SELECT
    ird.material_storage_id,
    SUM(ird.inbound_amount) AS make_inventory_inbound
    FROM inbound_record_detail ird
    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
    WHERE ir.approval_status = 1
    AND ir.inbound_type = 4
    AND ir.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND ir.display = 1
    GROUP BY ird.material_storage_id;
    """

# 生产出库临时表
SQL_CREATE_TMP_OUT_PRODUCTION = """
    CREATE TEMPORARY TABLE tmp_out_production AS
    SELECT
    ord.material_storage_id,
    SUM(ord.outbound_amount) AS production_outbound
    FROM outbound_record_detail ord
    JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
    WHERE o.approval_status = 1
    AND o.outbound_type = 0
    AND o.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND o.display = 1
    GROUP BY ord.material_storage_id;
    """

# 盘库出库临时表
SQL_CREATE_TMP_OUT_MKINV = """
    CREATE TEMPORARY TABLE tmp_out_mkinv AS
    SELECT
    ord.material_storage_id,
    SUM(ord.outbound_amount) AS make_inventory_outbound
    FROM outbound_record_detail ord
    JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
    WHERE o.approval_status = 1
    AND o.outbound_type = 5
    AND o.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND o.display = 1
    GROUP BY ord.material_storage_id;
    """

# 材料退回出库临时表
SQL_CREATE_TMP_OUT_RETURN = """
    CREATE TEMPORARY TABLE tmp_out_return AS
    SELECT
    ord.material_storage_id,
    SUM(ord.outbound_amount) AS return_outbound
    FROM outbound_record_detail ord
    JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
    WHERE o.approval_status = 1
    AND o.outbound_type = 4
    AND o.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND o.display = 1
    GROUP BY ord.material_storage_id;
    """

# 待审核入库临时表
SQL_CREATE_TMP_IN_PENDING = """
    CREATE TEMPORARY TABLE tmp_in_pending AS
    SELECT
    ird.material_storage_id,
    SUM(ird.inbound_amount) AS pending_inbound
    FROM inbound_record_detail ird
    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
    WHERE ird.inbound_amount IS NOT NULL
    AND ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND (
        ir.approval_status IN (0, 2)
        OR ir.approval_status IS NULL
        OR (ir.approval_status = 1 AND ir.approval_datetime >= DATE_ADD(:d, INTERVAL 1 DAY))
    )
    AND ir.display = 1
    GROUP BY ird.material_storage_id;
    """

# 待审核出库临时表
SQL_CREATE_TMP_OUT_PENDING = """
    CREATE TEMPORARY TABLE tmp_out_pending AS
    SELECT
    ord.material_storage_id,
    SUM(ord.outbound_amount) AS pending_outbound
    FROM outbound_record_detail ord
    JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
    WHERE ord.outbound_amount IS NOT NULL
    AND o.outbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND (
            o.approval_status IN (0, 2)
            OR o.approval_status IS NULL
            OR (o.approval_status = 1 AND o.approval_datetime >= DATE_ADD(:d, INTERVAL 1 DAY))
    )
    AND o.display = 1
    GROUP BY ord.material_storage_id;
    """

# 物料 key 集（仅限「截至当日曾经有过任意入库记录」的 material_storage）
SQL_CREATE_TMP_KEYS = """
    CREATE TEMPORARY TABLE tmp_keys AS
    SELECT DISTINCT ird.material_storage_id
    FROM inbound_record_detail ird
    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
    WHERE ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
    AND ir.display = 1;
    """

# upsert 主表 snapshot
SQL_UPSERT_SNAPSHOT = """
    INSERT INTO material_storage_snapshot (
        snapshot_date,
        material_storage_id,
        order_id,
        order_shoe_id,
        spu_material_id,
        actual_inbound_unit,
        pending_inbound,
        pending_outbound,
        inbound_amount,
        outbound_amount,
        make_inventory_inbound,
        make_inventory_outbound,
        current_amount,
        unit_price,
        average_price,
        material_outsource_status,
        material_outsource_date,
        purchase_order_item_id,
        material_storage_status,
        shoe_size_columns
    )
    SELECT
        :d AS snapshot_date,
        ms.material_storage_id,
        ms.order_id,
        ms.order_shoe_id,
        ms.spu_material_id,
        COALESCE(ms.actual_inbound_unit, 'PCS') AS actual_inbound_unit,
        COALESCE(pin.pending_inbound, 0) AS pending_inbound,
        COALESCE(pout.pending_outbound, 0) AS pending_outbound,
        COALESCE(pur.purchase_inbound, 0) - COALESCE(ret.return_outbound, 0) AS inbound_amount,
        COALESCE(prod.production_outbound, 0) AS outbound_amount,
        COALESCE(miin.make_inventory_inbound, 0) AS make_inventory_inbound,
        COALESCE(miout.make_inventory_outbound, 0) AS make_inventory_outbound,
        (COALESCE(pur.purchase_inbound, 0) - COALESCE(ret.return_outbound, 0))
            - COALESCE(prod.production_outbound, 0)
            + COALESCE(miin.make_inventory_inbound, 0)
            - COALESCE(miout.make_inventory_outbound, 0) AS current_amount,
        COALESCE(lp.latest_unit_price, 0) AS unit_price,
        CASE
        WHEN COALESCE(ia.total_inbound, 0) > 0
        THEN COALESCE(ia.total_inbound_value, 0) / ia.total_inbound
        ELSE 0
        END AS average_price,
        ms.material_outsource_status,
        ms.material_outsource_date,
        ms.purchase_order_item_id,
        ms.material_storage_status,
        ms.shoe_size_columns
    FROM tmp_keys k
    JOIN material_storage ms
    ON ms.material_storage_id = k.material_storage_id
    LEFT JOIN tmp_in_approved_all ia
    ON ia.material_storage_id = ms.material_storage_id
    LEFT JOIN tmp_latest_price lp
    ON lp.material_storage_id = ms.material_storage_id
    LEFT JOIN tmp_in_pending pin
    ON pin.material_storage_id = ms.material_storage_id
    LEFT JOIN tmp_out_pending pout
    ON pout.material_storage_id = ms.material_storage_id
    LEFT JOIN tmp_in_purchase pur
    ON pur.material_storage_id = ms.material_storage_id
    LEFT JOIN tmp_out_return ret
    ON ret.material_storage_id = ms.material_storage_id
    LEFT JOIN tmp_in_mkinv miin
    ON miin.material_storage_id = ms.material_storage_id
    LEFT JOIN tmp_out_production prod
    ON prod.material_storage_id = ms.material_storage_id
    LEFT JOIN tmp_out_mkinv miout
    ON miout.material_storage_id = ms.material_storage_id
    ON DUPLICATE KEY UPDATE
        order_id = VALUES(order_id),
        order_shoe_id = VALUES(order_shoe_id),
        spu_material_id = VALUES(spu_material_id),
        actual_inbound_unit = VALUES(actual_inbound_unit),
        pending_inbound = VALUES(pending_inbound),
        pending_outbound = VALUES(pending_outbound),
        inbound_amount = VALUES(inbound_amount),
        outbound_amount = VALUES(outbound_amount),
        make_inventory_inbound = VALUES(make_inventory_inbound),
        make_inventory_outbound = VALUES(make_inventory_outbound),
        current_amount = VALUES(current_amount),
        unit_price = VALUES(unit_price),
        average_price = VALUES(average_price),
        material_outsource_status = VALUES(material_outsource_status),
        material_outsource_date = VALUES(material_outsource_date),
        purchase_order_item_id = VALUES(purchase_order_item_id),
        material_storage_status = VALUES(material_storage_status),
        shoe_size_columns = VALUES(shoe_size_columns),
        update_time = CURRENT_TIMESTAMP;
    """

# 删除已移除物料的 snapshot 记录
SQL_DELETE_SNAPSHOT_REMOVED = """
    DELETE FROM material_storage_snapshot
    WHERE snapshot_date = :d
    AND material_storage_id NOT IN (SELECT material_storage_id FROM tmp_keys);
    """


# --------------------- SQL blocks (尺码明细) ---------------------
SQL_CREATE_TMP_SIZE_KEYS = """
    CREATE TEMPORARY TABLE tmp_size_keys AS
    SELECT
    msd.id               AS size_detail_id,
    msd.material_storage_id,
    msd.order_number,
    msd.size_value
    FROM material_storage_size_detail msd
    JOIN tmp_keys k ON k.material_storage_id = msd.material_storage_id;
    """


def _sql_create_tmp_size_in_purchase() -> str:
    sum_case = _build_size_sum_case(
        table_alias="ird",
        column_prefix="size_",
        column_suffix="_inbound_amount",
        order_number_alias="t.order_number",
    )
    return f"""
        CREATE TEMPORARY TABLE tmp_size_in_purchase AS
        SELECT
        t.material_storage_id,
        t.order_number,
        {sum_case} AS inbound_amount_n
        FROM inbound_record_detail ird
        JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        JOIN tmp_size_keys t ON t.material_storage_id = ird.material_storage_id
        WHERE ir.approval_status = 1
        AND ir.inbound_type = 0
        AND ir.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
        AND ir.display = 1
        GROUP BY t.material_storage_id, t.order_number;
        """.strip()


def _sql_create_tmp_size_in_mkinv() -> str:
    sum_case = _build_size_sum_case(
        table_alias="ird",
        column_prefix="size_",
        column_suffix="_inbound_amount",
        order_number_alias="t.order_number",
    )
    return f"""
        CREATE TEMPORARY TABLE tmp_size_in_mkinv AS
        SELECT
        t.material_storage_id,
        t.order_number,
        {sum_case} AS inbound_amount_n
        FROM inbound_record_detail ird
        JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        JOIN tmp_size_keys t ON t.material_storage_id = ird.material_storage_id
        WHERE ir.approval_status = 1
        AND ir.inbound_type = 4
        AND ir.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
        AND ir.display = 1
        GROUP BY t.material_storage_id, t.order_number;
        """.strip()


def _sql_create_tmp_size_out_prod() -> str:
    sum_case = _build_size_sum_case(
        table_alias="ord",
        column_prefix="size_",
        column_suffix="_outbound_amount",
        order_number_alias="t.order_number",
    )
    return f"""
        CREATE TEMPORARY TABLE tmp_size_out_prod AS
        SELECT
        t.material_storage_id,
        t.order_number,
        {sum_case} AS outbound_amount_n
        FROM outbound_record_detail ord
        JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
        JOIN tmp_size_keys t ON t.material_storage_id = ord.material_storage_id
        WHERE o.approval_status = 1
        AND o.outbound_type = 0
        AND o.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
        AND o.display = 1
        GROUP BY t.material_storage_id, t.order_number;
        """.strip()


def _sql_create_tmp_size_out_mkinv() -> str:
    sum_case = _build_size_sum_case(
        table_alias="ord",
        column_prefix="size_",
        column_suffix="_outbound_amount",
        order_number_alias="t.order_number",
    )
    return f"""
        CREATE TEMPORARY TABLE tmp_size_out_mkinv AS
        SELECT
        t.material_storage_id,
        t.order_number,
        {sum_case} AS outbound_amount_n
        FROM outbound_record_detail ord
        JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
        JOIN tmp_size_keys t ON t.material_storage_id = ord.material_storage_id
        WHERE o.approval_status = 1
        AND o.outbound_type = 5
        AND o.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
        AND o.display = 1
        GROUP BY t.material_storage_id, t.order_number;
        """.strip()


def _sql_create_tmp_size_out_return() -> str:
    sum_case = _build_size_sum_case(
        table_alias="ord",
        column_prefix="size_",
        column_suffix="_outbound_amount",
        order_number_alias="t.order_number",
    )
    return f"""
        CREATE TEMPORARY TABLE tmp_size_out_return AS
        SELECT
        t.material_storage_id,
        t.order_number,
        {sum_case} AS return_outbound_n
        FROM outbound_record_detail ord
        JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
        JOIN tmp_size_keys t ON t.material_storage_id = ord.material_storage_id
        WHERE o.approval_status = 1
        AND o.outbound_type = 4
        AND o.approval_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
        AND o.display = 1
        GROUP BY t.material_storage_id, t.order_number;
        """.strip()


def _sql_create_tmp_size_in_pend() -> str:
    sum_case = _build_size_sum_case(
        table_alias="ird",
        column_prefix="size_",
        column_suffix="_inbound_amount",
        order_number_alias="t.order_number",
    )
    return f"""
        CREATE TEMPORARY TABLE tmp_size_in_pend AS
        SELECT
        t.material_storage_id,
        t.order_number,
        {sum_case} AS pending_inbound_n
        FROM inbound_record_detail ird
        JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        JOIN tmp_size_keys t ON t.material_storage_id = ird.material_storage_id
        WHERE ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
        AND (
                ir.approval_status IN (0, 2)
                OR ir.approval_status IS NULL
                OR (ir.approval_status = 1 AND ir.approval_datetime >= DATE_ADD(:d, INTERVAL 1 DAY))
        )
        AND ir.display = 1
        GROUP BY t.material_storage_id, t.order_number;
        """.strip()


def _sql_create_tmp_size_out_pend() -> str:
    sum_case = _build_size_sum_case(
        table_alias="ord",
        column_prefix="size_",
        column_suffix="_outbound_amount",
        order_number_alias="t.order_number",
    )
    return f"""
        CREATE TEMPORARY TABLE tmp_size_out_pend AS
        SELECT
        t.material_storage_id,
        t.order_number,
        {sum_case} AS pending_outbound_n
        FROM outbound_record_detail ord
        JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
        JOIN tmp_size_keys t ON t.material_storage_id = ord.material_storage_id
        WHERE o.outbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
        AND (
                o.approval_status IN (0, 2)
                OR o.approval_status IS NULL
                OR (o.approval_status = 1 AND o.approval_datetime >= DATE_ADD(:d, INTERVAL 1 DAY))
        )
        AND o.display = 1
        GROUP BY t.material_storage_id, t.order_number;
        """.strip()


SQL_UPSERT_SIZE_SNAPSHOT = """
    INSERT INTO material_storage_size_detail_snapshot (
        snapshot_date,
        size_detail_id,
        material_storage_id,
        size_value,
        order_number,
        pending_inbound,
        pending_outbound,
        inbound_amount,
        outbound_amount,
        make_inventory_inbound,
        make_inventory_outbound,
        current_amount
    )
    SELECT
        :d AS snapshot_date,
        t.size_detail_id,
        t.material_storage_id,
        t.size_value,
        t.order_number,
        COALESCE(pi.pending_inbound_n, 0) AS pending_inbound,
        COALESCE(po.pending_outbound_n, 0) AS pending_outbound,
        COALESCE(ip.inbound_amount_n, 0) - COALESCE(rt.return_outbound_n, 0) AS inbound_amount,
        COALESCE(op.outbound_amount_n, 0) AS outbound_amount,
        COALESCE(imki.inbound_amount_n, 0) AS make_inventory_inbound,
        COALESCE(omki.outbound_amount_n, 0) AS make_inventory_outbound,
        (COALESCE(ip.inbound_amount_n, 0) - COALESCE(rt.return_outbound_n, 0))
            - COALESCE(op.outbound_amount_n, 0)
            + COALESCE(imki.inbound_amount_n, 0)
            - COALESCE(omki.outbound_amount_n, 0) AS current_amount
    FROM tmp_size_keys t
    LEFT JOIN tmp_size_in_purchase ip
    ON ip.material_storage_id = t.material_storage_id AND ip.order_number = t.order_number
    LEFT JOIN tmp_size_out_return rt
    ON rt.material_storage_id = t.material_storage_id AND rt.order_number = t.order_number
    LEFT JOIN tmp_size_in_mkinv imki
    ON imki.material_storage_id = t.material_storage_id AND imki.order_number = t.order_number
    LEFT JOIN tmp_size_out_prod op
    ON op.material_storage_id = t.material_storage_id AND op.order_number = t.order_number
    LEFT JOIN tmp_size_out_mkinv omki
    ON omki.material_storage_id = t.material_storage_id AND omki.order_number = t.order_number
    LEFT JOIN tmp_size_in_pend pi
    ON pi.material_storage_id = t.material_storage_id AND pi.order_number = t.order_number
    LEFT JOIN tmp_size_out_pend po
    ON po.material_storage_id = t.material_storage_id AND po.order_number = t.order_number
    ON DUPLICATE KEY UPDATE
        material_storage_id = VALUES(material_storage_id),
        size_value = VALUES(size_value),
        order_number = VALUES(order_number),
        pending_inbound = VALUES(pending_inbound),
        pending_outbound = VALUES(pending_outbound),
        inbound_amount = VALUES(inbound_amount),
        outbound_amount = VALUES(outbound_amount),
        make_inventory_inbound = VALUES(make_inventory_inbound),
        make_inventory_outbound = VALUES(make_inventory_outbound),
        current_amount = VALUES(current_amount),
        update_time = CURRENT_TIMESTAMP;
    """


SQL_DELETE_SIZE_SNAPSHOT_REMOVED = """
    DELETE FROM material_storage_size_detail_snapshot
    WHERE snapshot_date = :d
    AND size_detail_id NOT IN (SELECT size_detail_id FROM tmp_size_keys);
    """


# --------------------- Public entry ---------------------
def generate_material_storage_snapshot(
    app, db, snapshot_date: str, *, upsert: bool = True, cleanup_removed: bool = True
):
    """
    生成指定 snapshot_date (YYYY-MM-DD) 的两张月末快照。
    支持重复执行（upsert / 先删后插）。
    """
    args = SnapshotArgs(
        snapshot_date=snapshot_date, upsert=upsert, cleanup_removed=cleanup_removed
    )

    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            print(
                f"🧮 Building month-end snapshots for {args.snapshot_date} (end-of-day bound)."
            )

            # 1) 清理当日旧数据（仅在非 upsert 模式）
            if not args.upsert:
                _exec(
                    conn,
                    f"DELETE FROM {SIZE_SNAPSHOT_TABLE} WHERE snapshot_date = :d;",
                    {"d": args.snapshot_date},
                )
                _exec(
                    conn,
                    f"DELETE FROM {SNAPSHOT_TABLE} WHERE snapshot_date = :d;",
                    {"d": args.snapshot_date},
                )

            # 2) 丢弃残留临表
            _drop_temp_tables(conn)

            # ----------------- 总表临表构建 -----------------
            _exec(conn, SQL_CREATE_TMP_LATEST_PRICE, {"d": args.snapshot_date})
            _exec(conn, SQL_CREATE_TMP_IN_APPROVED_ALL, {"d": args.snapshot_date})
            _exec(conn, SQL_CREATE_TMP_IN_PURCHASE, {"d": args.snapshot_date})
            _exec(conn, SQL_CREATE_TMP_IN_MKINV, {"d": args.snapshot_date})
            _exec(conn, SQL_CREATE_TMP_OUT_PRODUCTION, {"d": args.snapshot_date})
            _exec(conn, SQL_CREATE_TMP_OUT_MKINV, {"d": args.snapshot_date})
            _exec(conn, SQL_CREATE_TMP_OUT_RETURN, {"d": args.snapshot_date})
            _exec(conn, SQL_CREATE_TMP_IN_PENDING, {"d": args.snapshot_date})
            _exec(conn, SQL_CREATE_TMP_OUT_PENDING, {"d": args.snapshot_date})

            # 物料 key 集（仅限「截至当日曾经有过任意入库记录」的 material_storage）
            _exec(conn, SQL_CREATE_TMP_KEYS, {"d": args.snapshot_date})

            # 写入 material_storage_snapshot
            _exec(conn, SQL_UPSERT_SNAPSHOT, {"d": args.snapshot_date})

            # upsert 时：精准删除 “本次不该存在的行”
            if args.upsert and args.cleanup_removed:
                _exec(conn, SQL_DELETE_SNAPSHOT_REMOVED, {"d": args.snapshot_date})

            # ----------------- 尺码维度临表构建 -----------------
            _exec(conn, SQL_CREATE_TMP_SIZE_KEYS)

            _exec(conn, _sql_create_tmp_size_in_purchase(), {"d": args.snapshot_date})
            _exec(conn, _sql_create_tmp_size_in_mkinv(), {"d": args.snapshot_date})
            _exec(conn, _sql_create_tmp_size_out_prod(), {"d": args.snapshot_date})
            _exec(conn, _sql_create_tmp_size_out_mkinv(), {"d": args.snapshot_date})
            _exec(conn, _sql_create_tmp_size_out_return(), {"d": args.snapshot_date})
            _exec(conn, _sql_create_tmp_size_in_pend(), {"d": args.snapshot_date})
            _exec(conn, _sql_create_tmp_size_out_pend(), {"d": args.snapshot_date})

            # 写入 material_storage_size_detail_snapshot
            _exec(conn, SQL_UPSERT_SIZE_SNAPSHOT, {"d": args.snapshot_date})

            # upsert 时：精准删除 “本次不该存在的行”
            if args.upsert and args.cleanup_removed:
                _exec(conn, SQL_DELETE_SIZE_SNAPSHOT_REMOVED, {"d": args.snapshot_date})

            trans.commit()
            print(f"✅ snapshots done for {args.snapshot_date}.")

        except Exception as e:
            trans.rollback()
            print("❌ Error while generating snapshots:", e)
            raise
        finally:
            conn.close()


# ------------------------- Standalone 执行辅助 -------------------------
if __name__ == "__main__":
    print(f"Using DB_URL: {DB_URL}")
    app = Flask(__name__)

    class DBWrapper:
        def __init__(self, engine):
            self.engine = engine

    engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=3600)
    db = DBWrapper(engine)

    for date in [
        "2025-11-30",
    ]:
        generate_material_storage_snapshot(
            app, db, date, upsert=True, cleanup_removed=True
        )

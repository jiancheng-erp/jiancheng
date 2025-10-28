
# -*- coding: utf-8 -*-
"""
generate_daily_change_standalone.py
-----------------------------------
直接可运行：连接 MySQL，生成每日净变动（父表）+ 尺码明细（子表）。

审批口径：
  - 待审核（含被驳回）：approval_status IN (0, 2)
  - 已审核：approval_status = 1
单价口径：
  - latest_unit_price：截止当日最后一次入库单价（不区分审批）
  - avg_unit_price：截止当日仅统计已审核入库的累计金额/累计数量

用法：
  python generate_daily_change_standalone.py --start 2025-03-17 --end 2025-10-10
  （如果不传参，默认跑“昨天”）
"""
import sys
import argparse
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, text

# ====== 数据库连接参数（按你的要求写死在脚本里） ======
DB_USER = "root"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "jiancheng"
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 daily_material_storage_change / daily_material_storage_size_detail_change")
    parser.add_argument("--start", type=str, help="开始日期 YYYY-MM-DD，默认=昨天")
    parser.add_argument("--end", type=str, help="结束日期 YYYY-MM-DD，默认=昨天")
    ns = parser.parse_args()
    if not ns.start or not ns.end:
        y = date.today() - timedelta(days=1)
        default_str = y.strftime("%Y-%m-%d")
        ns.start = ns.start or default_str
        ns.end = ns.end or default_str
    # 校验格式
    try:
        datetime.strptime(ns.start, "%Y-%m-%d")
        datetime.strptime(ns.end, "%Y-%m-%d")
    except ValueError as e:
        print(f"[参数错误] 日期格式应为 YYYY-MM-DD: {e}")
        sys.exit(2)
    return ns


def run_once_for_day(conn, the_day: date):
    now_date = the_day
    deadline = the_day + timedelta(days=1)

    upsert_parent_sql = text("""
INSERT INTO daily_material_storage_change (
    snapshot_date, material_storage_id,
    latest_unit_price, avg_unit_price,
    pending_inbound_sum, pending_outbound_sum,
    inbound_amount_sum, outbound_amount_sum,
    net_change
)
SELECT
    agg.snapshot_date,
    agg.material_storage_id,
    COALESCE(lp.unit_price, 0) AS latest_unit_price,
    COALESCE(ap.avg_unit_price, 0) AS avg_unit_price,
    COALESCE(agg.pending_inbound_sum, 0)  AS pending_inbound_sum,
    COALESCE(agg.pending_outbound_sum, 0) AS pending_outbound_sum,
    COALESCE(agg.inbound_amount_sum, 0)   AS inbound_amount_sum,
    COALESCE(agg.outbound_amount_sum, 0)  AS outbound_amount_sum,
    COALESCE(agg.inbound_amount_sum, 0) - COALESCE(agg.outbound_amount_sum, 0) AS net_change
FROM (
    /* ===== 当日四项汇总（pending/approved 的 in/out） ===== */
    SELECT
        t.snapshot_date,
        t.material_storage_id,
        SUM(t.pending_inbound_sum)  AS pending_inbound_sum,
        SUM(t.pending_outbound_sum) AS pending_outbound_sum,
        SUM(t.inbound_amount_sum)   AS inbound_amount_sum,
        SUM(t.outbound_amount_sum)  AS outbound_amount_sum
    FROM (
        /* 当日未审核入库（包含被驳回） */
        SELECT
            DATE(ir.inbound_datetime) AS snapshot_date,
            ird.material_storage_id   AS material_storage_id,
            SUM(COALESCE(ird.inbound_amount,0)) AS pending_inbound_sum,
            0 AS pending_outbound_sum,
            0 AS inbound_amount_sum,
            0 AS outbound_amount_sum
        FROM inbound_record_detail ird
        JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date
          AND ir.inbound_datetime <  :deadline
          AND ir.approval_status     IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id

        UNION ALL

        /* 当日已审核入库 */
        SELECT
            DATE(ir.inbound_datetime) AS snapshot_date,
            ird.material_storage_id   AS material_storage_id,
            0 AS pending_inbound_sum,
            0 AS pending_outbound_sum,
            SUM(COALESCE(ird.inbound_amount,0)) AS inbound_amount_sum,
            0 AS outbound_amount_sum
        FROM inbound_record_detail ird
        JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date
          AND ir.inbound_datetime <  :deadline
          AND ir.approval_status     = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id

        UNION ALL

        /* 当日未审核出库（包含被驳回） */
        SELECT
            DATE(orh.outbound_datetime) AS snapshot_date,
            ord.material_storage_id     AS material_storage_id,
            0 AS pending_inbound_sum,
            SUM(COALESCE(ord.outbound_amount,0)) AS pending_outbound_sum,
            0 AS inbound_amount_sum,
            0 AS outbound_amount_sum
        FROM outbound_record_detail ord
        JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date
          AND orh.outbound_datetime <  :deadline
          AND orh.approval_status      IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id

        UNION ALL

        /* 当日已审核出库 */
        SELECT
            DATE(orh.outbound_datetime) AS snapshot_date,
            ord.material_storage_id     AS material_storage_id,
            0 AS pending_inbound_sum,
            0 AS pending_outbound_sum,
            0 AS inbound_amount_sum,
            SUM(COALESCE(ord.outbound_amount,0)) AS outbound_amount_sum
        FROM outbound_record_detail ord
        JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date
          AND orh.outbound_datetime <  :deadline
          AND orh.approval_status      = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
    ) t
    GROUP BY t.snapshot_date, t.material_storage_id
) agg
/* ===== 截止当日（含历史）的“最新单价”（最后一条入库） ===== */
LEFT JOIN (
    SELECT
        ird.material_storage_id AS material_storage_id,
        ird.unit_price
    FROM inbound_record_detail ird
    JOIN inbound_record ir
      ON ir.inbound_record_id = ird.inbound_record_id
    JOIN (
        SELECT
            ird2.material_storage_id AS msid,
            MAX(CONCAT(DATE_FORMAT(ir2.inbound_datetime, '%Y%m%d%H%i%S'),
                       LPAD(ird2.id, 12, '0'))) AS max_key
        FROM inbound_record_detail ird2
        JOIN inbound_record ir2
          ON ir2.inbound_record_id = ird2.inbound_record_id
        WHERE ir2.inbound_datetime < :deadline
        GROUP BY ird2.material_storage_id
    ) last_k
      ON last_k.msid = ird.material_storage_id
     AND CONCAT(DATE_FORMAT(ir.inbound_datetime, '%Y%m%d%H%i%S'),
                LPAD(ird.id, 12, '0')) = last_k.max_key
) lp
  ON lp.material_storage_id = agg.material_storage_id
/* ===== 截止当日的“加权平均价”（仅审批=1） ===== */
LEFT JOIN (
    SELECT
        ird.material_storage_id AS material_storage_id,
        SUM(ird.inbound_amount * ird.unit_price) / NULLIF(SUM(ird.inbound_amount), 0) AS avg_unit_price
    FROM inbound_record_detail ird
    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
    WHERE ir.inbound_datetime < :deadline
      AND ir.approval_status   = 1
    GROUP BY ird.material_storage_id
) ap
  ON ap.material_storage_id = agg.material_storage_id

ON DUPLICATE KEY UPDATE
    latest_unit_price      = VALUES(latest_unit_price),
    avg_unit_price         = VALUES(avg_unit_price),
    pending_inbound_sum    = VALUES(pending_inbound_sum),
    pending_outbound_sum   = VALUES(pending_outbound_sum),
    inbound_amount_sum     = VALUES(inbound_amount_sum),
    outbound_amount_sum    = VALUES(outbound_amount_sum),
    net_change             = VALUES(net_change),
    update_time            = CURRENT_TIMESTAMP
;
    """)

    conn.execute(upsert_parent_sql, {"now_date": now_date, "deadline": deadline})

    upsert_detail_sql = text("""
INSERT INTO daily_material_storage_size_detail_change (
    daily_change_id, size_value, order_number,
    pending_inbound_sum, pending_outbound_sum,
    inbound_amount_sum, outbound_amount_sum
)
SELECT
    dmsc.daily_change_id,
    msd.size_value,
    msd.order_number,
    COALESCE(pi.sum_amount, 0) AS pending_inbound_sum,
    COALESCE(po.sum_amount, 0) AS pending_outbound_sum,
    COALESCE(ai.sum_amount, 0) AS inbound_amount_sum,
    COALESCE(ao.sum_amount, 0) AS outbound_amount_sum
FROM daily_material_storage_change dmsc
JOIN material_storage_size_detail msd
  ON msd.material_storage_id = dmsc.material_storage_id
LEFT JOIN (
    /* 当日未审核入库尺码汇总（包含被驳回） */
    SELECT snapshot_date, material_storage_id, order_number, SUM(amount) AS sum_amount
    FROM (
        SELECT DATE(ir.inbound_datetime) AS snapshot_date, ird.material_storage_id, 0 AS order_number, SUM(COALESCE(ird.size_34_inbound_amount,0)) AS amount
        FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 1, SUM(COALESCE(ird.size_35_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 2, SUM(COALESCE(ird.size_36_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 3, SUM(COALESCE(ird.size_37_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 4, SUM(COALESCE(ird.size_38_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 5, SUM(COALESCE(ird.size_39_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 6, SUM(COALESCE(ird.size_40_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 7, SUM(COALESCE(ird.size_41_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 8, SUM(COALESCE(ird.size_42_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 9, SUM(COALESCE(ird.size_43_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 10, SUM(COALESCE(ird.size_44_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 11, SUM(COALESCE(ird.size_45_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 12, SUM(COALESCE(ird.size_46_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status IN (0,2)
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
    ) z
    GROUP BY snapshot_date, material_storage_id, order_number
) pi
  ON pi.snapshot_date = dmsc.snapshot_date
 AND pi.material_storage_id = dmsc.material_storage_id
 AND pi.order_number = msd.order_number

LEFT JOIN (
    /* 当日已审核入库尺码汇总 */
    SELECT snapshot_date, material_storage_id, order_number, SUM(amount) AS sum_amount
    FROM (
        SELECT DATE(ir.inbound_datetime) AS snapshot_date, ird.material_storage_id, 0 AS order_number, SUM(COALESCE(ird.size_34_inbound_amount,0)) AS amount
        FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 1, SUM(COALESCE(ird.size_35_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 2, SUM(COALESCE(ird.size_36_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 3, SUM(COALESCE(ird.size_37_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 4, SUM(COALESCE(ird.size_38_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 5, SUM(COALESCE(ird.size_39_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 6, SUM(COALESCE(ird.size_40_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 7, SUM(COALESCE(ird.size_41_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 8, SUM(COALESCE(ird.size_42_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 9, SUM(COALESCE(ird.size_43_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 10, SUM(COALESCE(ird.size_44_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 11, SUM(COALESCE(ird.size_45_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
        UNION ALL
        SELECT DATE(ir.inbound_datetime), ird.material_storage_id, 12, SUM(COALESCE(ird.size_46_inbound_amount,0)) FROM inbound_record_detail ird JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date AND ir.inbound_datetime < :deadline AND ir.approval_status = 1
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
    ) z
    GROUP BY snapshot_date, material_storage_id, order_number
) ai
  ON ai.snapshot_date = dmsc.snapshot_date
 AND ai.material_storage_id = dmsc.material_storage_id
 AND ai.order_number = msd.order_number

LEFT JOIN (
    /* 当日未审核出库尺码汇总（包含被驳回） */
    SELECT snapshot_date, material_storage_id, order_number, SUM(amount) AS sum_amount
    FROM (
        SELECT DATE(orh.outbound_datetime) AS snapshot_date, ord.material_storage_id, 0 AS order_number, SUM(COALESCE(ord.size_34_outbound_amount,0)) AS amount
        FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 1, SUM(COALESCE(ord.size_35_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 2, SUM(COALESCE(ord.size_36_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 3, SUM(COALESCE(ord.size_37_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 4, SUM(COALESCE(ord.size_38_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 5, SUM(COALESCE(ord.size_39_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 6, SUM(COALESCE(ord.size_40_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 7, SUM(COALESCE(ord.size_41_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 8, SUM(COALESCE(ord.size_42_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 9, SUM(COALESCE(ord.size_43_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 10, SUM(COALESCE(ord.size_44_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 11, SUM(COALESCE(ord.size_45_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 12, SUM(COALESCE(ord.size_46_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status IN (0,2)
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
    ) z
    GROUP BY snapshot_date, material_storage_id, order_number
) po
  ON po.snapshot_date = dmsc.snapshot_date
 AND po.material_storage_id = dmsc.material_storage_id
 AND po.order_number = msd.order_number

LEFT JOIN (
    /* 当日已审核出库尺码汇总 */
    SELECT snapshot_date, material_storage_id, order_number, SUM(amount) AS sum_amount
    FROM (
        SELECT DATE(orh.outbound_datetime) AS snapshot_date, ord.material_storage_id, 0 AS order_number, SUM(COALESCE(ord.size_34_outbound_amount,0)) AS amount
        FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 1, SUM(COALESCE(ord.size_35_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 2, SUM(COALESCE(ord.size_36_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 3, SUM(COALESCE(ord.size_37_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 4, SUM(COALESCE(ord.size_38_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 5, SUM(COALESCE(ord.size_39_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 6, SUM(COALESCE(ord.size_40_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 7, SUM(COALESCE(ord.size_41_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 8, SUM(COALESCE(ord.size_42_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 9, SUM(COALESCE(ord.size_43_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 10, SUM(COALESCE(ord.size_44_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 11, SUM(COALESCE(ord.size_45_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
        UNION ALL
        SELECT DATE(orh.outbound_datetime), ord.material_storage_id, 12, SUM(COALESCE(ord.size_46_outbound_amount,0)) FROM outbound_record_detail ord JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date AND orh.outbound_datetime < :deadline AND orh.approval_status = 1
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
    ) z
    GROUP BY snapshot_date, material_storage_id, order_number
) ao
  ON ao.snapshot_date = dmsc.snapshot_date
 AND ao.material_storage_id = dmsc.material_storage_id
 AND ao.order_number = msd.order_number

WHERE dmsc.snapshot_date = :now_date

ON DUPLICATE KEY UPDATE
    pending_inbound_sum  = VALUES(pending_inbound_sum),
    pending_outbound_sum = VALUES(pending_outbound_sum),
    inbound_amount_sum   = VALUES(inbound_amount_sum),
    outbound_amount_sum  = VALUES(outbound_amount_sum),
    update_time          = CURRENT_TIMESTAMP
;
    """)

    conn.execute(upsert_detail_sql, {"now_date": now_date, "deadline": deadline})


def main():
    ns = parse_args()
    start_d = datetime.strptime(ns.start, "%Y-%m-%d").date()
    end_d = datetime.strptime(ns.end, "%Y-%m-%d").date()

    engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=3600, future=True)
    print(f"连接数据库：{DB_URL}")
    total_days = (end_d - start_d).days + 1
    processed = 0

    with engine.begin() as conn:  # 自动事务
        cur = start_d
        while cur <= end_d:
            run_once_for_day(conn, cur)
            processed += 1
            print(f"✅ {cur} 已生成/更新：父表 + 尺码明细 ({processed}/{total_days})")
            cur += timedelta(days=1)

    print("全部完成 ✅")


if __name__ == "__main__":
    main()

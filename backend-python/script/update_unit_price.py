#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新 material_storage.unit_price 为最新入库单价，
并更新 material_storage.average_price 为平均采购单价。

口径：
- 最新单价：取最近一次「入库记录」的单价（可选：仅审批通过）。
- 平均采购单价 = (采购入库总金额 - 材料退回总金额) / (采购入库总数量 - 材料退回总数量)。

重要：
- 只统计 display = 1 的记录（头表与明细表都要为 1）：
  inbound_record、inbound_record_detail、outbound_record、outbound_record_detail
"""

import argparse
import sys
import pymysql
from typing import List, Optional

# ===================== 数据库配置 =====================
DB_USER = "root"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "jiancheng"
# =====================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Update latest and average unit price for material_storage (display=1 only)."
    )
    parser.add_argument(
        "--ids", type=str, default="", help="Comma-separated material_storage_id list."
    )
    parser.add_argument(
        "--approved-only",
        action="store_true",
        help="Only consider approved inbound records for latest price.",
    )
    return parser.parse_args()


# =====================================================
# Helper: 构建最新单价更新 SQL（只看 display=1；可选仅审批通过）
# =====================================================
def build_update_sql(msids: Optional[List[int]], approved_only: bool) -> str:
    where_parts = [
        "ir.display = 1",
        "ird.display = 1",
    ]
    if approved_only:
        where_parts.append("ir.approval_status = 1")
    if msids:
        id_list = ",".join(str(i) for i in msids)
        where_parts.append(f"ird.material_storage_id IN ({id_list})")
    where_clause = " AND ".join(where_parts)

    sql = f"""
    WITH latest_price AS (
        SELECT material_storage_id, unit_price
        FROM (
            SELECT
                ird.material_storage_id,
                ird.unit_price,
                ir.inbound_datetime,
                ir.inbound_record_id,
                ird.id AS detail_id,
                ROW_NUMBER() OVER (
                    PARTITION BY ird.material_storage_id
                    ORDER BY ir.inbound_datetime DESC, ir.inbound_record_id DESC, ird.id DESC
                ) AS rn
            FROM inbound_record_detail ird
            JOIN inbound_record ir
              ON ir.inbound_record_id = ird.inbound_record_id
            WHERE {where_clause}
        ) x
        WHERE x.rn = 1
    )
    UPDATE material_storage ms
    JOIN latest_price lp
      ON lp.material_storage_id = ms.material_storage_id
    SET ms.unit_price = lp.unit_price;
    """.strip()
    return sql


# =====================================================
# Helper: 构建平均价更新 SQL（只看 display=1）
# =====================================================
def build_avg_price_sql(msids: Optional[List[int]]) -> str:
    # 可选的最终 UPDATE 过滤
    update_where = ""
    if msids:
        id_list = ",".join(str(i) for i in msids)
        update_where = f"WHERE ms.material_storage_id IN ({id_list})"

    sql = f"""
    WITH inbound_sum AS (
        SELECT 
            ird.material_storage_id AS msid,
            SUM(ird.inbound_amount * ird.unit_price) AS inbound_total_amount,
            SUM(ird.inbound_amount) AS inbound_total_qty
        FROM inbound_record_detail ird
        JOIN inbound_record ir 
          ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_type = 0 
          AND ir.approval_status = 1
          AND ir.display = 1 
          AND ird.display = 1
        GROUP BY ird.material_storage_id
    ),
    return_sum AS (
        SELECT 
            ord.material_storage_id AS msid,
            SUM(ord.outbound_amount * ord.unit_price) AS return_total_amount,
            SUM(ord.outbound_amount) AS return_total_qty
        FROM outbound_record_detail ord
        JOIN outbound_record orr 
          ON orr.outbound_record_id = ord.outbound_record_id
        WHERE orr.outbound_type = 4 
          AND orr.approval_status = 1
          AND orr.display = 1 
          AND ord.display = 1
        GROUP BY ord.material_storage_id
    ),
    avg_price_calc AS (
        SELECT 
            i.msid,
            (COALESCE(i.inbound_total_amount,0) - COALESCE(r.return_total_amount,0)) /
            NULLIF((COALESCE(i.inbound_total_qty,0) - COALESCE(r.return_total_qty,0)), 0) AS avg_price
        FROM inbound_sum i
        LEFT JOIN return_sum r ON i.msid = r.msid
    )
    UPDATE material_storage ms
    JOIN avg_price_calc c 
      ON c.msid = ms.material_storage_id
    SET ms.average_price = c.avg_price
    {update_where};
    """.strip()
    return sql


# =====================================================
def fetch_preview(conn, msids: Optional[List[int]], approved_only: bool):
    print("预览最新单价更新：")
    where_parts = [
        "ir.display = 1",
        "ird.display = 1",
    ]
    if approved_only:
        where_parts.append("ir.approval_status = 1")
    if msids:
        id_list = ",".join(str(i) for i in msids)
        where_parts.append(f"ird.material_storage_id IN ({id_list})")
    where_clause = " AND ".join(where_parts)

    preview_sql = f"""
    WITH latest_price AS (
        SELECT material_storage_id, unit_price
        FROM (
            SELECT
                ird.material_storage_id,
                ird.unit_price,
                ir.inbound_datetime,
                ir.inbound_record_id,
                ird.id AS detail_id,
                ROW_NUMBER() OVER (
                    PARTITION BY ird.material_storage_id
                    ORDER BY ir.inbound_datetime DESC, ir.inbound_record_id DESC, ird.id DESC
                ) AS rn
            FROM inbound_record_detail ird
            JOIN inbound_record ir
              ON ir.inbound_record_id = ird.inbound_record_id
            WHERE {where_clause}
        ) x
        WHERE x.rn = 1
    )
    SELECT material_storage_id, unit_price 
    FROM latest_price 
    ORDER BY material_storage_id;
    """
    with conn.cursor() as cur:
        cur.execute(preview_sql)
        for r in cur.fetchall():
            print(f"  msid={r[0]} -> new_unit_price={r[1]}")


# =====================================================
def main():
    args = parse_args()
    msids = None
    if args.ids.strip():
        msids = [int(x) for x in args.ids.split(",") if x.strip()]

    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.Cursor,
    )

    try:
        fetch_preview(conn, msids, args.approved_only)

        print("\\n执行更新最新单价...")
        with conn.cursor() as cur:
            cur.execute(build_update_sql(msids, args.approved_only))
        print("最新单价更新完成。")

        print("\\n执行更新平均价...")
        with conn.cursor() as cur:
            cur.execute(build_avg_price_sql(msids))
        conn.commit()
        print("平均价更新完成。")

    except Exception as e:
        conn.rollback()
        print("执行失败，已回滚。错误：", repr(e))
    finally:
        conn.close()


if __name__ == "__main__":
    main()

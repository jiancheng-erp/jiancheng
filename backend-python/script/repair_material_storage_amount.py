
# -*- coding: utf-8 -*-
"""
库存修复脚本（按新口径 + 明确执行顺序 1→2→3→4）
顺序要求：
1) 采购入库 inbound_type = 0：未审 -> pending_inbound；已审 -> inbound_amount 与 current_amount
2) 遍历非盘库出库（outbound_type != 5）：未审 -> pending_outbound；已审 -> 扣减 current_amount；材料退回（type=4）额外扣减 inbound_amount
3) 遍历盘库出库（outbound_type = 5）：对每条明细限流（若申请>库存，则改成库存上限），并联动重算 item_total_price 与单据头 total_price
4) 盘库回填 inbound_type = 4：未审 -> pending_inbound；已审 -> 增加 inbound_amount 与 current_amount
（注意：步骤 4 一定在 1-3 完成后执行，以满足“盘库出库后再回填”的时序语义）

- 尺码材料按“索引 -> 列号(size_34..size_46)”映射，order_number=index，size_value=shoe_size_columns[index]。
- 仅对盘库出库（type=5）执行“限流与联动改价”；非盘库出库不做限流，按真实数量扣减。

依赖：PyMySQL
"""

import json
import pymysql
from decimal import Decimal

# ====== 数据库配置 ======
HOST = "localhost"
USER = "root"
PASSWORD = "root"
DB = "jiancheng"
CHARSET = "utf8mb4"

# ====== 业务配置 ======
MIN_SIZE = 34
MAX_SIZE = 46

# 未审批口径（0=待审，2=驳回，如只统计 0，改成 (0,)）
PENDING_STATUSES = (0, 2)

# 出库时间列（用于排序，仅对 type=5 限流时有用）
OUTBOUND_TIME_COL = "outbound_datetime"

# 写 size detail 前是否 TRUNCATE 全表
TRUNCATE_SIZE_DETAIL_BEFORE = True


def get_conn():
    return pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DB, charset=CHARSET)


def fetchall(cur, sql, args=None):
    cur.execute(sql, args or ())
    return cur.fetchall()


def blank_size_dict():
    return {s: Decimal(0) for s in range(MIN_SIZE, MAX_SIZE + 1)}


def main():
    conn = get_conn()
    cur = conn.cursor()

    print("=== 0) 读取 material_storage 基本信息 ===")
    ms_rows = fetchall(cur, "SELECT material_storage_id, shoe_size_columns FROM material_storage")

    sized_msids, unsized_msids, sized_map = [], [], {}
    for msid, size_json in ms_rows:
        msid = int(msid)
        if size_json:
            try:
                arr = json.loads(size_json)
                if isinstance(arr, list) and arr:
                    sizes = [str(s).strip() for s in arr if str(s).strip()]
                    if sizes:
                        sized_msids.append(msid)
                        sized_map[msid] = sizes
                        continue
            except Exception:
                pass
        unsized_msids.append(msid)

    print(f"带尺码: {len(sized_msids)}，不带尺码: {len(unsized_msids)}")

    # ========== PART A) 带尺码 ==========
    if sized_msids:
        print("\\n=== A) 带尺码：严格按 1→2→3→4 顺序计算 ===")
        fmt_ids = ",".join(["%s"] * len(sized_msids))

        # ---------- 1) 采购入库 inbound_type = 0 ----------
        in0_appr_rows = fetchall(cur, f"""
            SELECT d.material_storage_id,
                   SUM(COALESCE(d.size_34_inbound_amount,0)), SUM(COALESCE(d.size_35_inbound_amount,0)),
                   SUM(COALESCE(d.size_36_inbound_amount,0)), SUM(COALESCE(d.size_37_inbound_amount,0)),
                   SUM(COALESCE(d.size_38_inbound_amount,0)), SUM(COALESCE(d.size_39_inbound_amount,0)),
                   SUM(COALESCE(d.size_40_inbound_amount,0)), SUM(COALESCE(d.size_41_inbound_amount,0)),
                   SUM(COALESCE(d.size_42_inbound_amount,0)), SUM(COALESCE(d.size_43_inbound_amount,0)),
                   SUM(COALESCE(d.size_44_inbound_amount,0)), SUM(COALESCE(d.size_45_inbound_amount,0)),
                   SUM(COALESCE(d.size_46_inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.inbound_type = 0 AND r.approval_status = 1
            GROUP BY d.material_storage_id
        """, sized_msids)
        in0_pend_rows = fetchall(cur, f"""
            SELECT d.material_storage_id,
                   SUM(COALESCE(d.size_34_inbound_amount,0)), SUM(COALESCE(d.size_35_inbound_amount,0)),
                   SUM(COALESCE(d.size_36_inbound_amount,0)), SUM(COALESCE(d.size_37_inbound_amount,0)),
                   SUM(COALESCE(d.size_38_inbound_amount,0)), SUM(COALESCE(d.size_39_inbound_amount,0)),
                   SUM(COALESCE(d.size_40_inbound_amount,0)), SUM(COALESCE(d.size_41_inbound_amount,0)),
                   SUM(COALESCE(d.size_42_inbound_amount,0)), SUM(COALESCE(d.size_43_inbound_amount,0)),
                   SUM(COALESCE(d.size_44_inbound_amount,0)), SUM(COALESCE(d.size_45_inbound_amount,0)),
                   SUM(COALESCE(d.size_46_inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.inbound_type = 0 AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
            GROUP BY d.material_storage_id
        """, sized_msids + list(PENDING_STATUSES))

        in0_appr = {msid: blank_size_dict() for msid in sized_msids}
        in0_pend = {msid: blank_size_dict() for msid in sized_msids}
        for row in in0_appr_rows:
            msid = int(row[0])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                in0_appr[msid][s] = Decimal(int(row[1 + (s - MIN_SIZE)] or 0))
        for row in in0_pend_rows:
            msid = int(row[0])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                in0_pend[msid][s] = Decimal(int(row[1 + (s - MIN_SIZE)] or 0))

        # ---------- 2) 非盘库出库（outbound_type != 5） ----------
        out_non_stock_appr_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, r.outbound_type,
                   SUM(COALESCE(d.size_34_outbound_amount,0)), SUM(COALESCE(d.size_35_outbound_amount,0)),
                   SUM(COALESCE(d.size_36_outbound_amount,0)), SUM(COALESCE(d.size_37_outbound_amount,0)),
                   SUM(COALESCE(d.size_38_outbound_amount,0)), SUM(COALESCE(d.size_39_outbound_amount,0)),
                   SUM(COALESCE(d.size_40_outbound_amount,0)), SUM(COALESCE(d.size_41_outbound_amount,0)),
                   SUM(COALESCE(d.size_42_outbound_amount,0)), SUM(COALESCE(d.size_43_outbound_amount,0)),
                   SUM(COALESCE(d.size_44_outbound_amount,0)), SUM(COALESCE(d.size_45_outbound_amount,0)),
                   SUM(COALESCE(d.size_46_outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type != 5
            GROUP BY d.material_storage_id, r.outbound_type
        """, sized_msids)
        out_non_stock_pend_rows = fetchall(cur, f"""
            SELECT d.material_storage_id,
                   SUM(COALESCE(d.size_34_outbound_amount,0)), SUM(COALESCE(d.size_35_outbound_amount,0)),
                   SUM(COALESCE(d.size_36_outbound_amount,0)), SUM(COALESCE(d.size_37_outbound_amount,0)),
                   SUM(COALESCE(d.size_38_outbound_amount,0)), SUM(COALESCE(d.size_39_outbound_amount,0)),
                   SUM(COALESCE(d.size_40_outbound_amount,0)), SUM(COALESCE(d.size_41_outbound_amount,0)),
                   SUM(COALESCE(d.size_42_outbound_amount,0)), SUM(COALESCE(d.size_43_outbound_amount,0)),
                   SUM(COALESCE(d.size_44_outbound_amount,0)), SUM(COALESCE(d.size_45_outbound_amount,0)),
                   SUM(COALESCE(d.size_46_outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
              AND r.outbound_type != 5
            GROUP BY d.material_storage_id
        """, sized_msids + list(PENDING_STATUSES))

        used_non_stock = {msid: blank_size_dict() for msid in sized_msids}
        returned_non_stock = {msid: blank_size_dict() for msid in sized_msids}  # 退回出库（type=4）用于扣 inbound_amount
        for row in out_non_stock_appr_rows:
            msid, ob_type = int(row[0]), int(row[1])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                q = Decimal(int(row[2 + (s - MIN_SIZE)] or 0))
                used_non_stock[msid][s] += q
                if ob_type == 4:
                    returned_non_stock[msid][s] += q

        pend_out_non_stock = {msid: blank_size_dict() for msid in sized_msids}
        for row in out_non_stock_pend_rows:
            msid = int(row[0])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                pend_out_non_stock[msid][s] += Decimal(int(row[1 + (s - MIN_SIZE)] or 0))

        # ---------- 先得出“临时 current”（只含 1)入库0 与 2)非盘库出库） ----------
        temp_curr = {msid: blank_size_dict() for msid in sized_msids}
        for msid in sized_msids:
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                temp_curr[msid][s] = max(in0_appr[msid][s] - used_non_stock[msid][s], 0)

        # ---------- 3) 盘库出库（type=5）限流 + 改价 ----------
        stocktake_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.unit_price,0) AS unit_price,
                   COALESCE(d.item_total_price,0) AS item_total_price,
                   COALESCE(d.size_34_outbound_amount,0), COALESCE(d.size_35_outbound_amount,0),
                   COALESCE(d.size_36_outbound_amount,0), COALESCE(d.size_37_outbound_amount,0),
                   COALESCE(d.size_38_outbound_amount,0), COALESCE(d.size_39_outbound_amount,0),
                   COALESCE(d.size_40_outbound_amount,0), COALESCE(d.size_41_outbound_amount,0),
                   COALESCE(d.size_42_outbound_amount,0), COALESCE(d.size_43_outbound_amount,0),
                   COALESCE(d.size_44_outbound_amount,0), COALESCE(d.size_45_outbound_amount,0),
                   COALESCE(d.size_46_outbound_amount,0),
                   r.{OUTBOUND_TIME_COL}
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1
              AND r.outbound_type = 5
            ORDER BY r.{OUTBOUND_TIME_COL} ASC, d.id ASC
        """, sized_msids)

        header_ids_to_recalc = set()
        for row in stocktake_rows:
            d_id = int(row[0]); header_id = int(row[1]); msid = int(row[2])
            unit_price = Decimal(row[3] or 0)
            req_sizes = {s: Decimal(int(row[5 + (s - MIN_SIZE)] or 0)) for s in range(MIN_SIZE, MAX_SIZE + 1)}

            allowed_sizes = {}
            changed = False
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                avail = max(temp_curr[msid][s], 0)
                allowed = min(req_sizes[s], avail)
                allowed_sizes[s] = allowed
                if allowed != req_sizes[s]:
                    changed = True

            if changed:
                new_qty_sum = sum(allowed_sizes.values())
                new_item_total = unit_price * Decimal(new_qty_sum)
                set_cols, params = [], []
                for s in range(MIN_SIZE, MAX_SIZE + 1):
                    set_cols.append(f"size_{s}_outbound_amount=%s")
                    params.append(int(allowed_sizes[s]))
                set_cols.append("item_total_price=%s")
                params.append(new_item_total)
                params.append(d_id)
                cur.execute(f"UPDATE outbound_record_detail SET {', '.join(set_cols)} WHERE id=%s", params)
                header_ids_to_recalc.add(header_id)

            for s in range(MIN_SIZE, MAX_SIZE + 1):
                temp_curr[msid][s] = max(temp_curr[msid][s] - allowed_sizes.get(s, req_sizes[s]), 0)

        conn.commit()

        # ---------- 4) 盘库回填 inbound_type = 4（在 1-3 之后） ----------
        in4_appr_rows = fetchall(cur, f"""
            SELECT d.material_storage_id,
                   SUM(COALESCE(d.size_34_inbound_amount,0)), SUM(COALESCE(d.size_35_inbound_amount,0)),
                   SUM(COALESCE(d.size_36_inbound_amount,0)), SUM(COALESCE(d.size_37_inbound_amount,0)),
                   SUM(COALESCE(d.size_38_inbound_amount,0)), SUM(COALESCE(d.size_39_inbound_amount,0)),
                   SUM(COALESCE(d.size_40_inbound_amount,0)), SUM(COALESCE(d.size_41_inbound_amount,0)),
                   SUM(COALESCE(d.size_42_inbound_amount,0)), SUM(COALESCE(d.size_43_inbound_amount,0)),
                   SUM(COALESCE(d.size_44_inbound_amount,0)), SUM(COALESCE(d.size_45_inbound_amount,0)),
                   SUM(COALESCE(d.size_46_inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.inbound_type = 4 AND r.approval_status = 1
            GROUP BY d.material_storage_id
        """, sized_msids)
        in4_pend_rows = fetchall(cur, f"""
            SELECT d.material_storage_id,
                   SUM(COALESCE(d.size_34_inbound_amount,0)), SUM(COALESCE(d.size_35_inbound_amount,0)),
                   SUM(COALESCE(d.size_36_inbound_amount,0)), SUM(COALESCE(d.size_37_inbound_amount,0)),
                   SUM(COALESCE(d.size_38_inbound_amount,0)), SUM(COALESCE(d.size_39_inbound_amount,0)),
                   SUM(COALESCE(d.size_40_inbound_amount,0)), SUM(COALESCE(d.size_41_inbound_amount,0)),
                   SUM(COALESCE(d.size_42_inbound_amount,0)), SUM(COALESCE(d.size_43_inbound_amount,0)),
                   SUM(COALESCE(d.size_44_inbound_amount,0)), SUM(COALESCE(d.size_45_inbound_amount,0)),
                   SUM(COALESCE(d.size_46_inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.inbound_type = 4 AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
            GROUP BY d.material_storage_id
        """, sized_msids + list(PENDING_STATUSES))

        in4_appr = {msid: blank_size_dict() for msid in sized_msids}
        in4_pend = {msid: blank_size_dict() for msid in sized_msids}
        for row in in4_appr_rows:
            msid = int(row[0])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                in4_appr[msid][s] = Decimal(int(row[1 + (s - MIN_SIZE)] or 0))
        for row in in4_pend_rows:
            msid = int(row[0])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                in4_pend[msid][s] = Decimal(int(row[1 + (s - MIN_SIZE)] or 0))

        # ---------- 写回尺码明细（基于最终四字段） ----------
        if TRUNCATE_SIZE_DETAIL_BEFORE:
            cur.execute("TRUNCATE TABLE material_storage_size_detail")
            conn.commit()

        insert_sql = """
            INSERT INTO material_storage_size_detail
            (material_storage_id, size_value, order_number, pending_inbound, pending_outbound, inbound_amount, current_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        total_rows = 0
        for msid, sizes in sized_map.items():
            if not TRUNCATE_SIZE_DETAIL_BEFORE:
                cur.execute("DELETE FROM material_storage_size_detail WHERE material_storage_id=%s", (msid,))

            for idx, size_val in enumerate(sizes):
                col = MIN_SIZE + idx
                if col > MAX_SIZE:
                    continue
                # inbound_amount = (in0_appr + in4_appr) - returned_non_stock(type=4)
                inbound_amount = max(in0_appr[msid][col] + in4_appr[msid][col] - returned_non_stock[msid][col], 0)
                # current_amount = temp_curr(含1&2&3) + in4_appr
                current_amount = temp_curr[msid][col] + in4_appr[msid][col]
                pending_inbound = in0_pend[msid][col] + in4_pend[msid][col]
                pending_outbound = pend_out_non_stock[msid][col]
                cur.execute(insert_sql, (msid, str(size_val), idx,
                                         pending_inbound, pending_outbound, inbound_amount, current_amount))
                total_rows += 1
        conn.commit()
        print(f"✅ 尺码明细写入完成，共 {total_rows} 行。")

        # ---------- 汇总写回 material_storage 四字段 ----------
        for msid in sized_msids:
            inbound_amount = sum(max(in0_appr[msid][s] + in4_appr[msid][s] - returned_non_stock[msid][s], 0)
                                 for s in range(MIN_SIZE, MAX_SIZE + 1))
            current_amount = sum((temp_curr[msid][s] + in4_appr[msid][s]) for s in range(MIN_SIZE, MAX_SIZE + 1))
            pending_inbound = sum((in0_pend[msid][s] + in4_pend[msid][s]) for s in range(MIN_SIZE, MAX_SIZE + 1))
            pending_outbound = sum(pend_out_non_stock[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1))
            cur.execute("""
                UPDATE material_storage
                SET inbound_amount=%s, current_amount=%s,
                    pending_inbound=%s, pending_outbound=%s
                WHERE material_storage_id=%s
            """, (inbound_amount, current_amount, pending_inbound, pending_outbound, msid))
        conn.commit()

        # ---------- 重算盘库出库（type=5）单头金额 ----------
        if header_ids_to_recalc:
            print(f"重算盘库出库单头金额：{len(header_ids_to_recalc)} 张（带尺码）")
            for hid in header_ids_to_recalc:
                cur.execute("""
                    UPDATE outbound_record o
                    SET o.total_price = (
                        SELECT COALESCE(SUM(COALESCE(d.item_total_price,0)), 0)
                        FROM outbound_record_detail d
                        WHERE d.outbound_record_id = o.outbound_record_id
                    )
                    WHERE o.outbound_record_id = %s
                """, (hid,))
            conn.commit()

    # ========== PART B) 不带尺码 ==========
    if unsized_msids:
        print("\\n=== B) 不带尺码：严格按 1→2→3→4 顺序计算 ===")
        fmt_ids = ",".join(["%s"] * len(unsized_msids))

        # 1) 采购入库 0
        in0_appr_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.inbound_type = 0 AND r.approval_status = 1
            GROUP BY d.material_storage_id
        """, unsized_msids)
        in0_pend_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.inbound_type = 0 AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
            GROUP BY d.material_storage_id
        """, unsized_msids + list(PENDING_STATUSES))
        in0_appr = {int(msid): Decimal(q or 0) for msid, q in in0_appr_rows}
        in0_pend = {int(msid): Decimal(q or 0) for msid, q in in0_pend_rows}

        # 2) 非盘库出库
        out_non_stock_appr_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, r.outbound_type, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type != 5
            GROUP BY d.material_storage_id, r.outbound_type
        """, unsized_msids)
        out_non_stock_pend_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
              AND r.outbound_type != 5
            GROUP BY d.material_storage_id
        """, unsized_msids + list(PENDING_STATUSES))

        used_non_stock = {msid: Decimal(0) for msid in unsized_msids}
        returned_non_stock = {msid: Decimal(0) for msid in unsized_msids}
        for msid, ob_type, qty in out_non_stock_appr_rows:
            msid = int(msid); ob_type = int(ob_type); qty = Decimal(q or 0)
            used_non_stock[msid] += qty
            if ob_type == 4:
                returned_non_stock[msid] += qty
        pend_out_non_stock = {int(msid): Decimal(q or 0) for msid, q in out_non_stock_pend_rows}

        # 临时 current（含 1&2）
        temp_curr = {msid: max(in0_appr.get(msid, 0) - used_non_stock.get(msid, 0), 0) for msid in unsized_msids}

        # 3) 盘库出库限流 & 改价
        stocktake_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.outbound_amount,0), COALESCE(d.unit_price,0), COALESCE(d.item_total_price,0),
                   r.{OUTBOUND_TIME_COL}
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type = 5
            ORDER BY r.{OUTBOUND_TIME_COL} ASC, d.id ASC
        """, unsized_msids)

        header_ids_to_recalc = set()
        for d_id, header_id, msid, req, unit_price, _old_total, _t in stocktake_rows:
            msid = int(msid)
            req = Decimal(req or 0)
            avail = max(temp_curr.get(msid, 0), 0)
            allowed = min(req, avail)
            if allowed != req:
                new_total = Decimal(unit_price or 0) * allowed
                cur.execute("""UPDATE outbound_record_detail
                               SET outbound_amount=%s, item_total_price=%s
                               WHERE id=%s""", (allowed, new_total, int(d_id)))
                header_ids_to_recalc.add(int(header_id))
            temp_curr[msid] = max(avail - allowed, 0)
        conn.commit()

        # 4) 盘库回填 inbound_type = 4（在 1-3 之后）
        in4_appr_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.inbound_type = 4 AND r.approval_status = 1
            GROUP BY d.material_storage_id
        """, unsized_msids)
        in4_pend_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.inbound_type = 4 AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
            GROUP BY d.material_storage_id
        """, unsized_msids + list(PENDING_STATUSES))
        in4_appr = {int(msid): Decimal(q or 0) for msid, q in in4_appr_rows}
        in4_pend = {int(msid): Decimal(q or 0) for msid, q in in4_pend_rows}

        # 写回 material_storage（四字段；inbound_amount 需要扣 returned_non_stock）
        for msid in unsized_msids:
            inbound_amount = max(in0_appr.get(msid, 0) + in4_appr.get(msid, 0) - returned_non_stock.get(msid, 0), 0)
            current_amount = temp_curr.get(msid, 0) + in4_appr.get(msid, 0)
            pending_inbound = in0_pend.get(msid, 0) + in4_pend.get(msid, 0)
            pending_outbound = pend_out_non_stock.get(msid, 0)
            cur.execute("""
                UPDATE material_storage
                SET inbound_amount=%s, current_amount=%s,
                    pending_inbound=%s, pending_outbound=%s
                WHERE material_storage_id=%s
            """, (inbound_amount, current_amount, pending_inbound, pending_outbound, msid))
        conn.commit()

        # 不带尺码无需写 size detail 行（该表仅服务于尺码材料）。

        if header_ids_to_recalc:
            print(f"重算盘库出库单头金额：{len(header_ids_to_recalc)} 张（不带尺码）")
            for hid in header_ids_to_recalc:
                cur.execute("""
                    UPDATE outbound_record o
                    SET o.total_price = (
                        SELECT COALESCE(SUM(COALESCE(d.item_total_price,0)), 0)
                        FROM outbound_record_detail d
                        WHERE d.outbound_record_id = o.outbound_record_id
                    )
                    WHERE o.outbound_record_id = %s
                """, (hid,))
            conn.commit()

    print("\\n✅ 全部完成（按顺序 1→2→3→4）：")
    print(" - 0类入库已先处理；非盘库出库与盘库出库限流随后；最后回填4类入库。")
    print(" - 退回出库(type=4)已额外扣减累计入库(inbound_amount)。")
    print(" - 尺码 detail 按索引->列号映射并回写。")

    conn.close()


if __name__ == "__main__":
    main()

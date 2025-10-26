# -*- coding: utf-8 -*-
"""
库存修复脚本（按新口径 + 明确执行顺序 1→2→3→4→5）

口径统一：
- inbound_amount  = 已审入库数量（inbound_type in (0,4)，approval_status=1）
- outbound_amount = 所有已审出库允许量总和（盘库 + 非盘库，含退回出库 type=4）
- current_amount  = inbound_amount - outbound_amount
- pending_* 口径：approval_status in (0,2)

顺序要求：
1) 入库（0 与 4）：未审 -> pending_inbound；已审 -> inbound_amount 与 current_amount（通过 current=inbound-outbound 表达）。
2) 非盘库（< 2025-09-05）：未审 -> pending_outbound；已审 -> 限流后计入 outbound_amount & 改价 & 扣减 current（隐含）；退回(type=4)同样计入 outbound_amount。
3) 盘库（=5）：同上（限流、计入 outbound_amount、改价）。
4) 非盘库（>= 2025-09-05）：同步骤2。
5) 特殊修正（仅不带尺码）：当 pending_inbound>0 且 current<0 且 pending_inbound != -current，且 msid 不在排除清单：
   - 设 delta = pending_inbound + current（>0）；
   - 选一条 outbound_amount=0 的出库明细（优先已审 & 非盘库），将 outbound_amount=delta，改 item_total_price 并重算单头；
   - material_storage：outbound_amount += delta；current_amount -= delta （**按你的新口径，直接相对扣减，不重算**）。

依赖：PyMySQL
"""

import json
from decimal import Decimal
import pymysql

# ====== 数据库配置 ======
HOST = "localhost"
USER = "root"
PASSWORD = "root"
DB = "jiancheng"
CHARSET = "utf8mb4"

# ====== 业务配置 ======
MIN_SIZE = 34
MAX_SIZE = 46

# 未审批口径（0=待审，2=驳回）
PENDING_STATUSES = (0, 2)

# 时间列与日期阈值（含时区以数据库为准）
OUTBOUND_TIME_COL = "outbound_datetime"
SPLIT_DATE = "2025-09-05"  # 步骤2：< 2025-09-05；步骤4：>= 2025-09-05

# 写 size detail 前是否 TRUNCATE 全表（谨慎！如有其他数据请设为 False）
TRUNCATE_SIZE_DETAIL_BEFORE = True

# 步骤 5 排除 msid
STEP5_EXCLUDE = {37679, 38116, 38114, 38502}


def get_conn():
    return pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DB, charset=CHARSET)


def fetchall(cur, sql, args=None):
    cur.execute(sql, args or ())
    return cur.fetchall()


def fetchone(cur, sql, args=None):
    cur.execute(sql, args or ())
    return cur.fetchone()


def blank_size_dict(default=Decimal(0)):
    return {s: Decimal(default) for s in range(MIN_SIZE, MAX_SIZE + 1)}


def main():
    conn = get_conn()
    cur = conn.cursor()

    print("=== 0) 读取 material_storage 基本信息与尺码映射 ===")
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

    # ------------- A) 带尺码材料 -------------
    if sized_msids:
        print("\n=== A) 带尺码：1→2(非盘库<9/5)→3(盘库)→4(非盘库>=9/5) ===")
        fmt_ids = ",".join(["%s"] * len(sized_msids))

        # Step 1: 入库（0 与 4）
        appr_rows = fetchall(cur, f"""
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
              AND r.approval_status = 1 AND r.inbound_type IN (0,4)
            GROUP BY d.material_storage_id
        """, sized_msids)
        pend_rows = fetchall(cur, f"""
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
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
              AND r.inbound_type IN (0,4)
            GROUP BY d.material_storage_id
        """, sized_msids + list(PENDING_STATUSES))

        appr_in = {msid: blank_size_dict() for msid in sized_msids}
        pend_in = {msid: blank_size_dict() for msid in sized_msids}
        for row in appr_rows:
            msid = int(row[0])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                appr_in[msid][s] = Decimal(int(row[1 + (s - MIN_SIZE)] or 0))
        for row in pend_rows:
            msid = int(row[0])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                pend_in[msid][s] = Decimal(int(row[1 + (s - MIN_SIZE)] or 0))

        # 运行态：current = inbound - outbound；先把 current 初始化为 inbound，再随着出库被消耗
        temp_curr = {msid: {s: appr_in[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1)} for msid in sized_msids}
        temp_pend_remain = {msid: {s: pend_in[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1)} for msid in sized_msids}
        # 累计已审出库的 outbound（按允许量）
        outbound_sum = {msid: blank_size_dict() for msid in sized_msids}
        header_ids_to_recalc = set()

        def cap_and_consume(msid, req_map):
            allowed = {}
            changed = False
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                req = Decimal(req_map[s])
                cap = max(temp_curr[msid][s] + temp_pend_remain[msid][s], 0)
                a = min(req, cap)
                allowed[s] = a
                if a != req:
                    changed = True
            # consume current and pending remainder；并累计 outbound
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                a = allowed[s]
                pend_used = max(a - max(temp_curr[msid][s], 0), 0)
                pend_used = min(pend_used, temp_pend_remain[msid][s])
                temp_pend_remain[msid][s] -= pend_used
                temp_curr[msid][s] -= a
                outbound_sum[msid][s] += a
            return allowed, changed

        # Step 2: 非盘库出库（< 2025-09-05）
        step2_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.unit_price,0),
                   COALESCE(d.size_34_outbound_amount,0), COALESCE(d.size_35_outbound_amount,0),
                   COALESCE(d.size_36_outbound_amount,0), COALESCE(d.size_37_outbound_amount,0),
                   COALESCE(d.size_38_outbound_amount,0), COALESCE(d.size_39_outbound_amount,0),
                   COALESCE(d.size_40_outbound_amount,0), COALESCE(d.size_41_outbound_amount,0),
                   COALESCE(d.size_42_outbound_amount,0), COALESCE(d.size_43_outbound_amount,0),
                   COALESCE(d.size_44_outbound_amount,0), COALESCE(d.size_45_outbound_amount,0),
                   COALESCE(d.size_46_outbound_amount,0),
                   r.outbound_type, r.{OUTBOUND_TIME_COL}
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type != 5
              AND DATE(r.{OUTBOUND_TIME_COL}) < %s
            ORDER BY r.{OUTBOUND_TIME_COL} ASC, d.id ASC
        """, sized_msids + [SPLIT_DATE])

        for row in step2_rows:
            d_id, hdr_id, msid = int(row[0]), int(row[1]), int(row[2])
            unit_price = Decimal(row[3] or 0)
            req = {s: Decimal(int(row[4 + (s - MIN_SIZE)] or 0)) for s in range(MIN_SIZE, MAX_SIZE + 1)}
            allowed, changed = cap_and_consume(msid, req)
            if changed:
                new_qty_sum = int(sum(allowed.values()))
                new_total = unit_price * Decimal(new_qty_sum)
                set_cols, params = [], []
                for s in range(MIN_SIZE, MAX_SIZE + 1):
                    set_cols.append(f"size_{s}_outbound_amount=%s"); params.append(int(allowed[s]))
                set_cols.append("item_total_price=%s"); params.append(new_total)
                params.append(d_id)
                cur.execute(f"UPDATE outbound_record_detail SET {', '.join(set_cols)} WHERE id=%s", params)
                header_ids_to_recalc.add(hdr_id)

        conn.commit()

        # Step 3: 盘库出库（=5）
        stock_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.unit_price,0),
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
              AND r.approval_status = 1 AND r.outbound_type = 5
            ORDER BY r.{OUTBOUND_TIME_COL} ASC, d.id ASC
        """, sized_msids)

        for row in stock_rows:
            d_id, hdr_id, msid = int(row[0]), int(row[1]), int(row[2])
            unit_price = Decimal(row[3] or 0)
            req = {s: Decimal(int(row[4 + (s - MIN_SIZE)] or 0)) for s in range(MIN_SIZE, MAX_SIZE + 1)}
            allowed, changed = cap_and_consume(msid, req)
            if changed:
                new_qty_sum = int(sum(allowed.values()))
                new_total = unit_price * Decimal(new_qty_sum)
                set_cols, params = [], []
                for s in range(MIN_SIZE, MAX_SIZE + 1):
                    set_cols.append(f"size_{s}_outbound_amount=%s"); params.append(int(allowed[s]))
                set_cols.append("item_total_price=%s"); params.append(new_total)
                params.append(d_id)
                cur.execute(f"UPDATE outbound_record_detail SET {', '.join(set_cols)} WHERE id=%s", params)
                header_ids_to_recalc.add(hdr_id)

        conn.commit()

        # Step 4: 非盘库出库（>= 2025-09-05）
        step4_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.unit_price,0),
                   COALESCE(d.size_34_outbound_amount,0), COALESCE(d.size_35_outbound_amount,0),
                   COALESCE(d.size_36_outbound_amount,0), COALESCE(d.size_37_outbound_amount,0),
                   COALESCE(d.size_38_outbound_amount,0), COALESCE(d.size_39_outbound_amount,0),
                   COALESCE(d.size_40_outbound_amount,0), COALESCE(d.size_41_outbound_amount,0),
                   COALESCE(d.size_42_outbound_amount,0), COALESCE(d.size_43_outbound_amount,0),
                   COALESCE(d.size_44_outbound_amount,0), COALESCE(d.size_45_outbound_amount,0),
                   COALESCE(d.size_46_outbound_amount,0),
                   r.outbound_type, r.{OUTBOUND_TIME_COL}
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type != 5
              AND DATE(r.{OUTBOUND_TIME_COL}) >= %s
            ORDER BY r.{OUTBOUND_TIME_COL} ASC, d.id ASC
        """, sized_msids + [SPLIT_DATE])

        for row in step4_rows:
            d_id, hdr_id, msid = int(row[0]), int(row[1]), int(row[2])
            unit_price = Decimal(row[3] or 0)
            req = {s: Decimal(int(row[4 + (s - MIN_SIZE)] or 0)) for s in range(MIN_SIZE, MAX_SIZE + 1)}
            allowed, changed = cap_and_consume(msid, req)
            if changed:
                new_qty_sum = int(sum(allowed.values()))
                new_total = unit_price * Decimal(new_qty_sum)
                set_cols, params = [], []
                for s in range(MIN_SIZE, MAX_SIZE + 1):
                    set_cols.append(f"size_{s}_outbound_amount=%s"); params.append(int(allowed[s]))
                set_cols.append("item_total_price=%s"); params.append(new_total)
                params.append(d_id)
                cur.execute(f"UPDATE outbound_record_detail SET {', '.join(set_cols)} WHERE id=%s", params)
                header_ids_to_recalc.add(hdr_id)

        conn.commit()

        # pending_outbound（非盘库，所有日期；未审）
        pend_out_rows = fetchall(cur, f"""
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

        pend_out = {msid: blank_size_dict() for msid in sized_msids}
        for row in pend_out_rows:
            msid = int(row[0])
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                pend_out[msid][s] = Decimal(int(row[1 + (s - MIN_SIZE)] or 0))

        # 写入尺码明细表（注意：需要表里有 outbound_amount 列）
        if TRUNCATE_SIZE_DETAIL_BEFORE:
            cur.execute("TRUNCATE TABLE material_storage_size_detail")
            conn.commit()

        insert_sql = """
            INSERT INTO material_storage_size_detail
            (material_storage_id, size_value, order_number, pending_inbound, pending_outbound, inbound_amount, outbound_amount, current_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        total_rows = 0
        for msid, sizes in sized_map.items():
            for idx, size_val in enumerate(sizes):
                col = MIN_SIZE + idx
                if col > MAX_SIZE:
                    continue
                pending_inbound = pend_in[msid][col]
                pending_outbound = pend_out[msid][col]
                inbound_amount = appr_in[msid][col]
                out_amount = outbound_sum[msid][col]
                current_amount = inbound_amount - out_amount
                cur.execute(insert_sql, (msid, str(size_val), idx,
                                         pending_inbound, pending_outbound,
                                         inbound_amount, out_amount, current_amount))
                total_rows += 1

        conn.commit()
        print(f"✅ 尺码明细写入完成，共 {total_rows} 行。")

        # 汇总回写 material_storage（inbound/outbound/current/pending_*）
        for msid in sized_msids:
            inbound_amount_sum = sum(appr_in[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1))
            outbound_amount_sum = sum(outbound_sum[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1))
            current_amount_sum = inbound_amount_sum - outbound_amount_sum
            pending_inbound_sum = sum(pend_in[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1))
            pending_outbound_sum = sum(pend_out[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1))
            cur.execute("""
                UPDATE material_storage
                SET inbound_amount=%s, outbound_amount=%s, current_amount=%s,
                    pending_inbound=%s, pending_outbound=%s
                WHERE material_storage_id=%s
            """, (inbound_amount_sum, outbound_amount_sum, current_amount_sum,
                  pending_inbound_sum, pending_outbound_sum, msid))
        conn.commit()

        if header_ids_to_recalc:
            print(f"重算被限流单据的 total_price：{len(header_ids_to_recalc)} 张（带尺码）")
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

    # ------------- B) 不带尺码材料 -------------
    if unsized_msids:
        print("\n=== B) 不带尺码：1→2(非盘库<9/5)→3(盘库)→4(非盘库>=9/5) ===")
        fmt_ids = ",".join(["%s"] * len(unsized_msids))

        # Step 1: 入库（0 与 4）
        appr_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.inbound_type IN (0,4)
            GROUP BY d.material_storage_id
        """, unsized_msids)
        pend_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
              AND r.inbound_type IN (0,4)
            GROUP BY d.material_storage_id
        """, unsized_msids + list(PENDING_STATUSES))

        appr_in = {int(msid): Decimal(q or 0) for msid, q in appr_rows}
        pend_in = {int(msid): Decimal(q or 0) for msid, q in pend_rows}
        temp_curr = {msid: appr_in.get(msid, Decimal(0)) for msid in unsized_msids}
        temp_pend_remain = {msid: pend_in.get(msid, Decimal(0)) for msid in unsized_msids}
        outbound_sum = {msid: Decimal(0) for msid in unsized_msids}
        header_ids_to_recalc = set()

        def cap_and_consume_unsized(msid, req_qty):
            cap = max(temp_curr.get(msid, Decimal(0)) + temp_pend_remain.get(msid, Decimal(0)), Decimal(0))
            allowed = min(Decimal(req_qty), cap)
            # pending 被消耗的部分（超过当前库存的部分）
            pend_used = max(allowed - max(temp_curr.get(msid, Decimal(0)), Decimal(0)), Decimal(0))
            pend_used = min(pend_used, temp_pend_remain.get(msid, Decimal(0)))
            temp_pend_remain[msid] = temp_pend_remain.get(msid, Decimal(0)) - pend_used
            temp_curr[msid] = temp_curr.get(msid, Decimal(0)) - allowed
            outbound_sum[msid] = outbound_sum.get(msid, Decimal(0)) + allowed
            return allowed

        # Step 2: 非盘库（< 9/5）
        step2_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.outbound_amount,0), COALESCE(d.unit_price,0), r.outbound_type, r.{OUTBOUND_TIME_COL}
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type != 5
              AND DATE(r.{OUTBOUND_TIME_COL}) < %s
            ORDER BY r.{OUTBOUND_TIME_COL} ASC, d.id ASC
        """, unsized_msids + [SPLIT_DATE])

        for d_id, hdr_id, msid, req, unit_price, _ob_type, _t in step2_rows:
            msid = int(msid)
            req = Decimal(req or 0)
            allowed = cap_and_consume_unsized(msid, req)
            if allowed != req:
                new_total = Decimal(unit_price or 0) * allowed
                cur.execute("""UPDATE outbound_record_detail
                               SET outbound_amount=%s, item_total_price=%s
                               WHERE id=%s""", (int(allowed), new_total, int(d_id)))
                header_ids_to_recalc.add(int(hdr_id))

        conn.commit()

        # Step 3: 盘库（=5）
        stock_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.outbound_amount,0), COALESCE(d.unit_price,0), r.{OUTBOUND_TIME_COL}
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type = 5
            ORDER BY r.{OUTBOUND_TIME_COL} ASC, d.id ASC
        """, unsized_msids)

        for d_id, hdr_id, msid, req, unit_price, _t in stock_rows:
            msid = int(msid)
            req = Decimal(req or 0)
            allowed = cap_and_consume_unsized(msid, req)
            if allowed != req:
                new_total = Decimal(unit_price or 0) * allowed
                cur.execute("""UPDATE outbound_record_detail
                               SET outbound_amount=%s, item_total_price=%s
                               WHERE id=%s""", (int(allowed), new_total, int(d_id)))
                header_ids_to_recalc.add(int(hdr_id))

        conn.commit()

        # Step 4: 非盘库（>= 9/5）
        step4_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.outbound_amount,0), COALESCE(d.unit_price,0), r.outbound_type, r.{OUTBOUND_TIME_COL}
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type != 5
              AND DATE(r.{OUTBOUND_TIME_COL}) >= %s
            ORDER BY r.{OUTBOUND_TIME_COL} ASC, d.id ASC
        """, unsized_msids + [SPLIT_DATE])

        for d_id, hdr_id, msid, req, unit_price, _ob_type, _t in step4_rows:
            msid = int(msid)
            req = Decimal(req or 0)
            allowed = cap_and_consume_unsized(msid, req)
            if allowed != req:
                new_total = Decimal(unit_price or 0) * allowed
                cur.execute("""UPDATE outbound_record_detail
                               SET outbound_amount=%s, item_total_price=%s
                               WHERE id=%s""", (int(allowed), new_total, int(d_id)))
                header_ids_to_recalc.add(int(hdr_id))

        conn.commit()

        # pending_outbound（非盘库，所有日期；未审）
        pend_out_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
              AND r.outbound_type != 5
            GROUP BY d.material_storage_id
        """, unsized_msids + list(PENDING_STATUSES))
        pend_out = {int(msid): Decimal(q or 0) for msid, q in pend_out_rows}

        # 回写 material_storage（不带尺码）
        for msid in unsized_msids:
            inbound_amount = appr_in.get(msid, Decimal(0))
            out_amount = outbound_sum.get(msid, Decimal(0))
            current_amount = inbound_amount - out_amount
            pending_inbound = pend_in.get(msid, Decimal(0))
            pending_outbound = pend_out.get(msid, Decimal(0))
            cur.execute("""
                UPDATE material_storage
                SET inbound_amount=%s, outbound_amount=%s, current_amount=%s,
                    pending_inbound=%s, pending_outbound=%s
                WHERE material_storage_id=%s
            """, (inbound_amount, out_amount, current_amount, pending_inbound, pending_outbound, msid))
        conn.commit()

        if header_ids_to_recalc:
            print(f"重算被限流单据的 total_price：{len(header_ids_to_recalc)} 张（不带尺码）")
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

        # ------------- C) 步骤 5（仅不带尺码材料） -------------
        print("\n=== C) 步骤 5：修正 pending_inbound>0 且 current<0 且二者不相反数的材料（仅不带尺码）===")
        # 找出需要处理的 msid
        fix_rows = fetchall(cur, f"""
            SELECT material_storage_id, inbound_amount, outbound_amount, pending_inbound, current_amount
            FROM material_storage
            WHERE material_storage_id IN ({fmt_ids})
              AND pending_inbound > 0
              AND current_amount < 0
              AND pending_inbound != -current_amount
        """, unsized_msids)

        # 过滤排除清单
        fix_targets = [(int(msid), Decimal(inb or 0), Decimal(outb or 0),
                        Decimal(pend or 0), Decimal(curr or 0))
                       for msid, inb, outb, pend, curr in fix_rows
                       if int(msid) not in STEP5_EXCLUDE]

        print(f"步骤 5 待处理 msid 数量：{len(fix_targets)}（已排除 {len(fix_rows) - len(fix_targets)} 个）")

        for msid, inbound_amount, outbound_amount, pending_inbound, current_amount in fix_targets:
            delta = pending_inbound + current_amount  # 注意：current<0，pend>0
            if delta <= 0:
                print(f" - 跳过 msid={msid}：delta={delta} <= 0")
                continue

            # 优先找：已审 & 非盘库 & outbound_amount=0 的出库明细（最新一条优先）
            candidate = fetchone(cur, f"""
                SELECT d.id, d.outbound_record_id, COALESCE(d.unit_price,0)
                FROM outbound_record_detail d
                JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
                WHERE d.material_storage_id = %s
                  AND COALESCE(d.outbound_amount,0) = 0
                  AND r.approval_status = 1
                  AND r.outbound_type != 5
                ORDER BY r.{OUTBOUND_TIME_COL} DESC, d.id ASC
                LIMIT 1
            """, (msid,))

            # 若没有，则降级：任意 outbound_amount=0 的明细
            if not candidate:
                candidate = fetchone(cur, f"""
                    SELECT d.id, d.outbound_record_id, COALESCE(d.unit_price,0)
                    FROM outbound_record_detail d
                    JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
                    WHERE d.material_storage_id = %s
                      AND COALESCE(d.outbound_amount,0) = 0
                    ORDER BY r.{OUTBOUND_TIME_COL} DESC, d.id ASC
                    LIMIT 1
                """, (msid,))

            if not candidate:
                print(f" ! 未找到 outbound_amount=0 的出库明细，msid={msid}，跳过")
                continue

            d_id, hdr_id, unit_price = int(candidate[0]), int(candidate[1]), Decimal(candidate[2] or 0)
            new_total = unit_price * delta

            # 更新该明细
            cur.execute("""
                UPDATE outbound_record_detail
                SET outbound_amount=%s, item_total_price=%s
                WHERE id=%s
            """, (int(delta), new_total, d_id))

            # 重算单据头 total_price
            cur.execute("""
                UPDATE outbound_record o
                SET o.total_price = (
                    SELECT COALESCE(SUM(COALESCE(d.item_total_price,0)), 0)
                    FROM outbound_record_detail d
                    WHERE d.outbound_record_id = o.outbound_record_id
                )
                WHERE o.outbound_record_id = %s
            """, (hdr_id,))

            # 同步回写 material_storage：按你的新规“相对修改”
            cur.execute("""
                UPDATE material_storage
                SET outbound_amount = COALESCE(outbound_amount,0) + %s,
                    current_amount  = COALESCE(current_amount,0) - %s
                WHERE material_storage_id = %s
            """, (int(delta), int(delta), msid))
            conn.commit()

            print(f" ✓ 已处理 msid={msid}，detail_id={d_id}，delta={int(delta)}；"
                  f"outbound_amount += {int(delta)}，current_amount -= {int(delta)}")

    print("\n✅ 全部完成：按 1→2(<9/5 非盘库)→3(盘库)→4(>=9/5 非盘库)→5 的顺序执行。")
    print(" - inbound_amount = 已审入库(0+4)；outbound_amount = 已审出库(盘库+非盘库)允许量；current = inbound - outbound。")
    print(" - 出库限流采用 (current + pending_inbound_remaining) 上限，并逐条改价与重算单头。")
    print(" - 退回出库(type=4)并入 outbound_amount（不再冲减 inbound）。")
    print(" - 尺码 detail 按索引->列号映射写入，并含 outbound_amount。")
    print(" - 第 5 步按你的新口径：仅对不带尺码材料做“相对扣减”，不整体重算。")

    conn.close()


if __name__ == "__main__":
    main()

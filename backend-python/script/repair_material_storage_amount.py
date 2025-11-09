# -*- coding: utf-8 -*-
"""
库存修复脚本（按新口径；取消 split_date；display=1 过滤；按出库时间计算）

业务口径（统一）：
- pending_inbound = 未审入库数量总和（approval_status in (0,2)）
- pending_outbound= 未审出库数量总和（approval_status in (0,2)）
- inbound_amount  = 已审采购入库数量（inbound_type = 0，approval_status=1）- 已審材料退回出库数量（outbound_type =4，approval_status=1）
- outbound_amount = 已审核出库数量总和（outbound_type in (1,2,3)，approval_status=1）
- make_inventory_inbound  = 已审盘库入库数量（inbound_type=4，approval_status=1）
- make_inventory_outbound = 已审盘库出库数量（outbound_type=5，approval_status=1）
- current_amount  = inbound_amount - outbound_amount + make_inventory_inbound - make_inventory_outbound

顺序要求：
1) 入库(inbound_type = 0)未审 -> pending_inbound；已审 -> inbound_amount 与 current_amount
2) 回填入库(inbound_type = 4)。全进入 make_inventory_inbound
3) 材料退回(outbound_type = 4), 未审 -> pending_outbound；已审：扣减 inbound_amount 与 current_amount
4) 盘库出库(outbound_type = 5)：全进入 make_inventory_outbound，并扣减 current_amount（通过 current 公式体现）
5) 其他出库(outbound_type in (1,2,3))：按时间顺序从旧到新来看，未审 -> pending_outbound；已审 -> 限流后计入 outbound_amount & 改价 & 扣减 current

重要实现点（提速）：
- material_storage 的 pending_outbound / outbound_amount 一律从明细字段 outbound_amount 聚合；
- 尺码层（material_storage_size_detail）仍按 size_*_*_amount 聚合回写；
- 所有限流/聚合都按“全量数据”，并严格过滤头表与明细 display=1；
- 限流与计算严格按出库时间（outbound_record.outbound_datetime）升序进行。
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

# 写 size detail 前是否 TRUNCATE 全表（谨慎！如有其他数据请设为 False）
TRUNCATE_SIZE_DETAIL_BEFORE = True


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
        print("\\n=== A) 带尺码：入库聚合 → 出库限流(常规出库1/2/3) → 尺码写回 → storage聚合 ===")
        fmt_ids = ",".join(["%s"] * len(sized_msids))

        # 入库（★ 口径：已审采购入库 type=0；待审 type in (0,4)）
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
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.inbound_type = 0
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
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
              AND r.inbound_type IN (0,4)
            GROUP BY d.material_storage_id
        """, sized_msids + list(PENDING_STATUSES))

        appr_in_purchase_total = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.inbound_type = 0
            GROUP BY d.material_storage_id
        """, sized_msids)
        appr_in_purchase_total = {int(msid): Decimal(q or 0) for msid, q in appr_in_purchase_total}

        pend_in_total = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
              AND r.inbound_type IN (0,4)
            GROUP BY d.material_storage_id
        """, sized_msids + list(PENDING_STATUSES))
        pend_in_total = {int(msid): Decimal(q or 0) for msid, q in pend_in_total}

        appr_make_inv_in_total = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.inbound_type = 4
            GROUP BY d.material_storage_id
        """, sized_msids)
        appr_make_inv_in_total = {int(msid): Decimal(q or 0) for msid, q in appr_make_inv_in_total}

        appr_return_out_total = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type = 4
            GROUP BY d.material_storage_id
        """, sized_msids)
        appr_return_out_total = {int(msid): Decimal(q or 0) for msid, q in appr_return_out_total}

        appr_make_inv_out_total = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type = 5
            GROUP BY d.material_storage_id
        """, sized_msids)
        appr_make_inv_out_total = {int(msid): Decimal(q or 0) for msid, q in appr_make_inv_out_total}

        appr_out_total = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type IN (1,2,3)
            GROUP BY d.material_storage_id
        """, sized_msids)
        appr_out_total = {int(msid): Decimal(q or 0) for msid, q in appr_out_total}

        # 尺码层 dict
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

        # 限流基数：仅“已审采购入库(type=0)”；未审入库作为上限补充
        temp_curr = {msid: {s: appr_in[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1)} for msid in sized_msids}
        temp_pend_remain = {msid: {s: pend_in[msid][s] for s in range(MIN_SIZE, MAX_SIZE + 1)} for msid in sized_msids}
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
            # consume
            for s in range(MIN_SIZE, MAX_SIZE + 1):
                a = allowed[s]
                pend_used = max(a - max(temp_curr[msid][s], 0), 0)
                pend_used = min(pend_used, temp_pend_remain[msid][s])
                temp_pend_remain[msid][s] -= pend_used
                temp_curr[msid][s] -= a
            return allowed, changed

        # —— 常规出库（outbound_type in 1/2/3），全量、按出库时间升序（退回=4 不在限流范围）
        step_non_stock_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.unit_price,0),
                   COALESCE(d.size_34_outbound_amount,0), COALESCE(d.size_35_outbound_amount,0),
                   COALESCE(d.size_36_outbound_amount,0), COALESCE(d.size_37_outbound_amount,0),
                   COALESCE(d.size_38_outbound_amount,0), COALESCE(d.size_39_outbound_amount,0),
                   COALESCE(d.size_40_outbound_amount,0), COALESCE(d.size_41_outbound_amount,0),
                   COALESCE(d.size_42_outbound_amount,0), COALESCE(d.size_43_outbound_amount,0),
                   COALESCE(d.size_44_outbound_amount,0), COALESCE(d.size_45_outbound_amount,0),
                   COALESCE(d.size_46_outbound_amount,0),
                   r.outbound_type, r.outbound_datetime
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type IN (1,2,3)
            ORDER BY r.outbound_datetime ASC, d.id ASC
        """, sized_msids)

        for row in step_non_stock_rows:
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

        # —— 盘库出库（=5），全量、按出库时间升序
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
                   r.outbound_datetime
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type = 5
            ORDER BY r.outbound_datetime ASC, d.id ASC
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

        # === 出库聚合（storage 层；显示=1；按头表审批） ===
        pend_out_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
            GROUP BY d.material_storage_id
        """, sized_msids + list(PENDING_STATUSES))
        pend_out_total = {int(msid): Decimal(q or 0) for msid, q in pend_out_rows}

        appr_out_rows_types123 = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type IN (1,2,3)
            GROUP BY d.material_storage_id
        """, sized_msids)
        appr_out_total_types123 = {int(msid): Decimal(q or 0) for msid, q in appr_out_rows_types123}

        # 尺码层出库聚合（展示用，显示=1）
        pend_out_size_rows = fetchall(cur, f"""
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
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
            GROUP BY d.material_storage_id
        """, sized_msids + list(PENDING_STATUSES))

        appr_out_size_rows = fetchall(cur, f"""
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
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type IN (1,2,3)
            GROUP BY d.material_storage_id
        """, sized_msids)

        pend_out_size = {msid: blank_size_dict() for msid in sized_msids}
        appr_out_size = {msid: blank_size_dict() for msid in sized_msids}
        for row in pend_out_size_rows:
            _msid = int(row[0])
            for _s in range(MIN_SIZE, MAX_SIZE + 1):
                pend_out_size[_msid][_s] = Decimal(int(row[1 + (_s - MIN_SIZE)] or 0))
        for row in appr_out_size_rows:
            _msid = int(row[0])
            for _s in range(MIN_SIZE, MAX_SIZE + 1):
                appr_out_size[_msid][_s] = Decimal(int(row[1 + (_s - MIN_SIZE)] or 0))

        # 写入尺码明细表
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
                pending_outbound = pend_out_size[msid][col]
                inbound_amount_by_size = appr_in[msid][col]          # 仅 type=0
                outbound_amount_by_size = appr_out_size[msid][col]   # 仅 1/2/3
                current_amount_by_size = inbound_amount_by_size - outbound_amount_by_size
                cur.execute(
                    insert_sql,
                    (msid, str(size_val), idx,
                     pending_inbound, pending_outbound,
                     inbound_amount_by_size, outbound_amount_by_size, current_amount_by_size)
                )
                total_rows += 1
        conn.commit()
        print(f"✅ 尺码明细写入完成，共 {total_rows} 行。")

        # === 汇总回写 material_storage（★ 新口径） ===
        for msid in sized_msids:
            inbound_purchase = appr_in_purchase_total.get(msid, Decimal(0))
            return_out = appr_return_out_total.get(msid, Decimal(0))
            make_inv_in = appr_make_inv_in_total.get(msid, Decimal(0))
            make_inv_out = appr_make_inv_out_total.get(msid, Decimal(0))
            outbound_123 = appr_out_total.get(msid, Decimal(0))
            inbound_amount = inbound_purchase - return_out
            current_amount = inbound_amount - outbound_123 + make_inv_in - make_inv_out
            pending_inbound_sum = pend_in_total.get(msid, Decimal(0))
            pending_outbound_sum = pend_out_total.get(msid, Decimal(0))
            cur.execute("""
                UPDATE material_storage
                SET inbound_amount=%s,
                    outbound_amount=%s,
                    make_inventory_inbound=%s,
                    make_inventory_outbound=%s,
                    current_amount=%s,
                    pending_inbound=%s,
                    pending_outbound=%s
                WHERE material_storage_id=%s
            """, (inbound_amount, outbound_123, make_inv_in, make_inv_out,
                  current_amount, pending_inbound_sum, pending_outbound_sum, msid))
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
        print("\\n=== B) 不带尺码：入库聚合 → 出库限流(常规出库1/2/3) → storage聚合 ===")
        fmt_ids = ",".join(["%s"] * len(unsized_msids))

        # 入库聚合（★ 口径）
        appr_in_purchase_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.inbound_type = 0
            GROUP BY d.material_storage_id
        """, unsized_msids)
        appr_in_purchase = {int(msid): Decimal(q or 0) for msid, q in appr_in_purchase_rows}

        pend_in_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
              AND r.inbound_type IN (0,4)
            GROUP BY d.material_storage_id
        """, unsized_msids + list(PENDING_STATUSES))
        pend_in = {int(msid): Decimal(q or 0) for msid, q in pend_in_rows}

        appr_make_inv_in_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.inbound_amount,0))
            FROM inbound_record_detail d
            JOIN inbound_record r ON r.inbound_record_id = d.inbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.inbound_type = 4
            GROUP BY d.material_storage_id
        """, unsized_msids)
        appr_make_inv_in = {int(msid): Decimal(q or 0) for msid, q in appr_make_inv_in_rows}

        appr_return_out_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type = 4
            GROUP BY d.material_storage_id
        """, unsized_msids)
        appr_return_out = {int(msid): Decimal(q or 0) for msid, q in appr_return_out_rows}

        appr_make_inv_out_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type = 5
            GROUP BY d.material_storage_id
        """, unsized_msids)
        appr_make_inv_out = {int(msid): Decimal(q or 0) for msid, q in appr_make_inv_out_rows}

        appr_out_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type IN (1,2,3)
            GROUP BY d.material_storage_id
        """, unsized_msids)
        appr_out = {int(msid): Decimal(q or 0) for msid, q in appr_out_rows}

        # 限流（仅对 1/2/3）
        temp_curr = {msid: appr_in_purchase.get(msid, Decimal(0)) for msid in unsized_msids}
        temp_pend_remain = {msid: pend_in.get(msid, Decimal(0)) for msid in unsized_msids}
        header_ids_to_recalc = set()

        def cap_and_consume_unsized(msid, req_qty):
            cap = max(temp_curr.get(msid, Decimal(0)) + temp_pend_remain.get(msid, Decimal(0)), Decimal(0))
            allowed = min(Decimal(req_qty), cap)
            pend_used = max(allowed - max(temp_curr.get(msid, Decimal(0)), Decimal(0)), Decimal(0))
            pend_used = min(pend_used, temp_pend_remain.get(msid, Decimal(0)))
            temp_pend_remain[msid] = temp_pend_remain.get(msid, Decimal(0)) - pend_used
            temp_curr[msid] = temp_curr.get(msid, Decimal(0)) - allowed
            return allowed

        # 常规出库（outbound_type in 1/2/3），全量，按出库时间
        step_non_stock_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.outbound_amount,0), COALESCE(d.unit_price,0), r.outbound_type, r.outbound_datetime
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type IN (1,2,3)
            ORDER BY r.outbound_datetime ASC, d.id ASC
        """, unsized_msids)
        for d_id, hdr_id, msid, req, unit_price, _ob_type, _t in step_non_stock_rows:
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

        # 盘库（=5），全量，按出库时间
        stock_rows = fetchall(cur, f"""
            SELECT d.id, d.outbound_record_id, d.material_storage_id,
                   COALESCE(d.outbound_amount,0), COALESCE(d.unit_price,0), r.outbound_datetime
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status = 1 AND r.outbound_type = 5
            ORDER BY r.outbound_datetime ASC, d.id ASC
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

        # storage 层聚合（显示=1）
        pend_out_rows = fetchall(cur, f"""
            SELECT d.material_storage_id, SUM(COALESCE(d.outbound_amount,0))
            FROM outbound_record_detail d
            JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
            WHERE d.display = 1 AND r.display = 1
              AND d.material_storage_id IN ({fmt_ids})
              AND r.approval_status IN ({",".join(["%s"]*len(PENDING_STATUSES))})
            GROUP BY d.material_storage_id
        """, unsized_msids + list(PENDING_STATUSES))
        pend_out = {int(msid): Decimal(q or 0) for msid, q in pend_out_rows}

        for msid in unsized_msids:
            inbound_purchase = appr_in_purchase.get(msid, Decimal(0))
            return_out = appr_return_out.get(msid, Decimal(0))
            make_inv_in = appr_make_inv_in.get(msid, Decimal(0))
            make_inv_out = appr_make_inv_out.get(msid, Decimal(0))
            outbound_123 = appr_out.get(msid, Decimal(0))
            inbound_amount = inbound_purchase - return_out
            current_amount = inbound_amount - outbound_123 + make_inv_in - make_inv_out
            pending_inbound_sum = pend_in.get(msid, Decimal(0))
            pending_outbound_sum = pend_out.get(msid, Decimal(0))
            cur.execute("""
                UPDATE material_storage
                SET inbound_amount=%s,
                    outbound_amount=%s,
                    make_inventory_inbound=%s,
                    make_inventory_outbound=%s,
                    current_amount=%s,
                    pending_inbound=%s,
                    pending_outbound=%s
                WHERE material_storage_id=%s
            """, (inbound_amount, outbound_123, make_inv_in, make_inv_out,
                  current_amount, pending_inbound_sum, pending_outbound_sum, msid))
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

        # ------------- C) 步骤 5（仅不带尺码材料；保留原修正逻辑；显示=1 限制） -------------
        print("\\n=== C) 步骤 5：修正 pending_inbound>0 且 current<0 且二者不相反数的材料（仅不带尺码）===")
        fix_rows = fetchall(cur, f"""
            SELECT material_storage_id, inbound_amount, outbound_amount, pending_inbound, current_amount
            FROM material_storage
            WHERE material_storage_id IN ({fmt_ids})
              AND pending_inbound > 0
              AND current_amount < 0
              AND pending_inbound != -current_amount
        """, unsized_msids)
        fix_targets = [(int(msid), Decimal(inb or 0), Decimal(outb or 0),
                        Decimal(pend or 0), Decimal(curr or 0))
                       for msid, inb, outb, pend, curr in fix_rows]

        print(f"步骤 5 待处理 msid 数量：{len(fix_targets)}")
        for msid, inbound_amount, outbound_amount, pending_inbound, current_amount in fix_targets:
            delta = pending_inbound + current_amount  # 注意：current<0，pend>0
            if delta <= 0:
                print(f" - 跳过 msid={msid}：delta={delta} <= 0")
                continue

            candidate = fetchone(cur, f"""
                SELECT d.id, d.outbound_record_id, COALESCE(d.unit_price,0)
                FROM outbound_record_detail d
                JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
                WHERE d.display = 1 AND r.display = 1
                  AND d.material_storage_id = %s
                  AND COALESCE(d.outbound_amount,0) = 0
                  AND r.approval_status = 1
                  AND r.outbound_type IN (1,2,3)
                ORDER BY r.outbound_datetime DESC, d.id ASC
                LIMIT 1
            """, (msid,))

            if not candidate:
                candidate = fetchone(cur, f"""
                    SELECT d.id, d.outbound_record_id, COALESCE(d.unit_price,0)
                    FROM outbound_record_detail d
                    JOIN outbound_record r ON r.outbound_record_id = d.outbound_record_id
                    WHERE d.display = 1 AND r.display = 1
                      AND d.material_storage_id = %s
                      AND COALESCE(d.outbound_amount,0) = 0
                    ORDER BY r.outbound_datetime DESC, d.id ASC
                    LIMIT 1
                """, (msid,))

            if not candidate:
                print(f" ! 未找到 outbound_amount=0 的出库明细，msid={msid}，跳过")
                continue

            d_id, hdr_id, unit_price = int(candidate[0]), int(candidate[1]), Decimal(candidate[2] or 0)
            new_total = unit_price * delta

            cur.execute("""
                UPDATE outbound_record_detail
                SET outbound_amount=%s, item_total_price=%s
                WHERE id=%s
            """, (int(delta), new_total, d_id))

            cur.execute("""
                UPDATE outbound_record o
                SET o.total_price = (
                    SELECT COALESCE(SUM(COALESCE(d.item_total_price,0)), 0)
                    FROM outbound_record_detail d
                    WHERE d.outbound_record_id = o.outbound_record_id
                )
                WHERE o.outbound_record_id = %s
            """, (hdr_id,))

            # 同步 storage：相对修改（注意这里只修改 outbound_amount/current_amount；其他口径由整体聚合保障一致）
            cur.execute("""
                UPDATE material_storage
                SET outbound_amount = COALESCE(outbound_amount,0) + %s,
                    current_amount  = COALESCE(current_amount,0) - %s
                WHERE material_storage_id = %s
            """, (int(delta), int(delta), msid))
            conn.commit()

            print(f" ✓ 已处理 msid={msid}，detail_id={d_id}，delta={int(delta)}；"
                  f"outbound_amount += {int(delta)}，current_amount -= {int(delta)}")

    print("\\n✅ 全部完成（新口径，无 split_date，display=1，按出库时间）：")
    print(" - inbound_amount = 已审采购入库(type=0) - 已审材料退回(outbound_type=4)")
    print(" - outbound_amount = 已审常规出库(type in 1,2,3)")
    print(" - make_inventory_inbound/outbound = 已审盘库 in/out")
    print(" - current = inbound - outbound + make_inventory_in - make_inventory_out")
    print(" - storage 出库口径一律按明细 d.outbound_amount 聚合；尺码层仍按 size_*_*_amount 写回")
    print(" - 限流基数仅取已审采购入库(type=0)，未审入库作为上限补充")

    conn.close()


if __name__ == "__main__":
    main()

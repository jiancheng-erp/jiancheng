# merge_ms_balance_stock.py
# pip install pymysql
import pymysql

# === DB 连接 ===
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "jiancheng"

# === 主表与主键 ===
TABLE_MS = "material_storage"
PK_MS = "material_storage_id"           # material_storage 主键

# === 入库明细与父表 ===
DETAIL_TABLE = "inbound_record_detail"  # 明细表
DETAIL_MS_FK = "material_storage_id"    # 明细表里指向 material_storage 的外键列名
DETAIL_PARENT_FK = "inbound_record_id"  # 明细表里指向父表的外键列名
DETAIL_QTY_COL = "inbound_amount"                  # ✅ 明细数量列名（如 inbound_amount / amount）
DETAIL_PRICE_COL = "unit_price"         # ✅ 明细单价列名

PARENT_TABLE = "inbound_record"         # 父表
PARENT_PK = "inbound_record_id"
PARENT_APPROVAL_COL = "approval_status"
PARENT_APPROVED_VALUE = 1               # 已审核的值

# === 运行选项 ===
DRY_RUN = False                          # 先预览，确认后改为 False
ADD_UNIQUE_INDEX_AFTER = True           # 合并后添加唯一索引，防止再重复（含 NULL 也唯一）
UNIQUE_INDEX_MODE = "functional"  # 'generated_column' 或 'functional'(8.0.13+)

# === 需要合计的列（按需增删）===
SUM_COLS = ["inbound_amount", "current_amount"]
for size in range(34, 47):  # 34..46
    SUM_COLS.append(f"size_{size}_inbound_amount")
    SUM_COLS.append(f"size_{size}_current_amount")

def build_group_table_sql():
    # 关键：这里 GROUP BY 包含 order_id。对于 order_id IS NULL，MySQL 会把同值(都为 NULL)的行分到同一组，
    # => 同一 (NULL, spu, unit) 会被合并为一条“余量库存”。
    sum_selects = ",\n      ".join([f"SUM(COALESCE(`{col}`,0)) AS `sum__{col}`" for col in SUM_COLS])
    return f"""
    CREATE TEMPORARY TABLE `ms_groups` AS
    SELECT
      `order_id`,
      `spu_material_id`,
      `actual_inbound_unit`,
      MIN(`{PK_MS}`) AS `keeper_id`,   -- 每组保留最小ID
      {sum_selects},
      COUNT(*) AS `cnt`
    FROM `{TABLE_MS}`
    GROUP BY `order_id`, `spu_material_id`, `actual_inbound_unit`
    HAVING COUNT(*) > 1
    """

def build_update_keeper_sql():
    set_clause = ",\n    ".join([f"k.`{col}` = g.`sum__{col}`" for col in SUM_COLS])
    return f"""
    UPDATE `{TABLE_MS}` k
    JOIN `ms_groups` g ON k.`{PK_MS}` = g.`keeper_id`
    SET
    {set_clause}
    """

def add_unique_index(cur):
    if not ADD_UNIQUE_INDEX_AFTER:
        return
    if UNIQUE_INDEX_MODE == "generated_column":
        # 生成列把 NULL→0，再在 (order_id_norm, spu, unit) 上建唯一索引
        try:
            cur.execute("""
                ALTER TABLE `material_storage`
                ADD COLUMN `order_id_norm` BIGINT
                  GENERATED ALWAYS AS (IFNULL(`order_id`, 0)) STORED
            """)
        except Exception as e:
            print(f"[提示] order_id_norm 可能已存在：{e}")
        try:
            cur.execute("""
                ALTER TABLE `material_storage`
                ADD UNIQUE KEY `uk_order_spu_unit_norm`
                  (`order_id_norm`, `spu_material_id`, `actual_inbound_unit`)
            """)
            print("唯一索引 uk_order_spu_unit_norm 创建成功（确保 NULL 订单的每个 (spu,unit) 仅一条）")
        except Exception as e:
            print(f"[提示] 唯一索引未创建（可能已存在）：{e}")

    elif UNIQUE_INDEX_MODE == "functional":
        try:
            cur.execute("""
                CREATE UNIQUE INDEX `uk_order_spu_unit_fn`
                ON `material_storage` ((IFNULL(`order_id`, 0)), `spu_material_id`, `actual_inbound_unit`)
            """)
            print("唯一索引 uk_order_spu_unit_fn 创建成功")
        except Exception as e:
            print(f"[提示] 唯一索引未创建（可能已存在或版本不支持）：{e}")

def main():
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4", autocommit=False
    )
    try:
        with conn.cursor() as cur:
            # 预览：重复组数（含 NULL 订单组）
            cur.execute(f"""
                SELECT COUNT(*) FROM (
                  SELECT 1
                  FROM `{TABLE_MS}`
                  GROUP BY `order_id`, `spu_material_id`, `actual_inbound_unit`
                  HAVING COUNT(*) > 1
                ) x
            """)
            groups = cur.fetchone()[0]

            # 预览：组内总行数
            cur.execute(f"""
                SELECT COUNT(*) FROM `{TABLE_MS}` t
                JOIN (
                  SELECT `order_id`, `spu_material_id`, `actual_inbound_unit`
                  FROM `{TABLE_MS}`
                  GROUP BY `order_id`, `spu_material_id`, `actual_inbound_unit`
                  HAVING COUNT(*) > 1
                ) d
                  ON d.`order_id` = t.`order_id`
                 AND d.`spu_material_id` = t.`spu_material_id`
                 AND d.`actual_inbound_unit` = t.`actual_inbound_unit`
            """)
            rows_in_groups = cur.fetchone()[0]

            print(f"[预览] 重复组数: {groups}, 组内总行数: {rows_in_groups}")
            if groups == 0:
                print("没有发现需要合并的组（包含 NULL 订单余量），退出。")
                conn.rollback()
                return

            if DRY_RUN:
                print("DRY_RUN=True，仅预览，不做修改。确认后把 DRY_RUN 设为 False。")
                conn.rollback()
                return

            # 1) 生成重复组汇总表（同一 (order_id, spu, unit) —— 含 NULL 订单）
            cur.execute("DROP TEMPORARY TABLE IF EXISTS `ms_groups`")
            cur.execute(build_group_table_sql())
            print("步骤1：生成 ms_groups 完成")

            # 2) old_id -> keeper_id 映射（不含保留行）
            cur.execute("DROP TEMPORARY TABLE IF EXISTS `ms_mapping`")
            cur.execute(f"""
                CREATE TEMPORARY TABLE `ms_mapping` AS
                SELECT ms.`{PK_MS}` AS `old_id`, g.`keeper_id`
                FROM `{TABLE_MS}` ms
                JOIN `ms_groups` g
                  ON ( (ms.`order_id` <=> g.`order_id`)   -- <=> 安全等值，NULL==NULL
                   AND ms.`spu_material_id` = g.`spu_material_id`
                   AND ms.`actual_inbound_unit` = g.`actual_inbound_unit`)
                WHERE ms.`{PK_MS}` <> g.`keeper_id`
            """)
            print("步骤2：生成 ms_mapping 完成")

            # 3) 把合计写回保留行（数量类字段汇总）
            cur.execute(build_update_keeper_sql())
            print("步骤3：回写合计到保留行 完成")

            # 4) 把所有明细的 FK 指向 keeper（包括 NULL 订单的余量库存对应的明细）
            cur.execute(f"""
                UPDATE `{DETAIL_TABLE}` det
                JOIN `ms_mapping` m ON det.`{DETAIL_MS_FK}` = m.`old_id`
                SET det.`{DETAIL_MS_FK}` = m.`keeper_id`
            """)
            print("步骤4：更新 inbound_record_detail 外键 完成")

            # 5a) 统计“已审核”明细的加权平均单价（仅对本次合并后的 keeper）
            cur.execute("DROP TEMPORARY TABLE IF EXISTS `ms_avg_price`")
            cur.execute(f"""
                CREATE TEMPORARY TABLE `ms_avg_price` AS
                SELECT
                  det.`{DETAIL_MS_FK}` AS `target_id`,
                  SUM(COALESCE(det.`{DETAIL_QTY_COL}`,0) * COALESCE(det.`{DETAIL_PRICE_COL}`,0)) AS `sum_amount`,
                  SUM(COALESCE(det.`{DETAIL_QTY_COL}`,0)) AS `sum_qty`
                FROM `{DETAIL_TABLE}` det
                JOIN `{PARENT_TABLE}` ir
                     ON ir.`{PARENT_PK}` = det.`{DETAIL_PARENT_FK}`
                    AND ir.`{PARENT_APPROVAL_COL}` = {PARENT_APPROVED_VALUE}
                JOIN `ms_groups` g
                     ON g.`keeper_id` = det.`{DETAIL_MS_FK}`
                GROUP BY det.`{DETAIL_MS_FK}`
                HAVING SUM(COALESCE(det.`{DETAIL_QTY_COL}`,0)) > 0
            """)
            print("步骤5a：统计已审核明细的加权平均单价 完成")

            # 5b) 用加权平均更新 keeper 的 average_price
            cur.execute(f"""
                UPDATE `{TABLE_MS}` k
                JOIN `ms_avg_price` a ON a.`target_id` = k.`{PK_MS}`
                SET k.`average_price` = ROUND(a.`sum_amount` / NULLIF(a.`sum_qty`, 0), 4)
            """)
            print("步骤5b：更新 keeper 的 average_price 完成")

            # 6) 删除多余行（包括 NULL 订单余量的多余行）
            cur.execute(f"""
                DELETE ms
                FROM `{TABLE_MS}` ms
                JOIN `ms_mapping` m ON ms.`{PK_MS}` = m.`old_id`
            """)
            print("步骤6：删除多余重复行 完成")

            # 7) 加唯一索引：确保“order_id 为 NULL 的每个 (spu, unit) 永远只有一条余量库存”
            add_unique_index(cur)

        conn.commit()
        print("✔ 合并完成并已提交。")

    except Exception as e:
        conn.rollback()
        print("✖ 出错，已回滚：", e)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()

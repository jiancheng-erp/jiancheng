# -*- coding: utf-8 -*-
"""
month_end_snapshot.py (v3, add outbound_amount columns)

一次性生成：
  1) material_storage_snapshot
  2) material_storage_size_detail_snapshot

口径：
- 边界：当日结束（< DATE_ADD(:d, INTERVAL 1 DAY)）
- 审核：已审核(=1) -> inbound_amount/outbound_amount/current_amount；待审与驳回(0/2) -> pending_inbound/pending_outbound
- 最新单价：截至当日最后一笔【已审核=1】入库单价
- 平均价：截至当日【已审核=1】入库加权平均(总金额/总数量)
- 尺码明细：严格以实时表 material_storage_size_detail 的 (msid, order_number, id) 为准
- size_detail_id = material_storage_size_detail.id 直接沿用主键
- 规则：若某 material_storage 在「首次入库(不限审核状态)」至 snapshot_date 期间完全没有任何入库记录，
        则本次不向两张快照表写入该 msid。
"""
from sqlalchemy import create_engine, text
from flask import Flask

# --------------------- DB CONFIG (standalone 可改) ---------------------
DB_USER = "root"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "jiancheng"
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


def generate_month_end_snapshot(app, db, snapshot_date: str):
    """
    生成指定 snapshot_date (YYYY-MM-DD) 的两张月末快照。
    支持重复执行（先删后插）。
    """
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            print(f"🧮 Building month-end snapshots for {snapshot_date} (end-of-day bound).")

            # 1) 清理当日旧数据
            conn.execute(text("DELETE FROM material_storage_size_detail_snapshot WHERE snapshot_date = :d;"),
                         {"d": snapshot_date})
            conn.execute(text("DELETE FROM material_storage_snapshot WHERE snapshot_date = :d;"),
                         {"d": snapshot_date})

            # 2) 丢弃残留临表
            for tmp in [
                "tmp_in_approved", "tmp_in_pending",
                "tmp_out_approved", "tmp_out_pending",
                "tmp_latest_price", "tmp_keys",
                "tmp_size_keys",
                "tmp_size_in_appr", "tmp_size_in_pend",
                "tmp_size_out_appr", "tmp_size_out_pend",
            ]:
                conn.execute(text(f"DROP TEMPORARY TABLE IF EXISTS {tmp}"))

            # 3) 最新已审核单价（截至当日）
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_latest_price AS
                WITH ranked AS (
                  SELECT
                    ird.material_storage_id,
                    ird.unit_price,
                    ROW_NUMBER() OVER (
                      PARTITION BY ird.material_storage_id
                      ORDER BY ir.inbound_datetime DESC, ird.id DESC
                    ) rn
                  FROM inbound_record_detail ird
                  JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
                  WHERE ir.approval_status = 1
                    AND ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                )
                SELECT material_storage_id, unit_price AS latest_unit_price
                FROM ranked WHERE rn = 1;
            """), {"d": snapshot_date})

            # 4) 总量聚合：入（已=1 / 待审+驳回=0,2）与出（已=1 / 待审+驳回=0,2）
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_in_approved AS
                SELECT
                  ird.material_storage_id,
                  SUM(ird.inbound_amount) AS total_inbound,
                  SUM(ird.inbound_amount * ird.unit_price) AS total_inbound_value
                FROM inbound_record_detail ird
                JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
                WHERE ir.approval_status = 1
                  AND ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                GROUP BY ird.material_storage_id;
            """), {"d": snapshot_date})

            # 待审+驳回 (0,2) 计入 pending_inbound
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_in_pending AS
                SELECT
                  ird.material_storage_id,
                  SUM(ird.inbound_amount) AS pending_inbound
                FROM inbound_record_detail ird
                JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
                WHERE ir.approval_status IN (0, 2)
                  AND ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                GROUP BY ird.material_storage_id;
            """), {"d": snapshot_date})

            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_out_approved AS
                SELECT
                  ord.material_storage_id,
                  SUM(ord.outbound_amount) AS total_outbound
                FROM outbound_record_detail ord
                JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
                WHERE o.approval_status = 1
                  AND o.outbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                GROUP BY ord.material_storage_id;
            """), {"d": snapshot_date})

            # 待审+驳回 (0,2) 计入 pending_outbound
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_out_pending AS
                SELECT
                  ord.material_storage_id,
                  SUM(ord.outbound_amount) AS pending_outbound
                FROM outbound_record_detail ord
                JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
                WHERE o.approval_status IN (0, 2)
                  AND o.outbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                GROUP BY ord.material_storage_id;
            """), {"d": snapshot_date})

            # 5) 物料 key 集（仅限「截至当日曾经有过任意入库记录」的 material_storage）
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_keys AS
                SELECT DISTINCT ird.material_storage_id
                FROM inbound_record_detail ird
                JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
                WHERE ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY);
            """), {"d": snapshot_date})

            # 6) 写入 material_storage_snapshot（新增 outbound_amount 列）
            conn.execute(text("""
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
                    COALESCE(pin.pending_inbound, 0),
                    COALESCE(pout.pending_outbound, 0),
                    COALESCE(ia.total_inbound, 0) AS inbound_amount,
                    COALESCE(oa.total_outbound, 0) AS outbound_amount,
                    COALESCE(ia.total_inbound, 0) - COALESCE(oa.total_outbound, 0) AS current_amount,
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
                JOIN material_storage ms ON ms.material_storage_id = k.material_storage_id
                LEFT JOIN tmp_in_approved ia ON ia.material_storage_id = ms.material_storage_id
                LEFT JOIN tmp_out_approved oa ON oa.material_storage_id = ms.material_storage_id
                LEFT JOIN tmp_in_pending pin ON pin.material_storage_id = ms.material_storage_id
                LEFT JOIN tmp_out_pending pout ON pout.material_storage_id = ms.material_storage_id
                LEFT JOIN tmp_latest_price lp ON lp.material_storage_id = ms.material_storage_id;
            """), {"d": snapshot_date})

            # 7) 尺码 key（仅限 tmp_keys 中的 msid）
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_size_keys AS
                SELECT
                  msd.id               AS size_detail_id,
                  msd.material_storage_id,
                  msd.order_number,
                  msd.size_value
                FROM material_storage_size_detail msd
                JOIN tmp_keys k ON k.material_storage_id = msd.material_storage_id;
            """))

            # 8) 尺码维度聚合（已=1 / 待审+驳回=0,2）
            # 已审核入库
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_size_in_appr AS
                SELECT
                  t.material_storage_id,
                  t.order_number,
                  SUM(
                    CASE t.order_number
                      WHEN 0  THEN COALESCE(ird.size_34_inbound_amount,0)
                      WHEN 1  THEN COALESCE(ird.size_35_inbound_amount,0)
                      WHEN 2  THEN COALESCE(ird.size_36_inbound_amount,0)
                      WHEN 3  THEN COALESCE(ird.size_37_inbound_amount,0)
                      WHEN 4  THEN COALESCE(ird.size_38_inbound_amount,0)
                      WHEN 5  THEN COALESCE(ird.size_39_inbound_amount,0)
                      WHEN 6  THEN COALESCE(ird.size_40_inbound_amount,0)
                      WHEN 7  THEN COALESCE(ird.size_41_inbound_amount,0)
                      WHEN 8  THEN COALESCE(ird.size_42_inbound_amount,0)
                      WHEN 9  THEN COALESCE(ird.size_43_inbound_amount,0)
                      WHEN 10 THEN COALESCE(ird.size_44_inbound_amount,0)
                      WHEN 11 THEN COALESCE(ird.size_45_inbound_amount,0)
                      WHEN 12 THEN COALESCE(ird.size_46_inbound_amount,0)
                    END
                  ) AS inbound_amount_n
                FROM inbound_record_detail ird
                JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
                JOIN tmp_size_keys t ON t.material_storage_id = ird.material_storage_id
                WHERE ir.approval_status = 1
                  AND ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                GROUP BY t.material_storage_id, t.order_number;
            """), {"d": snapshot_date})

            # 待审+驳回入库 → pending_inbound_n
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_size_in_pend AS
                SELECT
                  t.material_storage_id,
                  t.order_number,
                  SUM(
                    CASE t.order_number
                      WHEN 0  THEN COALESCE(ird.size_34_inbound_amount,0)
                      WHEN 1  THEN COALESCE(ird.size_35_inbound_amount,0)
                      WHEN 2  THEN COALESCE(ird.size_36_inbound_amount,0)
                      WHEN 3  THEN COALESCE(ird.size_37_inbound_amount,0)
                      WHEN 4  THEN COALESCE(ird.size_38_inbound_amount,0)
                      WHEN 5  THEN COALESCE(ird.size_39_inbound_amount,0)
                      WHEN 6  THEN COALESCE(ird.size_40_inbound_amount,0)
                      WHEN 7  THEN COALESCE(ird.size_41_inbound_amount,0)
                      WHEN 8  THEN COALESCE(ird.size_42_inbound_amount,0)
                      WHEN 9  THEN COALESCE(ird.size_43_inbound_amount,0)
                      WHEN 10 THEN COALESCE(ird.size_44_inbound_amount,0)
                      WHEN 11 THEN COALESCE(ird.size_45_inbound_amount,0)
                      WHEN 12 THEN COALESCE(ird.size_46_inbound_amount,0)
                    END
                  ) AS pending_inbound_n
                FROM inbound_record_detail ird
                JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
                JOIN tmp_size_keys t ON t.material_storage_id = ird.material_storage_id
                WHERE ir.approval_status IN (0, 2)
                  AND ir.inbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                GROUP BY t.material_storage_id, t.order_number;
            """), {"d": snapshot_date})

            # 已审核出库
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_size_out_appr AS
                SELECT
                  t.material_storage_id,
                  t.order_number,
                  SUM(
                    CASE t.order_number
                      WHEN 0  THEN COALESCE(ord.size_34_outbound_amount,0)
                      WHEN 1  THEN COALESCE(ord.size_35_outbound_amount,0)
                      WHEN 2  THEN COALESCE(ord.size_36_outbound_amount,0)
                      WHEN 3  THEN COALESCE(ord.size_37_outbound_amount,0)
                      WHEN 4  THEN COALESCE(ord.size_38_outbound_amount,0)
                      WHEN 5  THEN COALESCE(ord.size_39_outbound_amount,0)
                      WHEN 6  THEN COALESCE(ord.size_40_outbound_amount,0)
                      WHEN 7  THEN COALESCE(ord.size_41_outbound_amount,0)
                      WHEN 8  THEN COALESCE(ord.size_42_outbound_amount,0)
                      WHEN 9  THEN COALESCE(ord.size_43_outbound_amount,0)
                      WHEN 10 THEN COALESCE(ord.size_44_outbound_amount,0)
                      WHEN 11 THEN COALESCE(ord.size_45_outbound_amount,0)
                      WHEN 12 THEN COALESCE(ord.size_46_outbound_amount,0)
                    END
                  ) AS outbound_amount_n
                FROM outbound_record_detail ord
                JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
                JOIN tmp_size_keys t ON t.material_storage_id = ord.material_storage_id
                WHERE o.approval_status = 1
                  AND o.outbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                GROUP BY t.material_storage_id, t.order_number;
            """), {"d": snapshot_date})

            # 待审+驳回出库 → pending_outbound_n
            conn.execute(text("""
                CREATE TEMPORARY TABLE tmp_size_out_pend AS
                SELECT
                  t.material_storage_id,
                  t.order_number,
                  SUM(
                    CASE t.order_number
                      WHEN 0  THEN COALESCE(ord.size_34_outbound_amount,0)
                      WHEN 1  THEN COALESCE(ord.size_35_outbound_amount,0)
                      WHEN 2  THEN COALESCE(ord.size_36_outbound_amount,0)
                      WHEN 3  THEN COALESCE(ord.size_37_outbound_amount,0)
                      WHEN 4  THEN COALESCE(ord.size_38_outbound_amount,0)
                      WHEN 5  THEN COALESCE(ord.size_39_outbound_amount,0)
                      WHEN 6  THEN COALESCE(ord.size_40_outbound_amount,0)
                      WHEN 7  THEN COALESCE(ord.size_41_outbound_amount,0)
                      WHEN 8  THEN COALESCE(ord.size_42_outbound_amount,0)
                      WHEN 9  THEN COALESCE(ord.size_43_outbound_amount,0)
                      WHEN 10 THEN COALESCE(ord.size_44_outbound_amount,0)
                      WHEN 11 THEN COALESCE(ord.size_45_outbound_amount,0)
                      WHEN 12 THEN COALESCE(ord.size_46_outbound_amount,0)
                    END
                  ) AS pending_outbound_n
                FROM outbound_record_detail ord
                JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
                JOIN tmp_size_keys t ON t.material_storage_id = ord.material_storage_id
                WHERE o.approval_status IN (0, 2)
                  AND o.outbound_datetime < DATE_ADD(:d, INTERVAL 1 DAY)
                GROUP BY t.material_storage_id, t.order_number;
            """), {"d": snapshot_date})

            # 9) 写入 material_storage_size_detail_snapshot（新增 outbound_amount 列）
            conn.execute(text("""
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
                    COALESCE(ai.inbound_amount_n, 0) AS inbound_amount,
                    COALESCE(ao.outbound_amount_n, 0) AS outbound_amount,
                    COALESCE(ai.inbound_amount_n, 0) - COALESCE(ao.outbound_amount_n, 0) AS current_amount
                FROM tmp_size_keys t
                LEFT JOIN tmp_size_in_appr ai
                  ON ai.material_storage_id = t.material_storage_id AND ai.order_number = t.order_number
                LEFT JOIN tmp_size_out_appr ao
                  ON ao.material_storage_id = t.material_storage_id AND ao.order_number = t.order_number
                LEFT JOIN tmp_size_in_pend pi
                  ON pi.material_storage_id = t.material_storage_id AND pi.order_number = t.order_number
                LEFT JOIN tmp_size_out_pend po
                  ON po.material_storage_id = t.material_storage_id AND po.order_number = t.order_number;
            """), {"d": snapshot_date})

            trans.commit()
            print(f"✅ Month-end snapshots done for {snapshot_date}.")

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

    # 示例：生成若干月末快照
    for date in ["2025-03-31", "2025-04-30", "2025-05-31", "2025-06-30", "2025-07-31", "2025-08-31", "2025-09-30", "2025-10-31"]:
        generate_month_end_snapshot(app, db, date)

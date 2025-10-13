from sqlalchemy import text, create_engine
from flask import Flask

# =====================================================
# 🧩 Database configuration (edit as needed)
# =====================================================
DB_USER = "root"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "jiancheng"

DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


# =====================================================
# 🧩 Snapshot generation function
# =====================================================
def generate_material_storage_snapshot(app, db, snapshot_date: str):
    """
    Generate material_storage_snapshot data up to (and including) snapshot_date.

    Changes in this version:
      - End-of-day bound fixed: uses < DATE_ADD(:snapshot_date, INTERVAL 1 DAY)
        so all inbounds/outbounds on the snapshot_date are included.

    Pricing rules:
      - unit_price     = the latest inbound unit price on/before snapshot_date
      - average_price  = weighted average = sum(inbound_amount * unit_price) / sum(inbound_amount)

    Notes:
      - Groups by material_storage_id only (no size_storage coalesce).
      - Outbound-only materials will not be inserted (unchanged by request).
    """
    with app.app_context():
        print(f"📦 Starting material snapshot generation for {snapshot_date}...")

        connection = db.engine.connect()
        trans = connection.begin()

        try:
            # Clean any leftover temp tables (same connection)
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS tmp_inbound_sum"))
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS tmp_outbound_sum"))

            # ========== Step 1. Aggregate INBOUND up to end of snapshot day ==========
            print("▶️ Aggregating inbound data (latest price + weighted average, end-of-day bound)...")
            inbound_sql = text("""
                CREATE TEMPORARY TABLE tmp_inbound_sum AS
                WITH latest_inbound AS (
                    SELECT
                        ird.material_storage_id,
                        ird.unit_price AS latest_unit_price,
                        ROW_NUMBER() OVER (
                            PARTITION BY ird.material_storage_id
                            ORDER BY ir.inbound_datetime DESC, ird.id DESC
                        ) AS rn
                    FROM inbound_record_detail ird
                    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
                    WHERE ir.inbound_datetime < DATE_ADD(:snapshot_date, INTERVAL 1 DAY)
                ),
                inbound_agg AS (
                    SELECT
                        ird.material_storage_id,
                        MAX(ird.spu_material_id) AS spu_material_id,
                        MAX(ird.order_id) AS order_id,
                        SUM(ird.inbound_amount) AS total_inbound,
                        SUM(ird.inbound_amount * ird.unit_price) AS total_inbound_value,
                        SUM(COALESCE(ird.size_34_inbound_amount,0)) AS size_34,
                        SUM(COALESCE(ird.size_35_inbound_amount,0)) AS size_35,
                        SUM(COALESCE(ird.size_36_inbound_amount,0)) AS size_36,
                        SUM(COALESCE(ird.size_37_inbound_amount,0)) AS size_37,
                        SUM(COALESCE(ird.size_38_inbound_amount,0)) AS size_38,
                        SUM(COALESCE(ird.size_39_inbound_amount,0)) AS size_39,
                        SUM(COALESCE(ird.size_40_inbound_amount,0)) AS size_40,
                        SUM(COALESCE(ird.size_41_inbound_amount,0)) AS size_41,
                        SUM(COALESCE(ird.size_42_inbound_amount,0)) AS size_42,
                        SUM(COALESCE(ird.size_43_inbound_amount,0)) AS size_43,
                        SUM(COALESCE(ird.size_44_inbound_amount,0)) AS size_44,
                        SUM(COALESCE(ird.size_45_inbound_amount,0)) AS size_45,
                        SUM(COALESCE(ird.size_46_inbound_amount,0)) AS size_46
                    FROM inbound_record_detail ird
                    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
                    WHERE ir.inbound_datetime < DATE_ADD(:snapshot_date, INTERVAL 1 DAY)
                    GROUP BY ird.material_storage_id
                )
                SELECT
                    ia.material_storage_id,
                    ia.spu_material_id,
                    ia.order_id,
                    ia.total_inbound,
                    ia.total_inbound_value,
                    CASE WHEN ia.total_inbound > 0
                         THEN ia.total_inbound_value / ia.total_inbound ELSE 0 END AS average_price,
                    li.latest_unit_price,
                    ia.size_34, ia.size_35, ia.size_36, ia.size_37, ia.size_38, ia.size_39,
                    ia.size_40, ia.size_41, ia.size_42, ia.size_43, ia.size_44, ia.size_45, ia.size_46
                FROM inbound_agg ia
                LEFT JOIN (
                    SELECT material_storage_id, latest_unit_price
                    FROM latest_inbound
                    WHERE rn = 1
                ) li ON ia.material_storage_id = li.material_storage_id
            """)
            connection.execute(inbound_sql, {"snapshot_date": snapshot_date})
            inbound_count = connection.execute(text("SELECT COUNT(*) FROM tmp_inbound_sum")).scalar()
            print(f"✅ Inbound aggregation done. Rows: {inbound_count}")

            # ========== Step 2. Aggregate OUTBOUND up to end of snapshot day ==========
            print("▶️ Aggregating outbound data (end-of-day bound)...")
            outbound_sql = text("""
                CREATE TEMPORARY TABLE tmp_outbound_sum AS
                SELECT
                    ord.material_storage_id,
                    SUM(COALESCE(ord.outbound_amount,0)) AS total_outbound,
                    SUM(COALESCE(ord.size_34_outbound_amount,0)) AS size_34,
                    SUM(COALESCE(ord.size_35_outbound_amount,0)) AS size_35,
                    SUM(COALESCE(ord.size_36_outbound_amount,0)) AS size_36,
                    SUM(COALESCE(ord.size_37_outbound_amount,0)) AS size_37,
                    SUM(COALESCE(ord.size_38_outbound_amount,0)) AS size_38,
                    SUM(COALESCE(ord.size_39_outbound_amount,0)) AS size_39,
                    SUM(COALESCE(ord.size_40_outbound_amount,0)) AS size_40,
                    SUM(COALESCE(ord.size_41_outbound_amount,0)) AS size_41,
                    SUM(COALESCE(ord.size_42_outbound_amount,0)) AS size_42,
                    SUM(COALESCE(ord.size_43_outbound_amount,0)) AS size_43,
                    SUM(COALESCE(ord.size_44_outbound_amount,0)) AS size_44,
                    SUM(COALESCE(ord.size_45_outbound_amount,0)) AS size_45,
                    SUM(COALESCE(ord.size_46_outbound_amount,0)) AS size_46
                FROM outbound_record_detail ord
                JOIN outbound_record o ON o.outbound_record_id = ord.outbound_record_id
                WHERE o.outbound_datetime < DATE_ADD(:snapshot_date, INTERVAL 1 DAY)
                GROUP BY ord.material_storage_id
            """)
            connection.execute(outbound_sql, {"snapshot_date": snapshot_date})
            outbound_count = connection.execute(text("SELECT COUNT(*) FROM tmp_outbound_sum")).scalar()
            print(f"✅ Outbound aggregation done. Rows: {outbound_count}")

            # ========== Step 3. Merge inbound and outbound results ==========
            print("▶️ Computing net balances and inserting snapshot rows (with actual_inbound_unit)...")

            merge_sql = text("""
                INSERT INTO material_storage_snapshot (
                    snapshot_date,
                    material_storage_id,
                    order_id,
                    order_shoe_id,
                    spu_material_id,
                    actual_inbound_unit,
                    inbound_amount,
                    current_amount,
                    unit_price,
                    average_price,
                    size_34_current_amount,
                    size_35_current_amount,
                    size_36_current_amount,
                    size_37_current_amount,
                    size_38_current_amount,
                    size_39_current_amount,
                    size_40_current_amount,
                    size_41_current_amount,
                    size_42_current_amount,
                    size_43_current_amount,
                    size_44_current_amount,
                    size_45_current_amount,
                    size_46_current_amount,
                    size_34_inbound_amount,
                    size_35_inbound_amount,
                    size_36_inbound_amount,
                    size_37_inbound_amount,
                    size_38_inbound_amount,
                    size_39_inbound_amount,
                    size_40_inbound_amount,
                    size_41_inbound_amount,
                    size_42_inbound_amount,
                    size_43_inbound_amount,
                    size_44_inbound_amount,
                    size_45_inbound_amount,
                    size_46_inbound_amount
                )
                SELECT
                    :snapshot_date,
                    ib.material_storage_id,
                    ib.order_id,
                    NULL,
                    ib.spu_material_id,
                    COALESCE(ms.actual_inbound_unit, 'PCS'),
                    COALESCE(ib.total_inbound, 0),
                    COALESCE(ib.total_inbound,0) - COALESCE(ob.total_outbound,0),
                    COALESCE(ib.latest_unit_price, 0),
                    COALESCE(ib.average_price, 0),
                    COALESCE(ib.size_34,0) - COALESCE(ob.size_34,0),
                    COALESCE(ib.size_35,0) - COALESCE(ob.size_35,0),
                    COALESCE(ib.size_36,0) - COALESCE(ob.size_36,0),
                    COALESCE(ib.size_37,0) - COALESCE(ob.size_37,0),
                    COALESCE(ib.size_38,0) - COALESCE(ob.size_38,0),
                    COALESCE(ib.size_39,0) - COALESCE(ob.size_39,0),
                    COALESCE(ib.size_40,0) - COALESCE(ob.size_40,0),
                    COALESCE(ib.size_41,0) - COALESCE(ob.size_41,0),
                    COALESCE(ib.size_42,0) - COALESCE(ob.size_42,0),
                    COALESCE(ib.size_43,0) - COALESCE(ob.size_43,0),
                    COALESCE(ib.size_44,0) - COALESCE(ob.size_44,0),
                    COALESCE(ib.size_45,0) - COALESCE(ob.size_45,0),
                    COALESCE(ib.size_46,0) - COALESCE(ob.size_46,0),
                    COALESCE(ib.size_34,0),
                    COALESCE(ib.size_35,0),
                    COALESCE(ib.size_36,0),
                    COALESCE(ib.size_37,0),
                    COALESCE(ib.size_38,0),
                    COALESCE(ib.size_39,0),
                    COALESCE(ib.size_40,0),
                    COALESCE(ib.size_41,0),
                    COALESCE(ib.size_42,0),
                    COALESCE(ib.size_43,0),
                    COALESCE(ib.size_44,0),
                    COALESCE(ib.size_45,0),
                    COALESCE(ib.size_46,0)
                FROM tmp_inbound_sum ib
                LEFT JOIN tmp_outbound_sum ob
                  ON ib.material_storage_id = ob.material_storage_id
                LEFT JOIN material_storage ms
                  ON ms.material_storage_id = ib.material_storage_id
            """)
            result = connection.execute(merge_sql, {"snapshot_date": snapshot_date})
            inserted = getattr(result, "rowcount", None)
            print(f"✅ Snapshot data inserted successfully. Rows inserted: {inserted if inserted is not None else 'N/A'}")

            # Commit
            trans.commit()
            print(f"🎉 Snapshot generation complete for {snapshot_date}!")

        except Exception as e:
            trans.rollback()
            print("❌ Error occurred during snapshot generation:")
            print(e)
        finally:
            connection.close()


# =====================================================
# 🧩 Standalone execution (optional)
# =====================================================
if __name__ == "__main__":
    print(f"Using DB_URL: {DB_URL}")
    app = Flask(__name__)

    # Create engine & minimal wrapper with .engine to match expected interface
    engine = create_engine(DB_URL)

    class DBWrapper:
        def __init__(self, engine):
            self.engine = engine

    db = DBWrapper(engine)

    # Example usage:
    generate_material_storage_snapshot(app, db, "2025-03-31")

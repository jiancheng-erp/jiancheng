from apscheduler.schedulers.background import BackgroundScheduler
from wechat_api.auto_send_wechat_message_on_time import *
from datetime import date, timedelta


# 启动调度器函数（在主程序中调用）
def start_scheduler(app):
    scheduler = BackgroundScheduler()
    # scheduler.add_job(
    #     func=send_message_to_all,
    #     trigger='cron',
    #     hour=9, minute=0,
    #     args=[app],
    #     id='morning_status_message'
    # )
    # scheduler.add_job(
    #     func=send_message_to_all,
    #     trigger='cron',
    #     hour=12, minute=0,
    #     args=[app],
    #     id='noon_status_message'
    # )
    # scheduler.add_job(
    #     func=send_message_to_all,
    #     trigger='cron',
    #     hour=18, minute=0,
    #     args=[app],
    #     id='evening_status_message'
    # )
    # scheduler.add_job(
    #     func=send_message_to_production,
    #     trigger='cron',
    #     hour=9, minute=0,
    #     args=[app],
    #     id='production_morning_status_message'
    # )
    # scheduler.add_job(
    #     func=send_message_to_production,
    #     trigger='cron',
    #     hour=12, minute=0,
    #     args=[app],
    #     id='production_noon_status_message'
    # )
    # scheduler.add_job(
    #     func=send_message_to_production,
    #     trigger='cron',
    #     hour=18, minute=0,
    #     args=[app],
    #     id='production_evening_status_message'
    # )
    scheduler.add_job(
        func=snapshot_material_storage,
        trigger="cron",
        minute="*",
        second=0,  # 或者 second='0'
        args=[app],
        id="material_storage_snapshot",
        replace_existing=True,
    )
    scheduler.add_job(
        func=snapshot_daily_storage_change,
        trigger="cron",
        minute="*",
        second=30,  # 或者 second='30'
        args=[app],
        id="daily_storage_change_snapshot",
        replace_existing=True,
    )
    scheduler.start()


def snapshot_daily_storage_change(app):
    with app.app_context():
        sql = text(
            """
            -- 先把查询版改成只按 (snapshot_date, material_storage_id) 聚合的派生表 sub
            INSERT INTO daily_material_storage_change (
                snapshot_date, material_storage_id, inbound_amount, outbound_amount, net_change,
                size_34_inbound_amount, size_35_inbound_amount, size_36_inbound_amount, size_37_inbound_amount,
                size_38_inbound_amount, size_39_inbound_amount, size_40_inbound_amount, size_41_inbound_amount,
                size_42_inbound_amount, size_43_inbound_amount, size_44_inbound_amount, size_45_inbound_amount, size_46_inbound_amount,
                size_34_outbound_amount, size_35_outbound_amount, size_36_outbound_amount, size_37_outbound_amount,
                size_38_outbound_amount, size_39_outbound_amount, size_40_outbound_amount, size_41_outbound_amount,
                size_42_outbound_amount, size_43_outbound_amount, size_44_outbound_amount, size_45_outbound_amount, size_46_outbound_amount
            )
            SELECT
                snapshot_date,
                material_storage_id,
                SUM(inbound_amount)  AS inbound_amount,
                SUM(outbound_amount) AS outbound_amount,
                SUM(inbound_amount) - SUM(outbound_amount) AS net_change,
                -- 尺码入库
                SUM(size_34_inbound_amount), SUM(size_35_inbound_amount), SUM(size_36_inbound_amount), SUM(size_37_inbound_amount),
                SUM(size_38_inbound_amount), SUM(size_39_inbound_amount), SUM(size_40_inbound_amount), SUM(size_41_inbound_amount),
                SUM(size_42_inbound_amount), SUM(size_43_inbound_amount), SUM(size_44_inbound_amount), SUM(size_45_inbound_amount), SUM(size_46_inbound_amount),
                -- 尺码出库
                SUM(size_34_outbound_amount), SUM(size_35_outbound_amount), SUM(size_36_outbound_amount), SUM(size_37_outbound_amount),
                SUM(size_38_outbound_amount), SUM(size_39_outbound_amount), SUM(size_40_outbound_amount), SUM(size_41_outbound_amount),
                SUM(size_42_outbound_amount), SUM(size_43_outbound_amount), SUM(size_44_outbound_amount), SUM(size_45_outbound_amount), SUM(size_46_outbound_amount)
            FROM (
                -- 直接复用上面“查询版”的最外层 SELECT，但把 GROUP BY 精简为
                -- GROUP BY snapshot_date, material_storage_id
                /* 将上面查询版作为子查询贴过来并按上述调整 */
                WITH inbound AS (
                SELECT
                    DATE(ir.inbound_datetime)                    AS snapshot_date,
                    ird.material_storage_id                      AS material_storage_id,
                    SUM(ird.inbound_amount)                      AS inbound_amount,
                    0                                            AS outbound_amount,
                    -- 尺码入库
                    SUM(COALESCE(ird.size_34_inbound_amount,0))  AS size_34_inbound_amount,
                    SUM(COALESCE(ird.size_35_inbound_amount,0))  AS size_35_inbound_amount,
                    SUM(COALESCE(ird.size_36_inbound_amount,0))  AS size_36_inbound_amount,
                    SUM(COALESCE(ird.size_37_inbound_amount,0))  AS size_37_inbound_amount,
                    SUM(COALESCE(ird.size_38_inbound_amount,0))  AS size_38_inbound_amount,
                    SUM(COALESCE(ird.size_39_inbound_amount,0))  AS size_39_inbound_amount,
                    SUM(COALESCE(ird.size_40_inbound_amount,0))  AS size_40_inbound_amount,
                    SUM(COALESCE(ird.size_41_inbound_amount,0))  AS size_41_inbound_amount,
                    SUM(COALESCE(ird.size_42_inbound_amount,0))  AS size_42_inbound_amount,
                    SUM(COALESCE(ird.size_43_inbound_amount,0))  AS size_43_inbound_amount,
                    SUM(COALESCE(ird.size_44_inbound_amount,0))  AS size_44_inbound_amount,
                    SUM(COALESCE(ird.size_45_inbound_amount,0))  AS size_45_inbound_amount,
                    SUM(COALESCE(ird.size_46_inbound_amount,0))  AS size_46_inbound_amount,
                    -- 尺码出库占位
                    0 AS size_34_outbound_amount, 0 AS size_35_outbound_amount, 0 AS size_36_outbound_amount,
                    0 AS size_37_outbound_amount, 0 AS size_38_outbound_amount, 0 AS size_39_outbound_amount,
                    0 AS size_40_outbound_amount, 0 AS size_41_outbound_amount, 0 AS size_42_outbound_amount,
                    0 AS size_43_outbound_amount, 0 AS size_44_outbound_amount, 0 AS size_45_outbound_amount,
                    0 AS size_46_outbound_amount
                FROM inbound_record_detail ird
                JOIN inbound_record ir
                ON ir.inbound_record_id = ird.inbound_record_id
                WHERE ir.inbound_datetime >= :now_date
                AND ir.inbound_datetime < :previous_date
                GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id
            ),
            outbound AS (
                SELECT
                    DATE(orh.outbound_datetime)                   AS snapshot_date,
                    ord.material_storage_id                       AS material_storage_id,
                    0                                             AS inbound_amount,
                    SUM(COALESCE(ord.outbound_amount,0))          AS outbound_amount,
                    -- 尺码入库占位
                    0 AS size_34_inbound_amount, 0 AS size_35_inbound_amount, 0 AS size_36_inbound_amount,
                    0 AS size_37_inbound_amount, 0 AS size_38_inbound_amount, 0 AS size_39_inbound_amount,
                    0 AS size_40_inbound_amount, 0 AS size_41_inbound_amount, 0 AS size_42_inbound_amount,
                    0 AS size_43_inbound_amount, 0 AS size_44_inbound_amount, 0 AS size_45_inbound_amount,
                    0 AS size_46_inbound_amount,
                    -- 尺码出库
                    SUM(COALESCE(ord.size_34_outbound_amount,0))  AS size_34_outbound_amount,
                    SUM(COALESCE(ord.size_35_outbound_amount,0))  AS size_35_outbound_amount,
                    SUM(COALESCE(ord.size_36_outbound_amount,0))  AS size_36_outbound_amount,
                    SUM(COALESCE(ord.size_37_outbound_amount,0))  AS size_37_outbound_amount,
                    SUM(COALESCE(ord.size_38_outbound_amount,0))  AS size_38_outbound_amount,
                    SUM(COALESCE(ord.size_39_outbound_amount,0))  AS size_39_outbound_amount,
                    SUM(COALESCE(ord.size_40_outbound_amount,0))  AS size_40_outbound_amount,
                    SUM(COALESCE(ord.size_41_outbound_amount,0))  AS size_41_outbound_amount,
                    SUM(COALESCE(ord.size_42_outbound_amount,0))  AS size_42_outbound_amount,
                    SUM(COALESCE(ord.size_43_outbound_amount,0))  AS size_43_outbound_amount,
                    SUM(COALESCE(ord.size_44_outbound_amount,0))  AS size_44_outbound_amount,
                    SUM(COALESCE(ord.size_45_outbound_amount,0))  AS size_45_outbound_amount,
                    SUM(COALESCE(ord.size_46_outbound_amount,0))  AS size_46_outbound_amount
                FROM outbound_record_detail ord
                JOIN outbound_record orh
                ON orh.outbound_record_id = ord.outbound_record_id
                WHERE orh.outbound_datetime >= :previous_date
                AND orh.outbound_datetime < :now_date
                GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
            )
            SELECT
                x.snapshot_date,
                x.material_storage_id,
                SUM(x.inbound_amount)  AS inbound_amount,
                SUM(x.outbound_amount) AS outbound_amount,
                SUM(x.inbound_amount) - SUM(x.outbound_amount) AS net_change,
                -- 尺码入库
                SUM(x.size_34_inbound_amount) AS size_34_inbound_amount,
                SUM(x.size_35_inbound_amount) AS size_35_inbound_amount,
                SUM(x.size_36_inbound_amount) AS size_36_inbound_amount,
                SUM(x.size_37_inbound_amount) AS size_37_inbound_amount,
                SUM(x.size_38_inbound_amount) AS size_38_inbound_amount,
                SUM(x.size_39_inbound_amount) AS size_39_inbound_amount,
                SUM(x.size_40_inbound_amount) AS size_40_inbound_amount,
                SUM(x.size_41_inbound_amount) AS size_41_inbound_amount,
                SUM(x.size_42_inbound_amount) AS size_42_inbound_amount,
                SUM(x.size_43_inbound_amount) AS size_43_inbound_amount,
                SUM(x.size_44_inbound_amount) AS size_44_inbound_amount,
                SUM(x.size_45_inbound_amount) AS size_45_inbound_amount,
                SUM(x.size_46_inbound_amount) AS size_46_inbound_amount,
                -- 尺码出库
                SUM(x.size_34_outbound_amount) AS size_34_outbound_amount,
                SUM(x.size_35_outbound_amount) AS size_35_outbound_amount,
                SUM(x.size_36_outbound_amount) AS size_36_outbound_amount,
                SUM(x.size_37_outbound_amount) AS size_37_outbound_amount,
                SUM(x.size_38_outbound_amount) AS size_38_outbound_amount,
                SUM(x.size_39_outbound_amount) AS size_39_outbound_amount,
                SUM(x.size_40_outbound_amount) AS size_40_outbound_amount,
                SUM(x.size_41_outbound_amount) AS size_41_outbound_amount,
                SUM(x.size_42_outbound_amount) AS size_42_outbound_amount,
                SUM(x.size_43_outbound_amount) AS size_43_outbound_amount,
                SUM(x.size_44_outbound_amount) AS size_44_outbound_amount,
                SUM(x.size_45_outbound_amount) AS size_45_outbound_amount,
                SUM(x.size_46_outbound_amount) AS size_46_outbound_amount
            FROM (
                SELECT * FROM inbound
                UNION ALL
                SELECT * FROM outbound
            ) x
            GROUP BY
                x.snapshot_date, x.material_storage_id
            ORDER BY x.material_storage_id
            ) sub
            GROUP BY snapshot_date, material_storage_id
            ON DUPLICATE KEY UPDATE
                inbound_amount           = VALUES(inbound_amount),
                outbound_amount          = VALUES(outbound_amount),
                net_change               = VALUES(net_change),
                size_34_inbound_amount   = VALUES(size_34_inbound_amount),
                size_35_inbound_amount   = VALUES(size_35_inbound_amount),
                size_36_inbound_amount   = VALUES(size_36_inbound_amount),
                size_37_inbound_amount   = VALUES(size_37_inbound_amount),
                size_38_inbound_amount   = VALUES(size_38_inbound_amount),
                size_39_inbound_amount   = VALUES(size_39_inbound_amount),
                size_40_inbound_amount   = VALUES(size_40_inbound_amount),
                size_41_inbound_amount   = VALUES(size_41_inbound_amount),
                size_42_inbound_amount   = VALUES(size_42_inbound_amount),
                size_43_inbound_amount   = VALUES(size_43_inbound_amount),
                size_44_inbound_amount   = VALUES(size_44_inbound_amount),
                size_45_inbound_amount   = VALUES(size_45_inbound_amount),
                size_46_inbound_amount   = VALUES(size_46_inbound_amount),
                size_34_outbound_amount  = VALUES(size_34_outbound_amount),
                size_35_outbound_amount  = VALUES(size_35_outbound_amount),
                size_36_outbound_amount  = VALUES(size_36_outbound_amount),
                size_37_outbound_amount  = VALUES(size_37_outbound_amount),
                size_38_outbound_amount  = VALUES(size_38_outbound_amount),
                size_39_outbound_amount  = VALUES(size_39_outbound_amount),
                size_40_outbound_amount  = VALUES(size_40_outbound_amount),
                size_41_outbound_amount  = VALUES(size_41_outbound_amount),
                size_42_outbound_amount  = VALUES(size_42_outbound_amount),
                size_43_outbound_amount  = VALUES(size_43_outbound_amount),
                size_44_outbound_amount  = VALUES(size_44_outbound_amount),
                size_45_outbound_amount  = VALUES(size_45_outbound_amount),
                size_46_outbound_amount  = VALUES(size_46_outbound_amount),
                update_time              = CURRENT_TIMESTAMP;
            """
        )
        # 设置 now_date 和 next_date
        db.session.execute(sql, {"now_date": date.today(), "previous_date": date.today() - timedelta(days=1)})
        db.session.commit()
        print("Daily material storage change snapshot taken.")


def snapshot_material_storage(app):
    with app.app_context():
        sql = text(
            """
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
                material_outsource_status,
                material_outsource_date,
                purchase_order_item_id,
                material_storage_status,
                shoe_size_columns,
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
                :snapshot_date AS snapshot_date,
                ms.material_storage_id,
                ms.order_id,
                ms.order_shoe_id,
                ms.spu_material_id,
                ms.actual_inbound_unit,
                ms.inbound_amount,
                ms.current_amount,
                ms.unit_price,
                ms.average_price,
                ms.material_outsource_status,
                ms.material_outsource_date,
                ms.purchase_order_item_id,
                ms.material_storage_status,
                ms.shoe_size_columns,
                ms.size_34_current_amount,
                ms.size_35_current_amount,
                ms.size_36_current_amount,
                ms.size_37_current_amount,
                ms.size_38_current_amount,
                ms.size_39_current_amount,
                ms.size_40_current_amount,
                ms.size_41_current_amount,
                ms.size_42_current_amount,
                ms.size_43_current_amount,
                ms.size_44_current_amount,
                ms.size_45_current_amount,
                ms.size_46_current_amount,
                ms.size_34_inbound_amount,
                ms.size_35_inbound_amount,
                ms.size_36_inbound_amount,
                ms.size_37_inbound_amount,
                ms.size_38_inbound_amount,
                ms.size_39_inbound_amount,
                ms.size_40_inbound_amount,
                ms.size_41_inbound_amount,
                ms.size_42_inbound_amount,
                ms.size_43_inbound_amount,
                ms.size_44_inbound_amount,
                ms.size_45_inbound_amount,
                ms.size_46_inbound_amount
            FROM material_storage ms
        """
        )

        # 设置 snapshot_date
        db.session.execute(sql, {"snapshot_date": date.today()})
        db.session.commit()
        print("Material storage snapshot taken.")

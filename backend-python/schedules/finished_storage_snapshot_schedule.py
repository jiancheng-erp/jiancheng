from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

from app_config import db
from logger import logger
from sqlalchemy import text


BEIJING_TZ = "Asia/Shanghai"


def _prev_month_end() -> date:
    """返回本地时区下上个月最后一天的日期"""
    today_local = datetime.now(ZoneInfo(BEIJING_TZ)).date()
    first_day_this_month = today_local.replace(day=1)
    return first_day_this_month - timedelta(days=1)


def _yesterday_range_beijing():
    """返回北京时间下，昨天 [00:00, 24:00) 的开始/结束 datetime（不带时区）"""
    now_bj = datetime.now(ZoneInfo(BEIJING_TZ))
    today_bj = now_bj.date()
    start = datetime.combine(today_bj - timedelta(days=1), datetime.min.time(), tzinfo=ZoneInfo(BEIJING_TZ))
    end = datetime.combine(today_bj, datetime.min.time(), tzinfo=ZoneInfo(BEIJING_TZ))
    return start.replace(tzinfo=None), end.replace(tzinfo=None), (today_bj - timedelta(days=1))


def snapshot_daily_finished_storage_change(app):
    """按天汇总成品仓入/出库净变动，写入 daily_finished_shoe_storage_change + 尺码明细表。"""
    with app.app_context():
        start_dt, end_dt, snapshot_date = _yesterday_range_beijing()

        sql_parent = text(
            """
            INSERT INTO daily_finished_shoe_storage_change (
                snapshot_date,
                finished_shoe_storage_id,
                inbound_amount_sum,
                outbound_amount_sum,
                net_change
            )
            SELECT
                agg.snapshot_date,
                agg.finished_shoe_storage_id,
                COALESCE(agg.inbound_amount_sum, 0) AS inbound_amount_sum,
                COALESCE(agg.outbound_amount_sum, 0) AS outbound_amount_sum,
                COALESCE(agg.inbound_amount_sum, 0) - COALESCE(agg.outbound_amount_sum, 0) AS net_change
            FROM (
                SELECT
                    t.snapshot_date,
                    t.finished_shoe_storage_id,
                    SUM(t.inbound_amount_sum)  AS inbound_amount_sum,
                    SUM(t.outbound_amount_sum) AS outbound_amount_sum
                FROM (
                    SELECT
                        DATE(sir.inbound_datetime)             AS snapshot_date,
                        sird.finished_shoe_storage_id          AS finished_shoe_storage_id,
                        SUM(COALESCE(sird.inbound_amount, 0))  AS inbound_amount_sum,
                        0                                      AS outbound_amount_sum
                    FROM shoe_inbound_record_detail sird
                    JOIN shoe_inbound_record sir
                        ON sir.shoe_inbound_record_id = sird.shoe_inbound_record_id
                    WHERE sir.inbound_datetime >= :start_dt
                      AND sir.inbound_datetime <  :end_dt
                      AND sird.is_deleted = 0
                      AND sird.finished_shoe_storage_id IS NOT NULL
                    GROUP BY DATE(sir.inbound_datetime), sird.finished_shoe_storage_id

                    UNION ALL

                    SELECT
                        DATE(sor.outbound_datetime)            AS snapshot_date,
                        sord.finished_shoe_storage_id          AS finished_shoe_storage_id,
                        0                                      AS inbound_amount_sum,
                        SUM(COALESCE(sord.outbound_amount, 0)) AS outbound_amount_sum
                    FROM shoe_outbound_record_detail sord
                    JOIN shoe_outbound_record sor
                        ON sor.shoe_outbound_record_id = sord.shoe_outbound_record_id
                    WHERE sor.outbound_datetime >= :start_dt
                      AND sor.outbound_datetime <  :end_dt
                      AND sord.finished_shoe_storage_id IS NOT NULL
                    GROUP BY DATE(sor.outbound_datetime), sord.finished_shoe_storage_id
                ) t
                GROUP BY t.snapshot_date, t.finished_shoe_storage_id
            ) agg
            WHERE agg.snapshot_date = :snapshot_date
            ON DUPLICATE KEY UPDATE
                inbound_amount_sum  = VALUES(inbound_amount_sum),
                outbound_amount_sum = VALUES(outbound_amount_sum),
                net_change          = VALUES(net_change),
                update_time         = CURRENT_TIMESTAMP
            """
        )
        db.session.execute(sql_parent, {
            "start_dt": start_dt,
            "end_dt": end_dt,
            "snapshot_date": snapshot_date,
        })

        sql_size = text(
            """
            INSERT INTO daily_finished_shoe_size_detail_change (
                daily_change_id,
                size_value,
                order_number,
                inbound_amount_sum,
                outbound_amount_sum
            )
            SELECT
                dfssc.daily_change_id,
                sz.size_value,
                sz.order_number,
                COALESCE(inb.sum_amount, 0)  AS inbound_amount_sum,
                COALESCE(outb.sum_amount, 0) AS outbound_amount_sum
            FROM daily_finished_shoe_storage_change dfssc
            JOIN (
                SELECT 0 AS order_number, '34' AS size_value
                UNION ALL SELECT 1, '35'
                UNION ALL SELECT 2, '36'
                UNION ALL SELECT 3, '37'
                UNION ALL SELECT 4, '38'
                UNION ALL SELECT 5, '39'
                UNION ALL SELECT 6, '40'
                UNION ALL SELECT 7, '41'
                UNION ALL SELECT 8, '42'
                UNION ALL SELECT 9, '43'
                UNION ALL SELECT 10, '44'
                UNION ALL SELECT 11, '45'
                UNION ALL SELECT 12, '46'
            ) sz ON 1 = 1
            LEFT JOIN (
                SELECT
                    DATE(sir.inbound_datetime)    AS snapshot_date,
                    sird.finished_shoe_storage_id AS finished_shoe_storage_id,
                    sz_i.order_number             AS order_number,
                    SUM(
                        CASE sz_i.order_number
                            WHEN 0 THEN COALESCE(sird.size_34_amount, 0)
                            WHEN 1 THEN COALESCE(sird.size_35_amount, 0)
                            WHEN 2 THEN COALESCE(sird.size_36_amount, 0)
                            WHEN 3 THEN COALESCE(sird.size_37_amount, 0)
                            WHEN 4 THEN COALESCE(sird.size_38_amount, 0)
                            WHEN 5 THEN COALESCE(sird.size_39_amount, 0)
                            WHEN 6 THEN COALESCE(sird.size_40_amount, 0)
                            WHEN 7 THEN COALESCE(sird.size_41_amount, 0)
                            WHEN 8 THEN COALESCE(sird.size_42_amount, 0)
                            WHEN 9 THEN COALESCE(sird.size_43_amount, 0)
                            WHEN 10 THEN COALESCE(sird.size_44_amount, 0)
                            WHEN 11 THEN COALESCE(sird.size_45_amount, 0)
                            WHEN 12 THEN COALESCE(sird.size_46_amount, 0)
                        END
                    ) AS sum_amount
                FROM shoe_inbound_record_detail sird
                JOIN shoe_inbound_record sir
                    ON sir.shoe_inbound_record_id = sird.shoe_inbound_record_id
                JOIN (
                    SELECT 0 AS order_number
                    UNION ALL SELECT 1
                    UNION ALL SELECT 2
                    UNION ALL SELECT 3
                    UNION ALL SELECT 4
                    UNION ALL SELECT 5
                    UNION ALL SELECT 6
                    UNION ALL SELECT 7
                    UNION ALL SELECT 8
                    UNION ALL SELECT 9
                    UNION ALL SELECT 10
                    UNION ALL SELECT 11
                    UNION ALL SELECT 12
                ) sz_i ON 1 = 1
                WHERE sir.inbound_datetime >= :start_dt
                  AND sir.inbound_datetime <  :end_dt
                  AND sird.is_deleted = 0
                  AND sird.finished_shoe_storage_id IS NOT NULL
                GROUP BY DATE(sir.inbound_datetime), sird.finished_shoe_storage_id, sz_i.order_number
            ) inb
                ON inb.snapshot_date = dfssc.snapshot_date
               AND inb.finished_shoe_storage_id = dfssc.finished_shoe_storage_id
               AND inb.order_number = sz.order_number
            LEFT JOIN (
                SELECT
                    DATE(sor.outbound_datetime)   AS snapshot_date,
                    sord.finished_shoe_storage_id AS finished_shoe_storage_id,
                    sz_o.order_number             AS order_number,
                    SUM(
                        CASE sz_o.order_number
                            WHEN 0 THEN COALESCE(sord.size_34_amount, 0)
                            WHEN 1 THEN COALESCE(sord.size_35_amount, 0)
                            WHEN 2 THEN COALESCE(sord.size_36_amount, 0)
                            WHEN 3 THEN COALESCE(sord.size_37_amount, 0)
                            WHEN 4 THEN COALESCE(sord.size_38_amount, 0)
                            WHEN 5 THEN COALESCE(sord.size_39_amount, 0)
                            WHEN 6 THEN COALESCE(sord.size_40_amount, 0)
                            WHEN 7 THEN COALESCE(sord.size_41_amount, 0)
                            WHEN 8 THEN COALESCE(sord.size_42_amount, 0)
                            WHEN 9 THEN COALESCE(sord.size_43_amount, 0)
                            WHEN 10 THEN COALESCE(sord.size_44_amount, 0)
                            WHEN 11 THEN COALESCE(sord.size_45_amount, 0)
                            WHEN 12 THEN COALESCE(sord.size_46_amount, 0)
                        END
                    ) AS sum_amount
                FROM shoe_outbound_record_detail sord
                JOIN shoe_outbound_record sor
                    ON sor.shoe_outbound_record_id = sord.shoe_outbound_record_id
                JOIN (
                    SELECT 0 AS order_number
                    UNION ALL SELECT 1
                    UNION ALL SELECT 2
                    UNION ALL SELECT 3
                    UNION ALL SELECT 4
                    UNION ALL SELECT 5
                    UNION ALL SELECT 6
                    UNION ALL SELECT 7
                    UNION ALL SELECT 8
                    UNION ALL SELECT 9
                    UNION ALL SELECT 10
                    UNION ALL SELECT 11
                    UNION ALL SELECT 12
                ) sz_o ON 1 = 1
                WHERE sor.outbound_datetime >= :start_dt
                  AND sor.outbound_datetime <  :end_dt
                  AND sord.finished_shoe_storage_id IS NOT NULL
                GROUP BY DATE(sor.outbound_datetime), sord.finished_shoe_storage_id, sz_o.order_number
            ) outb
                ON outb.snapshot_date = dfssc.snapshot_date
               AND outb.finished_shoe_storage_id = dfssc.finished_shoe_storage_id
               AND outb.order_number = sz.order_number
            WHERE dfssc.snapshot_date = :snapshot_date
            ON DUPLICATE KEY UPDATE
                inbound_amount_sum  = VALUES(inbound_amount_sum),
                outbound_amount_sum = VALUES(outbound_amount_sum),
                update_time         = CURRENT_TIMESTAMP
            """
        )
        db.session.execute(sql_size, {
            "start_dt": start_dt,
            "end_dt": end_dt,
            "snapshot_date": snapshot_date,
        })

        db.session.commit()
        logger.info(f"📊 daily_finished_shoe_storage_change 已生成：date={snapshot_date}, 窗口[{start_dt} ~ {end_dt})（北京时区）")


def snapshot_finished_storage(app):
    """
    每次执行把当前 finished_shoe_storage 的数据快照到对应 snapshot 表。
    snapshot_date 默认=上个月最后一天（本地时区）。
    """
    with app.app_context():
        snapshot_date = _prev_month_end()

        sql_storage = text(
            """
            INSERT INTO finished_shoe_storage_snapshot (
                snapshot_date,
                finished_shoe_storage_id,
                order_shoe_type_id,
                finished_estimated_amount,
                size_34_estimated_amount,
                size_35_estimated_amount,
                size_36_estimated_amount,
                size_37_estimated_amount,
                size_38_estimated_amount,
                size_39_estimated_amount,
                size_40_estimated_amount,
                size_41_estimated_amount,
                size_42_estimated_amount,
                size_43_estimated_amount,
                size_44_estimated_amount,
                size_45_estimated_amount,
                size_46_estimated_amount,
                finished_actual_amount,
                size_34_actual_amount,
                size_35_actual_amount,
                size_36_actual_amount,
                size_37_actual_amount,
                size_38_actual_amount,
                size_39_actual_amount,
                size_40_actual_amount,
                size_41_actual_amount,
                size_42_actual_amount,
                size_43_actual_amount,
                size_44_actual_amount,
                size_45_actual_amount,
                size_46_actual_amount,
                finished_amount,
                size_34_amount,
                size_35_amount,
                size_36_amount,
                size_37_amount,
                size_38_amount,
                size_39_amount,
                size_40_amount,
                size_41_amount,
                size_42_amount,
                size_43_amount,
                size_44_amount,
                size_45_amount,
                size_46_amount,
                finished_status
            )
            SELECT
                :snapshot_date AS snapshot_date,
                fss.finished_shoe_id,
                fss.order_shoe_type_id,
                fss.finished_estimated_amount,
                fss.size_34_estimated_amount,
                fss.size_35_estimated_amount,
                fss.size_36_estimated_amount,
                fss.size_37_estimated_amount,
                fss.size_38_estimated_amount,
                fss.size_39_estimated_amount,
                fss.size_40_estimated_amount,
                fss.size_41_estimated_amount,
                fss.size_42_estimated_amount,
                fss.size_43_estimated_amount,
                fss.size_44_estimated_amount,
                fss.size_45_estimated_amount,
                fss.size_46_estimated_amount,
                fss.finished_actual_amount,
                fss.size_34_actual_amount,
                fss.size_35_actual_amount,
                fss.size_36_actual_amount,
                fss.size_37_actual_amount,
                fss.size_38_actual_amount,
                fss.size_39_actual_amount,
                fss.size_40_actual_amount,
                fss.size_41_actual_amount,
                fss.size_42_actual_amount,
                fss.size_43_actual_amount,
                fss.size_44_actual_amount,
                fss.size_45_actual_amount,
                fss.size_46_actual_amount,
                fss.finished_amount,
                fss.size_34_amount,
                fss.size_35_amount,
                fss.size_36_amount,
                fss.size_37_amount,
                fss.size_38_amount,
                fss.size_39_amount,
                fss.size_40_amount,
                fss.size_41_amount,
                fss.size_42_amount,
                fss.size_43_amount,
                fss.size_44_amount,
                fss.size_45_amount,
                fss.size_46_amount,
                fss.finished_status
            FROM finished_shoe_storage fss
            ON DUPLICATE KEY UPDATE
                order_shoe_type_id        = VALUES(order_shoe_type_id),
                finished_estimated_amount = VALUES(finished_estimated_amount),
                size_34_estimated_amount  = VALUES(size_34_estimated_amount),
                size_35_estimated_amount  = VALUES(size_35_estimated_amount),
                size_36_estimated_amount  = VALUES(size_36_estimated_amount),
                size_37_estimated_amount  = VALUES(size_37_estimated_amount),
                size_38_estimated_amount  = VALUES(size_38_estimated_amount),
                size_39_estimated_amount  = VALUES(size_39_estimated_amount),
                size_40_estimated_amount  = VALUES(size_40_estimated_amount),
                size_41_estimated_amount  = VALUES(size_41_estimated_amount),
                size_42_estimated_amount  = VALUES(size_42_estimated_amount),
                size_43_estimated_amount  = VALUES(size_43_estimated_amount),
                size_44_estimated_amount  = VALUES(size_44_estimated_amount),
                size_45_estimated_amount  = VALUES(size_45_estimated_amount),
                size_46_estimated_amount  = VALUES(size_46_estimated_amount),
                finished_actual_amount    = VALUES(finished_actual_amount),
                size_34_actual_amount     = VALUES(size_34_actual_amount),
                size_35_actual_amount     = VALUES(size_35_actual_amount),
                size_36_actual_amount     = VALUES(size_36_actual_amount),
                size_37_actual_amount     = VALUES(size_37_actual_amount),
                size_38_actual_amount     = VALUES(size_38_actual_amount),
                size_39_actual_amount     = VALUES(size_39_actual_amount),
                size_40_actual_amount     = VALUES(size_40_actual_amount),
                size_41_actual_amount     = VALUES(size_41_actual_amount),
                size_42_actual_amount     = VALUES(size_42_actual_amount),
                size_43_actual_amount     = VALUES(size_43_actual_amount),
                size_44_actual_amount     = VALUES(size_44_actual_amount),
                size_45_actual_amount     = VALUES(size_45_actual_amount),
                size_46_actual_amount     = VALUES(size_46_actual_amount),
                finished_amount           = VALUES(finished_amount),
                size_34_amount            = VALUES(size_34_amount),
                size_35_amount            = VALUES(size_35_amount),
                size_36_amount            = VALUES(size_36_amount),
                size_37_amount            = VALUES(size_37_amount),
                size_38_amount            = VALUES(size_38_amount),
                size_39_amount            = VALUES(size_39_amount),
                size_40_amount            = VALUES(size_40_amount),
                size_41_amount            = VALUES(size_41_amount),
                size_42_amount            = VALUES(size_42_amount),
                size_43_amount            = VALUES(size_43_amount),
                size_44_amount            = VALUES(size_44_amount),
                size_45_amount            = VALUES(size_45_amount),
                size_46_amount            = VALUES(size_46_amount),
                finished_status           = VALUES(finished_status),
                update_time               = CURRENT_TIMESTAMP
            """
        )
        db.session.execute(sql_storage, {"snapshot_date": snapshot_date})
        logger.info("✅ finished_shoe_storage → finished_shoe_storage_snapshot 完成")

        sql_size_detail = text(
            """
            INSERT INTO finished_shoe_size_detail_snapshot (
                snapshot_date,
                finished_shoe_storage_id,
                size_value,
                order_number,
                estimated_amount,
                actual_amount,
                current_amount
            )
            SELECT
                :snapshot_date AS snapshot_date,
                fss.finished_shoe_id,
                sz.size_value,
                sz.order_number,
                CASE sz.order_number
                    WHEN 0  THEN COALESCE(fss.size_34_estimated_amount, 0)
                    WHEN 1  THEN COALESCE(fss.size_35_estimated_amount, 0)
                    WHEN 2  THEN COALESCE(fss.size_36_estimated_amount, 0)
                    WHEN 3  THEN COALESCE(fss.size_37_estimated_amount, 0)
                    WHEN 4  THEN COALESCE(fss.size_38_estimated_amount, 0)
                    WHEN 5  THEN COALESCE(fss.size_39_estimated_amount, 0)
                    WHEN 6  THEN COALESCE(fss.size_40_estimated_amount, 0)
                    WHEN 7  THEN COALESCE(fss.size_41_estimated_amount, 0)
                    WHEN 8  THEN COALESCE(fss.size_42_estimated_amount, 0)
                    WHEN 9  THEN COALESCE(fss.size_43_estimated_amount, 0)
                    WHEN 10 THEN COALESCE(fss.size_44_estimated_amount, 0)
                    WHEN 11 THEN COALESCE(fss.size_45_estimated_amount, 0)
                    WHEN 12 THEN COALESCE(fss.size_46_estimated_amount, 0)
                END AS estimated_amount,
                CASE sz.order_number
                    WHEN 0  THEN COALESCE(fss.size_34_actual_amount, 0)
                    WHEN 1  THEN COALESCE(fss.size_35_actual_amount, 0)
                    WHEN 2  THEN COALESCE(fss.size_36_actual_amount, 0)
                    WHEN 3  THEN COALESCE(fss.size_37_actual_amount, 0)
                    WHEN 4  THEN COALESCE(fss.size_38_actual_amount, 0)
                    WHEN 5  THEN COALESCE(fss.size_39_actual_amount, 0)
                    WHEN 6  THEN COALESCE(fss.size_40_actual_amount, 0)
                    WHEN 7  THEN COALESCE(fss.size_41_actual_amount, 0)
                    WHEN 8  THEN COALESCE(fss.size_42_actual_amount, 0)
                    WHEN 9  THEN COALESCE(fss.size_43_actual_amount, 0)
                    WHEN 10 THEN COALESCE(fss.size_44_actual_amount, 0)
                    WHEN 11 THEN COALESCE(fss.size_45_actual_amount, 0)
                    WHEN 12 THEN COALESCE(fss.size_46_actual_amount, 0)
                END AS actual_amount,
                CASE sz.order_number
                    WHEN 0  THEN COALESCE(fss.size_34_amount, 0)
                    WHEN 1  THEN COALESCE(fss.size_35_amount, 0)
                    WHEN 2  THEN COALESCE(fss.size_36_amount, 0)
                    WHEN 3  THEN COALESCE(fss.size_37_amount, 0)
                    WHEN 4  THEN COALESCE(fss.size_38_amount, 0)
                    WHEN 5  THEN COALESCE(fss.size_39_amount, 0)
                    WHEN 6  THEN COALESCE(fss.size_40_amount, 0)
                    WHEN 7  THEN COALESCE(fss.size_41_amount, 0)
                    WHEN 8  THEN COALESCE(fss.size_42_amount, 0)
                    WHEN 9  THEN COALESCE(fss.size_43_amount, 0)
                    WHEN 10 THEN COALESCE(fss.size_44_amount, 0)
                    WHEN 11 THEN COALESCE(fss.size_45_amount, 0)
                    WHEN 12 THEN COALESCE(fss.size_46_amount, 0)
                END AS current_amount
            FROM finished_shoe_storage fss
            JOIN (
                SELECT 0 AS order_number, '34' AS size_value
                UNION ALL SELECT 1, '35'
                UNION ALL SELECT 2, '36'
                UNION ALL SELECT 3, '37'
                UNION ALL SELECT 4, '38'
                UNION ALL SELECT 5, '39'
                UNION ALL SELECT 6, '40'
                UNION ALL SELECT 7, '41'
                UNION ALL SELECT 8, '42'
                UNION ALL SELECT 9, '43'
                UNION ALL SELECT 10, '44'
                UNION ALL SELECT 11, '45'
                UNION ALL SELECT 12, '46'
            ) sz ON 1 = 1
            ON DUPLICATE KEY UPDATE
                estimated_amount = VALUES(estimated_amount),
                actual_amount    = VALUES(actual_amount),
                current_amount   = VALUES(current_amount),
                update_time      = CURRENT_TIMESTAMP
            """
        )
        db.session.execute(sql_size_detail, {"snapshot_date": snapshot_date})

        db.session.commit()
        logger.info(f"📸 finished_shoe_storage 快照完成：snapshot_date={snapshot_date}")

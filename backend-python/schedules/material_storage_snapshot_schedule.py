from datetime import date, timedelta, datetime
from logger import logger
from zoneinfo import ZoneInfo  # Python 3.9+
from app_config import db
from sqlalchemy import text

BEIJING_TZ = "Asia/Shanghai"

def _prev_month_end() -> date:
    """返回本地时区下上个月最后一天的日期"""
    today_local = datetime.now(ZoneInfo(BEIJING_TZ)).date()
    first_day_this_month = today_local.replace(day=1)
    return first_day_this_month - timedelta(days=1)


def _yesterday_range_beijing():
    """返回北京时间下，昨天 [00:00, 24:00) 的开始/结束 datetime（含时区）"""
    now_bj = datetime.now(ZoneInfo(BEIJING_TZ))
    today_bj = now_bj.date()
    start = datetime.combine(today_bj - timedelta(days=1), datetime.min.time(), tzinfo=ZoneInfo(BEIJING_TZ))
    end   = datetime.combine(today_bj, datetime.min.time(), tzinfo=ZoneInfo(BEIJING_TZ))
    # MySQL DATETIME 不带时区，这里传 ISO 字符串（去掉时区部分）
    return start.replace(tzinfo=None), end.replace(tzinfo=None), (today_bj - timedelta(days=1))


def snapshot_daily_storage_change(app):
    """
    生成每日净变动（按 msid 聚合到一条）：
    - inbound_amount_sum / outbound_amount_sum：当天已审核
    - pending_inbound_sum / pending_outbound_sum：当天未审核或被驳回(0,2)
    - latest_unit_price：截至当日结束，最近一次已审核入库单价
    - avg_unit_price：截至当日结束，累计(已审核)总金额/总数量
    默认取北京时间“昨天”的范围。
    幂等：ON DUPLICATE KEY UPDATE
    """
    with app.app_context():

        start_dt, end_dt, snapshot_date = _yesterday_range_beijing()

        # 说明：
        # - inbound_record.approval_status：1=已审核, 0=未审核；2=被驳回（你之前说明要算进 pending）
        # - outbound_record.approval_status：同理
        # - 单价/总价：来自 inbound_record_detail.unit_price 和 item_total_price
        # - 约束：daily_material_storage_change 的主键应为 (snapshot_date, material_storage_id)

        sql = text("""
            INSERT INTO daily_material_storage_change (
                snapshot_date,
                material_storage_id,
                latest_unit_price,
                avg_unit_price,
                pending_inbound_sum,
                pending_outbound_sum,
                inbound_amount_sum,
                outbound_amount_sum,
                net_change
            )
            SELECT
                :snapshot_date AS snapshot_date,
                msid.material_storage_id,

                -- latest_unit_price：截至 end_dt 最近一次“已审核”入库的单价
                COALESCE((
                    SELECT ird2.unit_price
                    FROM inbound_record_detail ird2
                    JOIN inbound_record ir2
                      ON ir2.inbound_record_id = ird2.inbound_record_id
                    WHERE ir2.approval_status = 1
                      AND ird2.material_storage_id = msid.material_storage_id
                      AND ir2.inbound_datetime < :end_dt
                    ORDER BY ir2.inbound_datetime DESC, ird2.id DESC
                    LIMIT 1
                ), 0) AS latest_unit_price,

                -- avg_unit_price：截至 end_dt 的累计(已审核)总金额/总数量
                COALESCE((
                    SELECT
                        CASE WHEN SUM(ird3.inbound_amount) = 0
                             THEN 0
                             ELSE SUM(COALESCE(ird3.item_total_price, ird3.unit_price * ird3.inbound_amount))
                                  / SUM(ird3.inbound_amount)
                        END
                    FROM inbound_record_detail ird3
                    JOIN inbound_record ir3
                      ON ir3.inbound_record_id = ird3.inbound_record_id
                    WHERE ir3.approval_status = 1
                      AND ird3.material_storage_id = msid.material_storage_id
                      AND ir3.inbound_datetime < :end_dt
                ), 0) AS avg_unit_price,

                -- 当天 pending 入库（未审核/被驳回）
                COALESCE((
                    SELECT SUM(ird4.inbound_amount)
                    FROM inbound_record_detail ird4
                    JOIN inbound_record ir4
                      ON ir4.inbound_record_id = ird4.inbound_record_id
                    WHERE ir4.approval_status IN (0, 2)
                      AND ird4.material_storage_id = msid.material_storage_id
                      AND ir4.inbound_datetime >= :start_dt
                      AND ir4.inbound_datetime <  :end_dt
                ), 0) AS pending_inbound_sum,

                -- 当天 pending 出库（未审核/被驳回）
                COALESCE((
                    SELECT SUM(ord4.outbound_amount)
                    FROM outbound_record_detail ord4
                    JOIN outbound_record or4
                      ON or4.outbound_record_id = ord4.outbound_record_id
                    WHERE or4.approval_status IN (0, 2)
                      AND ord4.material_storage_id = msid.material_storage_id
                      AND or4.outbound_datetime >= :start_dt
                      AND or4.outbound_datetime <  :end_dt
                ), 0) AS pending_outbound_sum,

                -- 当天已审核入库
                COALESCE((
                    SELECT SUM(ird5.inbound_amount)
                    FROM inbound_record_detail ird5
                    JOIN inbound_record ir5
                      ON ir5.inbound_record_id = ird5.inbound_record_id
                    WHERE ir5.approval_status = 1
                      AND ird5.material_storage_id = msid.material_storage_id
                      AND ir5.inbound_datetime >= :start_dt
                      AND ir5.inbound_datetime <  :end_dt
                ), 0) AS inbound_amount_sum,

                -- 当天已审核出库
                COALESCE((
                    SELECT SUM(ord5.outbound_amount)
                    FROM outbound_record_detail ord5
                    JOIN outbound_record or5
                      ON or5.outbound_record_id = ord5.outbound_record_id
                    WHERE or5.approval_status = 1
                      AND ord5.material_storage_id = msid.material_storage_id
                      AND or5.outbound_datetime >= :start_dt
                      AND or5.outbound_datetime <  :end_dt
                ), 0) AS outbound_amount_sum,

                -- 净变动
                COALESCE((
                    SELECT SUM(ird6.inbound_amount)
                    FROM inbound_record_detail ird6
                    JOIN inbound_record ir6
                      ON ir6.inbound_record_id = ird6.inbound_record_id
                    WHERE ir6.approval_status = 1
                      AND ird6.material_storage_id = msid.material_storage_id
                      AND ir6.inbound_datetime >= :start_dt
                      AND ir6.inbound_datetime <  :end_dt
                ), 0)
                -
                COALESCE((
                    SELECT SUM(ord6.outbound_amount)
                    FROM outbound_record_detail ord6
                    JOIN outbound_record or6
                      ON or6.outbound_record_id = ord6.outbound_record_id
                    WHERE or6.approval_status = 1
                      AND ord6.material_storage_id = msid.material_storage_id
                      AND or6.outbound_datetime >= :start_dt
                      AND or6.outbound_datetime <  :end_dt
                ), 0)
                AS net_change
            FROM (
                -- 驱动集：取当天窗口内有任一入/出库（已审/未审）或历史上曾有入库（用于单价/均价计算）的 msid
                SELECT DISTINCT material_storage_id
                FROM (
                    SELECT ird.material_storage_id
                    FROM inbound_record_detail ird
                    JOIN inbound_record ir
                      ON ir.inbound_record_id = ird.inbound_record_id
                    WHERE ir.inbound_datetime < :end_dt
                      AND ir.inbound_datetime >= DATE_SUB(:end_dt, INTERVAL 1 DAY)
                    UNION ALL
                    SELECT ord.material_storage_id
                    FROM outbound_record_detail ord
                    JOIN outbound_record orh
                      ON orh.outbound_record_id = ord.outbound_record_id
                    WHERE orh.outbound_datetime < :end_dt
                      AND orh.outbound_datetime >= DATE_SUB(:end_dt, INTERVAL 1 DAY)
                    UNION ALL
                    -- 保证当日虽然没有单据、但历史有入库的 msid 也能刷新 latest/avg 单价
                    SELECT ird.material_storage_id
                    FROM inbound_record_detail ird
                    JOIN inbound_record ir
                      ON ir.inbound_record_id = ird.inbound_record_id
                    WHERE ir.inbound_datetime < :end_dt
                ) u
            ) msid
            ON DUPLICATE KEY UPDATE
                latest_unit_price   = VALUES(latest_unit_price),
                avg_unit_price      = VALUES(avg_unit_price),
                pending_inbound_sum = VALUES(pending_inbound_sum),
                pending_outbound_sum= VALUES(pending_outbound_sum),
                inbound_amount_sum  = VALUES(inbound_amount_sum),
                outbound_amount_sum = VALUES(outbound_amount_sum),
                net_change          = VALUES(net_change),
                update_time         = CURRENT_TIMESTAMP
        """)

        db.session.execute(sql, {
            "snapshot_date": snapshot_date,  # 昨天的日期（北京）
            "start_dt": start_dt,            # 昨天 00:00:00
            "end_dt": end_dt                 # 今天 00:00:00（左闭右开）
        })
        db.session.commit()

        logger.info(f"📊 daily_material_storage_change 已生成：date={snapshot_date}, 窗口[{start_dt} ~ {end_dt})（北京时区）")


def snapshot_material_storage(app):
    """
    每次执行把当前 material_storage 和 material_storage_size_detail 的数据
    快照进对应 snapshot 表。snapshot_date 默认=上个月最后一天（本地时区）。
    """
    with app.app_context():
        snapshot_date = _prev_month_end()

        # material_storage → material_storage_snapshot
        sql_storage = text("""
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
                :snapshot_date AS snapshot_date,
                ms.material_storage_id,
                ms.order_id,
                ms.order_shoe_id,
                ms.spu_material_id,
                ms.actual_inbound_unit,
                ms.pending_inbound,
                ms.pending_outbound,
                ms.inbound_amount,
                ms.current_amount,
                ms.unit_price,
                ms.average_price,
                ms.material_outsource_status,
                ms.material_outsource_date,
                ms.purchase_order_item_id,
                ms.material_storage_status,
                COALESCE(ms.shoe_size_columns, JSON_ARRAY())
            FROM material_storage ms
            ON DUPLICATE KEY UPDATE
                order_id = VALUES(order_id),
                order_shoe_id = VALUES(order_shoe_id),
                spu_material_id = VALUES(spu_material_id),
                actual_inbound_unit = VALUES(actual_inbound_unit),
                pending_inbound = VALUES(pending_inbound),
                pending_outbound = VALUES(pending_outbound),
                inbound_amount = VALUES(inbound_amount),
                current_amount = VALUES(current_amount),
                unit_price = VALUES(unit_price),
                average_price = VALUES(average_price),
                material_outsource_status = VALUES(material_outsource_status),
                material_outsource_date = VALUES(material_outsource_date),
                purchase_order_item_id = VALUES(purchase_order_item_id),
                material_storage_status = VALUES(material_storage_status),
                shoe_size_columns = VALUES(shoe_size_columns),
                update_time = CURRENT_TIMESTAMP
        """)
        db.session.execute(sql_storage, {"snapshot_date": snapshot_date})
        logger.info("✅ material_storage → material_storage_snapshot 完成")

        # material_storage_size_detail → material_storage_size_detail_snapshot
        sql_size_detail = text("""
            INSERT INTO material_storage_size_detail_snapshot (
                snapshot_date,
                size_detail_id,
                material_storage_id,
                size_value,
                order_number,
                pending_inbound,
                pending_outbound,
                inbound_amount,
                current_amount
            )
            SELECT
                :snapshot_date AS snapshot_date,
                msd.id AS size_detail_id,
                msd.material_storage_id,
                msd.size_value,
                msd.order_number,
                msd.pending_inbound,
                msd.pending_outbound,
                msd.inbound_amount,
                msd.current_amount
            FROM material_storage_size_detail msd
            ON DUPLICATE KEY UPDATE
                material_storage_id = VALUES(material_storage_id),
                size_value = VALUES(size_value),
                order_number = VALUES(order_number),
                pending_inbound = VALUES(pending_inbound),
                pending_outbound = VALUES(pending_outbound),
                inbound_amount = VALUES(inbound_amount),
                current_amount = VALUES(current_amount),
                update_time = CURRENT_TIMESTAMP
        """)
        db.session.execute(sql_size_detail, {"snapshot_date": snapshot_date})

        db.session.commit()
        logger.info(f"📸 月末快照完成：snapshot_date={snapshot_date}")
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
    with app.app_context():
        start_dt, end_dt, snapshot_date = _yesterday_range_beijing()
        sql = text(
            """
            INSERT INTO daily_material_storage_change (
                snapshot_date,
                material_storage_id,
                latest_unit_price,
                avg_unit_price,
                pending_inbound_sum,
                pending_outbound_sum,
                inbound_amount_sum,
                outbound_amount_sum,
                make_inventory_inbound_sum,
                make_inventory_outbound_sum,
                net_change
            )
            SELECT
                agg.snapshot_date,
                agg.material_storage_id,
                COALESCE(lp.unit_price, 0)              AS latest_unit_price,
                COALESCE(ap.avg_unit_price, 0)          AS avg_unit_price,
                COALESCE(agg.pending_inbound_sum, 0)    AS pending_inbound_sum,
                COALESCE(agg.pending_outbound_sum, 0)   AS pending_outbound_sum,
                COALESCE(agg.inbound_amount_sum, 0)     AS inbound_amount_sum,
                COALESCE(agg.outbound_amount_sum, 0)    AS outbound_amount_sum,
                COALESCE(agg.make_inventory_inbound_sum, 0)
                    AS make_inventory_inbound_sum,
                COALESCE(agg.make_inventory_outbound_sum, 0)
                    AS make_inventory_outbound_sum,
                COALESCE(agg.inbound_amount_sum, 0)
                    - COALESCE(agg.outbound_amount_sum, 0)
                    + COALESCE(agg.make_inventory_inbound_sum, 0)
                    - COALESCE(agg.make_inventory_outbound_sum, 0)
                    AS net_change
            FROM (
                -- =============================================================
                -- 聚合出“某日 + 某 material_storage_id”的 6 个数量字段
                -- =============================================================
                SELECT
                    t.snapshot_date,
                    t.material_storage_id,
                    SUM(t.pending_inbound_sum)          AS pending_inbound_sum,
                    SUM(t.pending_outbound_sum)         AS pending_outbound_sum,
                    SUM(t.inbound_amount_sum)           AS inbound_amount_sum,
                    SUM(t.outbound_amount_sum)          AS outbound_amount_sum,
                    SUM(t.make_inventory_inbound_sum)   AS make_inventory_inbound_sum,
                    SUM(t.make_inventory_outbound_sum)  AS make_inventory_outbound_sum
                FROM (
                    -- ---------------------------------------------------------
                    -- 1) 当日未审核入库（含驳回），按入库时间 inbound_datetime
                    --     + 当日审批通过的跨日入库单，负数冲销 pending
                    -- ---------------------------------------------------------
                    SELECT
                        DATE(ir.inbound_datetime)             AS snapshot_date,
                        ird.material_storage_id               AS material_storage_id,
                        SUM(COALESCE(ird.inbound_amount, 0)) AS pending_inbound_sum,
                        0                                     AS pending_outbound_sum,
                        0                                     AS inbound_amount_sum,
                        0                                     AS outbound_amount_sum,
                        0                                     AS make_inventory_inbound_sum,
                        0                                     AS make_inventory_outbound_sum
                    FROM inbound_record_detail ird
                    JOIN inbound_record ir
                    ON ir.inbound_record_id = ird.inbound_record_id
                    WHERE ir.inbound_datetime >= :start_dt
                    AND ir.inbound_datetime <  :end_dt
                    AND (
                            ir.approval_status IN (0, 2)
                        OR (
                                ir.approval_status = 1
                            AND (
                                    ir.approval_datetime IS NULL
                                OR DATE(ir.approval_datetime) > :start_dt
                                )
                            )
                    )
                    AND ir.display = 1
                    AND ird.display = 1
                    GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id

                    UNION ALL

                    -- 1b) 当日审核通过的跨日入库单，负数计入 pending_inbound_sum
                    SELECT
                        DATE(ir.approval_datetime)             AS snapshot_date,
                        ird.material_storage_id                AS material_storage_id,
                        -SUM(COALESCE(ird.inbound_amount, 0))  AS pending_inbound_sum,
                        0                                      AS pending_outbound_sum,
                        0                                      AS inbound_amount_sum,
                        0                                      AS outbound_amount_sum,
                        0                                      AS make_inventory_inbound_sum,
                        0                                      AS make_inventory_outbound_sum
                    FROM inbound_record_detail ird
                    JOIN inbound_record ir
                    ON ir.inbound_record_id = ird.inbound_record_id
                    WHERE ir.approval_datetime >= :start_dt
                    AND ir.approval_datetime <  :end_dt
                    AND ir.approval_status     = 1
                    AND DATE(ir.inbound_datetime) < DATE(ir.approval_datetime)
                    AND ir.display = 1
                    AND ird.display = 1
                    GROUP BY DATE(ir.approval_datetime), ird.material_storage_id

                    UNION ALL

                    -- ---------------------------------------------------------
                    -- 2) 当日未审核出库（含驳回），按出库时间 outbound_datetime
                    --     + 当日审批通过的跨日出库单，负数冲销 pending
                    -- ---------------------------------------------------------
                    SELECT
                        DATE(orh.outbound_datetime)           AS snapshot_date,
                        ord.material_storage_id               AS material_storage_id,
                        0                                     AS pending_inbound_sum,
                        SUM(COALESCE(ord.outbound_amount, 0)) AS pending_outbound_sum,
                        0                                     AS inbound_amount_sum,
                        0                                     AS outbound_amount_sum,
                        0                                     AS make_inventory_inbound_sum,
                        0                                     AS make_inventory_outbound_sum
                    FROM outbound_record_detail ord
                    JOIN outbound_record orh
                    ON orh.outbound_record_id = ord.outbound_record_id
                    WHERE orh.outbound_datetime >= :start_dt
                    AND orh.outbound_datetime <  :end_dt
                    AND (
                            orh.approval_status IN (0, 2)
                        OR (
                                orh.approval_status = 1
                            AND (
                                    orh.approval_datetime IS NULL
                                OR DATE(orh.approval_datetime) > :start_dt
                                )
                            )
                    )
                    AND orh.display = 1
                    AND ord.display = 1
                    GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id

                    UNION ALL

                    -- 2b) 当日审核通过的跨日出库单，负数计入 pending_outbound_sum
                    SELECT
                        DATE(orh.approval_datetime)              AS snapshot_date,
                        ord.material_storage_id                  AS material_storage_id,
                        0                                        AS pending_inbound_sum,
                        -SUM(COALESCE(ord.outbound_amount, 0))   AS pending_outbound_sum,
                        0                                        AS inbound_amount_sum,
                        0                                        AS outbound_amount_sum,
                        0                                        AS make_inventory_inbound_sum,
                        0                                        AS make_inventory_outbound_sum
                    FROM outbound_record_detail ord
                    JOIN outbound_record orh
                    ON orh.outbound_record_id = ord.outbound_record_id
                    WHERE orh.approval_datetime >= :start_dt
                    AND orh.approval_datetime <  :end_dt
                    AND orh.approval_status    = 1
                    AND DATE(orh.outbound_datetime) < DATE(orh.approval_datetime)
                    AND orh.display = 1
                    AND ord.display = 1
                    GROUP BY DATE(orh.approval_datetime), ord.material_storage_id

                    UNION ALL

                    -- ---------------------------------------------------------
                    -- 3) 当日已审核“采购入库”（inbound_type = 0），按 approval_datetime
                    -- ---------------------------------------------------------
                    SELECT
                        DATE(ir.approval_datetime)            AS snapshot_date,
                        ird.material_storage_id               AS material_storage_id,
                        0                                     AS pending_inbound_sum,
                        0                                     AS pending_outbound_sum,
                        SUM(COALESCE(ird.inbound_amount, 0))  AS inbound_amount_sum,
                        0                                     AS outbound_amount_sum,
                        0                                     AS make_inventory_inbound_sum,
                        0                                     AS make_inventory_outbound_sum
                    FROM inbound_record_detail ird
                    JOIN inbound_record ir
                    ON ir.inbound_record_id = ird.inbound_record_id
                    WHERE ir.approval_datetime >= :start_dt
                    AND ir.approval_datetime <  :end_dt
                    AND ir.approval_status     = 1
                    AND ir.inbound_type        = 0
                    AND ir.display = 1
                    AND ird.display = 1
                    GROUP BY DATE(ir.approval_datetime), ird.material_storage_id

                    UNION ALL

                    -- ---------------------------------------------------------
                    -- 4) 当日已审核“材料退回出库”（outbound_type = 4），按 approval_datetime
                    --    以负数计入 inbound_amount_sum
                    -- ---------------------------------------------------------
                    SELECT
                        DATE(orh.approval_datetime)              AS snapshot_date,
                        ord.material_storage_id                  AS material_storage_id,
                        0                                        AS pending_inbound_sum,
                        0                                        AS pending_outbound_sum,
                        -SUM(COALESCE(ord.outbound_amount, 0))   AS inbound_amount_sum,
                        0                                        AS outbound_amount_sum,
                        0                                        AS make_inventory_inbound_sum,
                        0                                        AS make_inventory_outbound_sum
                    FROM outbound_record_detail ord
                    JOIN outbound_record orh
                    ON orh.outbound_record_id = ord.outbound_record_id
                    WHERE orh.approval_datetime >= :start_dt
                    AND orh.approval_datetime <  :end_dt
                    AND orh.approval_status    = 1
                    AND orh.outbound_type      = 4
                    AND orh.display = 1
                    AND ord.display = 1
                    GROUP BY DATE(orh.approval_datetime), ord.material_storage_id

                    UNION ALL

                    -- ---------------------------------------------------------
                    -- 5) 当日已审核“生产出库”（outbound_type = 0），按 approval_datetime
                    -- ---------------------------------------------------------
                    SELECT
                        DATE(orh.approval_datetime)             AS snapshot_date,
                        ord.material_storage_id                 AS material_storage_id,
                        0                                       AS pending_inbound_sum,
                        0                                       AS pending_outbound_sum,
                        0                                       AS inbound_amount_sum,
                        SUM(COALESCE(ord.outbound_amount, 0))   AS outbound_amount_sum,
                        0                                       AS make_inventory_inbound_sum,
                        0                                       AS make_inventory_outbound_sum
                    FROM outbound_record_detail ord
                    JOIN outbound_record orh
                    ON orh.outbound_record_id = ord.outbound_record_id
                    WHERE orh.approval_datetime >= :start_dt
                    AND orh.approval_datetime <  :end_dt
                    AND orh.approval_status    = 1
                    AND orh.outbound_type      = 0
                    AND orh.display = 1
                    AND ord.display = 1
                    GROUP BY DATE(orh.approval_datetime), ord.material_storage_id

                    UNION ALL

                    -- ---------------------------------------------------------
                    -- 6) 当日已审核“盘库入库”（inbound_type = 4），按 approval_datetime
                    -- ---------------------------------------------------------
                    SELECT
                        DATE(ir.approval_datetime)            AS snapshot_date,
                        ird.material_storage_id               AS material_storage_id,
                        0                                     AS pending_inbound_sum,
                        0                                     AS pending_outbound_sum,
                        0                                     AS inbound_amount_sum,
                        0                                     AS outbound_amount_sum,
                        SUM(COALESCE(ird.inbound_amount, 0))  AS make_inventory_inbound_sum,
                        0                                     AS make_inventory_outbound_sum
                    FROM inbound_record_detail ird
                    JOIN inbound_record ir
                    ON ir.inbound_record_id = ird.inbound_record_id
                    WHERE ir.approval_datetime >= :start_dt
                    AND ir.approval_datetime <  :end_dt
                    AND ir.approval_status     = 1
                    AND ir.inbound_type        = 4
                    AND ir.display = 1
                    AND ird.display = 1
                    GROUP BY DATE(ir.approval_datetime), ird.material_storage_id

                    UNION ALL

                    -- ---------------------------------------------------------
                    -- 7) 当日已审核“盘库出库”（outbound_type = 5），按 approval_datetime
                    -- ---------------------------------------------------------
                    SELECT
                        DATE(orh.approval_datetime)             AS snapshot_date,
                        ord.material_storage_id                 AS material_storage_id,
                        0                                       AS pending_inbound_sum,
                        0                                       AS pending_outbound_sum,
                        0                                       AS inbound_amount_sum,
                        0                                       AS outbound_amount_sum,
                        0                                       AS make_inventory_inbound_sum,
                        SUM(COALESCE(ord.outbound_amount, 0))   AS make_inventory_outbound_sum
                    FROM outbound_record_detail ord
                    JOIN outbound_record orh
                    ON orh.outbound_record_id = ord.outbound_record_id
                    WHERE orh.approval_datetime >= :start_dt
                    AND orh.approval_datetime <  :end_dt
                    AND orh.approval_status    = 1
                    AND orh.outbound_type      = 5
                    AND orh.display = 1
                    AND ord.display = 1
                    GROUP BY DATE(orh.approval_datetime), ord.material_storage_id
                ) t
                WHERE t.snapshot_date = :start_dt
                GROUP BY t.snapshot_date, t.material_storage_id
            ) agg

            -- =============================================================
            -- latest_unit_price：截止 deadline 之前，最后一次入库的单价（不分审批）
            -- =============================================================
            LEFT JOIN (
                SELECT
                    ird.material_storage_id AS material_storage_id,
                    ird.unit_price          AS unit_price
                FROM inbound_record_detail ird
                JOIN inbound_record ir
                ON ir.inbound_record_id = ird.inbound_record_id
                JOIN (
                    SELECT
                        ird2.material_storage_id AS msid,
                        MAX(
                            CONCAT(
                                DATE_FORMAT(ir2.inbound_datetime, '%Y%m%d%H%i%S'),
                                LPAD(ird2.id, 12, '0')
                            )
                        ) AS max_key
                    FROM inbound_record_detail ird2
                    JOIN inbound_record ir2
                    ON ir2.inbound_record_id = ird2.inbound_record_id
                    WHERE ir2.inbound_datetime < :end_dt
                    AND ir2.display = 1
                    AND ird2.display = 1
                    GROUP BY ird2.material_storage_id
                ) last_k
                ON last_k.msid = ird.material_storage_id
                AND CONCAT(
                        DATE_FORMAT(ir.inbound_datetime, '%Y%m%d%H%i%S'),
                        LPAD(ird.id, 12, '0')
                    ) = last_k.max_key
                WHERE ir.display = 1
                AND ird.display = 1
            ) lp
            ON lp.material_storage_id = agg.material_storage_id

            -- =============================================================
            -- avg_unit_price：截止 deadline 之前，所有“已审核入库”的加权平均价
            -- =============================================================
            LEFT JOIN (
                SELECT
                    ird.material_storage_id AS material_storage_id,
                    SUM(ird.inbound_amount * ird.unit_price)
                        / NULLIF(SUM(ird.inbound_amount), 0)   AS avg_unit_price
                FROM inbound_record_detail ird
                JOIN inbound_record ir
                ON ir.inbound_record_id = ird.inbound_record_id
                WHERE ir.approval_datetime < :end_dt
                AND ir.approval_status   = 1
                AND ir.display = 1
                AND ird.display = 1
                GROUP BY ird.material_storage_id
            ) ap
            ON ap.material_storage_id = agg.material_storage_id

            ON DUPLICATE KEY UPDATE
                latest_unit_price           = VALUES(latest_unit_price),
                avg_unit_price              = VALUES(avg_unit_price),
                pending_inbound_sum         = VALUES(pending_inbound_sum),
                pending_outbound_sum        = VALUES(pending_outbound_sum),
                inbound_amount_sum          = VALUES(inbound_amount_sum),
                outbound_amount_sum         = VALUES(outbound_amount_sum),
                make_inventory_inbound_sum  = VALUES(make_inventory_inbound_sum),
                make_inventory_outbound_sum = VALUES(make_inventory_outbound_sum),
                net_change                  = VALUES(net_change),
                update_time                 = CURRENT_TIMESTAMP
            ;
            """
        )
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
                outbound_amount,
                current_amount,
                make_inventory_inbound,
                make_inventory_outbound,
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
                ms.outbound_amount,
                ms.current_amount,
                ms.make_inventory_inbound,
                ms.make_inventory_outbound,
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
                outbound_amount = VALUES(outbound_amount),
                current_amount = VALUES(current_amount),
                make_inventory_inbound = VALUES(make_inventory_inbound),
                make_inventory_outbound = VALUES(make_inventory_outbound),
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
                outbound_amount,
                current_amount,
                make_inventory_inbound,
                make_inventory_outbound
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
                msd.outbound_amount,
                msd.current_amount
            FROM material_storage_size_detail msd
            ON DUPLICATE KEY UPDATE
                material_storage_id = VALUES(material_storage_id),
                size_value = VALUES(size_value),
                order_number = VALUES(order_number),
                pending_inbound = VALUES(pending_inbound),
                pending_outbound = VALUES(pending_outbound),
                inbound_amount = VALUES(inbound_amount),
                outbound_amount = VALUES(outbound_amount),
                current_amount = VALUES(current_amount),
                make_inventory_inbound = VALUES(make_inventory_inbound),
                make_inventory_outbound = VALUES(make_inventory_outbound),
                update_time = CURRENT_TIMESTAMP
        """)
        db.session.execute(sql_size_detail, {"snapshot_date": snapshot_date})

        db.session.commit()
        logger.info(f"📸 月末快照完成：snapshot_date={snapshot_date}")
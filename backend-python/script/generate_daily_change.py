from datetime import date, timedelta
from sqlalchemy import text, func
from models import *


def generate_daily_change(app, db):
    with app.app_context():
        start_date = date(2025, 3, 17)
        end_date = date(2025, 10, 10)
        cur = start_date
        while cur <= end_date:
            sql = text(
                """
INSERT INTO daily_material_storage_change (
    snapshot_date, material_storage_id,
    inbound_amount, outbound_amount, net_change,
    size_34_inbound_amount, size_35_inbound_amount, size_36_inbound_amount, size_37_inbound_amount,
    size_38_inbound_amount, size_39_inbound_amount, size_40_inbound_amount, size_41_inbound_amount,
    size_42_inbound_amount, size_43_inbound_amount, size_44_inbound_amount, size_45_inbound_amount, size_46_inbound_amount,
    size_34_outbound_amount, size_35_outbound_amount, size_36_outbound_amount, size_37_outbound_amount,
    size_38_outbound_amount, size_39_outbound_amount, size_40_outbound_amount, size_41_outbound_amount,
    size_42_outbound_amount, size_43_outbound_amount, size_44_outbound_amount, size_45_outbound_amount, size_46_outbound_amount,
    latest_unit_price, avg_unit_price
)
SELECT
    a.snapshot_date,
    a.material_storage_id,
    a.inbound_amount,
    a.outbound_amount,
    (a.inbound_amount - a.outbound_amount) AS net_change,
    -- 尺码入库
    a.size_34_inbound_amount, a.size_35_inbound_amount, a.size_36_inbound_amount, a.size_37_inbound_amount,
    a.size_38_inbound_amount, a.size_39_inbound_amount, a.size_40_inbound_amount, a.size_41_inbound_amount,
    a.size_42_inbound_amount, a.size_43_inbound_amount, a.size_44_inbound_amount, a.size_45_inbound_amount, a.size_46_inbound_amount,
    -- 尺码出库
    a.size_34_outbound_amount, a.size_35_outbound_amount, a.size_36_outbound_amount, a.size_37_outbound_amount,
    a.size_38_outbound_amount, a.size_39_outbound_amount, a.size_40_outbound_amount, a.size_41_outbound_amount,
    a.size_42_outbound_amount, a.size_43_outbound_amount, a.size_44_outbound_amount, a.size_45_outbound_amount, a.size_46_outbound_amount,
    lp.unit_price AS latest_unit_price,
    ap.avg_unit_price
FROM
(
    /* ===== 当日净变动汇总（不含CTE） ===== */
    SELECT
        x.snapshot_date,
        x.material_storage_id,
        SUM(x.inbound_amount)  AS inbound_amount,
        SUM(x.outbound_amount) AS outbound_amount,
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
        /* 当日入库聚合 */
        SELECT
            DATE(ir.inbound_datetime)                   AS snapshot_date,
            ird.material_storage_id                     AS material_storage_id,
            SUM(ird.inbound_amount)                     AS inbound_amount,
            0                                           AS outbound_amount,
            -- 尺码入库
            SUM(COALESCE(ird.size_34_inbound_amount,0)) AS size_34_inbound_amount,
            SUM(COALESCE(ird.size_35_inbound_amount,0)) AS size_35_inbound_amount,
            SUM(COALESCE(ird.size_36_inbound_amount,0)) AS size_36_inbound_amount,
            SUM(COALESCE(ird.size_37_inbound_amount,0)) AS size_37_inbound_amount,
            SUM(COALESCE(ird.size_38_inbound_amount,0)) AS size_38_inbound_amount,
            SUM(COALESCE(ird.size_39_inbound_amount,0)) AS size_39_inbound_amount,
            SUM(COALESCE(ird.size_40_inbound_amount,0)) AS size_40_inbound_amount,
            SUM(COALESCE(ird.size_41_inbound_amount,0)) AS size_41_inbound_amount,
            SUM(COALESCE(ird.size_42_inbound_amount,0)) AS size_42_inbound_amount,
            SUM(COALESCE(ird.size_43_inbound_amount,0)) AS size_43_inbound_amount,
            SUM(COALESCE(ird.size_44_inbound_amount,0)) AS size_44_inbound_amount,
            SUM(COALESCE(ird.size_45_inbound_amount,0)) AS size_45_inbound_amount,
            SUM(COALESCE(ird.size_46_inbound_amount,0)) AS size_46_inbound_amount,
            -- 出库尺码占位
            0 AS size_34_outbound_amount, 0 AS size_35_outbound_amount, 0 AS size_36_outbound_amount,
            0 AS size_37_outbound_amount, 0 AS size_38_outbound_amount, 0 AS size_39_outbound_amount,
            0 AS size_40_outbound_amount, 0 AS size_41_outbound_amount, 0 AS size_42_outbound_amount,
            0 AS size_43_outbound_amount, 0 AS size_44_outbound_amount, 0 AS size_45_outbound_amount,
            0 AS size_46_outbound_amount
        FROM inbound_record_detail ird
        JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
        WHERE ir.inbound_datetime >= :now_date
          AND ir.inbound_datetime <  :deadline
        GROUP BY DATE(ir.inbound_datetime), ird.material_storage_id

        UNION ALL

        /* 当日出库聚合 */
        SELECT
            DATE(orh.outbound_datetime)                   AS snapshot_date,
            ord.material_storage_id                       AS material_storage_id,
            0                                             AS inbound_amount,
            SUM(COALESCE(ord.outbound_amount,0))          AS outbound_amount,
            -- 入库尺码占位
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
        JOIN outbound_record orh ON orh.outbound_record_id = ord.outbound_record_id
        WHERE orh.outbound_datetime >= :now_date
          AND orh.outbound_datetime <  :deadline
        GROUP BY DATE(orh.outbound_datetime), ord.material_storage_id
    ) x
    GROUP BY x.snapshot_date, x.material_storage_id
) a
/* ===== 截止当日（含历史回溯）的“最新单价” =====
   逻辑：在 :deadline 之前的所有入库里，取每个 msid 的最后一条明细的 unit_price
   如需仅统计已审批数据，可在内外 WHERE 中加 AND ir.approval_status = 1
*/
LEFT JOIN (
    SELECT
        ird.material_storage_id AS material_storage_id,
        ird.unit_price
    FROM inbound_record_detail ird
    JOIN inbound_record ir
      ON ir.inbound_record_id = ird.inbound_record_id
    JOIN (
        SELECT
            ird2.material_storage_id AS msid,
            MAX(CONCAT(DATE_FORMAT(ir2.inbound_datetime, '%Y%m%d%H%i%S'),
                       LPAD(ird2.id, 12, '0'))) AS max_key
        FROM inbound_record_detail ird2
        JOIN inbound_record ir2
          ON ir2.inbound_record_id = ird2.inbound_record_id
        WHERE ir2.inbound_datetime < :deadline
        -- AND ir2.approval_status = 1  -- 如果需要只看已审批，取消注释
        GROUP BY ird2.material_storage_id
    ) last_k
      ON last_k.msid = ird.material_storage_id
     AND CONCAT(DATE_FORMAT(ir.inbound_datetime, '%Y%m%d%H%i%S'),
                LPAD(ird.id, 12, '0')) = last_k.max_key
) lp
  ON lp.material_storage_id = a.material_storage_id
/* ===== 截止当日（累计）“加权平均单价”（仅审批=1） =====
   逻辑：在当日截止时间 :deadline 之前的所有已审批入库，做 累计金额 / 累计数量
*/
LEFT JOIN (
    SELECT
        ird.material_storage_id AS material_storage_id,
        SUM(ird.inbound_amount * ird.unit_price) / NULLIF(SUM(ird.inbound_amount), 0) AS avg_unit_price
    FROM inbound_record_detail ird
    JOIN inbound_record ir ON ir.inbound_record_id = ird.inbound_record_id
    WHERE ir.inbound_datetime < :deadline
      AND ir.approval_status   = 1
    GROUP BY ird.material_storage_id
) ap
  ON ap.material_storage_id = a.material_storage_id

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
    latest_unit_price        = VALUES(latest_unit_price),
    avg_unit_price           = VALUES(avg_unit_price),
    update_time              = CURRENT_TIMESTAMP;
                """
            )
            # 设置 now_date 和 next_date
            db.session.execute(
                sql, {"now_date": cur, "deadline": cur + timedelta(days=1)}
            )
            db.session.commit()
            print(f"✅ {cur} 已生成每日净变动记录。")
            cur += timedelta(days=1)

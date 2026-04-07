-- 为 shoe_outbound_apply 表添加 apply_type 字段
-- 0 = 业务发起（走审核流程，旧流程）
-- 1 = 仓库发起（一步完成，仅通知业务/总经理）
-- 先检查列是否已存在，避免重复执行出错
SET SQL_SAFE_UPDATES = 0;
SET @db_name = DATABASE();
SET @col_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db_name
      AND TABLE_NAME = 'shoe_outbound_apply'
      AND COLUMN_NAME = 'apply_type'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE shoe_outbound_apply ADD COLUMN apply_type SMALLINT NOT NULL DEFAULT 0 COMMENT ''0=业务发起 1=仓库发起'' AFTER status',
    'SELECT ''Column apply_type already exists, skipping.'' AS info'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================
-- 为 shoe_outbound_apply_detail 表添加 actual_outbound_pairs 字段
-- NULL = 未执行出库，有值 = 已执行出库（实际出库双数）
-- ============================================================
SET @col_exists2 = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db_name
      AND TABLE_NAME = 'shoe_outbound_apply_detail'
      AND COLUMN_NAME = 'actual_outbound_pairs'
);

SET @sql2 = IF(@col_exists2 = 0,
    'ALTER TABLE shoe_outbound_apply_detail ADD COLUMN actual_outbound_pairs INT DEFAULT NULL COMMENT ''实际出库双数, NULL=未执行'' AFTER total_pairs',
    'SELECT ''Column actual_outbound_pairs already exists, skipping.'' AS info'
);

PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- ============================================================
-- 修复历史数据：已完成出库(status=4)的申请明细 total_pairs 被置0
-- 从出库记录明细(ShoeOutboundRecordDetail)反推实际出库数量
-- 同时回填 actual_outbound_pairs 和 total_pairs
-- ============================================================
UPDATE shoe_outbound_apply_detail sad
JOIN shoe_outbound_apply soa ON soa.apply_id = sad.apply_id
SET
    sad.actual_outbound_pairs = (
        SELECT COALESCE(SUM(sord.outbound_amount), 0)
        FROM shoe_outbound_record sor
        JOIN shoe_outbound_record_detail sord
            ON sord.shoe_outbound_record_id = sor.shoe_outbound_record_id
        WHERE sor.apply_id = soa.apply_id
          AND sord.finished_shoe_storage_id = sad.finished_shoe_storage_id
    ),
    sad.total_pairs = (
        SELECT COALESCE(SUM(sord.outbound_amount), 0)
        FROM shoe_outbound_record sor
        JOIN shoe_outbound_record_detail sord
            ON sord.shoe_outbound_record_id = sor.shoe_outbound_record_id
        WHERE sor.apply_id = soa.apply_id
          AND sord.finished_shoe_storage_id = sad.finished_shoe_storage_id
    )
WHERE soa.status = 4
  AND sad.total_pairs = 0
  AND sad.actual_outbound_pairs IS NULL;

SET SQL_SAFE_UPDATES = 1;

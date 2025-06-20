
SET SQL_SAFE_UPDATES = 0;
-- 1. 备份 spu_material 表为 spu_material_backup（如果已存在就先删除）
DROP TABLE IF EXISTS spu_material_backup;
CREATE TABLE spu_material_backup AS
SELECT * FROM spu_material;

-- 2. 清空原始 spu_material 表
TRUNCATE TABLE spu_material;

-- 插入去重后的新记录，先将 NULL 统一转为空字符串
INSERT INTO spu_material (
    material_id,
    material_model,
    material_specification,
    color,
    spu_rid
)
SELECT
    material_id,
    IFNULL(material_model, '') AS material_model,
    IFNULL(material_specification, '') AS material_specification,
    IFNULL(color, '') AS color,
    MIN(spu_rid) AS spu_rid
FROM spu_material_backup
GROUP BY
    material_id,
    IFNULL(material_model, ''),
    IFNULL(material_specification, ''),
    IFNULL(color, '');

-- 4. 创建持久化的实体映射表（旧 spu_material_id → 新 spu_material_id）
DROP TABLE IF EXISTS spu_material_id_mapping;
CREATE TABLE spu_material_id_mapping AS
SELECT
    smb.spu_material_id AS old_spu_material_id,
    sm.spu_material_id AS new_spu_material_id
FROM spu_material_backup AS smb
JOIN spu_material AS sm
  ON smb.material_id = sm.material_id
 AND IFNULL(smb.material_model, '') = IFNULL(sm.material_model, '')
 AND IFNULL(smb.material_specification, '') = IFNULL(sm.material_specification, '')
 AND IFNULL(smb.color, '') = IFNULL(sm.color, '');
 
DROP TABLE IF EXISTS spu_material_id_mapping;
DROP TABLE IF EXISTS spu_material_backup;
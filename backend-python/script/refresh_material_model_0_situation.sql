SET SQL_SAFE_UPDATES = 0;

-- 1. production_instruction_item
UPDATE jiancheng.production_instruction_item
SET material_model = CONCAT(
    SUBSTRING_INDEX(material_model, '-', 1), 
    '-', 
    TRIM(LEADING '0' FROM SUBSTRING_INDEX(material_model, '-', -1))
)
WHERE material_model LIKE '%-0%' 
  AND material_id = 249 
  AND production_instruction_item_id IS NOT NULL;

-- 2. bom_item
UPDATE jiancheng.bom_item
SET material_model = CONCAT(
    SUBSTRING_INDEX(material_model, '-', 1),
    '-',
    TRIM(LEADING '0' FROM SUBSTRING_INDEX(material_model, '-', -1))
)
WHERE material_model LIKE '%-0%' 
  AND material_id = 249 
  AND bom_item_id IS NOT NULL;

-- 3. purchase_order_item
UPDATE jiancheng.purchase_order_item
SET material_model = CONCAT(
    SUBSTRING_INDEX(material_model, '-', 1),
    '-',
    TRIM(LEADING '0' FROM SUBSTRING_INDEX(material_model, '-', -1))
)
WHERE material_model LIKE '%-0%' 
  AND material_id = 249 
  AND purchase_order_item_id IS NOT NULL;

-- 4. material_storage
UPDATE jiancheng.material_storage
SET material_model = CONCAT(
    SUBSTRING_INDEX(material_model, '-', 1),
    '-',
    TRIM(LEADING '0' FROM SUBSTRING_INDEX(material_model, '-', -1))
)
WHERE material_model LIKE '%-0%' 
  AND material_id = 249 
  AND material_storage_id IS NOT NULL;

-- 5. craft_sheet_item
UPDATE jiancheng.craft_sheet_item
SET material_model = CONCAT(
    SUBSTRING_INDEX(material_model, '-', 1),
    '-',
    TRIM(LEADING '0' FROM SUBSTRING_INDEX(material_model, '-', -1))
)
WHERE material_model LIKE '%-0%' 
  AND material_id = 249 
  AND craft_sheet_item_id IS NOT NULL;



SET SQL_SAFE_UPDATES = 1;
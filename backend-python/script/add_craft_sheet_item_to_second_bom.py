from app_config import db
from models import *
from logger import logger
from collections import Counter, defaultdict
from sqlalchemy import func


def add_craft_sheet_item_to_second_bom(app):
    with app.app_context():
        # ---- 第1步：批量查询所有已下发工艺单明细 ----
        print("正在查询工艺单明细...")
        craft_sheets = (
            db.session.query(CraftSheetItem)
            .join(
                CraftSheet, CraftSheet.craft_sheet_id == CraftSheetItem.craft_sheet_id
            )
            .filter(CraftSheet.craft_sheet_status.in_([2, 3]))
            .all()
        )
        print(f"共查询到 {len(craft_sheets)} 条工艺单明细")

        # 收集所有涉及的 order_shoe_type_id
        ost_ids = set(item.order_shoe_type_id for item in craft_sheets)
        print(f"涉及 {len(ost_ids)} 个 order_shoe_type_id")

        # ---- 第2步：批量查询每个 ost_id 对应的最新二次 BOM ----
        print("正在查询二次BOM...")
        # 子查询：每个 ost_id 对应的最大 bom_id（即最新二次BOM）
        latest_bom_subq = (
            db.session.query(
                Bom.order_shoe_type_id,
                func.max(Bom.bom_id).label("max_bom_id"),
            )
            .filter(Bom.bom_type == 1)
            .filter(Bom.order_shoe_type_id.in_(ost_ids))
            .group_by(Bom.order_shoe_type_id)
            .all()
        )
        # ost_id -> 最新 bom_id
        ost_to_bom_id = {row.order_shoe_type_id: row.max_bom_id for row in latest_bom_subq}
        print(f"找到 {len(ost_to_bom_id)} 个二次BOM")

        all_bom_ids = set(ost_to_bom_id.values())

        # ---- 第3步：批量查询这些 BOM 中 add_type=1 的所有 BomItem ----
        print("正在查询已有的二次BOM明细...")
        existing_bom_items = (
            db.session.query(BomItem)
            .filter(BomItem.bom_id.in_(all_bom_ids))
            .filter(BomItem.bom_item_add_type == "1")
            .all()
        )
        print(f"已有 {len(existing_bom_items)} 条 add_type=1 二次BOM明细")

        # 建立索引: (bom_id, material_id, spec, model, color) -> Counter(craft_name)
        existing_index = defaultdict(Counter)
        for bi in existing_bom_items:
            key = (
                bi.bom_id,
                bi.material_id,
                bi.material_specification or "",
                bi.material_model or "",
                (bi.bom_item_color or "").strip(),
            )
            craft = (bi.craft_name or "").strip()
            existing_index[key][craft] += 1

        # ---- 第4步：遍历工艺单明细，内存比对，找出缺失 ----
        print("正在比对并生成缺失记录...")
        total_added = 0
        for idx, item in enumerate(craft_sheets, 1):
            if idx % 5000 == 0:
                print(f"  已处理 {idx}/{len(craft_sheets)} ...")

            bom_id = ost_to_bom_id.get(item.order_shoe_type_id)
            if not bom_id:
                continue

            # 规范化工艺：按 @ 拆分并去掉空白，空工艺保留一条空字符串记录
            craft_list = []
            if item.craft_name and str(item.craft_name).strip():
                craft_list = [c.strip() for c in str(item.craft_name).split("@") if c.strip()]
            if not craft_list:
                craft_list = [""]

            key = (
                bom_id,
                item.material_id,
                item.material_specification or "",
                item.material_model or "",
                (item.color or "").strip(),
            )
            existing_craft_counter = existing_index[key]
            target_craft_counter = Counter((craft or "").strip() for craft in craft_list)

            for normalized_craft, target_count in target_craft_counter.items():
                existing_count = existing_craft_counter.get(normalized_craft, 0)
                deficit = max(0, target_count - existing_count)
                for _ in range(deficit):
                    new_bom_item = BomItem(
                        bom_id=bom_id,
                        material_id=item.material_id,
                        material_model=item.material_model,
                        material_specification=item.material_specification,
                        bom_item_color=item.color,
                        remark=item.remark,
                        department_id=item.department_id,
                        size_type="E",
                        bom_item_add_type="1",
                        unit_usage=0.0,
                        total_usage=0,
                        material_second_type=item.material_second_type,
                        craft_name=normalized_craft,
                        production_instruction_item_id=item.production_instruction_item_id,
                    )
                    db.session.add(new_bom_item)
                    total_added += 1
                    # 同步更新内存索引，避免同一 ost 的后续 item 重复插入
                    existing_craft_counter[normalized_craft] += 1

        print(f"比对完成，准备提交 {total_added} 条新记录...")
        db.session.commit()
        print(f"处理完成，共新增 {total_added} 条二次BOM明细")
        logger.info(f"add_craft_sheet_item_to_second_bom finished, total added = {total_added}")

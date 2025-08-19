from app_config import db
from models import *
from technical import second_bom
from logger import logger


def add_craft_sheet_item_to_second_bom(app):
    with app.app_context():
        craft_sheets = (
            db.session.query(CraftSheetItem)
            .join(
                CraftSheet, CraftSheet.craft_sheet_id == CraftSheetItem.craft_sheet_id
            )
            .filter(CraftSheet.craft_sheet_status == 2)
            .all()
        )
        for item in craft_sheets:
            if item.production_instruction_item_id == None:
                bom_item = (
                    db.session.query(BomItem, Bom)
                    .filter(BomItem.bom_item_add_type == 1)
                    .filter(BomItem.material_id == item.material_id)
                    .join(Bom, Bom.bom_id == BomItem.bom_id)
                    .filter(
                        BomItem.material_specification == item.material_specification
                    )
                    .filter(BomItem.material_model == item.material_model)
                    .filter(BomItem.bom_item_color == item.color)
                    .filter(Bom.order_shoe_type_id == item.order_shoe_type_id)
                    .first()
                )
                if not bom_item:
                    second_bom = (
                        db.session.query(Bom)
                        .filter(Bom.order_shoe_type_id == item.order_shoe_type_id)
                        .filter(Bom.bom_type == 1)
                        .first()
                    )
                    if second_bom:
                        second_bom_id = second_bom.bom_id
                        craft_list = item.craft_name.split("@")
                        if craft_list != []:
                            for craft in craft_list:
                                new_bom_item = BomItem(
                                    bom_id=second_bom_id,
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
                                    craft_name=craft,
                                    production_instruction_item_id = item.production_instruction_item_id
                                )
                        else:
                            new_bom_item = BomItem(
                                bom_id=second_bom_id,
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
                                craft_name="",
                                production_instruction_item_id=item.production_instruction_item_id
                            )
                        db.session.add(new_bom_item)
                        db.session.flush()
                        logger.debug(f"Added new second BOM item: {item.craft_sheet_item_id} to BOM {second_bom_id}")

        db.session.commit()

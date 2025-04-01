from models import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

def refresh_storage_craft_match_craft_sheet(app, db):
    with app.app_context():
        material_storage = db.session.query(MaterialStorage).all()
        for storage in material_storage:
            craft_item = (
                db.session.query(CraftSheetItem, ProductionInstructionItem)
                .join(
                    ProductionInstructionItem,
                    ProductionInstructionItem.production_instruction_item_id == CraftSheetItem.production_instruction_item_id,
                )
                .filter(
                    ProductionInstructionItem.production_instruction_item_id == storage.production_instruction_item_id
                )
                .first()
            )

            if craft_item:
                craft_sheet, prod_item = craft_item
                original_crafts = set(filter(None, (craft_sheet.craft_name or "").split("@")))
                
                if prod_item.material_type == "I":
                    # Find all similar hotsole entries
                    similiar_hotsoles = (
                        db.session.query(ProductionInstructionItem)
                        .filter(
                            ProductionInstructionItem.material_id == prod_item.material_id,
                            ProductionInstructionItem.material_model == prod_item.material_model,
                            ProductionInstructionItem.material_specification == prod_item.material_specification,
                            ProductionInstructionItem.color == prod_item.color,
                            ProductionInstructionItem.order_shoe_type_id == prod_item.order_shoe_type_id,
                            ProductionInstructionItem.material_type == "H"
                        )
                        .all()
                    )

                    hotsole_craft_names = set()
                    for hotsole in similiar_hotsoles:
                        if hotsole.pre_craft_name:
                            hotsole_craft_names.update(hotsole.pre_craft_name.split("@"))

                    # Combine and avoid duplicates
                    combined_crafts = original_crafts.union(hotsole_craft_names)
                    storage.craft_name = "@".join(sorted(combined_crafts))
                else:
                    storage.craft_name = craft_sheet.craft_name or None

                db.session.flush()

        size_material_storage = db.session.query(SizeMaterialStorage).all()
        for storage in size_material_storage:
            craft_item = (
                db.session.query(CraftSheetItem)
                .filter(
                    CraftSheetItem.production_instruction_item_id == storage.production_instruction_item_id
                )
                .first()
            )
            if craft_item:
                storage.craft_name = craft_item.craft_name
                db.session.flush()

        db.session.commit()


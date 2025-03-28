from models import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

def refresh_storage_craft_match_craft_sheet(app, db):
    with app.app_context():
        connection = db.engine.connect()
        inspector = inspect(db.engine)
        material_storage = db.session.query(MaterialStorage).all()
        for storage in material_storage:
            craft_item = (
                db.session.query(CraftSheetItem, ProductionInstructionItem)
                .join(
                    ProductionInstructionItem,
                    ProductionInstructionItem.production_instruction_item_id
                    == CraftSheetItem.production_instruction_item_id,
                )
                .filter(
                    ProductionInstructionItem.production_instruction_item_id == storage.production_instruction_item_id
                )
                .first()
            )
            if craft_item:
                if craft_item.ProductionInstructionItem.material_type == "I":
                    # find similiar hotsole
                    similiar_hotsole = (
                        db.session.query(ProductionInstructionItem)
                        .filter(
                            ProductionInstructionItem.material_id == craft_item.ProductionInstructionItem.material_id,
                            ProductionInstructionItem.material_model == craft_item.ProductionInstructionItem.material_model,
                            ProductionInstructionItem.material_specification == craft_item.ProductionInstructionItem.material_specification,
                            ProductionInstructionItem.color == craft_item.ProductionInstructionItem.color,
                            ProductionInstructionItem.order_shoe_type_id == craft_item.ProductionInstructionItem.order_shoe_type_id,
                            ProductionInstructionItem.material_type == "H"
                            )
                        .first()
                    )
                    hotsole_craft_name = similiar_hotsole.pre_craft_name if similiar_hotsole else None
                    if hotsole_craft_name:
                        if craft_item.CraftSheetItem.craft_name:
                            new_hotsole_craft_name = craft_item.CraftSheetItem.craft_name + "@" + hotsole_craft_name
                        else:
                            new_hotsole_craft_name = hotsole_craft_name
                        storage.craft_name = new_hotsole_craft_name
                    else:
                        storage.craft_name = craft_item.CraftSheetItem.craft_name
                    db.session.flush()
        size_material_storage = db.session.query(SizeMaterialStorage).all()
        for storage in size_material_storage:
            craft_item = (
                db.session.query(CraftSheetItem)
                .filter(
                    CraftSheetItem.production_instruction_item_id
                    == storage.production_instruction_item_id
                )
                .first()
            )
            if craft_item:
                storage.craft_name = craft_item.craft_name
                db.session.flush()
        db.session.commit()

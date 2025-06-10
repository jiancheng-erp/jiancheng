from ast import IsNot
from general_document import prodution_instruction
from models import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from logger import logger
#delete the space at the begining/end of the string columns and delete '色' at the end of the color columns
def format_space_and_color_stynax(app, db):
    with app.app_context():
        # Define the list of columns to be processed
        columns_to_process = [
            'craft_name',
            'color',
            'bom_item_color',
            'size_material_color',
            'material_storage_color',
            'material_name',
            'material_model',
            'material_specification',
            'size_material_model',
            'size_material_specification',
        ]

        # Process MaterialStorage table
        material_storage = db.session.query(MaterialStorage).all()
        for storage in material_storage:
            for column in columns_to_process:
                if hasattr(storage, column):
                    value = getattr(storage, column)
                    if value is not None:
                        # Remove leading/trailing spaces and '色' from color columns
                        if column == 'material_storage_color':
                            value = value.strip().replace('色', '').replace(' ', '')
                        else:
                            value = value.strip()
                        setattr(storage, column, value)
                        db.session.flush()  # Flush changes to the database

        # Process SizeMaterialStorage table
        size_material_storage = db.session.query(SizeMaterialStorage).all()
        for storage in size_material_storage:
            for column in columns_to_process:
                if hasattr(storage, column):
                    value = getattr(storage, column)
                    if value is not None:
                        # Remove leading/trailing spaces and '色' from color columns
                        if column == 'size_material_color':
                            value = value.strip().replace('色', '').replace(' ', '')
                        else:
                            value = value.strip()
                        setattr(storage, column, value)
                        db.session.flush()  # Flush changes to the database
        bom_item = db.session.query(BomItem).all()
        for item in bom_item:
            for column in columns_to_process:
                if hasattr(item, column):
                    value = getattr(item, column)
                    if value is not None:
                        # Remove leading/trailing spaces and '色' from color columns
                        if column == 'bom_item_color':
                            value = value.strip().replace('色', '').replace(' ', '')
                        else:
                            value = value.strip()
                        setattr(item, column, value)
                        db.session.flush()  # Flush changes to the database
        prodution_instruction_items = db.session.query(ProductionInstructionItem).all()
        for item in prodution_instruction_items:
            for column in columns_to_process:
                if hasattr(item, column):
                    value = getattr(item, column)
                    if value is not None:
                        # Remove leading/trailing spaces and '色' from color columns
                        if column == 'color':
                            value = value.strip().replace('色', '').replace(' ', '')
                        else:
                            value = value.strip()
                        setattr(item, column, value)
                        db.session.flush()  # Flush changes to the database
        purchase_order_items = db.session.query(PurchaseOrderItem).all()
        for item in purchase_order_items:
            for column in columns_to_process:
                if hasattr(item, column):
                    value = getattr(item, column)
                    if value is not None:
                        # Remove leading/trailing spaces and '色' from color columns
                        if column == 'color':
                            value = value.strip().replace('色', '').replace(' ', '')
                        else:
                            value = value.strip()
                        setattr(item, column, value)
                        db.session.flush()  # Flush changes to the database
        craft_sheet_items = db.session.query(CraftSheetItem).all()
        for item in craft_sheet_items:
            for column in columns_to_process:
                if hasattr(item, column):
                    value = getattr(item, column)
                    if value is not None:
                        # Remove leading/trailing spaces and '色' from color columns
                        if column == 'color':
                            value = value.strip().replace('色', '').replace(' ', '')
                        else:
                            value = value.strip()
                        setattr(item, column, value)
                        db.session.flush()  # Flush changes to the database
        # Commit the changes to the database
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.debug(f"Error committing changes: {e}")
        finally:
            db.session.close()
        
        
    
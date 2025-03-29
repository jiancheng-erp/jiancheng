from models import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

def refresh_default_craft_sheet(app, db):
    print("Refreshing default craft sheet...")
    with app.app_context():
        connection = db.engine.connect()
        inspector = inspect(db.engine)
        shoes = db.session.query(Shoe).all()
        for shoe in shoes:
            default_craft_sheet = db.session.query(DefaultCraftSheet).filter(DefaultCraftSheet.shoe_id == shoe.shoe_id).first()
            if default_craft_sheet:
                continue
            else:
                craft_sheet = db.session.query(CraftSheet, OrderShoe, Shoe).join(
                    OrderShoe, OrderShoe.order_shoe_id == CraftSheet.order_shoe_id
                ).join(
                    Shoe, Shoe.shoe_id == OrderShoe.shoe_id
                ).filter(
                    OrderShoe.shoe_id == shoe.shoe_id,
                    CraftSheet.craft_sheet_status != "1"
                ).first()
                if craft_sheet:
                    default_craft_sheet = DefaultCraftSheet(
                        shoe_id=shoe.shoe_id,
                        craft_sheet_id=craft_sheet.CraftSheet.craft_sheet_id,
                    )
                    db.session.add(default_craft_sheet)
                    db.session.flush()
        db.session.commit()
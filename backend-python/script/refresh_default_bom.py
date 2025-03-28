from models import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError


def refresh_default_bom(app, db):
    print("Refreshing default BOM...")
    with app.app_context():
        connection = db.engine.connect()
        inspector = inspect(db.engine)
        shoe_types = db.session.query(ShoeType).all()
        for shoe_type in shoe_types:
            default_first_bom = (
                db.session.query(DefaultBom).filter(
                    DefaultBom.shoe_type_id == shoe_type.shoe_type_id,
                    DefaultBom.bom_type == 0,
                )
            ).first()
            if not default_first_bom:
                first_bom = (
                    db.session.query(Bom, OrderShoeType, ShoeType).join(
                        OrderShoeType,
                        OrderShoeType.order_shoe_type_id == Bom.order_shoe_type_id,
                    )
                    .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
                    .filter(
                        OrderShoeType.shoe_type_id == shoe_type.shoe_type_id,
                        Bom.bom_type == 0,
                    )
                    .first()
                )
                if first_bom:
                    default_first_bom = DefaultBom(
                        shoe_type_id=shoe_type.shoe_type_id,
                        bom_id=first_bom.Bom.bom_id,
                        bom_type=0,
                        bom_status="2"
                    )
                    db.session.add(default_first_bom)
                    db.session.flush()
            default_second_bom = (
                db.session.query(DefaultBom).filter(
                    DefaultBom.shoe_type_id == shoe_type.shoe_type_id,
                    DefaultBom.bom_type == 1,
                )
            ).first()
            if not default_second_bom:
                second_bom = (
                    db.session.query(Bom, OrderShoeType, ShoeType).join(
                        OrderShoeType,
                        OrderShoeType.order_shoe_type_id == Bom.order_shoe_type_id,
                    )
                    .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
                    .filter(
                        OrderShoeType.shoe_type_id == shoe_type.shoe_type_id,
                        Bom.bom_type == 1,
                    )
                    .first()
                )
                if second_bom:
                    default_second_bom = DefaultBom(
                        shoe_type_id=shoe_type.shoe_type_id,
                        bom_id=second_bom.Bom.bom_id,
                        bom_type=1,
                        bom_status="2"
                    )
                    db.session.add(default_second_bom)
                    db.session.flush()
            

        db.session.commit()

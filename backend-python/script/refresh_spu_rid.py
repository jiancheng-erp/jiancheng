import random
import time

from numpy import size
from models import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from file_locations import FILE_STORAGE_PATH, IMAGE_UPLOAD_PATH
import os
from logger import logger
from warehouse import material_storage

NAME_TO_FIRST_ALPHABET = {
    '面料': 'ML',
    '里料': 'LL',
    '辅料': 'FL',
    '化工': 'HG',
    '饰品': 'SP',
    '包材': 'BC',
    '底材': 'DC',
    '生产工具': 'SC',
    '复合': 'FH',
    '加工': 'JG',
    '刀模': 'DM',
    '楦头': 'XT',
    '办公后勤': 'BG',
    '开发样品': 'KF',
    '固定资产': 'GD',
    '烫底': 'TD'
}
    


def refresh_spu_rid(app, db):
    logger.debug("Refreshing spu rid...")

    def normalize_empty(value):
        return value if value not in ("", None) else None

    def safe_equal(column, value):
        return column.is_(None) if value is None else column == value

    with app.app_context():
        material_storages = db.session.query(MaterialStorage).all()
        for material_storage in material_storages:
            model = normalize_empty(material_storage.inbound_model)
            spec = normalize_empty(material_storage.inbound_specification)
            color = normalize_empty(material_storage.material_storage_color)

            spu_material = db.session.query(SPUMaterial).filter(
                SPUMaterial.material_id == material_storage.actual_inbound_material_id,
                safe_equal(SPUMaterial.material_model, model),
                safe_equal(SPUMaterial.material_specification, spec),
                safe_equal(SPUMaterial.color, color),
            ).first()

            if not spu_material:
                spu_material_rid = generate_spu_rid(material_storage.actual_inbound_material_id)
                spu_material = SPUMaterial(
                    material_id=material_storage.actual_inbound_material_id,
                    material_model=model if model else '',
                    material_specification=spec if spec else '',
                    color=color if color else '',
                    spu_rid=spu_material_rid,
                )
                db.session.add(spu_material)
                db.session.flush()

            material_storage.spu_material_id = spu_material.spu_material_id
            db.session.flush()

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.debug(f"Error committing changes: {e}")
            raise e

def generate_spu_rid(material_id):
    # Generate a new spu_rid using an algorithm
    # This is a placeholder function. You should implement your own logic to generate a unique spu_rid.
    material_type_name = db.session.query(MaterialType, Material).join(
        Material, Material.material_type_id == MaterialType.material_type_id
    ).filter(
        Material.material_id == material_id
    ).first().MaterialType.material_type_name
    
    if material_type_name:
        first_alphabet = NAME_TO_FIRST_ALPHABET.get(material_type_name, 'XX')
        time_stamp = int(time.time())
        random_number = random.randint(1000, 9999)
        spu_rid = f"SPU{first_alphabet}{time_stamp}{random_number}"
        return spu_rid
    else:
        raise ValueError("Material type name not found in the database.")
    
    
    
def batch_update_spu_material_id(app, db, batch_size=1000):
    logger.info("Starting batch update for spu_material_id from material_storage...")

    with app.app_context():
        # 加载整个映射表到内存（dict 结构），只做一次
        logger.info("Loading spu_material_id_mapping into memory...")
        mapping_rows = db.session.execute(text("SELECT old_spu_material_id, new_spu_material_id FROM spu_material_id_mapping")).fetchall()
        mapping_dict = {row.old_spu_material_id: row.new_spu_material_id for row in mapping_rows}
        logger.info(f"Loaded {len(mapping_dict)} mapping records.")

        offset = 0
        total_updated = 0

        while True:
            # 分批获取 material_storage 记录
            storages = db.session.query(MaterialStorage).order_by(MaterialStorage.material_storage_id).offset(offset).limit(batch_size).all()
            if not storages:
                break

            for storage in storages:
                old_id = storage.spu_material_id
                new_id = mapping_dict.get(old_id)
                if new_id and new_id != old_id:
                    storage.spu_material_id = new_id

            db.session.commit()
            updated_count = len(storages)
            total_updated += updated_count
            offset += batch_size
            logger.info(f"Updated batch of {updated_count}, total updated: {total_updated}")

        logger.info(f"Finished updating spu_material_id in material_storage. Total: {total_updated}")
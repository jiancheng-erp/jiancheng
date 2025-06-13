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
    with app.app_context():
        # loop all material_storage and size_material_storage, and update the spu_table.
        # if not have a spu row, create it;if have, use the spu_material_id(use inbound_material_id,
        # inbound_material_model,inbound_material_specification,color for material_storage;
        # material_id,material_model,material_specification,color for size_material_storage
        # ), then insert the spu_material_id to material_storage and size_material_storage
        material_storages = db.session.query(MaterialStorage).all()
        for material_storage in material_storages:
            # get the spu_material_id from the database
            spu_material = db.session.query(SPUMaterial).filter(
                SPUMaterial.material_id == material_storage.actual_inbound_material_id,
                SPUMaterial.material_model == material_storage.inbound_model,
                SPUMaterial.material_specification == material_storage.inbound_specification,
                SPUMaterial.color == material_storage.material_storage_color,
            ).first()
            if not spu_material:
                # create a new spu_material
                # use algorithm to generate a new spu_material_rid
                spu_material_rid = generate_spu_rid(material_storage.actual_inbound_material_id)
                
                
                spu_material = SPUMaterial(
                    material_id=material_storage.actual_inbound_material_id,
                    material_model=material_storage.inbound_model,
                    material_specification=material_storage.inbound_specification,
                    color=material_storage.material_storage_color,
                    spu_rid=spu_material_rid,
                )
                db.session.add(spu_material)
                db.session.flush()
            # update the spu_rid to material_storage and size_material_storage
            material_storage.spu_material_id = spu_material.spu_material_id
            db.session.flush()
        # update the spu_rid to size_material_storage
        size_material_storages = db.session.query(SizeMaterialStorage).all()
        for size_material_storage in size_material_storages:
            # get the spu_material_id from the database
            spu_material = db.session.query(SPUMaterial).filter(
                SPUMaterial.material_id == size_material_storage.material_id,
                SPUMaterial.material_model == size_material_storage.size_material_model,
                SPUMaterial.material_specification == size_material_storage.size_material_specification,
                SPUMaterial.color == size_material_storage.size_material_color,
            ).first()
            if not spu_material:
                # create a new spu_material
                # use algorithm to generate a new spu_material_rid
                spu_material_rid = generate_spu_rid(size_material_storage.material_id)
                
                
                spu_material = SPUMaterial(
                    material_id=size_material_storage.material_id,
                    material_model=size_material_storage.size_material_model,
                    material_specification=size_material_storage.size_material_specification,
                    color=size_material_storage.size_material_color,
                    spu_rid=spu_material_rid,
                )
                db.session.add(spu_material)
                db.session.flush()
            # update the spu_rid to size_material_storage
            size_material_storage.spu_material_id = spu_material.spu_material_id
            db.session.flush()
        # commit the changes to the database
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
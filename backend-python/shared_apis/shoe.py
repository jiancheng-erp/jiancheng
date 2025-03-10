from flask import Blueprint, jsonify, request

from app_config import app, db
from models import *
from file_locations import IMAGE_STORAGE_PATH
from api_utility import to_camel, to_snake
from login.login import current_user, current_user_info

shoe_bp = Blueprint("shoe_bp", __name__)

SHOE_TABLE_ATTRNAMES = Shoe.__table__.columns.keys()
SHOETYPE_TABLE_ATTRNAMES = ShoeType.__table__.columns.keys()
@shoe_bp.route("/shoe/getallshoes", methods=["GET"])
def get_all_shoes():
    shoe_rid = request.args.get("shoerid")
    if shoe_rid is None:
        shoes = (
            db.session.query(Shoe, ShoeType, Color)
            .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
            .join(Color, ShoeType.color_id == Color.color_id)
            .all()
        )
    else:
        shoes = (
            db.session.query(Shoe, ShoeType, Color)
            .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
            .join(Color, ShoeType.color_id == Color.color_id)
            .filter(Shoe.shoe_rid.like(f"%{shoe_rid}%"))
            .all()
        )
    result = []
    for shoe, shoe_type, color in shoes:
        result.append(
            {
                "shoeId": shoe.shoe_id,
                "shoeTypeId": shoe_type.shoe_type_id,
                "shoeRId": shoe.shoe_rid,
                "shoeImage": shoe_type.shoe_image_url,
                "shoeDesigner": shoe.shoe_designer,
                "shoeColor": color.color_name,
                "shoeImage": (
                    IMAGE_STORAGE_PATH + shoe_type.shoe_image_url
                    if shoe_type.shoe_image_url is not None
                    else None
                ),
            }
        )
    print(result)
    return jsonify(result)


@shoe_bp.route("/shoe/getallshoesnew", methods=["GET"])
def get_all_shoes_new():
    shoe_rid = request.args.get("shoerid")
    _, _, department = current_user_info()
    shoe_department = department.department_name
    if shoe_rid is None:
        if shoe_department in ["开发一部", "开发二部", "开发三部"]:
            shoe_entities = (
                db.session.query(Shoe)
                .filter(Shoe.shoe_department_id == shoe_department)
                .all()
            )
        else:
            shoe_entities = (
                db.session.query(Shoe)
                .all()
            )
    else:
        if shoe_department in ["开发一部", "开发二部", "开发三部"]:
            shoe_entities = (
                db.session.query(Shoe)
                .filter(Shoe.shoe_department_id == shoe_department)
                .filter(Shoe.shoe_rid.like(f"%{shoe_rid}%"))
                .all()
            )
        else:
            shoe_entities = (
                db.session.query(Shoe)
                .filter(Shoe.shoe_rid.like(f"%{shoe_rid}%"))
                .all()
            )
    result_data = []
    for shoe in shoe_entities:
        shoe_response_data = dict()
        for attr in SHOE_TABLE_ATTRNAMES:
            shoe_response_data[to_camel(attr)] = getattr(shoe, attr)
        shoe_type_entities = (db.session.query(ShoeType, Color)
                              .join(Color, ShoeType.color_id == Color.color_id)
                              .filter(ShoeType.shoe_id == shoe.shoe_id)
                              .all())
        shoe_type_list = []
        for shoe_type in shoe_type_entities:
            shoe_type_response_data = dict()
            for attr in SHOETYPE_TABLE_ATTRNAMES:
                shoe_type_response_data[to_camel(attr)] = getattr(shoe_type.ShoeType, attr)
            shoe_type_response_data['colorName'] = shoe_type.Color.color_name
            shoe_type_response_data['shoeRid'] = shoe.shoe_rid
            if shoe_type.ShoeType.shoe_image_url:
                shoe_type_response_data['shoeImageUrl'] = IMAGE_STORAGE_PATH + shoe_type.ShoeType.shoe_image_url
            else:
                shoe_type_response_data['shoeImageUrl'] = None
            shoe_type_list.append(shoe_type_response_data)
        shoe_response_data['shoeTypeData'] = shoe_type_list
        result_data.append(shoe_response_data)
    return jsonify(result_data), 200


@shoe_bp.route("/shoe/getshoebatchinfotype", methods=["GET"])
def get_shoe_batch():
    batch_info_types = db.session.query(BatchInfoType).filter_by(batch_info_type_usage = 0).all()
    result = []
    for batch_info_type in batch_info_types:
        result.append(
            {
                "batchInfoTypeId": batch_info_type.batch_info_type_id,
                "batchInfoTypeName": batch_info_type.batch_info_type_name,
                "size34Slot": batch_info_type.size_34_name,
                "size35Slot": batch_info_type.size_35_name,
                "size36Slot": batch_info_type.size_36_name,
                "size37Slot": batch_info_type.size_37_name,
                "size38Slot": batch_info_type.size_38_name,
                "size39Slot": batch_info_type.size_39_name,
                "size40Slot": batch_info_type.size_40_name,
                "size41Slot": batch_info_type.size_41_name,
                "size42Slot": batch_info_type.size_42_name,
                "size43Slot": batch_info_type.size_43_name,
                "size44Slot": batch_info_type.size_44_name,
                "size45Slot": batch_info_type.size_45_name,
                "size46Slot": batch_info_type.size_46_name 
            }
        )
    
    return jsonify(result)


@shoe_bp.route("/shoe/getshoebatchinfotypelogistics", methods=["GET"])
def get_shoe_batch_logistics():
    batch_info_types = db.session.query(BatchInfoType).filter_by(batch_info_type_usage = 1).all()
    result = []
    for batch_info_type in batch_info_types:
        result.append(
            {
                "batchInfoTypeId": batch_info_type.batch_info_type_id,
                "batchInfoTypeName": batch_info_type.batch_info_type_name,
                "size34Slot": batch_info_type.size_34_name,
                "size35Slot": batch_info_type.size_35_name,
                "size36Slot": batch_info_type.size_36_name,
                "size37Slot": batch_info_type.size_37_name,
                "size38Slot": batch_info_type.size_38_name,
                "size39Slot": batch_info_type.size_39_name,
                "size40Slot": batch_info_type.size_40_name,
                "size41Slot": batch_info_type.size_41_name,
                "size42Slot": batch_info_type.size_42_name,
                "size43Slot": batch_info_type.size_43_name,
                "size44Slot": batch_info_type.size_44_name,
                "size45Slot": batch_info_type.size_45_name,
                "size46Slot": batch_info_type.size_46_name 
            }
        )
    
    return jsonify(result)


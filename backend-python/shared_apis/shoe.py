from flask import Blueprint, jsonify, request

from app_config import app, db
from models import *
from file_locations import IMAGE_STORAGE_PATH
from api_utility import to_camel, to_snake
from login.login import current_user, current_user_info
import json
import time

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
    time_s = time.time()
    shoe_rid = request.args.get("shoerid")
    _, _, department = current_user_info()
    user_department = department.department_name
    result_data = []
    
    query = (
        db.session.query(Shoe, ShoeType, Color)
            .outerjoin(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
            .outerjoin(Color, ShoeType.color_id == Color.color_id)
    )
    print("shoe rid is " + str(shoe_rid))
    if user_department in ["开发一部", "开发二部", "开发三部", "开发五部"]:
        query = query.filter(Shoe.shoe_department_id == user_department)
    if shoe_rid is not None:
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    response = query.all()
    meta_data = {}
    for row in response:
        shoe, shoe_type, color = row
        if shoe.shoe_id not in meta_data.keys():
            meta_data[shoe.shoe_id] = dict()
            for attr in SHOE_TABLE_ATTRNAMES:
                meta_data[shoe.shoe_id][to_camel(attr)] = getattr(shoe, attr)
            shoe_type_dict = dict()
            if shoe_type:
                for attr in SHOETYPE_TABLE_ATTRNAMES:
                    shoe_type_dict[to_camel(attr)] = getattr(shoe_type, attr)
                    shoe_type_dict['colorName'] = color.color_name
                    shoe_type_dict['shoeRid'] = shoe.shoe_rid
                    if shoe_type.shoe_image_url:
                        shoe_type_dict['shoeImageUrl'] = IMAGE_STORAGE_PATH + shoe_type.shoe_image_url
                    else:
                        shoe_type_dict['shoeImageUrl'] = None
                meta_data[shoe.shoe_id]['shoeTypeData'] = [shoe_type_dict]
        else:
            if shoe_type:
                shoe_type_dict = dict()
                for attr in SHOETYPE_TABLE_ATTRNAMES:
                    shoe_type_dict[to_camel(attr)] = getattr(shoe_type, attr)
                    shoe_type_dict['colorName'] = color.color_name
                    shoe_type_dict['shoeRid'] = shoe.shoe_rid
                    if shoe_type.shoe_image_url:
                        shoe_type_dict['shoeImageUrl'] = IMAGE_STORAGE_PATH + shoe_type.shoe_image_url
                    else:
                        shoe_type_dict['shoeImageUrl'] = None
                meta_data[shoe.shoe_id]['shoeTypeData'].append(shoe_type_dict)
    for key in meta_data.keys():
        result_data.append(meta_data[key])
    time_t2 = time.time()
    print("get all shoes new time taken is " + " " + str(time_t2 - time_s))
    return jsonify(result_data), 200

    # if shoe_rid is None:
    #     if shoe_department in ["开发一部", "开发二部", "开发三部", "开发五部"]:
    #         shoe_entities = (
    #             db.session.query(Shoe)
    #             .filter(Shoe.shoe_department_id == shoe_department)
    #             .all()
    #         )
    #     else:
    #         shoe_entities = (
    #             db.session.query(Shoe)
    #             .all()
    #         )
    # else:
    #     if shoe_department in ["开发一部", "开发二部", "开发三部", "开发五部"]:
    #         shoe_entities = (
    #             db.session.query(Shoe)
    #             .filter(Shoe.shoe_department_id == shoe_department)
    #             .filter(Shoe.shoe_rid.like(f"%{shoe_rid}%"))
    #             .all()
    #         )
    #     else:
    #         shoe_entities = (
    #             db.session.query(Shoe)
    #             .filter(Shoe.shoe_rid.like(f"%{shoe_rid}%"))
    #             .all()
    #         )
    # time_t1 = time.time()
    # for shoe in shoe_entities:
    #     shoe_response_data = dict()
    #     for attr in SHOE_TABLE_ATTRNAMES:
    #         shoe_response_data[to_camel(attr)] = getattr(shoe, attr)
    #     shoe_type_entities = (db.session.query(ShoeType, Color)
    #                           .join(Color, ShoeType.color_id == Color.color_id)
    #                           .filter(ShoeType.shoe_id == shoe.shoe_id)
    #                           .all())
    #     shoe_type_list = []
    #     for shoe_type in shoe_type_entities:
    #         shoe_type_response_data = dict()
    #         for attr in SHOETYPE_TABLE_ATTRNAMES:
    #             shoe_type_response_data[to_camel(attr)] = getattr(shoe_type.ShoeType, attr)
    #         shoe_type_response_data['colorName'] = shoe_type.Color.color_name
    #         shoe_type_response_data['shoeRid'] = shoe.shoe_rid
    #         if shoe_type.ShoeType.shoe_image_url:
    #             shoe_type_response_data['shoeImageUrl'] = IMAGE_STORAGE_PATH + shoe_type.ShoeType.shoe_image_url
    #         else:
    #             shoe_type_response_data['shoeImageUrl'] = None
    #         shoe_type_list.append(shoe_type_response_data)
    #     shoe_response_data['shoeTypeData'] = shoe_type_list
    #     result_data.append(shoe_response_data)
    


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

@shoe_bp.route("/shoe/getlastshoebatchinfotypebysizetable", methods=["GET"])
def get_last_shoe_batch_by_size_table():
    orderId = request.args.get("orderId")
    if orderId is None:
        return jsonify("orderId is required"), 400
    order_size_table = db.session.query(Order).filter_by(order_id = orderId).first().order_size_table
    #transform order_size_table json to dict
    order_size_table = json.loads(order_size_table)
    print(order_size_table)
    last_order_list = order_size_table['楦头']
    #trans the list to result like "size34Slot": last_order_list['楦头'][0], max to size47slot, if last_order_list is not enough, fill with None
    #use index to get the value
    result = {}
    for i in range(34, 47):
        if i - 34 < len(last_order_list):
            result[f'size{i}Slot'] = last_order_list[i-34]
        else:
            result[f'size{i}Slot'] = None
    print(result)
    return jsonify(result)

@shoe_bp.route("/shoe/getshoebatchinfotypebysizetable", methods=["GET"])
def get_shoe_batch_by_size_table():
    orderId = request.args.get("orderId")

    if orderId is None:
        return jsonify("orderId is required"), 400

    order = db.session.query(Order).filter_by(order_id=orderId).first()
    if not order or not order.order_size_table:
        return jsonify("Order size table not found"), 404

    # Transform order_size_table JSON to dict
    order_size_table = json.loads(order.order_size_table)

    size_key = "客人码"

    if size_key not in order_size_table:
        return jsonify(f"Size table '{size_key}' not found in order data"), 404

    # Extract the size data
    last_order_list = order_size_table[size_key]

    # Convert the list into a response format (e.g., "size34Slot": value)
    result = {}
    for i in range(34, 47):
        result[f'size{i}Slot'] = last_order_list[i - 34] if i - 34 < len(last_order_list) else None

    return jsonify(result)

    
    


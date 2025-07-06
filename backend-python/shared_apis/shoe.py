from flask import Blueprint, jsonify, request
from matplotlib.style import available

from app_config import db
from sqlalchemy import func
from models import *
from file_locations import IMAGE_STORAGE_PATH
from api_utility import to_camel, to_snake
from login.login import current_user, current_user_info
import json
import time
from logger import logger
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
    logger.debug(result)
    return jsonify(result)


@shoe_bp.route("/shoe/getallshoesnew", methods=["GET"])
def get_all_shoes_new():
    time_s = time.time()
    shoe_rid = request.args.get("shoerid")
    customer_name = request.args.get("customerName", None)
    available = request.args.get("available", type=int)
    _, _, department = current_user_info()
    user_department = department.department_name
    page = request.args.get("page", type=int)
    page_size = request.args.get("pageSize", type=int)
    if not page:
        page = 1
    if not page_size:
        page_size = 20
    result_data = []
    # .outerjoin(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
    #         .outerjoin(Color, ShoeType.color_id == Color.color_id)
    query = db.session.query(Shoe)
    if user_department in ["开发一部", "开发二部", "开发三部", "开发五部"]:
        query = query.filter(Shoe.shoe_department_id == user_department)

    if shoe_rid is not None and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if available:
        query = query.filter(Shoe.shoe_available == True)
    if customer_name is not None and customer_name != "":
        query = query.join(OrderShoe, Shoe.shoe_id == OrderShoe.shoe_id).filter(OrderShoe.customer_product_name.ilike(f"%{customer_name}%"))
    total_count = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()
    shoe_id_list = [shoe.shoe_id for shoe in response]
    entities = (
        db.session.query(Shoe, ShoeType, Color)
        .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(ShoeType.shoe_id.in_(shoe_id_list))
        .all()
    )
    res_data = {}
    for shoe in response:
        res_data[shoe.shoe_id] = dict()
        for attr in SHOE_TABLE_ATTRNAMES:
            res_data[shoe.shoe_id][to_camel(attr)] = getattr(shoe, attr)
        res_data[shoe.shoe_id]["shoeTypeData"] = []
        res_data[shoe.shoe_id]["shoeTypeColors"] = []

    for shoe, shoe_type, color in entities:
        shoe_type_res = {}
        color_entity = {}
        for attr in SHOETYPE_TABLE_ATTRNAMES:
            shoe_type_res[to_camel(attr)] = getattr(shoe_type, attr)
        shoe_type_res["colorName"] = color.color_name
        shoe_type_res["shoeRid"] = shoe.shoe_rid
        shoe_type_res["shoeImageUrl"] = (
            IMAGE_STORAGE_PATH + shoe_type.shoe_image_url + "?" + str(time.time())
            if shoe_type.shoe_image_url
            else None
        )
        color_entity = {'label':color.color_name,'value':color.color_id}
        res_data[shoe_type.shoe_id]['shoeTypeColors'].append(color_entity)
        res_data[shoe_type.shoe_id]["shoeTypeData"].append(shoe_type_res)
    result_data = list(res_data.values())
    time_t2 = time.time()
    logger.debug("get all shoes new time taken is " + " " + str(time_t2 - time_s))
    return {"shoeTable": result_data, "total": total_count}, 200


@shoe_bp.route("/shoe/getshoebatchinfotype", methods=["GET"])
def get_shoe_batch():
    batch_info_types = (
        db.session.query(BatchInfoType).filter_by(batch_info_type_usage=0).all()
    )
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
                "size46Slot": batch_info_type.size_46_name,
            }
        )

    return jsonify(result)


@shoe_bp.route("/shoe/getshoebatchinfotypelogistics", methods=["GET"])
def get_shoe_batch_logistics():
    batch_info_types = (
        db.session.query(BatchInfoType).filter_by(batch_info_type_usage=1).all()
    )
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
                "size46Slot": batch_info_type.size_46_name,
            }
        )

    return jsonify(result)


@shoe_bp.route("/shoe/getlastshoebatchinfotypebysizetable", methods=["GET"])
def get_last_shoe_batch_by_size_table():
    orderId = request.args.get("orderId")
    if orderId is None:
        return jsonify("orderId is required"), 400
    order_size_table = (
        db.session.query(Order).filter_by(order_id=orderId).first().order_size_table
    )
    # transform order_size_table json to dict
    order_size_table = json.loads(order_size_table)
    logger.debug(order_size_table)
    last_order_list = order_size_table["楦头"]
    # trans the list to result like "size34Slot": last_order_list['楦头'][0], max to size47slot, if last_order_list is not enough, fill with None
    # use index to get the value
    result = {}
    for i in range(34, 47):
        if i - 34 < len(last_order_list):
            result[f"size{i}Slot"] = last_order_list[i - 34]
        else:
            result[f"size{i}Slot"] = None
    logger.debug(result)
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
        result[f"size{i}Slot"] = (
            last_order_list[i - 34] if i - 34 < len(last_order_list) else None
        )

    return jsonify(result)


@shoe_bp.route("/shoe/shoecolorinfo", methods=["GET"])
def get_shoe_color_info():
    entities = (
        db.session.query(Color, func.count(ShoeType.shoe_type_id))
        .outerjoin(ShoeType, ShoeType.color_id == Color.color_id)
        .group_by(Color.color_id)
        .all()
    )
    res_data = []
    for color, count in entities:
        res_data.append(
            {
                "colorId": color.color_id,
                "colorNameCN": color.color_name,
                "colorNameEN": color.color_en_name,
                "colorNameSP": color.color_sp_name,
                "colorNameIT": color.color_it_name,
                "colorBoundCount": count,
            }
        )

    return jsonify({"colorInfo": res_data}), 200


@shoe_bp.route("/shoe/shoecolormerge", methods=["POST"])
def merge_shoe_colors():
    data = request.get_json()
    colors_to_merge = data.get("colorList")
    color_name = colors_to_merge[0]["colorNameCN"]
    cur_max = colors_to_merge[0]["colorBoundCount"]
    max_color_id = colors_to_merge[0]["colorId"]
    for color in colors_to_merge:
        if color["colorNameCN"] != color_name:
            return jsonify({"msg": "ERROR COLOR NOT THE SAME"}), 401
        if color["colorBoundCount"] > cur_max:
            cur_max = color["colorBoundCount"]
            max_color_id = color["colorId"]
    # now perform the merge
    shoe_type_entities = (
        db.session.query(ShoeType, Color)
        .join(Color, ShoeType.color_id == Color.color_id)
        .all()
    )
    color_ids = [color["colorId"] for color in colors_to_merge]
    for shoe_type, color in shoe_type_entities:
        if color.color_id in color_ids:
            shoe_type.color_id = max_color_id
    db.session.commit()
    return jsonify({"msg": "color merged"}), 200

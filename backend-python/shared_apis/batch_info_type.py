from flask import Blueprint, jsonify, request
from models import *
from api_utility import to_camel, to_snake
from constants import SHOESIZERANGE

from logger import logger
from app_config import db

#TODO ADD RESTRAINTS

batch_type_bp = Blueprint("batch_type_bp", __name__)
TABLE_ATTRNAMES = BatchInfoType.__table__.columns.keys()
TABLE_ATTRNAMES.remove("batch_info_type_usage")
API_USED_ATTRS = TABLE_ATTRNAMES
def get_order_batch_type_helper(order_id):
    # get batch info type (US, EU)
    # order_id = 1
    shoe_size_locale = (
        db.session.query(BatchInfoType)
        .join(Order, BatchInfoType.batch_info_type_id == Order.batch_info_type_id)
        .filter(Order.order_id == order_id)
        .first()
    )
    result = []
    for i in range(34, 47):
        locale = getattr(shoe_size_locale, f"size_{i}_name")
        type_name = getattr(shoe_size_locale, f"batch_info_type_name")
        id = getattr(shoe_size_locale, f"batch_info_type_id")
        if not locale:
            break
        obj = {"id": id, "prop": f"size{i}Amount", "label": locale, "type": type_name, "usage": getattr(shoe_size_locale, "batch_info_type_usage")}
        result.append(obj)
    return result


@batch_type_bp.route("/batchtype/getallbatchtypesbusiness", methods=["GET"])
def get_all_batch_types_business():
    entities = db.session.query(BatchInfoType).filter_by(batch_info_type_usage = 0).all()
    response_list = []
    attr_names = API_USED_ATTRS

    for entity in entities:
        result = {}
        for db_attr in attr_names:
            if getattr(entity, db_attr) == "":
                result[to_camel(db_attr)] = None
            else:
                result[to_camel(db_attr)] = getattr(entity, db_attr,None)
        response_list.append(result)
    return jsonify({"batchDataTypes": response_list}), 200


@batch_type_bp.route("/batchtype/addbatchtypebusiness", methods=["POST"])
def add_batch_type_business():
    batch_info_type_name = request.args.get("batchInfoTypeName")
    db_entity = BatchInfoType()
    for attr in API_USED_ATTRS:
        logger.debug(attr, request.json.get(to_camel(attr)))
        setattr(db_entity, attr, request.json.get(to_camel(attr)))
        db_entity.batch_info_type_id = None
        db_entity.batch_info_type_usage = 0
    db.session.add(db_entity)
    db.session.commit() 
        
    return jsonify({"message":"batch info type added from business success"}), 200


@batch_type_bp.route("/batchtype/deletebatchtypebusiness", methods=["DELETE"])
def delete_batch_type_business():
    batch_type_id = request.args.get("batchTypeId")
    entity_exists = db.session.query(BatchInfoType).filter_by(batch_info_type_id = batch_type_id, batch_info_type_usage = 0)
    if entity_exists:
        db.session.execute(db.delete(BatchInfoType).filter_by(batch_info_type_id = batch_type_id))
        db.session.commit()
        return jsonify({"msg":"deleted"}), 200
    else:
        return jsonify({"error":"batch info type not found"}), 400



@batch_type_bp.route("/batchtype/getallbatchtypeslogistics")
def get_batch_type_logistics():
    entities = db.session.query(BatchInfoType).filter_by(batch_info_type_usage = 1).all()
    response_list = []
    attr_names = API_USED_ATTRS

    for entity in entities:
        result = {}
        for db_attr in attr_names:
            if getattr(entity, db_attr) == "":
                result[to_camel(db_attr)] = None
            else:
                result[to_camel(db_attr)] = getattr(entity, db_attr,None)
        response_list.append(result)
    return jsonify({"batchDataTypes": response_list}), 200



@batch_type_bp.route("/batchtype/addbatchtypelogistics", methods=["POST"])
def add_batch_type_logistics():
    batch_info_type_name = request.args.get("batchInfoTypeName")
    db_entity = BatchInfoType()
    for attr in API_USED_ATTRS:
        logger.debug(attr, request.json.get(to_camel(attr)))
        setattr(db_entity, attr, request.json.get(to_camel(attr)))
        db_entity.batch_info_type_id = None
        db_entity.batch_info_type_usage = 1
    db.session.add(db_entity)
    db.session.commit() 
        
    return jsonify({"message":"batch info type added from logistics success"}), 200


@batch_type_bp.route("/batchtype/deletebatchtypelogistics", methods=["DELETE"])
def delete_batch_type_logistics():
    batch_type_id = request.args.get("batchTypeId")
    entity_exists = db.session.query(BatchInfoType).filter_by(batch_info_type_id = batch_type_id, batch_info_type_usage = 1)
    if entity_exists:
        db.session.execute(db.delete(BatchInfoType).filter_by(batch_info_type_id = batch_type_id))
        db.session.commit()
        return jsonify({"msg":"deleted"}), 200
    else:
        return jsonify({"error":"batch_type_doesnt exists"}), 400


@batch_type_bp.route("/batchtype/getorderbatchtype", methods=["GET"])
def get_order_batch_type():
    order_id = request.args.get("orderId")
    result = get_order_batch_type_helper(order_id)
    return result


@batch_type_bp.route("/batchtype/getbatchtypefororders", methods=["GET"])
def get_batch_type_for_orders():
    order_ids = request.args.get("orderIds")
    if not order_ids:
        return jsonify({"error": "No order IDs provided"}), 400
    order_ids = order_ids.split(",")
    shoe_size_locales = (
        db.session.query(BatchInfoType, Order)
        .join(Order, BatchInfoType.batch_info_type_id == Order.batch_info_type_id)
        .filter(Order.order_id.in_(order_ids))
        .all()
    )
    result = {}
    for row in shoe_size_locales:
        shoe_size_locale, order = row
        if order.order_id not in result:
            result[order.order_id] = []
        for i in range(len(SHOESIZERANGE)):
            db_index = i + 34
            locale = getattr(shoe_size_locale, f"size_{db_index}_name")
            type_name = getattr(shoe_size_locale, f"batch_info_type_name")
            id = getattr(shoe_size_locale, f"batch_info_type_id")
            if not locale:
                break
            obj = {
                "orderId": order.order_id,
                "id": id,
                "prop": f"size{db_index}Amount",
                "label": locale,
                "type": type_name,
                "usage": getattr(shoe_size_locale, "batch_info_type_usage"),
            }
            result[order.order_id].append(obj)
    return result
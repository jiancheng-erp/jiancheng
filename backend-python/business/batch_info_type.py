from flask import Blueprint, jsonify, request
from models import *
from api_utility import to_camel, to_snake


from app_config import db

batch_type_bp = Blueprint("batch_type_bp", __name__)
TABLE_ATTRNAMES = BatchInfoType.__table__.columns.keys()
TABLE_ATTRNAMES.remove("batch_info_type_usage")
API_USED_ATTRS = TABLE_ATTRNAMES
def get_order_batch_type_helper(order_id):
    # get batch info type (US, EU)
    shoe_size_locale = (
        db.session.query(BatchInfoType)
        .join(Order, BatchInfoType.batch_info_type_id == Order.batch_info_type_id)
        .filter(Order.order_id == order_id)
        .first()
    )
    result = []
    for i in range(34, 47):
        id = getattr(shoe_size_locale, "batch_info_type_id")
        locale = getattr(shoe_size_locale, f"size_{i}_name")
        type_name = getattr(shoe_size_locale, f"batch_info_type_name")
        if not locale:
            break
        obj = {"id": id,  "prop": f"size{i}Amount", "label": locale, "type": type_name}
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
        setattr(db_entity, attr, request.json.get(to_camel(attr)))
        db_entity.batch_info_type_id = None
        db_entity.batch_info_type_usage = 0
    db.session.add(db_entity)
    db.session.commit() 
        
    return jsonify({"message":"batch info type added from business success"}), 200


@batch_type_bp.route("/batchtype/deletebatchtypebusiness", methods=["DELETE"])
def delete_batch_type_business():
    batch_type_id = request.args.get("batchTypeId")
    entity_exists = db.session.query(BatchInfoType).filter_by(batch_info_type_id = batch_type_id, batch_info_type_usage = 0).first()
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
        setattr(db_entity, attr, request.json.get(to_camel(attr)))
        db_entity.batch_info_type_id = None
        db_entity.batch_info_type_usage = 1
    db.session.add(db_entity)
    db.session.commit() 
        
    return jsonify({"message":"batch info type added from logistics success"}), 200


@batch_type_bp.route("/batchtype/deletebatchtypelogistics", methods=["DELETE"])
def delete_batch_type_logistics():
    batch_type_id = request.args.get("batchTypeId")
    entity_exists = db.session.query(BatchInfoType).filter_by(batch_info_type_id = batch_type_id, batch_info_type_usage = 1).first()
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


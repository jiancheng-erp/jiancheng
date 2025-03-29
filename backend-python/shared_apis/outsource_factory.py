from flask import Blueprint, jsonify, request

from app_config import db
from models import *

outsource_factory_bp = Blueprint("outsource_factory_bp", __name__)


@outsource_factory_bp.route("/general/getalloutsourcefactories", methods=["GET"])
def get_all_outsource_factories():
    name_search = request.args.get("nameSearch")
    query = db.session.query(OutsourceFactory).filter_by(is_deleted=False)
    if name_search and name_search != '':
        query = query.filter(OutsourceFactory.factory_name.ilike(f"%{name_search}%"))
    factories = query.all()
    result = []
    for factory in factories:
        result.append(
            {
                "id": factory.factory_id,
                "value": factory.factory_name,
            }
        )
    return jsonify(result)


@outsource_factory_bp.route("/general/addnewoutsourcefactory", methods=["POST"])
def add_new_outsource_factory():
    data = request.get_json()
    response = (
        db.session.query(OutsourceFactory).filter_by(factory_name=data["name"]).all()
    )
    if response:
        return jsonify({"message": "厂家已存在"}), 400
    entity = OutsourceFactory(factory_name=data["name"])
    db.session.add(entity)
    db.session.flush()
    factory_id = entity.factory_id
    db.session.commit()
    return jsonify({"message": "添加成功", "factoryId": factory_id})


@outsource_factory_bp.route("/general/editoutsourcefactory", methods=["PUT"])
def edit_outsource_factory():
    data = request.get_json()
    for row in data:
        entity = db.session.query(OutsourceFactory).get(row["id"])
        if not entity:
            return jsonify({"message": "厂家不存在"})
        entity.factory_name = row["value"]
    db.session.commit()
    return jsonify({"message": "修改成功"})


@outsource_factory_bp.route("/general/deleteoutsourcefactory", methods=["DELETE"])
def delete_outsource_factory():
    factory_id = request.args.get("factoryId")
    entity = db.session.query(OutsourceFactory).get(factory_id)
    if entity:
        entity.is_deleted = 1
    db.session.commit()
    return jsonify({"message": "删除成功"})

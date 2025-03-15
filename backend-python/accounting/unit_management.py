from flask import Blueprint, jsonify, request
from models import *
from api_utility import to_camel, to_snake

import time
from app_config import app, db

units_management_bp = Blueprint("units_management", __name__)




currency_unit_attr_list = AccountingCurrencyUnit.__table__.columns.keys()

# unit_management
@units_management_bp.route("/units_management/all_units", methods=["GET"])
def all_unit():
    all_units = db.session.query(AccountingCurrencyUnit).all()
    response_units_list = []
    for entity in all_units:
        response_entity = {}
        for attr in currency_unit_attr_list:
            response_entity[to_camel(attr)] = getattr(entity, attr)
        response_units_list.append(response_entity)
    return jsonify({"currencyUnitList":response_units_list}), 200


@units_management_bp.routre("/units_management/add_unit", methods=["POST"])
def add_unit():
    unit_name_en = request.json.get("unit_name_en")
    unit_name_cn = request.json.get("unit_name_cn")
    new_entity = AccountingCurrencyUnit()
    new_entity.unit_name_en = unit_name_en
    new_entity.unit_name_cn = unit_name_cn
    db.session.add(new_entity)
    db.session.commit()
    return jsonify({"msg":"new unit added"}), 200

def remove_unit():
    return

def edit_unit_conversion(cur_unit_id, foreign_unit_id, rate):
    return

def activate_unit_converstion(conversion_id):
    return
def deactivate_unit_conversion(conversion_id):
    return                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
import traceback
from app_config import db
from constants import *
from flask import Blueprint, jsonify, request
from models import *

production_lines_bp = Blueprint("production_lines_bp", __name__)


@production_lines_bp.route("/production/getallproductionlines", methods=["GET"])
def get_all_production_lines():
    team = request.args.get("team")
    query = (
        db.session.query(ProductionLine)
        .filter(ProductionLine.is_deleted == False)
    )
    if team and team != '':
        query = query.filter(ProductionLine.production_team == team)
    response = query.all()
    result = []
    for row in response:
        obj = {
            "productionLineId": row.production_line_id,
            "productionTeam": row.production_team,
            "productionLineName": row.production_line_name,
        }
        result.append(obj)
    return result


@production_lines_bp.route("/production/addnewproductionline", methods=["POST"])
def add_new_production_line():
    team = request.json.get("team")
    name = request.json.get("name")
    line = db.session.query(ProductionLine).filter(
        ProductionLine.production_line_name == name,
        ProductionLine.production_team == team,
    ).first()
    if line:
        return jsonify({"message": "该生产线已存在"}), 400
    production_line = ProductionLine(production_line_name=name, production_team=team)
    db.session.add(production_line)
    db.session.commit()
    return jsonify({"message": "success"})


@production_lines_bp.route("/production/editproductionline", methods=["PATCH"])
def edit_production_line():
    data = request.get_json()
    for row in data:
        entity = (
            db.session.query(ProductionLine)
            .filter(ProductionLine.production_line_id == row["productionLineId"])
            .first()
        )
        entity.production_line_name = row["productionLineName"]
    db.session.commit()
    return jsonify({"message": "success"})


@production_lines_bp.route("/production/deleteproductionline", methods=["DELETE"])
def delete_production_line():
    production_line_id = request.args.get("productionLineId")
    entity = (
        db.session.query(ProductionLine)
        .filter(ProductionLine.production_line_id == production_line_id)
        .first()
    )
    entity.is_deleted = True
    db.session.commit()
    return jsonify({"message": "success"})

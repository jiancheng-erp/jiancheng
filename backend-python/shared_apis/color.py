from flask import Blueprint, jsonify, request

from app_config import db
from models import *
from api_utility import to_camel, to_snake
color_bp = Blueprint("color_bp", __name__)

@color_bp.route("/general/allcolors", methods=["GET"])
def get_all_colors():
    colors = Color.query.all()
    result = []
    for color in colors:
        result.append(
            {
                "value": color.color_id,
                "label": color.color_name,
            }
        )
    return jsonify(result)

@color_bp.route("/general/addnewcolor", methods=["POST"])
def add_new_color():
    request_attr_names = {"colorName":"color_name", "colorNameEN":"color_en_name", "colorNameSP":"color_sp_name", "colorNameIT":"color_it_name"}
    entity = Color()
    for attr in request_attr_names.keys():
        setattr(entity, request_attr_names[attr], request.json.get(attr))
    db.session.add(entity)
    db.session.commit()
    return jsonify({"message":"OK"}), 200
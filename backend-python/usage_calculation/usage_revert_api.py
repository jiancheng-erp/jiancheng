from flask import Blueprint, jsonify, request, send_file, current_app
import os
import datetime
from app_config import app, db
from models import *
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from api_utility import randomIdGenerater
from general_document.prodution_instruction import generate_instruction_excel_file
import json
from constants import DEFAULT_SUPPLIER

usage_revert_api = Blueprint('usage_revert_api', __name__)

@usage_revert_api.route('/usagecalculation/saverevertbomusage', methods=['POST'])
def save_revert_bom_usage():
    bom_rid = request.json.get("bomRid")
    bom_items = request.json.get("bomItems")
    bom = db.session.query(Bom).filter(Bom.bom_rid == bom_rid).first()
    for bom_item in bom_items:
        entity = (
            db.session.query(BomItem)
            .filter(BomItem.bom_item_id == bom_item["bomItemId"])
            .first()
        )
        for i in range(len(bom_item["sizeInfo"])):
            name = i + 34
            setattr(entity, f"size_{name}_total_usage", bom_item["sizeInfo"][i]["approvalAmount"])
            entity.total_usage = bom_item["approvalUsage"]
            entity.unit_usage = bom_item["unitUsage"]
            entity.remark = bom_item["remark"]
    order_shoe_status = (
        db.session.query(OrderShoeStatus)
        .join(OrderShoe, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == bom.order_shoe_type_id)
        .filter(OrderShoeStatus.current_status == 4)
        .first()
    )
    db.session.commit()
    return jsonify({"status": "success"})
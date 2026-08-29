from flask import Blueprint, jsonify, request, send_file, current_app
import os
import datetime
from app_config import db
from models import *
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from api_utility import randomIdGenerater
from general_document.prodution_instruction import generate_instruction_excel_file
import json
from constants import DEFAULT_SUPPLIER
from wechat_api.send_message_api import send_configurable_message
from usage_calculation.usage_modification import _build_usage_change_line

usage_revert_api = Blueprint('usage_revert_api', __name__)

@usage_revert_api.route('/usagecalculation/saverevertbomusage', methods=['POST'])
def save_revert_bom_usage():
    bom_rid = request.json.get("bomRid")
    bom_items = request.json.get("bomItems")

    # Fetch BOM entry
    bom = db.session.query(Bom).filter(Bom.bom_rid == bom_rid).first()
    if not bom:
        return jsonify({"error": "BOM not found"}), 404

    total_usage_updates = {}
    change_lines = []

    for bom_item in bom_items:
        # Fetch BOM Item
        entity = db.session.query(BomItem).filter(BomItem.bom_item_id == bom_item["bomItemId"]).first()
        if not entity:
            continue  # Skip if BOM item not found

        material = (
            db.session.query(Material)
            .filter(Material.material_id == entity.material_id)
            .first()
        )
        material_name = material.material_name if material else ""

        # 快照修改前的用量信息
        old_unit = entity.unit_usage
        old_approval = entity.total_usage
        old_sizes = [
            getattr(entity, f"size_{34 + i}_total_usage", None) for i in range(13)
        ]

        # Update size-based total usage and unit usage
        for i in range(len(bom_item["sizeInfo"])):
            size_name = i + 34  # Mapping index to size
            setattr(entity, f"size_{size_name}_total_usage", bom_item["sizeInfo"][i]["approvalAmount"])

        # Update general usage values
        entity.total_usage = bom_item["approvalUsage"]
        entity.unit_usage = bom_item["unitUsage"]
        entity.remark = bom_item["remark"]

        new_sizes = [
            getattr(entity, f"size_{34 + i}_total_usage", None) for i in range(13)
        ]
        line = _build_usage_change_line(
            material_name,
            1,
            old_unit,
            entity.unit_usage,
            old_approval,
            entity.total_usage,
            None,
            None,
            old_sizes,
            new_sizes,
            [],
            [],
        )
        if line:
            change_lines.append(line)

        # Prepare purchase order item update
        key = (entity.material_id, entity.material_specification, entity.material_model, entity.bom_item_color)
        total_usage_updates[key] = total_usage_updates.get(key, 0.00) + float(bom_item["approvalUsage"])

    # **Update Purchase Order Items**
    purchase_order_items = (
        db.session.query(PurchaseOrderItem)
        .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .join(Bom, BomItem.bom_id == Bom.bom_id)
        .filter(Bom.bom_rid == bom_rid)
        .all()
    )

    for poi in purchase_order_items:
        key = (poi.material_id, poi.material_specification, poi.material_model, poi.color)
        if key in total_usage_updates:
            poi.approval_usage = total_usage_updates[key]

    # Update Order Shoe Status if applicable
    order_shoe_status = (
        db.session.query(OrderShoeStatus)
        .join(OrderShoe, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == bom.order_shoe_type_id)
        .filter(OrderShoeStatus.current_status == 4)
        .first()
    )

    db.session.commit()

    # 技术部下发后修改用量，通知总仓经理
    order_info = (
        db.session.query(Order.order_rid, Shoe.shoe_rid)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == bom.order_shoe_type_id)
        .first()
    )
    if order_info and change_lines:
        order_rid, shoe_rid = order_info
        changes_text = "\n".join(change_lines)
        message = (
            "技术部已进行下发后用量修改，订单号：{order_rid}，鞋型号：{shoe_rid}\n"
            "{changes}\n"
            "请总仓经理及时核对"
        )
        send_configurable_message(
            "tech_usage_modification_notify_warehouse",
            message,
            "FanJianMing",
            context={"order_rid": order_rid, "shoe_rid": shoe_rid, "changes": changes_text},
            push_to_group=True,
        )
    return jsonify({"status": "success"})
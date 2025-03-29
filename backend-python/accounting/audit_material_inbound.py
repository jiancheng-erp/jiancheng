from flask import Blueprint, jsonify, request, abort, Response
import json
from models import *
from api_utility import to_camel, to_snake
from app_config import app, db
from accounting.accounting_transaction import (
    add_payable_entity,
    material_inbound_accounting_event,
)

audit_material_inbound_bp = Blueprint("audit_material_inbound_bp", __name__)


def _update_financial_record(supplier_name, total_price, inbound_record_id):
    # 财务
    code = material_inbound_accounting_event(
        supplier_name, total_price, inbound_record_id
    )
    # create payee if not exist
    if code == 1:
        payable_entity_code = add_payable_entity(supplier_name)
        if payable_entity_code == 0:
            material_inbound_accounting_event(
                supplier_name, total_price, inbound_record_id
            )
    elif code == 2:
        error_message = json.dumps({"error": "应付账户不存在"})
        abort(Response(error_message, 400))


@audit_material_inbound_bp.route("/accounting/approveinboundrecord", methods=["PATCH"])
def approve_inbound_record():
    data = request.get_json()
    inbound_record_id = data.get("inboundRecordId")
    inbound_record = (
        db.session.query(InboundRecord)
        .filter(InboundRecord.inbound_record_id == inbound_record_id)
        .first()
    )
    if not inbound_record:
        return jsonify({"message": "找不到入库单"}), 404
    
    supplier_name = (
        db.session.query(Supplier)
        .filter(Supplier.supplier_id == inbound_record.supplier_id)
        .first()
        .supplier_name
    )
    total_price = inbound_record.total_price
    if inbound_record.pay_method == '应付账款':
        _update_financial_record(supplier_name, total_price, inbound_record_id)
    inbound_record.approval_status = 1
    inbound_record.reject_reason = None
    db.session.commit()
    return jsonify({"message": "success"})


@audit_material_inbound_bp.route("/accounting/rejectinboundrecord", methods=["PATCH"])
def reject_inbound_record():
    data = request.get_json()
    inbound_record_id = data.get("inboundRecordId")
    reject_reason = data.get("rejectReason")
    inbound_record = (
        db.session.query(InboundRecord)
        .filter(InboundRecord.inbound_record_id == inbound_record_id)
        .first()
    )
    if not inbound_record:
        return jsonify({"message": "inbound record not found"}), 404
    inbound_record.approval_status = 2
    inbound_record.reject_reason = reject_reason
    db.session.commit()
    return jsonify({"message": "success"})

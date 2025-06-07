from flask import Blueprint, jsonify, request, abort, Response
import json
from models import *
from app_config import db
from accounting.accounting_transaction import (
    material_outbound_accounting_event,
)
from constants import ACCOUNTING_PAYEE_NOT_FOUND, ACCOUNTING_PAYABLE_ACCOUNT_NOT_FOUND
from accounting.audit_material_inbound import update_average_price

audit_material_outbound_bp = Blueprint("audit_material_outbound_bp", __name__)


def _update_financial_record(supplier_name, total_price, outbound_record_id):
    # 财务
    code = material_outbound_accounting_event(
        supplier_name, total_price, outbound_record_id
    )
    if code == ACCOUNTING_PAYEE_NOT_FOUND:
        error_message = json.dumps({"message": "供应商不存在"})
        abort(Response(error_message, 400))
    elif code == ACCOUNTING_PAYABLE_ACCOUNT_NOT_FOUND:
        error_message = json.dumps({"message": "供应商应付账户不存在"})
        abort(Response(error_message, 400))


@audit_material_outbound_bp.route("/accounting/approveoutboundrecord", methods=["PATCH"])
def approve_outbound_record():
    data = request.get_json()
    outbound_record_id = data.get("outboundRecordId")
    outbound_record = (
        db.session.query(OutboundRecord)
        .filter(OutboundRecord.outbound_record_id == outbound_record_id)
        .first()
    )
    if not outbound_record:
        return jsonify({"message": "找不到出库单"}), 404

    supplier_name = (
        db.session.query(Supplier)
        .filter(Supplier.supplier_id == outbound_record.supplier_id)
        .first()
        .supplier_name
    )
    total_price = outbound_record.total_price
    outbound_record.approval_status = 1
    outbound_record.reject_reason = None
    db.session.flush()
    
    if outbound_record.outbound_type == 4:  # 如果是材料退回
        _update_financial_record(supplier_name, total_price, outbound_record_id)
        if outbound_record.is_sized_material == 0:
            storage_id_list = (
                db.session.query(OutboundRecordDetail.material_storage_id)
                .filter(OutboundRecordDetail.outbound_record_id == outbound_record_id)
                .all()
            )
            update_average_price(storage_id_list, type=0)
        else:
            storage_id_list = (
                db.session.query(OutboundRecordDetail.size_material_storage_id)
                .filter(OutboundRecordDetail.outbound_record_id == outbound_record_id)
                .all()
            )
            update_average_price(storage_id_list, type=1)

    db.session.commit()
    return jsonify({"message": "success"})


@audit_material_outbound_bp.route("/accounting/rejectoutboundrecord", methods=["PATCH"])
def reject_outbound_record():
    data = request.get_json()
    outbound_record_id = data.get("outboundRecordId")
    reject_reason = data.get("rejectReason")
    outbound_record = (
        db.session.query(OutboundRecord)
        .filter(OutboundRecord.outbound_record_id == outbound_record_id)
        .first()
    )
    if not outbound_record:
        return jsonify({"message": "outbound record not found"}), 404
    outbound_record.approval_status = 2
    outbound_record.reject_reason = reject_reason
    db.session.commit()
    return jsonify({"message": "success"})

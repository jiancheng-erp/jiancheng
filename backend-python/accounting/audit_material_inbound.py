from flask import Blueprint, jsonify, request, abort, Response
from sqlalchemy import func
import json
from models import *
from api_utility import to_camel, to_snake
from app_config import db
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


def update_average_price(storage_id_list, type=0):
    inbound_subq = (
        db.session.query(
            InboundRecordDetail.material_storage_id,
            func.sum(InboundRecordDetail.item_total_price).label(
                "in_total_price"
            ),
            func.sum(InboundRecordDetail.inbound_amount).label("in_amount"),
        )
        .join(
            InboundRecord,
            InboundRecordDetail.inbound_record_id
            == InboundRecord.inbound_record_id,
        )
        .filter(
            InboundRecord.approval_status == 1,
            InboundRecordDetail.material_storage_id.in_(
                storage[0] for storage in storage_id_list
            ),
        )
        .group_by(
            InboundRecordDetail.material_storage_id,
        )
        .subquery()
    )

    outbound_subq = (
        db.session.query(
            OutboundRecordDetail.material_storage_id,
            func.sum(OutboundRecordDetail.item_total_price).label("out_total_price"),
            func.sum(OutboundRecordDetail.outbound_amount).label("out_amount"),
        )
        .join(OutboundRecord, OutboundRecordDetail.outbound_record_id == OutboundRecord.outbound_record_id)
        .filter(
            OutboundRecord.approval_status == 1,
            OutboundRecordDetail.material_storage_id.in_(
                storage[0] for storage in storage_id_list
            ),
        )
        .group_by(OutboundRecordDetail.material_storage_id)
        .subquery()
    )

    final_query = (
        db.session.query(
            inbound_subq.c.material_storage_id,
            (inbound_subq.c.in_total_price - func.coalesce(outbound_subq.c.out_total_price, 0)).label("net_total_price"),
            (inbound_subq.c.in_amount - func.coalesce(outbound_subq.c.out_amount, 0)).label("net_total_amount"),
            (
                (inbound_subq.c.in_total_price - func.coalesce(outbound_subq.c.out_total_price, 0)) /
                func.nullif((inbound_subq.c.in_amount - func.coalesce(outbound_subq.c.out_amount, 0)), 0)
            ).label("average_unit_price")
        )
        .outerjoin(outbound_subq, inbound_subq.c.material_storage_id == outbound_subq.c.material_storage_id)
        .subquery()
    )
    avg_prices = (
        db.session.query(
            MaterialStorage,
            final_query.c.average_unit_price,
        )
        .join(
            final_query,
            MaterialStorage.material_storage_id
            == final_query.c.material_storage_id,
        )
        .all()
    )
    for material_storage, avg_price in avg_prices:
        material_storage.average_price = avg_price


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
    if inbound_record.pay_method == "应付账款":
        _update_financial_record(supplier_name, total_price, inbound_record_id)

    inbound_record.approval_status = 1
    inbound_record.reject_reason = None
    db.session.flush()

    # update average price of material
    inbound_record_id = inbound_record.inbound_record_id
    storage_id_list = (
        db.session.query(InboundRecordDetail.material_storage_id)
        .filter(InboundRecordDetail.inbound_record_id == inbound_record_id)
        .all()
    )
    update_average_price(storage_id_list, type=0)

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

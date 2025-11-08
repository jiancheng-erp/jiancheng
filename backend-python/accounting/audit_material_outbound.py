from flask import Blueprint, jsonify, request, abort, Response
import json
from models import *
from app_config import db
from accounting.accounting_transaction import (
    material_outbound_accounting_event,
)
from constants import ACCOUNTING_PAYEE_NOT_FOUND, ACCOUNTING_PAYABLE_ACCOUNT_NOT_FOUND, SHOESIZERANGE
from accounting.audit_material_inbound import update_average_price
from decimal import Decimal
from collections import defaultdict
from datetime import datetime

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


def update_outbound_amount(outbound_detail_list: list[OutboundRecordDetail]):
    if not outbound_detail_list:
        return

    # 1) Gather unique storage ids
    msids = {d.material_storage_id for d in outbound_detail_list}

    # 2) Aggregate totals per storage (overall + each shoe size)
    agg_total = defaultdict(lambda: Decimal("0"))
    agg_size = defaultdict(lambda: defaultdict(lambda: 0))  # int for sizes is fine

    for detail in outbound_detail_list:
        msid = detail.material_storage_id

        # Sum overall outbound amount
        amount = getattr(detail, "outbound_amount", 0) or 0
        agg_total[msid] += Decimal(str(amount))

        # Sum each size amount
        for size in SHOESIZERANGE:
            col = f"size_{size}_outbound_amount"
            val = getattr(detail, col, 0) or 0
            agg_size[msid][size] += int(val)

    # 3) Load storages and size-details in bulk
    storages = (
        db.session.query(MaterialStorage)
        .filter(MaterialStorage.material_storage_id.in_(msids))
        .all()
    )

    size_details = (
        db.session.query(MaterialStorageSizeDetail)
        .filter(MaterialStorageSizeDetail.material_storage_id.in_(msids))
        .order_by(
            MaterialStorageSizeDetail.material_storage_id,
            MaterialStorageSizeDetail.order_number
        )
        .all()
    )

    # material_storage_id -> ordered list of its size-detail rows
    size_details_map: dict[int, list[MaterialStorageSizeDetail]] = defaultdict(list)
    for sd in size_details:
        size_details_map[sd.material_storage_id].append(sd)

    # 4) Apply aggregated updates
    for storage in storages:
        msid = storage.material_storage_id
        total = agg_total.get(msid, Decimal("0"))
        if total:  # only touch rows that actually have outbound totals
            storage.pending_outbound -= total
            storage.outbound_amount += total # 材料退回，应该增加出库总量
            storage.current_amount  -= total

            # Update per-size amounts (respect the ordering by order_number)
            sds = size_details_map.get(msid, [])
            for i, size in enumerate(SHOESIZERANGE):
                if i >= len(sds):
                    break  # no more size rows for this storage
                size_delta = agg_size[msid].get(size, 0)
                if size_delta:
                    sd = sds[i]
                    sd.pending_outbound -= size_delta
                    sd.outbound_amount += size_delta
                    sd.current_amount  -= size_delta


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
    outbound_record.approval_datetime = datetime.now()
    db.session.flush()
    
    if outbound_record.outbound_type == 4:  # 如果是材料退回
        _update_financial_record(supplier_name, total_price, outbound_record_id)
        outbound_detail_list = (
            db.session.query(OutboundRecordDetail)
            .filter(OutboundRecordDetail.outbound_record_id == outbound_record_id)
            .all()
        )
        storage_id_list = [detail.material_storage_id for detail in outbound_detail_list]
        update_average_price(storage_id_list)
        update_outbound_amount(outbound_detail_list)

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
    outbound_record.reject_datetime = datetime.now()
    db.session.commit()
    return jsonify({"message": "success"})

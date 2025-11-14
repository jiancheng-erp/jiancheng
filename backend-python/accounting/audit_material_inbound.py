from flask import Blueprint, jsonify, request, abort, Response
from sqlalchemy import func
import json
from models import *
from api_utility import to_camel, to_snake, format_datetime
from app_config import db
from accounting.accounting_transaction import (
    add_payable_entity,
    material_inbound_accounting_event,
)
from constants import *
from decimal import Decimal
from collections import defaultdict
from datetime import datetime
from warehouse.material_storage import _outbound_material_helper

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


def update_average_price(storage_id_list):
    inbound_subq = (
        db.session.query(
            InboundRecordDetail.material_storage_id,
            func.sum(InboundRecordDetail.item_total_price).label("in_total_price"),
            func.sum(InboundRecordDetail.inbound_amount).label("in_amount"),
        )
        .join(
            InboundRecord,
            InboundRecordDetail.inbound_record_id == InboundRecord.inbound_record_id,
        )
        .filter(
            InboundRecord.inbound_type == 0, # 0:采购入库
            InboundRecord.display == 1,
            InboundRecord.approval_status == 1,
            InboundRecordDetail.material_storage_id.in_(storage_id_list),
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
            OutboundRecord.outbound_type == 4, # 4:材料退回
            OutboundRecord.display == 1,
            OutboundRecord.approval_status == 1,
            OutboundRecordDetail.material_storage_id.in_(storage_id_list),
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
            MaterialStorage.material_storage_id == final_query.c.material_storage_id,
        )
        .all()
    )
    for material_storage, avg_price in avg_prices:
        material_storage.average_price = avg_price


def update_inbound_amount(inbound_detail_list: list[InboundRecordDetail]):
    if not inbound_detail_list:
        return

    # 1) Gather unique storage ids
    msids = {d.material_storage_id for d in inbound_detail_list}

    # 2) Aggregate totals per storage (overall + each shoe size)
    agg_total = defaultdict(lambda: Decimal("0"))
    agg_size = defaultdict(lambda: defaultdict(lambda: 0))  # int for sizes is fine

    for detail in inbound_detail_list:
        msid = detail.material_storage_id

        # Sum overall inbound amount
        amount = getattr(detail, "inbound_amount", 0) or 0
        agg_total[msid] += Decimal(str(amount))

        # Sum each size amount
        for size in SHOESIZERANGE:
            col = f"size_{size}_inbound_amount"
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
            MaterialStorageSizeDetail.order_number,
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
        if total:  # only touch rows that actually have incoming totals
            storage.pending_inbound -= total
            storage.inbound_amount += total
            storage.current_amount += total

            # Update per-size amounts (respect the ordering by order_number)
            sds = size_details_map.get(msid, [])
            for i, size in enumerate(SHOESIZERANGE):
                if i >= len(sds):
                    break  # no more size rows for this storage
                size_delta = agg_size[msid].get(size, 0)
                if size_delta:
                    sd = sds[i]
                    sd.pending_inbound -= size_delta
                    sd.inbound_amount += size_delta
                    sd.current_amount += size_delta


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
    inbound_record.approval_datetime = datetime.now()
    db.session.flush()

    # update average price of material
    inbound_record_id = inbound_record.inbound_record_id
    inbound_detail_list = (
        db.session.query(InboundRecordDetail)
        .filter(InboundRecordDetail.inbound_record_id == inbound_record_id)
        .all()
    )

    storage_id_list = [detail.material_storage_id for detail in inbound_detail_list]

    update_average_price(storage_id_list)

    # 更新库存数量
    update_inbound_amount(inbound_detail_list)

    # 如果是复合材料入库，直接出库到生产，出库staff_id为面料仓管理员
    if inbound_record.warehouse_id == COMPOSITE_MATERIAL_WAREHOUSE_ID:
        data = {
            "items": [], 
            "outboundType": 0, 
            "departmentId": CUTTING_DEPARTMENT, 
            "totalPrice": 0,
            "currentDateTime": format_datetime(datetime.now()),
        }
        for detail in inbound_detail_list:
            item = {
                "materialStorageId": detail.material_storage_id,
                "outboundQuantity": detail.inbound_amount,
                "orderId": detail.order_id,
                "unitPrice": detail.unit_price,
                "itemTotalPrice": detail.item_total_price,
            }
            data["items"].append(item)
            data["totalPrice"] += detail.item_total_price
        _outbound_material_helper(data, staff_id=SURFACE_MATERIAL_CLERK_STAFF_ID)

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
    inbound_record.reject_datetime = datetime.now()
    db.session.commit()
    return jsonify({"message": "success"})

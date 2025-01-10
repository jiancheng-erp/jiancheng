from datetime import datetime
from decimal import Decimal

from api_utility import format_date
from app_config import db
from constants import (
    END_OF_PRODUCTION_NUMBER,
    IN_PRODUCTION_ORDER_NUMBER,
    PRODUCTION_LINE_REFERENCE,
    SHOESIZERANGE,
)
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request
from models import *
from sqlalchemy import func, or_, and_
from api_utility import format_datetime

finished_storage_bp = Blueprint("finished_storage_bp", __name__)


@finished_storage_bp.route(
    "/warehouse/warehousemanager/getfinishedinoutoverview", methods=["GET"]
)
def get_finished_in_out_overview():
    """
    op_type:
        0: show all orders,
        1: show active orders
    """
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    op_type = request.args.get("opType", default=0, type=int)
    query = (
        db.session.query(
            Order,
            OrderShoe,
            Shoe,
            func.sum(OrderShoeBatchInfo.total_amount).label("total_amount"),
            FinishedShoeStorage,
            Color
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .group_by(OrderShoe.order_shoe_id, FinishedShoeStorage.finished_shoe_id)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if op_type != 0:
        query = query.filter(FinishedShoeStorage.finished_status != 2)
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            order,
            order_shoe,
            shoe,
            total_amount,
            storage_obj,
            color
        ) = row
        if storage_obj.finished_status == 0:
            status_name = "未完成入库"
        elif storage_obj.finished_status == 1:
            status_name = "已完成入库"
        else:
            status_name = "已完成出库"
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "storageId": storage_obj.finished_shoe_id,
            "customerProductName": order_shoe.customer_product_name,
            "inboundAmount": total_amount,
            "currentAmount": storage_obj.finished_amount,
            "statusName": status_name,
            "endDate": format_date(order.end_date),
            "colorName": color.color_name
        }
        result.append(obj)
    return {"result": result, "total": count_result}


def handle_order_shoe_status(order_id, order_shoe_id, storage):
    # get order shoe amount
    response = (
        db.session.query(
            SemifinishedShoeStorage.semifinished_estimated_amount,
            SemifinishedShoeStorage.semifinished_amount,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == SemifinishedShoeStorage.order_shoe_type_id,
        )
        .filter(OrderShoeType.order_shoe_id == order_shoe_id)
        .all()
    )
    flag = True
    for row in response:
        order_shoe_type_amount, produced_amount = row
        if produced_amount < order_shoe_type_amount:
            flag = False
    if flag:
        next_operation_ids = [118, 119, 120, 121]
        event_arr = []
        try:
            processor: EventProcessor = current_app.config["event_processor"]
            for operation_id in next_operation_ids:
                event = Event(
                    staff_id=21,
                    handle_time=datetime.now(),
                    operation_id=operation_id,
                    event_order_id=order_id,
                    event_order_shoe_id=order_shoe_id,
                )
                processor.processEvent(event)
                event_arr.append(event)
        except Exception:
            return jsonify({"message": "event processor error"}), 500
        db.session.add_all(event_arr)
    db.session.flush()


@finished_storage_bp.route(
    "/warehouse/warehousemanager/inboundfinished", methods=["POST", "PATCH"]
)
def inbound_finished():
    data = request.get_json()
    storage = FinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "failed"}), 400

    storage.finished_amount += int(data["amount"])
    if storage.finished_amount >= storage.finished_estimated_amount:
        storage.finished_status = 1
        handle_order_shoe_status(data["orderId"], data["orderShoeId"], storage)
    storage.finished_inbound_datetime = data["inboundDate"]

    record = ShoeInboundRecord(
        inbound_amount=data["amount"],
        inbound_datetime=data["inboundDate"],
        finished_shoe_storage_id=storage.finished_shoe_id,
    )
    db.session.add(record)
    db.session.flush()
    rid = (
        "FIR"
        + datetime.now().strftime("%Y%m%d%H%M%S")
        + str(record.shoe_inbound_record_id)
    )
    record.shoe_inbound_rid = rid
    db.session.commit()
    return jsonify({"message": "success"})


@finished_storage_bp.route(
    "/warehouse/warehousemanager/outboundfinished", methods=["POST", "PATCH"]
)
def outbound_finished():
    data = request.get_json()
    if data["isOutboundAll"]:
        response = (
            db.session.query(FinishedShoeStorage)
            .join(
                OrderShoe,
                OrderShoe.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .filter(OrderShoe.order_id == data["orderId"])
            .all()
        )
        for row in response:
            storage = row
            _outbound_helper(storage, data)
    else:
        storage = FinishedShoeStorage.query.get(data["storageId"])
        if not storage:
            return jsonify({"message": "failed"}), 400
        _outbound_helper(storage, data)
    db.session.commit()
    return jsonify({"message": "success"})


def _outbound_helper(storage, data):
    record = ShoeOutboundRecord(
        outbound_amount=storage.finished_amount,
        outbound_datetime=data["outboundDate"],
        outbound_address=data["outboundAddress"],
        outbound_type=1,
        finished_shoe_storage_id=storage.finished_shoe_id,
    )
    storage.finished_amount = 0
    storage.finished_status = 2
    db.session.add(record)
    db.session.flush()
    rid = (
        "FOR"
        + datetime.now().strftime("%Y%m%d%H%M%S")
        + str(record.shoe_outbound_record_id)
    )
    record.shoe_outbound_rid = rid


@finished_storage_bp.route(
    "/warehouse/warehousemanager/getfinishedinoutboundrecords", methods=["GET"]
)
def get_finished_in_out_bound_records():
    db.session.query()
    storage_id = request.args.get("storageId")
    inbound_response = (
        db.session.query(ShoeInboundRecord, OutsourceInfo, OutsourceFactory)
        .outerjoin(
            OutsourceInfo,
            OutsourceInfo.outsource_info_id == ShoeInboundRecord.outsource_info_id,
        )
        .outerjoin(
            OutsourceFactory,
            OutsourceFactory.factory_id == OutsourceInfo.factory_id,
        )
        .filter(ShoeInboundRecord.finished_shoe_storage_id == storage_id)
        .all()
    )
    outbound_response = (
        db.session.query(ShoeOutboundRecord, OutsourceInfo, OutsourceFactory)
        .outerjoin(
            OutsourceInfo,
            OutsourceInfo.outsource_info_id == ShoeOutboundRecord.outsource_info_id,
        )
        .outerjoin(
            OutsourceFactory,
            OutsourceFactory.factory_id == OutsourceInfo.factory_id,
        )
        .filter(ShoeOutboundRecord.finished_shoe_storage_id == storage_id)
        .all()
    )

    result = {"inboundRecords": [], "outboundRecords": []}
    for row in inbound_response:
        record, _, factory = row
        factory_name = factory.factory_name if factory else ""
        obj = {
            "productionType": record.inbound_type,
            "date": format_datetime(record.inbound_datetime),
            "amount": record.inbound_amount,
            "source": factory_name
        }
        result["inboundRecords"].append(obj)

    for row in outbound_response:
        record, _, factory = row
        factory_name = factory.factory_name if factory else ""
        obj = {
            "productionType": record.outbound_type,
            "date": format_datetime(record.outbound_datetime),
            "amount": record.outbound_amount,
            "destination": factory_name,
            "picker": record.picker,
            "department": record.outbound_department,
            "address": record.outbound_address
        }
        result["outboundRecords"].append(obj)
    return result


@finished_storage_bp.route(
    "/warehouse/warehousemanager/completeinboundfinished", methods=["PATCH"]
)
def complete_inbound_finished():
    data = request.get_json()
    storage = FinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "order shoe storage not found"}), 400
    storage.finished_status = 1
    db.session.commit()
    return jsonify({"message": "success"})


@finished_storage_bp.route(
    "/warehouse/warehousemanager/completeoutboundfinished", methods=["PATCH"]
)
def complete_outbound_finished():
    data = request.get_json()
    storage = FinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "order shoe storage not found"}), 400
    storage.finished_status = 2
    db.session.commit()
    return jsonify({"message": "success"})

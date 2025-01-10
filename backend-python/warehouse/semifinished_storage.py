from datetime import datetime
from decimal import Decimal

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

semifinished_storage_bp = Blueprint("semifinished_storage_bp", __name__)


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/getsemifinishedinoutoverview", methods=["GET"]
)
def get_semifinished_in_out_overview():
    """
    showAll: 0 means show all orders, 1 means show active orders
    """
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    show_all = request.args.get("showAll", default=0, type=int)

    query = (
        db.session.query(
            Order,
            OrderShoe,
            Shoe,
            SemifinishedShoeStorage,
            Color,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            SemifinishedShoeStorage,
            SemifinishedShoeStorage.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .group_by(OrderShoe.order_shoe_id, SemifinishedShoeStorage.semifinished_shoe_id)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if show_all != 0:
        query = query.join(OrderStatus, OrderStatus.order_id == Order.order_id).filter(
            OrderStatus.order_current_status == IN_PRODUCTION_ORDER_NUMBER
        )
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (order, order_shoe, shoe, storage_obj, color) = row
        if storage_obj.semifinished_status == 0:
            status_name = "未完成入库"
        elif storage_obj.semifinished_status == 1:
            status_name = "已完成入库"
        else:
            status_name = "已完成出库"
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "storageId": storage_obj.semifinished_shoe_id,
            "customerProductName": order_shoe.customer_product_name,
            "estimatedInboundAmount": storage_obj.semifinished_estimated_amount,
            "actualInboundAmount": storage_obj.semifinished_actual_amount,
            "currentAmount": storage_obj.semifinished_amount,
            "statusName": status_name,
            "colorName": color.color_name,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


def handle_order_shoe_status(order_id, order_shoe_id, storage):
    # get order shoe type amount and current produced amount
    query = (
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
    )
    # if the object is 0, progress cutting
    if storage.semifinished_object == 0:
        query = query.filter(SemifinishedShoeStorage.semifinished_object == 0)
        next_operation_ids = [84, 85, 86, 87]
    # progress sewing
    else:
        query = query.filter(SemifinishedShoeStorage.semifinished_object == 1)
        next_operation_ids = [102, 103, 104, 105]

    response = query.all()
    flag = True
    for row in response:
        order_shoe_type_amount, produced_amount = row
        if produced_amount < order_shoe_type_amount:
            flag = False
    if flag:
        try:
            event_arr = []
            processor: EventProcessor = current_app.config["event_processor"]
            for operation_id in next_operation_ids:
                event = Event(
                    staff_id=20,
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


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/inboundsemifinished", methods=["POST", "PATCH"]
)
def inbound_semifinished():
    data = request.get_json()
    storage = SemifinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "failed"}), 400

    if data["inboundType"] == 1 and not data["outsourceInfoId"]:
        return jsonify({"message": "failed"}), 400
    elif data["inboundType"] == 1:
        outsource_info = OutsourceInfo.query.get(data["outsourceInfoId"])
        if not outsource_info:
            return jsonify({"message": "failed"}), 400
        if outsource_info.outsource_status == 5:
            outsource_info.outsource_status = 6

    storage.semifinished_actual_amount += int(data["amount"])
    storage.semifinished_amount += int(data["amount"])
    storage.semifinished_inbound_datetime = data["inboundDate"]

    record = ShoeInboundRecord(
        inbound_amount=data["amount"],
        inbound_datetime=data["inboundDate"],
        inbound_type=data["inboundType"],
        semifinished_shoe_storage_id=data["storageId"],
        remark=data["remark"],
        subsequent_stock=storage.semifinished_amount,
        outsource_info_id=data["outsourceInfoId"]
    )
    db.session.add(record)
    db.session.flush()
    rid = (
        "SIR"
        + datetime.now().strftime("%Y%m%d%H%M%S")
        + str(record.shoe_inbound_record_id)
    )
    record.shoe_inbound_rid = rid
    db.session.commit()
    return jsonify({"message": "success"})


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/finishoutsourceinbound", methods=["PATCH"]
)
def finish_outsource_inbound():
    data = request.get_json()
    outsource_info_id = data["outsourceInfoId"]
    info_obj = db.session.query(OutsourceInfo).get(outsource_info_id)
    if not info_obj:
        return jsonify({"message": "semifinished storage not found"}), 400
    if info_obj.outsource_status not in [5, 6]:
        return jsonify({"message": "invalid status"}), 400
    info_obj.outsource_status = 7
    db.session.commit()
    return jsonify({"message": "success"})


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/finishinboundsemifinished", methods=["PATCH"]
)
def finish_inbound_semifinished():
    data = request.get_json()
    storage = SemifinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "order shoe storage not found"}), 400
    storage.semifinished_status = 1
    db.session.commit()
    return jsonify({"message": "success"})


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/finishoutboundsemifinished", methods=["PATCH"]
)
def finish_outbound_semifinished():
    data = request.get_json()
    storage = SemifinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "order shoe storage not found"}), 400
    storage.semifinished_status = 2
    db.session.commit()
    return jsonify({"message": "success"})


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/finishoutsourceoutbound", methods=["POST", "PATCH"]
)
def finish_outsource_outbound():
    data = request.get_json()
    outsource_info_id = data["outsourceInfoId"]
    info_obj = db.session.query(OutsourceInfo).get(outsource_info_id)
    if not info_obj:
        return jsonify({"message": "semifinished storage not found"}), 400
    if info_obj.outsource_status not in [2, 4]:
        return jsonify({"message": "invalid status"}), 400

    counter = 0
    if info_obj.material_required:
        counter += 1
    if info_obj.semifinished_required:
        counter += 1

    if info_obj.outbound_counter == counter:
        info_obj.outsource_status = 5
    else:
        info_obj.outsource_counter += 1
    db.session.commit()
    return jsonify({"message": "success"})


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/outboundsemifinished", methods=["POST", "PATCH"]
)
def outbound_semifinished():
    data = request.get_json()
    storage = SemifinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "failed"}), 400

    if data["outboundType"] == 1 and not data["outsourceInfoId"]:
        return jsonify({"message": "failed"}), 400
    elif data["outboundType"] == 1:
        outsource_info = OutsourceInfo.query.get(data["outsourceInfoId"])
        if not outsource_info:
            return jsonify({"message": "failed"}), 400
        if outsource_info.outsource_status == 2:
            outsource_info.outsource_status = 4

    storage.semifinished_amount -= int(data["outboundAmount"])
    record = ShoeOutboundRecord(
        outbound_amount=int(data["outboundAmount"]),
        outbound_datetime=data["outboundDate"],
        outbound_type=data["outboundType"],
        semifinished_shoe_storage_id=storage.semifinished_shoe_id,
        subsequent_stock=storage.semifinished_amount,
        remark=data["remark"]
    )
    if data["outboundType"] == 0:
        record.picker = data["picker"]
    elif data["outboundType"] == 1:
        if not data["outsourceInfoId"]:
            return jsonify({"message": "failed"}), 400
        outsource_info = OutsourceInfo.query.get(data["outsourceInfoId"])
        if not outsource_info:
            return jsonify({"message": "failed"}), 400
        if outsource_info.outsource_status == 2:
            outsource_info.outsource_status = 4
        record.outsource_info_id = outsource_info.outsource_info_id
    else:
        return jsonify({"message": "failed"}), 400

    db.session.add(record)
    db.session.flush()
    rid = (
        "SOR"
        + datetime.now().strftime("%Y%m%d%H%M%S")
        + str(record.shoe_outbound_record_id)
    )
    record.shoe_outbound_rid = rid
    db.session.commit()
    return jsonify({"message": "success"})


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/getsemifinishedinoutboundrecords", methods=["GET"]
)
def get_semifinished_in_out_bound_records():
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
        .filter(ShoeInboundRecord.semifinished_shoe_storage_id == storage_id)
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
        .filter(ShoeOutboundRecord.semifinished_shoe_storage_id == storage_id)
        .all()
    )

    result = {"inboundRecords": [], "outboundRecords": []}
    for row in inbound_response:
        record, _, factory = row
        factory_name = factory.factory_name if factory else None
        obj = {
            "productionType": record.inbound_type,
            "shoeInboundRId": record.shoe_inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "amount": record.inbound_amount,
            "subsequentStock": record.subsequent_stock,
            "source": factory_name,
            "remark": record.remark
        }
        result["inboundRecords"].append(obj)

    for row in outbound_response:
        record, _, factory = row
        factory_name = factory.factory_name if factory else None
        obj = {
            "productionType": record.outbound_type,
            "shoeOutboundRId": record.shoe_outbound_rid,
            "timestamp": format_datetime(record.outbound_datetime),
            "amount": record.outbound_amount,
            "subsequentStock": record.subsequent_stock,
            "destination": factory_name,
            "picker": record.picker,
            "remark": record.remark
        }
        result["outboundRecords"].append(obj)
    return result

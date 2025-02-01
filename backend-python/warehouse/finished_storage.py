from datetime import datetime
from decimal import Decimal

from api_utility import format_date
from app_config import db
from business.batch_info_type import get_order_batch_type_helper
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
    customer_name = request.args.get("customerName")
    show_all = request.args.get("showAll", default=0, type=int)
    query = (
        db.session.query(Order, Customer, OrderShoe, Shoe, FinishedShoeStorage, Color)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
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
    if customer_name and customer_name != "":
        query = query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    # if show_all != 0:
    #     query = query.join(OrderStatus, OrderStatus.order_id == Order.order_id).filter(
    #         OrderStatus.order_current_status == IN_PRODUCTION_ORDER_NUMBER
    #     )
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (order, customer, order_shoe, shoe, storage_obj, color) = row
        if storage_obj.finished_status == 0:
            status_name = "未完成入库"
        elif storage_obj.finished_status == 1:
            status_name = "已完成入库"
        else:
            status_name = "已完成出库"
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "customerName": customer.customer_name,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "storageId": storage_obj.finished_shoe_id,
            "customerProductName": order_shoe.customer_product_name,
            "estimatedInboundAmount": storage_obj.finished_estimated_amount,
            "actualInboundAmount": storage_obj.finished_actual_amount,
            "currentAmount": storage_obj.finished_amount,
            "statusName": status_name,
            "endDate": format_date(order.end_date),
            "colorName": color.color_name,
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
    # Determine the next available group_id
    next_group_id = (
        db.session.query(
            func.coalesce(func.max(ShoeInboundRecord.inbound_batch_id), 0)
        ).scalar()
        + 1
    )
    for row in data:
        operation_purpose = row["operationPurpose"]
        timestamp = row["timestamp"]
        formatted_timestamp = (
            timestamp.replace("-", "").replace(" ", "").replace(":", "")
        )
        items = row["items"]
        counter = 0
        for item in items:
            storage_id = item["storageId"]
            remark = item["remark"]
            amount_list = item["amountList"]
            rid = "FIR" + formatted_timestamp + f"{counter:02}"
            storage = FinishedShoeStorage.query.get(storage_id)
            if not storage:
                return jsonify({"message": "failed"}), 400

            for i in range(len(amount_list)):
                db_name = i + 34
                column_name1 = f"size_{db_name}_actual_amount"
                actual_amount = getattr(storage, column_name1) + int(amount_list[i])
                column_name2 = f"size_{db_name}_amount"
                current_amount = getattr(storage, column_name2) + int(amount_list[i])
                setattr(storage, column_name1, actual_amount)
                setattr(storage, column_name2, current_amount)
                storage.finished_actual_amount += int(amount_list[i])
                storage.finished_amount += int(amount_list[i])

            storage.finished_inbound_datetime = timestamp
            total_amount = sum([int(x) for x in amount_list])
            record = ShoeInboundRecord(
                inbound_amount=total_amount,
                inbound_datetime=timestamp,
                inbound_type=operation_purpose,
                finished_shoe_storage_id=storage_id,
                remark=remark,
                subsequent_stock=storage.finished_amount,
                inbound_batch_id=next_group_id,
            )
            for i in range(len(amount_list)):
                db_name = i + 34
                column_name = f"size_{db_name}_amount"
                setattr(record, column_name, int(amount_list[i]))

            db.session.add(record)
            record.shoe_inbound_rid = rid
            counter += 1
        next_group_id += 1
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
        factory_name = factory.factory_name if factory else None
        obj = {
            "productionType": record.inbound_type,
            "shoeInboundRId": record.shoe_inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "amount": record.inbound_amount,
            "subsequentStock": record.subsequent_stock,
            "source": factory_name,
            "remark": record.remark,
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
            "remark": record.remark,
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


@finished_storage_bp.route("/warehouse/getfinishedinboundrecords", methods=["GET"])
def get_finished_inbound_records():
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    inbound_rid = request.args.get("inboundRId")
    query = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            Shoe.shoe_rid,
            ShoeInboundRecord.shoe_inbound_rid,
            ShoeInboundRecord.inbound_datetime,
            ShoeInboundRecord.inbound_batch_id,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ShoeInboundRecord,
            ShoeInboundRecord.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .distinct(ShoeInboundRecord.inbound_batch_id)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if start_date and start_date != "":
        query = query.filter(ShoeInboundRecord.inbound_datetime >= start_date)
    if end_date and end_date != "":
        query = query.filter(ShoeInboundRecord.inbound_datetime <= end_date)
    if inbound_rid and inbound_rid != "":
        query = query.filter(ShoeInboundRecord.shoe_inbound_rid.ilike(f"%{inbound_rid}%"))
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            order_id,
            order_rid,
            shoe_rid,
            shoe_inbound_rid,
            inbound_datetime,
            inbound_batch_id,
        ) = row
        obj = {
            "orderId": order_id,
            "orderRId": order_rid,
            "shoeRId": shoe_rid,
            "inboundRId": shoe_inbound_rid,
            "inboundBatchId": inbound_batch_id,
            "timestamp": format_datetime(inbound_datetime),
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@finished_storage_bp.route(
    "/warehouse/getfinishedinboundrecordbybatchid", methods=["GET"]
)
def get_finished_inbound_record_by_batch_id():
    order_id = request.args.get("orderId")
    batch_id = request.args.get("inboundBatchId")
    response = (
        db.session.query(ShoeInboundRecord, Color)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeInboundRecord.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .filter(ShoeInboundRecord.inbound_batch_id == batch_id)
        .all()
    )
    result = {"items": [], "shoeSizeColumns": []}
    for row in response:
        record, color = row
        obj = {
            "inboundRId": record.shoe_inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "amount": record.inbound_amount,
            "subsequentStock": record.subsequent_stock,
            "remark": record.remark,
            "colorName": color.color_name,
        }
        for i in range(len(SHOESIZERANGE)):
            db_name = i + 34
            column_name = f"size_{db_name}_amount"
            obj[f"amount{i}"] = getattr(record, column_name)
        obj["totalAmount"] = record.inbound_amount
        result["items"].append(obj)

    shoe_size_result = get_order_batch_type_helper(order_id)
    resulted_filtered_columns = []
    for i in range(len(shoe_size_result)):
        resulted_filtered_columns.append(
            {"label": shoe_size_result[i]["label"], "prop": f"amount{i}"}
        )
    result["shoeSizeColumns"] = resulted_filtered_columns
    return result
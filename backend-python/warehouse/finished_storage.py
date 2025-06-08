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
from sqlalchemy import func, or_, and_, desc
from api_utility import format_datetime
from login.login import current_user_info
from logger import logger

finished_storage_bp = Blueprint("finished_storage_bp", __name__)


@finished_storage_bp.route("/warehouse/getfinishedstorages", methods=["GET"])
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
    customer_product_name = request.args.get("customerProductName")
    show_all = request.args.get("showAll", default=0, type=int)
    query = (
        db.session.query(
            Order, Customer, OrderShoe, Shoe, FinishedShoeStorage, Color, BatchInfoType
        )
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
        .join(
            BatchInfoType, BatchInfoType.batch_info_type_id == Order.batch_info_type_id
        )
        .order_by(Order.order_rid)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if customer_name and customer_name != "":
        query = query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if customer_product_name and customer_product_name != "":
        query = query.filter(
            OrderShoe.customer_product_name.ilike(f"%{customer_product_name}%")
        )
    if show_all == 0:
        query = query.filter(FinishedShoeStorage.finished_status == 0)
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (order, customer, order_shoe, shoe, storage_obj, color, batch_info) = row
        if storage_obj.finished_status == 0:
            status_name = "未完成入库"
        elif storage_obj.finished_status == 1:
            status_name = "已完成入库"
        else:
            status_name = "已完成出库"
        remaining_amount = (
            storage_obj.finished_estimated_amount
            - storage_obj.finished_actual_amount
            if storage_obj.finished_actual_amount > 0
            else 0
        )
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
            "remainingAmount": remaining_amount,
            "storageStatus": status_name,
            "endDate": format_date(order.end_date),
            "colorName": color.color_name,
            "shoeSizeColumns": [],
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size_db_name = i + 34
            obj[f"size{shoe_size_db_name}EstimatedAmount"] = getattr(
                storage_obj, f"size_{shoe_size_db_name}_estimated_amount"
            )
            obj[f"size{shoe_size_db_name}ActualAmount"] = getattr(
                storage_obj, f"size_{shoe_size_db_name}_actual_amount"
            )
            obj[f"size{shoe_size_db_name}Amount"] = getattr(
                storage_obj, f"size_{shoe_size_db_name}_amount"
            )
            obj["shoeSizeColumns"].append(
                getattr(batch_info, f"size_{shoe_size_db_name}_name")
            )
        result.append(obj)
    return {"result": result, "total": count_result}


@finished_storage_bp.route("/warehouse/getproductoverview", methods=["GET"])
def get_product_overview():
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    order_cid = request.args.get("orderCId")
    customer_name = request.args.get("customerName")
    customer_brand = request.args.get("customerBrand")
    approval_status = request.args.get("approvalStatus")
    query = (
        db.session.query(
            Order,
            Customer,
            func.sum(OrderShoeBatchInfo.total_amount).label("order_amount"),
            func.sum(FinishedShoeStorage.finished_amount),
            func.coalesce(func.sum(ShoeOutboundRecordDetail.outbound_amount), 0),
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .outerjoin(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .group_by(Order.order_id)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if order_cid and order_cid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{order_cid}%"))
    if customer_name and customer_name != "":
        query = query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if customer_brand and customer_brand != "":
        query = query.filter(Customer.customer_brand.ilike(f"%{customer_brand}%"))
    if approval_status and approval_status != "":
        query = query.filter(Order.is_outbound_allowed == approval_status)
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        order, customer, order_amount, current_stock, outbounded_amount = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderCId": order.order_cid,
            "customerName": customer.customer_name,
            "customerBrand": customer.customer_brand,
            "startDate": format_date(order.start_date),
            "endDate": format_date(order.end_date),
            "orderAmount": order_amount,
            "currentStock": current_stock,
            "outboundedAmount": outbounded_amount,
            "orderShoeTable": [],
            "isOutboundAllowed": order.is_outbound_allowed,
        }
        result.append(obj)

    for order_obj in result:
        order_id = order_obj["orderId"]
        order_shoe_query = (
            db.session.query(
                OrderShoe,
                Shoe,
                func.sum(OrderShoeBatchInfo.total_amount).label(
                    "order_amount_per_color"
                ),
                FinishedShoeStorage,
                func.coalesce(
                    func.sum(ShoeOutboundRecordDetail.outbound_amount).label(
                        "outbound_amount"
                    ),
                    0,
                ),
                Color,
            )
            .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
            .join(Color, Color.color_id == ShoeType.color_id)
            .join(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .outerjoin(
                ShoeOutboundRecordDetail,
                ShoeOutboundRecordDetail.finished_shoe_storage_id
                == FinishedShoeStorage.finished_shoe_id,
            )
            .filter(OrderShoe.order_id == order_id)
            .group_by(
                OrderShoeType.order_shoe_type_id, FinishedShoeStorage.finished_shoe_id
            )
            .all()
        )
        for row in order_shoe_query:
            (
                order_shoe,
                shoe,
                order_amount_per_color,
                storage_obj,
                outbound_amount,
                color,
            ) = row
            obj = {
                "orderShoeId": order_shoe.order_shoe_id,
                "shoeRId": shoe.shoe_rid,
                "customerProductName": order_shoe.customer_product_name,
                "orderAmountPerColor": order_amount_per_color,
                "outboundedAmount": outbound_amount,
                "storageId": storage_obj.finished_shoe_id,
                "currentStock": storage_obj.finished_amount,
                "colorName": color.color_name,
            }
            order_obj["orderShoeTable"].append(obj)
    return {"result": result, "total": count_result}


def _determine_status(storage):
    if storage.finished_estimated_amount > storage.finished_actual_amount:
        return False
    return True


@finished_storage_bp.route("/warehouse/inboundfinished", methods=["POST", "PATCH"])
def inbound_finished():
    data = request.get_json()
    remark = data.get("remark")
    items = data.get("items", [])
    timestamp = format_datetime(datetime.now())
    formatted_timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    rid = "FIR" + formatted_timestamp + "T0"
    inbound_record = ShoeInboundRecord(
        shoe_inbound_rid=rid,
        inbound_datetime=timestamp,
        inbound_type=0,
        remark=remark,
    )
    db.session.add(inbound_record)
    db.session.flush()

    total_amount = 0
    for item in items:
        storage_id = item["storageId"]
        remark = item["remark"]
        amount_list = item["amountList"]
        inbound_quantity = item.get("inboundQuantity", 0)
        response = (
            db.session.query(Order, OrderShoe, FinishedShoeStorage)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(
                FinishedShoeStorage.finished_shoe_id == storage_id,
            )
            .first()
        )
        if not response:
            return jsonify({"message": "无成品记录"}), 400

        order, order_shoe, storage = response
        storage.finished_actual_amount += inbound_quantity
        storage.finished_amount += inbound_quantity
        # for i in range(len(amount_list)):
        #     db_name = i + 34
        #     column_name1 = f"size_{db_name}_actual_amount"
        #     actual_amount = getattr(storage, column_name1) + int(amount_list[i])
        #     column_name2 = f"size_{db_name}_amount"
        #     current_amount = getattr(storage, column_name2) + int(amount_list[i])
        #     setattr(storage, column_name1, actual_amount)
        #     setattr(storage, column_name2, current_amount)
        #     storage.finished_actual_amount += int(amount_list[i])
        #     storage.finished_amount += int(amount_list[i])

        # sub_total_amount = sum([int(x) for x in amount_list])
        record_detail = ShoeInboundRecordDetail(
            inbound_amount=inbound_quantity,
            finished_shoe_storage_id=storage_id,
            remark=remark,
        )
        # for i in range(len(amount_list)):
        #     db_name = i + 34
        #     column_name = f"size_{db_name}_amount"
        #     setattr(record_detail, column_name, int(amount_list[i]))

        db.session.add(record_detail)
        if _determine_status(storage):
            storage.finished_status = 1
        record_detail.shoe_inbound_record_id = inbound_record.shoe_inbound_record_id
        total_amount += inbound_quantity
    inbound_record.inbound_amount = total_amount
    # check if the order_shoe is completed
    cross_check = (
        db.session.query(FinishedShoeStorage)
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(
            OrderShoe.order_shoe_id == order_shoe.order_shoe_id,
        )
        .all()
    )
    is_finished = True
    for storage in cross_check:
        if _determine_status(storage) is False:
            is_finished = False
            break
    if is_finished:
        processor: EventProcessor = current_app.config["event_processor"]
        staff_id = current_user_info()[1].staff_id
        try:
            for operation in [84, 85]:
                event = Event(
                    staff_id=staff_id,
                    handle_time=datetime.now(),
                    operation_id=operation,
                    event_order_id=order.order_id,
                    event_order_shoe_id=order_shoe.order_shoe_id,
                )
                processor.processEvent(event)

            # update order status
            for operation in [18, 19, 20, 21]:
                event = Event(
                    staff_id=staff_id,
                    handle_time=datetime.now(),
                    operation_id=operation,
                    event_order_id=order.order_id,
                )
                processor.processEvent(event)
        except Exception as e:
            logger.debug(e)
            return jsonify({"message": "failed"}), 400
    db.session.commit()
    return jsonify({"message": "success"})


def _determine_outbound_status(storage):
    outbound_amount = (
        db.session.query(func.sum(ShoeOutboundRecordDetail.outbound_amount))
        .filter(
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == storage.finished_shoe_id
        )
        .scalar()
    )
    if outbound_amount >= storage.finished_estimated_amount:
        return True
    return False


def check_finished_storage_status_for_order(order_id):
    """
    Check if all finished storage for the given order_id are completed.
    """
    finished_storages = (
        db.session.query(FinishedShoeStorage)
        .join(
            OrderShoeType,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(OrderShoe.order_id == order_id)
        .all()
    )
    for storage in finished_storages:
        if storage.finished_status != 2:  # Not completed
            return False
    return True


@finished_storage_bp.route(
    "/warehouse/warehousemanager/outboundfinished", methods=["POST", "PATCH"]
)
def outbound_finished():
    data = request.get_json()
    timestamp = format_datetime(datetime.now())
    formatted_timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    items = data["items"]
    rid = "FOR" + formatted_timestamp + "T0"
    picker = data.get("picker", "")
    outbound_record = ShoeOutboundRecord(
        shoe_outbound_rid=rid,
        outbound_datetime=timestamp,
        outbound_type=0,
        remark=data.get("remark", ""),
        picker=picker,
    )
    db.session.add(outbound_record)
    db.session.flush()

    total_amount = 0
    unique_order_id = set()
    for item in items:
        storage_id = item["storageId"]
        remark = item["remark"]
        outbound_quantity = item.get("outboundQuantity", 0)
        unique_order_id.add(item["orderId"])
        storage = db.session.query(FinishedShoeStorage).get(storage_id)
        if not storage:
            return jsonify({"message": "无成品记录"}), 400
        if storage.finished_amount == 0:
            return jsonify({"message": "没有库存"}), 400

        storage.finished_amount -= outbound_quantity
        record_detail = ShoeOutboundRecordDetail(
            shoe_outbound_record_id=outbound_record.shoe_outbound_record_id,
            outbound_amount=outbound_quantity,
            finished_shoe_storage_id=storage_id,
            remark=remark,
        )

        db.session.add(record_detail)
        db.session.flush()
        if _determine_outbound_status(storage) is True:
            storage.finished_status = 2
        total_amount += outbound_quantity
    outbound_record.outbound_amount = total_amount

    processor: EventProcessor = current_app.config["event_processor"]
    staff_id = current_user_info()[1].staff_id
    for order_id in unique_order_id:
        if check_finished_storage_status_for_order(order_id):
            try:
                for operation in [30, 31]:
                    event = Event(
                        staff_id=staff_id,
                        handle_time=datetime.now(),
                        operation_id=operation,
                        event_order_id=order_id,
                    )
                    processor.processEvent(event)
            except Exception as e:
                logger.debug(e)
                return jsonify({"message": "推进流程失败"}), 500
    db.session.commit()
    return jsonify({"message": "success"})


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
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    query = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            Shoe.shoe_rid,
            Color.color_name,
            ShoeInboundRecord.shoe_inbound_rid,
            ShoeInboundRecord.inbound_datetime,
            ShoeInboundRecordDetail,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ShoeInboundRecordDetail,
            ShoeInboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .join(
            ShoeInboundRecord,
            ShoeInboundRecord.shoe_inbound_record_id
            == ShoeInboundRecordDetail.shoe_inbound_record_id,
        )
        .order_by(desc(ShoeInboundRecord.inbound_datetime))
    )
    if start_date and start_date != "":
        query = query.filter(ShoeInboundRecord.inbound_datetime >= start_date)
    if end_date and end_date != "":
        query = query.filter(ShoeInboundRecord.inbound_datetime <= end_date)
    if inbound_rid and inbound_rid != "":
        query = query.filter(
            ShoeInboundRecord.shoe_inbound_rid.ilike(f"%{inbound_rid}%")
        )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            order_id,
            order_rid,
            shoe_rid,
            color_name,
            shoe_inbound_rid,
            inbound_datetime,
            inbound_detail,
        ) = row
        obj = {
            "orderId": order_id,
            "orderRId": order_rid,
            "shoeRId": shoe_rid,
            "colorName": color_name,
            "inboundRId": shoe_inbound_rid,
            "timestamp": format_datetime(inbound_datetime),
            "detailAmount": inbound_detail.inbound_amount,
            "remark": inbound_detail.remark,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@finished_storage_bp.route("/warehouse/getfinishedoutboundrecords", methods=["GET"])
def get_finished_outbound_records():
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    outbound_rid = request.args.get("outboundRId")
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    query = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            Order.order_cid,
            Shoe.shoe_rid,
            Color.color_name,
            Customer.customer_name,
            ShoeOutboundRecord.shoe_outbound_rid,
            ShoeOutboundRecord.outbound_datetime,
            ShoeOutboundRecordDetail,
        )
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .join(
            ShoeOutboundRecord,
            ShoeOutboundRecord.shoe_outbound_record_id
            == ShoeOutboundRecordDetail.shoe_outbound_record_id,
        )
        .order_by(desc(ShoeOutboundRecord.outbound_datetime))
    )
    if start_date and start_date != "":
        query = query.filter(ShoeOutboundRecord.outbound_datetime >= start_date)
    if end_date and end_date != "":
        query = query.filter(ShoeOutboundRecord.outbound_datetime <= end_date)
    if outbound_rid and outbound_rid != "":
        query = query.filter(
            ShoeOutboundRecord.shoe_outbound_rid.ilike(f"%{outbound_rid}%")
        )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []

    for row in response:
        (
            order_id,
            order_rid,
            order_cid,
            shoe_rid,
            color_name,
            customer_name,
            outbound_rid,
            outbound_datetime,
            record_detail,
        ) = row
        obj = {
            "orderId": order_id,
            "orderRId": order_rid,
            "orderCId": order_cid,
            "shoeRId": shoe_rid,
            "colorName": color_name,
            "customerName": customer_name,
            "outboundRId": outbound_rid,
            "timestamp": format_datetime(outbound_datetime),
            "detailAmount": record_detail.outbound_amount,
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
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
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


@finished_storage_bp.route(
    "/warehouse/getfinishedoutboundrecordbybatchid", methods=["GET"]
)
def get_finished_outbound_record_by_batch_id():
    order_id = request.args.get("orderId")
    batch_id = request.args.get("outboundBatchId")
    response = (
        db.session.query(ShoeOutboundRecord, Shoe, Color)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeOutboundRecord.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .filter(ShoeOutboundRecord.outbound_batch_id == batch_id)
        .all()
    )
    result = {"items": [], "shoeSizeColumns": []}
    for row in response:
        record, shoe, color = row
        obj = {
            "shoeRId": shoe.shoe_rid,
            "outboundRId": record.shoe_outbound_rid,
            "timestamp": format_datetime(record.outbound_datetime),
            "amount": record.outbound_amount,
            "subsequentStock": record.subsequent_stock,
            "remark": record.remark,
            "colorName": color.color_name,
        }
        for i in range(len(SHOESIZERANGE)):
            db_name = i + 34
            column_name = f"size_{db_name}_amount"
            obj[f"amount{i}"] = getattr(record, column_name)
        obj["totalAmount"] = record.outbound_amount
        result["items"].append(obj)

    shoe_size_result = get_order_batch_type_helper(order_id)
    resulted_filtered_columns = []
    for i in range(len(shoe_size_result)):
        resulted_filtered_columns.append(
            {"label": shoe_size_result[i]["label"], "prop": f"amount{i}"}
        )
    result["shoeSizeColumns"] = resulted_filtered_columns
    return result


@finished_storage_bp.route("/warehouse/getmultipleshoesizecolumns", methods=["GET"])
def get_multiple_shoe_size_columns():
    order_id = request.args.get("orderId")
    shoe_size_names = get_order_batch_type_helper(order_id)
    query = (
        db.session.query(FinishedShoeStorage)
        .outerjoin(
            ShoeOutboundRecord,
            FinishedShoeStorage.finished_shoe_id
            == ShoeOutboundRecord.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .filter(Order.order_id == order_id)
    )
    for i in range(len(SHOESIZERANGE)):
        db_name = i + 34
        column_name = f"size_{db_name}_amount"
        query = query.add_columns(
            func.coalesce(func.sum(getattr(ShoeOutboundRecord, column_name)), 0)
        )
    response = query.group_by(FinishedShoeStorage.finished_shoe_id).all()
    result = {}
    for row in response:
        storage, *shoe_size_columns = row
        result[storage.finished_shoe_id] = []
        for i in range(len(shoe_size_names)):
            shoe_size_db_name = i + 34
            obj = {
                "typeId": shoe_size_names[i]["id"],
                "typeName": shoe_size_names[i]["type"],
                "shoeSizeName": shoe_size_names[i]["label"],
                "predictQuantity": getattr(
                    storage, f"size_{shoe_size_db_name}_estimated_amount"
                ),
                "outboundedQuantity": int(shoe_size_columns[i]),
                "actualQuantity": getattr(
                    storage, f"size_{shoe_size_db_name}_actual_amount"
                ),
                "currentQuantity": getattr(storage, f"size_{shoe_size_db_name}_amount"),
            }
            result[storage.finished_shoe_id].append(obj)
    return result


@finished_storage_bp.route("/warehouse/gettotalstockoffinishedstorage", methods=["GET"])
def get_total_stock_of_finished_storage():
    """
    Get the total stock of semifinished storage.
    """
    total_stock = db.session.query(
        func.sum(FinishedShoeStorage.finished_amount)
    ).scalar()
    if total_stock is None:
        total_stock = 0
    return jsonify({"totalStock": total_stock})


@finished_storage_bp.route(
    "/warehouse/getremainingamountoffinishedstorage", methods=["GET"]
)
def get_remaining_amount_of_finished_storage():
    """
    Get the remaining amount of semifinished storage.
    """
    response = (
        db.session.query(
            func.sum(
                FinishedShoeStorage.finished_estimated_amount
                - FinishedShoeStorage.finished_actual_amount
            )
        )
        .filter(FinishedShoeStorage.finished_actual_amount > 0)
        .scalar()
    )
    return jsonify({"remainingAmount": response})

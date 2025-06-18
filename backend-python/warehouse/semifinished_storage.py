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
from sqlalchemy import func, or_, and_, desc
from api_utility import format_datetime
from shared_apis.batch_info_type import get_order_batch_type_helper

semifinished_storage_bp = Blueprint("semifinished_storage_bp", __name__)


@semifinished_storage_bp.route("/warehouse/getsemifinishedstorages", methods=["GET"])
def get_semifinished_storages():
    """
    showAll: 0 means show all orders, 1 means show active orders
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
            Order,
            Customer,
            OrderShoe,
            Shoe,
            SemifinishedShoeStorage,
            Color,
            BatchInfoType,
        )
        .join(Customer, Order.customer_id == Customer.customer_id)
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
        query = query.filter(SemifinishedShoeStorage.semifinished_status == 0)
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (order, customer, order_shoe, shoe, storage_obj, color, batch_info) = row
        if storage_obj.semifinished_status == 0:
            status_name = "未完成入库"
        elif storage_obj.semifinished_status == 1:
            status_name = "已完成入库"
        else:
            status_name = "已完成出库"
        remaining_amount = (
            storage_obj.semifinished_estimated_amount
            - storage_obj.semifinished_actual_amount
            if storage_obj.semifinished_actual_amount > 0
            else 0
        )
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "storageId": storage_obj.semifinished_shoe_id,
            "customerName": customer.customer_name,
            "customerProductName": order_shoe.customer_product_name,
            "estimatedInboundAmount": storage_obj.semifinished_estimated_amount,
            "actualInboundAmount": storage_obj.semifinished_actual_amount,
            "currentAmount": storage_obj.semifinished_amount,
            "remainingAmount": remaining_amount,
            "storageStatus": status_name,
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


@semifinished_storage_bp.route("/warehouse/getshoesizecolumns", methods=["GET"])
def get_shoe_size_columns():
    order_id = request.args.get("orderId")
    storage_id = request.args.get("storageId")
    storage_type = request.args.get("storageType", 0)
    if storage_type == 0:
        storage = SemifinishedShoeStorage.query.get(storage_id)
    else:
        storage = FinishedShoeStorage.query.get(storage_id)
    shoe_size_names = get_order_batch_type_helper(order_id)
    result = []
    for i, shoe_size in enumerate(shoe_size_names):
        shoe_size_db_name = i + 34
        obj = {
            "typeId": shoe_size_names[i]["id"],
            "typeName": shoe_size_names[i]["type"],
            "shoeSizeName": shoe_size_names[i]["label"],
            "predictQuantity": getattr(
                storage, f"size_{shoe_size_db_name}_estimated_amount"
            ),
            "actualQuantity": getattr(
                storage, f"size_{shoe_size_db_name}_actual_amount"
            ),
            "currentQuantity": getattr(storage, f"size_{shoe_size_db_name}_amount"),
        }
        result.append(obj)
    return result


def _determine_status(storage):
    if storage.semifinished_estimated_amount > storage.semifinished_actual_amount:
        return False
    return True


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/inboundsemifinished", methods=["POST", "PATCH"]
)
def inbound_semifinished():
    data = request.get_json()
    operation_purpose = data["operationPurpose"]
    outsource_info_id = data.get("outsourceInfoId", None)
    remark = data.get("remark")
    items = data.get("items", [])
    timestamp = format_datetime(datetime.now())
    formatted_timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    rid = "SIR" + formatted_timestamp + "T" + str(operation_purpose)
    inbound_record = ShoeInboundRecord(
        shoe_inbound_rid=rid,
        inbound_datetime=timestamp,
        inbound_type=operation_purpose,
        remark=remark,
    )
    if operation_purpose == 1 and not outsource_info_id:
        return jsonify({"message": "外包入库需选厂家"}), 400

    if operation_purpose == 1:
        outsource_info = db.session.query(OutsourceInfo).get(outsource_info_id)
        if not outsource_info:
            return jsonify({"message": "无外包信息"}), 400
        if outsource_info.outsource_status == 5:
            outsource_info.outsource_status = 6
        inbound_record.outsource_info_id = outsource_info_id

    db.session.add(inbound_record)
    db.session.flush()
    total_amount = 0

    for item in items:
        storage_id = item["storageId"]
        remark = item["remark"]
        inbound_quantity = item.get("inboundQuantity", 0)
        amount_list = item["amountList"]

        storage = db.session.query(SemifinishedShoeStorage).get(storage_id)
        if not storage:
            return jsonify({"message": "该库存不存在"}), 400

        storage.semifinished_actual_amount += inbound_quantity
        storage.semifinished_amount += inbound_quantity

        # for i in range(len(amount_list)):
        #     db_name = i + 34
        #     column_name1 = f"size_{db_name}_actual_amount"
        #     actual_amount = getattr(storage, column_name1) + int(amount_list[i])
        #     column_name2 = f"size_{db_name}_amount"
        #     current_amount = getattr(storage, column_name2) + int(amount_list[i])
        #     setattr(storage, column_name1, actual_amount)
        #     setattr(storage, column_name2, current_amount)
        #     storage.semifinished_actual_amount += int(amount_list[i])
        #     storage.semifinished_amount += int(amount_list[i])

        # sub_total_amount = sum([int(x) for x in amount_list])

        record_detail = ShoeInboundRecordDetail(
            shoe_inbound_record_id=inbound_record.shoe_inbound_record_id,
            inbound_amount=inbound_quantity,
            semifinished_shoe_storage_id=storage_id,
            remark=remark,
        )
        # for i in range(len(amount_list)):
        #     db_name = i + 34
        #     column_name = f"size_{db_name}_amount"
        #     setattr(record_detail, column_name, int(amount_list[i]))

        db.session.add(record_detail)
        total_amount += inbound_quantity
        if _determine_status(storage):
            storage.semifinished_status = 1
    inbound_record.inbound_amount = total_amount

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


def _determine_outbound_status(storage):
    outbound_amount = (
        db.session.query(func.sum(ShoeOutboundRecordDetail.outbound_amount))
        .filter(
            ShoeOutboundRecordDetail.semifinished_shoe_storage_id == storage.semifinished_shoe_id
        )
        .scalar()
    )
    if outbound_amount >= storage.semifinished_estimated_amount:
        return True
    return False


@semifinished_storage_bp.route(
    "/warehouse/outboundsemifinished", methods=["POST", "PATCH"]
)
def outbound_semifinished():
    data = request.get_json()
    picker = data.get("picker", None)
    remark = data.get("remark", None)
    items = data.get("items", [])
    timestamp = format_datetime(datetime.now())
    formatted_timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    rid = "SOR" + formatted_timestamp + "T0"
    outbound_record = ShoeOutboundRecord(
        shoe_outbound_rid=rid,
        outbound_datetime=timestamp,
        outbound_type=0,
        remark=remark,
        picker=picker,
    )
    db.session.add(outbound_record)
    db.session.flush()
    total_amount = 0
    for item in items:
        storage_id = item["storageId"]
        outboundQuantity = item.get("outboundQuantity", 0)
        remark = item.get("remark", None)
        amount_list = item["amountList"]
        storage = db.session.query(SemifinishedShoeStorage).get(storage_id)
        if not storage:
            return jsonify({"message": "failed"}), 400

        if storage.semifinished_amount < outboundQuantity:
            return jsonify({"message": "出库数量大于库存"}), 400
        storage.semifinished_amount -= outboundQuantity
        # for i in range(len(amount_list)):
        #     db_name = i + 34
        #     column_name = f"size_{db_name}_amount"
        #     current_amount = getattr(storage, column_name) - int(amount_list[i])
        #     if current_amount < 0:
        #         return jsonify({"message": "出库数量大于库存"}), 400
        #     setattr(storage, column_name, current_amount)
        #     storage.semifinished_amount -= int(amount_list[i])

        # sub_total_amount = sum([int(x) for x in amount_list])

        record = ShoeOutboundRecordDetail(
            shoe_outbound_record_id=outbound_record.shoe_outbound_record_id,
            outbound_amount=outboundQuantity,
            semifinished_shoe_storage_id=storage_id,
            remark=remark,
        )
        # for i in range(len(amount_list)):
        #     db_name = i + 34
        #     column_name = f"size_{db_name}_amount"
        #     setattr(record, column_name, int(amount_list[i]))

        db.session.add(record)
        db.session.flush()
        if _determine_outbound_status(storage) is True:
            storage.semifinished_status = 2
        total_amount += outboundQuantity
    outbound_record.outbound_amount = total_amount
    db.session.commit()
    return jsonify({"message": "success"})


@semifinished_storage_bp.route(
    "/warehouse/warehousemanager/getsemifinishedinoutboundrecords", methods=["GET"]
)
def get_semifinished_in_out_bound_records():
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


@semifinished_storage_bp.route("/warehouse/getsemiinboundrecords", methods=["GET"])
def get_semi_inbound_records():
    storage_id = request.args.get("storageId")
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    inbound_rid = request.args.get("inboundRId")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    query = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            Shoe.shoe_rid,
            ShoeInboundRecord,
            ShoeInboundRecordDetail,
            OutsourceFactory.factory_name,
            Color.color_name,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            SemifinishedShoeStorage,
            SemifinishedShoeStorage.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ShoeInboundRecordDetail,
            ShoeInboundRecordDetail.semifinished_shoe_storage_id
            == SemifinishedShoeStorage.semifinished_shoe_id,
        )
        .join(
            ShoeInboundRecord,
            ShoeInboundRecord.shoe_inbound_record_id
            == ShoeInboundRecordDetail.shoe_inbound_record_id,
        )
        .outerjoin(
            OutsourceInfo,
            OutsourceInfo.outsource_info_id == ShoeInboundRecord.outsource_info_id,
        )
        .outerjoin(
            OutsourceFactory,
            OutsourceFactory.factory_id == OutsourceInfo.factory_id,
        )
    )

    if start_date:
        query = query.filter(
            ShoeInboundRecord.inbound_datetime
            >= datetime.strptime(start_date, "%Y-%m-%d")
        )
    if end_date:
        query = query.filter(
            ShoeInboundRecord.inbound_datetime
            <= datetime.strptime(end_date, "%Y-%m-%d")
        )
    if inbound_rid:
        query = query.filter(
            ShoeInboundRecord.shoe_inbound_rid.ilike(f"%{inbound_rid}%")
        )
    if order_rid:
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid:
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    query = query.order_by(desc(ShoeInboundRecord.inbound_datetime))
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            order_id,
            order_rid,
            shoe_rid,
            inbound_record,
            inbound_detail,
            factory_name,
            color_name,
        ) = row
        obj = {
            "orderId": order_id,
            "orderRId": order_rid,
            "shoeRId": shoe_rid,
            "inboundRId": inbound_record.shoe_inbound_rid,
            "timestamp": format_datetime(inbound_record.inbound_datetime),
            "inboundType": inbound_record.inbound_type,
            "factoryName": factory_name,
            "detailAmount": inbound_detail.inbound_amount,
            "colorName": color_name,
            "remark": inbound_detail.remark,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@semifinished_storage_bp.route(
    "/warehouse/getsemiinboundrecordbybatchid", methods=["GET"]
)
def get_semi_inbound_record_by_batch_id():
    order_id = request.args.get("orderId")
    batch_id = request.args.get("inboundBatchId")
    response = (
        db.session.query(ShoeInboundRecord, Color, OutsourceFactory.factory_name)
        .join(
            SemifinishedShoeStorage,
            SemifinishedShoeStorage.semifinished_shoe_id
            == ShoeInboundRecord.semifinished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == SemifinishedShoeStorage.order_shoe_type_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .outerjoin(
            OutsourceInfo,
            OutsourceInfo.outsource_info_id == ShoeInboundRecord.outsource_info_id,
        )
        .outerjoin(
            OutsourceFactory,
            OutsourceFactory.factory_id == OutsourceInfo.factory_id,
        )
        .filter(ShoeInboundRecord.inbound_batch_id == batch_id)
        .all()
    )
    result = {"items": [], "shoeSizeColumns": []}
    for row in response:
        record, color, factory_name = row
        obj = {
            "inboundRId": record.shoe_inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "amount": record.inbound_amount,
            "subsequentStock": record.subsequent_stock,
            "source": factory_name,
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


@semifinished_storage_bp.route("/warehouse/getsemioutboundrecords", methods=["GET"])
def get_semi_outbound_records():
    storage_id = request.args.get("storageId")
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    outbound_rid = request.args.get("outboundRId")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    picker = request.args.get("picker")
    query = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            Shoe.shoe_rid,
            ShoeOutboundRecord,
            ShoeOutboundRecordDetail,
            Color.color_name,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            SemifinishedShoeStorage,
            SemifinishedShoeStorage.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.semifinished_shoe_storage_id
            == SemifinishedShoeStorage.semifinished_shoe_id,
        )
        .join(
            ShoeOutboundRecord,
            ShoeOutboundRecord.shoe_outbound_record_id
            == ShoeOutboundRecordDetail.shoe_outbound_record_id,
        )
    )

    if start_date:
        query = query.filter(
            ShoeOutboundRecord.outbound_datetime
            >= datetime.strptime(start_date, "%Y-%m-%d")
        )
    if end_date:
        query = query.filter(
            ShoeOutboundRecord.outbound_datetime
            <= datetime.strptime(end_date, "%Y-%m-%d")
        )
    if outbound_rid:
        query = query.filter(
            ShoeOutboundRecord.shoe_outbound_rid.ilike(f"%{outbound_rid}%")
        )
    if order_rid:
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid:
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if picker:
        query = query.filter(ShoeOutboundRecord.picker.ilike(f"%{picker}%"))
    query = query.order_by(desc(ShoeOutboundRecord.outbound_datetime))
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            order_id,
            order_rid,
            shoe_rid,
            outbound_record,
            outbound_detail,
            color_name,
        ) = row
        obj = {
            "orderId": order_id,
            "orderRId": order_rid,
            "shoeRId": shoe_rid,
            "outboundRId": outbound_record.shoe_outbound_rid,
            "timestamp": format_datetime(outbound_record.outbound_datetime),
            "outboundType": outbound_record.outbound_type,
            "detailAmount": outbound_detail.outbound_amount,
            "colorName": color_name,
            "picker": outbound_record.picker,
            "remark": outbound_detail.remark,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@semifinished_storage_bp.route(
    "/warehouse/getsemioutboundrecordbybatchid", methods=["GET"]
)
def get_semi_outbound_record_by_batch_id():
    order_id = request.args.get("orderId")
    batch_id = request.args.get("outboundBatchId")
    response = (
        db.session.query(ShoeOutboundRecord, Color)
        .join(
            SemifinishedShoeStorage,
            SemifinishedShoeStorage.semifinished_shoe_id
            == ShoeOutboundRecord.semifinished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == SemifinishedShoeStorage.order_shoe_type_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .filter(ShoeOutboundRecord.outbound_batch_id == batch_id)
        .all()
    )
    result = {"items": [], "shoeSizeColumns": []}
    for row in response:
        record, color = row
        obj = {
            "outboundRId": record.shoe_outbound_rid,
            "timestamp": format_datetime(record.outbound_datetime),
            "amount": record.outbound_amount,
            "subsequentStock": record.subsequent_stock,
            "picker": record.picker,
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


@semifinished_storage_bp.route("/warehouse/gettotalstockofsemistorage", methods=["GET"])
def get_total_stock_of_semi_storage():
    """
    Get the total stock of semifinished storage.
    """
    total_stock = db.session.query(
        func.sum(SemifinishedShoeStorage.semifinished_amount)
    ).scalar()
    if total_stock is None:
        total_stock = 0
    return jsonify({"totalStock": total_stock})


@semifinished_storage_bp.route("/warehouse/getremainingamountofsemistorage", methods=["GET"])
def get_remaining_amount_of_semi_storage():
    """
    Get the remaining amount of semifinished storage.
    """
    response = db.session.query(
        func.sum(SemifinishedShoeStorage.semifinished_estimated_amount - SemifinishedShoeStorage.semifinished_actual_amount)
    ).filter(
        SemifinishedShoeStorage.semifinished_actual_amount > 0
    ).scalar()
    return jsonify({"remainingAmount": response})

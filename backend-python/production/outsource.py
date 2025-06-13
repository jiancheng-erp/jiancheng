import traceback
from datetime import datetime, timedelta
from decimal import Decimal

from api_utility import (
    format_date,
    format_line_group,
    outsource_status_converter,
    outsource_status_strtoint,
    to_camel,
)
from app_config import db
from constants import *
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request
from models import *
from sqlalchemy import func, or_
from sqlalchemy.dialects.mysql import insert

outsource_bp = Blueprint("outsource_bp", __name__)


@outsource_bp.route(
    "/production/productionmanager/getorderoutsourceoverview", methods=["GET"]
)
def get_order_outsource_overview():
    page = request.args.get("page", type=int)
    page_size = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    outsource_status = request.args.get("outsourceStatus")
    query = (
        db.session.query(
            Order,
            OrderShoe,
            Shoe,
            Customer,
            OutsourceInfo,
            OutsourceFactory,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(OutsourceInfo, OutsourceInfo.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OutsourceFactory, OutsourceFactory.factory_id == OutsourceInfo.factory_id)
        .filter(OrderStatus.order_current_status >= IN_PRODUCTION_ORDER_NUMBER)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if outsource_status and outsource_status != "":
        query = query.filter(
            OutsourceInfo.outsource_status == outsource_status_strtoint(outsource_status)
        )
    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()
    result = []
    attr_names = OutsourceInfo.__table__.columns.keys()
    OUTSOURCE_TYPE_MAPPING = {
        "0": "裁断",
        "1": "针车",
        "2": "成型",
    }
    for row in response:
        (
            order,
            order_shoe,
            shoe,
            customer,
            outsource_info,
            factory,
        ) = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "customerName": customer.customer_name,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "orderEndDate": format_date(order.end_date),
            "outsourceFactory": factory.factory_name,
        }
        for db_attr in attr_names:
            if db_attr == "outsource_type":
                outsource_type = outsource_info.outsource_type.split(",")
                obj[to_camel(db_attr)] = [
                    OUTSOURCE_TYPE_MAPPING[team_int] for team_int in outsource_type
                ]
            elif db_attr == "outsource_status":
                obj[to_camel(db_attr)] = outsource_status_converter(
                    outsource_info.outsource_status
                )
            else:
                obj[to_camel(db_attr)] = getattr(outsource_info, db_attr)
        result.append(obj)
    return {"result": result, "totalLength": count_result}


@outsource_bp.route(
    "/production/productionmanager/getordershoeoutsourceinfo", methods=["GET"]
)
def get_order_shoe_outsource_info():
    order_shoe_id = request.args.get("orderShoeId")
    response = (
        (
            db.session.query(OutsourceInfo, OutsourceFactory)
            .join(OrderShoe, OrderShoe.order_shoe_id == OutsourceInfo.order_shoe_id)
            .join(
                OutsourceFactory,
                OutsourceFactory.factory_id == OutsourceInfo.factory_id,
            )
        )
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .all()
    )
    result = []
    for row in response:
        outsource_info, factory = row
        temp = ""
        if outsource_info.outsource_type == "0,1":
            temp = "裁断+针车"
        elif outsource_info.outsource_type == "1":
            temp = "针车"
        obj = {
            "outsourceInfoId": outsource_info.outsource_info_id,
            "outsourceType": temp,
            "outsourceFactory": {
                "id": outsource_info.factory_id,
                "value": factory.factory_name,
            },
            "outsourceAmount": outsource_info.outsource_amount,
            "outsourceStartDate": format_date(outsource_info.outsource_start_date),
            "outsourceEndDate": format_date(outsource_info.outsource_end_date),
            "outsourceStatus": outsource_status_converter(
                outsource_info.outsource_status
            ),
            "deadlineDate": format_date(outsource_info.deadline_date),
            "materialRequired": outsource_info.material_required,
            "semifinishedRequired": outsource_info.semifinished_required,
            "materialEstimatedOutboundDate": format_date(
                outsource_info.material_estimated_outbound_date
            ),
            "semifinishedEstimatedOutboundDate": format_date(
                outsource_info.semifinished_estimated_outbound_date
            ),
            "rejectionReason": outsource_info.rejection_reason,
        }
        result.append(obj)
    return result


@outsource_bp.route(
    "/production/productionmanager/getoutsourcebatchinfo", methods=["GET"]
)
def get_outsource_batch_info():
    order_shoe_id = request.args.get("orderShoeId")
    outsource_info_id = request.args.get("outsourceInfoId")
    query = (
        db.session.query(OutsourceBatchInfo, OrderShoeType.order_shoe_type_id, Color)
        .join(
            OrderShoeType,
            OutsourceBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .filter(
            OrderShoeType.order_shoe_id == order_shoe_id,
        )
    )
    if outsource_info_id and outsource_info_id != "":
        query = query.filter(OutsourceBatchInfo.outsource_info_id == outsource_info_id)

    entities = query.all()
    # Dictionary to accumulate total amounts by color
    color_totals = {}

    # First loop to accumulate total amounts for each color
    for entity in entities:
        outsource_batch_info, _, color = entity
        if color.color_name not in color_totals:
            color_totals[color.color_name] = 0
        color_totals[color.color_name] += outsource_batch_info.total_outsource_amount
    # Second loop to build the result list and include the color totals
    result = []
    for entity in entities:
        outsource_batch_info, order_shoe_type_id, color = entity
        obj = {
            "outsourceBatchInfoId": outsource_batch_info.outsource_batch_info_id,
            "orderShoeTypeId": order_shoe_type_id,
            "colorName": color.color_name,
            "totalAmount": color_totals[
                color.color_name
            ],  # Add total amount for the color
        }
        for i in range(34, 47):
            obj[f"size{i}Amount"] = getattr(
                outsource_batch_info, f"size_{i}_outsource_amount"
            )
        result.append(obj)
    return result


@outsource_bp.route(
    "/production/productionmanager/storeoutsourceforordershoe", methods=["PUT"]
)
def store_outsource_for_order_shoe():
    outsource_input = request.get_json()
    departments = ""
    for line in outsource_input["type"].split("+"):
        if line == "裁断":
            departments += "0,"
        elif line == "针车":
            departments += "1,"
        else:
            return jsonify({"message": "failed"}), 400
    departments = departments[:-1]
    obj = {
        "outsource_type": departments,
        "factory_id": outsource_input["factoryId"],
        "outsource_start_date": outsource_input["outsourceStartDate"],
        "outsource_end_date": outsource_input["outsourceEndDate"],
        "deadline_date": outsource_input["deadlineDate"],
        "outsource_amount": 0,
        "outsource_status": 0,
        "order_shoe_id": outsource_input["orderShoeId"],
    }
    obj["material_required"] = outsource_input["materialRequired"]
    obj["material_estimated_outbound_date"] = (
        outsource_input["materialEstimatedOutboundDate"]
        if obj["material_required"]
        else None
    )
    obj["semifinished_required"] = outsource_input["semifinishedRequired"]
    obj["semifinished_estimated_outbound_date"] = (
        outsource_input["semifinishedEstimatedOutboundDate"]
        if obj["semifinished_required"]
        else None
    )
    info_obj = None
    outsource_info_id = -1
    if outsource_input["outsourceInfoId"]:
        obj["outsource_info_id"] = outsource_input["outsourceInfoId"]
        outsource_info_id = outsource_input["outsourceInfoId"]
        stmt = insert(OutsourceInfo).values(**obj)
        stmt = stmt.on_duplicate_key_update(**obj)
        db.session.execute(stmt)
    else:
        info_obj = OutsourceInfo(**obj)
        db.session.add(info_obj)
        db.session.flush()
        outsource_info_id = info_obj.outsource_info_id
    # set production info
    production_obj = OrderShoeProductionInfo.query.filter_by(
        order_shoe_id=outsource_input["orderShoeId"]
    ).first()
    for line in outsource_input["type"].split("+"):
        if line == "裁断":
            production_obj.is_cutting_outsourced = True
        elif line == "针车":
            production_obj.is_sewing_outsourced = True
        elif line == "成型":
            production_obj.is_molding_outsourced = True

    outsource_amount = 0
    for row in outsource_input["outsourceAmount"]:
        outsource_obj = {}

        outsource_obj["total_outsource_amount"] = 0
        for i in range(34, 47):
            outsource_obj[f"size_{i}_outsource_amount"] = 0
            if f"size{i}Amount" in row:
                outsource_obj[f"size_{i}_outsource_amount"] = int(row[f"size{i}Amount"])
                outsource_obj["total_outsource_amount"] += int(row[f"size{i}Amount"])

        # set outsource batch info id
        if "outsourceBatchInfoId" in row:
            outsource_obj["outsource_batch_info_id"] = row["outsourceBatchInfoId"]

        # set outsource_info_id
        outsource_obj["outsource_info_id"] = outsource_info_id

        # set order_shoe_type_id
        outsource_obj["order_shoe_type_id"] = row["orderShoeTypeId"]

        stmt = insert(OutsourceBatchInfo).values(**outsource_obj)
        stmt = stmt.on_duplicate_key_update(**outsource_obj)
        db.session.execute(stmt)
        outsource_amount += outsource_obj["total_outsource_amount"]

    # set amount
    outsource_info = db.session.query(OutsourceInfo).get(outsource_info_id)
    outsource_info.outsource_amount = outsource_amount
    db.session.commit()
    return jsonify({"message": "success"})


@outsource_bp.route(
    "/production/productionmanager/deleteoutsourceinfo", methods=["DELETE"]
)
def delete_outsource_info():
    order_shoe_id = request.args.get("orderShoeId")
    outsource_info_id = request.args.get("outsourceInfoId")
    outsource_info = (
        db.session.query(OutsourceInfo)
        .filter(OutsourceInfo.outsource_info_id == outsource_info_id)
        .first()
    )
    # set production info
    production_obj = OrderShoeProductionInfo.query.filter_by(
        order_shoe_id=order_shoe_id
    ).first()
    for line in outsource_info.outsource_type.split(","):
        if line == "0":
            production_obj.is_cutting_outsourced = False
        elif line == "1":
            production_obj.is_sewing_outsourced = False
        elif line == "2":
            production_obj.is_molding_outsourced = False

    db.session.delete(outsource_info)
    db.session.query(OutsourceBatchInfo).filter(
        OutsourceBatchInfo.outsource_info_id == outsource_info_id
    ).delete()
    db.session.commit()
    return jsonify({"message": "succuess"})


@outsource_bp.route(
    "/production/productionmanager/submitoutsourceinfo", methods=["PATCH"]
)
def submit_outsource_info():
    data = request.get_json()
    # set approval status to 1
    info_id = data["outsourceInfoId"]
    response = (
        db.session.query(OutsourceInfo)
        .filter(OutsourceInfo.outsource_info_id == info_id)
        .first()
    )
    response.outsource_status = 1
    db.session.commit()
    return jsonify({"message": "success"})


@outsource_bp.route(
    "/production/productionmanager/editoutsourcestatus", methods=["PATCH"]
)
def edit_outsource_status():
    data = request.get_json()
    outsource_info_id = data["outsourceInfoId"]
    outsource_obj = db.session.query(OutsourceInfo).get(outsource_info_id)
    outsource_obj.outsource_status = 4
    db.session.commit()
    return jsonify({"message": "success"})


@outsource_bp.route(
    "/production/productionmanager/getoutsourcesemifinishedshipping", methods=["GET"]
)
def get_outsource_semifinished_shipping():
    outsource_info_id = request.args.get("outsourceInfoId")
    response = (
        db.session.query(OutsourceInfo, SemifinishedShoeStorage, ShoeOutboundRecord)
        .join(
            SemifinishedShoeStorage,
            SemifinishedShoeStorage.order_shoe_id == OutsourceInfo.order_shoe_id,
        )
        .join(
            ShoeOutboundRecord,
            ShoeOutboundRecord.semifinished_shoe_storage_id
            == SemifinishedShoeStorage.semifinished_shoe_id,
        )
        .filter(
            OutsourceInfo.outsource_info_id == outsource_info_id,
        )
        .all()
    )
    result = []
    for row in response:
        outsource_info, shoe_storage, record = row
        obj = {
            "semifinishedObject": shoe_storage.semifinished_object,
            "semifinishedAmount": shoe_storage.semifinished_amount,
            "semifinishedStatus": shoe_storage.semifinished_status,
            "semifinishedEstimatedOutboundDate": outsource_info.semifinished_estimated_outbound_date,
            "outboundDatetime": record.outbound_datetime,
        }
        result.append(obj)
    return result


@outsource_bp.route(
    "/production/productionmanager/getoutsourcematerialshipping", methods=["GET"]
)
def get_outsource_material_shipping():
    outsource_info_id = request.args.get("outsourceInfoId")
    # 发货数量：material_storage.current_amount
    query1 = (
        db.session.query(
            OutsourceInfo,
            MaterialStorage.material_outsource_status,
            MaterialStorage.current_amount,
            MaterialStorage.material_storage_color,
            Material,
            MaterialType,
            OutboundRecord,
        )
        .join(OrderShoe, OutsourceInfo.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            MaterialStorage,
            MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(
            Material,
            Material.material_id == MaterialStorage.material_id,
        )
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(
            OutboundRecord,
            OutboundRecord.material_storage_id == MaterialStorage.material_storage_id,
        )
        .filter(
            OutsourceInfo.outsource_info_id == outsource_info_id,
        )
    )
    response = query1.all()
    result = []
    for row in response:
        (
            outsource_info,
            material_outsource_status,
            current_amount,
            color_name,
            material,
            material_type,
            record,
        ) = row
        obj = {
            "materialType": material_type.material_type_name,
            "materialName": material.material_name,
            "materialUnit": material.material_unit,
            "outsourceStatus": material_outsource_status,
            "outboundAmount": current_amount,
            "materialEstimateOutboundDate": outsource_info.material_estimated_outbound_date,
            "outboundDatetime": record.outbound_datetime,
            "colorName": color_name,
        }
        result.append(obj)
    return result


@outsource_bp.route(
    "/production/productionmanager/getoutsourceapprovaloverview", methods=["GET"]
)
def get_outsource_approval_overview():
    page = request.args.get("page", type=int)
    page_size = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    query = (
        db.session.query(Order, OrderShoe, Shoe, OutsourceInfo, OutsourceFactory)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OutsourceInfo, OutsourceInfo.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OutsourceFactory, OutsourceFactory.factory_id == OutsourceInfo.factory_id)
        .filter(OutsourceInfo.outsource_status != 0)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()
    result = []
    mapping = {"0": "裁断", "1": "针车", "2": "成型"}
    for row in response:
        (order, order_shoe, shoe, outsource_info, factory) = row

        arr = [
            mapping[team_int] for team_int in outsource_info.outsource_type.split(",")
        ]
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "orderStartDate": format_date(order.start_date),
            "orderEndDate": format_date(order.end_date),
            "outsourceInfoId": outsource_info.outsource_info_id,
            "outsourceType": arr,
            "factoryName": factory.factory_name,
            "outsourceAmount": outsource_info.outsource_amount,
            "outsourceStartDate": format_date(outsource_info.outsource_start_date),
            "outsourceEndDate": format_date(outsource_info.outsource_end_date),
            "outsourceStatus": outsource_status_converter(
                outsource_info.outsource_status
            ),
            "deadlineDate": format_date(outsource_info.deadline_date),
            "semifinishedEstimatedOutboundDate": format_date(
                outsource_info.semifinished_estimated_outbound_date
            ),
            "semifinishedRequired": outsource_info.semifinished_required,
            "materialEstimatedOutboundDate": format_date(
                outsource_info.material_estimated_outbound_date
            ),
        }
        result.append(obj)
    return {"result": result, "totalLength": count_result}


@outsource_bp.route("/production/productionmanager/approveoutsource", methods=["PATCH"])
def approve_outsource():
    outsource_info_id = request.get_json()["outsourceInfoId"]
    entity = db.session.query(OutsourceInfo).get(outsource_info_id)
    entity.outsource_status = 2
    production_info = (
        db.session.query(OrderShoeProductionInfo)
        .filter_by(order_shoe_id=entity.order_shoe_id)
        .first()
    )
    if entity.outsource_type == "0,1":
        production_info.is_cutting_outsourced = True
    elif entity.outsource_type == "1":
        production_info.is_sewing_outsourced = True
    db.session.commit()
    return {"message": "success"}


@outsource_bp.route("/production/productionmanager/rejectoutsource", methods=["PATCH"])
def reject_outsource():
    data = request.get_json()
    outsource_info_id = data["outsourceInfoId"]
    entity = db.session.query(OutsourceInfo).get(outsource_info_id)
    entity.outsource_status = 3
    entity.rejection_reason = data["rejectionReason"]
    db.session.commit()
    return {"message": "success"}


@outsource_bp.route(
    "/production/productionmanager/getoutsourcecostdetail", methods=["GET"]
)
def get_outsource_cost_detail():
    outsource_info_id = request.args.get("outsourceInfoId")
    response = (
        db.session.query(OutsourceCostDetail)
        .filter_by(outsource_info_id=outsource_info_id)
        .all()
    )
    attr_names = OutsourceCostDetail.__table__.columns.keys()
    result = []
    for row in response:
        obj = {}
        for db_attr in attr_names:
            if db_attr == "item_cost":
                obj[to_camel(db_attr)] = float(getattr(row, db_attr))
            else:
                obj[to_camel(db_attr)] = getattr(row, db_attr)
        result.append(obj)
    return result


@outsource_bp.route(
    "/production/productionmanager/storeoutsourcecostdata", methods=["PATCH"]
)
def store_outsource_cost_data():
    data = request.get_json()
    if data:
        outsource_info_id = data[0]["outsourceInfoId"]
    # delete outsource cost
    db.session.query(OutsourceCostDetail).filter_by(
        outsource_info_id=outsource_info_id
    ).delete()
    db.session.flush()
    # insert new data
    result = []
    total_cost = 0
    for row in data:
        total_cost += Decimal(row["itemTotalCost"])
        entity = OutsourceCostDetail(
            item_name=row["itemName"],
            item_cost=row["itemCost"],
            item_total_cost=row["itemTotalCost"],
            remark=row["remark"],
            outsource_info_id=row["outsourceInfoId"],
        )
        result.append(entity)
    outsource_info = db.session.query(OutsourceInfo).get(outsource_info_id)
    outsource_info.total_cost = total_cost
    db.session.add_all(result)
    db.session.commit()
    return jsonify({"message": "success"})

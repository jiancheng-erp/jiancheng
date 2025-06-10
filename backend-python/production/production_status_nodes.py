import traceback
from datetime import datetime, timedelta

from api_utility import format_date, format_line_group
from app_config import db
from constants import *
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request
from models import *
from sqlalchemy import func, or_
from sqlalchemy.dialects.mysql import insert
from logger import logger
production_status_nodes_bp = Blueprint("production_status_nodes_bp", __name__)


@production_status_nodes_bp.route(
    "/production/productionmanager/getfinishednodes", methods=["GET"]
)
def get_finished_nodes():
    page = request.args.get("page", type=int)
    page_size = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    status_point = request.args.get("nodeName")
    query = (
        db.session.query(Order, OrderShoe, Shoe, OrderShoeStatusReference)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderStatus, Order.order_id == OrderStatus.order_id)
        .join(
            OrderShoeStatusReference,
            OrderShoeStatusReference.status_id == OrderShoeStatus.current_status,
        )
        .filter(OrderStatus.order_current_status == 9)
        .filter(OrderShoeStatus.current_status_value.in_([0, 1]))
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if status_point and ORDER_SHOE_STATUS_REFERENCE[status_point]:
        query = query.filter(
            OrderShoeStatus.current_status == ORDER_SHOE_STATUS_REFERENCE[status_point]
        )
    else:
        query = query.filter(
            OrderShoeStatus.current_status.in_([18, 23, 24, 30, 31, 32, 33, 40, 41, 42])
        )
    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()
    result = []
    for row in response:
        order, order_shoe, shoe, reference = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "nodeName": reference.status_name,
        }
        result.append(obj)
    return {"result": result, "totalLength": count_result}


@production_status_nodes_bp.route(
    "/production/productionmanager/getordershoestatus", methods=["GET"]
)
def get_order_shoe_status():
    order_shoe_id = request.args.get("orderShoeId")
    order_shoe_status = (
        db.session.query(func.group_concat(OrderShoeStatus.current_status))
        .filter(OrderShoeStatus.order_shoe_id == order_shoe_id)
        .first()
    )
    arr = order_shoe_status[0].split(",")
    return arr


@production_status_nodes_bp.route(
    "/production/productionmanager/editordershoestatus", methods=["PATCH"]
)
def edit_order_shoe_status():
    data = request.get_json()
    order_shoe_id = data["orderShoeId"]
    arr = []
    order_shoe_status, status_value = (
        db.session.query(
            func.group_concat(OrderShoeStatus.current_status),
            func.group_concat(OrderShoeStatus.current_status_value),
        )
        .filter(OrderShoeStatus.order_shoe_id == order_shoe_id)
        .first()
    )
    status_arr: list = order_shoe_status.split(",")
    status_value_arr: list = status_value.split(",")

    # 相关外包完成才能推进生产线完成
    outsource_info = (
        db.session.query(OutsourceInfo).filter_by(order_shoe_id=order_shoe_id).all()
    )
    for info in outsource_info:
        if (
            (
                "24" in status_arr
                and info.outsource_type[-1] == "0"
                and info.outsource_status != 7
            )
            or (
                "33" in status_arr
                and info.outsource_type[-1] == "1"
                and info.outsource_status != 7
            )
            or (
                "41" in status_arr
                and info.outsource_type[-1] == "2"
                and info.outsource_status != 7
            )
        ):
            return jsonify({"message": "外包尚未完成"}), 400

    # 半成品或成品入库完成才能推进生产线完成
    storage_status = None
    if "24" in status_arr:
        storage_status = (
            db.session.query(
                SemifinishedShoeStorage.semifinished_status.label("storage_status")
            )
            .filter_by(order_shoe_id=order_shoe_id, semifinished_object=0)
            .scalar()
        )
    elif "33" in status_arr:
        storage_status = (
            db.session.query(
                SemifinishedShoeStorage.semifinished_status.label("storage_status")
            )
            .filter_by(order_shoe_id=order_shoe_id, semifinished_object=1)
            .scalar()
        )
    elif "41" in status_arr:
        storage_status = (
            db.session.query(
                FinishedShoeStorage.finished_status.label("storage_status")
            )
            .filter_by(order_shoe_id=order_shoe_id)
            .scalar()
        )
    # if not storage_status:
    #     return jsonify({"message": "仓库不存在"}), 404
    if storage_status and storage_status != 1:
        return jsonify({"message": "成品尚未入库"}), 400

    team = -1
    # 添加半成品仓，成品仓
    if "18" in status_arr:
        team = 0
        order_shoe_type_ids = (
            db.session.query(OrderShoeType.order_shoe_type_id)
            .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
            .filter_by(order_shoe_id=order_shoe_id)
            .all()
        )
        logger.debug(order_shoe_type_ids)
        for id in order_shoe_type_ids:
            for obj in [0, 1]:
                semi_entity = SemifinishedShoeStorage(
                    order_shoe_type_id=id[0],
                    semifinished_status=0,
                    semifinished_object=obj,
                )
                arr.append(semi_entity)
            finished_entity = FinishedShoeStorage(
                order_shoe_type_id=id[0],
                finished_status=0,
            )
            arr.append(finished_entity)
    elif "24" in status_arr:
        team = 1
    elif "33" in status_arr:
        team = 2
    if team > -1:
        # 如果没有自产，直接跳至工组结束
        production_amount = (
            db.session.query(
                func.sum(OrderShoeProductionAmount.total_production_amount)
            )
            .join(
                OrderShoeType,
                OrderShoeProductionAmount.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .filter(
                OrderShoe.order_shoe_id == order_shoe_id,
                OrderShoeProductionAmount.production_team == team,
            )
            .group_by(
                OrderShoe.order_shoe_id, OrderShoeProductionAmount.production_team
            )
            .scalar()
        )
        if production_amount == 0:
            current_status_id = -1
            next_status_id = -1
            if "18" in status_arr:
                current_status_id = 18
                next_status_id = 24
            elif "24" in status_arr:
                current_status_id = 24
                next_status_id = 33
            elif "33" in status_arr:
                current_status_id = 33
                next_status_id = 41
            else:
                return (
                    jsonify({"message": "Invalid status"}),
                    400,
                )
            status_obj = (
                db.session.query(OrderShoeStatus)
                .filter_by(
                    order_shoe_id=order_shoe_id, current_status=current_status_id
                )
                .first()
            )
            status_obj.current_status = next_status_id
            status_obj.current_status_value = 0
            db.session.add_all(arr)
            db.session.commit()
            return jsonify({"message": "跳至下一生产线结束"}), 200
    production_nodes = ["18", "23", "24", "30", "31", "32", "33", "40", "41", "42"]
    matching_status = next((num for num in status_arr if num in production_nodes), None)
    if not matching_status:
        return (
            jsonify({"message": "You cannot progress the production in this state"}),
            400,
        )
    # 生产线开始要等工价审批完才能结束
    if "23" in status_arr and (
        "22" not in status_arr or (status_value_arr[status_arr.index("22")] != "2")
    ):
        return jsonify({"message": "裁断工价单尚未审批"}), 400
    if "32" in status_arr and (
        "29" not in status_arr or (status_value_arr[status_arr.index("29")] != "2")
    ):
        return jsonify({"message": "针车工价单尚未审批"}), 400
    if "40" in status_arr and (
        "39" not in status_arr or (status_value_arr[status_arr.index("39")] != "2")
    ):
        return jsonify({"message": "成型工价单尚未审批"}), 400
    if "18" in status_arr:
        report1 = UnitPriceReport(order_shoe_id=order_shoe_id, team="裁断", status=0)
        arr.append(report1)
    elif "24" in status_arr:
        report1 = UnitPriceReport(
            order_shoe_id=order_shoe_id, team="针车预备", status=0
        )
        report2 = UnitPriceReport(order_shoe_id=order_shoe_id, team="针车", status=0)
        arr.append(report1)
        arr.append(report2)
    elif "33" in status_arr:
        report = UnitPriceReport(order_shoe_id=order_shoe_id, team="成型", status=0)
        arr.append(report)
    try:
        processor: EventProcessor = current_app.config["event_processor"]
        # find operation id
        operations = (
            db.session.query(Operation)
            .filter_by(operation_type=2, operation_modified_status=int(matching_status))
            .all()
        )
        operation_ids = [row.operation_id for row in operations]
        for op in operation_ids:
            event = Event(
                staff_id=1,
                handle_time=datetime.now(),
                operation_id=op,
                event_order_id=data["orderId"],
                event_order_shoe_id=order_shoe_id,
            )
            processor.processEvent(event)
    except Exception as e:
        logger.debug(e)
        return jsonify({"message": "failed"}), 400
    db.session.add_all(arr)
    db.session.commit()
    return jsonify({"message": "success"})

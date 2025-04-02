from torch import res
import constants
import time
from app_config import db
from flask import Blueprint, jsonify, request, send_file, current_app
from sqlalchemy import func, null
from api_utility import to_snake, to_camel
from login.login import current_user, current_user_info
import math
import os
from datetime import datetime
from event_processor import EventProcessor
import json

from constants import IN_PRODUCTION_ORDER_NUMBER, SHOESIZERANGE
from general_document.order_export import (
    generate_excel_file,
)
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH
from models import *
from shared_apis import order

DEPARTMENT_STATUS_DICT = {
    "3": ["6"],
    "7": ["0"],
    "14": ["4", "11"],
    "13": ["9", "13", "0"],
    "11": ["7"],
}
DEPARTMENT_ORDER_STATUS_DICT = {"4": ["6"], "2": ["7"]}

DEPARTMENT_DICT = {
    "3": "物控部",
    "7": "开发部",
    "14": "用量填写",
    "13": "技术部",
    "11": "总仓",
    "2": "总经理",
    "4": "业务部经理",
}

STATUS_REVERT_DICT = {
    "0": "材料名称，型号，规格等信息错误/缺失",
    "4": "材料用量错误/缺失",
    "6": "采购用量错误/缺失",
    "7": "采购用量错误/缺失",
    "9": "工艺单错误/缺失",
    "11": "生产用量错误/缺失",
}

ORDER_STATUS_REVERT_DICT = {"6": "订单信息有误/缺失"}

FIRST_LOGISTICS_FLOW = [0, 4, 6]
SECOND_LOGISTICS_FLOW = [0, 4, 7]
CRAFT_SHEET_FLOW = [0, 9, 11, 13]

ORDER_ISSUE_FLOW = [6, 7]

revert_order_api = Blueprint("revert_order_api", __name__)


@revert_order_api.route("/revertorder/getrevertorderlist", methods=["GET"])
def get_revert_order_list():
    import re

    def extract_rid_number(order_rid):
        """Extract the base number from order_rid like 'K25-001(2)' -> 1"""
        match = re.search(r"[KW]\d{2}-(\d{3})", order_rid)
        if match:
            return int(match.group(1))
        return None

    department_id = request.args.get("departmentId")
    staff_id = request.args.get("staffId")
    order_status = DEPARTMENT_STATUS_DICT.get(department_id)

    orders = (
        db.session.query(Order, OrderShoe, Shoe, OrderShoeStatus, Customer)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .filter(
            OrderShoeStatus.current_status.in_(order_status),
            OrderShoeStatus.revert_info.isnot(None),
        )
        .all()
    )

    result = []
    for order, order_shoe, shoe, order_shoe_status, customer in orders:
        if order_shoe_status.current_status == 0:
            rid_number = extract_rid_number(order.order_rid)
            prefix = order.order_rid[0] if order.order_rid else ""

            if staff_id == "15":
                # show order_rid after k25-200, w25-200
                if prefix in ("K", "W") and rid_number is not None and rid_number < 200:
                    continue

            if staff_id == "7":
                # show order_rid before/equal to 200 and only 开发一部
                if prefix in ("K", "W") and rid_number is not None and rid_number > 200:
                    continue
                if shoe.shoe_department_id != "开发一部":
                    continue

            if staff_id == "31":
                # show order_rid before/equal to 200 and only 开发二部
                if prefix in ("K", "W") and rid_number is not None and rid_number > 200:
                    continue
                if shoe.shoe_department_id != "开发二部":
                    continue

            if staff_id == "32":
                # show order_rid before/equal to 200 and only 开发三部
                if prefix in ("K", "W") and rid_number is not None and rid_number > 200:
                    continue
                if shoe.shoe_department_id != "开发三部":
                    continue

        revert_info = json.loads(order_shoe_status.revert_info)
        source_status = revert_info.get("source_status", "")
        desti_status = revert_info.get("desti_status", "")
        revert_time = revert_info.get("revert_time", "")
        revert_depart = revert_info.get("revert_depart", "")
        revert_reason = revert_info.get("revert_reason", "")
        current_status = revert_info.get("middle_process", [])[0]

        result.append(
            {
                "orderId": order.order_id,
                "orderRId": order.order_rid,
                "shoeId": shoe.shoe_rid,
                "currentStatus": current_status,
                "customerName": customer.customer_name,
                "statusSource": revert_depart,
                "statusDesti": desti_status,
                "revertTime": revert_time,
                "revertReason": revert_reason,
            }
        )

    return jsonify(result)


@revert_order_api.route("/revertorder/getsinglerevertorder", methods=["GET"])
def get_single_revert_order():
    order_id = request.args.get("orderId")
    order = (
        db.session.query(Order, OrderShoe, Shoe, OrderShoeStatus, Customer)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .filter(
            Order.order_id == order_id,
            OrderShoeStatus.revert_info.isnot(None),
        )
        .first()
    )
    revert_info = json.loads(order.OrderShoeStatus.revert_info)
    source_status = revert_info.get("source_status", "")
    desti_status = revert_info.get("desti_status", "")
    revert_time = revert_info.get("revert_time", "")
    revert_depart = revert_info.get("revert_depart", "")
    revert_reason = revert_info.get("revert_reason", "")
    revert_detail = revert_info.get("revert_detail", "")
    middle_process = revert_info.get("middle_process", [])
    # convert middle process to department string
    middle_process_departments = []
    for status in middle_process:
        department = DEPARTMENT_DICT.get(
            next(
                (
                    key
                    for key, value in DEPARTMENT_STATUS_DICT.items()
                    if str(status) in value
                ),
                "Unknown Department",
            )
        )
        middle_process_departments.append(department)
    middle_process = middle_process_departments
    result = {
        "orderId": order[0].order_id,
        "orderRId": order[0].order_rid,
        "shoeId": order[2].shoe_rid,
        "customerName": order[4].customer_name,
        "statusSource": revert_depart,
        "revertTime": revert_time,
        "revertReason": revert_reason,
        "revertDetail": revert_detail,
        "middleProcess": middle_process,
    }
    return jsonify(result)


@revert_order_api.route("/revertorder/getrevertorderreason", methods=["GET"])
def get_revert_order_reason():
    order_id = request.args.get("orderId")
    flow = request.args.get("flow")
    if flow == "1":
        flow_list = FIRST_LOGISTICS_FLOW
    elif flow == "2":
        flow_list = SECOND_LOGISTICS_FLOW
    elif flow == "3":
        flow_list = CRAFT_SHEET_FLOW
    order_shoe_status = (
        db.session.query(Order, OrderShoe, OrderShoeStatus)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(
            Order.order_id == order_id, OrderShoeStatus.current_status.in_(flow_list)
        )
        .first()
    )

    result = []
    for status, reason in STATUS_REVERT_DICT.items():
        order_shoe_status_reference = OrderShoeStatusReference.query.filter_by(
            status_id=status
        ).first()
        # if status in flow_list and not current status and index before current_status
        if (
            int(status) in flow_list
            and int(status) != order_shoe_status[2].current_status
            and flow_list.index(int(status))
            < flow_list.index(order_shoe_status[2].current_status)
        ):
            result.append(
                {
                    "statusName": order_shoe_status_reference.status_name,
                    "status": status,
                    "reason": reason,
                }
            )
    return jsonify(result)


@revert_order_api.route("/revertorder/getrevertorderreasonfororder", methods=["GET"])
def get_revert_order_reason_for_order():
    order_id = request.args.get("orderId")
    flow = request.args.get("flow")
    if flow == "1":
        flow_list = ORDER_ISSUE_FLOW
    order_status = (
        db.session.query(Order, OrderStatus)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .filter(
            Order.order_id == order_id, OrderStatus.order_current_status.in_(flow_list)
        )
        .first()
    )

    result = []
    for status, reason in ORDER_STATUS_REVERT_DICT.items():
        order_status_reference = OrderStatusReference.query.filter_by(
            order_status_id=status
        ).first()
        # if status in flow_list and not current status and index before current_status
        if (
            int(status) in flow_list
            and int(status) != order_status[1].order_current_status
            and flow_list.index(int(status))
            < flow_list.index(order_status[1].order_current_status)
        ):
            result.append(
                {
                    "statusName": order_status_reference.order_status_name,
                    "status": status,
                    "reason": reason,
                }
            )

    return jsonify(result)


@revert_order_api.route("/revertorder/revertordersavefororder", methods=["POST"])
def revert_order_save_for_order():
    order_id = request.json.get("orderId")
    flow = request.json.get("flow")
    revert_to_status = int(request.json.get("revertToStatus"))
    revert_reason = request.json.get("revertReason")
    revert_detail = request.json.get("revertDetail")
    is_need_middle_process = request.json.get("isNeedMiddleProcess")
    revert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if flow == 1:
        flow_list = ORDER_ISSUE_FLOW
    order_current_status_db = (
        db.session.query(Order, OrderStatus)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .filter(
            Order.order_id == order_id, OrderStatus.order_current_status.in_(flow_list)
        )
        .first()
    )
    order_current_status = order_current_status_db[1].order_current_status
    middle_process_list = []
    if is_need_middle_process == "1":
        middle_process_list = flow_list[
            flow_list.index(revert_to_status) : flow_list.index(order_current_status)
        ]
    elif is_need_middle_process == "0":
        middle_process_list = [revert_to_status]
    # use status(value) to get the department (key), and use DEPARTMENT_DICT to get the department name
    revert_depart = DEPARTMENT_DICT.get(
        next(
            (
                key
                for key, value in DEPARTMENT_ORDER_STATUS_DICT.items()
                if str(revert_to_status) in value
            ),
            None,
        ),
        "Unknown Department",
    )
    initialing_department = DEPARTMENT_DICT.get(
        next(
            (
                key
                for key, value in DEPARTMENT_ORDER_STATUS_DICT.items()
                if str(order_current_status) in value
            ),
            None,
        ),
        "Unknown Department",
    )
    revert_dict = {
        "source_status": order_current_status,
        "desti_status": revert_to_status,
        "revert_time": revert_time,
        "revert_depart": initialing_department,
        "revert_reason": revert_reason,
        "revert_detail": revert_detail,
        "middle_process": middle_process_list,
    }
    order_current_status_db[1].order_current_status = revert_to_status
    if flow == 1:
        order_current_status_db[1].order_status_value = 1
    db.session.flush()
    revert_event = RevertEvent(
        order_id=order_id,
        revert_reason=revert_reason,
        responsible_department=revert_depart,
        initialing_department=initialing_department,
        event_time=revert_time,
    )
    db.session.add(revert_event)
    db.session.flush()
    db.session.commit()

    return jsonify({"message": "success"})


@revert_order_api.route("/revertorder/revertordersave", methods=["POST"])
def revert_order_save():
    order_id = request.json.get("orderId")
    flow = request.json.get("flow")
    revert_to_status = int(request.json.get("revertToStatus"))
    revert_reason = request.json.get("revertReason")
    revert_detail = request.json.get("revertDetail")
    is_need_middle_process = request.json.get("isNeedMiddleProcess")
    revert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if flow == 1:
        flow_list = FIRST_LOGISTICS_FLOW
    elif flow == 2:
        flow_list = SECOND_LOGISTICS_FLOW
    elif flow == 3:
        flow_list = CRAFT_SHEET_FLOW
    order_current_status_db = (
        db.session.query(Order, OrderShoe, OrderShoeStatus)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(
            Order.order_id == order_id, OrderShoeStatus.current_status.in_(flow_list)
        )
        .first()
    )
    order_current_status = order_current_status_db.OrderShoeStatus.current_status
    middle_process_list = []
    if is_need_middle_process == "1":
        # ger middle process list from the flow (between revert_to_status and order_current_status)
        middle_process_list = flow_list[
            flow_list.index(revert_to_status) : flow_list.index(order_current_status)
        ]
    elif is_need_middle_process == "0":
        middle_process_list = [revert_to_status]
    # use status(value) to get the department (key), and use DEPARTMENT_DICT to get the department name
    revert_depart = DEPARTMENT_DICT.get(
        next(
            (
                key
                for key, value in DEPARTMENT_STATUS_DICT.items()
                if str(revert_to_status) in value
            ),
            None,
        ),
        "Unknown Department",
    )
    initialing_department = DEPARTMENT_DICT.get(
        next(
            (
                key
                for key, value in DEPARTMENT_STATUS_DICT.items()
                if str(order_current_status) in value
            ),
            None,
        ),
        "Unknown Department",
    )
    revert_dict = {
        "source_status": order_current_status,
        "desti_status": revert_to_status,
        "revert_time": revert_time,
        "revert_depart": initialing_department,
        "revert_reason": revert_reason,
        "revert_detail": revert_detail,
        "middle_process": middle_process_list,
    }
    order_current_status_db.OrderShoeStatus.revert_info = json.dumps(revert_dict)
    order_current_status_db.OrderShoeStatus.current_status = revert_to_status
    db.session.flush()
    revert_event = RevertEvent(
        order_id=order_id,
        revert_reason=revert_reason,
        responsible_department=revert_depart,
        initialing_department=initialing_department,
        event_time=revert_time,
    )
    db.session.add(revert_event)
    db.session.flush()
    db.session.commit()
    return jsonify({"message": "success"})


@revert_order_api.route("/revertorder/processrevertorder", methods=["POST"])
def process_revert_order():
    order_id = request.json.get("orderId")
    order_shoe_status = (
        db.session.query(Order, OrderShoe, OrderShoeStatus)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(Order.order_id == order_id, OrderShoeStatus.revert_info.isnot(None))
        .first()[2]
    )
    print(order_shoe_status)
    revert_info_dict = json.loads(order_shoe_status.revert_info)
    new_middle_process = revert_info_dict["middle_process"]
    source_status = revert_info_dict["source_status"]
    new_middle_process.pop(0)
    if len(new_middle_process) == 0:
        order_shoe_status.revert_info = null()
        order_shoe_status.current_status = source_status
        db.session.flush()
        db.session.commit()
        return jsonify({"message": "success"})
    new_revert_info_dict = {
        "source_status": revert_info_dict["source_status"],
        "desti_status": revert_info_dict["desti_status"],
        "revert_time": revert_info_dict["revert_time"],
        "revert_depart": revert_info_dict["revert_depart"],
        "revert_reason": revert_info_dict["revert_reason"],
        "revert_detail": revert_info_dict["revert_detail"],
        "middle_process": new_middle_process,
    }
    order_shoe_status.revert_info = json.dumps(new_revert_info_dict)
    order_shoe_status.current_status = new_middle_process[0]
    db.session.flush()
    db.session.commit()
    return jsonify({"message": "success"})

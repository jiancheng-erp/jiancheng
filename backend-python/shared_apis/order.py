from numpy import character
import constants
import time
from app_config import db
from flask import Blueprint, jsonify, request, send_file, current_app
from sqlalchemy import func, or_, case
from api_utility import to_snake, to_camel, estimate_status_converter
from login.login import current_user, current_user_info
import math
import os
import shutil
from datetime import datetime, timedelta, date
from decimal import Decimal, InvalidOperation
from event_processor import EventProcessor

from constants import IN_PRODUCTION_ORDER_NUMBER, SHOESIZERANGE, ORDER_FINISH_SYMBOL
from shared_apis.department import get_business_department_ids
from general_document.order_export import (
    generate_excel_file,
    generate_amount_excel_file,
)
from general_document.production_order_export import (
    generate_production_excel_file,
    generate_production_amount_excel_file,
)
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from models import *
from shared_apis import customer
from logger import logger
order_bp = Blueprint("order_bp", __name__)
# 订单初始状态
ORDER_CREATION_STATUS = 6
# 订单开发部状态
ORDER_IN_PROD_STATUS = 9
# 包装信息状态
PACKAGING_SPECS_UPLOADED = "2"
# 业务部经理角色码
BUSINESS_MANAGER_ROLE = 4
ORDER_STATUS_MANAGER_DISPLAY_MSG = {
    0:"文员未提交",
    1:"待审批"
}
# 业务部职员角色码
BUSINESS_CLERK_ROLE = 21
ORDER_STATUS_CLERK_DISPLAY_MSG = {
    0:"未提交",
    1:"已提交"
}
# 技术部文员
TECHNICAL_CLERK_ROLE = 15

# 鞋型初始状态（投产指令单创建）
DEV_ORDER_SHOE_STATUS = 0
# 开发部经理角色码
DEV_DEPARTMENT_MANAGER = 7
# 开发一部部门码
DEV_DEPARTMENT_1 = 11
# 开发二部部门码
DEV_DEPARTMENT_2 = 14
# 开发三部部门码
DEV_DEPARTMENT_3 = 15
# 开发五部部门码
DEV_DEPARTMENT_5 = 16

COLOR_CARD_PENDING = "0"
COLOR_CARD_CONFIRMED = "1"


# 面料计算，一次bom填写
USAGE_CALCULATION_ORDER_SHOE_STATUS = 4
# 面料计算文员角色码
USAGE_CALCULATION_ROLE = 18
# 面料计算部门码

# 工艺单
CRAFT_SHEET_ORDER_SHOE_STATUS = 9
# 面料计算文员角色码
TECH_DEPARTMENT_MANAGER = 5


PACKAGING_DOC_CANDIDATES = ["包装资料.xlsx", "包装资料.xls", "包装资料.pdf"]


def _locate_packaging_doc(order_rid: str):
    if not order_rid:
        return None
    base_dirs = [
        os.path.join(FILE_STORAGE_PATH, "业务部文件", order_rid),
        os.path.join(FILE_STORAGE_PATH, order_rid),  # legacy fallback
    ]
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            continue
        for name in PACKAGING_DOC_CANDIDATES:
            candidate_path = os.path.join(base_dir, name)
            if os.path.exists(candidate_path):
                return {
                    "path": candidate_path,
                    "file_name": name,
                    "ext": os.path.splitext(candidate_path)[1].lower(),
                }
    logger.debug(
        "packaging doc not found for order_rid=%r, checked dirs=%s",
        order_rid,
        base_dirs,
    )
    return None


@order_bp.route("/ordershoe/getordershoebyorder", methods=["GET"])
def get_order_shoe_by_order():
    order_id = request.args.get("orderid")
    entities = (
        db.session.query(OrderShoe, Shoe)
        .filter(OrderShoe.order_id == order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .all()
    )
    return

@order_bp.route("/order/getdevordershoebystatusfordoc", methods=["GET"])
def get_dev_orders_for_doc():
    _, staff, department = current_user_info()

    shoe_department = department.department_name
    status_val = DEV_ORDER_SHOE_STATUS
    t_s = time.time()
    status_val = request.args.get("ordershoestatus")
    # order_shoe_by_department_table = (
    #     db.session.query(
    #         OrderShoe.shoe_id,
    #         OrderShoe.order_shoe_id,
    #         OrderShoe.order_id,
    #         Shoe,
    #     )
    #     .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
    #     .filter(Shoe.shoe_department_id == shoe_department)
    #     .first()
    # )
    if staff.staff_id == TECHNICAL_CLERK_ROLE:
        entities = (
            db.session.query(
                Order,
                Customer,
                Shoe,
                OrderShoeStatus.current_status_value,
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(OrderStatus, OrderStatus.order_id == Order.order_id)
            .join(
                OrderShoeStatus,
                OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(Customer, Order.customer_id == Customer.customer_id)
            .filter(OrderStatus.order_current_status == ORDER_IN_PROD_STATUS)
            .filter(OrderShoeStatus.current_status == status_val)
            .filter(OrderShoeStatus.revert_info.is_(None))
            .order_by(Order.start_date.desc())
            .all()
        )
    else:
        entities = (
            db.session.query(
                Order,
                Customer,
                Shoe,
                OrderShoeStatus.current_status_value,
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(OrderStatus, OrderStatus.order_id == Order.order_id)
            .join(
                OrderShoeStatus,
                OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(Customer, Order.customer_id == Customer.customer_id)
            .filter(OrderStatus.order_current_status == ORDER_IN_PROD_STATUS)
            .filter(OrderShoeStatus.current_status == status_val)
            .filter(Order.order_paper_color_document_status == "0")
            .filter(Order.order_paper_production_instruction_status == "0")
            .filter(OrderShoeStatus.revert_info.is_(None))
            .filter(Shoe.shoe_department_id == shoe_department)
            .order_by(Order.start_date.desc())
            .all()
        )

    pending_orders, in_progress_orders = [], []
    for entity in entities:
        order, customer, shoe, status_value = entity
        formatted_start_date = order.start_date.strftime("%Y-%m-%d")
        formatted_deadline_date = order.end_date.strftime("%Y-%m-%d")
        response_obj = {
            "orderId": order.order_id,
            "orderRid": order.order_rid,
            "customerName": customer.customer_name,
            "shoeRId": shoe.shoe_rid,
            "statusValue": status_value,
            "createTime": formatted_start_date,
            "deadlineTime": formatted_deadline_date,
        }
        if status_value == 0:
            pending_orders.append(response_obj)
        elif status_value == 1:
            in_progress_orders.append(response_obj)

    result = {"pendingOrders": pending_orders, "inProgressOrders": in_progress_orders}
    t_e = time.time()
    logger.debug("Time Taken is ")
    logger.debug(t_e - t_s)
    return result


@order_bp.route("/order/getdevordershoebystatus", methods=["GET"])
def get_dev_orders():
    # TODO hard code deparment name, should be department id
    _, staff, department = current_user_info()

    shoe_department = department.department_name
    logger.debug("department" + shoe_department)
    status_val = DEV_ORDER_SHOE_STATUS
    t_s = time.time()
    status_val = request.args.get("ordershoestatus")
    # order_shoe_by_department_table = (
    #     db.session.query(
    #         OrderShoe.shoe_id,
    #         OrderShoe.order_shoe_id,
    #         OrderShoe.order_id,
    #         Shoe,
    #     )
    #     .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
    #     .filter(Shoe.shoe_department_id == shoe_department)
    #     .first()
    # )
    if staff.staff_id == TECHNICAL_CLERK_ROLE:
        entities = (
            db.session.query(
                Order,
                Customer,
                Shoe,
                OrderShoeStatus.current_status_value,
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(OrderStatus, OrderStatus.order_id == Order.order_id)
            .join(
                OrderShoeStatus,
                OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(Customer, Order.customer_id == Customer.customer_id)
            .filter(OrderStatus.order_current_status == ORDER_IN_PROD_STATUS)
            .filter(OrderShoeStatus.current_status == status_val)
            .filter(OrderShoeStatus.revert_info.is_(None))
            .order_by(Order.start_date.desc())
            .all()
        )
    else:
        entities = (
            db.session.query(
                Order,
                Customer,
                Shoe,
                OrderShoeStatus.current_status_value,
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .join(OrderStatus, OrderStatus.order_id == Order.order_id)
            .join(
                OrderShoeStatus,
                OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(Customer, Order.customer_id == Customer.customer_id)
            .filter(OrderStatus.order_current_status == ORDER_IN_PROD_STATUS)
            .filter(OrderShoeStatus.current_status == status_val)
            .filter(OrderShoeStatus.revert_info.is_(None))
            .filter(Shoe.shoe_department_id == shoe_department)
            .order_by(Order.start_date.desc())
            .all()
        )

    pending_orders, in_progress_orders = [], []
    for entity in entities:
        order, customer, shoe, status_value = entity
        formatted_start_date = order.start_date.strftime("%Y-%m-%d")
        formatted_deadline_date = order.end_date.strftime("%Y-%m-%d")
        response_obj = {
            "orderId": order.order_id,
            "orderRid": order.order_rid,
            "customerName": customer.customer_name,
            "shoeRId": shoe.shoe_rid,
            "statusValue": status_value,
            "createTime": formatted_start_date,
            "deadlineTime": formatted_deadline_date,
        }
        if status_value == 0:
            pending_orders.append(response_obj)
        elif status_value == 1:
            in_progress_orders.append(response_obj)

    result = {"pendingOrders": pending_orders, "inProgressOrders": in_progress_orders}
    t_e = time.time()
    logger.debug("Time Taken is ")
    logger.debug(t_e - t_s)
    return result


@order_bp.route("/order/colorcard/orders", methods=["GET"])
def list_color_card_orders():
    character, staff, department = current_user_info()
    if character.character_id != DEV_DEPARTMENT_MANAGER:
        return jsonify({"message": "仅开发部可操作"}), 403

    shoe_department = department.department_name
    status_filter = request.args.get("status")
    keyword = (request.args.get("keyword") or "").strip()

    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.args.get("pageSize", 20))
    except (TypeError, ValueError):
        page_size = 20
    page = page if page > 0 else 1
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    query = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            Customer.customer_name,
            func.group_concat(func.distinct(Shoe.shoe_rid)).label("shoe_rids"),
            Order.start_date,
            Order.end_date,
            Order.color_card_confirm_status,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .filter(OrderStatus.order_current_status == ORDER_IN_PROD_STATUS)
        .filter(Shoe.shoe_department_id == shoe_department)
        .group_by(
            Order.order_id,
            Order.order_rid,
            Customer.customer_name,
            Order.start_date,
            Order.end_date,
            Order.color_card_confirm_status,
        )
    )

    if status_filter in (COLOR_CARD_PENDING, COLOR_CARD_CONFIRMED):
        query = query.filter(Order.color_card_confirm_status == status_filter)

    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Order.order_rid.like(like_pattern),
                Customer.customer_name.like(like_pattern),
                Shoe.shoe_rid.like(like_pattern),
            )
        )

    query = query.order_by(Order.start_date.desc())
    base_query = query.order_by(None)
    total = (
        db.session.query(func.count())
        .select_from(base_query.subquery())
        .scalar()
        or 0
    )

    rows = (
        base_query.order_by(Order.start_date.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    payload = []
    for row in rows:
        payload.append(
            {
                "orderId": row.order_id,
                "orderRid": row.order_rid,
                "customerName": row.customer_name,
                "shoeRids": row.shoe_rids.split(",") if row.shoe_rids else [],
                "createTime": row.start_date.strftime("%Y-%m-%d") if row.start_date else None,
                "deadlineTime": row.end_date.strftime("%Y-%m-%d") if row.end_date else None,
                "colorCardStatus": row.color_card_confirm_status,
            }
        )

    return jsonify(
        {
            "orders": payload,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
    )


@order_bp.route("/order/colorcard/confirm", methods=["POST"])
def confirm_color_card():
    character, staff, department = current_user_info()
    if character.character_id != DEV_DEPARTMENT_MANAGER:
        return jsonify({"message": "仅开发部可操作"}), 403

    data = request.get_json() or {}
    order_id = data.get("orderId")
    if not order_id:
        return jsonify({"message": "缺少订单ID"}), 400

    order_entity = db.session.query(Order).filter(Order.order_id == order_id).first()
    if not order_entity:
        return jsonify({"message": "订单不存在"}), 404

    ownership = (
        db.session.query(Order.order_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_id == order_id)
        .filter(Shoe.shoe_department_id == department.department_name)
        .first()
    )
    if not ownership:
        return jsonify({"message": "无权确认该订单"}), 403

    if order_entity.color_card_confirm_status == COLOR_CARD_CONFIRMED:
        return jsonify({"message": "色卡已确认"})

    order_entity.color_card_confirm_status = COLOR_CARD_CONFIRMED
    db.session.commit()
    return jsonify({"message": "色卡确认完成"})


@order_bp.route("/order/colorcard/batch-confirm", methods=["POST"])
def batch_confirm_color_card():
    character, staff, department = current_user_info()
    if character.character_id != DEV_DEPARTMENT_MANAGER:
        return jsonify({"message": "仅开发部可操作"}), 403

    data = request.get_json() or {}
    order_ids = data.get("orderIds")
    if not isinstance(order_ids, list) or not order_ids:
        return jsonify({"message": "请提供订单ID列表"}), 400

    try:
        normalized_ids = {int(order_id) for order_id in order_ids}
    except (TypeError, ValueError):
        return jsonify({"message": "存在无效的订单ID"}), 400

    if not normalized_ids:
        return jsonify({"message": "订单ID列表为空"}), 400

    ownership_rows = (
        db.session.query(Order.order_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_id.in_(normalized_ids))
        .filter(Shoe.shoe_department_id == department.department_name)
        .distinct()
        .all()
    )

    owned_ids = {row.order_id for row in ownership_rows}
    unauthorized_ids = list(normalized_ids - owned_ids)

    if not owned_ids:
        return jsonify({"message": "所选订单无可操作权限"}), 403

    orders = (
        db.session.query(Order)
        .filter(Order.order_id.in_(owned_ids))
        .all()
    )

    updated = 0
    already_confirmed = []
    for order in orders:
        if order.color_card_confirm_status == COLOR_CARD_CONFIRMED:
            already_confirmed.append(order.order_id)
            continue
        order.color_card_confirm_status = COLOR_CARD_CONFIRMED
        updated += 1

    if updated:
        db.session.commit()

    message_parts = [f"成功确认 {updated} 单"]
    if already_confirmed:
        message_parts.append(f"{len(already_confirmed)} 单已确认，跳过")
    if unauthorized_ids:
        message_parts.append(f"{len(unauthorized_ids)} 单无权限")

    return jsonify(
        {
            "message": "，".join(message_parts),
            "updated": updated,
            "alreadyConfirmed": already_confirmed,
            "unauthorized": unauthorized_ids,
        }
    )


@order_bp.route("/order/getprodordershoebystatus", methods=["GET"])
def get_orders_by_status():
    t_s = time.time()
    logger.debug("ORDERSHOESTATUS GET REQUEST WITH STATUS OF")
    status_val = request.args.get("ordershoestatus")
    entities = (
        db.session.query(
            Order,
            Customer,
            Shoe,
            OrderShoeStatus.current_status_value,
        )
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderStatus.order_current_status == ORDER_IN_PROD_STATUS)
        .filter(OrderShoeStatus.current_status == status_val)
        .filter(OrderShoeStatus.revert_info.is_(None))
        .order_by(Order.start_date.desc())
        .all()
    )
    pending_orders, in_progress_orders = [], []
    for entity in entities:
        order, customer, shoe, status_value = entity
        formatted_start_date = order.start_date.strftime("%Y-%m-%d")
        formatted_deadline_date = order.end_date.strftime("%Y-%m-%d")
        response_obj = {
            "orderId": order.order_id,
            "orderRid": order.order_rid,
            "customerName": customer.customer_name,
            "shoeRId": shoe.shoe_rid,
            "statusValue": status_value,
            "createTime": formatted_start_date,
            "deadlineTime": formatted_deadline_date,
        }
        if status_value == 0:
            pending_orders.append(response_obj)
        elif status_value == 1:
            in_progress_orders.append(response_obj)

    result = {"pendingOrders": pending_orders, "inProgressOrders": in_progress_orders}
    t_e = time.time()
    logger.debug("Time Taken is ")
    logger.debug(t_e - t_s)
    return result


@order_bp.route("/order/getordersinproduction", methods=["GET"])
def get_orders_in_production():
    status_val = request.args.get("ordershoestatus")
    response = (
        db.session.query(
            Order,
            func.max(OrderShoeStatus.current_status_value).label("status_value"),
            Customer,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .filter(
            OrderShoeStatus.current_status >= status_val,
            OrderShoeStatus.current_status < 42,
        )
        .group_by(Order.order_id)
        .all()
    )

    new_orders, progress_orders = [], []
    for row in response:
        order, status_val, customer = row
        formatted_date = order.start_date.strftime("%Y-%m-%d")
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "createTime": formatted_date,
            "customerName": customer.customer_name,
        }
        if status_val == 0:
            new_orders.append(obj)
        elif status_val == 1:
            progress_orders.append(obj)
    result = {"newOrders": new_orders, "progressOrders": progress_orders}
    return result


@order_bp.route("/order/onmount", methods=["GET"])
def get_on_mount():
    return current_user()


@order_bp.route("/order/getorderInfo", methods=["GET"])
def get_order_info():
    order_id = request.args.get("orderid")
    current_status = request.args.get("status", None)
    entities = (
        db.session.query(Order, Customer, OrderStatus)
        .filter(Order.order_id == order_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
        .first()
    )
    formatted_start_date = entities.Order.start_date.strftime("%Y-%m-%d")
    formatted_end_date = entities.Order.end_date.strftime("%Y-%m-%d")
    status_mapping = {
        "0":  {"operation_id": 17, "previous_status": "订单总经理确认", "current_status": "投产指令单填写"},
        "6":  {"operation_id": 47, "previous_status": "一次用量填写", "current_status": "一次采购订单填写"},
        "4":  {"operation_id": 39, "previous_status": "投产指令单填写", "current_status": "一次用量填写"},
        "7":  {"operation_id": 47, "previous_status": "一次用量填写", "current_status": "二次采购订单填写"},
        "9":  {"operation_id": 39, "previous_status": "投产指令单填写", "current_status": "工艺单填写"},
        "11": {"operation_id": 57, "previous_status": "工艺单填写", "current_status": "二次用量填写"},
        "13": {"operation_id": 61, "previous_status": "二次用量填写", "current_status": "二次用量(BOM)审批"},
    }

    if current_status is not None and current_status in status_mapping:
        mapping = status_mapping[current_status]
        event = db.session.query(Event).filter(
            Event.event_order_id == entities.Order.order_id,
            Event.operation_id == mapping["operation_id"]
        ).first()

        previous_status_time = (
            event.handle_time.strftime("%Y-%m-%d %H:%M:%S")
            if event else "N/A"
        )
        previous_status = mapping["previous_status"]
        current_shoe_status = mapping["current_status"]
        #计算迟滞时间 = 当前时间-处理时间，转换为合适表达方式(小时/天)
        delay_time = datetime.now() - event.handle_time if event else None
        if delay_time:
            if delay_time.days > 0:
                delay_time_str = f"{delay_time.days}天"
            else:
                delay_time_str = f"{delay_time.seconds // 3600}小时"
    result = {
        "orderId": entities.Order.order_rid,
        "orderDBId": entities.Order.order_id,
        "customerName": entities.Customer.customer_name,
        "customerBrand": entities.Customer.customer_brand,
        "createTime": formatted_start_date,
        "deadlineTime": formatted_end_date,
        "status": (
            entities.OrderStatus.order_current_status if entities.OrderStatus else "N/A"
        ),
        "lastStatus": (
            entities.Order.last_status if entities.Order.last_status else "N/A"
            
        ),
        "cuttingModelStatus": (
            entities.Order.cutting_model_status if entities.Order.cutting_model_status else "N/A"
        ),
        "packagingStatus": (
            entities.Order.packaging_status if entities.Order.packaging_status else "N/A"
        ),
        "previousOrderShoeStatus": previous_status if current_status is not None else "N/A",
        "previousOrderShoeStatusTime": previous_status_time if current_status is not None else "N/A",
        "currentOrderShoeStatus": current_shoe_status if current_status is not None else "N/A",
        "delayTime": delay_time_str if current_status is not None and delay_time else "N/A",
    }
    return jsonify(result)


@order_bp.route("/order/getbusinessorderinfo", methods=["GET"])
def get_order_info_business():
    result = {}
    order_id = request.args.get("orderid")
    character, _, _ = current_user_info()
    hide_price_detail = False
    if character is not None:
        hide_price_detail = character.character_id == BUSINESS_CLERK_ROLE
    entity = (
        db.session.query(
            Order,
            Customer,
            OrderStatus,
            BatchInfoType,
            Staff,
        )
        .filter(Order.order_id == order_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(
            BatchInfoType, Order.batch_info_type_id == BatchInfoType.batch_info_type_id
        )
        .join(Staff, Order.salesman_id == Staff.staff_id)
        .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
        .first()
    )
    formatted_start_date = entity.Order.start_date.strftime("%Y-%m-%d")
    formatted_end_date = entity.Order.end_date.strftime("%Y-%m-%d")

    order_shoe_entities = (
        db.session.query(Order, OrderShoe, Shoe)
        .filter(Order.order_id == order_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        # .join(Color, Color.shoe_id )
        .all()
    )
    batch_info_type_response = {}
    batch_info_type_attrs = entity.BatchInfoType.__table__.columns.keys()
    batch_info_type_attrs.remove("batch_info_type_usage")
    for attr in batch_info_type_attrs:
        batch_info_type_response[to_camel(attr)] = getattr(entity.BatchInfoType, attr)
    result = {
        "orderId": entity.Order.order_id,
        "orderRid": entity.Order.order_rid,
        "orderCid": entity.Order.order_cid,
        "orderType": entity.Order.order_type,
        "batchInfoTypeName": entity.BatchInfoType.batch_info_type_name,
        "batchInfoType": batch_info_type_response,
        "orderStaffName": entity.Staff.staff_name,
        "dateInfo": formatted_start_date + " —— " + formatted_end_date,
        "startDate": formatted_start_date,
        "endDate": formatted_end_date,
        "customerName": entity.Customer.customer_name,
        "customerBrand": entity.Customer.customer_brand,
        "customerInfo": "客人编号:"
        + entity.Customer.customer_name
        + " 客人商标: "
        + entity.Customer.customer_brand,
        "orderStatus": (
            entity.OrderStatus.order_current_status if entity.OrderStatus else "N/A"
        ),
        "orderStatusVal": (
            entity.OrderStatus.order_status_value if entity.OrderStatus else "N/A"
        ),
        "orderShoeAllData": [],
    }
    # Query the latest revert event from 总经理, only show when order is still at status 6 (not yet re-submitted)
    order_current_status = entity.OrderStatus.order_current_status if entity.OrderStatus else None
    if order_current_status == ORDER_CREATION_STATUS:
        latest_revert_event = (
            db.session.query(RevertEvent)
            .filter(
                RevertEvent.order_id == order_id,
                RevertEvent.initialing_department == "总经理",
            )
            .order_by(RevertEvent.event_time.desc())
            .first()
        )
        if latest_revert_event:
            result["revertInfo"] = {
                "revertReason": latest_revert_event.revert_reason,
                "revertDetail": latest_revert_event.revert_detail,
                "revertTime": latest_revert_event.event_time.strftime("%Y-%m-%d %H:%M:%S") if latest_revert_event.event_time else "",
                "initialingDepartment": latest_revert_event.initialing_department,
            }
    if entity.Order.production_list_upload_status == "2":
        result["wrapRequirementUploadStatus"] = "已上传包装文件"
    else:
        result["wrapRequirementUploadStatus"] = "未上传包装文件"
    packaging_doc = _locate_packaging_doc(entity.Order.order_rid)
    result["packagingDoc"] = {
        "exists": packaging_doc is not None,
        "fileName": packaging_doc["file_name"] if packaging_doc else None,
        "ext": packaging_doc["ext"] if packaging_doc else None,
    }
    order_shoe_ids = []
    for order_shoe in order_shoe_entities:
        response = {}
        response["orderShoeId"] = order_shoe.OrderShoe.order_shoe_id
        response["shoeId"] = order_shoe.Shoe.shoe_id
        response["shoeRid"] = order_shoe.Shoe.shoe_rid
        response["shoeCid"] = order_shoe.OrderShoe.customer_product_name
        response["orderShoeStatusList"] = []
        response["orderShoeRemarkRep"] = (
            "工艺备注:"
            + order_shoe.OrderShoe.business_technical_remark
            + " \n"
            + "材料备注:"
            + order_shoe.OrderShoe.business_material_remark
        )
        response["orderShoeTechnicalRemark"] = (
            order_shoe.OrderShoe.business_technical_remark
        )
        response["orderShoeMaterialRemark"] = (
            order_shoe.OrderShoe.business_material_remark
        )
        response["orderShoeRemarkExist"] = not (
            order_shoe.OrderShoe.business_technical_remark == ""
            and order_shoe.OrderShoe.business_material_remark == ""
        )
        # response["orderShoeStatus"] = order_shoe.OrderShoeStatus.current_status
        # response["orderShoeStatusVal"] = order_shoe.OrderShoeStatus.current_status_value
        result["orderShoeAllData"].append(response)
        order_shoe_id = order_shoe.OrderShoe.order_shoe_id
        if order_shoe_id not in order_shoe_ids:
            order_shoe_ids.append(order_shoe_id)

        # order_shoe_status_entities = (db.session.query(OrderShoe, OrderShoeStatus, OrderShoeStatusReference)
        # .filter(OrderShoe.order_shoe_id == order_shoe_id)
        # .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        # .join(OrderShoeStatusReference, OrderShoeStatus.current_status == OrderShoeStatusReference.status_id)
        # .all())
        # logger.debug(order_shoe_status_entities)
        # logger.debug(order_shoe_id)

    order_shoe_id_to_status = {order_shoe_id: "" for order_shoe_id in order_shoe_ids}
    order_shoe_id_to_order_shoe_types = {
        order_shoe_id: [] for order_shoe_id in order_shoe_ids
    }
    for order_shoe_id in order_shoe_ids:
        order_shoe_status_entities = (
            db.session.query(OrderShoeStatus, OrderShoeStatusReference)
            .filter(OrderShoeStatus.order_shoe_id == order_shoe_id)
            .join(
                OrderShoeStatusReference,
                OrderShoeStatus.current_status == OrderShoeStatusReference.status_id,
            )
            .all()
        )
        for entity in order_shoe_status_entities:
            status_message = entity.OrderShoeStatusReference.status_name
            order_shoe_id_to_status[order_shoe_id] += status_message

        order_shoe_type_entities = (
            db.session.query(OrderShoeType, Color, ShoeType)
            .filter(OrderShoeType.order_shoe_id == order_shoe_id)
            .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
            .join(Color, Color.color_id == ShoeType.color_id)
        ).all()

        order_shoe_type_ids = [
            entity.OrderShoeType.order_shoe_type_id
            for entity in order_shoe_type_entities
        ]

        for entity in order_shoe_type_entities:
            response_order_shoe = {
                "orderShoeTypeId": entity.OrderShoeType.order_shoe_type_id,
                "shoeTypeColorName": entity.Color.color_name,
                "shoeTypeColorId": entity.Color.color_id,
                "customerColorName": entity.OrderShoeType.customer_color_name,
                "shoeTypeImgUrl": IMAGE_STORAGE_PATH + entity.ShoeType.shoe_image_url if entity.ShoeType.shoe_image_url is not None else None,
                "shoeTypeBatchInfoList": [],
            }
            order_shoe_type_unit_price = entity.OrderShoeType.unit_price
            order_shoe_type_currency_type = entity.OrderShoeType.currency_type
            shoe_type_batch_infos = (
                db.session.query(OrderShoeBatchInfo, PackagingInfo)
                .filter(
                    OrderShoeBatchInfo.order_shoe_type_id
                    == entity.OrderShoeType.order_shoe_type_id
                )
                .join(
                    PackagingInfo,
                    OrderShoeBatchInfo.packaging_info_id
                    == PackagingInfo.packaging_info_id,
                )
            ).all()
            total_size_34 = 0
            total_size_35 = 0
            total_size_36 = 0
            total_size_37 = 0
            total_size_38 = 0
            total_size_39 = 0
            total_size_40 = 0
            total_size_41 = 0
            total_size_42 = 0
            total_size_43 = 0
            total_size_44 = 0
            total_size_45 = 0
            total_size_46 = 0
            overall_total = 0
            unit_price = 0
            total_price = 0
            currency_type = ""
            database_attr_list = [
                "packaging_info_name",
                "packaging_info_locale",
                "size_34_ratio",
                "size_35_ratio",
                "size_36_ratio",
                "size_37_ratio",
                "size_38_ratio",
                "size_39_ratio",
                "size_40_ratio",
                "size_41_ratio",
                "size_42_ratio",
                "size_43_ratio",
                "size_44_ratio",
                "size_45_ratio",
                "size_46_ratio",
                "total_quantity_ratio",
            ]
            db_attr_to_froend_key = {}
            for entity in shoe_type_batch_infos:
                total_size_34 += entity.OrderShoeBatchInfo.size_34_amount
                total_size_35 += entity.OrderShoeBatchInfo.size_35_amount
                total_size_36 += entity.OrderShoeBatchInfo.size_36_amount
                total_size_37 += entity.OrderShoeBatchInfo.size_37_amount
                total_size_38 += entity.OrderShoeBatchInfo.size_38_amount
                total_size_39 += entity.OrderShoeBatchInfo.size_39_amount
                total_size_40 += entity.OrderShoeBatchInfo.size_40_amount
                total_size_41 += entity.OrderShoeBatchInfo.size_41_amount
                total_size_42 += entity.OrderShoeBatchInfo.size_42_amount
                total_size_43 += entity.OrderShoeBatchInfo.size_43_amount
                total_size_44 += entity.OrderShoeBatchInfo.size_44_amount
                total_size_45 += entity.OrderShoeBatchInfo.size_45_amount
                total_size_46 += entity.OrderShoeBatchInfo.size_46_amount
                overall_total += entity.OrderShoeBatchInfo.total_amount
                total_price += (
                    entity.OrderShoeBatchInfo.total_amount * order_shoe_type_unit_price
                )
                unit_price = order_shoe_type_unit_price
                currency_type = order_shoe_type_currency_type
                # batchInfoEntity = {}
                # for db_attr in database_attr_list:
                #     logger.debug("getting this db_attr " + db_attr)
                #     parsed_key = "".join(db_attr.rsplit(db_attr))
                #     logger.debug(parsed_key)
                #     batchInfoEntity[parsed_key] = getattr(entity.PackagingInfo, db_attr)
                # response_order_shoe['shoeTypeBatchInfoList'].append(batchInfoEntity)
                temp_obj = {
                    to_camel(db_attr): getattr(entity.PackagingInfo, db_attr)
                    for db_attr in database_attr_list
                }
                # casting decimal to int or float accordingly for frontend
                if entity.OrderShoeBatchInfo.packaging_info_quantity != None:
                    if entity.OrderShoeBatchInfo.packaging_info_quantity == int(entity.OrderShoeBatchInfo.packaging_info_quantity):
                        temp_obj["unitPerRatio"] = int(entity.OrderShoeBatchInfo.packaging_info_quantity)
                    else:
                        temp_obj["unitPerRatio"] = float(entity.OrderShoeBatchInfo.packaging_info_quantity)
                temp_obj['total'] = int(temp_obj['unitPerRatio'] * temp_obj['totalQuantityRatio'])
                # per-size amounts for this batch row (used by the Excel-style layout)
                for i in range(34, 47):
                    temp_obj[f"size{i}Amount"] = getattr(
                        entity.OrderShoeBatchInfo, f"size_{i}_amount"
                    )
                response_order_shoe["shoeTypeBatchInfoList"].append(temp_obj)

            price_filled = (
                order_shoe_type_unit_price is not None
                and float(order_shoe_type_unit_price) > 0
                and order_shoe_type_currency_type is not None
            )

            shoeTypeBatchData = {
                "size34Amount": total_size_34,
                "size35Amount": total_size_35,
                "size36Amount": total_size_36,
                "size37Amount": total_size_37,
                "size38Amount": total_size_38,
                "size39Amount": total_size_39,
                "size40Amount": total_size_40,
                "size41Amount": total_size_41,
                "size42Amount": total_size_42,
                "size43Amount": total_size_43,
                "size44Amount": total_size_44,
                "size45Amount": total_size_45,
                "size46Amount": total_size_46,
                "totalAmount": overall_total,
                "unitPrice": round(float(unit_price), 2),
                "totalPrice": round(float(total_price), 2),
                "currencyType": currency_type,
            }

            if hide_price_detail:
                shoeTypeBatchData["unitPrice"] = None
                shoeTypeBatchData["totalPrice"] = None
                shoeTypeBatchData["currencyType"] = None

            response_order_shoe["priceFilled"] = price_filled
            response_order_shoe["priceMasked"] = hide_price_detail

            response_order_shoe["shoeTypeBatchData"] = shoeTypeBatchData
            order_shoe_id_to_order_shoe_types[order_shoe_id].append(response_order_shoe)
        # for entity in order_shoe_type_entities:
        #     order_shoe_id_to_order_shoe_types[order_shoe_id].append(
        #         {   "orderShoeTypeId":entity.OrderShoeType.order_shoe_type_id,
        #             "shoeTypeColorName":entity.Color.color_name,
        #            "shoeTypeColorId":entity.Color.color_id,
        #            "ShoeTypeImgUrl":entity.ShoeType.shoe_image_url,
        #            "shoeTypeBatchData":shoeTypeBatchData
        #         })

    for order_shoe in result["orderShoeAllData"]:

        order_shoe["currentStatus"] = order_shoe_id_to_status[order_shoe["orderShoeId"]]
        order_shoe["orderShoeTypes"] = order_shoe_id_to_order_shoe_types[
            order_shoe["orderShoeId"]
        ]

    return jsonify(result)


@order_bp.route("/order/getordershoesizetotal", methods=["GET"])
def get_order_shoe_size_total():

    order_id = request.args.get("orderid")
    order_shoe_rid = request.args.get("ordershoeid")
    color = request.args.get("color")
    # Fetch the order_shoe_type_id based on filters
    order_shoe_type_id = (
        db.session.query(Order, OrderShoe, OrderShoeType, Shoe, ShoeType, Color)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(Order.order_rid == order_id)
        .filter(Shoe.shoe_rid == order_shoe_rid)
        .filter(Color.color_name == color)
        .first()
        .OrderShoeType.order_shoe_type_id
    )

    # Fetch all batch info entries for the given order_shoe_type_id
    entities = (
        db.session.query(OrderShoeBatchInfo)
        .filter(OrderShoeBatchInfo.order_shoe_type_id == order_shoe_type_id)
        .all()
    )

    # Initialize accumulators for totals of all sizes
    mapping = {}
    for i in range(34, 47):
        mapping[i] = 0
    overall_total = 0

    # Collect results and accumulate totals
    result = []
    for entity in entities:
        # Accumulate totals for each size and overall
        for i in range(34, 47):
            mapping[i] += getattr(entity, f"size_{i}_amount")
        overall_total += entity.total_amount

    # Append the totals for all sizes and overall to the result
    obj = {}
    for i in range(34, 47):
        obj[f"size{i}Amount"] = mapping[i]
    obj["total"] = overall_total
    result.append(obj)
    # Return the result as JSON
    return jsonify(result)


@order_bp.route("/order/getordershoesizesinfo", methods=["GET"])
def get_order_shoe_sizes_info():
    order_id = request.args.get("orderid")
    order_shoe_id = request.args.get("ordershoeid")
    entities = (
        db.session.query(Order, OrderShoe, Shoe, OrderShoeBatchInfo, Color)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(Color, Color.color_id == OrderShoeBatchInfo.color_id)
        .filter(Order.order_rid == order_id)
        .filter(Shoe.shoe_rid == order_shoe_id)
        .all()
    )

    # Dictionary to accumulate total amounts by color
    color_totals = {}

    # First loop to accumulate total amounts for each color
    for entity in entities:
        order, order_shoe, shoe, order_shoe_batch_info, color = entity
        if color.color_name not in color_totals:
            color_totals[color.color_name] = 0
        color_totals[color.color_name] += order_shoe_batch_info.total_amount

    # Second loop to build the result list and include the color totals
    result = []
    for entity in entities:
        order, order_shoe, shoe, order_shoe_batch_info, color = entity
        result.append(
            {
                "size": order_shoe_batch_info.name,
                "35": order_shoe_batch_info.size_35_amount,
                "36": order_shoe_batch_info.size_36_amount,
                "37": order_shoe_batch_info.size_37_amount,
                "38": order_shoe_batch_info.size_38_amount,
                "39": order_shoe_batch_info.size_39_amount,
                "40": order_shoe_batch_info.size_40_amount,
                "41": order_shoe_batch_info.size_41_amount,
                "42": order_shoe_batch_info.size_42_amount,
                "43": order_shoe_batch_info.size_43_amount,
                "44": order_shoe_batch_info.size_44_amount,
                "45": order_shoe_batch_info.size_45_amount,
                "color": color.color_name,
                "pairAmount": order_shoe_batch_info.total_amount,
                "total": color_totals[
                    color.color_name
                ],  # Add total amount for the color
            }
        )

    return jsonify(result)


# 业务经理显示被下发到自己的所有状态的订单
# 如果用户非业务经理,显示当前用户添加的订单
@order_bp.route("/order/getbusinessdisplayorderbyuser", methods=["GET"])
def get_display_orders_manager():
    filter_status = request.args.get("filterStatus")   # "0" or other
    history_status = request.args.get("historyStatus") # None 表示进行中，否则历史
    character, staff, _ = current_user_info()
    current_staff_id = staff.staff_id
    current_user_role = character.character_id

    # --- 基础查询（公共部分） ---
    base_q = (
        db.session.query(
            Order, OrderShoe, Shoe, Customer, OrderStatus, OrderStatusReference
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
        .outerjoin(
            OrderStatusReference,
            OrderStatus.order_current_status == OrderStatusReference.order_status_id,
        )
    )

    # --- 角色与归属维度（经理可切换主管/业务，文员固定业务） ---
    if current_user_role == BUSINESS_MANAGER_ROLE:
        # filterStatus == "0" 看 “主管”，否则看 “业务”
        owner_col = Order.supervisor_id if filter_status == "0" else Order.salesman_id
        msg_mapping = ORDER_STATUS_MANAGER_DISPLAY_MSG
    elif current_user_role == BUSINESS_CLERK_ROLE:
        owner_col = Order.salesman_id
        msg_mapping = ORDER_STATUS_CLERK_DISPLAY_MSG
    else:
        return jsonify({"message": "invalid user role"}), 401

    q = base_q.filter(owner_col == current_staff_id)
    q = q.filter(Order.order_type != "F")

    # --- 订单状态维度（进行中 <16 / 历史 >=16） ---
    is_history = bool(history_status)
    if is_history:
        q = q.filter(OrderStatus.order_current_status >= ORDER_FINISH_SYMBOL)
    else:
        q = q.filter(OrderStatus.order_current_status < ORDER_FINISH_SYMBOL)

    entities = q.order_by(Order.order_rid.asc()).all()

    # --- 部门人员映射（业务部门动态判定：含业务经理/文员角色的部门；避免 KeyError 用 get） ---
    business_department_ids = get_business_department_ids()
    department_staff = (
        db.session.query(Staff)
        .filter(Staff.department_id.in_(business_department_ids))
        .all()
        if business_department_ids
        else []
    )
    id_to_name = {s.staff_id: s.staff_name for s in department_staff}

    # --- 结果组装 ---
    result = []
    for order, order_shoe, shoe, customer, order_status, order_status_reference in entities:
        formatted_start_date = order.start_date.strftime("%Y-%m-%d")
        formatted_end_date = order.end_date.strftime("%Y-%m-%d")

        order_status_message = "N/A"
        if order_status_reference and order_status:
            order_status_message = order_status_reference.order_status_name
            if order_status.order_current_status == ORDER_CREATION_STATUS:
                if order_status.order_status_value is not None:
                    order_status_message += " \n" + msg_mapping[order_status.order_status_value]

        if order.production_list_upload_status != PACKAGING_SPECS_UPLOADED:
            order_status_message += "\n包装材料待上传"

        result.append({
            "orderDbId": order.order_id,
            "orderShoeId": order_shoe.order_shoe_id,
            "customerProductName": order_shoe.customer_product_name,
            "shoeRId": shoe.shoe_rid,
            "orderRid": order.order_rid,
            "orderCid": order.order_cid,
            "orderType": order.order_type,
            "customerName": customer.customer_name,
            "customerBrand": customer.customer_brand,
            "orderStartDate": formatted_start_date,
            "orderEndDate": formatted_end_date,
            "orderStatus": order_status_message,
            "orderStatusVal": order_status.order_current_status if order_status else None,
            "orderSalesman": id_to_name.get(order.salesman_id, ""),
            "orderSupervisor": id_to_name.get(order.supervisor_id, ""),
            "productionStatus": "",
        })

    # —— 补充生产/出库状态 ——
    order_shoe_ids = [r["orderShoeId"] for r in result if r.get("orderShoeId")]
    if order_shoe_ids:
        prod_infos = {
            pi.order_shoe_id: pi
            for pi in db.session.query(OrderShoeProductionInfo)
            .filter(OrderShoeProductionInfo.order_shoe_id.in_(order_shoe_ids))
            .all()
        }
        estimated_info = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.coalesce(
                    func.sum(FinishedShoeStorage.finished_estimated_amount), 0
                ).label("total_estimated"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(OrderShoe.order_shoe_id.in_(order_shoe_ids))
            .group_by(OrderShoe.order_shoe_id)
            .all()
        )
        estimated_map = {
            row.order_shoe_id: int(row.total_estimated)
            for row in estimated_info
        }
        outbound_info = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.coalesce(
                    func.sum(ShoeOutboundRecordDetail.outbound_amount), 0
                ).label("total_outbound"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .join(
                ShoeOutboundRecordDetail,
                ShoeOutboundRecordDetail.finished_shoe_storage_id
                == FinishedShoeStorage.finished_shoe_id,
            )
            .filter(OrderShoe.order_shoe_id.in_(order_shoe_ids))
            .group_by(OrderShoe.order_shoe_id)
            .all()
        )
        outbound_map = {
            row.order_shoe_id: int(row.total_outbound)
            for row in outbound_info
        }
        # 查询是否有入库完成的记录
        inbound_done_info = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.count(FinishedShoeStorage.finished_shoe_id).label("done_count"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(
                OrderShoe.order_shoe_id.in_(order_shoe_ids),
                FinishedShoeStorage.finished_status >= 1,
            )
            .group_by(OrderShoe.order_shoe_id)
            .all()
        )
        inbound_done_map = {
            row.order_shoe_id: int(row.done_count) > 0
            for row in inbound_done_info
        }
        pending_apply_info = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.count(ShoeOutboundApply.apply_id.distinct()).label("pending_count"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .join(
                ShoeOutboundApplyDetail,
                ShoeOutboundApplyDetail.finished_shoe_storage_id
                == FinishedShoeStorage.finished_shoe_id,
            )
            .join(
                ShoeOutboundApply,
                ShoeOutboundApply.apply_id == ShoeOutboundApplyDetail.apply_id,
            )
            .filter(
                OrderShoe.order_shoe_id.in_(order_shoe_ids),
                ShoeOutboundApply.status.in_([1, 3]),
            )
            .group_by(OrderShoe.order_shoe_id)
            .all()
        )
        pending_apply_map = {
            row.order_shoe_id: int(row.pending_count)
            for row in pending_apply_info
        }
        for r in result:
            os_id = r.get("orderShoeId")
            if not os_id:
                continue
            pi = prod_infos.get(os_id)
            if not pi:
                r["productionStatus"] = "未排产"
                continue
            estimated_status = estimate_status_converter(pi)
            if estimated_status != "生产已结束":
                r["productionStatus"] = estimated_status
                continue
            # 生产已结束，检查是否入库完成
            if not inbound_done_map.get(os_id, False):
                r["productionStatus"] = "成型"
                continue
            estimated = estimated_map.get(os_id, 0)
            outbound = outbound_map.get(os_id, 0)
            has_pending_apply = pending_apply_map.get(os_id, 0) > 0
            if outbound > 0 and outbound >= estimated and estimated > 0:
                r["productionStatus"] = f"已全部出库 ({outbound}双)"
            elif outbound > 0:
                r["productionStatus"] = f"部分出库 (已出{outbound}/{estimated}双)"
            elif has_pending_apply:
                r["productionStatus"] = "出库审核中"
            else:
                r["productionStatus"] = "待成品出库"

    # —— 补充退回状态 ——
    order_ids_in_result = list({r["orderDbId"] for r in result if r.get("orderDbId")})
    if order_ids_in_result:
        reverted_order_ids = {
            row.order_id
            for row in db.session.query(RevertEvent.order_id)
            .filter(RevertEvent.order_id.in_(order_ids_in_result))
            .distinct()
            .all()
        }
        for r in result:
            r["hasRevertEvent"] = r["orderDbId"] in reverted_order_ids
    else:
        for r in result:
            r["hasRevertEvent"] = False

    # —— 补充每单总双数 ——
    if order_ids_in_result:
        order_total_pairs_rows = (
            db.session.query(
                Order.order_id,
                func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label("total_pairs"),
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
            )
            .filter(Order.order_id.in_(order_ids_in_result))
            .group_by(Order.order_id)
            .all()
        )
        order_total_pairs_map = {row.order_id: int(row.total_pairs or 0) for row in order_total_pairs_rows}
        for r in result:
            r["orderTotalPairs"] = order_total_pairs_map.get(r["orderDbId"], 0)
    else:
        for r in result:
            r["orderTotalPairs"] = 0

    return jsonify(result)


# 业务经理统计看板：客户/业务员下单情况、手上未完成订单、近半年热门款式
PERIOD_DAYS = {
    "week": 7,
    "month": 30,
    "halfyear": 182,
    "year": 365,
}
HOT_SHOE_PERIOD_DAYS = 182  # 近半年
HOT_SHOE_LIMIT = 20


def _business_dept_staff_ids():
    """业务经理返回本部门人员ID列表；业务文员只返回自己（仅看本人相关）；其余角色返回 None（不限部门）。"""
    character, staff, _ = current_user_info()
    if character.character_id == BUSINESS_MANAGER_ROLE:
        return [
            s.staff_id
            for s in db.session.query(Staff.staff_id)
            .filter(Staff.department_id == staff.department_id)
            .all()
        ]
    if character.character_id == BUSINESS_CLERK_ROLE:
        return [staff.staff_id]
    return None


def _resolve_stat_range(period, start_str, end_str):
    """优先使用自定义起止日期，否则按预设周期计算。返回 (start_date, end_date)。"""
    today = date.today()
    parsed_start = parsed_end = None
    if start_str:
        try:
            parsed_start = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            parsed_start = None
    if end_str:
        try:
            parsed_end = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            parsed_end = None
    if parsed_start and parsed_end:
        if parsed_start > parsed_end:
            parsed_start, parsed_end = parsed_end, parsed_start
        return parsed_start, parsed_end
    if period not in PERIOD_DAYS:
        period = "month"
    return today - timedelta(days=PERIOD_DAYS[period]), today


def _order_pairs_subquery():
    return (
        db.session.query(
            Order.order_id.label("order_id"),
            func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label(
                "total_pairs"
            ),
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .group_by(Order.order_id)
        .subquery()
    )


@order_bp.route("/order/businessstatistics", methods=["GET"])
def get_business_statistics():
    period = request.args.get("period", "month")
    if period not in PERIOD_DAYS:
        period = "month"

    # 归属范围：业务经理看本部门；业务文员仅看本人；其余角色看全部
    dept_staff_ids = _business_dept_staff_ids()

    today = date.today()
    period_start, period_end = _resolve_stat_range(
        period, request.args.get("startDate"), request.args.get("endDate")
    )
    hot_start = today - timedelta(days=HOT_SHOE_PERIOD_DAYS)

    staff_id_to_name = {
        s.staff_id: s.staff_name for s in db.session.query(Staff).all()
    }

    # 每单总双数子查询
    pairs_subq = _order_pairs_subquery()

    # 订单级别数据（本部门全部正式订单）
    order_q = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            Order.customer_id,
            Customer.customer_name,
            Customer.customer_brand,
            Order.salesman_id,
            Order.start_date,
            Order.end_date,
            func.coalesce(pairs_subq.c.total_pairs, 0).label("total_pairs"),
            OrderStatus.order_current_status,
        )
        .join(Customer, Customer.customer_id == Order.customer_id)
        .outerjoin(pairs_subq, pairs_subq.c.order_id == Order.order_id)
        .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
        .filter(Order.order_type != "F")
    )
    if dept_staff_ids is not None:
        order_q = order_q.filter(Order.salesman_id.in_(dept_staff_ids))
    orders = order_q.all()

    # 1) 客户下单情况（按周期，依据订单开始日期）
    # 2) 业务员下单情况（按周期）
    customer_stats = {}
    salesman_stats = {}
    # 3) 手上未完成订单（当前快照，按客户汇总）
    unfinished_by_customer = {}
    unfinished_total_pairs = 0

    for row in orders:
        pairs = int(row.total_pairs or 0)
        in_period = row.start_date is not None and period_start <= row.start_date <= period_end

        if in_period:
            c = customer_stats.setdefault(
                row.customer_id,
                {"customerId": row.customer_id, "customerName": row.customer_name, "customerBrand": row.customer_brand or "", "orderCount": 0, "totalPairs": 0},
            )
            c["orderCount"] += 1
            c["totalPairs"] += pairs

            s = salesman_stats.setdefault(
                row.salesman_id,
                {
                    "salesmanId": row.salesman_id,
                    "salesmanName": staff_id_to_name.get(row.salesman_id, ""),
                    "orderCount": 0,
                    "totalPairs": 0,
                },
            )
            s["orderCount"] += 1
            s["totalPairs"] += pairs

        is_unfinished = (
            row.order_current_status is None
            or row.order_current_status < ORDER_FINISH_SYMBOL
        )
        if is_unfinished:
            unfinished_total_pairs += pairs
            u = unfinished_by_customer.setdefault(
                row.customer_id,
                {
                    "customerId": row.customer_id,
                    "customerName": row.customer_name,
                    "customerBrand": row.customer_brand or "",
                    "orderCount": 0,
                    "totalPairs": 0,
                    "orders": [],
                },
            )
            u["orderCount"] += 1
            u["totalPairs"] += pairs
            u["orders"].append(
                {
                    "orderRid": row.order_rid,
                    "salesmanName": staff_id_to_name.get(row.salesman_id, ""),
                    "totalPairs": pairs,
                    "orderEndDate": row.end_date.strftime("%Y-%m-%d")
                    if row.end_date
                    else "",
                }
            )

    # 4) 近半年下单频率最高的款式（按工厂型号 shoe_rid）
    hot_q = (
        db.session.query(
            Shoe.shoe_rid,
            func.count(func.distinct(Order.order_id)).label("order_count"),
            func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label(
                "total_pairs"
            ),
        )
        .join(OrderShoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .outerjoin(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .filter(Order.order_type != "F", Order.start_date >= hot_start)
    )
    if dept_staff_ids is not None:
        hot_q = hot_q.filter(Order.salesman_id.in_(dept_staff_ids))
    hot_rows = (
        hot_q.group_by(Shoe.shoe_rid)
        .order_by(func.count(func.distinct(Order.order_id)).desc())
        .limit(HOT_SHOE_LIMIT)
        .all()
    )

    customer_list = sorted(
        customer_stats.values(), key=lambda x: x["totalPairs"], reverse=True
    )
    salesman_list = sorted(
        salesman_stats.values(), key=lambda x: x["totalPairs"], reverse=True
    )
    unfinished_list = sorted(
        unfinished_by_customer.values(), key=lambda x: x["totalPairs"], reverse=True
    )
    hot_list = [
        {
            "shoeRId": r.shoe_rid,
            "orderCount": int(r.order_count or 0),
            "totalPairs": int(r.total_pairs or 0),
        }
        for r in hot_rows
    ]

    return jsonify(
        {
            "period": period,
            "periodStart": period_start.strftime("%Y-%m-%d"),
            "periodEnd": period_end.strftime("%Y-%m-%d"),
            "customerStats": customer_list,
            "salesmanStats": salesman_list,
            "unfinishedByCustomer": unfinished_list,
            "unfinishedTotalPairs": unfinished_total_pairs,
            "unfinishedOrderCount": sum(u["orderCount"] for u in unfinished_list),
            "hotShoes": hot_list,
        }
    )


def _stat_detail_orders(filter_clause, dept_staff_ids, start_date, end_date):
    """返回给定过滤条件下、指定日期范围内的订单明细列表与汇总。"""
    staff_id_to_name = {s.staff_id: s.staff_name for s in db.session.query(Staff).all()}
    pairs_subq = _order_pairs_subquery()
    q = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            Order.customer_id,
            Customer.customer_name,
            Order.salesman_id,
            Order.start_date,
            Order.end_date,
            func.coalesce(pairs_subq.c.total_pairs, 0).label("total_pairs"),
            OrderStatus.order_current_status,
            OrderStatusReference.order_status_name,
        )
        .join(Customer, Customer.customer_id == Order.customer_id)
        .outerjoin(pairs_subq, pairs_subq.c.order_id == Order.order_id)
        .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
        .outerjoin(
            OrderStatusReference,
            OrderStatus.order_current_status == OrderStatusReference.order_status_id,
        )
        .filter(Order.order_type != "F")
        .filter(Order.start_date >= start_date, Order.start_date <= end_date)
        .filter(filter_clause)
    )
    if dept_staff_ids is not None:
        q = q.filter(Order.salesman_id.in_(dept_staff_ids))
    q = q.order_by(Order.start_date.desc())

    orders = []
    total_pairs = 0
    for row in q.all():
        pairs = int(row.total_pairs or 0)
        total_pairs += pairs
        is_unfinished = (
            row.order_current_status is None
            or row.order_current_status < ORDER_FINISH_SYMBOL
        )
        orders.append(
            {
                "orderRid": row.order_rid,
                "customerName": row.customer_name,
                "salesmanName": staff_id_to_name.get(row.salesman_id, ""),
                "totalPairs": pairs,
                "orderStartDate": row.start_date.strftime("%Y-%m-%d") if row.start_date else "",
                "orderEndDate": row.end_date.strftime("%Y-%m-%d") if row.end_date else "",
                "orderStatus": row.order_status_name or "N/A",
                "isUnfinished": is_unfinished,
            }
        )
    return orders, total_pairs


@order_bp.route("/order/businessstatisticsdetail", methods=["GET"])
def get_business_statistics_detail():
    detail_type = request.args.get("type")
    key = request.args.get("key")
    if detail_type not in ("customer", "salesman", "shoe") or not key:
        return jsonify({"message": "invalid params"}), 400

    dept_staff_ids = _business_dept_staff_ids()
    start_date, end_date = _resolve_stat_range(
        request.args.get("period", "month"),
        request.args.get("startDate"),
        request.args.get("endDate"),
    )

    result = {"type": detail_type, "images": []}

    if detail_type == "customer":
        customer = db.session.query(Customer).filter(Customer.customer_id == key).first()
        if customer:
            result["title"] = customer.customer_name + (f"（{customer.customer_brand}）" if customer.customer_brand else "")
        else:
            result["title"] = str(key)
        orders, total_pairs = _stat_detail_orders(
            Order.customer_id == key, dept_staff_ids, start_date, end_date
        )
    elif detail_type == "salesman":
        s = db.session.query(Staff).filter(Staff.staff_id == key).first()
        result["title"] = s.staff_name if s else str(key)
        orders, total_pairs = _stat_detail_orders(
            Order.salesman_id == key, dept_staff_ids, start_date, end_date
        )
    else:  # shoe，按工厂型号 shoe_rid
        result["title"] = key
        shoe = db.session.query(Shoe).filter(Shoe.shoe_rid == key).first()
        if shoe:
            shoe_types = (
                db.session.query(ShoeType, Color)
                .outerjoin(Color, ShoeType.color_id == Color.color_id)
                .filter(ShoeType.shoe_id == shoe.shoe_id)
                .all()
            )
            for shoe_type, color in shoe_types:
                if shoe_type.shoe_image_url:
                    result["images"].append(
                        {
                            "colorName": color.color_name if color else "",
                            "imageUrl": IMAGE_STORAGE_PATH + shoe_type.shoe_image_url,
                        }
                    )
        order_ids_subq = (
            db.session.query(OrderShoe.order_id)
            .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
            .filter(Shoe.shoe_rid == key)
            .subquery()
        )
        orders, total_pairs = _stat_detail_orders(
            Order.order_id.in_(db.session.query(order_ids_subq.c.order_id)),
            dept_staff_ids,
            start_date,
            end_date,
        )

    result["orders"] = orders
    result["orderCount"] = len(orders)
    result["totalPairs"] = total_pairs
    result["unfinishedOrderCount"] = sum(1 for o in orders if o["isUnfinished"])
    result["periodStart"] = start_date.strftime("%Y-%m-%d")
    result["periodEnd"] = end_date.strftime("%Y-%m-%d")
    return jsonify(result)


@order_bp.route("/order/checkorderridexists", methods=["GET"])
def check_order_rid_exists():
    order_rid = request.args.get("pendingRid")
    pending_exists = db.session.query(Order).filter(Order.order_rid == order_rid).first()
    if pending_exists:
        return jsonify({"result":"订单号已存在", "exists":True}), 200
    else:
        return jsonify({"result":"订单号未占用", "exists":False}), 200


@order_bp.route("/order/exportselectionsummary", methods=["POST"])
def export_order_selection_summary():
    """按前端所选订单鞋型（order_shoe）导出汇总 Excel。

    Request JSON: { orderShoeIds: number[] }
    列：订单号 / 客人 / 工厂型号 / 客户型号 / 双数 / 客户订单号 / 客人货期
    """
    from general_document.order_summary_excel import build_order_selection_summary_excel

    data = request.get_json(silent=True) or {}
    order_shoe_ids = data.get("orderShoeIds") or []
    order_shoe_ids = [i for i in order_shoe_ids if i is not None]
    if not order_shoe_ids:
        return jsonify({"message": "未选择订单"}), 400

    pairs_sq = (
        db.session.query(
            OrderShoeType.order_shoe_id.label("order_shoe_id"),
            func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label(
                "total_pairs"
            ),
        )
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .filter(OrderShoeType.order_shoe_id.in_(order_shoe_ids))
        .group_by(OrderShoeType.order_shoe_id)
        .subquery()
    )
    rows_q = (
        db.session.query(Order, OrderShoe, Shoe, Customer, pairs_sq.c.total_pairs)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .outerjoin(pairs_sq, pairs_sq.c.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoe.order_shoe_id.in_(order_shoe_ids))
        .order_by(Order.order_rid.asc())
        .all()
    )
    rows = []
    for order, order_shoe, shoe, customer_obj, total_pairs in rows_q:
        rows.append(
            {
                "order_rid": order.order_rid,
                "customer_name": customer_obj.customer_name,
                "shoe_rid": shoe.shoe_rid,
                "customer_product_name": order_shoe.customer_product_name,
                "total_pairs": int(total_pairs or 0),
                "order_cid": order.order_cid,
                "end_date": order.end_date,
            }
        )

    bio, filename = build_order_selection_summary_excel(rows)
    return send_file(
        bio,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )



@order_bp.route("/order/getcurrencyrates", methods=["GET"])
def get_currency_rates():
    now = datetime.now()
    year, month = now.year, now.month
    # find RMB/CNY base unit
    rmb_unit = (
        db.session.query(AccountingCurrencyUnit)
        .filter(AccountingCurrencyUnit.unit_name_cn == "人民币")
        .first()
    )
    rates = {"RMB": 1.0, "CNY": 1.0}
    if rmb_unit:
        all_units = db.session.query(AccountingCurrencyUnit).all()
        for unit in all_units:
            if unit.unit_id == rmb_unit.unit_id:
                continue
            row = (
                db.session.query(AccountingUnitConversionTable)
                .filter(
                    AccountingUnitConversionTable.unit_from == rmb_unit.unit_id,
                    AccountingUnitConversionTable.unit_to == unit.unit_id,
                    AccountingUnitConversionTable.rate_year * 100
                    + AccountingUnitConversionTable.rate_month
                    <= year * 100 + month,
                )
                .order_by(
                    (
                        AccountingUnitConversionTable.rate_year * 100
                        + AccountingUnitConversionTable.rate_month
                    ).desc()
                )
                .first()
            )
            if row and row.rate:
                rates[unit.unit_name_en] = float(row.rate)
    return jsonify({"rates": rates}), 200


# TODO delete
@order_bp.route("/order/getallorders", methods=["GET"])
def get_all_orders():
    desc_symbol = request.args.get("descSymbol", None)
    exclude_history = request.args.get("excludeHistory", None)
    entities = (
        db.session.query(Order, OrderShoe, Shoe, Customer, OrderStatus, OrderStatusReference)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
        .outerjoin(
            OrderStatusReference,
            OrderStatus.order_current_status == OrderStatusReference.order_status_id,
        )
        .filter(Order.order_type != "F")
    )
    if exclude_history:
        entities = entities.filter(
            or_(
                OrderStatus.order_current_status.is_(None),
                OrderStatus.order_current_status < ORDER_FINISH_SYMBOL,
            )
        )
    # 业务经理/文员只看本业务部（按业务员所属部门归属）的订单；其它角色（生产/物控/总经理等）看全部
    try:
        character, staff, _ = current_user_info()
        if character.character_id in (BUSINESS_MANAGER_ROLE, BUSINESS_CLERK_ROLE):
            dept_staff_ids = [
                s.staff_id
                for s in db.session.query(Staff.staff_id)
                .filter(Staff.department_id == staff.department_id)
                .all()
            ]
            entities = entities.filter(Order.salesman_id.in_(dept_staff_ids))
    except Exception:
        pass
    if desc_symbol:
        entities = entities.order_by(Order.order_rid.desc()).all()
    else:
        entities = entities.order_by(Order.order_rid.asc()).all()
    result = []
    staff_entities = (db.session.query(Staff).all())
    staff_id_to_name_mapping = {}
    for staff in staff_entities:
        staff_id_to_name_mapping[staff.staff_id] = staff.staff_name
    for entity in entities:
        order, order_shoe, shoe, customer, order_status, order_status_reference = entity
        formatted_start_date = order.start_date.strftime("%Y-%m-%d")
        formatted_end_date = order.end_date.strftime("%Y-%m-%d")
        order_status_message = "N/A"
        if order_status_reference and order_status:
            order_status_message = order_status_reference.order_status_name
            if order_status.order_current_status == ORDER_CREATION_STATUS:
                if (
                    order_status.order_status_value != None
                    and order_status.order_status_value == 0
                ):
                    order_status_message += " \n业务员未提交"
                elif (
                    order_status.order_status_value != None
                    and order_status.order_status_value == 1
                ):
                    order_status_message += " \n待经理审核下发"
        if order.production_list_upload_status != PACKAGING_SPECS_UPLOADED:
            order_status_message += "\n包装材料待上传"

        result.append(
            {
                "orderDbId": order.order_id,
                "orderShoeId": order_shoe.order_shoe_id,
                "customerProductName": order_shoe.customer_product_name,
                "shoeRId": shoe.shoe_rid,
                "orderRid": order.order_rid,
                "orderCid": order.order_cid,
                "orderType": order.order_type,
                "shoeCid": order_shoe.customer_product_name,
                "orderSalesman": staff_id_to_name_mapping[order.salesman_id] if order.salesman_id in staff_id_to_name_mapping.keys() else '',
                "orderSupervisor": staff_id_to_name_mapping[order.supervisor_id] if order.supervisor_id in staff_id_to_name_mapping.keys() else '',
                "customerName": customer.customer_name,
                "customerBrand": customer.customer_brand,
                "orderStartDate": formatted_start_date,
                "orderEndDate": formatted_end_date,
                "orderStatus": order_status_message,
                "orderStatusVal": order_status.order_current_status,
                "orderPackagingStatus": order.packaging_status,
                "orderLastStatus": order.last_status,
                "orderCuttingModelStatus": order.cutting_model_status,
                "productionStatus": "",
            }
        )

    # —— 补充生产/出库状态 ——
    order_shoe_ids = [r["orderShoeId"] for r in result if r.get("orderShoeId")]
    if order_shoe_ids:
        # 查询生产排期信息
        prod_infos = {
            pi.order_shoe_id: pi
            for pi in db.session.query(OrderShoeProductionInfo)
            .filter(OrderShoeProductionInfo.order_shoe_id.in_(order_shoe_ids))
            .all()
        }
        # 查询预计数量
        estimated_info = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.coalesce(
                    func.sum(FinishedShoeStorage.finished_estimated_amount), 0
                ).label("total_estimated"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(OrderShoe.order_shoe_id.in_(order_shoe_ids))
            .group_by(OrderShoe.order_shoe_id)
            .all()
        )
        estimated_map = {
            row.order_shoe_id: int(row.total_estimated)
            for row in estimated_info
        }
        # 查询出库数量
        outbound_info = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.coalesce(
                    func.sum(ShoeOutboundRecordDetail.outbound_amount), 0
                ).label("total_outbound"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .join(
                ShoeOutboundRecordDetail,
                ShoeOutboundRecordDetail.finished_shoe_storage_id
                == FinishedShoeStorage.finished_shoe_id,
            )
            .filter(OrderShoe.order_shoe_id.in_(order_shoe_ids))
            .group_by(OrderShoe.order_shoe_id)
            .all()
        )
        outbound_map = {
            row.order_shoe_id: int(row.total_outbound)
            for row in outbound_info
        }
        # 查询是否有入库完成的记录
        inbound_done_info = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.count(FinishedShoeStorage.finished_shoe_id).label("done_count"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(
                OrderShoe.order_shoe_id.in_(order_shoe_ids),
                FinishedShoeStorage.finished_status >= 1,
            )
            .group_by(OrderShoe.order_shoe_id)
            .all()
        )
        inbound_done_map = {
            row.order_shoe_id: int(row.done_count) > 0
            for row in inbound_done_info
        }
        # 查询待审核的出库申请
        pending_apply_info = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.count(ShoeOutboundApply.apply_id.distinct()).label("pending_count"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .join(
                ShoeOutboundApplyDetail,
                ShoeOutboundApplyDetail.finished_shoe_storage_id
                == FinishedShoeStorage.finished_shoe_id,
            )
            .join(
                ShoeOutboundApply,
                ShoeOutboundApply.apply_id == ShoeOutboundApplyDetail.apply_id,
            )
            .filter(
                OrderShoe.order_shoe_id.in_(order_shoe_ids),
                ShoeOutboundApply.status.in_([1, 3]),
            )
            .group_by(OrderShoe.order_shoe_id)
            .all()
        )
        pending_apply_map = {
            row.order_shoe_id: int(row.pending_count)
            for row in pending_apply_info
        }

        for r in result:
            os_id = r.get("orderShoeId")
            if not os_id:
                continue
            pi = prod_infos.get(os_id)
            if not pi:
                r["productionStatus"] = "未排产"
                continue
            estimated_status = estimate_status_converter(pi)
            if estimated_status != "生产已结束":
                r["productionStatus"] = estimated_status
                continue
            # 生产已结束，检查是否入库完成
            if not inbound_done_map.get(os_id, False):
                r["productionStatus"] = "成型"
                continue
            estimated = estimated_map.get(os_id, 0)
            outbound = outbound_map.get(os_id, 0)
            has_pending_apply = pending_apply_map.get(os_id, 0) > 0
            if outbound > 0 and outbound >= estimated and estimated > 0:
                r["productionStatus"] = f"已全部出库 ({outbound}双)"
            elif outbound > 0:
                r["productionStatus"] = f"部分出库 (已出{outbound}/{estimated}双)"
            elif has_pending_apply:
                r["productionStatus"] = "出库审核中"
            else:
                r["productionStatus"] = "待出库"

    # —— 补充退回状态 ——
    order_ids_in_result = list({r["orderDbId"] for r in result if r.get("orderDbId")})
    if order_ids_in_result:
        reverted_order_ids = {
            row.order_id
            for row in db.session.query(RevertEvent.order_id)
            .filter(RevertEvent.order_id.in_(order_ids_in_result))
            .distinct()
            .all()
        }
        for r in result:
            r["hasRevertEvent"] = r["orderDbId"] in reverted_order_ids
    else:
        for r in result:
            r["hasRevertEvent"] = False

    # —— 补充每单总双数 ——
    if order_ids_in_result:
        order_total_pairs_rows = (
            db.session.query(
                Order.order_id,
                func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label("total_pairs"),
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
            )
            .filter(Order.order_id.in_(order_ids_in_result))
            .group_by(Order.order_id)
            .all()
        )
        order_total_pairs_map = {row.order_id: int(row.total_pairs or 0) for row in order_total_pairs_rows}
        for r in result:
            r["orderTotalPairs"] = order_total_pairs_map.get(r["orderDbId"], 0)
    else:
        for r in result:
            r["orderTotalPairs"] = 0

    return jsonify(result)


@order_bp.route("/order/getallorderstatus", methods=["GET"])
def get_all_order_status():
    entities = db.session.query(OrderStatusReference).all()
    result = []
    for entity in entities:
        result.append(
            {"value": entity.order_status_id, "label": entity.order_status_name}
        )
    return jsonify(result)


@order_bp.route("/order/deleteorder", methods=["DELETE"])
def delete_order():
    order_id = request.args.get("orderId")
    order_entity = db.session.query(Order).filter_by(order_id=order_id).first()
    if not order_entity:
        return jsonify({"message": "delete failed"}), 404
    order_local_path = os.path.join(FILE_STORAGE_PATH, order_entity.order_rid)
    if os.path.exists(order_local_path):
        shutil.rmtree(order_local_path)
    else:
        logger.debug("path doesnt exist in server")
    order_shoe_entities = db.session.query(OrderShoe).filter_by(order_id=order_id).all()
    order_shoe_ids = [entity.order_shoe_id for entity in order_shoe_entities]
    order_shoe_type_entities = (
        db.session.query(OrderShoeType)
        .filter(OrderShoeType.order_shoe_id.in_(order_shoe_ids))
        .all()
    )
    order_shoe_type_ids = [
        entity.order_shoe_type_id for entity in order_shoe_type_entities
    ]

    db.session.query(OrderShoeBatchInfo).filter(
        OrderShoeBatchInfo.order_shoe_type_id.in_(order_shoe_type_ids)
    ).delete()
    db.session.query(OrderShoeType).filter(
        OrderShoeType.order_shoe_id.in_(order_shoe_ids)
    ).delete()
    db.session.query(OrderShoeStatus).filter(
        OrderShoeStatus.order_shoe_id.in_(order_shoe_ids)
    ).delete()
    db.session.query(OrderShoeProductionInfo).filter(
        OrderShoeProductionInfo.order_shoe_id.in_(order_shoe_ids)
    ).delete()
    db.session.query(OrderShoe).filter_by(order_id=order_id).delete()
    db.session.query(OrderStatus).filter_by(order_id=order_id).delete()
    db.session.delete(order_entity)
    db.session.commit()
    return jsonify({"message": "Delete OK"}), 200


@order_bp.route("/order/getordershoeinfo", methods=["GET"])
def get_order_shoe_info():
    order_id = request.args.get("orderrid")
    entities = (
        db.session.query(
            Order,
            OrderShoe,
            OrderShoeType,
            Shoe,
            ShoeType,
            OrderShoeBatchInfo,
            Color,
            func.group_concat(OrderShoeStatusReference.status_name).label(
                "combined_statuses"
            ),
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .outerjoin(
            OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id
        )  # Outer join to handle cases where there's no status
        .outerjoin(
            OrderShoeStatusReference,
            OrderShoeStatus.current_status == OrderShoeStatusReference.status_id,
        )
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id
        )  # Join ShoeType using the correct relation with OrderShoeType
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,  # Ensure each batch is for the correct shoe type
        )
        .join(Color, Color.color_id == ShoeType.color_id)
        .filter(Order.order_rid == order_id)
        .group_by(
            Order.order_id,
            OrderShoe.order_shoe_id,
            OrderShoeType.order_shoe_type_id,
            ShoeType.shoe_type_id,
            Color.color_id,
            OrderShoeBatchInfo.order_shoe_batch_info_id,
        )  # Group by fields that ensure uniqueness for each type and batch
        .all()
    )
    result = []
    for entity in entities:
        (
            order,
            order_shoe,
            order_shoe_type,
            shoe,
            shoe_type,
            order_shoe_batch_info,
            color,
            combined_statuses,
        ) = entity
        formatted_start_date = order.start_date.strftime("%Y-%m-%d")
        formatted_end_date = order.end_date.strftime("%Y-%m-%d")
        result.append(
            {
                "orderRid": order.order_rid,
                "inheritId": shoe.shoe_rid,
                "customerId": order_shoe.customer_product_name,
                "colorCN": color.color_name,
                "colorEN": color.color_en_name,
                "sizeId": order_shoe_batch_info.name,
                "7/35": order_shoe_batch_info.size_35_amount,
                "7.5/36": order_shoe_batch_info.size_36_amount,
                "8/37": order_shoe_batch_info.size_37_amount,
                "8.5/38": order_shoe_batch_info.size_38_amount,
                "9/39": order_shoe_batch_info.size_39_amount,
                "9.5/40": order_shoe_batch_info.size_40_amount,
                "10/41": order_shoe_batch_info.size_41_amount,
                "10.5/42": order_shoe_batch_info.size_42_amount,
                "11/43": order_shoe_batch_info.size_43_amount,
                "12/44": order_shoe_batch_info.size_44_amount,
                "13/45": order_shoe_batch_info.size_45_amount,
                "pairCount": order_shoe_batch_info.total_amount,
                "status": combined_statuses,
            }
        )
    return jsonify(result)


@order_bp.route("/order/getorderdocinfo", methods=["GET"])
def get_order_doc_info():
    order_rid = request.args.get("orderrid")
    entity = db.session.query(Order).filter(Order.order_rid == order_rid).first()
    result = {
        "productionDoc": (
            "未上传" if entity.production_list_upload_status == "0" else "已上传"
        ),
        "amountDoc": "未上传" if entity.amount_list_upload_status == "0" else "已上传",
    }
    return jsonify(result)


@order_bp.route("/order/getordershoestatusoptions", methods=["GET"])
def get_order_shoe_status_options():
    references = (
        db.session.query(OrderShoeStatusReference)
        .order_by(OrderShoeStatusReference.status_id.asc())
        .all()
    )
    options = [
        {"value": ref.status_id, "label": ref.status_name} for ref in references
    ]
    return jsonify({"options": options})


def _get_linger_info_for_shoe(order_shoe_id, linger_stage_id=None, min_stay_days=0):
    """Collect active (in-progress) statuses for an order shoe and compute stay days."""
    query = (
        db.session.query(OrderShoeStatus, OrderShoeStatusReference)
        .join(
            OrderShoeStatusReference,
            OrderShoeStatus.current_status == OrderShoeStatusReference.status_id,
        )
        .filter(
            OrderShoeStatus.order_shoe_id == order_shoe_id,
            OrderShoeStatus.current_status_value == 0,
        )
    )
    if linger_stage_id is not None:
        query = query.filter(OrderShoeStatus.current_status == linger_stage_id)
    now = datetime.now()
    names = []
    earliest = None
    max_delay = 0
    for status, ref in query.all():
        entered = status.update_time or status.create_time
        delay_days = (now - entered).days if entered else 0
        if min_stay_days and delay_days < min_stay_days:
            continue
        names.append(ref.status_name)
        if entered and (earliest is None or entered < earliest):
            earliest = entered
        if delay_days > max_delay:
            max_delay = delay_days
    return {
        "names": names,
        "earliest": earliest.strftime("%Y-%m-%d %H:%M:%S") if earliest else "N/A",
        "maxDelay": max_delay,
    }


@order_bp.route("/order/getorderfullinfo", methods=["GET"])
def get_order_full_info():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 10, type=int)
    order_search = request.args.get("orderSearch", "", type=str)
    customer_search = request.args.get("customerSearch", "", type=str)
    shoe_rid_search = request.args.get("shoeRIdSearch", "", type=str)
    shoe_cid_search = request.args.get("shoeCIdSearch", "", type=str)
    order_cid_search = request.args.get("orderCIdSearch", "", type=str)
    view_past_tasks = request.args.get("viewPastTasks", 0, type=int)
    linger_stage_value = request.args.get("lingerStageValue", "", type=str)
    min_stay_days = request.args.get("minStayDays", 0, type=int)
    try:
        linger_stage_id = (
            int(linger_stage_value) if linger_stage_value not in (None, "") else None
        )
    except (TypeError, ValueError):
        linger_stage_id = None

    character, staff, department = current_user_info()

    order_shoe_status = (
        db.session.query(
            OrderShoe.order_shoe_id,
            func.group_concat(OrderShoeStatus.current_status).label("current_status"),
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        .group_by(OrderShoe.order_shoe_id)
        .subquery()
    )

    order_shoe_status_reference = (
        db.session.query(
            OrderShoe.order_shoe_id,
            func.group_concat(OrderShoeStatusReference.status_name).label(
                "status_name"
            ),
        )
        .join(
            OrderShoeStatus,
            OrderShoeStatusReference.status_id == OrderShoeStatus.current_status,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        .group_by(OrderShoe.order_shoe_id)
        .subquery()
    )

    order_amount_subquery = (
        db.session.query(
            Order.order_id,
            func.sum(OrderShoeBatchInfo.total_amount).label("order_amount"),
        )
        .join(
            OrderShoe,
            OrderShoe.order_id == Order.order_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .group_by(OrderShoe.order_id)
        .subquery()
    )

    order_price_subquery = (
        db.session.query(
            Order.order_id,
            func.sum(OrderShoeType.unit_price * OrderShoeBatchInfo.total_amount).label("order_total_price"),
            func.max(OrderShoeType.currency_type).label("order_currency"),
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .group_by(Order.order_id)
        .subquery()
    )

    query = (
        db.session.query(
            Order,
            OrderStatusReference,
            OrderShoe,
            order_shoe_status_reference.c.status_name.label(
                "order_shoe_status_reference_names"
            ),
            Customer,
            Shoe,
            order_amount_subquery.c.order_amount,
            order_price_subquery.c.order_total_price,
            order_price_subquery.c.order_currency,
        )
        .join(OrderStatus, Order.order_id == OrderStatus.order_id)
        .join(
            OrderStatusReference,
            OrderStatus.order_current_status == OrderStatusReference.order_status_id,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .outerjoin(
            order_shoe_status,
            OrderShoe.order_shoe_id == order_shoe_status.c.order_shoe_id,
        )
        .outerjoin(
            order_shoe_status_reference,
            OrderShoe.order_shoe_id == order_shoe_status_reference.c.order_shoe_id,
        )
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(
            order_amount_subquery,
            Order.order_id == order_amount_subquery.c.order_id,
        )
        .outerjoin(
            order_price_subquery,
            Order.order_id == order_price_subquery.c.order_id,
        )
        .filter(
            Order.order_rid.like(f"%{order_search}%"),
            Customer.customer_name.like(f"%{customer_search}%"),
            Shoe.shoe_rid.like(f"%{shoe_rid_search}%"),
            func.coalesce(OrderShoe.customer_product_name, "").like(f"%{shoe_cid_search}%"),
            func.coalesce(Order.order_cid, "").like(f"%{order_cid_search}%"),
        )
        .group_by(Order.order_id, OrderStatus.order_status_id, OrderShoe.order_shoe_id)
        .order_by(Order.order_id.desc())
    )

    if character.character_id == DEV_DEPARTMENT_MANAGER:
        query = query.filter(OrderStatus.order_current_status >= ORDER_IN_PROD_STATUS)
        query = query.filter(Shoe.shoe_department_id == department.department_name)
        if view_past_tasks == 1:
            query = query.filter(~func.find_in_set('0', order_shoe_status.c.current_status))

    #TODO
    # if character.character_id == USAGE_CALCULATION_ROLE:
    #     query = query.filter(OrderStatus.order_current_status >= ORDER_IN_PROD_STATUS)
    #     if view_past_tasks == 1:
    #         query = query.filter(OrderShoe. > USAGE_CALCULATION_ORDER_SHOE_STATUS)
    #     else:
    #         query = query.filter(func.find_in_set('0', order_shoe_status.c.current_status))

    # if character.character_id == TECH_DEPARTMENT_MANAGER:
    #     query = query.filter(OrderStatus.order_current_status >= ORDER_IN_PROD_STATUS)
    #     if view_past_tasks == 1:
    #         query = query.filter(
    #             OrderShoeStatus.current_status > CRAFT_SHEET_ORDER_SHOE_STATUS
    #         )
    #     else:
    #         query = query.filter(
    #             OrderShoeStatus.current_status >= CRAFT_SHEET_ORDER_SHOE_STATUS
    #         )

    if linger_stage_id is not None or min_stay_days > 0:
        linger_subquery = db.session.query(OrderShoeStatus.order_shoe_id).filter(
            OrderShoeStatus.current_status_value == 0
        )
        if linger_stage_id is not None:
            linger_subquery = linger_subquery.filter(
                OrderShoeStatus.current_status == linger_stage_id
            )
        if min_stay_days > 0:
            cutoff_time = datetime.now() - timedelta(days=min_stay_days)
            linger_subquery = linger_subquery.filter(
                OrderShoeStatus.update_time <= cutoff_time
            )
        query = query.filter(OrderShoe.order_shoe_id.in_(linger_subquery))

    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()

    # Build currency -> RMB rate map for orderTotalPriceRmb conversion
    _currency_rmb_rates = {"RMB": 1.0, "CNY": 1.0}
    try:
        _rmb_unit = (
            db.session.query(AccountingCurrencyUnit)
            .filter(AccountingCurrencyUnit.unit_name_cn == "人民币")
            .first()
        )
        if _rmb_unit:
            _now = datetime.now()
            _all_units = db.session.query(AccountingCurrencyUnit).all()
            for _u in _all_units:
                if _u.unit_id == _rmb_unit.unit_id:
                    continue
                _row = (
                    db.session.query(AccountingUnitConversionTable)
                    .filter(
                        AccountingUnitConversionTable.unit_from == _rmb_unit.unit_id,
                        AccountingUnitConversionTable.unit_to == _u.unit_id,
                        AccountingUnitConversionTable.rate_year * 100
                        + AccountingUnitConversionTable.rate_month
                        <= _now.year * 100 + _now.month,
                    )
                    .order_by(
                        (
                            AccountingUnitConversionTable.rate_year * 100
                            + AccountingUnitConversionTable.rate_month
                        ).desc()
                    )
                    .first()
                )
                if _row and _row.rate:
                    _currency_rmb_rates[_u.unit_name_en] = float(_row.rate)
    except Exception:
        pass

    # Initialize a dictionary to group orders
    orders_dict = {}

    # Loop through the query result
    for (
        order,
        order_status_reference,
        order_shoe,
        order_shoe_status_reference_names,
        customer,
        shoe,
        order_amount,
        order_total_price,
        order_currency,
    ) in response:
        formatted_start_date = (
            order.start_date.strftime("%Y-%m-%d") if order.start_date else "N/A"
        )
        formatted_end_date = (
            order.end_date.strftime("%Y-%m-%d") if order.end_date else "N/A"
        )

        # If the order isn't already in the dictionary, add it
        if order.order_id not in orders_dict:
            orders_dict[order.order_id] = {
                "orderId": order.order_id if order.order_id else "N/A",
                "orderRid": order.order_rid if order.order_rid else "N/A",
                "orderCid": order.order_cid if order.order_cid else "N/A",
                "shoeRid": shoe.shoe_rid if shoe else "N/A",
                "customerName": customer.customer_name if customer else "N/A",
                "createTime": formatted_start_date,
                "deadlineTime": formatted_end_date,
                "status": (
                    order_status_reference.order_status_name
                    if order_status_reference
                    else "N/A"
                ),
                "shoes": {},  # Using a dictionary to avoid duplicate shoes
                "orderAmount": order_amount if order_amount else 0,
                "orderTotalPrice": float(order_total_price) if order_total_price else None,
                "orderCurrency": order_currency or "",
                "orderTotalPriceRmb": (
                    round(float(order_total_price) * _currency_rmb_rates.get(order_currency, 1.0), 2)
                    if order_total_price else None
                ),
            }

        # Use a unique key for each shoe to avoid duplicates
        shoe_key = order_shoe.order_shoe_id if order_shoe else "N/A"

        if shoe_key not in orders_dict[order.order_id]["shoes"]:
            purchase_status_string = ""
            if order_status_reference.order_status_name == "生产订单创建":
                purchase_status_string = "业务部正在处理中"
            else:
                _status_names = order_shoe_status_reference_names or ""
                if "一次采购入库" in _status_names:
                    purchase_status_string += "一次采购已完成, 等待入库 | "
                if "二次采购入库" in _status_names:
                    purchase_status_string += "二次采购已完成，等待入库 | "
                if "投产指令单创建" in _status_names or "面料单位用量计算" in _status_names:
                    purchase_status_string += "技术部正在处理中 | "
                if "一次采购订单创建" in _status_names:
                    purchase_status_string += "物控经理正在处理中 | "
                if "总仓采购订单创建" in _status_names:
                    purchase_status_string += "总仓经理正在处理中 | "
                
            # Prepare shoe information for the first occurrence
            orders_dict[order.order_id]["shoes"][shoe_key] = {
                "shoeRid": shoe.shoe_rid if shoe else "N/A",
                "customerId": order_shoe.customer_product_name if order_shoe else "N/A",
                "designDepartment": shoe.shoe_department_id if shoe and shoe.shoe_department_id else "",
                "firstBom": "N/A",
                "secondBom": "N/A",
                "firstOrder": "N/A",
                "secondOrder": "N/A",
                "statuses": "".join(
                    (order_shoe_status_reference_names or "").split(" | ")
                ),  # To hold the combined statuses as a string
                "purchaseStatus": purchase_status_string.strip(" | "),  # Clean up trailing separator
                "bussinessEventTime": "N/A",
                "productionOrderIssueEventTime": "N/A",
                "firstUsageInputIssueEventTime": "N/A",
                "firstPurchaseOrderIssueEventTime": "N/A",
                "secondPurchaseOrderIssueEventTime": "N/A",
            }

            linger_info = _get_linger_info_for_shoe(
                order_shoe.order_shoe_id if order_shoe else None,
                linger_stage_id,
                min_stay_days,
            )
            matched_names = " | ".join(linger_info["names"]) if linger_info["names"] else ""
            orders_dict[order.order_id]["shoes"][shoe_key].update(
                {
                    "matchedStatusName": matched_names,
                    "matchedStatusUpdateTime": (
                        linger_info["earliest"] if linger_info["names"] else ""
                    ),
                    "matchedStatusDelayText": (
                        f'{linger_info["maxDelay"]}天' if linger_info["names"] else ""
                    ),
                    "_matchedNames": linger_info["names"],
                    "_matchedDelay": linger_info["maxDelay"],
                }
            )

        # # Assign BOM based on bom_type
        # if bom:
        #     if bom.bom_type == 0:
        #         orders_dict[order.order_id]["shoes"][shoe_key]["firstBom"] = bom.bom_rid
        #     elif bom.bom_type == 1:
        #         orders_dict[order.order_id]["shoes"][shoe_key][
        #             "secondBom"
        #         ] = bom.bom_rid

        # # Assign purchase orders based on purchase_order_type
        # if purchase_order:
        #     if purchase_order.purchase_order_type == "F":
        #         orders_dict[order.order_id]["shoes"][shoe_key][
        #             "firstOrder"
        #         ] = purchase_order.purchase_order_rid
        #     elif purchase_order.purchase_order_type == "S":
        #         orders_dict[order.order_id]["shoes"][shoe_key][
        #             "secondOrder"
        #         ] = purchase_order.purchase_order_rid

    # Convert the shoes from dictionary to list and create the final result list
    result = []
    for order_id, order_data in orders_dict.items():
        order_data["shoes"] = list(
            order_data["shoes"].values()
        )  # Convert shoe dict to list

        matched_name_set = []
        max_matched_delay = 0
        has_match = False
        for shoe in order_data["shoes"]:
            for name in shoe.get("_matchedNames", []):
                has_match = True
                if name not in matched_name_set:
                    matched_name_set.append(name)
            if shoe.get("_matchedDelay", 0) > max_matched_delay:
                max_matched_delay = shoe.get("_matchedDelay", 0)
            shoe.pop("_matchedNames", None)
            shoe.pop("_matchedDelay", None)
        order_data["matchedStatusNames"] = " | ".join(matched_name_set)
        order_data["maxMatchedDelayText"] = (
            f"{max_matched_delay}天" if has_match else ""
        )

        all_order_event_times = (
            db.session.query(Event).join(
                Order, Event.event_order_id == Order.order_id
            ).filter(
                Order.order_id == order_id
            ).all()
        )
        # bussiness event time : Event.operation_id == 13
        business_event_times = [
            event.handle_time.strftime("%Y-%m-%d %H:%M:%S")
            for event in all_order_event_times
            if event.operation_id == 15
        ]
        # production_order issue event time : Event.operation_id == 39
        production_order_issue_event_times = [
            event.handle_time.strftime("%Y-%m-%d %H:%M:%S")
            for event in all_order_event_times
            if event.operation_id == 39
        ]
        # first_usage_input_issue event time : Event.operation_id == 47
        first_usage_input_issue_event_times = [
            event.handle_time.strftime("%Y-%m-%d %H:%M:%S")
            for event in all_order_event_times
            if event.operation_id == 47
        ]
        # first_purchase_order_issue event time : Event.operation_id == 51
        first_purchase_order_issue_event_times = [
            event.handle_time.strftime("%Y-%m-%d %H:%M:%S")
            for event in all_order_event_times
            if event.operation_id == 51
        ]
        # second_usage_input_issue event time : Event.operation_id == 53
        second_usage_input_issue_event_times = [
            event.handle_time.strftime("%Y-%m-%d %H:%M:%S")
            for event in all_order_event_times
            if event.operation_id == 53
        ]
        for shoe in order_data["shoes"]:
            shoe["bussinessEventTime"] = (
                business_event_times[0] if business_event_times else "N/A"
            )
            shoe["productionOrderIssueEventTime"] = (
                production_order_issue_event_times[0]
                if production_order_issue_event_times
                else "N/A"
            )
            shoe["firstUsageInputIssueEventTime"] = (
                first_usage_input_issue_event_times[0]
                if first_usage_input_issue_event_times
                else "N/A"
            )
            shoe["firstPurchaseOrderIssueEventTime"] = (
                first_purchase_order_issue_event_times[0]
                if first_purchase_order_issue_event_times
                else "N/A"
            )
            shoe["secondPurchaseInputIssueEventTime"] = (
                second_usage_input_issue_event_times[0]
                if second_usage_input_issue_event_times
                else "N/A"
            )
        result.append(order_data)

        

    return jsonify({"result": result, "total": count_result})


@order_bp.route("/order/getlingerdashboard", methods=["GET"])
def get_linger_dashboard():
    linger_stage_value = request.args.get("lingerStageValue", "", type=str)
    min_stay_days = request.args.get("minStayDays", 0, type=int)
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 20, type=int)
    try:
        linger_stage_id = (
            int(linger_stage_value) if linger_stage_value not in (None, "") else None
        )
    except (TypeError, ValueError):
        linger_stage_id = None

    now = datetime.now()
    records = []

    # 鞋型阶段滞留：order_shoe_status 中仍在进行中的状态
    shoe_query = (
        db.session.query(
            Order, Customer, Shoe, OrderShoe, OrderShoeStatus, OrderShoeStatusReference
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(
            OrderShoeStatusReference,
            OrderShoeStatusReference.status_id == OrderShoeStatus.current_status,
        )
        .filter(OrderShoeStatus.current_status_value == 0)
    )
    if linger_stage_id is not None:
        shoe_query = shoe_query.filter(
            OrderShoeStatus.current_status == linger_stage_id
        )
    for order, customer, shoe, order_shoe, status, ref in shoe_query.all():
        entered = status.update_time or status.create_time
        delay_days = (now - entered).days if entered else 0
        if min_stay_days and delay_days < min_stay_days:
            continue
        records.append(
            {
                "orderRid": order.order_rid,
                "customerName": customer.customer_name if customer else "N/A",
                "lingerStageType": "鞋型",
                "lingerStage": ref.status_name,
                "shoeRid": shoe.shoe_rid if shoe else "N/A",
                "customerProductName": (
                    order_shoe.customer_product_name if order_shoe else "N/A"
                ),
                "lingerSince": (
                    entered.strftime("%Y-%m-%d %H:%M:%S") if entered else "N/A"
                ),
                "delayText": f"{delay_days}天",
                "_delayDays": delay_days,
            }
        )

    # 订单阶段滞留：仅在未按鞋型阶段过滤时统计（阶段选项来自鞋型状态，与订单状态编号空间不同）
    if linger_stage_id is None:
        order_query = (
            db.session.query(Order, Customer, OrderStatus, OrderStatusReference)
            .join(OrderStatus, OrderStatus.order_id == Order.order_id)
            .join(Customer, Customer.customer_id == Order.customer_id)
            .join(
                OrderStatusReference,
                OrderStatusReference.order_status_id
                == OrderStatus.order_current_status,
            )
            .filter(OrderStatus.order_status_value == 0)
        )
        for order, customer, status, ref in order_query.all():
            entered = status.update_time or status.create_time
            delay_days = (now - entered).days if entered else 0
            if min_stay_days and delay_days < min_stay_days:
                continue
            records.append(
                {
                    "orderRid": order.order_rid,
                    "customerName": customer.customer_name if customer else "N/A",
                    "lingerStageType": "订单",
                    "lingerStage": ref.order_status_name,
                    "shoeRid": "N/A",
                    "customerProductName": "N/A",
                    "lingerSince": (
                        entered.strftime("%Y-%m-%d %H:%M:%S") if entered else "N/A"
                    ),
                    "delayText": f"{delay_days}天",
                    "_delayDays": delay_days,
                }
            )

    order_count = sum(1 for r in records if r["lingerStageType"] == "订单")
    shoe_count = sum(1 for r in records if r["lingerStageType"] == "鞋型")
    over_seven = sum(1 for r in records if r["_delayDays"] > 7)

    summary = [
        {"title": "滞留总数", "value": len(records)},
        {"title": "订单阶段滞留", "value": order_count},
        {"title": "鞋型阶段滞留", "value": shoe_count},
        {"title": "超7天", "value": over_seven},
    ]

    stage_counter = {}
    for r in records:
        stage_counter[r["lingerStage"]] = stage_counter.get(r["lingerStage"], 0) + 1
    stage_distribution = [
        {"name": name, "value": value}
        for name, value in sorted(
            stage_counter.items(), key=lambda item: item[1], reverse=True
        )
    ]

    type_distribution = [
        {"name": "订单阶段", "value": order_count},
        {"name": "鞋型阶段", "value": shoe_count},
    ]

    records.sort(key=lambda r: r["_delayDays"], reverse=True)
    top_records = records[:20]
    records_total = len(records)
    start = max(page - 1, 0) * page_size
    detail_records = records[start : start + page_size]
    for r in top_records:
        r.pop("_delayDays", None)
    for r in detail_records:
        r.pop("_delayDays", None)

    return jsonify(
        {
            "summary": summary,
            "topRecords": top_records,
            "records": detail_records,
            "recordsTotal": records_total,
            "stageDistribution": stage_distribution,
            "typeDistribution": type_distribution,
        }
    )


@order_bp.route("/order/exportorderexcel", methods=["GET"])
def export_order_excel():
    """Export filtered orders as an Excel file (same filters as getorderfullinfo)."""
    import io
    from openpyxl import Workbook

    order_search = request.args.get("orderSearch", "", type=str)
    customer_search = request.args.get("customerSearch", "", type=str)
    shoe_rid_search = request.args.get("shoeRIdSearch", "", type=str)
    convert_to_rmb = request.args.get("convertToRMB", "0") == "1"
    view_past_tasks = request.args.get("viewPastTasks", 0, type=int)

    # Build currency -> RMB rate map
    _currency_rmb_rates = {"RMB": 1.0, "CNY": 1.0}
    try:
        _rmb_unit = (
            db.session.query(AccountingCurrencyUnit)
            .filter(AccountingCurrencyUnit.unit_name_cn == "人民币")
            .first()
        )
        if _rmb_unit:
            _now = datetime.now()
            for _u in db.session.query(AccountingCurrencyUnit).all():
                if _u.unit_id == _rmb_unit.unit_id:
                    continue
                _row = (
                    db.session.query(AccountingUnitConversionTable)
                    .filter(
                        AccountingUnitConversionTable.unit_from == _rmb_unit.unit_id,
                        AccountingUnitConversionTable.unit_to == _u.unit_id,
                        AccountingUnitConversionTable.rate_year * 100
                        + AccountingUnitConversionTable.rate_month
                        <= _now.year * 100 + _now.month,
                    )
                    .order_by(
                        (
                            AccountingUnitConversionTable.rate_year * 100
                            + AccountingUnitConversionTable.rate_month
                        ).desc()
                    )
                    .first()
                )
                if _row and _row.rate:
                    _currency_rmb_rates[_u.unit_name_en] = float(_row.rate)
    except Exception:
        pass

    order_price_subquery = (
        db.session.query(
            Order.order_id,
            func.sum(OrderShoeType.unit_price * OrderShoeBatchInfo.total_amount).label("order_total_price"),
            func.max(OrderShoeType.currency_type).label("order_currency"),
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeBatchInfo, OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .group_by(Order.order_id)
        .subquery()
    )

    order_amount_subquery = (
        db.session.query(
            Order.order_id,
            func.sum(OrderShoeBatchInfo.total_amount).label("order_amount"),
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeBatchInfo, OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .group_by(Order.order_id)
        .subquery()
    )

    query = (
        db.session.query(
            Order,
            Customer,
            OrderStatusReference,
            Shoe,
            OrderShoe,
            order_amount_subquery.c.order_amount,
            order_price_subquery.c.order_total_price,
            order_price_subquery.c.order_currency,
        )
        .join(OrderStatus, Order.order_id == OrderStatus.order_id)
        .join(OrderStatusReference, OrderStatus.order_current_status == OrderStatusReference.order_status_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(order_amount_subquery, Order.order_id == order_amount_subquery.c.order_id)
        .outerjoin(order_price_subquery, Order.order_id == order_price_subquery.c.order_id)
        .filter(
            Order.order_rid.like(f"%{order_search}%"),
            Customer.customer_name.like(f"%{customer_search}%"),
            Shoe.shoe_rid.like(f"%{shoe_rid_search}%"),
        )
        .group_by(Order.order_id, OrderShoe.order_shoe_id, OrderStatusReference.order_status_id)
        .order_by(Order.order_id.desc())
    )

    rows = query.all()

    # Group by order
    orders_dict = {}
    for order, customer, status_ref, shoe, order_shoe, amount, total_price, currency in rows:
        if order.order_id not in orders_dict:
            orders_dict[order.order_id] = {
                "orderRid": order.order_rid or "",
                "customerName": customer.customer_name if customer else "",
                "createTime": order.start_date.strftime("%Y-%m-%d") if order.start_date else "",
                "deadlineTime": order.end_date.strftime("%Y-%m-%d") if order.end_date else "",
                "status": status_ref.order_status_name if status_ref else "",
                "orderAmount": amount or 0,
                "orderTotalPrice": float(total_price) if total_price else 0,
                "orderCurrency": currency or "",
                "shoes": [],
            }
        orders_dict[order.order_id]["shoes"].append({
            "shoeRid": shoe.shoe_rid if shoe else "",
            "customerId": order_shoe.customer_product_name if order_shoe else "",
            "designDepartment": shoe.shoe_department_id if shoe and shoe.shoe_department_id else "",
        })

    wb = Workbook()
    ws = wb.active
    ws.title = "订单查询"

    if convert_to_rmb:
        headers = ["订单号", "客人名称", "工厂型号", "客户型号", "设计部门", "订单数量",
                    "订单金额(RMB)", "订单日期", "交货日期", "订单状态"]
    else:
        headers = ["订单号", "客人名称", "工厂型号", "客户型号", "设计部门", "订单数量",
                    "订单金额", "金额单位", "订单日期", "交货日期", "订单状态"]
    ws.append(headers)

    for oid in sorted(orders_dict.keys(), reverse=True):
        od = orders_dict[oid]
        shoe_rids = ", ".join(s["shoeRid"] for s in od["shoes"])
        customer_ids = ", ".join(s["customerId"] for s in od["shoes"])
        departments = ", ".join(filter(None, (s["designDepartment"] for s in od["shoes"])))

        price = od["orderTotalPrice"]
        currency = od["orderCurrency"]

        if convert_to_rmb:
            rmb_price = round(price * _currency_rmb_rates.get(currency, 1.0), 2) if price else ""
            ws.append([
                od["orderRid"], od["customerName"], shoe_rids, customer_ids,
                departments, od["orderAmount"], rmb_price,
                od["createTime"], od["deadlineTime"], od["status"],
            ])
        else:
            ws.append([
                od["orderRid"], od["customerName"], shoe_rids, customer_ids,
                departments, od["orderAmount"],
                round(price, 2) if price else "",
                currency,
                od["createTime"], od["deadlineTime"], od["status"],
            ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="订单查询.xlsx",
    )


@order_bp.route("/order/getorderpageinfo", methods=["GET"])
def get_order_page_info():
    order_search = request.args.get("orderSearch", "", type=str)
    customer_search = request.args.get("customerSearch", "", type=str)
    shoe_rid_search = request.args.get("shoeRIdSearch", "", type=str)
    order_status = request.args.get("orderStatus", "", type=int)
    status_value = request.args.get("statusValue", "", type=int)

    # Base query for filtering orders
    base_query = (
        db.session.query(Order.order_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        .filter(
            Order.order_rid.like(f"%{order_search}%"),
            Customer.customer_name.like(f"%{customer_search}%"),
            Shoe.shoe_rid.like(f"%{shoe_rid_search}%"),
        )
    )

    if order_status == 1:
        # Subquery to find OrderShoe IDs with any status > status_value
        matching_shoes_subquery = (
            db.session.query(OrderShoe.order_shoe_id)
            .join(
                OrderShoeStatus,
                OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id,
            )
            .filter(OrderShoeStatus.current_status > status_value)
            .distinct()
            .subquery()
        )

        # Count distinct orders related to the matching shoes
        total_orders = (
            base_query.filter(OrderShoe.order_shoe_id.in_(matching_shoes_subquery))
            .distinct(Order.order_id)
            .count()
        )
    else:
        # Count distinct orders in the default case
        total_orders = base_query.distinct(Order.order_id).count()

    # Calculate the total number of pages
    total_pages = math.ceil(total_orders / 10)

    return jsonify({"totalOrders": total_orders, "totalPages": total_pages})


@order_bp.route("/order/getactiveorders", methods=["GET"])
def get_active_orders():
    response = (
        db.session.query(Order, OrderStatus)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .filter(OrderStatus.order_current_status <= IN_PRODUCTION_ORDER_NUMBER)
        .all()
    )
    res = []
    for row in response:
        order, order_status = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderStatus": order_status.order_current_status,
        }
        res.append(obj)
    return res


@order_bp.route("/order/getactiveordershoes", methods=["GET"])
def get_active_order_shoes():
    response = (
        db.session.query(Order, OrderStatus, OrderShoe, Shoe)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(OrderStatus.order_current_status >= IN_PRODUCTION_ORDER_NUMBER)
        .order_by(Order.order_rid.asc())
        .all()
    )
    res = []
    for row in response:
        order, order_status, order_shoe, shoe = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderStatus": order_status.order_current_status,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
        }
        res.append(obj)
    return res


@order_bp.route("/order/gettechnicalconfirmstatus", methods=["GET"])
def get_technical_confirm_status():
    order_id = request.args.get("orderid")
    order_shoe_status = (
        db.session.query(Order, OrderShoe, OrderShoeStatus)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(Order.order_id == order_id)
        .all()
    )
    for order, order_shoe, order_shoe_status in order_shoe_status:
        if order_shoe_status.current_status == 9:
            return jsonify(
                {"status": "鞋型辅料材料规格尚未由技术部确认，请谨慎生成采购订单！"}
            )
    return jsonify({"status": "鞋型辅料材料规格已由技术部确认！"})


@order_bp.route("/order/exportorder", methods=["GET"])
def export_order():
    output_type = request.args.get("outputType", type=int)
    order_ids = request.args.get("orderIds").split(",")

    # 获取订单与 batch_info_type 映射
    order_batch_type_map = dict(
        db.session.query(Order.order_id, Order.batch_info_type_id)
        .filter(Order.order_id.in_(order_ids))
        .all()
    )

    # 获取所有唯一的 batch_info_type_id
    batch_info_type_ids = list(set(filter(None, order_batch_type_map.values())))
    batch_info_types = (
        db.session.query(BatchInfoType)
        .filter(BatchInfoType.batch_info_type_id.in_(batch_info_type_ids))
        .all()
    )

    # 构建 batch_info_type_id => 尺码名列表映射
    batch_size_names_map = {}
    for bit in batch_info_types:
        batch_size_names_map[bit.batch_info_type_id] = [
            getattr(bit, f"size_{i+34}_name") for i in range(len(SHOESIZERANGE))
        ]

    response = (
        db.session.query(
            Order,
            OrderShoe,
            Shoe,
            OrderShoeType,
            ShoeType,
            OrderShoeBatchInfo,
            PackagingInfo,
            Color,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id,
        )
        .join(Color, Color.color_id == ShoeType.color_id)
        .filter(Order.order_id.in_(order_ids))
        .all()
    )

    order_shoe_mapping = {}

    for row in response:
        (
            order,
            order_shoe,
            shoe,
            order_shoe_type,
            shoe_type,
            order_shoe_batch_info,
            packaging_info,
            color,
        ) = row

        current_batch_type_id = order_batch_type_map.get(order.order_id)
        size_names = batch_size_names_map.get(current_batch_type_id, [])

        obj = {
            "packagingInfoName": packaging_info.packaging_info_name,
            "packagingInfoLocale": packaging_info.packaging_info_locale,
            "totalQuantityRatio": packaging_info.total_quantity_ratio,
            "count": order_shoe_batch_info.packaging_info_quantity,
            "sizeNames": size_names,
        }

        for i in range(len(SHOESIZERANGE)):
            obj[f"size{SHOESIZERANGE[i]}Ratio"] = getattr(
                packaging_info, f"size_{i+34}_ratio"
            )

        shoe_meta_data = {
            "color": color.color_name,
            "colorName": order_shoe_type.customer_color_name,
            "imgUrl": shoe_type.shoe_image_url,
            "unitPrice": order_shoe_type.unit_price,
            "packagingInfo": [obj],
        }

        if order_shoe.order_shoe_id not in order_shoe_mapping:
            order_shoe_mapping[order_shoe.order_shoe_id] = {
                "orderRId": order.order_rid,
                "customerProductName": order_shoe.customer_product_name,
                "shoeRId": shoe.shoe_rid,
                "shoes": [shoe_meta_data],
                "remark": (order_shoe.business_technical_remark or "") + (order_shoe.business_material_remark or ""),
                "currencyType": order_shoe_type.currency_type,
            }
        else:
            order_shoe_mapping[order_shoe.order_shoe_id]["shoes"].append(shoe_meta_data)

    # 构建 meta_data（备用用作整体字段）
    meta_data = {
        "batchSizeNames": batch_size_names_map  # 如果你后续也需要在模板中用
    }

    template_path = os.path.join(FILE_STORAGE_PATH, "订单模板.xlsx")
    first_order = db.session.query(Order).filter(Order.order_id == order_ids[0]).first()
    order_rid = first_order.order_rid if first_order else "未知订单"
    send_name = f"导出订单_{order_rid}.xlsx"
    timestamp = str(time.time())

    if output_type == 0:
        new_file_name = f"导出配码订单_{timestamp}.xlsx"
        send_name = f"导出配码订单_{order_rid}.xlsx"
        new_file_path = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出配码订单", new_file_name)
        generate_excel_file(template_path, new_file_path, order_shoe_mapping, meta_data)
    else:
        new_file_name = f"导出数量订单_{timestamp}.xlsx"
        send_name = f"导出数量订单_{order_rid}.xlsx"
        new_file_path = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出数量订单", new_file_name)
        generate_amount_excel_file(template_path, new_file_path, order_shoe_mapping, meta_data)

    return send_file(new_file_path, as_attachment=True, download_name=send_name)


@order_bp.route("/order/exportproductionorder", methods=["GET"])
def export_production_order():
    output_type = request.args.get("outputType", type=int)
    order_ids = request.args.get("orderIds").split(",")
    include_price = request.args.get("includePrice", default=1, type=int)
    include_price = bool(include_price)
    response = (
        db.session.query(
            Order,
            Customer,
            OrderShoe,
            Shoe,
            OrderShoeType,
            ShoeType,
            OrderShoeBatchInfo,
            PackagingInfo,
            Color
        )
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id,
        )
        .join(
            Color, Color.color_id == ShoeType.color_id
        )
        .filter(Order.order_id.in_(order_ids))
        .all()
    )
    order_shoe_mapping = {}
    for row in response:
        (
            order,
            customer,
            order_shoe,
            shoe,
            order_shoe_type,
            shoe_type,
            order_shoe_batch_info,
            packaging_info,
            color
            
        ) = row
        if order_shoe.order_shoe_id not in order_shoe_mapping:
            order_shoe_mapping[order_shoe.order_shoe_id] = {
                "orderRId": order.order_rid,
                "customerProductName": order_shoe.customer_product_name,
                "shoeRId": shoe.shoe_rid,
                "shoes": [],
                "remark": order_shoe.business_technical_remark + order_shoe.business_material_remark,
                "orderStartDate": order.start_date.strftime("%Y-%m-%d") if order.start_date else "N/A",
                "orderEndDate": order.end_date.strftime("%Y-%m-%d") if order.end_date else "N/A",
                "orderCId": order.order_cid,
                "title": f"健诚集团{customer.customer_name}号客人{customer.customer_brand}生产订单",
                "currencyType": order_shoe_type.currency_type
            }
            shoe_meta_data = {
                "color": color.color_name,
                "colorName": order_shoe_type.customer_color_name,
                "imgUrl": shoe_type.shoe_image_url,
                "unitPrice": order_shoe_type.unit_price,
                "packagingInfo": [],
            }
            obj = {
                "packagingInfoName": packaging_info.packaging_info_name,
                "packagingInfoLocale": packaging_info.packaging_info_locale,
                "totalQuantityRatio": packaging_info.total_quantity_ratio,
                "count": order_shoe_batch_info.packaging_info_quantity,
            }
            for i in range(len(SHOESIZERANGE)):
                obj[f"size{SHOESIZERANGE[i]}Ratio"] = getattr(
                    packaging_info, f"size_{i+34}_ratio"
                )
            shoe_meta_data["packagingInfo"].append(obj)
            order_shoe_mapping[order_shoe.order_shoe_id]["shoes"].append(shoe_meta_data)
        else:
            shoe_meta_data = {
                "color": color.color_name,
                "colorName": order_shoe_type.customer_color_name,
                "imgUrl": shoe_type.shoe_image_url,
                "unitPrice": order_shoe_type.unit_price,
                "packagingInfo": [],
            }
            obj = {
                "packagingInfoName": packaging_info.packaging_info_name,
                "packagingInfoLocale": packaging_info.packaging_info_locale,
                "totalQuantityRatio": packaging_info.total_quantity_ratio,
                "count": order_shoe_batch_info.packaging_info_quantity,
            }
            for i in range(len(SHOESIZERANGE)):
                obj[f"size{SHOESIZERANGE[i]}Ratio"] = getattr(
                    packaging_info, f"size_{i+34}_ratio"
                )
            shoe_meta_data["packagingInfo"].append(obj)
            order_shoe_mapping[order_shoe.order_shoe_id]["shoes"].append(shoe_meta_data)
    shoe_size_names = (
        db.session.query(BatchInfoType)
        .join(Order, Order.batch_info_type_id == BatchInfoType.batch_info_type_id)
        .filter(Order.order_id == order_ids[0])
        .first()
    )
    meta_data = {"sizeNames": []}
    # add size_name of batch info type
    for i in range(len(SHOESIZERANGE)):
        meta_data["sizeNames"].append(getattr(shoe_size_names, f"size_{i+34}_name"))
    template_path = os.path.join(FILE_STORAGE_PATH, "生产订单模板.xlsx")
    first_order = db.session.query(Order).filter(Order.order_id == order_ids[0]).first()
    order_rid = first_order.order_rid if first_order else "未知订单"
    send_name = f"导出生产订单_{order_rid}.xlsx"
    if output_type == 0:
        timestamp = str(time.time())
        new_file_name = f"导出配码生产订单_{timestamp}.xlsx"
        send_name = f"导出配码生产订单_{order_rid}.xlsx"
        new_file_path = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出配码生产订单", new_file_name)
        generate_production_excel_file(
            template_path,
            new_file_path,
            order_shoe_mapping,
            meta_data,
            include_price=include_price,
        )
    else:
        timestamp = str(time.time())
        new_file_name = f"导出数量生产订单_{timestamp}.xlsx"
        send_name = f"导出数量生产订单_{order_rid}.xlsx"
        new_file_path = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出数量生产订单", new_file_name)
        generate_production_amount_excel_file(
            template_path,
            new_file_path,
            order_shoe_mapping,
            meta_data,
            include_price=include_price,
        )
    return send_file(new_file_path, as_attachment=True, download_name=send_name)


@order_bp.route("/order/downloadpackagingdoc", methods=["GET"])
def download_packaging_doc():
    order_id = request.args.get("orderId", type=int)
    if not order_id:
        return jsonify({"message": "orderId is required"}), 400

    order_entity = db.session.query(Order).filter(Order.order_id == order_id).first()
    if not order_entity:
        return jsonify({"message": "order not found"}), 404

    packaging_doc = _locate_packaging_doc(order_entity.order_rid)
    if not packaging_doc:
        return jsonify({"message": "包装资料不存在"}), 404

    return send_file(
        packaging_doc["path"],
        as_attachment=True,
        download_name=packaging_doc.get("file_name", os.path.basename(packaging_doc["path"]))
    )


@order_bp.route("/order/uploadpackagingdoc", methods=["POST"])
def upload_packaging_doc():
    if "file" not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    order_id = request.form.get("orderId", type=int)
    if not order_id:
        return jsonify({"message": "orderId is required"}), 400

    order_entity = db.session.query(Order).filter(Order.order_id == order_id).first()
    if not order_entity:
        return jsonify({"message": "order not found"}), 404

    ext = os.path.splitext(uploaded_file.filename)[1].lower()
    if ext not in [".xlsx", ".xls", ".pdf"]:
        return jsonify({"message": "仅支持 xlsx、xls 或 pdf 格式的包装资料"}), 400

    target_dir = os.path.join(FILE_STORAGE_PATH, "业务部文件", order_entity.order_rid)
    os.makedirs(target_dir, exist_ok=True)

    # 删除已有的包装资料（含不同扩展名及历史遗留路径），避免下载时命中旧文件
    for base_dir in [
        target_dir,
        os.path.join(FILE_STORAGE_PATH, order_entity.order_rid),  # legacy fallback
    ]:
        for name in PACKAGING_DOC_CANDIDATES:
            old_path = os.path.join(base_dir, name)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError as e:
                    logger.debug(e)

    target_file_path = os.path.join(target_dir, f"包装资料{ext}")
    uploaded_file.save(target_file_path)
    return jsonify({"message": "包装资料替换成功"}), 200


@order_bp.route("/order/approveoutboundbybusiness", methods=["PATCH"])
def approve_outbound_by_business():
    order_ids = request.get_json()
    character, staff, department = current_user_info()
    staff_id = staff.staff_id
    db.session.query(Order).filter(
        Order.order_id.in_(order_ids), Order.is_outbound_allowed != 2
    ).update({Order.is_outbound_allowed: 1}, synchronize_session=False)
    try:
        processor: EventProcessor = current_app.config["event_processor"]
        events = []
        for order_id in order_ids:
            for operation in [18, 19, 20, 21, 22, 23, 24, 25, 26, 27]:
                event = Event(
                    staff_id=staff_id,
                    handle_time=datetime.now(),
                    operation_id=operation,
                    event_order_id=order_id,
                )
                processor.processEvent(event)
                events.append(event)
        db.session.add_all(events)
    except Exception as e:
        logger.debug(e)
        return jsonify({"message": "failed"}), 400
    db.session.commit()
    return jsonify({"message": "批准成功"}), 200


@order_bp.route("/order/approveoutboundbygeneralmanager", methods=["PATCH"])
def approve_outbound_by_general_manager():
    order_ids = request.get_json()
    character, staff, department = current_user_info()
    staff_id = staff.staff_id
    db.session.query(Order).filter(
        Order.order_id.in_(order_ids), Order.is_outbound_allowed != 2
    ).update({Order.is_outbound_allowed: 2}, synchronize_session=False)
    try:
        processor: EventProcessor = current_app.config["event_processor"]
        events = []
        for order_id in order_ids:
            for operation in [28, 29]:
                event = Event(
                    staff_id=staff_id,
                    handle_time=datetime.now(),
                    operation_id=operation,
                    event_order_id=order_id,
                )
                processor.processEvent(event)
                events.append(event)
        db.session.add_all(events)
    except Exception as e:
        logger.debug(e)
        return jsonify({"message": "failed"}), 400
    db.session.commit()
    return jsonify({"message": "批准成功"}), 200


@order_bp.route("/order/getordershoetypeeditinfo", methods=["GET"])
def get_order_shoe_type_edit_info():
    """获取订单下每个鞋型的可编辑信息（颜色、客户型号、客户颜色、单价、币种、数量）"""
    order_id = request.args.get("orderId", type=int)
    if not order_id:
        return jsonify({"message": "缺少orderId参数"}), 400

    order = db.session.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return jsonify({"message": "订单不存在"}), 404

    customer = (
        db.session.query(Customer)
        .filter(Customer.customer_id == order.customer_id)
        .first()
    )

    order_shoes = (
        db.session.query(OrderShoe, Shoe)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(OrderShoe.order_id == order_id)
        .all()
    )

    result_shoes = []
    for order_shoe, shoe in order_shoes:
        shoe_types = (
            db.session.query(OrderShoeType, ShoeType, Color)
            .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
            .join(Color, Color.color_id == ShoeType.color_id)
            .filter(OrderShoeType.order_shoe_id == order_shoe.order_shoe_id)
            .all()
        )
        shoe_type_list = []
        for ost, shoe_type, color in shoe_types:
            batch_infos = (
                db.session.query(OrderShoeBatchInfo)
                .filter(
                    OrderShoeBatchInfo.order_shoe_type_id == ost.order_shoe_type_id
                )
                .all()
            )
            batch_list = []
            for b in batch_infos:
                batch_obj = {
                    "orderShoeBatchInfoId": b.order_shoe_batch_info_id,
                    "name": b.name,
                    "totalAmount": b.total_amount or 0,
                    "totalPrice": float(b.total_price) if b.total_price is not None else 0,
                }
                for i in range(34, 47):
                    batch_obj[f"size{i}Amount"] = getattr(b, f"size_{i}_amount") or 0
                batch_list.append(batch_obj)
            shoe_type_list.append(
                {
                    "orderShoeTypeId": ost.order_shoe_type_id,
                    "colorId": color.color_id,
                    "colorName": color.color_name,
                    "customerColorName": ost.customer_color_name or "",
                    "unitPrice": float(ost.unit_price) if ost.unit_price is not None else 0,
                    "currencyType": ost.currency_type or "",
                    "shoeImageUrl": (
                        IMAGE_STORAGE_PATH + shoe_type.shoe_image_url
                        if shoe_type.shoe_image_url
                        else None
                    ),
                    "batchInfoList": batch_list,
                }
            )
        result_shoes.append(
            {
                "orderShoeId": order_shoe.order_shoe_id,
                "shoeId": shoe.shoe_id,
                "shoeRid": shoe.shoe_rid,
                "customerProductName": order_shoe.customer_product_name or "",
                "shoeTypes": shoe_type_list,
            }
        )

    return jsonify(
        {
            "orderId": order.order_id,
            "orderRid": order.order_rid,
            "customerName": customer.customer_name if customer else "",
            "packagingDocExists": _locate_packaging_doc(order.order_rid) is not None,
            "orderShoes": result_shoes,
        }
    )


def _resolve_shoe_type_image_for_color(shoe_id, new_color_id):
    """按新颜色推导鞋型图片路径。

    鞋型图片按颜色存放（shoe/{标识}/{颜色名}/shoe_image.jpg）。参考同款鞋型任一
    带图片的兄弟记录来学习路径规则，将颜色目录替换为新颜色名。仅当新颜色的图片
    在图片服务器上确实存在时才返回该路径，否则返回 None（留空，等待后续上传）。
    """
    new_color = (
        db.session.query(Color).filter(Color.color_id == new_color_id).first()
    )
    if not new_color:
        return None
    sibling = (
        db.session.query(ShoeType)
        .filter(
            ShoeType.shoe_id == shoe_id,
            ShoeType.shoe_image_url.isnot(None),
            ShoeType.shoe_image_url != "",
        )
        .first()
    )
    if not sibling:
        return None
    parts = sibling.shoe_image_url.replace("\\", "/").split("/")
    # 期望形如 shoe/{标识}/{颜色名}/shoe_image.jpg
    if len(parts) < 4:
        return None
    parts[2] = new_color.color_name
    candidate = "/".join(parts)
    if os.path.exists(os.path.join(IMAGE_UPLOAD_PATH, candidate)):
        return candidate
    return None


@order_bp.route("/order/updateordershoetypeeditinfo", methods=["POST"])
def update_order_shoe_type_edit_info():
    """更新订单鞋型信息（客户型号、颜色、客户颜色、单价、币种、数量）。

    修改颜色时不会直接改动共享的 shoe_type 记录，而是为该鞋型定位/新建
    对应颜色的 shoe_type 并改变 order_shoe_type 的指向，从而避免影响其他订单。

    注意路径变化：
    - 图片服务器（IMAGE_UPLOAD_PATH / IMAGE_STORAGE_PATH）上鞋型图片是按颜色存放的，
      路径形如 shoe/{标识}/{颜色名}/shoe_image.jpg。新建颜色对应的 shoe_type 时不能
      沿用旧颜色的图片路径，需按新颜色名推导，且仅当图片实际存在时才引用，否则留空。
    - 文件服务器（FILE_STORAGE_PATH）上的订单文件按 {order_id}/{shoe_rid} 组织，与颜色无关，
      因此修改颜色不涉及订单文件目录的迁移。
    """
    data = request.get_json() or {}
    order_shoe_updates = data.get("orderShoes", [])
    shoe_type_updates = data.get("shoeTypes", [])

    try:
        # 1) 更新客户型号（order_shoe 为订单私有，不会影响其他订单）
        for item in order_shoe_updates:
            order_shoe_id = item.get("orderShoeId")
            if order_shoe_id is None:
                continue
            order_shoe = (
                db.session.query(OrderShoe)
                .filter(OrderShoe.order_shoe_id == order_shoe_id)
                .first()
            )
            if not order_shoe:
                continue
            if "customerProductName" in item:
                order_shoe.customer_product_name = item.get("customerProductName") or ""

        # 预先校验：同一 order_shoe 内不能出现重复颜色
        planned_colors = {}
        ost_cache = {}
        for st in shoe_type_updates:
            ost_id = st.get("orderShoeTypeId")
            if ost_id is None:
                continue
            ost = (
                db.session.query(OrderShoeType)
                .filter(OrderShoeType.order_shoe_type_id == ost_id)
                .first()
            )
            if not ost:
                continue
            ost_cache[ost_id] = ost
            current_shoe_type = (
                db.session.query(ShoeType)
                .filter(ShoeType.shoe_type_id == ost.shoe_type_id)
                .first()
            )
            target_color = st.get("colorId")
            if target_color is None:
                target_color = current_shoe_type.color_id if current_shoe_type else None
            used_colors = planned_colors.setdefault(ost.order_shoe_id, set())
            if target_color in used_colors:
                return jsonify({"message": "同一鞋型下存在重复的颜色，请检查"}), 400
            used_colors.add(target_color)

        # 2) 更新每个鞋型的信息
        affected_ost_ids = set()  # 记录数量发生变化的鞋型，稍后同步入库预计数量
        for st in shoe_type_updates:
            ost_id = st.get("orderShoeTypeId")
            ost = ost_cache.get(ost_id)
            if not ost:
                continue

            if "customerColorName" in st:
                ost.customer_color_name = st.get("customerColorName") or ""
            if "currencyType" in st:
                ost.currency_type = st.get("currencyType") or ""
            if "unitPrice" in st and st.get("unitPrice") is not None:
                try:
                    ost.unit_price = Decimal(str(st.get("unitPrice")))
                except (InvalidOperation, ValueError):
                    return jsonify({"message": "单价格式不正确"}), 400

            # 处理颜色修改：定位/新建对应颜色的 shoe_type，避免修改共享记录
            new_color_id = st.get("colorId")
            if new_color_id is not None:
                current_shoe_type = (
                    db.session.query(ShoeType)
                    .filter(ShoeType.shoe_type_id == ost.shoe_type_id)
                    .first()
                )
                if current_shoe_type and new_color_id != current_shoe_type.color_id:
                    shoe_id = current_shoe_type.shoe_id
                    target_shoe_type = (
                        db.session.query(ShoeType)
                        .filter(
                            ShoeType.shoe_id == shoe_id,
                            ShoeType.color_id == new_color_id,
                        )
                        .first()
                    )
                    if not target_shoe_type:
                        # 图片按颜色存放，新建颜色不能沿用旧颜色的图片路径，
                        # 需按新颜色名推导并校验图片是否存在，否则留空等待上传。
                        new_image_url = _resolve_shoe_type_image_for_color(
                            shoe_id, new_color_id
                        )
                        target_shoe_type = ShoeType(
                            shoe_id=shoe_id,
                            color_id=new_color_id,
                            shoe_image_url=new_image_url,
                        )
                        db.session.add(target_shoe_type)
                        db.session.flush()
                    ost.shoe_type_id = target_shoe_type.shoe_type_id

            # 3) 更新数量并重算金额
            unit_price = ost.unit_price or Decimal("0")
            for batch in st.get("batchInfoList", []):
                batch_id = batch.get("orderShoeBatchInfoId")
                if batch_id is None:
                    continue
                b = (
                    db.session.query(OrderShoeBatchInfo)
                    .filter(OrderShoeBatchInfo.order_shoe_batch_info_id == batch_id)
                    .first()
                )
                if not b:
                    continue
                size_provided = False
                size_total = 0
                for i in range(34, 47):
                    key = f"size{i}Amount"
                    if key in batch:
                        size_provided = True
                        val = int(batch.get(key) or 0)
                        setattr(b, f"size_{i}_amount", val)
                        size_total += val
                if size_provided:
                    b.total_amount = size_total
                elif "totalAmount" in batch:
                    b.total_amount = int(batch.get("totalAmount") or 0)
                b.total_price = unit_price * (b.total_amount or 0)
                affected_ost_ids.add(ost.order_shoe_type_id)

        # 4) 同步入库预计数量：成品/半成品入库的预计数量按鞋型下所有批次汇总，
        #    修改订单数量后必须同步更新，否则入库时的预计数量会与实际订单不一致。
        _sync_estimated_inbound_amounts(affected_ost_ids)

        db.session.commit()
        return jsonify({"message": "修改成功"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新订单鞋型信息失败: {e}")
        return jsonify({"message": "修改失败"}), 500


def _sync_estimated_inbound_amounts(order_shoe_type_ids):
    """按鞋型重新汇总各尺码数量，并同步更新成品/半成品入库的预计数量。

    成品仓（FinishedShoeStorage）与半成品仓（SemifinishedShoeStorage）中的预计入库
    数量（finished_estimated_amount / semifinished_estimated_amount 及各尺码预计数量）
    是排期时按该鞋型下所有批次数量汇总得到的。当订单数量被修改后，这里按相同规则
    重新汇总并回写，保证入库时的预计数量与订单数量一致。仅当对应库存记录已存在时更新。
    """
    for ost_id in order_shoe_type_ids:
        if ost_id is None:
            continue
        # 汇总该鞋型下所有批次的总数量与各尺码数量
        batches = (
            db.session.query(OrderShoeBatchInfo)
            .filter(OrderShoeBatchInfo.order_shoe_type_id == ost_id)
            .all()
        )
        total_amount = 0
        size_totals = {i: 0 for i in range(34, 47)}
        for b in batches:
            total_amount += b.total_amount or 0
            for i in range(34, 47):
                size_totals[i] += getattr(b, f"size_{i}_amount") or 0

        finished_storage = (
            db.session.query(FinishedShoeStorage)
            .filter(FinishedShoeStorage.order_shoe_type_id == ost_id)
            .first()
        )
        if finished_storage:
            finished_storage.finished_estimated_amount = total_amount
            for i in range(34, 47):
                setattr(
                    finished_storage, f"size_{i}_estimated_amount", size_totals[i]
                )

        semifinished_storage = (
            db.session.query(SemifinishedShoeStorage)
            .filter(SemifinishedShoeStorage.order_shoe_type_id == ost_id)
            .first()
        )
        if semifinished_storage:
            semifinished_storage.semifinished_estimated_amount = total_amount
            for i in range(34, 47):
                setattr(
                    semifinished_storage, f"size_{i}_estimated_amount", size_totals[i]
                )

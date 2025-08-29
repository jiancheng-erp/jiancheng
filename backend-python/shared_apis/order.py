from numpy import character
import constants
import time
from app_config import db
from flask import Blueprint, jsonify, request, send_file, current_app
from sqlalchemy import func
from api_utility import to_snake, to_camel
from login.login import current_user, current_user_info
import math
import os
from datetime import datetime
from event_processor import EventProcessor

from constants import IN_PRODUCTION_ORDER_NUMBER, SHOESIZERANGE, BUSINESS_DEPARTMENT, ORDER_FINISH_SYMBOL
from general_document.order_export import (
    generate_excel_file,
    generate_amount_excel_file,
)
from general_document.production_order_export import (
    generate_production_excel_file,
    generate_production_amount_excel_file,
)
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH
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


# 面料计算，一次bom填写
USAGE_CALCULATION_ORDER_SHOE_STATUS = 4
# 面料计算文员角色码
USAGE_CALCULATION_ROLE = 18
# 面料计算部门码

# 工艺单
CRAFT_SHEET_ORDER_SHOE_STATUS = 9
# 面料计算文员角色码
TECH_DEPARTMENT_MANAGER = 5


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
            .order_by(Order.start_date.asc())
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
            .order_by(Order.start_date.asc())
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
            .order_by(Order.start_date.asc())
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
            .order_by(Order.start_date.asc())
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
        .order_by(Order.start_date.asc())
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
        "batchInfoTypeName": entity.BatchInfoType.batch_info_type_name,
        "batchInfoType": batch_info_type_response,
        "orderStaffName": entity.Staff.staff_name,
        "dateInfo": formatted_start_date + " —— " + formatted_end_date,
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
    if entity.Order.production_list_upload_status == "2":
        result["wrapRequirementUploadStatus"] = "已上传包装文件"
    else:
        result["wrapRequirementUploadStatus"] = "未上传包装文件"
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
                response_order_shoe["shoeTypeBatchInfoList"].append(temp_obj)

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

    # --- 订单状态维度（进行中 <16 / 历史 >=16） ---
    is_history = bool(history_status)
    if is_history:
        q = q.filter(OrderStatus.order_current_status >= ORDER_FINISH_SYMBOL)
    else:
        q = q.filter(OrderStatus.order_current_status < ORDER_FINISH_SYMBOL)

    entities = q.order_by(Order.order_rid.asc()).all()

    # --- 部门人员映射（避免 KeyError 用 get） ---
    department_staff = (
        db.session.query(Staff)
        .filter_by(department_id=BUSINESS_DEPARTMENT)
        .all()
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
            "customerProductName": order_shoe.customer_product_name,
            "shoeRId": shoe.shoe_rid,
            "orderRid": order.order_rid,
            "orderCid": order.order_cid,
            "customerName": customer.customer_name,
            "customerBrand": customer.customer_brand,
            "orderStartDate": formatted_start_date,
            "orderEndDate": formatted_end_date,
            "orderStatus": order_status_message,
            "orderStatusVal": order_status.order_current_status if order_status else None,
            "orderSalesman": id_to_name.get(order.salesman_id, ""),
            "orderSupervisor": id_to_name.get(order.supervisor_id, ""),
        })

    return jsonify(result)

@order_bp.route("/order/checkorderridexists", methods=["GET"])
def check_order_rid_exists():
    order_rid = request.args.get("pendingRid")
    pending_exists = db.session.query(Order).filter(Order.order_rid == order_rid).first()
    if pending_exists:
        return jsonify({"result":"订单号已存在", "exists":True}), 200
    else:
        return jsonify({"result":"订单号未占用", "exists":False}), 200

# TODO delete
@order_bp.route("/order/getallorders", methods=["GET"])
def get_all_orders():
    desc_symbol = request.args.get("descSymbol", None)
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
    )
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
                "customerProductName": order_shoe.customer_product_name,
                "shoeRId": shoe.shoe_rid,
                "orderRid": order.order_rid,
                "orderCid": order.order_cid,
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
            }
        )
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
        for file_name in os.listdir(order_local_path):
            file_path = os.path.join(order_local_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                os.rmdir(file_path)
        os.rmdir(order_local_path)
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
        )
        .join(OrderStatus, Order.order_id == OrderStatus.order_id)
        .join(
            OrderStatusReference,
            OrderStatus.order_current_status == OrderStatusReference.order_status_id,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(
            order_shoe_status,
            OrderShoe.order_shoe_id == order_shoe_status.c.order_shoe_id,
        )
        .join(
            order_shoe_status_reference,
            OrderShoe.order_shoe_id == order_shoe_status_reference.c.order_shoe_id,
        )
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(
            Order.order_rid.like(f"%{order_search}%"),
            Customer.customer_name.like(f"%{customer_search}%"),
            Shoe.shoe_rid.like(f"%{shoe_rid_search}%"),
            OrderShoe.customer_product_name.like(f"%{shoe_cid_search}%"),
            Order.order_cid.like(f"%{order_cid_search}%"),
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

    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()

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
            }

        # Use a unique key for each shoe to avoid duplicates
        shoe_key = order_shoe.order_shoe_id if order_shoe else "N/A"

        if shoe_key not in orders_dict[order.order_id]["shoes"]:
            purchase_status_string = ""
            if order_status_reference.order_status_name == "生产订单创建":
                purchase_status_string = "业务部正在处理中"
            else:
                if "一次采购入库" in order_shoe_status_reference_names:
                    purchase_status_string += "一次采购已完成, 等待入库 | "
                if "二次采购入库" in order_shoe_status_reference_names:
                    purchase_status_string += "二次采购已完成，等待入库 | "
                if "投产指令单创建" in order_shoe_status_reference_names or "面料单位用量计算" in order_shoe_status_reference_names:
                    purchase_status_string += "技术部正在处理中 | "
                if "一次采购订单创建" in order_shoe_status_reference_names:
                    purchase_status_string += "物控经理正在处理中 | "
                if "总仓采购订单创建" in order_shoe_status_reference_names:
                    purchase_status_string += "总仓经理正在处理中 | "
                
            # Prepare shoe information for the first occurrence
            orders_dict[order.order_id]["shoes"][shoe_key] = {
                "shoeRid": shoe.shoe_rid if shoe else "N/A",
                "customerId": order_shoe.customer_product_name if order_shoe else "N/A",
                "firstBom": "N/A",
                "secondBom": "N/A",
                "firstOrder": "N/A",
                "secondOrder": "N/A",
                "statuses": "".join(
                    order_shoe_status_reference_names.split(" | ")
                ),  # To hold the combined statuses as a string
                "purchaseStatus": purchase_status_string.strip(" | "),  # Clean up trailing separator
                "bussinessEventTime": "N/A",
                "productionOrderIssueEventTime": "N/A",
                "firstUsageInputIssueEventTime": "N/A",
                "firstPurchaseOrderIssueEventTime": "N/A",
                "secondPurchaseOrderIssueEventTime": "N/A",
            }

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
        print(order_id)
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
    timestamp = str(time.time())

    if output_type == 0:
        new_file_name = f"导出配码订单_{timestamp}.xlsx"
        new_file_path = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出配码订单", new_file_name)
        generate_excel_file(template_path, new_file_path, order_shoe_mapping, meta_data)
    else:
        new_file_name = f"导出数量订单_{timestamp}.xlsx"
        new_file_path = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出数量订单", new_file_name)
        generate_amount_excel_file(template_path, new_file_path, order_shoe_mapping, meta_data)

    return send_file(new_file_path, as_attachment=True, download_name=new_file_name)


@order_bp.route("/order/exportproductionorder", methods=["GET"])
def export_production_order():
    output_type = request.args.get("outputType", type=int)
    order_ids = request.args.get("orderIds").split(",")
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
    if output_type == 0:
        timestamp = str(time.time())
        new_file_name = f"导出配码生产订单_{timestamp}.xlsx"
        new_file_path = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出配码生产订单", new_file_name)
        generate_production_excel_file(template_path, new_file_path, order_shoe_mapping, meta_data)
    else:
        timestamp = str(time.time())
        new_file_name = f"导出数量生产订单_{timestamp}.xlsx"
        new_file_path = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出数量生产订单", new_file_name)
        generate_production_amount_excel_file(
            template_path, new_file_path, order_shoe_mapping, meta_data
        )
    return send_file(new_file_path, as_attachment=True, download_name=new_file_name)


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

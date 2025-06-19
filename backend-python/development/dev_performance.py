from flask import Blueprint, jsonify, request, send_file, current_app
import os
import datetime
from app_config import db
from models import *
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from api_utility import randomIdGenerater
from general_document.prodution_instruction import generate_instruction_excel_file
import json
from constants import DEFAULT_SUPPLIER
from wechat_api.send_message_api import send_massage_to_users
from logger import logger
from login.login import current_user, current_user_info
from sqlalchemy import func, case, distinct, or_

dev_performance_bp = Blueprint("dev_performance", __name__)


@dev_performance_bp.route("/devproductionorder/getalldesigners", methods=["GET"])
def get_all_designers():
    _, _, department = current_user_info()
    user_department = department.department_name

    # 空值转换为“设计师信息空缺”
    designer_group = case(
        (func.ifnull(Shoe.shoe_designer, "") == "", "设计师信息空缺"),
        else_=Shoe.shoe_designer,
    )

    # 联表统计
    results = (
        db.session.query(
            designer_group.label("designer"),
            Shoe.shoe_department_id.label("department"),
            func.count(distinct(Order.order_id)).label("totalOrderCount"),
            func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label("totalShoeCountBussiness"),
            func.coalesce(func.sum(FinishedShoeStorage.finished_actual_amount), 0).label("totalShoeCountProduct"),
        )
        .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .outerjoin(OrderShoeBatchInfo, OrderShoeType.order_shoe_type_id == OrderShoeBatchInfo.order_shoe_type_id)
        .outerjoin(FinishedShoeStorage, OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id)
        .filter(Shoe.shoe_department_id == user_department)
        .group_by(designer_group, Shoe.shoe_department_id)
        .all()
    )

    # 构造返回结构
    designer_list = []
    for row in results:
        designer_list.append({
            "designer": row.designer,
            "department": row.department,
            "totalOrderCount": row.totalOrderCount,
            "totalShoeCountBussiness": row.totalShoeCountBussiness,
            "totalShoeCountProduct": row.totalShoeCountProduct
        })

    return jsonify({"status": "success", "data": designer_list}), 200



@dev_performance_bp.route("/devproductionorder/getallshoeswithadesigner", methods=["GET"])
def get_all_shoes_with_designer():
    from sqlalchemy import func, or_

    designer = request.args.get("designer")
    _, _, department = current_user_info()
    user_department = department.department_name

    if designer is None:
        return jsonify({"status": "error", "message": "Designer is required"}), 400

    if designer == "设计师信息空缺":
        designer_filter = or_(Shoe.shoe_designer == None, Shoe.shoe_designer == "")
    else:
        designer_filter = Shoe.shoe_designer == designer

    results = (
        db.session.query(
            Shoe.shoe_id,
            Shoe.shoe_rid,
            Shoe.shoe_designer,
            Shoe.shoe_department_id,
            ShoeType.shoe_type_id,
            ShoeType.color_id,
            Color.color_name,
            Order.order_id,
            Order.order_rid,
            Order.order_cid,
            Order.start_date,
            Order.end_date,
            Order.customer_id,
            Order.salesman_id,
            Order.supervisor_id,
            func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label("business_amount"),
            func.coalesce(func.sum(FinishedShoeStorage.finished_actual_amount), 0).label("product_amount"),
        )
        .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .join(OrderShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .outerjoin(OrderShoeBatchInfo, OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .outerjoin(FinishedShoeStorage, FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(designer_filter, Shoe.shoe_department_id == user_department)
        .group_by(
            Shoe.shoe_id,
            Shoe.shoe_rid,
            Shoe.shoe_designer,
            Shoe.shoe_department_id,
            ShoeType.shoe_type_id,
            ShoeType.color_id,
            Color.color_name,
            Order.order_id,
            Order.order_rid,
            Order.order_cid,
            Order.start_date,
            Order.end_date,
            Order.customer_id,
            Order.salesman_id,
            Order.supervisor_id
        )
        .all()
    )

    # 构建结构
    shoe_map = {}
    counted_pairs = set()

    for row in results:
        shoe_key = row.shoe_id
        color_key = row.shoe_type_id
        order_pair_key = (row.shoe_id, row.order_id)

        if shoe_key not in shoe_map:
            shoe_map[shoe_key] = {
                "shoeId": row.shoe_id,
                "shoeRid": row.shoe_rid,
                "shoeDesigner": row.shoe_designer or "",
                "shoeDepartment_id": row.shoe_department_id,
                "colors": {},
                "totalOrderCount": 0,
                "totalOrderCountColor": 0,
                "totalShoeCountBussiness": 0,
                "totalShoeCountProduct": 0,
            }

        if color_key not in shoe_map[shoe_key]["colors"]:
            shoe_map[shoe_key]["colors"][color_key] = {
                "shoeTypeId": row.shoe_type_id,
                "colorId": row.color_id,
                "colorName": row.color_name,
                "orders": []
            }

        # 附加订单信息
        shoe_map[shoe_key]["colors"][color_key]["orders"].append({
            "orderId": row.order_id,
            "orderRid": row.order_rid,
            "orderCid": row.order_cid,
            "startDate": row.start_date.strftime("%Y-%m-%d") if row.start_date else None,
            "endDate": row.end_date.strftime("%Y-%m-%d") if row.end_date else None,
            "customerId": row.customer_id,
            "salesmanId": row.salesman_id,
            "supervisorId": row.supervisor_id,
            "businessAmount": row.business_amount,
            "productAmount": row.product_amount
        })

        shoe_map[shoe_key]["totalOrderCountColor"] += 1

        if order_pair_key not in counted_pairs:
            counted_pairs.add(order_pair_key)
            shoe_map[shoe_key]["totalOrderCount"] += 1
            shoe_map[shoe_key]["totalShoeCountBussiness"] += row.business_amount
            shoe_map[shoe_key]["totalShoeCountProduct"] += row.product_amount

    # 整理为最终列表结构
    final_data = []
    for shoe in shoe_map.values():
        shoe["colors"] = list(shoe["colors"].values())
        final_data.append(shoe)

    return jsonify({"status": "success", "data": final_data}), 200




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

    designer_keyword = request.args.get("designer", "").strip()
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()
    year = request.args.get("year", "").strip()
    month = request.args.get("month", "").strip()

    # 子查询：每个 order_shoe_type_id 对应的总业务量
    batch_amount_subquery = (
        db.session.query(
            OrderShoeBatchInfo.order_shoe_type_id,
            func.sum(OrderShoeBatchInfo.total_amount).label("total_business_amount")
        )
        .group_by(OrderShoeBatchInfo.order_shoe_type_id)
        .subquery()
    )

    # 子查询：每个 order_shoe_type_id 对应的生产量，仅 team=2
    production_amount_subquery = (
        db.session.query(
            OrderShoeProductionAmount.order_shoe_type_id,
            func.sum(OrderShoeProductionAmount.total_production_amount).label("total_production_amount")
        )
        .filter(OrderShoeProductionAmount.production_team == 2)
        .group_by(OrderShoeProductionAmount.order_shoe_type_id)
        .subquery()
    )

    # 第一层：基础子查询，按 order_shoe_type 展开
    base_subquery = (
        db.session.query(
            case(
                (func.ifnull(Shoe.shoe_designer, "") == "", "设计师信息空缺"),
                else_=Shoe.shoe_designer
            ).label("designer"),
            Shoe.shoe_department_id.label("department"),
            Order.order_id.label("order_id"),
            func.coalesce(batch_amount_subquery.c.total_business_amount, 0).label("business_amount"),
            production_amount_subquery.c.total_production_amount.label("production_amount")
        )
        .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .outerjoin(batch_amount_subquery, batch_amount_subquery.c.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .outerjoin(production_amount_subquery, production_amount_subquery.c.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(Shoe.shoe_department_id == user_department)
    )

    # 时间与设计师筛选
    if designer_keyword:
        base_subquery = base_subquery.filter(Shoe.shoe_designer.like(f"%{designer_keyword}%"))
    if year:
        base_subquery = base_subquery.filter(func.year(Order.start_date) == int(year))
    elif month:
        base_subquery = base_subquery.filter(func.date_format(Order.start_date, "%Y-%m") == month)
    else:
        if start_date:
            base_subquery = base_subquery.filter(Order.start_date >= start_date)
        if end_date:
            base_subquery = base_subquery.filter(Order.start_date <= end_date)

    base_subquery = base_subquery.subquery()

    # 第二层：按设计师聚合
    final_query = (
        db.session.query(
            base_subquery.c.designer,
            base_subquery.c.department,
            func.count(distinct(base_subquery.c.order_id)).label("totalOrderCount"),
            func.sum(base_subquery.c.business_amount).label("totalShoeCountBussiness"),
            func.sum(
                case(
                    (base_subquery.c.production_amount != None, base_subquery.c.production_amount),
                    else_=base_subquery.c.business_amount
                )
            ).label("totalShoeCountProduct")
        )
        .group_by(base_subquery.c.designer, base_subquery.c.department)
    )

    results = final_query.all()

    response = [
        {
            "designer": row.designer,
            "department": row.department,
            "totalOrderCount": row.totalOrderCount,
            "totalShoeCountBussiness": row.totalShoeCountBussiness,
            "totalShoeCountProduct": row.totalShoeCountProduct
        }
        for row in results
    ]

    return jsonify({"status": "success", "data": response}), 200




@dev_performance_bp.route("/devproductionorder/getallshoeswithadesigner", methods=["GET"])
def get_all_shoes_with_designer():
    designer = request.args.get("designer")
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()
    year = request.args.get("year", "").strip()
    month = request.args.get("month", "").strip()
    shoe_rid = request.args.get("shoeRid")

    _, _, department = current_user_info()
    user_department = department.department_name

    if not designer:
        return jsonify({"status": "error", "message": "Designer is required"}), 400

    if designer == "设计师信息空缺":
        designer_filter = or_(Shoe.shoe_designer == None, Shoe.shoe_designer == "")
    else:
        designer_filter = Shoe.shoe_designer == designer

    # 日期筛选优先级：年 > 月 > 指定时间段
    if year:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    elif month:
        start_date, end_date = get_month_date_range(month)

    # 子查询：业务量按 order_shoe_type_id 聚合
    batch_amount_subquery = (
        db.session.query(
            OrderShoeBatchInfo.order_shoe_type_id,
            func.sum(OrderShoeBatchInfo.total_amount).label("total_business_amount")
        )
        .group_by(OrderShoeBatchInfo.order_shoe_type_id)
        .subquery()
    )

    # 子查询：生产量，仅限 production_team = 2
    production_amount_subquery = (
        db.session.query(
            OrderShoeProductionAmount.order_shoe_type_id,
            func.sum(OrderShoeProductionAmount.total_production_amount).label("total_production_amount")
        )
        .filter(OrderShoeProductionAmount.production_team == 2)
        .group_by(OrderShoeProductionAmount.order_shoe_type_id)
        .subquery()
    )

    # 主查询
    query = (
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
            func.coalesce(func.max(batch_amount_subquery.c.total_business_amount), 0).label("business_amount"),
            func.coalesce(func.max(production_amount_subquery.c.total_production_amount), 0).label("product_amount"),

        )
        .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .join(OrderShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .outerjoin(batch_amount_subquery, batch_amount_subquery.c.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .outerjoin(production_amount_subquery, production_amount_subquery.c.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(designer_filter, Shoe.shoe_department_id == user_department)
    )

    if start_date:
        query = query.filter(Order.start_date >= start_date)
    if end_date:
        query = query.filter(Order.start_date <= end_date)
    if shoe_rid:
        query = query.filter(Shoe.shoe_rid.like(f"%{shoe_rid}%"))

    query = query.group_by(
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

    results = query.all()

    # 数据结构组装
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
        shoe_map[shoe_key]["totalOrderCountColor"] += 1
        product_amount = row.product_amount if (row.product_amount is not None and row.product_amount != 0) else row.business_amount

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
            "productAmount": product_amount
        })

        if order_pair_key not in counted_pairs:
            counted_pairs.add(order_pair_key)
            shoe_map[shoe_key]["totalOrderCount"] += 1
        shoe_map[shoe_key]["totalShoeCountBussiness"] += row.business_amount
        shoe_map[shoe_key]["totalShoeCountProduct"] += product_amount

    final_data = []
    for shoe in shoe_map.values():
        shoe["colors"] = list(shoe["colors"].values())
        final_data.append(shoe)

    return jsonify({"status": "success", "data": final_data}), 200



import calendar

def get_month_date_range(month_str):  # month_str 形如 "2025-04"
    year, month = map(int, month_str.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    start_date = f"{month_str}-01"
    end_date = f"{month_str}-{last_day:02d}"
    return start_date, end_date




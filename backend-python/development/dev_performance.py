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
# left import for future messaging hooks; currently unused
from logger import logger
from login.login import current_user, current_user_info
from sqlalchemy import and_, func, case, distinct, or_

dev_performance_bp = Blueprint("dev_performance", __name__)


@dev_performance_bp.route("/devproductionorder/getalldesigners", methods=["GET"])
def get_all_designers():

    _, _, department = current_user_info()
    user_dep_name = getattr(department, "department_name", "") or ""

    designer_keyword = request.args.get("designer", "").strip()
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()
    year = request.args.get("year", "").strip()
    month = request.args.get("month", "").strip()
    department = request.args.get("department", "").strip()

    # 每个 order_shoe_type_id 的业务量
    batch_amount_subquery = (
        db.session.query(
            OrderShoeBatchInfo.order_shoe_type_id,
            func.sum(OrderShoeBatchInfo.total_amount).label("total_business_amount"),
        )
        .group_by(OrderShoeBatchInfo.order_shoe_type_id)
        .subquery()
    )

    # 每个 order_shoe_type_id 的生产量（仅 team = 2）
    production_amount_subquery = (
        db.session.query(
            OrderShoeProductionAmount.order_shoe_type_id,
            func.sum(OrderShoeProductionAmount.total_production_amount).label("total_production_amount"),
        )
        .filter(OrderShoeProductionAmount.production_team == 2)
        .group_by(OrderShoeProductionAmount.order_shoe_type_id)
        .subquery()
    )

    # 基础查询：展开到 order_shoe_type 级别
    base_q = (
        db.session.query(
            case(
                (func.ifnull(Shoe.shoe_designer, "") == "", "设计师信息空缺"),
                else_=Shoe.shoe_designer,
            ).label("designer"),
            Shoe.shoe_department_id.label("department"),
            Order.order_id.label("order_id"),
            func.coalesce(batch_amount_subquery.c.total_business_amount, 0).label("business_amount"),
            func.coalesce(production_amount_subquery.c.total_production_amount, None).label("production_amount"),
        )
        .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .outerjoin(batch_amount_subquery, batch_amount_subquery.c.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .outerjoin(production_amount_subquery, production_amount_subquery.c.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
    )

    # 部门过滤逻辑：财务部看全量；其他部门仅看本部门
    if user_dep_name != "财务部":
        base_q = base_q.filter(Shoe.shoe_department_id == user_dep_name)

    # 设计师与时间筛选
    if designer_keyword:
        base_q = base_q.filter(Shoe.shoe_designer.like(f"%{designer_keyword}%"))
    if department:
        base_q = base_q.filter(Shoe.shoe_department_id == department)

    if year:
        base_q = base_q.filter(func.year(Order.start_date) == int(year))
    elif month:
        # month 形如 "2025-08"
        base_q = base_q.filter(func.date_format(Order.start_date, "%Y-%m") == month)
    else:
        if start_date:
            base_q = base_q.filter(Order.start_date >= start_date)
        if end_date:
            base_q = base_q.filter(Order.start_date <= end_date)

    base_sq = base_q.subquery()

    # 聚合到设计师
    final_q = (
        db.session.query(
            base_sq.c.designer,
            base_sq.c.department,
            func.count(distinct(base_sq.c.order_id)).label("totalOrderCount"),
            func.sum(base_sq.c.business_amount).label("totalShoeCountBussiness"),
            func.sum(
                case(
                    (base_sq.c.production_amount != None, base_sq.c.production_amount),
                    else_=base_sq.c.business_amount,
                )
            ).label("totalShoeCountProduct"),
        )
        .group_by(base_sq.c.designer, base_sq.c.department)
        .order_by(base_sq.c.department.asc(), base_sq.c.designer.asc()) 
    )

    results = final_q.all()
    response = [
        {
            "designer": r.designer,
            "department": r.department,
            "totalOrderCount": int(r.totalOrderCount or 0),
            "totalShoeCountBussiness": int(r.totalShoeCountBussiness or 0),
            "totalShoeCountProduct": int(r.totalShoeCountProduct or 0),
        }
        for r in results
    ]
    return jsonify({"status": "success", "data": response}), 200





@dev_performance_bp.route("/devproductionorder/getallshoeswithadesigner", methods=["GET"])
def get_all_shoes_with_designer():
    designer = request.args.get("designer")
    designer_department = request.args.get("department", "").strip()
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()
    year = request.args.get("year", "").strip()
    month = request.args.get("month", "").strip()
    shoe_rid = request.args.get("shoeRid")

    _, _, department = current_user_info()
    # 与第一个接口保持一致的写法
    user_dep_name = getattr(department, "department_name", "") or ""

    if not designer:
        return jsonify({"status": "error", "message": "Designer is required"}), 400

    if designer == "设计师信息空缺":
        designer_filter = and_(or_(Shoe.shoe_designer == None, Shoe.shoe_designer == ""), Shoe.shoe_department_id == designer_department)
    else:
        designer_filter = and_(Shoe.shoe_designer == designer, Shoe.shoe_department_id == designer_department)

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

    # 主查询（先不加部门限制，保持与第一个接口相同的时机）
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
        .filter(designer_filter)
    )

    # 与第一个接口一致的部门过滤逻辑：财务部看全量；其他部门仅看本部门
    if user_dep_name != "财务部":
        query = query.filter(Shoe.shoe_department_id == user_dep_name)

    # 其它筛选
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



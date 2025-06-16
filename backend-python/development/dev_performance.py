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
from sqlalchemy import or_

dev_performance_bp = Blueprint("dev_performance", __name__)


@dev_performance_bp.route("/devproductionorder/getalldesigners", methods=["GET"])
def get_all_designers():
    from sqlalchemy import func, case

    # 当前用户所属部门
    _, _, department = current_user_info()
    user_department = department.department_name

    designer_group = case(
        (func.ifnull(Shoe.shoe_designer, "") == "", "设计师信息空缺"),
        else_=Shoe.shoe_designer,
    )

    # 分组聚合：设计师 => 总订单数
    results = (
        db.session.query(
            designer_group.label("designer"),
            Shoe.shoe_department_id,
            func.count(OrderShoe.order_id).label("order_count"),
        )
        .join(OrderShoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(Shoe.shoe_department_id == user_department)
        .group_by(designer_group, Shoe.shoe_department_id)
        .all()
    )

    # 构造返回结构
    designer_list = []
    for row in results:
        designer_list.append(
            {
                "designer": row.designer,
                "department": row.shoe_department_id,
                "totalOrderCount": row.order_count,
            }
        )

    return jsonify({"status": "success", "data": designer_list}), 200


@dev_performance_bp.route("/devproductionorder/getallshoeswithadesigner", methods=["GET"])
def get_all_shoes_with_designer():
    designer = request.args.get("designer")
    if designer is None:
        return jsonify({"status": "error", "message": "Designer is required"}), 400

    # 根据是否是“确实信息鞋型”进行条件判断
    if designer == "设计师信息空缺":
        designer_filter = or_(Shoe.shoe_designer == None, Shoe.shoe_designer == '')
    else:
        designer_filter = Shoe.shoe_designer == designer

    # 三表连接查询
    results = (
        db.session.query(
            Shoe.shoe_id,
            Shoe.shoe_rid,
            Shoe.shoe_designer,
            Shoe.shoe_department_id,
            Order.order_id,
            Order.order_rid,
            Order.order_cid,
            Order.start_date,
            Order.end_date,
            Order.customer_id,
            Order.salesman_id,
            Order.supervisor_id,
        )
        .join(OrderShoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .filter(designer_filter)
        .all()
    )

    # 构建数据结构
    shoe_dict = {}
    for row in results:
        shoe_key = row.shoe_id
        if shoe_key not in shoe_dict:
            shoe_dict[shoe_key] = {
                "shoeId": row.shoe_id,
                "shoeRid": row.shoe_rid,
                "shoeDesigner": row.shoe_designer or "",  # 保证为字符串
                "shoeDepartment_id": row.shoe_department_id,
                "orders": [],
            }

        shoe_dict[shoe_key]["orders"].append({
            "orderId": row.order_id,
            "orderRid": row.order_rid,
            "orderCid": row.order_cid,
            "startDate": row.start_date.strftime("%Y-%m-%d") if row.start_date else None,
            "endDate": row.end_date.strftime("%Y-%m-%d") if row.end_date else None,
            "customerId": row.customer_id,
            "salesmanId": row.salesman_id,
            "supervisorId": row.supervisor_id,
        })

    return jsonify({"status": "success", "data": list(shoe_dict.values())}), 200

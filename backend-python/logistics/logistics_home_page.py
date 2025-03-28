from flask import Blueprint, jsonify, request
from sqlalchemy.dialects.mysql import insert

from app_config import app, db
from models import *

logistics_home_page_bp = Blueprint("logistics_home_page_bp", __name__)


@logistics_home_page_bp.route("/logistics/task", methods=["GET"])
def get_task():
    task_status = request.args.get("taskstatus")
    shoe_status = request.args.get("shoestatus")
    task_name = ""

    query = (
        db.session.query(Order, OrderShoe, OrderShoeStatus, OrderShoeStatusReference)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        .join(
            OrderShoeStatusReference,
            OrderShoeStatus.current_status == OrderShoeStatusReference.status_id,
        )
        .filter(OrderShoeStatus.current_status_value == task_status)
        .order_by(Order.start_date)
    )

    if shoe_status != "all":
        query = query.filter(OrderShoeStatus.current_status == int(shoe_status))
    else:
        # If "all", we need to check for statuses 6 or 13
        query = query.filter(OrderShoeStatus.current_status.in_([6, 7]))

    response = query.distinct(Order.order_id).all()

    unique_orders = {}

    for row in response:
        order_id = row.Order.order_id

        # Determine taskName based on current_status if not already set for this order
        if order_id not in unique_orders:
            if row.OrderShoeStatus.current_status == 6:
                task_name = "一次采购订单创建"
            elif row.OrderShoeStatus.current_status == 7:
                task_name = "二次采购订单创建"
            else:
                task_name = ""  # Default or any other logic

            unique_orders[order_id] = {
                "taskName": task_name,
                "orderId": row.Order.order_id,
                "orderRId": row.Order.order_rid,
                "createTime": row.Order.start_date.isoformat(),
            }

    result = list(unique_orders.values())
    return jsonify(result)

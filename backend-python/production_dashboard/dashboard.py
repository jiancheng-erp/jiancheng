from datetime import date

from flask import Blueprint, jsonify
from sqlalchemy import func

from api_utility import format_date
from app_config import db
from models import (
    BatchInfoType,
    Customer,
    Order,
    OrderShoe,
    OrderShoeBatchInfo,
    OrderShoeProductionInfo,
    OrderShoeType,
    PackagingInfo,
    Shoe,
    ShoeType,
    Color
)

production_dashboard_bp = Blueprint("production_dashboard_bp", __name__)


@production_dashboard_bp.route(
    "/production/dashboard/todaymoldingorders", methods=["GET"]
)
def get_today_molding_orders():
    """Return molding orders scheduled for the current day."""
    today = date.today()

    query = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            OrderShoe.order_shoe_id,
            OrderShoe.customer_product_name,
            Shoe.shoe_id,
            Shoe.shoe_rid,
            Customer.customer_name,
            ShoeType.shoe_type_id,
            Color.color_name,
            OrderShoeProductionInfo.molding_line_group,
            OrderShoeProductionInfo.molding_start_date,
            OrderShoeProductionInfo.molding_end_date,
            func.sum(OrderShoeBatchInfo.total_amount).label("total_amount"),
            func.sum(OrderShoeBatchInfo.size_34_amount).label("size_34_amount"),
            func.sum(OrderShoeBatchInfo.size_35_amount).label("size_35_amount"),
            func.sum(OrderShoeBatchInfo.size_36_amount).label("size_36_amount"),
            func.sum(OrderShoeBatchInfo.size_37_amount).label("size_37_amount"),
            func.sum(OrderShoeBatchInfo.size_38_amount).label("size_38_amount"),
            func.sum(OrderShoeBatchInfo.size_39_amount).label("size_39_amount"),
            func.sum(OrderShoeBatchInfo.size_40_amount).label("size_40_amount"),
            func.sum(OrderShoeBatchInfo.size_41_amount).label("size_41_amount"),
            func.sum(OrderShoeBatchInfo.size_42_amount).label("size_42_amount"),
            func.sum(OrderShoeBatchInfo.size_43_amount).label("size_43_amount"),
            func.sum(OrderShoeBatchInfo.size_44_amount).label("size_44_amount"),
            func.sum(OrderShoeBatchInfo.size_45_amount).label("size_45_amount"),
            func.sum(OrderShoeBatchInfo.size_46_amount).label("size_46_amount"),
            func.max(BatchInfoType.size_34_name).label("size_34_name"),
            func.max(BatchInfoType.size_35_name).label("size_35_name"),
            func.max(BatchInfoType.size_36_name).label("size_36_name"),
            func.max(BatchInfoType.size_37_name).label("size_37_name"),
            func.max(BatchInfoType.size_38_name).label("size_38_name"),
            func.max(BatchInfoType.size_39_name).label("size_39_name"),
            func.max(BatchInfoType.size_40_name).label("size_40_name"),
            func.max(BatchInfoType.size_41_name).label("size_41_name"),
            func.max(BatchInfoType.size_42_name).label("size_42_name"),
            func.max(BatchInfoType.size_43_name).label("size_43_name"),
            func.max(BatchInfoType.size_44_name).label("size_44_name"),
            func.max(BatchInfoType.size_45_name).label("size_45_name"),
            func.max(BatchInfoType.size_46_name).label("size_46_name"),
        )
        .join(
            OrderShoeProductionInfo,
            OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id,
        )
        .outerjoin(
            BatchInfoType, PackagingInfo.batch_info_type_id == BatchInfoType.batch_info_type_id
        )
        .filter(OrderShoeProductionInfo.molding_start_date <= today)
        .filter(OrderShoeProductionInfo.molding_end_date >= today)
        .group_by(
            Order.order_id,
            Order.order_rid,
            OrderShoe.order_shoe_id,
            OrderShoe.customer_product_name,
            Shoe.shoe_id,
            Shoe.shoe_rid,
            Customer.customer_name,
            ShoeType.shoe_type_id,
            Color.color_name,
            OrderShoeProductionInfo.molding_line_group,
            OrderShoeProductionInfo.molding_start_date,
            OrderShoeProductionInfo.molding_end_date,
        )
        .order_by(Order.order_rid, OrderShoe.order_shoe_id)
    )

    molding_orders = []
    for (
        order_id,
        order_rid,
        order_shoe_id,
        customer_product_name,
        shoe_id,
        shoe_rid,
        customer_name,
        shoe_type_id,
        color_name,
        molding_line_group,
        molding_start_date,
        molding_end_date,
        total_amount,
        size_34_amount,
        size_35_amount,
        size_36_amount,
        size_37_amount,
        size_38_amount,
        size_39_amount,
        size_40_amount,
        size_41_amount,
        size_42_amount,
        size_43_amount,
        size_44_amount,
        size_45_amount,
        size_46_amount,
        size_34_name,
        size_35_name,
        size_36_name,
        size_37_name,
        size_38_name,
        size_39_name,
        size_40_name,
        size_41_name,
        size_42_name,
        size_43_name,
        size_44_name,
        size_45_name,
        size_46_name,
    ) in query:
        molding_orders.append(
            {
                "orderId": order_id,
                "orderRId": order_rid,
                "shoeTypeId": shoe_type_id,
                "colorName": color_name,
                "orderShoeId": order_shoe_id,
                "customerProductName": customer_product_name,
                "customerName": customer_name,
                "shoeId": shoe_id,
                "shoeRId": shoe_rid,
                "moldingLineGroup": molding_line_group,
                "moldingStartDate": format_date(molding_start_date),
                "moldingEndDate": format_date(molding_end_date),
                "totalAmount": total_amount,
                "sizeAmounts": {
                    "size34": {"name": size_34_name, "amount": size_34_amount},
                    "size35": {"name": size_35_name, "amount": size_35_amount},
                    "size36": {"name": size_36_name, "amount": size_36_amount},
                    "size37": {"name": size_37_name, "amount": size_37_amount},
                    "size38": {"name": size_38_name, "amount": size_38_amount},
                    "size39": {"name": size_39_name, "amount": size_39_amount},
                    "size40": {"name": size_40_name, "amount": size_40_amount},
                    "size41": {"name": size_41_name, "amount": size_41_amount},
                    "size42": {"name": size_42_name, "amount": size_42_amount},
                    "size43": {"name": size_43_name, "amount": size_43_amount},
                    "size44": {"name": size_44_name, "amount": size_44_amount},
                    "size45": {"name": size_45_name, "amount": size_45_amount},
                    "size46": {"name": size_46_name, "amount": size_46_amount},
                },
            }
        )

    return jsonify(molding_orders)
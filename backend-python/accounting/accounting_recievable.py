from flask import Blueprint, jsonify, request, send_file
from accounting import accounting
from models import *
from api_utility import (
    to_camel,
    to_snake,
    db_obj_to_res,
    format_date,
    format_datetime,
    format_outbound_type,
    accounting_audit_status_converter,
)
from api_utility import normalize_decimal
from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload
from general_document.accounting_recievable_excel import (
    generate_accounting_recievable_excel,
)
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
import time
from datetime import datetime, timedelta
from logger import logger
from decimal import Decimal
from app_config import db

accounting_recievable_bp = Blueprint("accounting_recievable_bp", __name__)


@accounting_recievable_bp.route("/finance/get_receivable_list", methods=["GET"])
def get_receivable_list():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    search_order = request.args.get("searchOrder", "").strip()
    search_customer = request.args.get("searchCustomer", "").strip()
    factory_model_kw = request.args.get("factoryModel", "").strip()
    customer_model_kw = request.args.get("customerModel", "").strip()
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")

    query = (
        db.session.query(Order)
    )

    if search_order:
        query = query.filter(Order.order_rid.like(f"%{search_order}%"))

    if start_date:
        try:
            query = query.filter(
                Order.start_date >= datetime.strptime(start_date, "%Y-%m-%d").date()
            )
        except ValueError:
            pass
    if end_date:
        try:
            query = query.filter(
                Order.start_date <= datetime.strptime(end_date, "%Y-%m-%d").date()
            )
        except ValueError:
            pass

    if search_customer:
        query = query.join(Customer, Customer.customer_id == Order.customer_id).filter(
            Customer.customer_name.like(f"%{search_customer}%")
        )
    query = query.join(OrderStatus, OrderStatus.order_id == Order.order_id).filter(
        OrderStatus.order_current_status >= 7
    )

    total = query.count()
    orders = query.offset((page - 1) * per_page).limit(per_page).all()

    order_ids = [o.order_id for o in orders]
    customer_ids = [o.customer_id for o in orders if o.customer_id]

    customers = (
        db.session.query(Customer).filter(Customer.customer_id.in_(customer_ids)).all()
    )
    customer_dict = {c.customer_id: c.customer_name for c in customers}

    order_shoes = (
        db.session.query(OrderShoe).filter(OrderShoe.order_id.in_(order_ids)).all()
    )
    order_shoe_ids = [os.order_shoe_id for os in order_shoes]
    shoe_dict = {os.order_shoe_id: os.customer_product_name for os in order_shoes}

    order_shoe_types = (
        db.session.query(OrderShoeType)
        .filter(OrderShoeType.order_shoe_id.in_(order_shoe_ids))
        .all()
    )
    ost_ids = [ost.order_shoe_type_id for ost in order_shoe_types]
    shoe_type_ids = [ost.shoe_type_id for ost in order_shoe_types if ost.shoe_type_id]

    # 中间映射：ShoeType -> Shoe
    shoe_types = (
        db.session.query(ShoeType)
        .filter(ShoeType.shoe_type_id.in_(shoe_type_ids))
        .all()
    )
    shoe_type_map = {st.shoe_type_id: st.shoe_id for st in shoe_types}

    shoes = (
        db.session.query(Shoe)
        .filter(Shoe.shoe_id.in_(set(shoe_type_map.values())))
        .all()
    )
    shoe_map = {s.shoe_id: s.shoe_rid for s in shoes}

    ost_to_factory_model = {}
    for ost in order_shoe_types:
        shoe_type_id = ost.shoe_type_id
        shoe_id = shoe_type_map.get(shoe_type_id)
        if shoe_id:
            ost_to_factory_model[ost.order_shoe_type_id] = shoe_map.get(shoe_id, "")

    # 批次
    batches = (
        db.session.query(OrderShoeBatchInfo)
        .filter(OrderShoeBatchInfo.order_shoe_type_id.in_(ost_ids))
        .all()
    )
    batch_map = {}
    for b in batches:
        batch_map.setdefault(b.order_shoe_type_id, []).append(b)

    # 筛选逻辑（工厂型号、客户型号）
    if factory_model_kw:
        order_shoe_types = [
            ost
            for ost in order_shoe_types
            if factory_model_kw
            in (ost_to_factory_model.get(ost.order_shoe_type_id, ""))
        ]
    if customer_model_kw:
        order_shoe_types = [
            ost
            for ost in order_shoe_types
            if customer_model_kw in (shoe_dict.get(ost.order_shoe_id, ""))
        ]

    result = []
    for order in orders:
        receivable_total = Decimal("0.00")
        paid_total = Decimal("0.00")
        shoe_items = []

        for order_shoe in order_shoes:
            if order_shoe.order_id != order.order_id:
                continue
            customer_model = shoe_dict.get(order_shoe.order_shoe_id, "")
            for ost in order_shoe_types:
                if ost.order_shoe_id != order_shoe.order_shoe_id:
                    continue

                unit_price = ost.unit_price or Decimal("0.00")
                quantity = sum(
                    batch.total_amount or 0
                    for batch in batch_map.get(ost.order_shoe_type_id, [])
                )
                subtotal = unit_price * quantity

                shoe_items.append(
                    {
                        "factoryModel": ost_to_factory_model.get(
                            ost.order_shoe_type_id, ""
                        ),
                        "customerModel": customer_model,
                        "color": ost.customer_color_name or "",
                        "quantity": quantity,
                        "unitPrice": float(unit_price),
                        "subtotal": float(subtotal),
                    }
                )

                receivable_total += subtotal

        result.append(
            {
                "orderCode": order.order_rid,
                "customerName": customer_dict.get(order.customer_id, ""),
                "orderDate": (
                    order.start_date.strftime("%Y-%m-%d") if order.start_date else ""
                ),
                "orderEndDate": (
                    order.end_date.strftime("%Y-%m-%d") if order.end_date else ""
                ),
                "totalAmount": float(receivable_total),
                "paidAmount": float(paid_total),
                "transactionCount": 0,
                "shoes": shoe_items,
            }
        )

    return jsonify({"total": total, "receivables": result})


@accounting_recievable_bp.route("/finance/download_receivable_excel", methods=["GET"])
def download_receivable_excel():
    search_order = request.args.get("searchOrder", "").strip()
    search_customer = request.args.get("searchCustomer", "").strip()
    factory_model_kw = request.args.get("factoryModel", "").strip()
    customer_model_kw = request.args.get("customerModel", "").strip()
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")

    query = (
        db.session.query(Order)
    )

    if search_order:
        query = query.filter(Order.order_rid.like(f"%{search_order}%"))

    if start_date:
        try:
            query = query.filter(
                Order.start_date >= datetime.strptime(start_date, "%Y-%m-%d").date()
            )
        except ValueError:
            pass
    if end_date:
        try:
            query = query.filter(
                Order.start_date <= datetime.strptime(end_date, "%Y-%m-%d").date()
            )
        except ValueError:
            pass

    if search_customer:
        query = query.join(Customer, Customer.customer_id == Order.customer_id).filter(
            Customer.customer_name.like(f"%{search_customer}%")
        )
    query = query.join(OrderStatus, OrderStatus.order_id == Order.order_id).filter(
        OrderStatus.order_current_status >= 7
    )

    total = query.count()
    orders = query.all()

    order_ids = [o.order_id for o in orders]
    customer_ids = [o.customer_id for o in orders if o.customer_id]

    customers = (
        db.session.query(Customer).filter(Customer.customer_id.in_(customer_ids)).all()
    )
    customer_dict = {c.customer_id: c.customer_name for c in customers}

    order_shoes = (
        db.session.query(OrderShoe).filter(OrderShoe.order_id.in_(order_ids)).all()
    )
    order_shoe_ids = [os.order_shoe_id for os in order_shoes]
    shoe_dict = {os.order_shoe_id: os.customer_product_name for os in order_shoes}

    order_shoe_types = (
        db.session.query(OrderShoeType)
        .filter(OrderShoeType.order_shoe_id.in_(order_shoe_ids))
        .all()
    )
    ost_ids = [ost.order_shoe_type_id for ost in order_shoe_types]
    shoe_type_ids = [ost.shoe_type_id for ost in order_shoe_types if ost.shoe_type_id]

    # 中间映射：ShoeType -> Shoe
    shoe_types = (
        db.session.query(ShoeType)
        .filter(ShoeType.shoe_type_id.in_(shoe_type_ids))
        .all()
    )
    shoe_type_map = {st.shoe_type_id: st.shoe_id for st in shoe_types}

    shoes = (
        db.session.query(Shoe)
        .filter(Shoe.shoe_id.in_(set(shoe_type_map.values())))
        .all()
    )
    shoe_map = {s.shoe_id: s.shoe_rid for s in shoes}

    ost_to_factory_model = {}
    for ost in order_shoe_types:
        shoe_type_id = ost.shoe_type_id
        shoe_id = shoe_type_map.get(shoe_type_id)
        if shoe_id:
            ost_to_factory_model[ost.order_shoe_type_id] = shoe_map.get(shoe_id, "")

    # 批次
    batches = (
        db.session.query(OrderShoeBatchInfo)
        .filter(OrderShoeBatchInfo.order_shoe_type_id.in_(ost_ids))
        .all()
    )
    batch_map = {}
    for b in batches:
        batch_map.setdefault(b.order_shoe_type_id, []).append(b)

    # 筛选逻辑（工厂型号、客户型号）
    if factory_model_kw:
        order_shoe_types = [
            ost
            for ost in order_shoe_types
            if factory_model_kw
            in (ost_to_factory_model.get(ost.order_shoe_type_id, ""))
        ]
    if customer_model_kw:
        order_shoe_types = [
            ost
            for ost in order_shoe_types
            if customer_model_kw in (shoe_dict.get(ost.order_shoe_id, ""))
        ]

    result = []
    for order in orders:
        receivable_total = Decimal("0.00")
        paid_total = Decimal("0.00")
        shoe_items = []

        for order_shoe in order_shoes:
            if order_shoe.order_id != order.order_id:
                continue
            customer_model = shoe_dict.get(order_shoe.order_shoe_id, "")
            for ost in order_shoe_types:
                if ost.order_shoe_id != order_shoe.order_shoe_id:
                    continue

                unit_price = ost.unit_price or Decimal("0.00")
                quantity = sum(
                    batch.total_amount or 0
                    for batch in batch_map.get(ost.order_shoe_type_id, [])
                )
                subtotal = unit_price * quantity

                shoe_items.append(
                    {
                        "factoryModel": ost_to_factory_model.get(
                            ost.order_shoe_type_id, ""
                        ),
                        "customerModel": customer_model,
                        "color": ost.customer_color_name or "",
                        "quantity": quantity,
                        "unitPrice": float(unit_price),
                        "subtotal": float(subtotal),
                    }
                )

                receivable_total += subtotal

        result.append(
            {
                "orderCode": order.order_rid,
                "customerName": customer_dict.get(order.customer_id, ""),
                "orderDate": (
                    order.start_date.strftime("%Y-%m-%d") if order.start_date else ""
                ),
                "orderEndDate": (
                    order.end_date.strftime("%Y-%m-%d") if order.end_date else ""
                ),
                "totalAmount": float(receivable_total),
                "paidAmount": float(paid_total),
                "transactionCount": 0,
                "shoes": shoe_items,
            }
        )
    # 生成Excel文件
    file_path = generate_accounting_recievable_excel(
        template_path=f"{FILE_STORAGE_PATH}/应收明细模板.xlsx",
        save_path=f"{FILE_STORAGE_PATH}/财务部文件/应收明细/应收明细_{int(time.time())}.xlsx",
        customer_name=search_customer,
        time_range=f"{start_date} - {end_date}" if start_date and end_date else "全部",
        receivables_data=result,
    )
    if not file_path:
        return jsonify({"error": "Failed to generate Excel file"}), 500
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"应收明细{search_customer if search_customer else ''}_{start_date if start_date else ''}_{end_date if end_date else ''}.xlsx",
    )

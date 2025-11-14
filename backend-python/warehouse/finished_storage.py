from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from collections import defaultdict, OrderedDict
from api_utility import format_date
from app_config import db
from file_locations import FILE_STORAGE_PATH
from shared_apis import shoe
from shared_apis.batch_info_type import get_order_batch_type_helper
from constants import *
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request, send_file
from models import *
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, or_, and_, desc, literal, Numeric, case, Integer, not_
from api_utility import format_datetime
from login.login import current_user_info
from logger import logger
from constants import SHOESIZERANGE
from general_document.finished_warehouse_excel import (
    build_finished_inbound_excel,
    build_finished_outbound_excel,
    build_finished_inout_excel
)
from general_document.shoe_outbound_list import generate_finished_outbound_excel
from shared_apis.utility_func import normalize_category_by_batch_type
from shared_apis.utility_func import normalize_currency
import os

finished_storage_bp = Blueprint("finished_storage_bp", __name__)


@finished_storage_bp.route("/warehouse/getfinishedstorages", methods=["GET"])
def get_finished_in_out_overview():
    """
    查询成品入/出库总览（支持“仅可入库”过滤）
    inboundableOnly:
        0: 不限（默认）
        1: 仅可入库（finished_actual_amount < finished_estimated_amount）
    showAll:
        0: 后端不额外限制
        1: 仅显示当前仓有库存（finished_amount > 0）
    """
    page = request.args.get("page", type=int, default=1)
    number = request.args.get("pageSize", type=int, default=20)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    customer_name = request.args.get("customerName")
    customer_product_name = request.args.get("customerProductName")
    order_cid = request.args.get("orderCId")
    customer_brand = request.args.get("customerBrand")
    storage_status_num = request.args.get("storageStatusNum", type=int)
    show_all = request.args.get("showAll", default=0, type=int)
    inboundable_only = request.args.get("inboundableOnly", default=0, type=int)
    category_kw = (request.args.get("category") or "").strip()

    # 完成事件（仅取 operation_id=22 的最新时间）
    ev_subq = (
        db.session.query(
            Event.event_order_id.label("order_id"),
            func.max(Event.handle_time).label("finished_time"),
        )
        .filter(Event.operation_id == 22)
        .group_by(Event.event_order_id)
        .subquery()
    )

    # 基础联结查询（注意：用它来构建“过滤条件一致的 ID 子查询”和“最终明细查询”）
    base_query = (
        db.session.query(
            Order.order_rid.label("order_rid_for_sort"),
            FinishedShoeStorage.finished_shoe_id.label("storage_id_pk"),
            Order,
            Customer,
            OrderShoe,
            Shoe,
            FinishedShoeStorage,
            Color,
            BatchInfoType,
            ev_subq.c.finished_time,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(BatchInfoType, BatchInfoType.batch_info_type_id == Order.batch_info_type_id)
        .outerjoin(ev_subq, ev_subq.c.order_id == Order.order_id)
    )

    # —— 动态过滤条件（与前端一致）——
    if order_rid:
        base_query = base_query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid:
        base_query = base_query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if customer_name:
        base_query = base_query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if customer_product_name:
        base_query = base_query.filter(OrderShoe.customer_product_name.ilike(f"%{customer_product_name}%"))
    if storage_status_num is not None and storage_status_num > -1:
        base_query = base_query.filter(FinishedShoeStorage.finished_status == storage_status_num)
    if order_cid:
        base_query = base_query.filter(Order.order_cid.ilike(f"%{order_cid}%"))
    if customer_brand:
        base_query = base_query.filter(Customer.customer_brand.ilike(f"%{customer_brand}%"))

    if category_kw == "男鞋":
        base_query = base_query.filter(BatchInfoType.batch_info_type_name.like("%男%"))
    elif category_kw == "女鞋":
        base_query = base_query.filter(BatchInfoType.batch_info_type_name.like("%女%"))
    elif category_kw == "童鞋":
        base_query = base_query.filter(BatchInfoType.batch_info_type_name.like("%童%"))
    elif category_kw == "其它":
        base_query = base_query.filter(
            or_(
                BatchInfoType.batch_info_type_name.is_(None),
                and_(
                    not_(BatchInfoType.batch_info_type_name.like("%男%")),
                    not_(BatchInfoType.batch_info_type_name.like("%女%")),
                    not_(BatchInfoType.batch_info_type_name.like("%童%")),
                ),
            )
        )

    # 仅显示当前仓有库存
    if show_all == 1:
        base_query = base_query.filter(FinishedShoeStorage.finished_amount > 0)

    # 仅显示“可入库”
    if inboundable_only == 1:
        base_query = base_query.filter(
            FinishedShoeStorage.finished_actual_amount < FinishedShoeStorage.finished_estimated_amount
        )
        # 如需用“欠数 > 0”替代，可写：
        # base_query = base_query.filter(
        #     (FinishedShoeStorage.finished_estimated_amount - FinishedShoeStorage.finished_actual_amount) > 0
        # )

    # —— 先做“ID 子查询 + 去重计数” ——（避免 DISTINCT + JOIN 分页混乱）
    id_subq = (
        base_query
        .with_entities(
            FinishedShoeStorage.finished_shoe_id.label("sid"),
            Order.order_rid.label("order_rid_for_sort"),
        )
        .distinct()
        .subquery()
    )

    # 计数（去重后）
    total = db.session.query(func.count()).select_from(id_subq).scalar()

    # 取当页主键（可按 order_rid 排序，也可改为创建时间等）
    page_ids = (
        db.session.query(id_subq.c.sid)
        .order_by(id_subq.c.order_rid_for_sort.asc())
        .limit(number)
        .offset((page - 1) * number)
        .all()
    )
    page_ids = [x[0] for x in page_ids]
    if not page_ids:
        return {"result": [], "total": total}

    # —— 用当页主键回查完整明细 ——（与原 base_query 同样的列）
    page_query = base_query.filter(FinishedShoeStorage.finished_shoe_id.in_(page_ids)).order_by(Order.order_rid.asc())
    rows = page_query.all()

    # —— 组装返回 —— 
    result = []
    for (
        order_rid_for_sort,
        storage_id_pk,
        order,
        customer,
        order_shoe,
        shoe,
        storage_obj,
        color,
        batch_info,
        finished_time,
    ) in rows:

        estimated = storage_obj.finished_estimated_amount or 0
        actual = storage_obj.finished_actual_amount or 0
        remaining_amount = max(estimated - actual, 0)  # ✅ 修正

        # 注意：batch_info 这里是内联接；若你今后改为外联，需要加 None 判断
        if "男" in batch_info.batch_info_type_name:
            batch_type = "男鞋"
        elif "女" in batch_info.batch_info_type_name:
            batch_type = "女鞋"
        elif "童" in batch_info.batch_info_type_name:
            batch_type = "童鞋"
        else:
            batch_type = "其它"

        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderCId": order.order_cid,
            "customerBrand": customer.customer_brand,
            "customerName": customer.customer_name,
            "orderShoeId": order_shoe.order_shoe_id,
            "designer": shoe.shoe_designer,
            "adjuster": order_shoe.adjust_staff,
            "finishedTime": format_date(finished_time) if finished_time else None,
            "shoeRId": shoe.shoe_rid,
            "storageId": storage_obj.finished_shoe_id,
            "customerProductName": order_shoe.customer_product_name,
            "estimatedInboundAmount": estimated,
            "actualInboundAmount": actual,
            "currentAmount": storage_obj.finished_amount or 0,
            "remainingAmount": remaining_amount,
            "storageStatusNum": storage_obj.finished_status,
            "storageStatusLabel": FINISHED_STORAGE_STATUS[storage_obj.finished_status],
            "endDate": format_date(order.end_date),
            "colorName": color.color_name,
            "batchType": batch_type,
            "shoeSizeColumns": [],
        }

        for i in range(len(SHOESIZERANGE)):
            shoe_size_db_name = i + 34
            obj[f"size{shoe_size_db_name}EstimatedAmount"] = getattr(
                storage_obj, f"size_{shoe_size_db_name}_estimated_amount"
            )
            obj[f"size{shoe_size_db_name}ActualAmount"] = getattr(
                storage_obj, f"size_{shoe_size_db_name}_actual_amount"
            )
            obj[f"size{shoe_size_db_name}Amount"] = getattr(
                storage_obj, f"size_{shoe_size_db_name}_amount"
            )
            obj["shoeSizeColumns"].append(
                getattr(batch_info, f"size_{shoe_size_db_name}_name")
            )

        result.append(obj)

    return {"result": result, "total": total}



@finished_storage_bp.route("/warehouse/getproductoverview", methods=["GET"])
def get_product_overview():
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    order_cid = request.args.get("orderCId")
    customer_name = request.args.get("customerName")
    customer_brand = request.args.get("customerBrand")
    audit_status_num = request.args.get("auditStatusNum", type=int)
    storage_status_num = request.args.get("storageStatusNum", type=int)
    order_amount_subquery = (
        db.session.query(
            Order.order_id,
            func.sum(OrderShoeBatchInfo.total_amount).label("total_amount"),
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .group_by(Order.order_id)
        .subquery()
    )

    finished_amount_subquery = (
        db.session.query(
            Order.order_id,
            func.sum(FinishedShoeStorage.finished_estimated_amount).label(
                "finished_estimated_amount"
            ),
            func.sum(FinishedShoeStorage.finished_actual_amount).label(
                "finished_actual_amount"
            ),
            func.sum(FinishedShoeStorage.finished_amount).label("finished_amount"),
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .group_by(Order.order_id)
        .subquery()
    )

    outbounded_amount_subquery = (
        db.session.query(
            Order.order_id,
            func.coalesce(
                func.sum(ShoeOutboundRecordDetail.outbound_amount),
                0,
            ).label("outbounded_amount"),
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .outerjoin(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .group_by(Order.order_id)
        .subquery()
    )
    query = (
        db.session.query(
            Order,
            Customer,
            order_amount_subquery.c.total_amount,
            finished_amount_subquery.c.finished_estimated_amount,
            finished_amount_subquery.c.finished_actual_amount,
            finished_amount_subquery.c.finished_amount,
            outbounded_amount_subquery.c.outbounded_amount,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(
            order_amount_subquery,
            order_amount_subquery.c.order_id == Order.order_id,
        )
        .join(
            finished_amount_subquery,
            finished_amount_subquery.c.order_id == Order.order_id,
        )
        .join(
            outbounded_amount_subquery,
            outbounded_amount_subquery.c.order_id == Order.order_id,
        )
        .order_by(Order.order_rid)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if order_cid and order_cid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{order_cid}%"))
    if customer_name and customer_name != "":
        query = query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if customer_brand and customer_brand != "":
        query = query.filter(Customer.customer_brand.ilike(f"%{customer_brand}%"))
    if audit_status_num is not None and audit_status_num > -1:
        query = query.filter(Order.is_outbound_allowed == audit_status_num)

    if storage_status_num == FINISHED_STORAGE_STATUS_ENUM["PRODUCT_OUTBOUND_FINISHED"]:
        query = query.filter(
            outbounded_amount_subquery.c.outbounded_amount
            >= finished_amount_subquery.c.finished_estimated_amount
        )
    elif storage_status_num == FINISHED_STORAGE_STATUS_ENUM["PRODUCT_INBOUND_FINISHED"]:
        query = query.filter(
            finished_amount_subquery.c.finished_actual_amount
            >= finished_amount_subquery.c.finished_estimated_amount,
            outbounded_amount_subquery.c.outbounded_amount
            < finished_amount_subquery.c.finished_estimated_amount,
        )
    elif storage_status_num == FINISHED_STORAGE_STATUS_ENUM["PRODUCT_INBOUND_NOT_FINISHED"]:
        query = query.filter(
            finished_amount_subquery.c.finished_actual_amount
            < finished_amount_subquery.c.finished_estimated_amount
        )
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            order,
            customer,
            order_amount,
            estimated_amount,
            actual_amount,
            current_stock,
            outbounded_amount,
        ) = row
        if outbounded_amount >= estimated_amount:
            storage_status = FINISHED_STORAGE_STATUS_ENUM["PRODUCT_OUTBOUND_FINISHED"]
        elif actual_amount >= estimated_amount:
            storage_status = FINISHED_STORAGE_STATUS_ENUM["PRODUCT_INBOUND_FINISHED"]
        elif actual_amount < estimated_amount:
            storage_status = FINISHED_STORAGE_STATUS_ENUM["PRODUCT_INBOUND_NOT_FINISHED"]
        else:
            storage_status = "未知状态"
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderCId": order.order_cid,
            "customerName": customer.customer_name,
            "customerBrand": customer.customer_brand,
            "startDate": format_date(order.start_date),
            "endDate": format_date(order.end_date),
            "orderAmount": order_amount,
            "currentStock": current_stock,
            "outboundedAmount": outbounded_amount,
            "orderShoeTable": [],
            "storageStatusNum": storage_status,
            "storageStatusLabel": FINISHED_STORAGE_STATUS[storage_status],
            "auditStatusNum": order.is_outbound_allowed,
            "auditStatusLabel": PRODUCT_OUTBOUND_AUDIT_STATUS[order.is_outbound_allowed],
        }
        result.append(obj)

    for order_obj in result:
        order_id = order_obj["orderId"]
        order_shoe_query = (
            db.session.query(
                OrderShoe,
                Shoe,
                func.sum(OrderShoeBatchInfo.total_amount).label(
                    "order_amount_per_color"
                ),
                FinishedShoeStorage,
                func.coalesce(
                    func.sum(ShoeOutboundRecordDetail.outbound_amount).label(
                        "outbound_amount"
                    ),
                    0,
                ),
                Color,
            )
            .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
            .join(Color, Color.color_id == ShoeType.color_id)
            .join(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .outerjoin(
                ShoeOutboundRecordDetail,
                ShoeOutboundRecordDetail.finished_shoe_storage_id
                == FinishedShoeStorage.finished_shoe_id,
            )
            .filter(OrderShoe.order_id == order_id)
            .group_by(
                OrderShoeType.order_shoe_type_id, FinishedShoeStorage.finished_shoe_id
            )
            .all()
        )
        for row in order_shoe_query:
            (
                order_shoe,
                shoe,
                order_amount_per_color,
                storage_obj,
                outbound_amount,
                color,
            ) = row
            obj = {
                "orderShoeId": order_shoe.order_shoe_id,
                "shoeRId": shoe.shoe_rid,
                "customerProductName": order_shoe.customer_product_name,
                "orderAmountPerColor": order_amount_per_color,
                "outboundedAmount": outbound_amount,
                "storageId": storage_obj.finished_shoe_id,
                "currentStock": storage_obj.finished_amount,
                "colorName": color.color_name,
            }
            order_obj["orderShoeTable"].append(obj)
    return {"result": result, "total": count_result}


def _determine_status(storage):
    if storage.finished_estimated_amount > storage.finished_actual_amount:
        return False
    return True


@finished_storage_bp.route("/warehouse/inboundfinished", methods=["POST", "PATCH"])
def inbound_finished():
    data = request.get_json()
    remark = data.get("remark")
    items = data.get("items", [])
    timestamp = format_datetime(datetime.now())
    formatted_timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    rid = "FIR" + formatted_timestamp + "T0"
    inbound_record = ShoeInboundRecord(
        shoe_inbound_rid=rid,
        inbound_datetime=timestamp,
        inbound_type=0,
        remark=remark,
    )
    db.session.add(inbound_record)
    db.session.flush()

    total_amount = 0
    for item in items:
        storage_id = item["storageId"]
        remark = item["remark"]
        amount_list = item["amountList"]
        inbound_quantity = item.get("inboundQuantity", 0)
        response = (
            db.session.query(Order, OrderShoe, FinishedShoeStorage)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(
                FinishedShoeStorage.finished_shoe_id == storage_id,
            )
            .first()
        )
        if not response:
            return jsonify({"message": "无成品记录"}), 400

        order, order_shoe, storage = response
        storage.finished_actual_amount += inbound_quantity
        storage.finished_amount += inbound_quantity
        # for i in range(len(amount_list)):
        #     db_name = i + 34
        #     column_name1 = f"size_{db_name}_actual_amount"
        #     actual_amount = getattr(storage, column_name1) + int(amount_list[i])
        #     column_name2 = f"size_{db_name}_amount"
        #     current_amount = getattr(storage, column_name2) + int(amount_list[i])
        #     setattr(storage, column_name1, actual_amount)
        #     setattr(storage, column_name2, current_amount)
        #     storage.finished_actual_amount += int(amount_list[i])
        #     storage.finished_amount += int(amount_list[i])

        # sub_total_amount = sum([int(x) for x in amount_list])
        record_detail = ShoeInboundRecordDetail(
            inbound_amount=inbound_quantity,
            finished_shoe_storage_id=storage_id,
            remark=remark,
        )
        # for i in range(len(amount_list)):
        #     db_name = i + 34
        #     column_name = f"size_{db_name}_amount"
        #     setattr(record_detail, column_name, int(amount_list[i]))

        db.session.add(record_detail)
        if _determine_status(storage):
            storage.finished_status = 1
        record_detail.shoe_inbound_record_id = inbound_record.shoe_inbound_record_id
        total_amount += inbound_quantity
    inbound_record.inbound_amount = total_amount
    # check if the order_shoe is completed
    cross_check = (
        db.session.query(FinishedShoeStorage)
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(
            OrderShoe.order_shoe_id == order_shoe.order_shoe_id,
        )
        .all()
    )
    is_finished = True
    for storage in cross_check:
        if _determine_status(storage) is False:
            is_finished = False
            break
    if is_finished:
        processor: EventProcessor = current_app.config["event_processor"]
        staff_id = current_user_info()[1].staff_id
        try:
            for operation in [84, 85]:
                event = Event(
                    staff_id=staff_id,
                    handle_time=datetime.now(),
                    operation_id=operation,
                    event_order_id=order.order_id,
                    event_order_shoe_id=order_shoe.order_shoe_id,
                )
                processor.processEvent(event)

            # update order status
            for operation in [18, 19, 20, 21]:
                event = Event(
                    staff_id=staff_id,
                    handle_time=datetime.now(),
                    operation_id=operation,
                    event_order_id=order.order_id,
                )
                processor.processEvent(event)
        except Exception as e:
            logger.debug(e)
            return jsonify({"message": "failed"}), 400
    db.session.commit()
    return jsonify({"message": "success"})


def _determine_outbound_status(storage):
    outbound_amount = (
        db.session.query(func.sum(ShoeOutboundRecordDetail.outbound_amount))
        .filter(
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == storage.finished_shoe_id
        )
        .scalar()
    )
    if outbound_amount >= storage.finished_estimated_amount:
        return True
    return False


@finished_storage_bp.route(
    "/warehouse/warehousemanager/outboundfinished", methods=["POST", "PATCH"]
)
def outbound_finished():
    data = request.get_json()
    timestamp = format_datetime(datetime.now())
    formatted_timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    items = data["items"]
    rid = "FOR" + formatted_timestamp + "T0"
    picker = data.get("picker", "")
    outbound_record = ShoeOutboundRecord(
        shoe_outbound_rid=rid,
        outbound_datetime=timestamp,
        outbound_type=0,
        remark=data.get("remark", ""),
        picker=picker,
    )
    db.session.add(outbound_record)
    db.session.flush()

    total_amount = 0
    unique_order_id = set()

    # get all the shoe storage ids from the items
    storage_ids = [item["storageId"] for item in items]
    storages = (
        db.session.query(FinishedShoeStorage)
        .filter(FinishedShoeStorage.finished_shoe_id.in_(storage_ids))
        .all()
    )
    if not storages:
        return jsonify({"message": "无成品记录"}), 400
    storage_dict = {storage.finished_shoe_id: storage for storage in storages}
    for item in items:
        storage_id = item["storageId"]
        remark = item["remark"]
        outbound_quantity = item.get("outboundQuantity", 0)
        unique_order_id.add(item["orderId"])
        storage = storage_dict.get(storage_id)
        if not storage:
            continue  # Skip if storage not found

        storage.finished_amount -= outbound_quantity
        if storage.finished_amount < 0:
            return jsonify({"message": f"仓库编号{storage_id}出库数量超过库存"}), 400
        record_detail = ShoeOutboundRecordDetail(
            shoe_outbound_record_id=outbound_record.shoe_outbound_record_id,
            outbound_amount=outbound_quantity,
            finished_shoe_storage_id=storage_id,
            remark=remark,
        )

        db.session.add(record_detail)
        db.session.flush()
        if _determine_outbound_status(storage) is True:
            storage.finished_status = 2
        total_amount += outbound_quantity
    outbound_record.outbound_amount = total_amount

    processor: EventProcessor = current_app.config["event_processor"]
    staff_id = current_user_info()[1].staff_id

    # get all the orders
    orders = (
        db.session.query(Order, FinishedShoeStorage)
        .join(
            OrderShoe,
            OrderShoe.order_id == Order.order_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .filter(Order.order_id.in_(unique_order_id))
        .all()
    )
    storage_map = {}
    order_map = {}
    for order, storage in orders:
        if order.order_id not in storage_map:
            storage_map[order.order_id] = []
        storage_map[order.order_id].append(storage)
        order_map[order.order_id] = order
    for order_id, storages in storage_map.items():
        if all(storage.finished_status == 2 for storage in storages):
            order = order_map[order_id]
            # All storages for this order are finished
            try:
                for operation in [30, 31]:
                    event = Event(
                        staff_id=staff_id,
                        handle_time=datetime.now(),
                        operation_id=operation,
                        event_order_id=order_id,
                    )
                    processor.processEvent(event)
            except Exception as e:
                logger.debug(e)
                return jsonify({"message": "推进流程失败"}), 500
    db.session.commit()
    return jsonify({"message": "success"})


@finished_storage_bp.route(
    "/warehouse/warehousemanager/getfinishedinoutboundrecords", methods=["GET"]
)
def get_finished_in_out_bound_records():
    storage_id = request.args.get("storageId")
    inbound_response = (
        db.session.query(ShoeInboundRecord, OutsourceInfo, OutsourceFactory)
        .outerjoin(
            OutsourceInfo,
            OutsourceInfo.outsource_info_id == ShoeInboundRecord.outsource_info_id,
        )
        .outerjoin(
            OutsourceFactory,
            OutsourceFactory.factory_id == OutsourceInfo.factory_id,
        )
        .filter(ShoeInboundRecord.finished_shoe_storage_id == storage_id)
        .all()
    )
    outbound_response = (
        db.session.query(ShoeOutboundRecord, OutsourceInfo, OutsourceFactory)
        .outerjoin(
            OutsourceInfo,
            OutsourceInfo.outsource_info_id == ShoeOutboundRecord.outsource_info_id,
        )
        .outerjoin(
            OutsourceFactory,
            OutsourceFactory.factory_id == OutsourceInfo.factory_id,
        )
        .filter(ShoeOutboundRecord.finished_shoe_storage_id == storage_id)
        .all()
    )

    result = {"inboundRecords": [], "outboundRecords": []}
    for row in inbound_response:
        record, _, factory = row
        factory_name = factory.factory_name if factory else None
        obj = {
            "productionType": record.inbound_type,
            "shoeInboundRId": record.shoe_inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "amount": record.inbound_amount,
            "subsequentStock": record.subsequent_stock,
            "source": factory_name,
            "remark": record.remark,
        }
        result["inboundRecords"].append(obj)

    for row in outbound_response:
        record, _, factory = row
        factory_name = factory.factory_name if factory else None
        obj = {
            "productionType": record.outbound_type,
            "shoeOutboundRId": record.shoe_outbound_rid,
            "timestamp": format_datetime(record.outbound_datetime),
            "amount": record.outbound_amount,
            "subsequentStock": record.subsequent_stock,
            "destination": factory_name,
            "picker": record.picker,
            "remark": record.remark,
        }
        result["outboundRecords"].append(obj)
    return result


@finished_storage_bp.route(
    "/warehouse/warehousemanager/completeinboundfinished", methods=["PATCH"]
)
def complete_inbound_finished():
    data = request.get_json()
    storage = FinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "order shoe storage not found"}), 400
    storage.finished_status = 1
    db.session.commit()
    return jsonify({"message": "success"})


@finished_storage_bp.route(
    "/warehouse/warehousemanager/completeoutboundfinished", methods=["PATCH"]
)
def complete_outbound_finished():
    data = request.get_json()
    storage = FinishedShoeStorage.query.get(data["storageId"])
    if not storage:
        return jsonify({"message": "order shoe storage not found"}), 400
    storage.finished_status = 2
    db.session.commit()
    return jsonify({"message": "success"})


@finished_storage_bp.route("/warehouse/getfinishedinboundrecords", methods=["GET"])
def get_finished_inbound_records():
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    inbound_rid = request.args.get("inboundRId")
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    customer_name = request.args.get("customerName")
    customer_product_name = request.args.get("customerProductName")
    order_cid = request.args.get("orderCId")
    customer_brand = request.args.get("customerBrand")
    query = (
        db.session.query(
            Order,
            Shoe.shoe_rid,
            OrderShoe.customer_product_name,
            Color.color_name,
            Customer,
            ShoeInboundRecord,
            ShoeInboundRecordDetail,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ShoeInboundRecordDetail,
            ShoeInboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .join(
            ShoeInboundRecord,
            ShoeInboundRecord.shoe_inbound_record_id
            == ShoeInboundRecordDetail.shoe_inbound_record_id,
        )
        .filter(ShoeInboundRecord.transaction_type == 1)  # 1 for inbound
        .filter(ShoeInboundRecordDetail.is_deleted == 0)  # 0 for not deleted
        .order_by(desc(ShoeInboundRecord.inbound_datetime))
    )
    if start_date and start_date != "":
        query = query.filter(ShoeInboundRecord.inbound_datetime >= start_date)
    if end_date and end_date != "":
        query = query.filter(ShoeInboundRecord.inbound_datetime <= end_date)
    if inbound_rid and inbound_rid != "":
        query = query.filter(
            ShoeInboundRecord.shoe_inbound_rid.ilike(f"%{inbound_rid}%")
        )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if customer_name and customer_name != "":
        query = query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if customer_product_name and customer_product_name != "":
        query = query.filter(
            OrderShoe.customer_product_name.ilike(f"%{customer_product_name}%")
        )
    if order_cid and order_cid != "":
        query = query.filter(Order.order_cid.ilike(f"%{order_cid}%"))
    if customer_brand and customer_brand != "":
        query = query.filter(Customer.customer_brand.ilike(f"%{customer_brand}%"))
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            order,
            shoe_rid,
            customer_product_name,
            color_name,
            customer,
            record,
            inbound_detail,
        ) = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "shoeRId": shoe_rid,
            "colorName": color_name,
            "inboundRId": record.shoe_inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "inboundDetailId": inbound_detail.record_detail_id,
            "detailAmount": inbound_detail.inbound_amount,
            "remark": inbound_detail.remark,
            "customerName": customer.customer_name,
            "customerProductName": customer_product_name,
            "customerBrand": customer.customer_brand,
            "orderCId": order.order_cid,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@finished_storage_bp.route("/warehouse/getfinishedoutboundrecords", methods=["GET"])
def get_finished_outbound_records():
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    outbound_rid = request.args.get("outboundRId")
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    customer_name = request.args.get("customerName")
    customer_product_name = request.args.get("customerProductName")
    order_cid = request.args.get("orderCId")
    customer_brand = request.args.get("customerBrand")
    query = (
        db.session.query(
            Order,
            Shoe.shoe_rid,
            Color.color_name,
            Customer,
            OrderShoe.customer_product_name,
            ShoeOutboundRecord.shoe_outbound_record_id,
            ShoeOutboundRecord.shoe_outbound_rid,
            ShoeOutboundRecord.outbound_datetime,
            ShoeOutboundRecordDetail,
        )
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .join(
            ShoeOutboundRecord,
            ShoeOutboundRecord.shoe_outbound_record_id
            == ShoeOutboundRecordDetail.shoe_outbound_record_id,
        )
        .order_by(desc(ShoeOutboundRecord.outbound_datetime))
    )
    if start_date and start_date != "":
        query = query.filter(ShoeOutboundRecord.outbound_datetime >= start_date)
    if end_date and end_date != "":
        query = query.filter(ShoeOutboundRecord.outbound_datetime <= end_date)
    if outbound_rid and outbound_rid != "":
        query = query.filter(
            ShoeOutboundRecord.shoe_outbound_rid.ilike(f"%{outbound_rid}%")
        )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if customer_name and customer_name != "":
        query = query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if customer_product_name and customer_product_name != "":
        query = query.filter(
            OrderShoe.customer_product_name.ilike(f"%{customer_product_name}%")
        )
    if order_cid and order_cid != "":
        query = query.filter(Order.order_cid.ilike(f"%{order_cid}%"))
    if customer_brand and customer_brand != "":
        query = query.filter(Customer.customer_brand.ilike(f"%{customer_brand}%"))
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []

    for row in response:
        (
            order,
            shoe_rid,
            color_name,
            customer,
            customer_product_name,
            outbound_id,
            outbound_rid,
            outbound_datetime,
            record_detail,
        ) = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderCId": order.order_cid,
            "shoeRId": shoe_rid,
            "colorName": color_name,
            "customerName": customer.customer_name,
            "customerProductName": customer_product_name,
            "outboundRId": outbound_rid,
            "outboundId": outbound_id,
            "timestamp": format_datetime(outbound_datetime),
            "detailAmount": record_detail.outbound_amount,
            "customerBrand": customer.customer_brand,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@finished_storage_bp.route(
    "/warehouse/getfinishedinboundrecordbybatchid", methods=["GET"]
)
def get_finished_inbound_record_by_batch_id():
    order_id = request.args.get("orderId")
    batch_id = request.args.get("inboundBatchId")
    response = (
        db.session.query(ShoeInboundRecord, Color)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeInboundRecord.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .filter(ShoeInboundRecord.inbound_batch_id == batch_id)
        .all()
    )
    result = {"items": [], "shoeSizeColumns": []}
    for row in response:
        record, color = row
        obj = {
            "inboundRId": record.shoe_inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "amount": record.inbound_amount,
            "subsequentStock": record.subsequent_stock,
            "remark": record.remark,
            "colorName": color.color_name,
        }
        for i in range(len(SHOESIZERANGE)):
            db_name = i + 34
            column_name = f"size_{db_name}_amount"
            obj[f"amount{i}"] = getattr(record, column_name)
        obj["totalAmount"] = record.inbound_amount
        result["items"].append(obj)

    shoe_size_result = get_order_batch_type_helper(order_id)
    resulted_filtered_columns = []
    for i in range(len(shoe_size_result)):
        resulted_filtered_columns.append(
            {"label": shoe_size_result[i]["label"], "prop": f"amount{i}"}
        )
    result["shoeSizeColumns"] = resulted_filtered_columns
    return result


@finished_storage_bp.route(
    "/warehouse/getfinishedoutboundrecordbybatchid", methods=["GET"]
)
def get_finished_outbound_record_by_batch_id():
    order_id = request.args.get("orderId")
    batch_id = request.args.get("outboundBatchId")
    response = (
        db.session.query(ShoeOutboundRecord, Shoe, Color)
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeOutboundRecord.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .filter(ShoeOutboundRecord.outbound_batch_id == batch_id)
        .all()
    )
    result = {"items": [], "shoeSizeColumns": []}
    for row in response:
        record, shoe, color = row
        obj = {
            "shoeRId": shoe.shoe_rid,
            "outboundRId": record.shoe_outbound_rid,
            "timestamp": format_datetime(record.outbound_datetime),
            "amount": record.outbound_amount,
            "subsequentStock": record.subsequent_stock,
            "remark": record.remark,
            "colorName": color.color_name,
        }
        for i in range(len(SHOESIZERANGE)):
            db_name = i + 34
            column_name = f"size_{db_name}_amount"
            obj[f"amount{i}"] = getattr(record, column_name)
        obj["totalAmount"] = record.outbound_amount
        result["items"].append(obj)

    shoe_size_result = get_order_batch_type_helper(order_id)
    resulted_filtered_columns = []
    for i in range(len(shoe_size_result)):
        resulted_filtered_columns.append(
            {"label": shoe_size_result[i]["label"], "prop": f"amount{i}"}
        )
    result["shoeSizeColumns"] = resulted_filtered_columns
    return result


@finished_storage_bp.route("/warehouse/getmultipleshoesizecolumns", methods=["GET"])
def get_multiple_shoe_size_columns():
    order_id = request.args.get("orderId")
    shoe_size_names = get_order_batch_type_helper(order_id)
    query = (
        db.session.query(FinishedShoeStorage)
        .outerjoin(
            ShoeOutboundRecord,
            FinishedShoeStorage.finished_shoe_id
            == ShoeOutboundRecord.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .filter(Order.order_id == order_id)
    )
    for i in range(len(SHOESIZERANGE)):
        db_name = i + 34
        column_name = f"size_{db_name}_amount"
        query = query.add_columns(
            func.coalesce(func.sum(getattr(ShoeOutboundRecord, column_name)), 0)
        )
    response = query.group_by(FinishedShoeStorage.finished_shoe_id).all()
    result = {}
    for row in response:
        storage, *shoe_size_columns = row
        result[storage.finished_shoe_id] = []
        for i in range(len(shoe_size_names)):
            shoe_size_db_name = i + 34
            obj = {
                "typeId": shoe_size_names[i]["id"],
                "typeName": shoe_size_names[i]["type"],
                "shoeSizeName": shoe_size_names[i]["label"],
                "predictQuantity": getattr(
                    storage, f"size_{shoe_size_db_name}_estimated_amount"
                ),
                "outboundedQuantity": int(shoe_size_columns[i]),
                "actualQuantity": getattr(
                    storage, f"size_{shoe_size_db_name}_actual_amount"
                ),
                "currentQuantity": getattr(storage, f"size_{shoe_size_db_name}_amount"),
            }
            result[storage.finished_shoe_id].append(obj)
    return result


@finished_storage_bp.route("/warehouse/gettotalstockoffinishedstorage", methods=["GET"])
def get_total_stock_of_finished_storage():
    """
    Get the total stock of semifinished storage.
    """
    total_stock = db.session.query(
        func.sum(FinishedShoeStorage.finished_amount)
    ).scalar()
    if total_stock is None:
        total_stock = 0
    return jsonify({"totalStock": total_stock})


@finished_storage_bp.route(
    "/warehouse/getremainingamountoffinishedstorage", methods=["GET"]
)
def get_remaining_amount_of_finished_storage():
    """
    Get the remaining amount of semifinished storage.
    """
    response = (
        db.session.query(
            func.sum(
                FinishedShoeStorage.finished_estimated_amount
                - FinishedShoeStorage.finished_actual_amount
            )
        )
        .filter(FinishedShoeStorage.finished_actual_amount > 0)
        .scalar()
    )
    result = response if response is not None else 0
    return jsonify({"remainingAmount": result})


@finished_storage_bp.route("/warehouse/deletefinishedinbounddetail", methods=["DELETE"])
def delete_finished_inbound_detail():
    """
    Delete a finished inbound detail.
    """
    detail_id = request.args.get("inboundDetailId")
    if not detail_id:
        return jsonify({"message": "参数错误"}), 400

    response = (
        db.session.query(
            ShoeInboundRecord,
            ShoeInboundRecordDetail,
            FinishedShoeStorage,
            ShoeOutboundRecordDetail,
        )
        .join(
            ShoeInboundRecordDetail,
            ShoeInboundRecord.shoe_inbound_record_id
            == ShoeInboundRecordDetail.shoe_inbound_record_id,
        )
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeInboundRecordDetail.finished_shoe_storage_id,
        )
        .outerjoin(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .filter(ShoeInboundRecordDetail.record_detail_id == detail_id)
        .first()
    )

    if not response:
        return jsonify({"message": "入库记录不存在"}), 404

    record, detail, storage, outbound_detail = response

    if outbound_detail:
        return jsonify({"message": "订单已出库，无法删除入库记录"}), 409

    amount = detail.inbound_amount
    storage.finished_actual_amount -= amount
    storage.finished_amount -= amount
    storage.finished_status = 0

    # 标记入库记录明细为已删除
    detail.is_deleted = 1

    # 新增撤回入库单记录
    timestamp = format_datetime(datetime.now())
    formatted_timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    rid = "FIR" + formatted_timestamp + "T0"
    reversal_record = ShoeInboundRecord(
        shoe_inbound_rid=rid,
        inbound_datetime=formatted_timestamp,
        inbound_type=record.inbound_type,
        inbound_amount=-amount,  # 负数表示撤回
        transaction_type=2,  # 2表示撤回入库
        related_inbound_record_id=record.shoe_inbound_record_id,
    )
    db.session.add(reversal_record)
    db.session.flush()
    new_detail = ShoeInboundRecordDetail(
        shoe_inbound_record_id=reversal_record.shoe_inbound_record_id,
        finished_shoe_storage_id=storage.finished_shoe_id,
        inbound_amount=-amount,  # 负数表示撤回
        is_deleted=0,
    )
    db.session.add(new_detail)
    db.session.commit()
    return jsonify({"message": "删除成功"})


@finished_storage_bp.route("/product/getstoragestatusoptions", methods=["GET"])
def get_storage_status_options():
    result = {"storageStatusOptions": [], "storageStatusEnum": {}}
    for key, value in FINISHED_STORAGE_STATUS.items():
        obj = {
            "value": key,
            "label": value,
        }
        result["storageStatusOptions"].append(obj)

    for key, value in FINISHED_STORAGE_STATUS_ENUM.items():
        result["storageStatusEnum"][key] = value
    return result

@finished_storage_bp.route("/product/getoutboundauditstatusoptions", methods=["GET"])
def get_outbound_audit_status_options():
    result = {"productOutboundAuditStatusOptions": [], "productOutboundAuditStatusEnum": {}}
    for key, value in PRODUCT_OUTBOUND_AUDIT_STATUS.items():
        obj = {
            "value": key,
            "label": value,
        }
        result["productOutboundAuditStatusOptions"].append(obj)
    for key, value in PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.items():
        result["productOutboundAuditStatusEnum"][key] = value
    return result

def _sum_size_cols(detail_alias):
    # 尺码 34~46 汇总；None 当 0
    cols = []
    for size in SHOESIZERANGE:
        col = getattr(detail_alias, f"size_{size}_amount")
        cols.append(func.coalesce(col, 0))
    total = cols[0]
    for c in cols[1:]:
        total = total + c
    return total


@finished_storage_bp.route("/warehouse/getshoeinoutbounddetail", methods=["GET"])
def get_shoe_inoutbound_detail():
    """
    入/出库明细（逐条 detail 展示，总数，不展开尺码）
    查询参数：
      - mode: month | year
      - month: 'YYYY-MM' (mode=month 时必填)
      - year: 'YYYY'     (mode=year  时必填)
      - direction: '' | 'IN' | 'OUT'
      - keyword: 仅用于按 rid(业务单号) 模糊查询
      - shoeRid: 工厂型号 模糊查询
      - color:   颜色 模糊查询
      - page, pageSize
    返回：
      {
        code, message, total, list: [...],
        stat: {
          inQty, outQty,
          inAmountByCurrency:  {"CNY": 123.45, "USD": 0, "EUR": 0, ...},
          outAmountByCurrency: {"CNY":  67.89, "USD": 0, "EUR": 0, ...}
        }
      }
    """
    # ---- 参数 ----
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 20, type=int)
    mode = (request.args.get("mode") or "month").lower()
    month = request.args.get("month")  # 'YYYY-MM'
    year = request.args.get("year")    # 'YYYY'
    direction = (request.args.get("direction") or "").upper()  # '', 'IN', 'OUT'

    # 关键词仅匹配 rid（不再匹配 recordId/detailId）
    keyword = (request.args.get("keyword") or "").strip()

    # 新增：工厂型号与颜色筛选
    shoe_rid_kw = (request.args.get("shoeRid") or "").strip()
    color_kw = (request.args.get("color") or "").strip()
    category_kw = (request.args.get("category") or "").strip()

    # ---- 时间范围 ----
    try:
        if mode == "month":
            if not month:
                return jsonify({"code": 400, "message": "month 必填（YYYY-MM）"}), 400
            start_dt = datetime.strptime(month + "-01", "%Y-%m-%d")
            end_dt = start_dt + relativedelta(months=1)
        elif mode == "year":
            if not year:
                return jsonify({"code": 400, "message": "year 必填（YYYY）"}), 400
            start_dt = datetime(int(year), 1, 1)
            end_dt = datetime(int(year) + 1, 1, 1)
        else:
            return jsonify({"code": 400, "message": "mode 只支持 month / year"}), 400
    except Exception:
        return jsonify({"code": 400, "message": "时间参数格式错误"}), 400

    # ========= 工具 =========
    def _sum_size_cols(detail_cls):
        return sum(getattr(detail_cls, f"size_{i}_amount", 0) or 0 for i in SHOESIZERANGE)

    # ========= 合计尺码列表达式 =========
    inbound_total_qty = func.coalesce(
        ShoeInboundRecordDetail.inbound_amount,
        _sum_size_cols(ShoeInboundRecordDetail)
    )
    outbound_total_qty = func.coalesce(
        ShoeOutboundRecordDetail.outbound_amount,
        _sum_size_cols(ShoeOutboundRecordDetail)
    )

    # ========= 入库明细（含批次链路与 batch_type_name） =========
    inbound_detail_q = (
        db.session.query(
            literal("IN").label("direction"),
            ShoeInboundRecord.shoe_inbound_record_id.label("record_id"),
            ShoeInboundRecordDetail.record_detail_id.label("detail_id"),
            ShoeInboundRecord.shoe_inbound_rid.label("rid"),
            Shoe.shoe_rid.label("shoeRid"),
            Color.color_name.label("color"),
            Shoe.shoe_designer.label("designer"),  # 设计师
            OrderShoe.adjust_staff.label("adjuster"),  # 调版师
            inbound_total_qty.cast(Integer).label("detail_quantity"),
            OrderShoeType.unit_price.label("unit_price"),           # 单价
            ShoeInboundRecord.inbound_datetime.label("occur_time"),
            OrderShoeType.currency_type.label("currency"),          # 工单币种
            ShoeInboundRecord.remark.label("remark"),
            literal(None).label("picker"),
            BatchInfoType.batch_info_type_name.label("batch_type_name"),  # 用于判定男女童
        )
        .select_from(ShoeInboundRecord)
        .join(
            ShoeInboundRecordDetail,
            ShoeInboundRecordDetail.shoe_inbound_record_id == ShoeInboundRecord.shoe_inbound_record_id
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == ShoeInboundRecordDetail.finished_shoe_storage_id
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        # —— 批次链路（外连接，避免无批次被过滤）——
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id
        )
        .outerjoin(
            BatchInfoType,
            BatchInfoType.batch_info_type_id == PackagingInfo.batch_info_type_id
        )
        .filter(
            ShoeInboundRecord.inbound_datetime >= start_dt,
            ShoeInboundRecord.inbound_datetime < end_dt
        )
    )

    # ========= 出库明细（含批次链路与 batch_type_name） =========
    outbound_detail_q = (
        db.session.query(
            literal("OUT").label("direction"),
            ShoeOutboundRecord.shoe_outbound_record_id.label("record_id"),
            ShoeOutboundRecordDetail.record_detail_id.label("detail_id"),
            ShoeOutboundRecord.shoe_outbound_rid.label("rid"),
            Shoe.shoe_rid.label("shoeRid"),
            Color.color_name.label("color"),
            Shoe.shoe_designer.label("designer"),  # 设计师
            OrderShoe.adjust_staff.label("adjuster"),  # 调版师
            outbound_total_qty.cast(Integer).label("detail_quantity"),
            OrderShoeType.unit_price.label("unit_price"),           # 单价
            ShoeOutboundRecord.outbound_datetime.label("occur_time"),
            OrderShoeType.currency_type.label("currency"),          # 工单币种
            ShoeOutboundRecord.remark.label("remark"),
            ShoeOutboundRecord.picker.label("picker"),
            BatchInfoType.batch_info_type_name.label("batch_type_name"),  # 用于判定男女童
        )
        .select_from(ShoeOutboundRecord)
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.shoe_outbound_record_id == ShoeOutboundRecord.shoe_outbound_record_id
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == ShoeOutboundRecordDetail.finished_shoe_storage_id
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        # —— 批次链路（外连接）——
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id
        )
        .outerjoin(
            BatchInfoType,
            BatchInfoType.batch_info_type_id == PackagingInfo.batch_info_type_id
        )
        .filter(
            ShoeOutboundRecord.outbound_datetime >= start_dt,
            ShoeOutboundRecord.outbound_datetime < end_dt
        )
    )

    # ---- 合并 ----
    if direction == "IN":
        union_query = inbound_detail_q
    elif direction == "OUT":
        union_query = outbound_detail_q
    else:
        union_query = inbound_detail_q.union_all(outbound_detail_q)

    u = union_query.subquery("u")

    # ---- 筛选（仅 rid / shoeRid / color）----
    wheres = []
    if keyword:
        wheres.append(u.c.rid.ilike(f"%{keyword}%"))
    if shoe_rid_kw:
        wheres.append(u.c.shoeRid.ilike(f"%{shoe_rid_kw}%"))
    if color_kw:
        wheres.append(u.c.color.ilike(f"%{color_kw}%"))
    if category_kw == "男鞋":
        wheres.append(u.c.batch_type_name.like("%男%"))
    elif category_kw == "女鞋":
        wheres.append(u.c.batch_type_name.like("%女%"))
    elif category_kw == "童鞋":
        wheres.append(u.c.batch_type_name.like("%童%"))
    elif category_kw == "其它":
        # 其它：既不含“男/女/童”，或为空
        wheres.append(
            or_(
                u.c.batch_type_name.is_(None),
                and_(
                    not_(u.c.batch_type_name.like("%男%")),
                    not_(u.c.batch_type_name.like("%女%")),
                    not_(u.c.batch_type_name.like("%童%")),
                ),
            )
        )

    # ---- 数量统计（SQL端）----
    in_qty_expr = case((u.c.direction == literal("IN"), u.c.detail_quantity), else_=0)
    out_qty_expr = case((u.c.direction == literal("OUT"), u.c.detail_quantity), else_=0)

    stat_qty_row = (
        db.session.query(
            func.coalesce(func.sum(in_qty_expr), 0),
            func.coalesce(func.sum(out_qty_expr), 0),
        )
        .select_from(u)
        .filter(*wheres)
        .first()
    )
    in_qty_total = int(stat_qty_row[0] or 0)
    out_qty_total = int(stat_qty_row[1] or 0)

    # ---- 总条数（分页用）----
    total = (
        db.session.query(func.count(literal(1)))
        .select_from(u)
        .filter(*wheres)
        .scalar()
    ) or 0

    # ---- 列表数据（分页）----
    rows = (
        db.session.query(u)
        .filter(*wheres)
        .order_by(u.c.occur_time.desc(), u.c.record_id.desc(), u.c.detail_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # ---- 列表序列化（含“category”= 男/女/童/其它）----
    result_list = []
    for r in rows:
        unit_price = Decimal(r.unit_price or 0.0)
        qty = int(r.detail_quantity or 0)
        detail_amount = unit_price * qty
        currency_norm = normalize_currency(r.currency)
        result_list.append({
            "direction": r.direction,
            "recordId": r.record_id,
            "detailId": r.detail_id,
            "rid": r.rid,
            "designer": r.designer or "",     # 设计师
            "adjuster": r.adjuster or "",     # 调版师
            "shoeRid": r.shoeRid or "",
            "color": r.color or "",
            "category": normalize_category_by_batch_type(getattr(r, "batch_type_name", "")),  # ← 男女童
            "quantity": qty,
            "amount": round(detail_amount, 3),  # 单条金额
            "unitPrice": unit_price,
            "occurTime": r.occur_time.isoformat(sep=" "),
            "currency": currency_norm,
            "remark": r.remark or "",
            "picker": r.picker or "",
        })

    # ---- 金额统计（Python端按币种分别累计）----
    amt_rows = (
        db.session.query(u.c.direction, u.c.detail_quantity, u.c.unit_price, u.c.currency)
        .filter(*wheres)
        .all()
    )

    in_amount_by_ccy: Dict[str, Decimal] = {}
    out_amount_by_ccy: Dict[str, Decimal] = {}

    for ar in amt_rows:
        qty = int(ar.detail_quantity or 0)
        unit_price = Decimal(ar.unit_price or 0.0)
        amt = unit_price * qty
        ccy = normalize_currency(ar.currency)
        if ar.direction == "IN":
            in_amount_by_ccy[ccy] = round(in_amount_by_ccy.get(ccy, Decimal(0.0)) + amt, 3)
        elif ar.direction == "OUT":
            out_amount_by_ccy[ccy] = round(out_amount_by_ccy.get(ccy, Decimal(0.0)) + amt, 3)

    return jsonify({
        "code": 200,
        "message": "ok",
        "list": result_list,
        "total": int(total),
        "stat": {
            "inQty": in_qty_total,
            "outQty": out_qty_total,
            "inAmountByCurrency": in_amount_by_ccy,   # CNY/RMB、USD/USA 已统一
            "outAmountByCurrency": out_amount_by_ccy,
        }
    })

    
@finished_storage_bp.route("/warehouse/getshoeinoutboundsummarybymodel", methods=["GET"])
def get_shoe_inoutbound_summary_by_model():
    """
    出入库汇总（按型号 / 型号+颜色）
    - mode: month | year
    - month: 'YYYY-MM' (mode=month 必填)
    - year:  'YYYY'    (mode=year  必填)
    - direction: '' | 'IN' | 'OUT'
    - keyword: rid 模糊
    - shoeRid: 型号模糊
    - color:  颜色模糊
    - groupBy: 'model' | 'model_color'  默认 model
    返回结构见你原注释
    """
    # ====== 参数 ======
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 20, type=int)
    mode = (request.args.get("mode") or "month").lower()
    month = request.args.get("month")
    year  = request.args.get("year")
    direction = (request.args.get("direction") or "").upper()  # '', IN, OUT
    keyword = (request.args.get("keyword") or "").strip()      # rid 模糊
    shoe_rid_kw = (request.args.get("shoeRid") or "").strip()
    color_kw = (request.args.get("color") or "").strip()
    group_by = (request.args.get("groupBy") or "model").lower()  # 'model'|'model_color'
    category_kw = (request.args.get("category") or "").strip()

    # ====== 时间范围 ======
    try:
        if mode == "month":
            if not month:
                return jsonify({"code": 400, "message": "month 必填（YYYY-MM）"}), 400
            start_dt = datetime.strptime(month + "-01", "%Y-%m-%d")
            end_dt = start_dt + relativedelta(months=1)
        elif mode == "year":
            if not year:
                return jsonify({"code": 400, "message": "year 必填（YYYY）"}), 400
            start_dt = datetime(int(year), 1, 1)
            end_dt = datetime(int(year) + 1, 1, 1)
        else:
            return jsonify({"code": 400, "message": "mode 只支持 month / year"}), 400
    except Exception:
        return jsonify({"code": 400, "message": "时间参数格式错误"}), 400

    # ====== 通用工具：尺码汇总、币种归一化、鞋类归一化 ======
    def _sum_size_cols(detail_cls):
        return sum(
            getattr(detail_cls, f"size_{i}_amount", 0) or 0
            for i in SHOESIZERANGE
        )

    # ====== 入库明细 ======
    inbound_total_qty = func.coalesce(
        ShoeInboundRecordDetail.inbound_amount,
        _sum_size_cols(ShoeInboundRecordDetail)
    )
    inbound_q = (
        db.session.query(
            literal("IN").label("direction"),
            Shoe.shoe_rid.label("shoeRid"),
            Color.color_name.label("color"),
            Shoe.shoe_designer.label("designer"),           # 设计师
            OrderShoe.adjust_staff.label("adjuster"),       # 调版师
            inbound_total_qty.cast(Integer).label("qty"),
            OrderShoeType.unit_price.label("unit_price"),
            OrderShoeType.currency_type.label("currency"),
            ShoeInboundRecord.shoe_inbound_rid.label("rid"),
            ShoeInboundRecord.inbound_datetime.label("occur_time"),
            BatchInfoType.batch_info_type_name.label("batch_type_name"),  # ← 新增：用于判定鞋类
        )
        .select_from(ShoeInboundRecord)
        .join(
            ShoeInboundRecordDetail,
            ShoeInboundRecordDetail.shoe_inbound_record_id == ShoeInboundRecord.shoe_inbound_record_id
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == ShoeInboundRecordDetail.finished_shoe_storage_id
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        # —— 批次链路（外连接，避免无批次数据被过滤）——
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id
        )
        .outerjoin(
            BatchInfoType,
            BatchInfoType.batch_info_type_id == PackagingInfo.batch_info_type_id
        )
        .filter(
            ShoeInboundRecord.inbound_datetime >= start_dt,
            ShoeInboundRecord.inbound_datetime < end_dt
        )
    )

    # ====== 出库明细 ======
    outbound_total_qty = func.coalesce(
        ShoeOutboundRecordDetail.outbound_amount,
        _sum_size_cols(ShoeOutboundRecordDetail)
    )
    outbound_q = (
        db.session.query(
            literal("OUT").label("direction"),
            Shoe.shoe_rid.label("shoeRid"),
            Color.color_name.label("color"),
            Shoe.shoe_designer.label("designer"),
            OrderShoe.adjust_staff.label("adjuster"),
            outbound_total_qty.cast(Integer).label("qty"),
            OrderShoeType.unit_price.label("unit_price"),
            OrderShoeType.currency_type.label("currency"),
            ShoeOutboundRecord.shoe_outbound_rid.label("rid"),
            ShoeOutboundRecord.outbound_datetime.label("occur_time"),
            BatchInfoType.batch_info_type_name.label("batch_type_name"),  # ← 新增：用于判定鞋类
        )
        .select_from(ShoeOutboundRecord)
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.shoe_outbound_record_id == ShoeOutboundRecord.shoe_outbound_record_id
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == ShoeOutboundRecordDetail.finished_shoe_storage_id
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        # —— 批次链路（外连接）——
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id
        )
        .outerjoin(
            BatchInfoType,
            BatchInfoType.batch_info_type_id == PackagingInfo.batch_info_type_id
        )
        .filter(
            ShoeOutboundRecord.outbound_datetime >= start_dt,
            ShoeOutboundRecord.outbound_datetime < end_dt
        )
    )

    # 方向过滤（尽量前置减数据量）
    if direction == "IN":
        base_q = inbound_q
    elif direction == "OUT":
        base_q = outbound_q
    else:
        base_q = inbound_q.union_all(outbound_q)

    u = base_q.subquery("u")

    # 关键字等过滤
    wheres = []
    if keyword:
        wheres.append(u.c.rid.ilike(f"%{keyword}%"))
    if shoe_rid_kw:
        wheres.append(u.c.shoeRid.ilike(f"%{shoe_rid_kw}%"))
    if color_kw:
        wheres.append(u.c.color.ilike(f"%{color_kw}%"))
    if category_kw == "男鞋":
        wheres.append(u.c.batch_type_name.like("%男%"))
    elif category_kw == "女鞋":
        wheres.append(u.c.batch_type_name.like("%女%"))
    elif category_kw == "童鞋":
        wheres.append(u.c.batch_type_name.like("%童%"))
    elif category_kw == "其它":
        # 其它：为空或不包含“男/女/童”
        wheres.append(
            or_(
                u.c.batch_type_name.is_(None),
                and_(
                    not_(u.c.batch_type_name.like("%男%")),
                    not_(u.c.batch_type_name.like("%女%")),
                    not_(u.c.batch_type_name.like("%童%")),
                ),
            )
        )

    # 取明细（按时间倒序只是为了稳定性）
    records = (
        db.session.query(u)
        .filter(*wheres)
        .order_by(u.c.occur_time.desc())
        .all()
    )

    def group_key(row):
        if group_by == "model_color":
            return (row.shoeRid or "-", row.color or "-")
        return (row.shoeRid or "-", None)

    # 聚合
    agg = {}  # key -> dict
    total_in_qty = 0
    total_out_qty = 0
    total_in_amt = defaultdict(Decimal)   # 货币 -> 金额
    total_out_amt = defaultdict(Decimal)

    for record in records:
        key = group_key(record)
        if key not in agg:
            agg[key] = {
                "shoeRid": key[0],
                "color": key[1],  # 可能为 None
                "designer": record.designer or "",   # 设计师
                "adjuster": record.adjuster or "",   # 调版师
                "category": normalize_category_by_batch_type(getattr(record, "batch_type_name", "")),  # ← 新增
                "unitPrice": Decimal(record.unit_price or 0.0),
                "inQty": 0,
                "outQty": 0,
                "inAmountByCurrency": defaultdict(Decimal),
                "outAmountByCurrency": defaultdict(Decimal),
            }
        item = agg[key]

        qty = int(record.qty or 0)
        unit_price = Decimal(record.unit_price or 0.0)
        cur = normalize_currency(record.currency)
        amount = round(unit_price * qty, 3)

        if record.direction == "IN":
            item["inQty"] += qty
            item["inAmountByCurrency"][cur] += amount
            total_in_qty += qty
            total_in_amt[cur] += amount
        else:
            item["outQty"] += qty
            item["outAmountByCurrency"][cur] += amount
            total_out_qty += qty
            total_out_amt[cur] += amount

    # 构造列表并分页
    rows = []
    for _, it in agg.items():
        in_map = {c: round(v, 3) for c, v in it["inAmountByCurrency"].items()}
        out_map = {c: round(v, 3) for c, v in it["outAmountByCurrency"].items()}
        keys = set(in_map.keys()) | set(out_map.keys())
        net_map = {c: round(in_map.get(c, 0) - out_map.get(c, 0), 3) for c in keys}
        rows.append({
            "shoeRid": it["shoeRid"],
            "color": it["color"] or "",
            "designer": it["designer"] or "",
            "adjuster": it["adjuster"] or "",
            "category": it["category"],                 # 男鞋 / 女鞋 / 童鞋 / 其它
            "unitPrice": it["unitPrice"],
            "inQty": it["inQty"],
            "outQty": it["outQty"],
            "netQty": it["inQty"] - it["outQty"],
            "inAmountByCurrency": in_map,
            "outAmountByCurrency": out_map,
            "netAmountByCurrency": net_map,
        })

    # 排序：净数量降序，其次型号、颜色
    rows.sort(key=lambda x: (-x["netQty"], x["shoeRid"], x.get("color", "")))

    total_groups = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]

    # 整体汇总 stat
    keys = set(total_in_amt.keys()) | set(total_out_amt.keys())
    total_net_amt = {c: round(total_in_amt.get(c, 0) - total_out_amt.get(c, 0), 3) for c in keys}

    return jsonify({
        "code": 200,
        "message": "ok",
        "list": page_rows,
        "total": total_groups,
        "stat": {
            "inQty": int(total_in_qty),
            "outQty": int(total_out_qty),
            "netQty": int(total_in_qty - total_out_qty),
            "inAmountByCurrency": {c: round(v, 3) for c, v in total_in_amt.items()},
            "outAmountByCurrency": {c: round(v, 3) for c, v in total_out_amt.items()},
            "netAmountByCurrency": total_net_amt,
        }
    })

    
@finished_storage_bp.route("/warehouse/export/finished-inbound", methods=["GET"])
def export_finished_inbound_records():
    filters = {
        "order_rid": request.args.get("orderRId"),
        "shoe_rid": request.args.get("shoeRId"),
        "start_date": request.args.get("startDate"),
        "end_date": request.args.get("endDate"),
        "inbound_rid": request.args.get("inboundRId"),
        "customer_name": request.args.get("customerName"),
        "customer_product_name": request.args.get("customerProductName"),
        "order_cid": request.args.get("orderCId"),
        "customer_brand": request.args.get("customerBrand"),
    }
    bio, filename = build_finished_inbound_excel(filters)
    return send_file(bio, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@finished_storage_bp.route("/warehouse/export/finished-outbound", methods=["GET"])
def export_finished_outbound_records():
    filters = {
        "order_rid": request.args.get("orderRId"),
        "shoe_rid": request.args.get("shoeRId"),
        "start_date": request.args.get("startDate"),
        "end_date": request.args.get("endDate"),
        "outbound_rid": request.args.get("outboundRId"),
        "customer_name": request.args.get("customerName"),
        "customer_product_name": request.args.get("customerProductName"),
        "order_cid": request.args.get("orderCId"),
        "customer_brand": request.args.get("customerBrand"),
    }
    bio, filename = build_finished_outbound_excel(filters)
    return send_file(bio, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@finished_storage_bp.route("/warehouse/export/finished-inout", methods=["GET"])
def export_finished_inout_records():
    filters = {
        "order_rid": request.args.get("orderRId"),
        "shoe_rid": request.args.get("shoeRId"),
        "start_date": request.args.get("startDate"),
        "end_date": request.args.get("endDate"),
        "inbound_rid": request.args.get("inboundRId"),
        "outbound_rid": request.args.get("outboundRId"),
        "customer_name": request.args.get("customerName"),
        "customer_product_name": request.args.get("customerProductName"),
        "order_cid": request.args.get("orderCId"),
        "customer_brand": request.args.get("customerBrand"),
    }
    bio, filename = build_finished_inout_excel(filters)
    return send_file(bio, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
@finished_storage_bp.route("/warehouse/downloadfinishedoutboundrecordbybatchid", methods=["POST"])
def download_finished_outbound_record_by_batch_id():
    """
    接口只负责：
    1. 接收前端参数
    2. 调用生成 Excel 的函数
    3. send_file 返回给前端
    """
    data = request.get_json(silent=True) or {}

    outbound_record_ids = data.get("outboundRecordIds")  # [1,2,3]
    outbound_rids = data.get("outboundRIds")  # 可选，业务单号过滤
    

    if not outbound_record_ids:
        return jsonify({"error": "缺少参数：outboundRecordIds"}), 400
    # 模板路径：按你的项目实际位置来
    # 你说模板叫“出货清单模板.xlsx”，比如你放在 app 根目录 / templates/excel 里
    template_path = os.path.join(
        FILE_STORAGE_PATH, "出货清单模板.xlsx"
    )
    # 如果你直接放在项目根目录，也可以这么写：
    # template_path = os.path.join(current_app.root_path, "出货清单模板.xlsx")

    try:
        excel_io, filename = generate_finished_outbound_excel(
            template_path=template_path,
            outbound_record_ids=outbound_record_ids,
            outbound_rids=outbound_rids,
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        # 比如未找到记录
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        # 兜底错误，方便调试
        current_app.logger.exception("导出出货清单失败")
        return jsonify({"error": "导出出货清单失败"}), 500

    return send_file(
        excel_io,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )






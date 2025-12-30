from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
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
    build_finished_inout_excel,
    build_finished_inout_summary_by_model_excel,
)
from general_document.shoe_outbound_list import (
    generate_finished_outbound_apply_excel,
    generate_finished_outbound_excel,
)
from shared_apis.utility_func import normalize_category_by_batch_type
from shared_apis.utility_func import normalize_currency
import os

finished_storage_bp = Blueprint("finished_storage_bp", __name__)


@finished_storage_bp.route("/warehouse/getfinishedstorages", methods=["GET"])
def get_finished_in_out_overview():
    """
    鏌ヨ鎴愬搧鍏?鍑哄簱鎬昏锛堟敮鎸佲€滀粎鍙叆搴撯€濊繃婊わ級
    inboundableOnly:
        0: 涓嶉檺锛堥粯璁わ級
        1: 浠呭彲鍏ュ簱锛坒inished_actual_amount < finished_estimated_amount锛?
    showAll:
        0: 鍚庣涓嶉澶栭檺鍒?
        1: 浠呮樉绀哄綋鍓嶄粨鏈夊簱瀛橈紙finished_amount > 0锛?
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

    # 瀹屾垚浜嬩欢锛堜粎鍙?operation_id=22 鐨勬渶鏂版椂闂达級
    ev_subq = (
        db.session.query(
            Event.event_order_id.label("order_id"),
            func.max(Event.handle_time).label("finished_time"),
        )
        .filter(Event.operation_id == 22)
        .group_by(Event.event_order_id)
        .subquery()
    )

    # 鍩虹鑱旂粨鏌ヨ锛堟敞鎰忥細鐢ㄥ畠鏉ユ瀯寤衡€滆繃婊ゆ潯浠朵竴鑷寸殑 ID 瀛愭煡璇⑩€濆拰鈥滄渶缁堟槑缁嗘煡璇⑩€濓級
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
            FinishedShoeStorage.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .join(
            BatchInfoType, BatchInfoType.batch_info_type_id == Order.batch_info_type_id
        )
        .outerjoin(ev_subq, ev_subq.c.order_id == Order.order_id)
    )

    # 鈥斺€?鍔ㄦ€佽繃婊ゆ潯浠讹紙涓庡墠绔竴鑷达級鈥斺€?
    if order_rid:
        base_query = base_query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid:
        base_query = base_query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if customer_name:
        base_query = base_query.filter(
            Customer.customer_name.ilike(f"%{customer_name}%")
        )
    if customer_product_name:
        base_query = base_query.filter(
            OrderShoe.customer_product_name.ilike(f"%{customer_product_name}%")
        )
    if storage_status_num is not None and storage_status_num > -1:
        base_query = base_query.filter(
            FinishedShoeStorage.finished_status == storage_status_num
        )
    if order_cid:
        base_query = base_query.filter(Order.order_cid.ilike(f"%{order_cid}%"))
    if customer_brand:
        base_query = base_query.filter(
            Customer.customer_brand.ilike(f"%{customer_brand}%")
        )

    if category_kw == "鐢烽瀷":
        base_query = base_query.filter(BatchInfoType.batch_info_type_name.like("%鐢?"))
    elif category_kw == "濂抽瀷":
        base_query = base_query.filter(BatchInfoType.batch_info_type_name.like("%濂?"))
    elif category_kw == "绔ラ瀷":
        base_query = base_query.filter(BatchInfoType.batch_info_type_name.like("%绔?"))
    elif category_kw == "鍏跺畠":
        base_query = base_query.filter(
            or_(
                BatchInfoType.batch_info_type_name.is_(None),
                and_(
                    not_(BatchInfoType.batch_info_type_name.like("%鐢?")),
                    not_(BatchInfoType.batch_info_type_name.like("%濂?")),
                    not_(BatchInfoType.batch_info_type_name.like("%绔?")),
                ),
            )
        )

    # 浠呮樉绀哄綋鍓嶄粨鏈夊簱瀛?
    if show_all == 1:
        base_query = base_query.filter(FinishedShoeStorage.finished_amount > 0)

    # 浠呮樉绀衡€滃彲鍏ュ簱鈥?
    if inboundable_only == 1:
        base_query = base_query.filter(
            FinishedShoeStorage.finished_actual_amount
            < FinishedShoeStorage.finished_estimated_amount
        )
        # 濡傞渶鐢ㄢ€滄瑺鏁?> 0鈥濇浛浠ｏ紝鍙啓锛?
        # base_query = base_query.filter(
        #     (FinishedShoeStorage.finished_estimated_amount - FinishedShoeStorage.finished_actual_amount) > 0
        # )

    # 鈥斺€?鍏堝仛鈥淚D 瀛愭煡璇?+ 鍘婚噸璁℃暟鈥?鈥斺€旓紙閬垮厤 DISTINCT + JOIN 鍒嗛〉娣蜂贡锛?
    id_subq = (
        base_query.with_entities(
            FinishedShoeStorage.finished_shoe_id.label("sid"),
            Order.order_rid.label("order_rid_for_sort"),
        )
        .distinct()
        .subquery()
    )

    # 璁℃暟锛堝幓閲嶅悗锛?
    total = db.session.query(func.count()).select_from(id_subq).scalar()

    # 鍙栧綋椤典富閿紙鍙寜 order_rid 鎺掑簭锛屼篃鍙敼涓哄垱寤烘椂闂寸瓑锛?
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

    # 鈥斺€?鐢ㄥ綋椤典富閿洖鏌ュ畬鏁存槑缁?鈥斺€旓紙涓庡師 base_query 鍚屾牱鐨勫垪锛?
    page_query = base_query.filter(
        FinishedShoeStorage.finished_shoe_id.in_(page_ids)
    ).order_by(Order.order_rid.asc())
    rows = page_query.all()

    # 鈥斺€?缁勮杩斿洖 鈥斺€?
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
        remaining_amount = max(estimated - actual, 0)  # 鉁?淇

        # 娉ㄦ剰锛歜atch_info 涓虹鐞嗚繖涓€鏈路锛岀敤鍚勭鏉垮垎绫伙紝娌℃湁鍙傝€冭繃鍘绘椂鐨勬暟鎹拷
        raw_batch_name = getattr(batch_info, "batch_info_type_name", "") or ""
        batch_type = normalize_category_by_batch_type(raw_batch_name)

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
    page = request.args.get("page", type=int, default=1)
    number = request.args.get("pageSize", type=int, default=20)
    order_rid = request.args.get("orderRId")
    order_cid = request.args.get("orderCId")
    customer_name = request.args.get("customerName")
    customer_brand = request.args.get("customerBrand")
    audit_status_num = request.args.get("auditStatusNum", type=int)
    storage_status_num = request.args.get("storageStatusNum", type=int)

    # ====== 璁㈠崟鎬婚噺锛堟寜閰嶇爜鎬诲弻鏁帮級 ======
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

    # ====== 鎴愬搧鍏ュ簱 / 褰撳墠搴撳瓨 姹囨€?======
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
            FinishedShoeStorage.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .group_by(Order.order_id)
        .subquery()
    )

    # ====== 鍑哄簱鎬婚噺姹囨€伙紙鎸夎鍗曪級 ======
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
            FinishedShoeStorage.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .outerjoin(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == FinishedShoeStorage.finished_shoe_id,
        )
        .group_by(Order.order_id)
        .subquery()
    )

    # ====== 鍑哄簱鐢宠鑱氬悎锛堟寜璁㈠崟锛涗粠鏄庣粏鍙嶆帹璁㈠崟锛?======
    apply_agg_subquery = (
        db.session.query(
            Order.order_id.label("order_id"),
            # 褰撳墠璁㈠崟鎵€鏈夆€滃湪娴佺▼涓€濈殑鐢宠鍙屾暟鎬诲拰锛坰tatus=1/3锛?
            func.coalesce(
                func.sum(
                    case(
                        (
                            ShoeOutboundApply.status.in_([1, 3]),
                            ShoeOutboundApplyDetail.total_pairs,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("pending_outbound_amount"),
            # audit_level: 0/NULL=娌℃湁鍦ㄦ祦绋嬩腑鐨勭敵璇凤紱1=鏈?status=1锛?=鏈?status=3
            func.max(
                case(
                    (ShoeOutboundApply.status == 1, 1),  # 寰呮€荤粡鐞嗗鏍?
                    (ShoeOutboundApply.status == 3, 2),  # 寰呬粨搴撳嚭搴?
                    else_=0,
                )
            ).label("audit_level"),
        )
        .join(
            ShoeOutboundApply,
            ShoeOutboundApply.apply_id == ShoeOutboundApplyDetail.apply_id,
        )
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeOutboundApplyDetail.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .group_by(Order.order_id)
        .subquery()
    )

    # ====== 涓绘煡璇紙鎸夎鍗曡仛鍚堬級 ======
    query = (
        db.session.query(
            Order,
            Customer,
            order_amount_subquery.c.total_amount,
            finished_amount_subquery.c.finished_estimated_amount,
            finished_amount_subquery.c.finished_actual_amount,
            finished_amount_subquery.c.finished_amount,
            outbounded_amount_subquery.c.outbounded_amount,
            apply_agg_subquery.c.pending_outbound_amount,
            apply_agg_subquery.c.audit_level,
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
        .outerjoin(
            apply_agg_subquery,
            apply_agg_subquery.c.order_id == Order.order_id,
        )
        .order_by(Order.order_rid)
    )

    # ====== 杩囨护鏉′欢 ======
    if order_rid:
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if order_cid:
        query = query.filter(Order.order_cid.ilike(f"%{order_cid}%"))
    if customer_name:
        query = query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if customer_brand:
        query = query.filter(Customer.customer_brand.ilike(f"%{customer_brand}%"))

    # 审核状态筛选（基于 audit_level）
    if audit_status_num is not None and audit_status_num > -1:
        if (
            audit_status_num
            == PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM["PRODUCT_OUTBOUND_AUDIT_NOT_INIT"]
        ):
            # 没有在流程中的申请：audit_level 为 0 或 NULL
            query = query.filter(
                or_(
                    apply_agg_subquery.c.audit_level == None,
                    apply_agg_subquery.c.audit_level == 0,
                )
            )
        elif (
            audit_status_num
            == PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM["PRODUCT_OUTBOUND_AUDIT_ONGOING"]
        ):
            # 有 status=1（待总经理审核）
            query = query.filter(apply_agg_subquery.c.audit_level == 1)
        elif (
            audit_status_num
            == PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM["PRODUCT_OUTBOUND_AUDIT_APPROVED"]
        ):
            # 有 status=3（待仓库出库），且没有 status=1
            query = query.filter(apply_agg_subquery.c.audit_level == 2)

    # 仓库状态筛选
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
    elif (
        storage_status_num
        == FINISHED_STORAGE_STATUS_ENUM["PRODUCT_INBOUND_NOT_FINISHED"]
    ):
        query = query.filter(
            finished_amount_subquery.c.finished_actual_amount
            < finished_amount_subquery.c.finished_estimated_amount
        )

    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()

    # ====== 第一层：订单级对象 ======
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
            pending_outbound_amount,
            audit_level,
        ) = row

        pending_outbound_amount = pending_outbound_amount or 0
        audit_level = audit_level or 0

        # 仓库状态
        if outbounded_amount >= estimated_amount:
            storage_status = FINISHED_STORAGE_STATUS_ENUM["PRODUCT_OUTBOUND_FINISHED"]
        elif actual_amount >= estimated_amount:
            storage_status = FINISHED_STORAGE_STATUS_ENUM["PRODUCT_INBOUND_FINISHED"]
        elif actual_amount < estimated_amount:
            storage_status = FINISHED_STORAGE_STATUS_ENUM[
                "PRODUCT_INBOUND_NOT_FINISHED"
            ]
        else:
            storage_status = "未知状态"

        # 订单审核状态（基于 audit_level）
        if audit_level == 1:
            audit_status_val = PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM[
                "PRODUCT_OUTBOUND_AUDIT_ONGOING"
            ]
        elif audit_level == 2:
            audit_status_val = PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM[
                "PRODUCT_OUTBOUND_AUDIT_APPROVED"
            ]
        else:
            audit_status_val = PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM[
                "PRODUCT_OUTBOUND_AUDIT_NOT_INIT"
            ]

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
            "pendingOutboundAmount": int(pending_outbound_amount),
            "orderShoeTable": [],
            "storageStatusNum": storage_status,
            "storageStatusLabel": FINISHED_STORAGE_STATUS[storage_status],
            "auditStatusNum": audit_status_val,
            "auditStatusLabel": PRODUCT_OUTBOUND_AUDIT_STATUS[audit_status_val],
        }
        result.append(obj)

    # ====== 子查询：按配码统计“已出库数量”（通过申请明细反查批次） ======
    outbound_by_batch_subquery = (
        db.session.query(
            ShoeOutboundApplyDetail.order_shoe_batch_info_id.label("batch_id"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            ShoeOutboundApply.status == 4,  # 仓库已完成出库
                            ShoeOutboundApplyDetail.total_pairs,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("outbounded_amount"),
        )
        .join(
            ShoeOutboundApply,
            ShoeOutboundApply.apply_id == ShoeOutboundApplyDetail.apply_id,
        )
        .group_by(ShoeOutboundApplyDetail.order_shoe_batch_info_id)
        .subquery()
    )

    # ====== 第二层：每个订单下的 鞋型 + 颜色 + 配码 + 尺码列 ======
    for order_obj in result:
        order_id = order_obj["orderId"]

        # 1）当前订单的尺码列配置
        shoe_size_meta_list = get_order_batch_type_helper(order_id)
        size_columns = []
        for idx, meta in enumerate(shoe_size_meta_list[: len(SHOESIZERANGE)]):
            db_size = SHOESIZERANGE[idx]  # 34~46
            size_columns.append(
                {
                    "label": meta["label"],
                    "prop": f"size_{db_size}_amount",
                }
            )

        # 2）配码 + 包装信息 + 按配码统计的已出库数量
        batch_info_query = (
            db.session.query(
                OrderShoeBatchInfo,
                PackagingInfo,
                outbound_by_batch_subquery.c.outbounded_amount,
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_type_id
                == OrderShoeBatchInfo.order_shoe_type_id,
            )
            .join(
                OrderShoe,
                OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id,
            )
            .outerjoin(
                PackagingInfo,
                PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id,
            )
            .outerjoin(
                outbound_by_batch_subquery,
                outbound_by_batch_subquery.c.batch_id
                == OrderShoeBatchInfo.order_shoe_batch_info_id,
            )
            .filter(OrderShoe.order_id == order_id)
            .all()
        )

        batch_info_map = defaultdict(list)

        for batch_info, pkg, outbounded_amount in batch_info_query:
            total_amount = batch_info.total_amount or 0
            out_amount = outbounded_amount or 0
            batch_available_amount = max(total_amount - out_amount, 0)

            bi = {
                "batchInfoId": batch_info.order_shoe_batch_info_id,
                "batchName": batch_info.name,
                "packagingInfoId": batch_info.packaging_info_id,
                "packagingInfoName": pkg.packaging_info_name if pkg else None,
                "totalAmount": total_amount,
                "outboundedAmount": out_amount,
                "batchAvailableAmount": batch_available_amount,
                "packagingInfoQuantity": (
                    float(batch_info.packaging_info_quantity)
                    if batch_info.packaging_info_quantity is not None
                    else None
                ),
                "pairsPerCarton": (
                    int(pkg.total_quantity_ratio)
                    if pkg and pkg.total_quantity_ratio is not None
                    else None
                ),
            }
            for size in SHOESIZERANGE:
                col = f"size_{size}_amount"
                bi[col] = getattr(batch_info, col)
            batch_info_map[batch_info.order_shoe_type_id].append(bi)

        # 3）颜色行 + 仓库库存（订单下所有颜色）
        order_shoe_query = (
            db.session.query(
                OrderShoe,
                Shoe,
                func.sum(OrderShoeBatchInfo.total_amount).label(
                    "order_amount_per_color"
                ),
                FinishedShoeStorage,
                func.coalesce(
                    func.sum(ShoeOutboundRecordDetail.outbound_amount),
                    0,
                ).label("outbound_amount"),
                Color,
                OrderShoeType,
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
                OrderShoeType.order_shoe_type_id,
                FinishedShoeStorage.finished_shoe_id,
            )
            .all()
        )

        for (
            order_shoe,
            shoe,
            order_amount_per_color,
            storage_obj,
            outbound_amount,
            color,
            order_s_type,
        ) in order_shoe_query:
            color_obj = {
                "orderShoeId": order_shoe.order_shoe_id,
                "shoeRId": shoe.shoe_rid,
                "customerProductName": order_shoe.customer_product_name,
                "orderAmountPerColor": order_amount_per_color,
                "outboundedAmount": outbound_amount,
                "storageId": storage_obj.finished_shoe_id,
                "currentStock": storage_obj.finished_amount,
                "colorName": color.color_name,
                "orderShoeTypeId": order_s_type.order_shoe_type_id,
                "sizeColumns": size_columns,
                "batchInfos": batch_info_map.get(order_s_type.order_shoe_type_id, []),
            }
            order_obj["orderShoeTable"].append(color_obj)

    return jsonify({"result": result, "total": count_result})


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

    outbound_ids = [row[5] for row in response]
    apply_map = {}
    if outbound_ids:
        apply_rows = (
            db.session.query(
                ShoeOutboundApply.outbound_record_id, ShoeOutboundApply.apply_id
            )
            .filter(ShoeOutboundApply.outbound_record_id.in_(outbound_ids))
            .all()
        )
        for outbound_record_id, apply_id in apply_rows:
            apply_map.setdefault(outbound_record_id, []).append(apply_id)

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
        apply_ids = apply_map.get(outbound_id, [])
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
            "applyIds": apply_ids,
            "applyId": apply_ids[0] if len(apply_ids) == 1 else None,
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
    result = {
        "productOutboundAuditStatusOptions": [],
        "productOutboundAuditStatusEnum": {},
    }
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
    year = request.args.get("year")  # 'YYYY'
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
        return sum(
            getattr(detail_cls, f"size_{i}_amount", 0) or 0 for i in SHOESIZERANGE
        )

    # ========= 合计尺码列表达式 =========
    inbound_total_qty = func.coalesce(
        ShoeInboundRecordDetail.inbound_amount, _sum_size_cols(ShoeInboundRecordDetail)
    )
    outbound_total_qty = func.coalesce(
        ShoeOutboundRecordDetail.outbound_amount,
        _sum_size_cols(ShoeOutboundRecordDetail),
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
            OrderShoeType.unit_price.label("unit_price"),  # 单价
            ShoeInboundRecord.inbound_datetime.label("occur_time"),
            OrderShoeType.currency_type.label("currency"),  # 工单币种
            ShoeInboundRecord.remark.label("remark"),
            literal(None).label("picker"),
            BatchInfoType.batch_info_type_name.label(
                "batch_type_name"
            ),  # 用于判定男女童
        )
        .select_from(ShoeInboundRecord)
        .join(
            ShoeInboundRecordDetail,
            ShoeInboundRecordDetail.shoe_inbound_record_id
            == ShoeInboundRecord.shoe_inbound_record_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == ShoeInboundRecordDetail.finished_shoe_storage_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        # —— 批次链路（外连接，避免无批次被过滤）——
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id,
        )
        .outerjoin(
            BatchInfoType,
            BatchInfoType.batch_info_type_id == PackagingInfo.batch_info_type_id,
        )
        .filter(
            ShoeInboundRecord.inbound_datetime >= start_dt,
            ShoeInboundRecord.inbound_datetime < end_dt,
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
            OrderShoeType.unit_price.label("unit_price"),  # 单价
            ShoeOutboundRecord.outbound_datetime.label("occur_time"),
            OrderShoeType.currency_type.label("currency"),  # 工单币种
            ShoeOutboundRecord.remark.label("remark"),
            ShoeOutboundRecord.picker.label("picker"),
            BatchInfoType.batch_info_type_name.label(
                "batch_type_name"
            ),  # 用于判定男女童
        )
        .select_from(ShoeOutboundRecord)
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.shoe_outbound_record_id
            == ShoeOutboundRecord.shoe_outbound_record_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == ShoeOutboundRecordDetail.finished_shoe_storage_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        # —— 批次链路（外连接）——
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id,
        )
        .outerjoin(
            BatchInfoType,
            BatchInfoType.batch_info_type_id == PackagingInfo.batch_info_type_id,
        )
        .filter(
            ShoeOutboundRecord.outbound_datetime >= start_dt,
            ShoeOutboundRecord.outbound_datetime < end_dt,
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
        db.session.query(func.count(literal(1))).select_from(u).filter(*wheres).scalar()
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
        result_list.append(
            {
                "direction": r.direction,
                "recordId": r.record_id,
                "detailId": r.detail_id,
                "rid": r.rid,
                "designer": r.designer or "",  # 设计师
                "adjuster": r.adjuster or "",  # 调版师
                "shoeRid": r.shoeRid or "",
                "color": r.color or "",
                "category": normalize_category_by_batch_type(
                    getattr(r, "batch_type_name", "")
                ),  # ← 男女童
                "quantity": qty,
                "amount": round(detail_amount, 3),  # 单条金额
                "unitPrice": unit_price,
                "occurTime": r.occur_time.isoformat(sep=" "),
                "currency": currency_norm,
                "remark": r.remark or "",
                "picker": r.picker or "",
            }
        )

    # ---- 金额统计（Python端按币种分别累计）----
    amt_rows = (
        db.session.query(
            u.c.direction, u.c.detail_quantity, u.c.unit_price, u.c.currency
        )
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
            in_amount_by_ccy[ccy] = round(
                in_amount_by_ccy.get(ccy, Decimal(0.0)) + amt, 3
            )
        elif ar.direction == "OUT":
            out_amount_by_ccy[ccy] = round(
                out_amount_by_ccy.get(ccy, Decimal(0.0)) + amt, 3
            )

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "list": result_list,
            "total": int(total),
            "stat": {
                "inQty": in_qty_total,
                "outQty": out_qty_total,
                "inAmountByCurrency": in_amount_by_ccy,  # CNY/RMB、USD/USA 已统一
                "outAmountByCurrency": out_amount_by_ccy,
            },
        }
    )


def _collect_shoe_inout_summary(filters: Dict[str, Any]):
    filters = filters or {}
    mode = (filters.get("mode") or "month").lower()
    month = filters.get("month")
    year = filters.get("year")
    direction = (filters.get("direction") or "").upper()
    keyword = (filters.get("keyword") or "").strip()
    shoe_rid_kw = (filters.get("shoeRid") or "").strip()
    color_kw = (filters.get("color") or "").strip()
    group_by = (filters.get("groupBy") or "model").lower()
    category_kw = (filters.get("category") or "").strip()

    try:
        if mode == "month":
            if not month:
                raise ValueError("month 必填（YYYY-MM）")
            start_dt = datetime.strptime(month + "-01", "%Y-%m-%d")
            end_dt = start_dt + relativedelta(months=1)
        elif mode == "year":
            if not year:
                raise ValueError("year 必填（YYYY）")
            start_dt = datetime(int(year), 1, 1)
            end_dt = datetime(int(year) + 1, 1, 1)
        else:
            raise ValueError("mode 只支持 month / year")
    except ValueError as exc:
        message = str(exc)
        predefined = {"month 必填（YYYY-MM）", "year 必填（YYYY）", "mode 只支持 month / year"}
        if message in predefined:
            raise
        raise ValueError("时间参数格式错误") from exc

    def _sum_size_cols(detail_cls):
        return sum(
            getattr(detail_cls, f"size_{i}_amount", 0) or 0 for i in SHOESIZERANGE
        )

    inbound_total_qty = func.coalesce(
        ShoeInboundRecordDetail.inbound_amount, _sum_size_cols(ShoeInboundRecordDetail)
    )

    outbound_total_qty = func.coalesce(
        ShoeOutboundRecordDetail.outbound_amount,
        _sum_size_cols(ShoeOutboundRecordDetail),
    )

    def _build_inbound_query(range_start: datetime | None, range_end: datetime | None):
        query = (
            db.session.query(
                literal("IN").label("direction"),
                Shoe.shoe_rid.label("shoeRid"),
                Color.color_name.label("color"),
                Shoe.shoe_designer.label("designer"),
                OrderShoe.adjust_staff.label("adjuster"),
                inbound_total_qty.cast(Integer).label("qty"),
                OrderShoeType.unit_price.label("unit_price"),
                OrderShoeType.currency_type.label("currency"),
                ShoeInboundRecord.shoe_inbound_rid.label("rid"),
                ShoeInboundRecord.inbound_datetime.label("occur_time"),
                BatchInfoType.batch_info_type_name.label("batch_type_name"),
            )
            .select_from(ShoeInboundRecord)
            .join(
                ShoeInboundRecordDetail,
                ShoeInboundRecordDetail.shoe_inbound_record_id
                == ShoeInboundRecord.shoe_inbound_record_id,
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_type_id
                == ShoeInboundRecordDetail.finished_shoe_storage_id,
            )
            .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
            .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
            .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
            .join(Color, Color.color_id == ShoeType.color_id)
            .outerjoin(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .outerjoin(
                PackagingInfo,
                PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id,
            )
            .outerjoin(
                BatchInfoType,
                BatchInfoType.batch_info_type_id == PackagingInfo.batch_info_type_id,
            )
        )
        if range_start:
            query = query.filter(ShoeInboundRecord.inbound_datetime >= range_start)
        if range_end:
            query = query.filter(ShoeInboundRecord.inbound_datetime < range_end)
        return query

    def _build_outbound_query(range_start: datetime | None, range_end: datetime | None):
        query = (
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
                BatchInfoType.batch_info_type_name.label("batch_type_name"),
            )
            .select_from(ShoeOutboundRecord)
            .join(
                ShoeOutboundRecordDetail,
                ShoeOutboundRecordDetail.shoe_outbound_record_id
                == ShoeOutboundRecord.shoe_outbound_record_id,
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_type_id
                == ShoeOutboundRecordDetail.finished_shoe_storage_id,
            )
            .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
            .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
            .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
            .join(Color, Color.color_id == ShoeType.color_id)
            .outerjoin(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .outerjoin(
                PackagingInfo,
                PackagingInfo.packaging_info_id == OrderShoeBatchInfo.packaging_info_id,
            )
            .outerjoin(
                BatchInfoType,
                BatchInfoType.batch_info_type_id == PackagingInfo.batch_info_type_id,
            )
        )
        if range_start:
            query = query.filter(ShoeOutboundRecord.outbound_datetime >= range_start)
        if range_end:
            query = query.filter(ShoeOutboundRecord.outbound_datetime < range_end)
        return query

    def _build_flow_union(range_start: datetime | None, range_end: datetime | None):
        return _build_inbound_query(range_start, range_end).union_all(
            _build_outbound_query(range_start, range_end)
        )

    period_q = _build_flow_union(start_dt, end_dt)
    opening_q = _build_flow_union(None, start_dt)
    closing_q = _build_flow_union(None, end_dt)

    def _build_common_filters(alias):
        conds = []
        if keyword:
            conds.append(alias.c.rid.ilike(f"%{keyword}%"))
        if shoe_rid_kw:
            conds.append(alias.c.shoeRid.ilike(f"%{shoe_rid_kw}%"))
        if color_kw:
            conds.append(alias.c.color.ilike(f"%{color_kw}%"))
        if category_kw == "男鞋":
            conds.append(alias.c.batch_type_name.like("%男%"))
        elif category_kw == "女鞋":
            conds.append(alias.c.batch_type_name.like("%女%"))
        elif category_kw == "童鞋":
            conds.append(alias.c.batch_type_name.like("%童%"))
        elif category_kw == "其它":
            conds.append(
                or_(
                    alias.c.batch_type_name.is_(None),
                    and_(
                        not_(alias.c.batch_type_name.like("%男%")),
                        not_(alias.c.batch_type_name.like("%女%")),
                        not_(alias.c.batch_type_name.like("%童%")),
                    ),
                )
            )
        return conds

    period_u = period_q.subquery("period_u")
    opening_u = opening_q.subquery("opening_u")
    closing_u = closing_q.subquery("closing_u")

    period_filters = _build_common_filters(period_u)
    opening_filters = _build_common_filters(opening_u)
    closing_filters = _build_common_filters(closing_u)

    period_records = db.session.query(period_u).filter(*period_filters).all()
    opening_records = db.session.query(opening_u).filter(*opening_filters).all()
    closing_records = db.session.query(closing_u).filter(*closing_filters).all()

    def group_key(row):
        if group_by == "model_color":
            return (row.shoeRid or "-", row.color or "-")
        return (row.shoeRid or "-", None)

    def ensure_entry(row_key, source_row):
        if row_key not in agg:
            agg[row_key] = {
                "shoeRid": row_key[0],
                "color": row_key[1],
                "designer": source_row.designer or "",
                "adjuster": source_row.adjuster or "",
                "category": normalize_category_by_batch_type(
                    getattr(source_row, "batch_type_name", "")
                ),
                "unitPrice": Decimal(source_row.unit_price or 0.0),
                "inQty": 0,
                "outQty": 0,
                "inAmountByCurrency": defaultdict(Decimal),
                "outAmountByCurrency": defaultdict(Decimal),
            }
        return agg[row_key]

    agg: Dict[tuple, Dict[str, Any]] = {}

    for record in period_records:
        key = group_key(record)
        item = ensure_entry(key, record)

        qty = int(record.qty or 0)
        unit_price = Decimal(record.unit_price or 0.0)
        cur = normalize_currency(record.currency)
        amount = unit_price * qty

        if record.direction == "IN":
            item["inQty"] += qty
            if cur:
                item["inAmountByCurrency"][cur] += amount
        else:
            item["outQty"] += qty
            if cur:
                item["outAmountByCurrency"][cur] += amount

    def _build_balance_lookup(record_rows):
        lookup: Dict[tuple, Dict[str, Any]] = {}
        for record in record_rows:
            key = group_key(record)
            entry = lookup.setdefault(
                key, {"qty": 0, "amounts": defaultdict(Decimal)}
            )
            qty = int(record.qty or 0)
            cur = normalize_currency(record.currency)
            amount = Decimal(record.unit_price or 0.0) * qty
            if record.direction == "IN":
                entry["qty"] += qty
                if cur:
                    entry["amounts"][cur] += amount
            else:
                entry["qty"] -= qty
                if cur:
                    entry["amounts"][cur] -= amount
        return lookup

    opening_lookup = _build_balance_lookup(opening_records)
    closing_lookup = _build_balance_lookup(closing_records)

    rows: List[Dict[str, Any]] = []
    for key, item in agg.items():
        in_amount_raw = item["inAmountByCurrency"]
        out_amount_raw = item["outAmountByCurrency"]
        in_map = {c: round(v, 3) for c, v in in_amount_raw.items() if v}
        out_map = {c: round(v, 3) for c, v in out_amount_raw.items() if v}

        amount_keys = set(in_amount_raw.keys()) | set(out_amount_raw.keys())
        net_amount_raw = {
            c: in_amount_raw.get(c, Decimal(0)) - out_amount_raw.get(c, Decimal(0))
            for c in amount_keys
        }
        net_map = {c: round(v, 3) for c, v in net_amount_raw.items() if v}
        net_qty = item["inQty"] - item["outQty"]

        closing_entry = closing_lookup.get(key)
        if closing_entry:
            closing_qty = closing_entry["qty"]
            closing_amount_raw = defaultdict(Decimal)
            for cur, val in closing_entry["amounts"].items():
                closing_amount_raw[cur] = val
        else:
            closing_qty = net_qty
            closing_amount_raw = defaultdict(Decimal, net_amount_raw)

        opening_entry = opening_lookup.get(key)
        if opening_entry:
            opening_qty = opening_entry["qty"]
            opening_amount_raw = defaultdict(Decimal)
            for cur, val in opening_entry["amounts"].items():
                opening_amount_raw[cur] = val
        else:
            opening_qty = closing_qty - net_qty
            opening_amount_raw = defaultdict(Decimal)
            combined = set(closing_amount_raw.keys()) | set(net_amount_raw.keys())
            for cur in combined:
                opening_amount_raw[cur] = (
                    closing_amount_raw.get(cur, Decimal(0))
                    - net_amount_raw.get(cur, Decimal(0))
                )

        opening_map = {c: round(v, 3) for c, v in opening_amount_raw.items() if v}
        closing_map = {c: round(v, 3) for c, v in closing_amount_raw.items() if v}

        rows.append(
            {
                "shoeRid": item["shoeRid"],
                "color": item["color"] or "",
                "designer": item["designer"],
                "adjuster": item["adjuster"],
                "category": item["category"],
                "unitPrice": item["unitPrice"],
                "openingQty": opening_qty,
                "inQty": item["inQty"],
                "outQty": item["outQty"],
                "netQty": net_qty,
                "closingQty": closing_qty,
                "inAmountByCurrency": in_map,
                "outAmountByCurrency": out_map,
                "netAmountByCurrency": net_map,
                "openingAmountByCurrency": opening_map,
                "closingAmountByCurrency": closing_map,
            }
        )

    rows.sort(key=lambda x: (-x["netQty"], x["shoeRid"], x.get("color", "")))

    if direction == "IN":
        rows = [row for row in rows if row["inQty"] > 0]
    elif direction == "OUT":
        rows = [row for row in rows if row["outQty"] > 0]

    def _sum_amounts(rows_data: List[Dict[str, Any]], field: str):
        total = defaultdict(Decimal)
        for item in rows_data:
            for cur, val in item.get(field, {}).items():
                total[cur] += Decimal(str(val))
        return {c: round(v, 3) for c, v in total.items() if v}

    stat = {
        "inQty": int(sum(row["inQty"] for row in rows)),
        "outQty": int(sum(row["outQty"] for row in rows)),
        "netQty": int(sum(row["netQty"] for row in rows)),
        "openingQty": int(sum(row.get("openingQty", 0) for row in rows)),
        "closingQty": int(sum(row.get("closingQty", 0) for row in rows)),
        "inAmountByCurrency": _sum_amounts(rows, "inAmountByCurrency"),
        "outAmountByCurrency": _sum_amounts(rows, "outAmountByCurrency"),
        "netAmountByCurrency": _sum_amounts(rows, "netAmountByCurrency"),
        "openingAmountByCurrency": _sum_amounts(rows, "openingAmountByCurrency"),
        "closingAmountByCurrency": _sum_amounts(rows, "closingAmountByCurrency"),
    }

    return {"rows": rows, "stat": stat}


@finished_storage_bp.route(
    "/warehouse/getshoeinoutboundsummarybymodel", methods=["GET"]
)
def get_shoe_inoutbound_summary_by_model():
    """出入库汇总（按型号 / 型号+颜色）"""

    page = max(request.args.get("page", 1, type=int) or 1, 1)
    page_size = request.args.get("pageSize", 20, type=int) or 20
    page_size = max(1, min(page_size, 200))

    filters = {
        "mode": request.args.get("mode") or "month",
        "month": request.args.get("month"),
        "year": request.args.get("year"),
        "direction": request.args.get("direction"),
        "keyword": request.args.get("keyword"),
        "shoeRid": request.args.get("shoeRid"),
        "color": request.args.get("color"),
        "groupBy": request.args.get("groupBy") or "model",
        "category": request.args.get("category"),
    }

    try:
        summary = _collect_shoe_inout_summary(filters)
    except ValueError as exc:
        return jsonify({"code": 400, "message": str(exc)}), 400

    rows = summary["rows"]
    stat = summary["stat"]
    total_groups = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "list": page_rows,
            "total": total_groups,
            "stat": stat,
        }
    )


@finished_storage_bp.route(
    "/warehouse/export/shoeinoutsummarybymodel", methods=["GET"]
)
def export_shoe_inout_summary_by_model():
    filters = {
        "mode": request.args.get("mode") or "month",
        "month": request.args.get("month"),
        "year": request.args.get("year"),
        "direction": request.args.get("direction"),
        "keyword": request.args.get("keyword"),
        "shoeRid": request.args.get("shoeRid"),
        "color": request.args.get("color"),
        "groupBy": request.args.get("groupBy") or "model",
        "category": request.args.get("category"),
    }

    try:
        summary = _collect_shoe_inout_summary(filters)
    except ValueError as exc:
        return jsonify({"code": 400, "message": str(exc)}), 400

    bio, filename = build_finished_inout_summary_by_model_excel(
        summary["rows"], summary["stat"], filters
    )
    return send_file(
        bio,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


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
    return send_file(
        bio,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


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
    return send_file(
        bio,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


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
    return send_file(
        bio,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@finished_storage_bp.route(
    "/warehouse/downloadfinishedoutboundrecordbybatchid", methods=["POST"]
)
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
    template_path = os.path.join(FILE_STORAGE_PATH, "出货清单模板.xlsx")
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


@finished_storage_bp.route(
    "/warehouse/downloadfinishedoutboundapply", methods=["POST"]
)
def download_finished_outbound_apply():
    data = request.get_json(silent=True) or {}
    apply_ids = data.get("applyIds")

    if not apply_ids:
        return jsonify({"error": "缺少参数：applyIds"}), 400

    template_path = os.path.join(FILE_STORAGE_PATH, "出货清单模板.xlsx")

    try:
        excel_io, filename = generate_finished_outbound_apply_excel(
            template_path=template_path,
            apply_ids=apply_ids,
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception:
        current_app.logger.exception("导出出库申请失败")
        return jsonify({"error": "导出出库申请失败"}), 500

    return send_file(
        excel_io,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ============================================================
# 出库申请（ShoeOutboundApply）相关接口
# ============================================================

# 状态含义：
# 0 草稿（业务编辑中）
# 1 已提交，待总经理审核
# 2 总经理驳回
# 3 总经理通过，待仓库出库
# 4 仓库已完成出库
# 5 已作废/取消
_OUTBOUND_APPLY_STATUS_LABEL = {
    0: "草稿",
    1: "待总经理审核",
    2: "总经理驳回",
    3: "待仓库出库",
    4: "已完成出库",
    5: "已作废/取消",
}


def _get_current_staff_id() -> Optional[int]:
    try:
        _, staff, _ = current_user_info()
        return getattr(staff, "staff_id", None)
    except Exception:
        return None


@finished_storage_bp.route("/warehouse/outbound-apply/save", methods=["POST"])
def save_outbound_apply():
    """
    业务保存/提交出库申请单（支持一个申请单包含多个订单的明细）
    """
    data = request.get_json(silent=True) or {}
    apply_id = data.get("applyId")
    order_id = data.get("orderId")
    target_status = data.get("status", 0)
    remark = data.get("remark") or ""
    details = data.get("details") or []

    # 新增：预计出库时间，前端传字符串 "YYYY-MM-DD HH:mm:ss"
    expected_outbound_time_str = data.get("expectedOutboundTime") or None
    expected_outbound_dt = None
    if expected_outbound_time_str:
        try:
            expected_outbound_dt = datetime.strptime(
                expected_outbound_time_str, "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            return jsonify({"message": "预计出库时间格式应为 YYYY-MM-DD HH:mm:ss"}), 400

    if not order_id:
        return jsonify({"message": "缺少 orderId"}), 400
    if not isinstance(details, list) or not details:
        return jsonify({"message": "明细不能为空"}), 400
    if target_status not in (0, 1):
        return jsonify({"message": "status 只能为 0(草稿) 或 1(提交)"}), 400

    staff_id = _get_current_staff_id()
    if not staff_id:
        return jsonify({"message": "无法获取当前登录员工信息"}), 401

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"message": "订单不存在"}), 404

    # ====== 新建 / 编辑表头 ======
    if apply_id:
        apply_obj: ShoeOutboundApply = ShoeOutboundApply.query.get(apply_id)
        if not apply_obj:
            return jsonify({"message": "申请单不存在"}), 404
        if apply_obj.status not in (0, 2):
            return jsonify({"message": "当前状态下不允许修改申请单"}), 409

        apply_obj.order_id = order_id
        apply_obj.remark = remark
        apply_obj.business_staff_id = apply_obj.business_staff_id or staff_id
        apply_obj.status = target_status
        apply_obj.expected_outbound_datetime = expected_outbound_dt
        ShoeOutboundApplyDetail.query.filter_by(apply_id=apply_obj.apply_id).delete()
    else:
        timestamp = format_datetime(datetime.now())
        rid_suffix = timestamp.replace("-", "").replace(" ", "").replace(":", "")
        apply_rid = "SOA" + rid_suffix + "T0"

        apply_obj = ShoeOutboundApply(
            apply_rid=apply_rid,
            order_id=order_id,
            business_staff_id=staff_id,
            status=target_status,
            remark=remark,
            expected_outbound_datetime=expected_outbound_dt,
        )
        db.session.add(apply_obj)
        db.session.flush()

    # 写入明细（箱数可以为小数，但 total_pairs 必须是整数）
    for row in details:
        try:
            storage_id = int(row["finishedShoeStorageId"])
            order_shoe_type_id = int(row["orderShoeTypeId"])
        except Exception:
            return (
                jsonify(
                    {"message": "明细中 finishedShoeStorageId / orderShoeTypeId 不合法"}
                ),
                400,
            )

        # cartonCount 允许小数，用 Decimal 处理
        try:
            carton_count = Decimal(str(row.get("cartonCount") or "0"))
            pairs_per_carton = Decimal(str(row.get("pairsPerCarton") or "0"))
        except Exception:
            return jsonify({"message": "明细中 cartonCount / pairsPerCarton 非法"}), 400

        # totalPairs 可以前端直接传，也可以后端计算；无论如何，最后统一成整数
        total_pairs_raw = row.get("totalPairs")
        if total_pairs_raw is not None:
            try:
                total_pairs_dec = Decimal(str(total_pairs_raw))
            except Exception:
                return jsonify({"message": "明细中 totalPairs 非法"}), 400
        else:
            total_pairs_dec = carton_count * pairs_per_carton

        # 四舍五入到整数，保证双数是整数
        total_pairs_dec = total_pairs_dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total_pairs = int(total_pairs_dec)

        if total_pairs <= 0:
            return (
                jsonify(
                    {
                        "message": "每条明细 totalPairs 或 (cartonCount * pairsPerCarton) 四舍五入后必须 > 0"
                    }
                ),
                400,
            )

        detail_obj = ShoeOutboundApplyDetail(
            apply_id=apply_obj.apply_id,
            finished_shoe_storage_id=storage_id,
            order_shoe_type_id=order_shoe_type_id,
            order_shoe_batch_info_id=row.get("orderShoeBatchInfoId"),
            packaging_info_id=row.get("packagingInfoId"),
            carton_count=carton_count,  # 保存小数箱数
            pairs_per_carton=int(pairs_per_carton),  # 每箱双数依然是整数
            total_pairs=total_pairs,  # 确保是整数
            remark=row.get("remark"),
        )
        db.session.add(detail_obj)

    db.session.commit()
    return jsonify(
        {
            "message": "success",
            "applyId": apply_obj.apply_id,
            "applyRId": apply_obj.apply_rid,
            "status": apply_obj.status,
            "statusLabel": _OUTBOUND_APPLY_STATUS_LABEL.get(
                apply_obj.status, "未知状态"
            ),
        }
    )


@finished_storage_bp.route("/warehouse/outbound-apply/list", methods=["GET"])
def list_outbound_applies():
    """
    出库申请单列表（支持简单筛选）
    Query 参数：
      - page, pageSize
      - orderRId   # 这里会匹配“主订单号”和“作为明细所属订单”的申请单
      - applyRId
      - customerName
      - status: 0/1/2/3/4/5
    """
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 20, type=int)
    order_rid_kw = (request.args.get("orderRId") or "").strip()
    apply_rid_kw = (request.args.get("applyRId") or "").strip()
    customer_name_kw = (request.args.get("customerName") or "").strip()
    status = request.args.get("status", type=int)

    q = (
        db.session.query(
            ShoeOutboundApply,
            Order,
            Customer,
            func.coalesce(func.sum(ShoeOutboundApplyDetail.total_pairs), 0).label(
                "total_pairs"
            ),
        )
        .join(Order, Order.order_id == ShoeOutboundApply.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .outerjoin(
            ShoeOutboundApplyDetail,
            ShoeOutboundApplyDetail.apply_id == ShoeOutboundApply.apply_id,
        )
        .group_by(ShoeOutboundApply.apply_id, Order.order_id, Customer.customer_id)
        .order_by(desc(ShoeOutboundApply.create_time))
    )

    if order_rid_kw:
        # 找出所有“包含该订单”的申请单ID（通过明细 -> 库存 -> 型号 -> 订单链路）
        apply_ids_subq = (
            db.session.query(ShoeOutboundApplyDetail.apply_id)
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.finished_shoe_id
                == ShoeOutboundApplyDetail.finished_shoe_storage_id,
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_type_id
                == FinishedShoeStorage.order_shoe_type_id,
            )
            .join(
                OrderShoe,
                OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id,
            )
            .join(Order, Order.order_id == OrderShoe.order_id)
            .filter(Order.order_rid.ilike(f"%{order_rid_kw}%"))
            .distinct()
            .subquery()
        )

        q = q.filter(
            or_(
                Order.order_rid.ilike(f"%{order_rid_kw}%"),
                ShoeOutboundApply.apply_id.in_(apply_ids_subq),
            )
        )

    if apply_rid_kw:
        q = q.filter(ShoeOutboundApply.apply_rid.ilike(f"%{apply_rid_kw}%"))
    if customer_name_kw:
        q = q.filter(Customer.customer_name.ilike(f"%{customer_name_kw}%"))
    if status is not None and status >= 0:
        q = q.filter(ShoeOutboundApply.status == status)

    total = q.count()
    rows = q.limit(page_size).offset((page - 1) * page_size).all()

    result = []
    for apply_obj, order, customer, total_pairs in rows:
        result.append(
            {
                "applyId": apply_obj.apply_id,
                "applyRId": apply_obj.apply_rid,
                "orderId": order.order_id,
                "orderRId": order.order_rid,
                "orderCId": order.order_cid,
                "customerName": customer.customer_name,
                "customerBrand": customer.customer_brand,
                "totalPairs": int(total_pairs or 0),
                "status": apply_obj.status,
                "statusLabel": _OUTBOUND_APPLY_STATUS_LABEL.get(
                    apply_obj.status, "未知状态"
                ),
                "remark": apply_obj.remark,
                "expectedOutboundTime": (
                    format_datetime(apply_obj.expected_outbound_datetime)
                    if apply_obj.expected_outbound_datetime
                    else None
                ),
                "actualOutboundTime": (
                    format_datetime(apply_obj.actual_outbound_datetime)
                    if apply_obj.actual_outbound_datetime
                    else None
                ),
                "createTime": format_datetime(apply_obj.create_time),
                "updateTime": format_datetime(apply_obj.update_time),
            }
        )

    return jsonify({"result": result, "total": total})


@finished_storage_bp.route("/warehouse/outbound-apply/detail", methods=["GET"])
def get_outbound_apply_detail():
    """
    查询单个出库申请单详情（含明细）
    Query:
      - applyId
    """
    apply_id = request.args.get("applyId", type=int)
    if not apply_id:
        return jsonify({"message": "缺少 applyId"}), 400

    apply_obj: ShoeOutboundApply = ShoeOutboundApply.query.get(apply_id)
    if not apply_obj:
        return jsonify({"message": "申请单不存在"}), 404

    order = Order.query.get(apply_obj.order_id)
    customer = Customer.query.get(order.customer_id) if order else None

    detail_rows = (
        db.session.query(
            ShoeOutboundApplyDetail,
            FinishedShoeStorage,
            OrderShoeType,
            OrderShoe,
            ShoeType,
            Shoe,
            Color,
            OrderShoeBatchInfo,
            PackagingInfo,
        )
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeOutboundApplyDetail.finished_shoe_storage_id,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .outerjoin(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_batch_info_id
            == ShoeOutboundApplyDetail.order_shoe_batch_info_id,
        )
        .outerjoin(
            PackagingInfo,
            PackagingInfo.packaging_info_id
            == ShoeOutboundApplyDetail.packaging_info_id,
        )
        .filter(ShoeOutboundApplyDetail.apply_id == apply_id)
        .all()
    )

    detail_list = []
    for (
        d,
        storage,
        ost,
        order_shoe,
        shoe_type,
        shoe,
        color,
        batch_info,
        pkg,
    ) in detail_rows:
        detail_list.append(
            {
                "applyDetailId": d.apply_detail_id,
                "finishedShoeStorageId": d.finished_shoe_storage_id,
                "orderShoeTypeId": d.order_shoe_type_id,
                "orderShoeBatchInfoId": d.order_shoe_batch_info_id,
                "packagingInfoId": d.packaging_info_id,
                "cartonCount": d.carton_count,
                "pairsPerCarton": d.pairs_per_carton,
                "totalPairs": d.total_pairs,
                "remark": d.remark,
                "shoeRId": shoe.shoe_rid if shoe else None,
                "colorName": color.color_name if color else None,
                "customerProductName": (
                    order_shoe.customer_product_name if order_shoe else None
                ),
                "currentStock": storage.finished_amount if storage else None,
                "finishedStatus": storage.finished_status if storage else None,
                "inboundFinished": 1 if (storage and storage.finished_status == 1) else 0,
                "batchName": batch_info.name if batch_info else None,
                "packagingInfoName": pkg.packaging_info_name if pkg else None,
            }
        )

    header = {
        "applyId": apply_obj.apply_id,
        "applyRId": apply_obj.apply_rid,
        "orderId": order.order_id if order else None,
        "orderRId": order.order_rid if order else None,
        "orderCId": order.order_cid if order else None,
        "customerName": customer.customer_name if customer else None,
        "customerBrand": customer.customer_brand if customer else None,
        "status": apply_obj.status,
        "statusLabel": _OUTBOUND_APPLY_STATUS_LABEL.get(apply_obj.status, "未知状态"),
        "remark": apply_obj.remark,
        "businessStaffId": apply_obj.business_staff_id,
        "gmStaffId": apply_obj.gm_staff_id,
        "warehouseStaffId": apply_obj.warehouse_staff_id,
        "outboundRecordId": apply_obj.outbound_record_id,
        "expectedOutboundTime": (
            format_datetime(apply_obj.expected_outbound_datetime)
            if apply_obj.expected_outbound_datetime
            else None
        ),
        "actualOutboundTime": (
            format_datetime(apply_obj.actual_outbound_datetime)
            if apply_obj.actual_outbound_datetime
            else None
        ),
        "createTime": format_datetime(apply_obj.create_time),
        "updateTime": format_datetime(apply_obj.update_time),
    }

    return jsonify({"header": header, "details": detail_list})


@finished_storage_bp.route("/warehouse/outbound-apply/audit", methods=["POST"])
def audit_outbound_apply():
    """
    总经理审核出库申请
    Request JSON:
    {
        "applyId": 123,
        "action": "approve" | "reject",
        "remark": "审核意见（可选）"
    }
    """
    data = request.get_json(silent=True) or {}
    apply_id = data.get("applyId")
    action = (data.get("action") or "").lower()
    remark = data.get("remark") or ""

    if not apply_id:
        return jsonify({"message": "缺少 applyId"}), 400
    if action not in ("approve", "reject"):
        return jsonify({"message": "action 只能为 approve / reject"}), 400

    staff_id = _get_current_staff_id()
    if not staff_id:
        return jsonify({"message": "无法获取当前登录员工信息"}), 401

    apply_obj: ShoeOutboundApply = ShoeOutboundApply.query.get(apply_id)
    if not apply_obj:
        return jsonify({"message": "申请单不存在"}), 404

    if apply_obj.status != 1:
        return jsonify({"message": "只有“待总经理审核”的申请单才能审核"}), 409

    apply_obj.gm_staff_id = staff_id
    if remark:
        apply_obj.remark = (apply_obj.remark or "") + f"\n[总经理审核]: {remark}"

    if action == "approve":
        apply_obj.status = 3  # 待仓库出库
    else:
        apply_obj.status = 2  # 总经理驳回

    db.session.commit()
    return jsonify(
        {
            "message": "success",
            "applyId": apply_obj.apply_id,
            "status": apply_obj.status,
            "statusLabel": _OUTBOUND_APPLY_STATUS_LABEL.get(
                apply_obj.status, "未知状态"
            ),
        }
    )


@finished_storage_bp.route("/warehouse/outbound-apply/execute", methods=["POST"])
def execute_outbound_apply():
    """
    仓库按申请单执行出库：
      - 校验库存
      - 生成 ShoeOutboundRecord + ShoeOutboundRecordDetail
      - 扣减 FinishedShoeStorage.finished_amount
      - 更新申请状态为 已完成出库(4)，写入 outbound_record_id
      - 若订单所有成品库存出完，则推进事件（仿照 outbound_finished）

    Request JSON:
    {
        "applyId": 123,
        "picker": "张三",
        "remark": "仓库出货备注（可选）"
    }
    """
    data = request.get_json(silent=True) or {}
    apply_id = data.get("applyId")
    picker = data.get("picker") or ""
    extra_remark = data.get("remark") or ""
    detail_payloads = data.get("details")

    if not apply_id:
        return jsonify({"message": "缺少 applyId"}), 400
    if not isinstance(detail_payloads, list) or not detail_payloads:
        return jsonify({"message": "缺少出库明细的实际出库数量"}), 400

    detail_input_map: dict[int, dict] = {}
    for item in detail_payloads:
        if not isinstance(item, dict):
            return jsonify({"message": "明细格式不正确"}), 400
        detail_id = item.get("applyDetailId")
        actual_pairs_raw = item.get("actualPairs")
        actual_carton_raw = item.get("actualCartonCount")
        if not detail_id:
            return jsonify({"message": "明细缺少 applyDetailId"}), 400
        if detail_id in detail_input_map:
            return jsonify({"message": f"明细 {detail_id} 重复填写实际出库数量"}), 400

        # 允许两种填法：实际双数 或 实际箱数（优先箱数）
        actual_pairs_val = None
        actual_carton_val = None
        if actual_carton_raw is not None:
            try:
                actual_carton_val = Decimal(str(actual_carton_raw))
            except Exception:
                return (
                    jsonify({"message": f"明细 {detail_id} 的实际出库箱数格式不正确"}),
                    400,
                )
            if actual_carton_val < 0:
                return (
                    jsonify({"message": f"明细 {detail_id} 的实际出库箱数不能为负数"}),
                    400,
                )
        if actual_pairs_raw is not None:
            try:
                actual_pairs_val = int(Decimal(str(actual_pairs_raw)))
            except Exception:
                return (
                    jsonify({"message": f"明细 {detail_id} 的实际出库数量格式不正确"}),
                    400,
                )
            if actual_pairs_val < 0:
                return (
                    jsonify({"message": f"明细 {detail_id} 的实际出库数量不能为负数"}),
                    400,
                )

        if actual_carton_val is None and actual_pairs_val is None:
            return jsonify({"message": f"明细 {detail_id} 缺少实际出库数量/箱数"}), 400

        detail_input_map[detail_id] = {
            "actual_pairs": actual_pairs_val,
            "actual_carton": actual_carton_val,
        }

    staff_id = _get_current_staff_id()
    if not staff_id:
        return jsonify({"message": "无法获取当前登录员工信息"}), 401

    apply_obj: ShoeOutboundApply = ShoeOutboundApply.query.get(apply_id)
    if not apply_obj:
        return jsonify({"message": "申请单不存在"}), 404

    if apply_obj.status != 3:
        return jsonify({"message": "只有“待仓库出库”的申请单才能执行"}), 409
    if apply_obj.outbound_record_id:
        return jsonify({"message": "该申请单已关联出库记录，不能重复执行"}), 409

    details: list[ShoeOutboundApplyDetail] = ShoeOutboundApplyDetail.query.filter_by(
        apply_id=apply_id
    ).all()
    if not details:
        return jsonify({"message": "申请单没有明细，无法执行"}), 400
    missing_qty_ids = [
        d.apply_detail_id for d in details if d.apply_detail_id not in detail_input_map
    ]
    if missing_qty_ids:
        return (
            jsonify(
                {
                    "message": f"缺少明细 {missing_qty_ids[:3]} 的实际出库数量，请补充后再试"
                }
            ),
            400,
        )

    storage_ids = [d.finished_shoe_storage_id for d in details]
    storages = (
        db.session.query(FinishedShoeStorage)
        .filter(FinishedShoeStorage.finished_shoe_id.in_(storage_ids))
        .all()
    )
    storage_map = {s.finished_shoe_id: s for s in storages}
    if len(storage_map) != len(set(storage_ids)):
        return jsonify({"message": "部分明细对应的成品库存记录不存在"}), 400

    # 先做库存检查
    for d in details:
        s = storage_map[d.finished_shoe_storage_id]
        input_obj = detail_input_map.get(d.apply_detail_id, {})
        actual_qty = input_obj.get("actual_pairs")
        actual_carton = input_obj.get("actual_carton")
        if actual_carton is not None:
            if not d.pairs_per_carton:
                return (
                    jsonify(
                        {
                            "message": f"明细 {d.apply_detail_id} 缺少每箱双数，无法用箱数计算实际出库"
                        }
                    ),
                    400,
                )
            actual_qty = int(
                (actual_carton or Decimal("0")) * Decimal(str(d.pairs_per_carton or 0))
            )
        if actual_qty is None:
            return (
                jsonify(
                    {
                        "message": f"明细 {d.apply_detail_id} 缺少实际出库数量，请检查后重试"
                    }
                ),
                400,
            )

        if (s.finished_amount or 0) < actual_qty:
            return (
                jsonify(
                    {
                        "message": f"仓库编号 {s.finished_shoe_id} 库存不足（库存 {s.finished_amount}，实际出库 {actual_qty}）"
                    }
                ),
                400,
            )

    # 创建出库主记录
    now_dt = datetime.now()
    timestamp = format_datetime(datetime.now())
    rid_suffix = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    shoe_outbound_rid = "FOR" + rid_suffix + "T0"

    outbound_record = ShoeOutboundRecord(
        shoe_outbound_rid=shoe_outbound_rid,
        outbound_datetime=timestamp,
        outbound_type=0,
        remark=(apply_obj.remark or ""),
        picker=picker,
    )
    db.session.add(outbound_record)
    db.session.flush()

    total_amount = 0
    expected_total_amount = 0
    diff_notes = []

    # === 获取本申请涉及的所有订单 ===
    order_id_rows = (
        db.session.query(Order.order_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .filter(FinishedShoeStorage.finished_shoe_id.in_(storage_ids))
        .distinct()
        .all()
    )
    unique_order_ids = {row.order_id for row in order_id_rows}

    # 扣减库存 + 写出库明细
    for d in details:
        s = storage_map[d.finished_shoe_storage_id]
        input_obj = detail_input_map.get(d.apply_detail_id, {})
        qty = input_obj.get("actual_pairs")
        actual_carton = input_obj.get("actual_carton")
        if actual_carton is not None:
            qty = int(
                (actual_carton or Decimal("0")) * Decimal(str(d.pairs_per_carton or 0))
            )
        expected_qty = int(d.total_pairs or 0)
        expected_total_amount += expected_qty

        s.finished_amount = (s.finished_amount or 0) - qty
        if s.finished_amount < 0:
            return (
                jsonify({"message": f"仓库编号{s.finished_shoe_id}出库数量超过库存"}),
                400,
            )

        record_detail = ShoeOutboundRecordDetail(
            shoe_outbound_record_id=outbound_record.shoe_outbound_record_id,
            outbound_amount=qty,
            finished_shoe_storage_id=d.finished_shoe_storage_id,
            remark=d.remark,
        )
        db.session.add(record_detail)
        db.session.flush()

        if _determine_outbound_status(s):
            s.finished_status = 2

        total_amount += qty
        diff_value = qty - expected_qty
        # 将实际出库数量/箱数回写到申请明细，避免后续再次按预计数量处理
        d.total_pairs = qty
        if actual_carton is not None:
            d.carton_count = actual_carton
        if diff_value != 0:
            diff_notes.append(
                f"明细{d.apply_detail_id}: 预计{expected_qty} 实际{qty} 差异{diff_value}"
            )

    if diff_notes:
        diff_text = "; ".join(diff_notes)

    outbound_record.outbound_amount = total_amount

    # 更新申请单状态 & 关联出库记录
    apply_obj.status = 4  # 已完成出库
    apply_obj.warehouse_staff_id = staff_id
    apply_obj.outbound_record_id = outbound_record.shoe_outbound_record_id
    apply_obj.actual_outbound_datetime = now_dt

    # 推订单事件（所有涉及的订单）
    processor: EventProcessor = current_app.config.get("event_processor")
    if processor and unique_order_ids:
        orders = (
            db.session.query(Order, FinishedShoeStorage)
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                FinishedShoeStorage,
                FinishedShoeStorage.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(Order.order_id.in_(unique_order_ids))
            .all()
        )
        storage_map_by_order = {}
        order_map = {}
        for order_row, storage in orders:
            storage_map_by_order.setdefault(order_row.order_id, []).append(storage)
            order_map[order_row.order_id] = order_row

        for order_id, storages_per_order in storage_map_by_order.items():
            if all(s.finished_status == 2 for s in storages_per_order):
                order_row = order_map[order_id]
                order_row.order_actual_end_date = datetime.now().date()
                try:
                    for operation in range(22, 36):
                        event = Event(
                            staff_id=staff_id,
                            handle_time=datetime.now(),
                            operation_id=operation,
                            event_order_id=order_row.order_id,
                        )
                        processor.processEvent(event)
                except Exception as e:
                    logger.debug(e)
                    db.session.rollback()
                    return jsonify({"message": "推进流程失败"}), 500

    db.session.commit()
    return jsonify(
        {
            "message": "success",
            "applyId": apply_obj.apply_id,
            "applyRId": apply_obj.apply_rid,
            "outboundRecordId": outbound_record.shoe_outbound_record_id,
            "outboundRId": outbound_record.shoe_outbound_rid,
            "status": apply_obj.status,
            "statusLabel": _OUTBOUND_APPLY_STATUS_LABEL.get(
                apply_obj.status, "未知状态"
            ),
            "expectedTotalPairs": expected_total_amount,
            "actualTotalPairs": total_amount,
            "quantityDiff": total_amount - expected_total_amount,
        }
    )

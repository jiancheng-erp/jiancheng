from datetime import datetime
from app_config import db
from constants import (
    FINISHED_STORAGE_STATUS,
    FINISHED_STORAGE_STATUS_ENUM,
    SHOESIZERANGE,
)
from flask import Blueprint, jsonify, request
from models import (
    Order,
    OrderShoe,
    OrderShoeType,
    Shoe,
    ShoeType,
    Color,
    Customer,
    FinishedShoeStorage,
    ShoeInboundRecord,
    ShoeInboundRecordDetail,
    ShoeOutboundRecord,
    ShoeOutboundRecordDetail,
)
from sqlalchemy import func, desc
from api_utility import format_datetime

finished_storage_overview_bp = Blueprint("finished_storage_overview_bp", __name__)


@finished_storage_overview_bp.route(
    "/admin/finished-storage-overview", methods=["GET"]
)
def finished_storage_overview():
    """
    管理员成品仓库存状况概览，支持按订单号、鞋型号、客户、状态筛选和分页。
    状态: 0=未完成入库, 1=已完成入库, 2=已完成出库
    """
    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("pageSize", type=int, default=20)
    order_rid = request.args.get("orderRId", "", type=str).strip()
    shoe_rid = request.args.get("shoeRId", "", type=str).strip()
    customer_name = request.args.get("customerName", "", type=str).strip()
    status_num = request.args.get("statusNum", type=int)

    query = (
        db.session.query(
            FinishedShoeStorage,
            Order.order_rid,
            Order.order_id,
            Shoe.shoe_rid,
            OrderShoe.customer_product_name,
            Color.color_name,
            Customer.customer_name,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == FinishedShoeStorage.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
    )

    if order_rid:
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid:
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if customer_name:
        query = query.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if status_num is not None and status_num >= 0:
        query = query.filter(FinishedShoeStorage.finished_status == status_num)

    total = query.count()
    rows = (
        query.order_by(desc(FinishedShoeStorage.update_time))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for storage, order_rid_val, order_id, shoe_rid_val, cust_prod, color, cust_name in rows:
        status_label = FINISHED_STORAGE_STATUS.get(
            storage.finished_status, "未知"
        )
        result.append(
            {
                "finishedShoeId": storage.finished_shoe_id,
                "orderShoeTypeId": storage.order_shoe_type_id,
                "orderId": order_id,
                "orderRid": order_rid_val,
                "shoeRid": shoe_rid_val,
                "customerProductName": cust_prod or "",
                "colorName": color or "",
                "customerName": cust_name or "",
                "estimatedAmount": storage.finished_estimated_amount or 0,
                "actualAmount": storage.finished_actual_amount or 0,
                "currentStock": storage.finished_amount or 0,
                "status": storage.finished_status,
                "statusLabel": status_label,
                "updateTime": format_datetime(storage.update_time)
                if storage.update_time
                else "",
            }
        )

    return jsonify({"result": result, "total": total})


@finished_storage_overview_bp.route(
    "/admin/finished-storage-inbound-records", methods=["GET"]
)
def finished_storage_inbound_records():
    """
    获取某个 finished_shoe_id 对应的所有入库记录（含已撤回的）。
    """
    storage_id = request.args.get("finishedShoeId", type=int)
    if not storage_id:
        return jsonify({"error": "缺少 finishedShoeId"}), 400

    rows = (
        db.session.query(ShoeInboundRecord, ShoeInboundRecordDetail)
        .join(
            ShoeInboundRecordDetail,
            ShoeInboundRecordDetail.shoe_inbound_record_id
            == ShoeInboundRecord.shoe_inbound_record_id,
        )
        .filter(ShoeInboundRecordDetail.finished_shoe_storage_id == storage_id)
        .order_by(desc(ShoeInboundRecord.inbound_datetime))
        .all()
    )

    result = []
    for record, detail in rows:
        result.append(
            {
                "recordId": record.shoe_inbound_record_id,
                "detailId": detail.record_detail_id,
                "rid": record.shoe_inbound_rid,
                "amount": detail.inbound_amount,
                "datetime": format_datetime(record.inbound_datetime),
                "inboundType": record.inbound_type,
                "inboundTypeLabel": "自产" if record.inbound_type == 0 else "外协",
                "transactionType": record.transaction_type,
                "transactionTypeLabel": "入库"
                if record.transaction_type == 1
                else "撤回",
                "isDeleted": detail.is_deleted or 0,
                "canRevert": record.transaction_type == 1
                and not detail.is_deleted,
            }
        )
    return jsonify({"result": result})


@finished_storage_overview_bp.route(
    "/admin/finished-storage-outbound-records", methods=["GET"]
)
def finished_storage_outbound_records():
    """
    获取某个 finished_shoe_id 对应的所有出库记录。
    """
    storage_id = request.args.get("finishedShoeId", type=int)
    if not storage_id:
        return jsonify({"error": "缺少 finishedShoeId"}), 400

    rows = (
        db.session.query(ShoeOutboundRecord, ShoeOutboundRecordDetail)
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.shoe_outbound_record_id
            == ShoeOutboundRecord.shoe_outbound_record_id,
        )
        .filter(ShoeOutboundRecordDetail.finished_shoe_storage_id == storage_id)
        .order_by(desc(ShoeOutboundRecord.outbound_datetime))
        .all()
    )

    result = []
    for record, detail in rows:
        result.append(
            {
                "recordId": record.shoe_outbound_record_id,
                "detailId": detail.record_detail_id,
                "rid": record.shoe_outbound_rid,
                "amount": detail.outbound_amount,
                "datetime": format_datetime(record.outbound_datetime),
                "picker": record.picker or "",
                "remark": record.remark or "",
            }
        )
    return jsonify({"result": result})


@finished_storage_overview_bp.route(
    "/admin/revert-finished-inbound", methods=["DELETE"]
)
def revert_finished_inbound():
    """
    撤销一次入库记录。
    与现有 deletefinishedinbounddetail 逻辑一致：
    - 扣减 storage 的 actual_amount / amount
    - 标记 detail 为 is_deleted=1
    - 创建 transaction_type=2 的撤回记录
    """
    detail_id = request.args.get("detailId", type=int)
    if not detail_id:
        return jsonify({"error": "缺少 detailId"}), 400

    row = (
        db.session.query(
            ShoeInboundRecord,
            ShoeInboundRecordDetail,
            FinishedShoeStorage,
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
        .filter(ShoeInboundRecordDetail.record_detail_id == detail_id)
        .filter(ShoeInboundRecordDetail.is_deleted == 0)
        .filter(ShoeInboundRecord.transaction_type == 1)
        .first()
    )

    if not row:
        return jsonify({"error": "入库记录不存在或已被撤回"}), 404

    record, detail, storage = row

    # 检查是否有出库引用此库存
    outbound_detail = (
        db.session.query(ShoeOutboundRecordDetail)
        .filter(
            ShoeOutboundRecordDetail.finished_shoe_storage_id
            == storage.finished_shoe_id
        )
        .first()
    )
    if outbound_detail:
        return jsonify({"error": "该库存已有出库记录，无法撤回入库"}), 409

    amount = detail.inbound_amount
    storage.finished_actual_amount -= amount
    storage.finished_amount -= amount
    storage.finished_status = 0

    # 尺码级别回退
    for size in SHOESIZERANGE:
        col_actual = f"size_{size}_actual_amount"
        col_amount = f"size_{size}_amount"
        col_detail = f"size_{size}_amount"
        detail_qty = getattr(detail, col_detail, 0) or 0
        if detail_qty:
            cur_actual = getattr(storage, col_actual, 0) or 0
            setattr(storage, col_actual, cur_actual - detail_qty)
            cur_amount = getattr(storage, col_amount, 0) or 0
            setattr(storage, col_amount, cur_amount - detail_qty)

    detail.is_deleted = 1

    timestamp = format_datetime(datetime.now())
    formatted_ts = timestamp.replace("-", "").replace(" ", "").replace(":", "")
    reversal_record = ShoeInboundRecord(
        shoe_inbound_rid="FIR" + formatted_ts + "T0",
        inbound_datetime=datetime.now(),
        inbound_type=record.inbound_type,
        inbound_amount=-amount,
        transaction_type=2,
        related_inbound_record_id=record.shoe_inbound_record_id,
    )
    db.session.add(reversal_record)
    db.session.flush()

    reversal_detail = ShoeInboundRecordDetail(
        shoe_inbound_record_id=reversal_record.shoe_inbound_record_id,
        finished_shoe_storage_id=storage.finished_shoe_id,
        inbound_amount=-amount,
        is_deleted=0,
    )
    # 尺码级别撤回明细
    for size in SHOESIZERANGE:
        col_detail = f"size_{size}_amount"
        detail_qty = getattr(detail, col_detail, 0) or 0
        if detail_qty:
            setattr(reversal_detail, col_detail, -detail_qty)

    db.session.add(reversal_detail)
    db.session.commit()

    return jsonify({"message": f"已撤回入库 {amount} 双"})


@finished_storage_overview_bp.route(
    "/admin/revert-finished-outbound", methods=["DELETE"]
)
def revert_finished_outbound():
    """
    撤销一次出库记录。
    - 恢复 storage 的 amount（库存加回）
    - 删除出库明细记录
    - 如果出库记录下无明细则一并删除出库主记录
    - status 回退（若为 2 已完成出库 → 回退为 1）
    """
    detail_id = request.args.get("detailId", type=int)
    if not detail_id:
        return jsonify({"error": "缺少 detailId"}), 400

    row = (
        db.session.query(ShoeOutboundRecord, ShoeOutboundRecordDetail, FinishedShoeStorage)
        .join(
            ShoeOutboundRecordDetail,
            ShoeOutboundRecordDetail.shoe_outbound_record_id
            == ShoeOutboundRecord.shoe_outbound_record_id,
        )
        .join(
            FinishedShoeStorage,
            FinishedShoeStorage.finished_shoe_id
            == ShoeOutboundRecordDetail.finished_shoe_storage_id,
        )
        .filter(ShoeOutboundRecordDetail.record_detail_id == detail_id)
        .first()
    )

    if not row:
        return jsonify({"error": "出库记录不存在"}), 404

    record, detail, storage = row
    amount = detail.outbound_amount or 0

    # 恢复库存
    storage.finished_amount = (storage.finished_amount or 0) + amount
    if storage.finished_status == 2:
        storage.finished_status = 1

    # 尺码级别恢复
    for size in SHOESIZERANGE:
        col_amount = f"size_{size}_amount"
        col_detail = f"size_{size}_amount"
        detail_qty = getattr(detail, col_detail, 0) or 0
        if detail_qty:
            cur = getattr(storage, col_amount, 0) or 0
            setattr(storage, col_amount, cur + detail_qty)

    # 删除出库明细
    db.session.delete(detail)
    db.session.flush()

    # 如果该出库主记录下已无其他明细，也删除主记录
    remaining = (
        db.session.query(ShoeOutboundRecordDetail)
        .filter(
            ShoeOutboundRecordDetail.shoe_outbound_record_id
            == record.shoe_outbound_record_id,
            ShoeOutboundRecordDetail.record_detail_id != detail_id,
        )
        .count()
    )
    if remaining == 0:
        db.session.delete(record)

    db.session.commit()
    return jsonify({"message": f"已撤回出库 {amount} 双"})

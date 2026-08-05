"""管理员用：核对/调整「核定用量与实际采购数量差距过大」的采购订单明细。

- 核定用量  approval_amount        —— 依据 BOM 核定的合理需求量
- 采购数量  purchase_amount        —— 下单采购数量
- 调整数量  adjust_purchase_amount —— 调整后采购数量（多次下发/补单时优先生效）

实际下单量按现网约定取「调整数量优先，否则原采购数量」。
当实际下单量远大于核定用量时，往往是录入错误/重复下单/漏核定，需要人工复核并调整。
"""

from decimal import Decimal, InvalidOperation

from app_config import db
from flask import Blueprint, jsonify, request
from sqlalchemy import and_, case, func, or_
from models import (
    Material,
    Order,
    OrderShoe,
    PurchaseDivideOrder,
    PurchaseOrder,
    PurchaseOrderItem,
    Shoe,
    Supplier,
)

purchase_approval_adjust_bp = Blueprint("purchase_approval_adjust_bp", __name__)

_PURCHASE_TYPE_LABEL = {"N": "一次采购", "S": "二次采购"}


def _dec(value) -> Decimal:
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(0)


def _effective_amount(item: PurchaseOrderItem) -> Decimal:
    adjust = _dec(item.adjust_purchase_amount)
    if adjust != 0:
        return adjust
    return _dec(item.purchase_amount)


def _num(value):
    """Decimal -> float，None 保持 None，便于前端展示。"""
    if value is None:
        return None
    return float(_dec(value))


@purchase_approval_adjust_bp.route("/purchaseadjust/list", methods=["GET"])
def list_over_purchase_items():
    """列出核定与采购差距过大的采购明细。

    Query:
      ratio               倍数阈值（effective >= approval * ratio），默认 3
      minExcess           绝对差阈值（effective - approval），过滤噪声，默认 0
      minApproval         核定用量下限，低于此值不计（仅对有核定的行），默认 0
      includeZeroApproval 是否纳入「无核定却采购」的行，默认 1
      keyword             按订单号/工厂型号模糊筛选
      page / pageSize     分页，默认 1 / 20
    """
    try:
        ratio = Decimal(str(request.args.get("ratio", "3")))
    except (InvalidOperation, TypeError, ValueError):
        ratio = Decimal("3")
    min_excess = _dec(request.args.get("minExcess", "0"))
    min_approval = _dec(request.args.get("minApproval", "0"))
    include_zero_approval = request.args.get("includeZeroApproval", "1") not in (
        "0",
        "false",
        "False",
    )
    keyword = (request.args.get("keyword") or "").strip()
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(int(request.args.get("pageSize", 20)), 1), 200)
    except (TypeError, ValueError):
        page_size = 20

    # 实际下单量：调整数量非 0 优先，否则原采购数量
    effective_expr = case(
        (
            func.coalesce(PurchaseOrderItem.adjust_purchase_amount, 0) != 0,
            PurchaseOrderItem.adjust_purchase_amount,
        ),
        else_=func.coalesce(PurchaseOrderItem.purchase_amount, 0),
    )
    approval_expr = func.coalesce(PurchaseOrderItem.approval_amount, 0)
    ratio_order = case(
        (approval_expr > 0, effective_expr / approval_expr), else_=None
    )

    over_purchase_cond = and_(
        approval_expr > 0,
        approval_expr >= min_approval,
        effective_expr >= approval_expr * ratio,
        (effective_expr - approval_expr) >= min_excess,
    )
    zero_approval_cond = and_(
        approval_expr <= 0,
        effective_expr > 0,
        effective_expr >= min_excess,
    )
    flag_cond = (
        or_(over_purchase_cond, zero_approval_cond)
        if include_zero_approval
        else over_purchase_cond
    )

    query = (
        db.session.query(
            PurchaseOrderItem,
            PurchaseOrder.purchase_order_rid,
            PurchaseOrder.purchase_order_type,
            Order.order_rid,
            Shoe.shoe_rid,
            OrderShoe.customer_product_name,
            Material.material_name,
            Supplier.supplier_name,
        )
        .join(
            PurchaseDivideOrder,
            PurchaseDivideOrder.purchase_divide_order_id
            == PurchaseOrderItem.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseOrder.purchase_order_id == PurchaseDivideOrder.purchase_order_id,
        )
        .outerjoin(Order, Order.order_id == PurchaseOrder.order_id)
        .outerjoin(OrderShoe, OrderShoe.order_shoe_id == PurchaseOrder.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .outerjoin(Material, Material.material_id == PurchaseOrderItem.material_id)
        .outerjoin(Supplier, Supplier.supplier_id == Material.material_supplier)
        .filter(flag_cond)
    )

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(Order.order_rid.like(like), Shoe.shoe_rid.like(like))
        )

    total = query.count()

    # 按订单时间倒序（新订单在前），同订单内按超采倍数降序
    page_rows = (
        query.order_by(
            Order.start_date.desc(),
            Order.order_rid.desc(),
            ratio_order.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for (
        item,
        purchase_order_rid,
        purchase_order_type,
        order_rid,
        shoe_rid,
        customer_product_name,
        material_name,
        supplier_name,
    ) in page_rows:
        approval = _dec(item.approval_amount)
        effective = _effective_amount(item)
        if approval > 0:
            reason = "超采"
            ratio_value = float(effective / approval)
        else:
            reason = "无核定却采购"
            ratio_value = None

        result.append(
            {
                "purchaseOrderItemId": item.purchase_order_item_id,
                "purchaseOrderRid": purchase_order_rid or "",
                "purchaseType": _PURCHASE_TYPE_LABEL.get(
                    purchase_order_type, purchase_order_type or "?"
                ),
                "orderRid": order_rid or "",
                "shoeRid": shoe_rid or "",
                "customerProductName": customer_product_name or "",
                "materialName": material_name or "",
                "supplierName": supplier_name or "",
                "materialModel": item.material_model or "",
                "materialSpecification": item.material_specification or "",
                "color": item.color or "",
                "inboundUnit": item.inbound_unit or "",
                "approvalAmount": _num(item.approval_amount),
                "purchaseAmount": _num(item.purchase_amount),
                "adjustPurchaseAmount": _num(item.adjust_purchase_amount),
                "effectiveAmount": float(effective),
                "excess": float(effective - approval),
                "ratio": ratio_value,
                "reason": reason,
            }
        )

    return jsonify({"total": total, "result": result})


@purchase_approval_adjust_bp.route("/purchaseadjust/adjust", methods=["POST"])
def adjust_purchase_item():
    """调整单条采购明细的调整采购数量（可选同时修正核定用量）。"""
    data = request.get_json() or {}
    item_id = data.get("purchaseOrderItemId")
    if item_id is None:
        return jsonify({"message": "缺少 purchaseOrderItemId"}), 400

    item = db.session.query(PurchaseOrderItem).get(item_id)
    if item is None:
        return jsonify({"message": "采购明细不存在"}), 404

    if "adjustPurchaseAmount" in data and data["adjustPurchaseAmount"] is not None:
        new_adjust = _dec(data["adjustPurchaseAmount"])
        if new_adjust < 0:
            return jsonify({"message": "调整采购数量不能为负"}), 400
        item.adjust_purchase_amount = new_adjust

    if "approvalAmount" in data and data["approvalAmount"] is not None:
        new_approval = _dec(data["approvalAmount"])
        if new_approval < 0:
            return jsonify({"message": "核定用量不能为负"}), 400
        item.approval_amount = new_approval

    db.session.commit()
    return jsonify(
        {
            "message": "success",
            "purchaseOrderItemId": item.purchase_order_item_id,
            "adjustPurchaseAmount": _num(item.adjust_purchase_amount),
            "approvalAmount": _num(item.approval_amount),
        }
    )

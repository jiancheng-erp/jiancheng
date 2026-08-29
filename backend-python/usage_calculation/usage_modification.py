"""用量修改相关接口。

面向"已经完成一次采购订单创建、二次采购订单创建"的订单，允许对 BOM 用量
（单位用量 / 核定用量 / 分码用量）以及采购用量（采购数量 / 分码采购量）进行修改。

订单列表页 -> 选择订单 -> 复用 /secondpurchase/getordershoelist 获取鞋型列表 ->
复用 /secondpurchase/getshoebomitems 获取材料明细 -> 本模块 save 接口保存修改。
"""

from decimal import Decimal, InvalidOperation
import copy

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, func, not_, or_

from app_config import db
from models import (
    Bom,
    BomItem,
    Color,
    Customer,
    Material,
    MaterialType,
    Order,
    OrderShoe,
    OrderShoeBatchInfo,
    OrderShoeType,
    ProductionInstructionItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Shoe,
    ShoeType,
    Supplier,
)
from shared_apis.batch_info_type import get_order_batch_type_helper
from wechat_api.send_message_api import send_configurable_message

usage_modification_bp = Blueprint("usage_modification_bp", __name__)

# 已完成采购订单创建（已提交/已下发）对应的采购订单状态
_COMPLETED_PURCHASE_STATUS = ("2", "3")


def _notify_warehouse_manager_usage_modified(bom_item_ids, changes_text):
    """技术部下发后修改用量后，通知总仓经理，包含修改前/修改后全部信息。"""
    valid_ids = [i for i in bom_item_ids if i is not None]
    if not valid_ids:
        return
    order_info = (
        db.session.query(Order.order_rid, Shoe.shoe_rid)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Bom, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .join(BomItem, BomItem.bom_id == Bom.bom_id)
        .filter(BomItem.bom_item_id.in_(valid_ids))
        .first()
    )
    if not order_info:
        return
    order_rid, shoe_rid = order_info
    message = (
        "技术部已进行下发后用量修改，订单号：{order_rid}，鞋型号：{shoe_rid}\n"
        "{changes}\n"
        "请总仓经理及时核对"
    )
    send_configurable_message(
        "tech_usage_modification_notify_warehouse",
        message,
        "FanJianMing",
        context={"order_rid": order_rid, "shoe_rid": shoe_rid, "changes": changes_text},
        push_to_group=True,
    )


def _fmt_num(value):
    if value is None or value == "":
        return "-"
    dec = _to_decimal(value)
    if dec is None:
        return str(value)
    dec = dec.normalize()
    return format(dec, "f")


def _num_eq(a, b):
    da, db_ = _to_decimal(a), _to_decimal(b)
    if da is None and db_ is None:
        return True
    if da is None or db_ is None:
        return False
    return da == db_


def _is_zero(value):
    dec = _to_decimal(value)
    return dec is not None and dec == 0


def _all_zero(values):
    return all(_is_zero(v) or _to_decimal(v) is None for v in values)


def _sizes_changed(old, new):
    if len(old) != len(new):
        return True
    return any(not _num_eq(o, n) for o, n in zip(old, new))


def _fmt_sizes(sizes):
    return "[" + ", ".join(_fmt_num(s) for s in sizes) + "]"


def _build_usage_change_line(
    name,
    category,
    old_unit,
    new_unit,
    old_appr,
    new_appr,
    old_pur,
    new_pur,
    old_sizes,
    new_sizes,
    old_size_pur,
    new_size_pur,
):
    """组装单条材料的修改前/修改后明细，仅列出发生变化的字段。更改为 0 的字段不列出。"""
    parts = []
    if not _num_eq(old_unit, new_unit) and not _is_zero(new_unit):
        parts.append(f"  单位用量：{_fmt_num(old_unit)} → {_fmt_num(new_unit)}")
    if not _num_eq(old_appr, new_appr) and not _is_zero(new_appr):
        parts.append(f"  核定用量：{_fmt_num(old_appr)} → {_fmt_num(new_appr)}")
    if not _num_eq(old_pur, new_pur) and not _is_zero(new_pur):
        parts.append(f"  采购数量：{_fmt_num(old_pur)} → {_fmt_num(new_pur)}")
    if category == 1:
        if _sizes_changed(old_sizes, new_sizes) and not _all_zero(new_sizes):
            parts.append(f"  分码核定：{_fmt_sizes(old_sizes)} → {_fmt_sizes(new_sizes)}")
        if (
            old_size_pur
            and _sizes_changed(old_size_pur, new_size_pur)
            and not _all_zero(new_size_pur)
        ):
            parts.append(
                f"  分码采购：{_fmt_sizes(old_size_pur)} → {_fmt_sizes(new_size_pur)}"
            )
    if not parts:
        return ""
    return f"材料：{name}\n" + "\n".join(parts)



def _to_decimal(value):
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _to_int(value):
    if value is None or value == "":
        return None
    try:
        return int(round(float(value)))
    except (ValueError, TypeError):
        return None


@usage_modification_bp.route("/usagemodification/orders", methods=["GET"])
def get_modifiable_orders():
    """列出已经完成一次采购订单创建与二次采购订单创建的订单。"""
    keyword = request.args.get("keyword", "").strip()

    # 已完成一次采购订单创建的订单（一次采购订单 type='F' 且已提交/下发）
    first_done_order_ids = (
        db.session.query(PurchaseOrder.order_id)
        .filter(
            PurchaseOrder.purchase_order_type == "F",
            PurchaseOrder.purchase_order_status.in_(_COMPLETED_PURCHASE_STATUS),
        )
        .distinct()
        .subquery()
    )

    # 已完成二次采购订单创建的订单（二次采购订单 type='S' 且已提交/下发）
    second_done_order_ids = (
        db.session.query(PurchaseOrder.order_id)
        .filter(
            PurchaseOrder.purchase_order_type == "S",
            PurchaseOrder.purchase_order_status.in_(_COMPLETED_PURCHASE_STATUS),
        )
        .distinct()
        .subquery()
    )

    query = (
        db.session.query(Order, Customer)
        .outerjoin(Customer, Customer.customer_id == Order.customer_id)
        .filter(
            or_(
                Order.order_id.in_(
                    db.session.query(first_done_order_ids.c.order_id)
                ),
                Order.order_id.in_(
                    db.session.query(second_done_order_ids.c.order_id)
                ),
            )
        )
    )

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Order.order_rid.like(like),
                Customer.customer_name.like(like),
            )
        )

    result = []
    for order, customer in query.order_by(Order.order_rid.desc()).all():
        result.append(
            {
                "orderId": order.order_id,
                "orderRid": order.order_rid,
                "customerName": customer.customer_name if customer else "",
                "createTime": (
                    order.start_date.isoformat() if order.start_date else None
                ),
                "deadlineTime": (
                    order.end_date.isoformat() if order.end_date else None
                ),
            }
        )

    return jsonify(result)


@usage_modification_bp.route("/usagemodification/ordershoes", methods=["GET"])
def get_usage_modification_order_shoes():
    """按颜色拆开返回订单下的鞋型列表（每个鞋型+颜色一行）。"""
    order_id = request.args.get("orderId")

    entities = (
        db.session.query(OrderShoe, OrderShoeType, Shoe, Color)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(OrderShoe.order_id == order_id)
        .order_by(Shoe.shoe_rid, Color.color_name)
        .all()
    )

    result = []
    for order_shoe, order_shoe_type, shoe, color in entities:
        result.append(
            {
                "orderShoeId": order_shoe.order_shoe_id,
                "orderShoeTypeId": order_shoe_type.order_shoe_type_id,
                "inheritId": shoe.shoe_rid,
                "customerId": order_shoe.customer_product_name,
                "designer": shoe.shoe_designer,
                "editter": order_shoe.adjust_staff,
                "color": color.color_name,
            }
        )
    return jsonify(result)


def _is_purchase_completed(order_shoe_id, purchase_type):
    """判断某订单鞋型的采购订单是否已完成（已提交/已下发，状态 '2' 或 '3'）。"""
    if order_shoe_id is None:
        return False
    return (
        db.session.query(PurchaseOrder.purchase_order_id)
        .filter(
            PurchaseOrder.order_shoe_id == order_shoe_id,
            PurchaseOrder.purchase_order_type == purchase_type,
            PurchaseOrder.purchase_order_status.in_(_COMPLETED_PURCHASE_STATUS),
        )
        .first()
        is not None
    )


def _resolve_purchase_scope(order_shoe_id):
    """依据采购完成状态确定可修改的采购范围（按材料类型区分）。

    - 一次采购(物控经理, 'F') 与 二次采购(总仓, 'S') 都已完成 -> "both" 两者都可修改
    - 仅一次采购已完成 -> "first"  仅修改一次采购材料
    - 仅二次采购已完成 -> "second" 仅修改二次采购材料
    - 都未完成 -> 默认 "first"
    """
    first_done = _is_purchase_completed(order_shoe_id, "F")
    second_done = _is_purchase_completed(order_shoe_id, "S")
    if first_done and second_done:
        return "both"
    if second_done and not first_done:
        return "second"
    return "first"


def _second_purchase_material_predicate():
    """二次采购(总仓)负责的材料：辅料(A / material_type_id=3) 与 烫底。"""
    pit_type = func.coalesce(ProductionInstructionItem.material_type, "")
    return or_(
        pit_type == "A",
        Material.material_type_id == 3,
        and_(pit_type == "H", Material.material_name == "烫底"),
    )


def _material_scope_filter(purchase_scope):
    """按采购范围返回材料过滤条件；both 表示不过滤（两类材料都返回）。"""
    if purchase_scope == "both":
        return None
    accessory = _second_purchase_material_predicate()
    if purchase_scope == "second":
        return accessory
    # 一次采购(物控)负责的材料 = 二次采购材料之外的全部
    return not_(accessory)


@usage_modification_bp.route("/usagemodification/bomitems", methods=["GET"])
def get_usage_modification_bom_items():
    """按鞋型(订单鞋型)与颜色查询 BOM 的材料明细，附带采购用量。

    始终查询一次BOM(bom_type=0)，并根据采购完成状态按材料类型区分范围：
    - 一次采购(物控经理)与二次采购(总仓)都已完成 -> 两类材料都返回
    - 仅一次采购已完成 -> 仅返回一次采购材料（主料等）
    - 仅二次采购已完成 -> 仅返回二次采购材料（辅料 + 烫底）
    """
    order_shoe_type_id = request.args.get("orderShoeTypeId")
    order_id = request.args.get("orderId")

    size_name_info = get_order_batch_type_helper(order_id) if order_id else []

    # 依据采购完成状态确定可修改的采购范围（按材料类型区分）
    order_shoe_type = (
        db.session.query(OrderShoeType)
        .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
        .first()
    )
    order_shoe_id = order_shoe_type.order_shoe_id if order_shoe_type else None
    purchase_scope = _resolve_purchase_scope(order_shoe_id)
    material_filter = _material_scope_filter(purchase_scope)

    entities = (
        db.session.query(
            BomItem,
            Material,
            MaterialType,
            Supplier,
            Color,
            PurchaseOrderItem,
            ProductionInstructionItem,
            OrderShoeType.order_shoe_type_id,
        )
        .join(Bom, BomItem.bom_id == Bom.bom_id)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(Material, Material.material_id == BomItem.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .outerjoin(
            PurchaseOrderItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id
        )
        .outerjoin(
            ProductionInstructionItem,
            ProductionInstructionItem.production_instruction_item_id
            == BomItem.production_instruction_item_id,
        )
        .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
        .filter(Bom.bom_type == 0)
    )
    if material_filter is not None:
        entities = entities.filter(material_filter)
    entities = entities.order_by(
        Supplier.supplier_name, Material.material_name
    ).all()

    size_info_template = [
        {
            "size": name_obj["label"],
            "approvalAmount": 0,
            "purchaseAmount": 0,
            "orderPairs": 0,
        }
        for name_obj in size_name_info
    ]

    # 各订单鞋型(颜色)的下单数量（分码 + 合计），用于核定用量自动计算
    order_shoe_type_ids = {row[7] for row in entities}
    pairs_map = _build_order_pairs_map(order_shoe_type_ids)

    result = {}
    for (
        bom_item,
        material,
        material_type,
        supplier,
        color,
        purchase_order_item,
        production_instruction_item,
        order_shoe_type_id,
    ) in entities:
        if bom_item.bom_item_id in result:
            # 已处理过该 BOM 项，补充采购项信息（若之前缺失）
            if (
                result[bom_item.bom_item_id]["purchaseOrderItemId"] is None
                and purchase_order_item is not None
            ):
                _fill_purchase_info(
                    result[bom_item.bom_item_id], purchase_order_item, size_name_info
                )
            continue

        craft_name = (
            production_instruction_item.pre_craft_name
            if production_instruction_item and production_instruction_item.pre_craft_name
            else bom_item.craft_name
        )

        entry = {
            "bomItemId": bom_item.bom_item_id,
            "purchaseOrderItemId": None,
            "materialType": material_type.material_type_name,
            "materialName": material.material_name,
            "materialModel": bom_item.material_model,
            "materialSpecification": bom_item.material_specification,
            "color": bom_item.bom_item_color or color.color_name,
            "unit": material.material_unit,
            "craftName": craft_name,
            "materialCategory": material.material_category,
            "unitUsage": (
                float(bom_item.unit_usage) if bom_item.unit_usage is not None else 0
            ),
            "approvalUsage": (
                float(bom_item.total_usage) if bom_item.total_usage is not None else 0
            ),
            "purchaseAmount": 0,
            "sizeInfo": copy.deepcopy(size_info_template),
        }

        pairs = pairs_map.get(order_shoe_type_id, {})
        entry["orderTotalPairs"] = pairs.get("total", 0)

        # BOM 分码用量 + 各码下单数量
        for i in range(len(size_name_info)):
            approval_amount = getattr(bom_item, f"size_{34 + i}_total_usage", None)
            entry["sizeInfo"][i]["approvalAmount"] = approval_amount or 0
            entry["sizeInfo"][i]["orderPairs"] = pairs.get(34 + i, 0)

        if purchase_order_item is not None:
            _fill_purchase_info(entry, purchase_order_item, size_name_info)

        result[bom_item.bom_item_id] = entry

    return jsonify(
        {
            "purchaseScope": purchase_scope,
            "items": list(result.values()),
        }
    )


def _build_order_pairs_map(order_shoe_type_ids):
    """按订单鞋型(颜色)统计下单数量：{ost_id: {34..46: 数量, 'total': 合计}}。"""
    pairs_map = {}
    valid_ids = [i for i in order_shoe_type_ids if i is not None]
    if not valid_ids:
        return pairs_map

    batch_infos = (
        db.session.query(OrderShoeBatchInfo)
        .filter(OrderShoeBatchInfo.order_shoe_type_id.in_(valid_ids))
        .all()
    )
    for info in batch_infos:
        bucket = pairs_map.setdefault(
            info.order_shoe_type_id,
            {**{i: 0 for i in range(34, 47)}, "total": 0},
        )
        for i in range(34, 47):
            bucket[i] += getattr(info, f"size_{i}_amount", 0) or 0
        bucket["total"] += info.total_amount or 0
    return pairs_map


def _fill_purchase_info(entry, purchase_order_item, size_name_info):
    """把采购项的采购用量填入 entry。"""
    entry["purchaseOrderItemId"] = purchase_order_item.purchase_order_item_id
    entry["purchaseAmount"] = (
        float(purchase_order_item.purchase_amount)
        if purchase_order_item.purchase_amount is not None
        else 0
    )
    for i in range(len(size_name_info)):
        size_purchase = getattr(
            purchase_order_item, f"size_{34 + i}_purchase_amount", None
        )
        entry["sizeInfo"][i]["purchaseAmount"] = size_purchase or 0


@usage_modification_bp.route("/usagemodification/save", methods=["POST"])
def save_usage_modification():
    """保存 BOM 用量与采购用量的修改。

    请求体::

        {
            "items": [
                {
                    "bomItemId": 1,
                    "purchaseOrderItemId": 2,          # 可为空
                    "materialCategory": 0/1,            # 1 表示按尺码
                    "unitUsage": 1.23,
                    "approvalUsage": 100,
                    "purchaseAmount": 120,
                    "sizeInfo": [
                        {"size": "35", "approvalAmount": 10, "purchaseAmount": 12},
                        ...
                    ]
                }
            ]
        }
    """
    items = request.json.get("items", []) if request.json else []
    change_lines = []

    for item in items:
        bom_item_id = item.get("bomItemId")
        if bom_item_id is None:
            continue

        bom_item = (
            db.session.query(BomItem)
            .filter(BomItem.bom_item_id == bom_item_id)
            .first()
        )
        if bom_item is None:
            continue

        material_category = item.get("materialCategory", 0)
        size_info = item.get("sizeInfo") or []

        material = (
            db.session.query(Material)
            .filter(Material.material_id == bom_item.material_id)
            .first()
        )
        material_name = material.material_name if material else ""

        # 快照修改前的用量信息
        old_unit = bom_item.unit_usage
        old_approval = bom_item.total_usage
        old_sizes = [
            getattr(bom_item, f"size_{34 + i}_total_usage", None) for i in range(13)
        ]

        purchase_order_item = None
        purchase_order_item_id = item.get("purchaseOrderItemId")
        if purchase_order_item_id is not None:
            purchase_order_item = (
                db.session.query(PurchaseOrderItem)
                .filter(
                    PurchaseOrderItem.purchase_order_item_id == purchase_order_item_id
                )
                .first()
            )
        old_purchase = (
            purchase_order_item.purchase_amount if purchase_order_item else None
        )
        old_size_purchase = (
            [
                getattr(purchase_order_item, f"size_{34 + i}_purchase_amount", None)
                for i in range(13)
            ]
            if purchase_order_item
            else []
        )

        # 更新 BOM 用量
        unit_usage = _to_decimal(item.get("unitUsage"))
        if unit_usage is not None:
            bom_item.unit_usage = unit_usage

        approval_usage = _to_decimal(item.get("approvalUsage"))
        if approval_usage is not None:
            bom_item.total_usage = approval_usage

        if material_category == 1:
            for i, size_entry in enumerate(size_info):
                approval_amount = _to_int(size_entry.get("approvalAmount"))
                setattr(bom_item, f"size_{34 + i}_total_usage", approval_amount)

        # 更新采购用量
        if purchase_order_item is not None:
            purchase_amount = _to_decimal(item.get("purchaseAmount"))
            if purchase_amount is not None:
                purchase_order_item.purchase_amount = purchase_amount

            if material_category == 1:
                for i, size_entry in enumerate(size_info):
                    size_purchase = _to_int(size_entry.get("purchaseAmount"))
                    setattr(
                        purchase_order_item,
                        f"size_{34 + i}_purchase_amount",
                        size_purchase,
                    )

        line = _build_usage_change_line(
            material_name,
            material_category,
            old_unit,
            bom_item.unit_usage,
            old_approval,
            bom_item.total_usage,
            old_purchase,
            purchase_order_item.purchase_amount if purchase_order_item else None,
            old_sizes,
            [getattr(bom_item, f"size_{34 + i}_total_usage", None) for i in range(13)],
            old_size_purchase,
            (
                [
                    getattr(purchase_order_item, f"size_{34 + i}_purchase_amount", None)
                    for i in range(13)
                ]
                if purchase_order_item
                else []
            ),
        )
        if line:
            change_lines.append(line)

    db.session.commit()
    if change_lines:
        _notify_warehouse_manager_usage_modified(
            [item.get("bomItemId") for item in items], "\n".join(change_lines)
        )
    return jsonify({"status": "success"})


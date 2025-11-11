# scripts/sync_bom_secondary_to_primary.py
from decimal import Decimal, ROUND_CEILING
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import func, or_, desc

from models import (
    Bom,
    BomItem,
    PurchaseOrder,
    PurchaseDivideOrder,
    PurchaseOrderItem,
    OrderShoeType,
    OrderShoe,
    Order,
    CraftSheetItem,
    Material,
)
from logger import logger


# =========================
# 配置区
# =========================
LOG_PREFIX = "[SyncBOM]"
RID_JOINER = "-"
ACTIVE_PO_STATUSES = {"0", "1", "2"}  # 有效采购单状态

# 属于“一次采购”的材料类型：面(1)、里(2)、底材(7)、烫底(16)
FIRST_PURCHASE_MTIDS = {1, 2, 7, 16}

# 底材、烫底 的拆分单类型为 'S'；其他 'N'
DIVIDE_TYPE_S_MTIDS = {7, 16}
DIVIDE_TYPE_FOR_S = "S"
DIVIDE_TYPE_FOR_NORMAL = "N"

# 采购单类型编码（务必与库实际一致）
FIRST_PO_TYPE = "F"   # 一次采购
SECOND_PO_TYPE = "S"  # 二次采购

# BOM 的尺码字段
SIZE_FIELDS = [
    "size_34_total_usage", "size_35_total_usage", "size_36_total_usage",
    "size_37_total_usage", "size_38_total_usage", "size_39_total_usage",
    "size_40_total_usage", "size_41_total_usage", "size_42_total_usage",
    "size_43_total_usage", "size_44_total_usage", "size_45_total_usage",
    "size_46_total_usage",
]

# 尺码字段映射到采购条目字段
SIZE_FIELD_TO_PO_FIELD = {
    f: f.replace("total_usage", "purchase_amount") for f in SIZE_FIELDS
}


# =========================
# 工具函数
# =========================
def _norm_str(s: Optional[str]) -> str:
    return str(s).strip() if s else ""


def _as_int(v) -> Optional[int]:
    try:
        return int(v) if v is not None else None
    except Exception:
        return None


def _as_dec(v, scale=5) -> Decimal:
    if v is None:
        return Decimal("0")
    d = Decimal(str(v))
    return d.quantize(Decimal("1." + "0" * scale))


def _tuple_key_from_vals(mid, model, spec, color):
    """一次/二次BOM对比键：None 与空字符串等价。"""
    return (
        mid if mid is not None else None,
        _norm_str(model),
        _norm_str(spec),
        _norm_str(color),
    )


def _compose_divide_rid(base_po_rid: str, supplier_id: Optional[int]) -> str:
    last4 = "0000" if supplier_id is None else str(supplier_id)[-4:].zfill(4)
    return f"{base_po_rid}{last4}"


def _divide_order_type_for_material_type(material_type_id: Optional[int]) -> str:
    return DIVIDE_TYPE_FOR_S if material_type_id in DIVIDE_TYPE_S_MTIDS else DIVIDE_TYPE_FOR_NORMAL


def _pick_po_for_ordershoe_by_material_type(session, order_shoe_id: int, material_type_id: Optional[int]):
    """按材料类型路由到“订单鞋”的一次/二次采购单；若多张，取 issue_date 最新。"""
    po_type = FIRST_PO_TYPE if material_type_id in FIRST_PURCHASE_MTIDS else SECOND_PO_TYPE
    return (
        session.query(PurchaseOrder)
        .filter(
            PurchaseOrder.order_shoe_id == order_shoe_id,
            PurchaseOrder.purchase_order_type == po_type,
            or_(
                PurchaseOrder.purchase_order_status == None,
                PurchaseOrder.purchase_order_status.in_(ACTIVE_PO_STATUSES),
            ),
        )
        .order_by(
            desc(PurchaseOrder.purchase_order_issue_date),
            desc(PurchaseOrder.purchase_order_id),
        )
        .first()
    )


def _find_or_create_purchase_divide_order(session, po, supplier_id, divide_type, dry_run):
    """按“PO_RID-供应商后四位”查/建拆分单，并设置类型 S/N。"""
    rid = _compose_divide_rid(po.purchase_order_rid, supplier_id)
    pdo = (
        session.query(PurchaseDivideOrder)
        .filter(
            PurchaseDivideOrder.purchase_order_id == po.purchase_order_id,
            PurchaseDivideOrder.purchase_divide_order_rid == rid,
        )
        .first()
    )
    if pdo:
        return pdo
    pdo = PurchaseDivideOrder(
        purchase_order_id=po.purchase_order_id,
        purchase_divide_order_rid=rid,
        purchase_divide_order_type=divide_type,
    )
    logger.debug(f"{LOG_PREFIX} 新建 PurchaseDivideOrder: {rid} (type={divide_type}, PO={po.purchase_order_id})")
    if not dry_run:
        session.add(pdo)
        session.flush()
    return pdo


def _merge_duplicated_secondary(items: Iterable[BomItem]) -> List[Dict]:
    """
    二次BOM按 (material_id, model, spec, color) 合并（total_usage 与尺码累加，忽略 craft_name）。
    """
    bucket: Dict[Tuple, Dict] = {}
    for it in items:
        key = _tuple_key_from_vals(
            it.material_id, it.material_model, it.material_specification, it.bom_item_color
        )
        if key not in bucket:
            bucket[key] = {
                "material_id": it.material_id,
                "material_model": _norm_str(it.material_model) or None,
                "material_specification": _norm_str(it.material_specification) or None,
                "color": _norm_str(it.bom_item_color) or None,
                "unit_usage": _as_dec(it.unit_usage),      # 仅保留；不参与采购数量
                "total_usage": _as_dec(it.total_usage),    # ★ 采购数量取这个（核定用量）
                "department_id": it.department_id,
                "bom_item_add_type": it.bom_item_add_type or "0",
                "remark": _norm_str(it.remark) or None,
                "size_type": _norm_str(it.size_type) or "E",
                "material_second_type": _norm_str(it.material_second_type) or None,
                "pairs": it.pairs,
                "production_instruction_item_id": it.production_instruction_item_id,
                "sizes": {f: _as_int(getattr(it, f)) or 0 for f in SIZE_FIELDS},
            }
        else:
            b = bucket[key]
            b["total_usage"] += _as_dec(it.total_usage)
            for f in SIZE_FIELDS:
                b["sizes"][f] += _as_int(getattr(it, f)) or 0
    return list(bucket.values())


def _purchase_group_key(
    order_shoe_id,
    po_type,
    supplier_id,
    divide_type,
    material_id,
    model,
    spec,
    color,
):
    """采购聚合键：同一个 order_shoe + 采购类型 + 供应商 + 拆分类型 + 材料四件套；忽略 size_type 与 craft_name。"""
    return (
        order_shoe_id,
        po_type,
        supplier_id if supplier_id is not None else None,
        divide_type,
        material_id if material_id is not None else None,
        _norm_str(model),
        _norm_str(spec),
        _norm_str(color),
    )


def _ceil_to_int(d: Decimal) -> Decimal:
    """
    把 Decimal 向上取整到最近的整数，例如：
      10.0 -> 10
      10.1 -> 11
      10.00001 -> 11
    """
    if d is None:
        return Decimal("0")
    if not isinstance(d, Decimal):
        d = Decimal(str(d))
    if d == d.to_integral_value():
        return d
    return d.to_integral_value(rounding=ROUND_CEILING)


# =========================
# 步骤 1：二次 BOM 与工艺单对齐（只操作 status=3 的二次 BOM）
# =========================
def sync_secondary_bom_with_craft_sheet(
    session,
    *,
    dry_run: bool = True,
    ost_ids: Optional[List[int]] = None,
    limit: Optional[int] = None,
) -> int:
    """
    先把“二次 BOM” 与工艺单对齐，补齐缺失材料：
      - 只处理 bom_type=1 且 bom_status='3' 的 BOM
      - 比对 key = (material_id, material_model, material_specification, color)
        （NULL 与 '' 视为相同）
      - 对于在 craft_sheet_item 中存在但在 bom_item(bom_item_add_type='1') 里不存在的材料，
        在对应二次 BOM 下新增 BomItem：
            * unit_usage / total_usage 直接取 CraftSheetItem 的字段
            * bom_item_add_type 固定为 '1'
            * 颜色取 CraftSheetItem.color
            * size_type 固定为 'E'
    返回：新增的二次 BOM item 条数
    """
    logger.debug(f"{LOG_PREFIX} sync_secondary_bom_with_craft_sheet start, dry_run={dry_run}")

    # 找出有二次 BOM 且状态为 3 的 order_shoe_type_id
    q = session.query(Bom.order_shoe_type_id).filter(
        Bom.bom_type == 1,
        Bom.bom_status == "3",
    )
    if ost_ids:
        q = q.filter(Bom.order_shoe_type_id.in_(ost_ids))

    q = q.group_by(Bom.order_shoe_type_id).order_by(Bom.order_shoe_type_id)
    if limit:
        q = q.limit(limit)

    target_ost_ids = [row[0] for row in q.all()]
    logger.debug(f"{LOG_PREFIX} secondary BOM to fix (status=3): {target_ost_ids}")

    total_new_secondary_items = 0

    for ost_id in target_ost_ids:
        # 取该 ost_id 最新的一张二次 BOM（状态为 3）
        secondary_bom = (
            session.query(Bom)
            .filter(
                Bom.order_shoe_type_id == ost_id,
                Bom.bom_type == 1,
                Bom.bom_status == "3",
            )
            .order_by(desc(Bom.bom_id))
            .first()
        )
        if not secondary_bom:
            continue

        # 当前二次 BOM 已有的 bom_item（只看 bom_item_add_type='1'）
        existing_items = (
            session.query(BomItem)
            .filter(
                BomItem.bom_id == secondary_bom.bom_id,
                BomItem.bom_item_add_type == "1",
            )
            .all()
        )
        existing_keys = {
            _tuple_key_from_vals(
                it.material_id,
                it.material_model,
                it.material_specification,
                it.bom_item_color,
            )
            for it in existing_items
        }

        # 该 ost 对应的所有 craft_sheet_item
        craft_items = (
            session.query(CraftSheetItem)
            .filter(CraftSheetItem.order_shoe_type_id == ost_id)
            .all()
        )
        if not craft_items:
            continue

        logger.debug(
            f"{LOG_PREFIX} ost_id={ost_id}: secondary BOM {secondary_bom.bom_id}, "
            f"existing secondary items={len(existing_items)}, craft items={len(craft_items)}"
        )

        for ci in craft_items:
            key = _tuple_key_from_vals(
                ci.material_id,
                ci.material_model,
                ci.material_specification,
                ci.color,
            )
            if key in existing_keys:
                continue  # 该材料已在二次 BOM 中存在（按四件套）

            # 按 CraftSheetItem 补一条二次 BOM 记录
            new_bi = BomItem(
                bom_id=secondary_bom.bom_id,
                material_id=ci.material_id,
                material_specification=ci.material_specification,
                material_model=ci.material_model,
                # 用工艺单的 unit_usage / total_usage
                unit_usage=_as_dec(ci.unit_usage, scale=5),
                total_usage=_as_dec(ci.total_usage, scale=5),
                department_id=ci.department_id,
                bom_item_add_type="1",  # 追加类型
                remark=ci.remark,
                bom_item_color=ci.color,
                size_type="E",  # 没有 size_type，按系统默认 'E'
                material_second_type=ci.material_second_type,
                craft_name=ci.craft_name,
                pairs=ci.pairs,
                production_instruction_item_id=ci.production_instruction_item_id,
            )
            if not dry_run:
                session.add(new_bi)

            existing_keys.add(key)
            total_new_secondary_items += 1

        if not dry_run:
            session.flush()

    if not dry_run and total_new_secondary_items:
        session.commit()

    logger.debug(
        f"{LOG_PREFIX} sync_secondary_bom_with_craft_sheet done, "
        f"new secondary bom_items={total_new_secondary_items}, dry_run={dry_run}"
    )
    return total_new_secondary_items


# =========================
# 步骤 2：二次 → 一次 BOM + 采购聚合（原有逻辑）
# =========================
def sync_secondary_to_primary_bom(app, db, *, dry_run: bool = True, limit: Optional[int] = None):
    """
    同步二次→一次BOM，并聚合采购：
    - 新增一次BOM条目（不写 craft_name）
    - 采购按 (order_shoe, supplier, po_type, divide_type, material_id+model+spec+color) 聚合
    - 忽略 size_type 与 craft_name
    - 采购数量 = 核定用量 total_usage；各尺码数量累加
    - inbound_unit = Material.material_unit
    - 底材/烫底（7、16）PDO 类型 = 'S'，其余 'N'
    """
    with app.app_context():
        session = db.session
        logger.debug(f"{LOG_PREFIX} Start, dry_run={dry_run}")

        # 有二次/一次BOM的 ost
        second_boms = (
            session.query(Bom.order_shoe_type_id)
            .filter(Bom.bom_type == 1)
            .group_by(Bom.order_shoe_type_id)
            .subquery()
        )
        primary_boms = (
            session.query(Bom.order_shoe_type_id)
            .filter(Bom.bom_type == 0)
            .group_by(Bom.order_shoe_type_id)
            .subquery()
        )
        both = (
            session.query(second_boms.c.order_shoe_type_id)
            .join(
                primary_boms,
                primary_boms.c.order_shoe_type_id == second_boms.c.order_shoe_type_id,
            )
            .order_by(second_boms.c.order_shoe_type_id)
        )
        if limit:
            both = both.limit(limit)

        total_new_bom_items, total_new_po_items = 0, 0
        purchase_bucket: Dict[Tuple, Dict] = {}

        for (ost_id,) in both:
            # 选“最新版”的一次/二次 BOM（按 bom_id 最大）
            primary_bom = (
                session.query(Bom)
                .filter(Bom.order_shoe_type_id == ost_id, Bom.bom_type == 0)
                .order_by(desc(Bom.bom_id))
                .first()
            )
            secondary_bom = (
                session.query(Bom)
                .filter(Bom.order_shoe_type_id == ost_id, Bom.bom_type == 1)
                .order_by(desc(Bom.bom_id))
                .first()
            )
            if not primary_bom or not secondary_bom:
                continue

            p_items = (
                session.query(BomItem)
                .filter(BomItem.bom_id == primary_bom.bom_id)
                .all()
            )
            s_items = (
                session.query(BomItem)
                .filter(BomItem.bom_id == secondary_bom.bom_id)
                .all()
            )

            existing_keys = {
                _tuple_key_from_vals(
                    i.material_id,
                    i.material_model,
                    i.material_specification,
                    i.bom_item_color,
                )
                for i in p_items
            }
            merged = _merge_duplicated_secondary(s_items)
            to_add = [
                d
                for d in merged
                if _tuple_key_from_vals(
                    d["material_id"],
                    d["material_model"],
                    d["material_specification"],
                    d["color"],
                )
                not in existing_keys
            ]
            if not to_add:
                continue

            ost = session.get(OrderShoeType, ost_id)

            # 批量取 Material 信息（supplier、type、unit）
            material_ids = [d["material_id"] for d in to_add if d["material_id"]]
            mat_info_map: Dict[int, Tuple[Optional[int], Optional[int], Optional[str]]] = {}
            if material_ids:
                rows = (
                    session.query(
                        Material.material_id,
                        Material.material_supplier,
                        Material.material_type_id,
                        Material.material_unit,
                    )
                    .filter(Material.material_id.in_(material_ids))
                    .all()
                )
                mat_info_map = {
                    mid: (sid, mtid, unit) for mid, sid, mtid, unit in rows
                }

            # ===== 写一次BOM & 收集采购聚合 =====
            for d in to_add:
                # 1) 新增一次BOM条目 —— 不写 craft_name
                new_primary = BomItem(
                    bom_id=primary_bom.bom_id,
                    material_id=d["material_id"],
                    material_specification=d["material_specification"],
                    material_model=d["material_model"],
                    unit_usage=d["unit_usage"],          # 仅保留；不会用于采购量
                    total_usage=d["total_usage"],        # 采购量依据（核定用量）
                    department_id=d["department_id"],
                    bom_item_add_type=d["bom_item_add_type"],
                    remark=d["remark"],
                    bom_item_color=d["color"],
                    size_type=d["size_type"],
                    material_second_type=d["material_second_type"],
                    craft_name=None,                     # 强制不写 craft_name
                    pairs=d["pairs"],
                    production_instruction_item_id=d["production_instruction_item_id"],
                )
                for f, v in d["sizes"].items():
                    setattr(new_primary, f, v)

                if not dry_run:
                    session.add(new_primary)
                    session.flush()  # 获取 bom_item_id

                total_new_bom_items += 1

                # 2) 采购聚合（忽略 size_type 与 craft_name）
                if ost:
                    supplier_id, type_id, unit = mat_info_map.get(
                        d["material_id"], (None, None, None)
                    )
                    po_type = (
                        FIRST_PO_TYPE
                        if type_id in FIRST_PURCHASE_MTIDS
                        else SECOND_PO_TYPE
                    )
                    divide_type = _divide_order_type_for_material_type(type_id)

                    pkey = _purchase_group_key(
                        ost.order_shoe_id,
                        po_type,
                        supplier_id,
                        divide_type,
                        d["material_id"],
                        d["material_model"],
                        d["material_specification"],
                        d["color"],
                    )
                    if pkey not in purchase_bucket:
                        purchase_bucket[pkey] = {
                            "purchase_amount": Decimal("0"),
                            "sizes": {sf: 0 for sf in SIZE_FIELDS},
                            "inbound_unit": unit,
                            "any_bom_item_id": (
                                None if dry_run else new_primary.bom_item_id
                            ),
                            "order_shoe_id": ost.order_shoe_id,
                            "material_id": d["material_id"],
                            "material_model": d["material_model"],
                            "material_specification": d["material_specification"],
                            "color": d["color"],
                            "remark": d["remark"],
                            "supplier_id": supplier_id,
                            "material_type_id": type_id,
                        }
                    acc = purchase_bucket[pkey]
                    acc["purchase_amount"] += d["total_usage"]  # 汇总核定用量
                    for sf in SIZE_FIELDS:
                        acc["sizes"][sf] += int(d["sizes"].get(sf) or 0)
                    if not acc["inbound_unit"] and unit:
                        acc["inbound_unit"] = unit
                    if not dry_run and not acc["any_bom_item_id"]:
                        acc["any_bom_item_id"] = new_primary.bom_item_id

            if not dry_run:
                session.flush()

        # ===== 统一落库聚合后的采购条目 =====
        logger.debug(
            f"{LOG_PREFIX} 开始写入聚合后的采购条目，共 {len(purchase_bucket)} 组"
        )
        for pkey, val in purchase_bucket.items():
            (
                order_shoe_id,
                po_type,
                supplier_id,
                divide_type,
                material_id,
                model,
                spec,
                color,
            ) = pkey

            # 寻找该 order_shoe + 采购类型 的采购单
            target_po = (
                session.query(PurchaseOrder)
                .filter(
                    PurchaseOrder.order_shoe_id == order_shoe_id,
                    PurchaseOrder.purchase_order_type == po_type,
                    or_(
                        PurchaseOrder.purchase_order_status == None,
                        PurchaseOrder.purchase_order_status.in_(ACTIVE_PO_STATUSES),
                    ),
                )
                .order_by(
                    desc(PurchaseOrder.purchase_order_issue_date),
                    desc(PurchaseOrder.purchase_order_id),
                )
                .first()
            )
            if not target_po:
                logger.debug(
                    f"{LOG_PREFIX} 跳过：未找到匹配采购单 order_shoe_id={order_shoe_id}, type={po_type}"
                )
                continue

            # 找/建拆分单
            pdo = _find_or_create_purchase_divide_order(
                session, target_po, supplier_id, divide_type, dry_run
            )

            # === 先看该拆分单里是否已有同名材料 ===
            existing_poi = (
                session.query(PurchaseOrderItem)
                .filter(
                    PurchaseOrderItem.purchase_divide_order_id == pdo.purchase_divide_order_id,
                    PurchaseOrderItem.inbound_material_id == material_id,
                    func.coalesce(PurchaseOrderItem.material_model, "") == _norm_str(model),
                    func.coalesce(PurchaseOrderItem.material_specification, "") == _norm_str(spec),
                    func.coalesce(PurchaseOrderItem.color, "") == _norm_str(color),
                )
                .first()
            )

            if existing_poi:
            # ✅ 覆盖原数量，而不是累加
                existing_poi.purchase_amount = val["purchase_amount"]

                for sf, pf in SIZE_FIELD_TO_PO_FIELD.items():
                    new_size_val = val["sizes"].get(sf) or None
                    setattr(existing_poi, pf, new_size_val)

                if not dry_run:
                    session.add(existing_poi)
                logger.debug(
                    f"{LOG_PREFIX} merge PO item in PDO={pdo.purchase_divide_order_id}, "
                    f"material_id={material_id}, model='{model}', spec='{spec}', color='{color}'"
                )
            else:
                # 聚合后的采购条目（不写 craft_name；size_type 也不参与）
                po_item = PurchaseOrderItem(
                    bom_item_id=(None if dry_run else val["any_bom_item_id"]),
                    purchase_divide_order_id=(
                        None if dry_run else pdo.purchase_divide_order_id
                    ),
                    purchase_amount=val["purchase_amount"],   # 汇总后的核定用量
                    adjust_purchase_amount=Decimal("0"),
                    approval_amount=Decimal("0"),
                    inbound_material_id=material_id,
                    inbound_unit=val["inbound_unit"],
                    material_id=material_id,
                    material_specification=spec,
                    material_model=model,
                    color=color,
                    size_type="E",
                    craft_name=None,
                    remark=val["remark"],
                    related_selected_material_storage=[],
                )
                for sf, pf in SIZE_FIELD_TO_PO_FIELD.items():
                    setattr(po_item, pf, val["sizes"].get(sf) or None)

                if not dry_run:
                    session.add(po_item)
                    session.flush()
                total_new_po_items += 1

        if not dry_run:
            session.commit()

        logger.debug(
            f"{LOG_PREFIX} Done. 新增一次BOM项={total_new_bom_items}, 新采购条目(新建)={total_new_po_items}"
        )
        if dry_run:
            logger.debug(f"{LOG_PREFIX} （dry_run 模式未写入数据库）")


def sync_for_ost_ids(
    session, ost_ids: List[int], *, dry_run: bool = False
) -> Tuple[int, int]:
    """
    仅针对指定的 order_shoe_type_id 列表：
      - 比对二次/一次BOM，找出二次有而一次没有的材料（以 material_id+model+spec+color 判等；NULL/空等价）
      - 将缺失材料新增到一次BOM（不写 craft_name；忽略 size_type）
      - 将同一 order_shoe + 采购类型 + 供应商 + 拆分类型 + 材料四件套 聚合（核定用量 total_usage & 各尺码相加）
      - 仅在已存在对应 PurchaseOrder 时写入 PurchaseOrderItem
      - PurchaseDivideOrder：RID=PO_RID + 供应商ID后四位；material_type_id ∈ {7,16} 的类型=S，其余=N
      - 写采购条目时，如果拆分单里已有同名材料，改为累加数量而不是新增
    返回: (新增的一次BOM条数, 新增的采购明细条数)
    """
    if not ost_ids:
        return (0, 0)

    total_new_bom_items, total_new_po_items = 0, 0
    purchase_bucket: Dict[Tuple, Dict] = {}

    for ost_id in ost_ids:
        # 选“最新版”的一次/二次 BOM（按 bom_id 最大）
        primary_bom = (
            session.query(Bom)
            .filter(Bom.order_shoe_type_id == ost_id, Bom.bom_type == 0)
            .order_by(desc(Bom.bom_id))
            .first()
        )
        secondary_bom = (
            session.query(Bom)
            .filter(Bom.order_shoe_type_id == ost_id, Bom.bom_type == 1)
            .order_by(desc(Bom.bom_id))
            .first()
        )
        if not primary_bom or not secondary_bom:
            continue

        p_items = (
            session.query(BomItem)
            .filter(BomItem.bom_id == primary_bom.bom_id)
            .all()
        )
        s_items = (
            session.query(BomItem)
            .filter(BomItem.bom_id == secondary_bom.bom_id)
            .all()
        )

        existing_keys = {
            _tuple_key_from_vals(
                i.material_id,
                i.material_model,
                i.material_specification,
                i.bom_item_color,
            )
            for i in p_items
        }
        merged = _merge_duplicated_secondary(s_items)
        to_add = [
            d
            for d in merged
            if _tuple_key_from_vals(
                d["material_id"],
                d["material_model"],
                d["material_specification"],
                d["color"],
            )
            not in existing_keys
        ]
        if not to_add:
            continue

        ost = session.get(OrderShoeType, ost_id)

        # 批量取 Material 信息（supplier、type、unit）
        material_ids = [d["material_id"] for d in to_add if d["material_id"]]
        mat_info_map: Dict[int, Tuple[Optional[int], Optional[int], Optional[str]]] = {}
        if material_ids:
            rows = (
                session.query(
                    Material.material_id,
                    Material.material_supplier,
                    Material.material_type_id,
                    Material.material_unit,
                )
                .filter(Material.material_id.in_(material_ids))
                .all()
            )
            mat_info_map = {
                mid: (sid, mtid, unit) for mid, sid, mtid, unit in rows
            }

        # ===== 写一次BOM & 收集采购聚合 =====
        for d in to_add:
            # 1) 新增一次BOM条目 —— 不写 craft_name
            new_primary = BomItem(
                bom_id=primary_bom.bom_id,
                material_id=d["material_id"],
                material_specification=d["material_specification"],
                material_model=d["material_model"],
                unit_usage=d["unit_usage"],
                total_usage=d["total_usage"],
                department_id=d["department_id"],
                bom_item_add_type=d["bom_item_add_type"],
                remark=d["remark"],
                bom_item_color=d["color"],
                size_type=d["size_type"],
                material_second_type=d["material_second_type"],
                craft_name=None,
                pairs=d["pairs"],
                production_instruction_item_id=d["production_instruction_item_id"],
            )
            for f, v in d["sizes"].items():
                setattr(new_primary, f, v)

            if not dry_run:
                session.add(new_primary)
                session.flush()  # 需要 bom_item_id

            total_new_bom_items += 1

            # 2) 采购聚合（忽略 size_type 与 craft_name）
            if ost:
                supplier_id, type_id, unit = mat_info_map.get(
                    d["material_id"], (None, None, None)
                )
                po_type = (
                    FIRST_PO_TYPE
                    if type_id in FIRST_PURCHASE_MTIDS
                    else SECOND_PO_TYPE
                )
                divide_type = _divide_order_type_for_material_type(type_id)

                pkey = _purchase_group_key(
                    ost.order_shoe_id,
                    po_type,
                    supplier_id,
                    divide_type,
                    d["material_id"],
                    d["material_model"],
                    d["material_specification"],
                    d["color"],
                )
                if pkey not in purchase_bucket:
                    purchase_bucket[pkey] = {
                        "purchase_amount": Decimal("0"),
                        "sizes": {sf: 0 for sf in SIZE_FIELDS},
                        "inbound_unit": unit,
                        "any_bom_item_id": (
                            None if dry_run else new_primary.bom_item_id
                        ),
                        "order_shoe_id": ost.order_shoe_id,
                        "material_id": d["material_id"],
                        "material_model": d["material_model"],
                        "material_specification": d["material_specification"],
                        "color": d["color"],
                        "remark": d["remark"],
                        "supplier_id": supplier_id,
                        "material_type_id": type_id,
                    }
                acc = purchase_bucket[pkey]
                acc["purchase_amount"] += d["total_usage"]
                for sf in SIZE_FIELDS:
                    acc["sizes"][sf] += int(d["sizes"].get(sf) or 0)
                if not acc["inbound_unit"] and unit:
                    acc["inbound_unit"] = unit
                if not dry_run and not acc["any_bom_item_id"]:
                    acc["any_bom_item_id"] = new_primary.bom_item_id

        if not dry_run:
            session.flush()

    # ===== 统一落库聚合后的采购条目（仅写入“已存在”的采购单）=====
    for pkey, val in purchase_bucket.items():
        (
            order_shoe_id,
            po_type,
            supplier_id,
            divide_type,
            material_id,
            model,
            spec,
            color,
        ) = pkey
        target_po = (
            session.query(PurchaseOrder)
            .filter(
                PurchaseOrder.order_shoe_id == order_shoe_id,
                PurchaseOrder.purchase_order_type == po_type,
                or_(
                    PurchaseOrder.purchase_order_status == None,
                    PurchaseOrder.purchase_order_status.in_(ACTIVE_PO_STATUSES),
                ),
            )
            .order_by(
                desc(PurchaseOrder.purchase_order_issue_date),
                desc(PurchaseOrder.purchase_order_id),
            )
            .first()
        )
        if not target_po:
            # 找不到采购单就跳过
            continue

        pdo = _find_or_create_purchase_divide_order(
            session,
            target_po,
            supplier_id,
            _divide_order_type_for_material_type(val["material_type_id"]),
            dry_run,
        )

        # === 先看该拆分单里是否已有同名材料 ===
        existing_poi = (
            session.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_divide_order_id == pdo.purchase_divide_order_id,
                PurchaseOrderItem.inbound_material_id == material_id,
                func.coalesce(PurchaseOrderItem.material_model, "") == _norm_str(model),
                func.coalesce(PurchaseOrderItem.material_specification, "") == _norm_str(spec),
                func.coalesce(PurchaseOrderItem.color, "") == _norm_str(color),
            )
            .first()
        )

        if existing_poi:
            existing_poi.purchase_amount = val["purchase_amount"]
            for sf, pf in SIZE_FIELD_TO_PO_FIELD.items():
                new_size_val = val["sizes"].get(sf) or None
                setattr(existing_poi, pf, new_size_val)

            if not dry_run:
                session.add(existing_poi)
        else:
            po_item = PurchaseOrderItem(
                bom_item_id=(None if dry_run else val["any_bom_item_id"]),
                purchase_divide_order_id=(
                    None if dry_run else pdo.purchase_divide_order_id
                ),
                purchase_amount=val["purchase_amount"],
                adjust_purchase_amount=Decimal("0"),
                approval_amount=Decimal("0"),
                inbound_material_id=material_id,
                inbound_unit=val["inbound_unit"],
                material_id=material_id,
                material_specification=spec,
                material_model=model,
                color=color,
                size_type="E",
                craft_name=None,
                remark=val["remark"],
                related_selected_material_storage=[],
            )
            for sf, pf in SIZE_FIELD_TO_PO_FIELD.items():
                setattr(po_item, pf, val["sizes"].get(sf) or None)

            if not dry_run:
                session.add(po_item)
                session.flush()
            total_new_po_items += 1

    return (total_new_bom_items, total_new_po_items)



# =========================
# 步骤 3：采购条目尾处理（只修 purchase_amount=0 & approval_amount=0）
# =========================
def fix_zero_purchase_items_from_bom(
    session, *, dry_run: bool = False, limit: Optional[int] = None
) -> int:
    """
    针对 purchase_order_item 中 purchase_amount=0 且 approval_amount=0 的条目：
      - 用 bom_item_id 找到 BomItem -> Bom -> OrderShoeType -> OrderShoe -> Order
      - 订单下所有 BOM 中 “相同材料(material_id+model+spec+color)” 的 total_usage 之和
        作为该采购明细的 approval_amount
      - 当前 BomItem 的 total_usage 作为采购量来源：
        如果是小数，则 purchase_amount 向上取整为最近整数
    返回：成功更新的 POI 条数
    """
    logger.debug(
        f"{LOG_PREFIX} fix_zero_purchase_items_from_bom start, dry_run={dry_run}"
    )

    q = (
        session.query(PurchaseOrderItem)
        .filter(
            PurchaseOrderItem.purchase_amount == 0,
            PurchaseOrderItem.approval_amount == 0,
            PurchaseOrderItem.bom_item_id != None,
        )
        .order_by(PurchaseOrderItem.purchase_order_item_id)
    )

    if limit:
        q = q.limit(limit)

    updated = 0

    for poi in q:
        bom_item = session.get(BomItem, poi.bom_item_id)
        if not bom_item or not bom_item.bom_id:
            continue

        bom = session.get(Bom, bom_item.bom_id)
        if not bom or not bom.order_shoe_type_id:
            continue

        ost = session.get(OrderShoeType, bom.order_shoe_type_id)
        if not ost or not ost.order_shoe_id:
            continue

        order_shoe = (
            session.query(OrderShoe)
            .filter_by(order_shoe_id=ost.order_shoe_id)
            .first()
        )
        if not order_shoe or not order_shoe.order_id:
            continue

        order_id = order_shoe.order_id

        # 该订单下所有 order_shoe_type_id
        ost_ids_subq = (
            session.query(OrderShoeType.order_shoe_type_id)
            .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .filter(OrderShoe.order_id == order_id)
            .subquery()
        )

        # 订单所有 BOM 中相同材料（四件套）的 total_usage 之和
        total_usage_sum = (
            session.query(func.coalesce(func.sum(BomItem.total_usage), 0))
            .join(Bom, BomItem.bom_id == Bom.bom_id)
            .join(
                ost_ids_subq,
                Bom.order_shoe_type_id == ost_ids_subq.c.order_shoe_type_id,
            )
            .filter(
                BomItem.material_id == bom_item.material_id,
                func.coalesce(BomItem.material_model, "") ==
                func.coalesce(bom_item.material_model, ""),
                func.coalesce(BomItem.material_specification, "") ==
                func.coalesce(bom_item.material_specification, ""),
                func.coalesce(BomItem.bom_item_color, "") ==
                func.coalesce(bom_item.bom_item_color, ""),
            )
            .scalar()
        )

        total_usage_sum = _as_dec(total_usage_sum or 0, scale=5)
        current_usage = _as_dec(bom_item.total_usage or 0, scale=5)
        purchase_amount = _ceil_to_int(current_usage)

        poi.approval_amount = total_usage_sum
        poi.purchase_amount = purchase_amount

        if not dry_run:
            session.add(poi)

        updated += 1

    if not dry_run and updated:
        session.flush()
        session.commit()

    logger.debug(
        f"{LOG_PREFIX} fix_zero_purchase_items_from_bom done, updated={updated}, dry_run={dry_run}"
    )
    return updated

def run_full_sync_pipeline(app, db, *, dry_run: bool = False, limit: Optional[int] = None):
    """
    一次性执行完整流程：
      1. 同步工艺单 → 补齐 status=3 的二次 BOM 缺失材料
      2. 同步二次 → 一次 BOM 并生成采购单
      3. 修复 purchase_amount / approval_amount 为 0 的采购明细

    参数：
        app        Flask 应用对象（用于 app_context）
        db         SQLAlchemy 实例
        dry_run    True = 仅打印日志不写库
        limit      限制处理的 ost 数量（可选）

    返回：
        dict，总结信息，例如：
        {
            "added_secondary_bom_items": 12,
            "added_primary_bom_items": 8,
            "added_purchase_items": 8,
            "fixed_purchase_items": 5
        }
    """

    results = {
        "added_secondary_bom_items": 0,
        "added_primary_bom_items": 0,
        "added_purchase_items": 0,
        "fixed_purchase_items": 0,
    }

    with app.app_context():
        session = db.session

        logger.info("=" * 80)
        logger.info(f"{LOG_PREFIX} 🚀 开始执行完整BOM同步流程 dry_run={dry_run}")
        logger.info("=" * 80)

        # Step 1: 工艺单 → 二次BOM
        logger.info(f"{LOG_PREFIX} [STEP 1] 补齐二次BOM缺失材料（按工艺单对齐）")
        added_secondary = sync_secondary_bom_with_craft_sheet(
            session, dry_run=dry_run, limit=limit
        )
        results["added_secondary_bom_items"] = added_secondary
        logger.info(f"{LOG_PREFIX} 补齐二次BOM材料完成，新增 {added_secondary} 条")

        # Step 2: 二次 → 一次BOM + 采购单
        logger.info(f"{LOG_PREFIX} [STEP 2] 同步二次→一次BOM并聚合采购")
        sync_secondary_to_primary_bom(app, db, dry_run=dry_run, limit=limit)
        # 因 sync_secondary_to_primary_bom 内部已经有计数器输出，这里可不重复统计
        logger.info(f"{LOG_PREFIX} 二次→一次BOM同步完成")

        # Step 3: 修复采购明细的 0 值
        logger.info(f"{LOG_PREFIX} [STEP 3] 修复采购明细 purchase_amount / approval_amount = 0 的条目")
        fixed_count = fix_zero_purchase_items_from_bom(session, dry_run=dry_run)
        results["fixed_purchase_items"] = fixed_count
        logger.info(f"{LOG_PREFIX} 修复采购条目完成，共 {fixed_count} 条")

        logger.info("=" * 80)
        logger.info(
            f"{LOG_PREFIX} ✅ 全流程执行完成 (dry_run={dry_run})\n"
            f"  二次BOM补齐: {results['added_secondary_bom_items']} 条\n"
            f"  修复采购条目: {results['fixed_purchase_items']} 条"
        )
        logger.info("=" * 80)

        return results

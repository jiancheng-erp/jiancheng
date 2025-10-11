# scripts/sync_bom_secondary_to_primary.py
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Tuple
from sqlalchemy import func, or_, desc
from models import (
    Bom,
    BomItem,
    PurchaseOrder,
    PurchaseDivideOrder,
    PurchaseOrderItem,
    OrderShoeType,
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
    "size_43_total_usage", "size_44_total_usage", "size_45_total_usage", "size_46_total_usage"
]

# 尺码字段映射到采购条目字段
SIZE_FIELD_TO_PO_FIELD = {f: f.replace("total_usage", "purchase_amount") for f in SIZE_FIELDS}

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
    return (mid if mid is not None else None, _norm_str(model), _norm_str(spec), _norm_str(color))

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
            or_(PurchaseOrder.purchase_order_status == None,
                PurchaseOrder.purchase_order_status.in_(ACTIVE_PO_STATUSES)),
        )
        .order_by(desc(PurchaseOrder.purchase_order_issue_date), desc(PurchaseOrder.purchase_order_id))
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
        key = _tuple_key_from_vals(it.material_id, it.material_model, it.material_specification, it.bom_item_color)
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

def _purchase_group_key(order_shoe_id, po_type, supplier_id, divide_type, material_id, model, spec, color):
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

# =========================
# 主逻辑（带 with app.app_context）
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
        both = session.query(second_boms.c.order_shoe_type_id).join(
            primary_boms,
            primary_boms.c.order_shoe_type_id == second_boms.c.order_shoe_type_id,
        ).order_by(second_boms.c.order_shoe_type_id)
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

            p_items = session.query(BomItem).filter(BomItem.bom_id == primary_bom.bom_id).all()
            s_items = session.query(BomItem).filter(BomItem.bom_id == secondary_bom.bom_id).all()

            existing_keys = {
                _tuple_key_from_vals(i.material_id, i.material_model, i.material_specification, i.bom_item_color)
                for i in p_items
            }
            merged = _merge_duplicated_secondary(s_items)
            to_add = [
                d for d in merged
                if _tuple_key_from_vals(d["material_id"], d["material_model"], d["material_specification"], d["color"])
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
                mat_info_map = {mid: (sid, mtid, unit) for mid, sid, mtid, unit in rows}

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
                    supplier_id, type_id, unit = mat_info_map.get(d["material_id"], (None, None, None))
                    po_type = FIRST_PO_TYPE if type_id in FIRST_PURCHASE_MTIDS else SECOND_PO_TYPE
                    divide_type = _divide_order_type_for_material_type(type_id)

                    pkey = _purchase_group_key(
                        ost.order_shoe_id, po_type, supplier_id, divide_type,
                        d["material_id"], d["material_model"], d["material_specification"], d["color"]
                    )
                    if pkey not in purchase_bucket:
                        purchase_bucket[pkey] = {
                            "purchase_amount": Decimal("0"),
                            "sizes": {sf: 0 for sf in SIZE_FIELDS},
                            "inbound_unit": unit,
                            "any_bom_item_id": (None if dry_run else new_primary.bom_item_id),
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
        logger.debug(f"{LOG_PREFIX} 开始写入聚合后的采购条目，共 {len(purchase_bucket)} 组")
        for pkey, val in purchase_bucket.items():
            order_shoe_id, po_type, supplier_id, divide_type, material_id, model, spec, color = pkey

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
                .order_by(desc(PurchaseOrder.purchase_order_issue_date), desc(PurchaseOrder.purchase_order_id))
                .first()
            )
            if not target_po:
                logger.debug(f"{LOG_PREFIX} 跳过：未找到匹配采购单 order_shoe_id={order_shoe_id}, type={po_type}")
                continue

            # 找/建拆分单
            pdo = _find_or_create_purchase_divide_order(
                session, target_po, supplier_id, divide_type, dry_run
            )

            # 聚合后的采购条目（不写 craft_name；size_type 也不参与）
            po_item = PurchaseOrderItem(
                bom_item_id=(None if dry_run else val["any_bom_item_id"]),
                purchase_divide_order_id=(None if dry_run else pdo.purchase_divide_order_id),

                purchase_amount=val["purchase_amount"],   # 汇总后的核定用量
                adjust_purchase_amount=Decimal("0"),
                approval_amount=Decimal("0"),

                inbound_material_id=material_id,
                inbound_unit=val["inbound_unit"],

                material_id=material_id,
                material_specification=spec,
                material_model=model,
                color=color,
                size_type='E',
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

        logger.debug(f"{LOG_PREFIX} Done. 新增一次BOM项={total_new_bom_items}, 新采购条目={total_new_po_items}")
        if dry_run:
            logger.debug(f"{LOG_PREFIX} （dry_run 模式未写入数据库）")
            
            
def sync_for_ost_ids(session, ost_ids: List[int], *, dry_run: bool = False) -> Tuple[int, int]:
    """
    仅针对指定的 order_shoe_type_id 列表：
      - 比对二次/一次BOM，找出二次有而一次没有的材料（以 material_id+model+spec+color 判等；NULL/空等价）
      - 将缺失材料新增到一次BOM（不写 craft_name；忽略 size_type）
      - 将同一 order_shoe + 采购类型 + 供应商 + 拆分类型 + 材料四件套 聚合（核定用量 total_usage & 各尺码相加）
      - 仅在已存在对应 PurchaseOrder 时写入 PurchaseOrderItem
      - PurchaseDivideOrder：RID=PO_RID + 供应商ID后四位；material_type_id ∈ {7,16} 的类型=S，其余=N
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

        p_items = session.query(BomItem).filter(BomItem.bom_id == primary_bom.bom_id).all()
        s_items = session.query(BomItem).filter(BomItem.bom_id == secondary_bom.bom_id).all()

        existing_keys = {
            _tuple_key_from_vals(i.material_id, i.material_model, i.material_specification, i.bom_item_color)
            for i in p_items
        }
        merged = _merge_duplicated_secondary(s_items)
        to_add = [
            d for d in merged
            if _tuple_key_from_vals(d["material_id"], d["material_model"], d["material_specification"], d["color"])
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
            mat_info_map = {mid: (sid, mtid, unit) for mid, sid, mtid, unit in rows}

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
                supplier_id, type_id, unit = mat_info_map.get(d["material_id"], (None, None, None))
                po_type = FIRST_PO_TYPE if type_id in FIRST_PURCHASE_MTIDS else SECOND_PO_TYPE
                divide_type = _divide_order_type_for_material_type(type_id)

                pkey = _purchase_group_key(
                    ost.order_shoe_id, po_type, supplier_id, divide_type,
                    d["material_id"], d["material_model"], d["material_specification"], d["color"]
                )
                if pkey not in purchase_bucket:
                    purchase_bucket[pkey] = {
                        "purchase_amount": Decimal("0"),
                        "sizes": {sf: 0 for sf in SIZE_FIELDS},
                        "inbound_unit": unit,
                        "any_bom_item_id": (None if dry_run else new_primary.bom_item_id),
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
        order_shoe_id, po_type, supplier_id, divide_type, material_id, model, spec, color = pkey
        target_po = (
            session.query(PurchaseOrder)
            .filter(
                PurchaseOrder.order_shoe_id == order_shoe_id,
                PurchaseOrder.purchase_order_type == po_type,
                or_(PurchaseOrder.purchase_order_status == None,
                    PurchaseOrder.purchase_order_status.in_(ACTIVE_PO_STATUSES)),
            )
            .order_by(desc(PurchaseOrder.purchase_order_issue_date), desc(PurchaseOrder.purchase_order_id))
            .first()
        )
        if not target_po:
            # 找不到采购单就跳过
            continue

        pdo = _find_or_create_purchase_divide_order(
            session, target_po, supplier_id, _divide_order_type_for_material_type(val["material_type_id"]), dry_run
        )

        po_item = PurchaseOrderItem(
            bom_item_id=(None if dry_run else val["any_bom_item_id"]),
            purchase_divide_order_id=(None if dry_run else pdo.purchase_divide_order_id),

            purchase_amount=val["purchase_amount"],
            adjust_purchase_amount=Decimal("0"),
            approval_amount=Decimal("0"),

            inbound_material_id=material_id,
            inbound_unit=val["inbound_unit"],

            material_id=material_id,
            material_specification=spec,
            material_model=model,
            color=color,
            size_type='E',
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


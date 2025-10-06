# missing_material_purchase_api.py
from flask import Blueprint, jsonify, request
from sqlalchemy import func, case, desc, asc
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from api_utility import randomIdGenerater
from models import (
    Material,
    db,
    Order,
    OrderStatus,
    OrderStatusReference,
    OrderShoe,
    OrderShoeStatus,
    Customer,
    Shoe,
    ShoeType,
    Color,
    OrderShoeType,
    WarehouseMissingPurchaseRecord as WMR,
    WarehouseMissingPurchaseRecordItem as WMRItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    PurchaseDivideOrder,
    BomItem,
    Bom,
)

missing_material_purchase_bp = Blueprint("missing_material_purchase_api", __name__)

# 你模型里是 String(1) 存 0/1/2，因此这里统一用数字字符串
ACTIVE_STATUSES = ["0", "1", "2"]  # 0-已提交, 1-审批中, 2-执行中
SIZE_COLS = [34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46]
STATUS_STAGE_NUMERIC = {
    "0": "技术部已下发",
    "1": "核定用量已补充",
    "2": "采购用量填写完成",
}
PENDING_NODE_NUMERIC = {
    "0": "等待用量填写",
    "1": "等待采购填写",
    "2": "采购用量填写完成",
}
SIZE_BASED_TYPES = {'O': '大底', 'M': '中底', 'H': '烫底'}
MAT_TYPE_NAME = {
    'S':'面料','I':'里料','A':'辅料',
    'O':'大底','M':'中底','H':'烫底'
}

def _to_f4(x):
    if x is None: return 0.0
    try:
        return float(Decimal(x).quantize(Decimal('0.0001')))
    except Exception:
        return float(x)

def _fmt_time(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None

def _stage_text(status):
    # 按你的状态枚举返回中文
    return status or ''


def _sum_list(nums) -> Decimal:
    s = Decimal("0")
    for v in (nums or []):
        try:
            s += Decimal(str(v or 0))
        except Exception:
            pass
    return s

def _is_size_based(mt: str) -> bool:
    return mt in ("O", "M", "H")  # 大底/中底/烫底

def _to_float4(x):
    try:
        return round(float(x or 0), 4)
    except Exception:
        return 0.0
    
def fill_item_size_columns(poi: PurchaseOrderItem, arr: List[int]):
    arr = list(arr or [])
    if len(arr) < len(SIZE_COLS):
        arr += [0] * (len(SIZE_COLS) - len(arr))
    for idx, size in enumerate(SIZE_COLS):
        setattr(poi, f"size_{size}_purchase_amount", int(arr[idx] or 0))

def fill_bom_size_columns(bi: BomItem, arr: List[int]):
    arr = list(arr or [])
    if len(arr) < len(SIZE_COLS):
        arr += [0] * (len(SIZE_COLS) - len(arr))
    for idx, size in enumerate(SIZE_COLS):
        setattr(bi, f"size_{size}_total_usage", int(arr[idx] or 0))

# ---- 材料大类/物料类型推断：把“材料大类/数字类型” -> 单字符物料类型（你模型里是 String(1)） ----
# 说明：前端已不再显式传大类，这里优先从 items[].materialType（来自 getmaterialdetail）推断；
# 若缺失，再看 items[].category（旧字段）；都没有则默认 'A'
# 你可以按实际习惯修改映射。
def _convert_material_type(item: dict) -> str:
    # 1) 优先使用 getmaterialdetail 返回的 materialType（可能是 1/2/3/5/7/16）
    mt = item.get("materialType")
    if mt is not None:
        try:
            code = int(mt)
            # 根据你给的映射：1-面料/2-里料/3/5-辅料/7-大底/中底/16-烫底
            if code == 1:
                return "S"  # surface
            if code == 2:
                return "I"  # lining (Inner)
            if code in (3, 5):
                return "A"  # accessory
            if code == 7:
                return "O"  # outsole/midsole 二者同为 7，这里默认记为 O
            if code == 16:
                return "H"  # hotmelt
        except Exception:
            pass

    # 2) 兼容旧的字符串大类（surface/lining/accessory/outsole/midsole/hotmelt）
    cat = (item.get("category") or "").strip().lower()
    if cat:
        mapping = {
            "surface": "S",
            "lining": "I",
            "accessory": "A",
            "outsole": "O",
            "midsole": "M",
            "hotmelt": "H",
        }
        if cat in mapping:
            return mapping[cat]

    # 3) 兜底
    return "A"


# =========== 工具：聚合每个 order_shoe 是否出现过 status=8 和 15 ===========
def subq_order_shoe_flags(db, OrderShoeStatus):
    return (
        db.session.query(
            OrderShoeStatus.order_shoe_id.label("osh_id"),
            func.max(case((OrderShoeStatus.current_status == 8, 1), else_=0)).label("has8"),
            func.max(case((OrderShoeStatus.current_status == 15, 1), else_=0)).label("has15"),
        )
        .group_by(OrderShoeStatus.order_shoe_id)
        .subquery()
    )


# ================================= 1) 主表：已下发到总仓（可排除补采中） ================================
@missing_material_purchase_bp.route("/missing_material_purchase/getwarehouseorders", methods=["GET"])
def get_warehouse_orders():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 20, type=int)
    keyword = (request.args.get("keyword") or "").strip()
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    sort_prop = request.args.get("sortProp", "issueDate")
    sort_order = request.args.get("sortOrder", "desc")
    only_pending = request.args.get("onlyPending", 0, type=int)
    exclude_in_progress = request.args.get("excludeInProgress", 1, type=int)

    flags = subq_order_shoe_flags(db, OrderShoeStatus)

    # 已下发（同一 order_shoe 同时出现 8 和 15）
    q = (
        db.session.query(Order, OrderShoe, Customer, Shoe)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(flags, flags.c.osh_id == OrderShoe.order_shoe_id)
        .filter(flags.c.has8 == 1, flags.c.has15 == 1)
    )

    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (Order.order_rid.like(like))
            | (Customer.customer_name.like(like))
            | (Shoe.shoe_rid.like(like))
            | (OrderShoe.customer_product_name.like(like))
            | (Order.order_cid.like(like))
        )

    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            q = q.filter(Order.start_date >= sd)
        except Exception:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            q = q.filter(Order.start_date <= ed)
        except Exception:
            pass

    # 子查询：统计每个订单的“进行中补采记录”数量
    sub_inprog_cnt = (
        db.session.query(WMR.order_id.label("oid"), func.count(WMR.id).label("cnt"))
        .filter(WMR.status.in_(ACTIVE_STATUSES))
        .group_by(WMR.order_id)
        .subquery()
    )

    if only_pending == 1:
        q = q.join(sub_inprog_cnt, sub_inprog_cnt.c.oid == Order.order_id)

    if exclude_in_progress == 1:
        q = q.outerjoin(sub_inprog_cnt, sub_inprog_cnt.c.oid == Order.order_id).filter(
            (sub_inprog_cnt.c.cnt.is_(None)) | (sub_inprog_cnt.c.cnt == 0)
        )

    if sort_prop == "issueDate":
        q = q.order_by(desc(Order.start_date) if sort_order == "desc" else Order.start_date)
    else:
        q = q.order_by(desc(Order.order_id))

    total = q.distinct().count()
    rows = q.distinct().limit(page_size).offset((page - 1) * page_size).all()

    order_ids = list({r[0].order_id for r in rows})
    pending_map = {}
    if order_ids:
        pend_rows = (
            db.session.query(WMR.order_id, func.count(WMR.id))
            .filter(WMR.order_id.in_(order_ids), WMR.status.in_(ACTIVE_STATUSES))
            .group_by(WMR.order_id)
            .all()
        )
        pending_map = {oid: cnt for (oid, cnt) in pend_rows}

    def map_row(order, order_shoe, customer, shoe):
        return {
            "order_rid": order.order_rid,
            "customer_name": customer.customer_name,
            "customer_product_name": order_shoe.customer_product_name,
            "customer_brand": getattr(order, "customer_brand", None),
            "issue_date": order.start_date.isoformat() if order.start_date else None,
            "warehouse_status_text": "已下发",
            "warehouse_status_tag": "success",
            "pending_request_count": pending_map.get(order.order_id, 0),
            "order_id": order.order_id,
            "order_shoe_id": order_shoe.order_shoe_id,
            "order_shoe_type_id": getattr(order_shoe, "order_shoe_type_id", None),
        }

    return jsonify({"total": total, "list": [map_row(*r) for r in rows]})


# ========================== 2) 补采流程中订单 - 汇总数字 ==========================
@missing_material_purchase_bp.route("/missing_material_purchase/inprogress/summary", methods=["GET"])
def inprogress_summary():
    count = (
        db.session.query(WMR.order_id)
        .filter(WMR.status.in_(ACTIVE_STATUSES))
        .distinct()
        .count()
    )
    return jsonify({"count": count})


# =========================== 3) 补采流程中订单 - 列表 ===========================
@missing_material_purchase_bp.route("/missing_material_purchase/inprogress", methods=["GET"])
def inprogress_list():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 10, type=int)

    base = (
        db.session.query(
            WMR.id,
            WMR.order_id,
            WMR.status,
            WMR.created_at,
            Order.order_rid,
            Customer.customer_name,
        )
        .join(Order, Order.order_id == WMR.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .filter(WMR.status.in_(ACTIVE_STATUSES))
        .order_by(desc(WMR.created_at))
    )

    total = base.count()
    rows = base.limit(page_size).offset((page - 1) * page_size).all()

    def map_row(r):
        (rid, order_id, status, created_at, order_rid, cust_name) = r
        s = str(status) if status is not None else ""
        return {
            "id": rid,
            "order_id": order_id,
            "orderRid": order_rid,
            "customerName": cust_name,
            "stageText": STATUS_STAGE_NUMERIC.get(s, s),
            "pendingNodeText": PENDING_NODE_NUMERIC.get(s, "处理中"),
            "createdAt": created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else None,
        }

    return jsonify({"total": total, "list": [map_row(r) for r in rows]})


# =========================== 4) 新建补采请求（含明细） ===========================
@missing_material_purchase_bp.route("/missing_material_purchase/request", methods=["POST"])
def create_missing_purchase_request():
    data = request.get_json(force=True) or {}

    order_id = data.get("orderId")
    order_shoe_id = data.get("orderShoeId")
    order_shoe_type_id = data.get("orderShoeTypeId")
    reason = data.get("reason")
    remark = data.get("remark")
    items = data.get("items") or []

    if not order_id or not items:
        return jsonify({"success": False, "message": "orderId 与 items 不能为空"}), 400

    # 主记录：状态置 '0'（已提交）
    rec = WMR(
        order_id=order_id,
        order_shoe_id=order_shoe_id,
        status="0",
        reason=reason,
        remark=remark,
        created_at=datetime.now(),
    )
    db.session.add(rec)
    db.session.flush()  # 得到 rec.id

    # 明细：数量/单位前端未传，unit_usage/approval_usage/purchase_amount 先置空
    for it in items:
        item = WMRItem(
            record_id=rec.id,
            material_type=_convert_material_type(it),     # 必填字段，后端自动推断
            material_id=it.get("materialId"),
            material_model=it.get("model"),
            material_specification=it.get("spec"),
            color=(it.get("color") or None),
            unit_usage=None,          # 前端未传数量，先空
            approval_usage=None,      # 审批后回填
            purchase_amount=None,     # 计划采购后回填
            order_shoe_type_id=it.get("orderShoeTypeId") or order_shoe_type_id,
        )
        db.session.add(item)

    db.session.commit()
    return jsonify({"success": True, "id": rec.id})


# =========================== 5) 鞋型颜色（含 orderShoeTypeId） ===========================
@missing_material_purchase_bp.get("/missing_material_purchase/shoe_colors")
def get_shoe_colors():
    order_id = request.args.get("orderId", type=int)
    order_shoe_id = request.args.get("orderShoeId", type=int)
    if not order_shoe_id:
        return jsonify({"list": []})

    rows = (
        db.session.query(
            Color.color_name.label("name"),
            OrderShoeType.order_shoe_type_id.label("order_shoe_type_id"),
        )
        .join(ShoeType, ShoeType.color_id == Color.color_id)
        .join(OrderShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .filter(OrderShoeType.order_shoe_id == order_shoe_id)
        .order_by(Color.color_name.asc(), OrderShoeType.order_shoe_type_id.asc())
        .all()
    )

    out = []
    seen = set()
    for name, ost_id in rows:
        if not name or not ost_id:
            continue
        if ost_id in seen:
            continue
        seen.add(ost_id)
        out.append({"name": name, "orderShoeTypeId": int(ost_id), "id": int(ost_id)})

    return jsonify({"list": out})

@missing_material_purchase_bp.get("/missing_material_purchase/record_detail")
def get_missing_purchase_record_detail():
    rid = request.args.get("id", type=int)
    if not rid:
        return jsonify({"message": "id is required"}), 400

    # 取主记录 + 订单&客户信息
    rec = (
        db.session.query(
            WMR.id,
            WMR.order_id,
            WMR.order_shoe_id,
            WMR.status,
            WMR.reason,
            WMR.remark,
            WMR.created_at,
            Order.order_rid,
            Customer.customer_name,
        )
        .join(Order, Order.order_id == WMR.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .filter(WMR.id == rid)
        .first()
    )
    if not rec:
        return jsonify({"message": "record not found"}), 404

    (rid, order_id, order_shoe_id, status, reason, remark, created_at, order_rid, cust_name) = rec

    STATUS_STAGE = {
        "pending": "已提交",
        "approving": "审批中",
        "processing": "执行中",
        "approved": "已通过",
        "rejected": "已驳回",
        "canceled": "已撤销",
        "0": "已提交",  # 如果你用 0/1/2
        "1": "审批中",
        "2": "执行中",
    }

    # 取明细，顺带把颜色名 join 出来
    item_rows = (
        db.session.query(
            WMRItem.id,
            WMRItem.material_type,
            WMRItem.material_id,
            WMRItem.material_model,
            WMRItem.material_specification,
            WMRItem.color,
            WMRItem.unit_usage,
            WMRItem.approval_usage,
            WMRItem.purchase_amount,
            WMRItem.order_shoe_type_id,
            Color.color_name.label("shoe_color_name"),
            Material.material_name.label("material_name"),
        )
        .outerjoin(OrderShoeType, OrderShoeType.order_shoe_type_id == WMRItem.order_shoe_type_id)
        .outerjoin(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .outerjoin(Color, Color.color_id == ShoeType.color_id)
        .outerjoin(Material, Material.material_id == WMRItem.material_id)
        .filter(WMRItem.record_id == rid)
        .order_by(WMRItem.id.asc())
        .all()
    )

    TYPE_TEXT = {
        "S": "面料",
        "I": "里料",
        "A": "辅料",
        "O": "大底",
        "M": "中底",
        "H": "烫底",
        None: "",
        "": "",
    }

    def to_num(x):
        try:
            return float(x) if x is not None else None
        except Exception:
            return None

    items = []
    for (
        iid,
        mtype,
        mid,
        model,
        spec,
        color,
        unit_usage,
        approval_usage,
        purchase_amount,
        ost_id,
        shoe_color_name,
        material_name,
    ) in item_rows:
        items.append(
            {
                "id": int(iid),
                "materialType": mtype,
                "materialTypeText": TYPE_TEXT.get(mtype, mtype),
                "materialId": int(mid) if mid else None,
                "materialName": material_name,
                "materialModel": model,
                "materialSpecification": spec,
                "color": color,
                "unitUsage": to_num(unit_usage),
                "approvalUsage": to_num(approval_usage),
                "purchaseAmount": to_num(purchase_amount),
                "orderShoeTypeId": int(ost_id) if ost_id else None,
                "shoeColorName": shoe_color_name,
            }
        )

    record = {
        "id": int(rid),
        "orderId": int(order_id),
        "orderShoeId": int(order_shoe_id) if order_shoe_id else None,
        "status": status,
        "stageText": STATUS_STAGE.get(status, status),
        "reason": reason,
        "remark": remark,
        "createdAt": created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else None,
        "orderRid": order_rid,
        "customerName": cust_name,
    }

    return jsonify({"record": record, "items": items})


def _to_float4(v):
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        v = float(v)
    return round(float(v), 4)

def _fmt_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

def _get_order_qty_from_ost(ost):
    # 在不同库里字段名可能不一样，这里做多候选兜底
    for attr in ("order_qty", "quantity", "qty", "order_quantity", "count"):
        if hasattr(ost, attr):
            val = getattr(ost, attr)
            if val is not None:
                try:
                    return float(val)
                except Exception:
                    return 0.0
    return 0.0

def _stage_text(status):
    mapping = {
        "0": "等待用量填写",
        "1": "等待采购用量",
        "2": "补采流程已完成"
        
        
    }
    return mapping.get(status, str(status or ""))

@missing_material_purchase_bp.get("/missing_material_purchase/usage_tasks")
def usage_tasks():
    """
    列表：需要填写/核定用量的补采记录
    支持筛选：keyword（订单号/客户/记录ID），onlyPending(0/1)，排序，分页
    返回：id/orderRid/customerName/createdAt/stageText/pendingNodeText/itemCount/filledCount
    """
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 20, type=int)
    keyword = (request.args.get("keyword") or "").strip()
    only_pending = request.args.get("onlyPending", 1, type=int)
    sort_prop = request.args.get("sortProp", "createdAt")
    sort_order = request.args.get("sortOrder", "desc")

    # per-record 统计子查询
    item_stat = (
        db.session.query(
            WMRItem.record_id.label("rid"),
            func.count(WMRItem.id).label("item_count"),
            func.sum(case((WMRItem.approval_usage.isnot(None), 1), else_=0)).label("filled_count"),
        )
        .group_by(WMRItem.record_id)
        .subquery()
    )

    q = (
        db.session.query(
            WMR.id,
            WMR.order_id,
            WMR.status,
            WMR.created_at,
            Order.order_rid,
            Customer.customer_name,
            item_stat.c.item_count,
            item_stat.c.filled_count,
        )
        .join(Order, Order.order_id == WMR.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(item_stat, item_stat.c.rid == WMR.id)
        .filter(WMR.status == "0")  # 用量填写状态
    )

    if keyword:
        like = f"%{keyword}%"
        # 记录ID精确/模糊都可；其他用 LIKE
        cond = (Order.order_rid.like(like)) | (Customer.customer_name.like(like))
        if keyword.isdigit():
            cond = cond | (WMR.id == int(keyword))
        q = q.filter(cond)

    if only_pending == 1:
        q = q.filter(item_stat.c.filled_count < item_stat.c.item_count)

    # 排序
    sort_map = {
        "id": WMR.id,
        "createdAt": WMR.created_at,
        "orderRid": Order.order_rid,
        "itemCount": item_stat.c.item_count,
        "filledCount": item_stat.c.filled_count,
    }
    order_col = sort_map.get(sort_prop, WMR.created_at)
    q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))

    total = q.count()
    rows = q.limit(page_size).offset((page - 1) * page_size).all()

    data = []
    for rid, order_id, status, created_at, order_rid, cust_name, item_cnt, filled_cnt in rows:
        data.append(
            {
                "id": int(rid),
                "orderRid": order_rid,
                "customerName": cust_name,
                "createdAt": _fmt_time(created_at),
                "stageText": _stage_text(status),
                "pendingNodeText": "待填写用量" if (filled_cnt or 0) < (item_cnt or 0) else "已填写",
                "itemCount": int(item_cnt or 0),
                "filledCount": int(filled_cnt or 0),
            }
        )

    return jsonify({"total": total, "list": data})
@missing_material_purchase_bp.get("/missing_material_purchase/purchase_amount_tasks")
def purchase_amount_tasks():
    """
    列表：需要填写/核定用量的补采记录
    支持筛选：keyword（订单号/客户/记录ID），onlyPending(0/1)，排序，分页
    返回：id/orderRid/customerName/createdAt/stageText/pendingNodeText/itemCount/filledCount
    """
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 20, type=int)
    keyword = (request.args.get("keyword") or "").strip()
    only_pending = request.args.get("onlyPending", 1, type=int)
    sort_prop = request.args.get("sortProp", "createdAt")
    sort_order = request.args.get("sortOrder", "desc")

    # per-record 统计子查询
    item_stat = (
        db.session.query(
            WMRItem.record_id.label("rid"),
            func.count(WMRItem.id).label("item_count"),
            func.sum(case((WMRItem.purchase_amount.isnot(None), 1), else_=0)).label("filled_count"),
        )
        .group_by(WMRItem.record_id)
        .subquery()
    )

    q = (
        db.session.query(
            WMR.id,
            WMR.order_id,
            WMR.status,
            WMR.created_at,
            Order.order_rid,
            Customer.customer_name,
            item_stat.c.item_count,
            item_stat.c.filled_count,
        )
        .join(Order, Order.order_id == WMR.order_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(item_stat, item_stat.c.rid == WMR.id)
        .filter(WMR.status == "1")  # 采购量填写状态
    )
    

    if keyword:
        like = f"%{keyword}%"
        # 记录ID精确/模糊都可；其他用 LIKE
        cond = (Order.order_rid.like(like)) | (Customer.customer_name.like(like))
        if keyword.isdigit():
            cond = cond | (WMR.id == int(keyword))
        q = q.filter(cond)

    if only_pending == 1:
        q = q.filter(item_stat.c.filled_count < item_stat.c.item_count)

    # 排序
    sort_map = {
        "id": WMR.id,
        "createdAt": WMR.created_at,
        "orderRid": Order.order_rid,
        "itemCount": item_stat.c.item_count,
        "filledCount": item_stat.c.filled_count,
    }
    order_col = sort_map.get(sort_prop, WMR.created_at)
    q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))
    
    total = q.count()
    rows = q.limit(page_size).offset((page - 1) * page_size).all()
    data = []
    for rid, order_id, status, created_at, order_rid, cust_name, item_cnt, filled_cnt in rows:
        data.append(
            {
                "id": int(rid),
                "orderRid": order_rid,
                "customerName": cust_name,
                "createdAt": _fmt_time(created_at),
                "stageText": _stage_text(status),
                "pendingNodeText": "待填写用量" if (filled_cnt or 0) < (item_cnt or 0) else "已填写",
                "itemCount": int(item_cnt or 0),
                "filledCount": int(filled_cnt or 0),
            }
        )

    return jsonify({"total": total, "list": data})


@missing_material_purchase_bp.get("/missing_material_purchase/usage_form")
def usage_form():
    record_id = request.args.get("id", type=int)
    if not record_id:
        return jsonify({"message": "缺少参数 id"}), 400

    rec = db.session.query(WMR).filter(WMR.id == record_id).first()
    if not rec:
        return jsonify({"message": "记录不存在"}), 404

    order = db.session.query(Order).filter(Order.order_id == rec.order_id).first()
    customer = (
        db.session.query(Customer).filter(Customer.customer_id == order.customer_id).first()
        if order else None
    )
    shoe_rid = (
        db.session.query(Shoe.shoe_rid)
        .join(OrderShoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(OrderShoe.order_shoe_id == rec.order_shoe_id)
        .scalar()
        if rec.order_shoe_id else None
    )

    record = {
        "id": int(rec.id),
        "orderId": int(rec.order_id),
        "orderRid": getattr(order, "order_rid", None),
        "orderShoeId": int(rec.order_shoe_id) if rec.order_shoe_id else None,
        "shoeRid": shoe_rid,
        "customerName": getattr(customer, "customer_name", None),
        "createdAt": _fmt_time(rec.created_at),
        "stageText": _stage_text(rec.status),
        "reason": rec.reason,
        "remark": rec.remark,
    }

    items = db.session.query(WMRItem).filter(WMRItem.record_id == rec.id).all()

    # 批量拿颜色/订单数量（按你的项目方式）
    ost_ids = {it.order_shoe_type_id for it in items if it.order_shoe_type_id}
    color_map, qty_map = {}, {}
    if ost_ids:
        rows = (
            db.session.query(OrderShoeType, ShoeType, Color)
            .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
            .join(Color, Color.color_id == ShoeType.color_id)
            .filter(OrderShoeType.order_shoe_type_id.in_(ost_ids))
            .all()
        )
        for ost, st, col in rows:
            ost_id = int(ost.order_shoe_type_id)
            color_map[ost_id] = getattr(col, "color_name", "") or ""
            qty_map[ost_id] = _get_order_qty_from_ost(ost)  # 你现有的获取逻辑

    # 可选：材料名映射
    mat_name_map = {}
    try:
        from models import Material
        mat_ids = {it.material_id for it in items if it.material_id}
        if mat_ids:
            mrows = (
                db.session.query(Material.material_id, Material.material_name)
                .filter(Material.material_id.in_(mat_ids))
                .all()
            )
            mat_name_map = {int(mid): name for (mid, name) in mrows}
    except Exception:
        pass

    type_text = {"S": "面料", "I": "里料", "A": "辅料", "O": "大底", "M": "中底", "H": "烫底"}

    out_items = []
    for it in items:
        ost_id = int(it.order_shoe_type_id) if it.order_shoe_type_id else None
        row = {
            "id": int(it.id),
            "orderShoeTypeId": ost_id,
            "shoeColorName": color_map.get(ost_id or -1, ""),
            "materialName": mat_name_map.get(int(it.material_id)) if it.material_id else "-",
            "materialModel": it.material_model or "",
            "materialSpecification": it.material_specification or "",
            "color": it.color or "",
            "orderQty": _to_float4(qty_map.get(ost_id or -1, 0.0)),
            "unitUsage": _to_float4(it.unit_usage),
            "approvalUsage": _to_float4(it.approval_usage),
            "materialType": type_text.get(it.material_type, ""),
        }

        if _is_size_based(it.material_type):
            # 新：数组优先
            if it.size_qty_arr:
                row["sizeQuantitiesArr"] = list(it.size_qty_arr)

            # 若有数组，前端也会显示 approvalUsage；这里可以用数组合计覆盖一下（防脏数据）
            if it.size_qty_arr:
                row["approvalUsage"] = _to_float4(_sum_list(it.size_qty_arr))

        out_items.append(row)

    return jsonify({"record": record, "items": out_items})



@missing_material_purchase_bp.post("/missing_material_purchase/usage_save")
def usage_save():
    data = request.get_json(force=True) or {}
    record_id = data.get("recordId")
    items = data.get("items") or []
    if not record_id or not isinstance(items, list):
        return jsonify({"success": False, "message": "参数不合法"}), 400

    rec = db.session.query(WMR).filter(WMR.id == record_id).first()
    if not rec:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    item_map = {
        int(x.id): x
        for x in db.session.query(WMRItem).filter(WMRItem.record_id == record_id).all()
    }


    updated = 0
    for row in items:
        iid = row.get("id")
        if not iid: continue
        model_item = item_map.get(int(iid))
        if not model_item: continue

        uu  = row.get("unitUsage", None)
        au  = row.get("approvalUsage", None)
        arr = row.get("sizeQuantitiesArr", None)  # 新：数组
        mp  = row.get("sizeQuantities", None)     # 旧：Map（兼容）

        if _is_size_based(model_item.material_type):
            # 优先数组；否则把 Map 按当前列顺序转数组
            if isinstance(arr, list):
                clean_arr = [int(Decimal(str(v or 0))) for v in arr]
            else:
                clean_arr = None

            if clean_arr is not None:
                model_item.size_qty_arr   = clean_arr
                model_item.approval_usage = _sum_list(clean_arr)  # 核定=数组合计
                # 可选清空 unit_usage：带尺码材料按数量，不依赖单位用量
                # model_item.unit_usage   = None
            else:
                # 未提供数组也允许更新其它字段（如果你想严格要求数组，这里可以直接报错）
                if uu is not None:
                    model_item.unit_usage = Decimal(str(uu)) if not isinstance(uu, Decimal) else uu
                if au is not None:
                    model_item.approval_usage = Decimal(str(au)) if not isinstance(au, Decimal) else au
        else:
            # 普通材料：照常保存
            if uu is not None:
                model_item.unit_usage = Decimal(str(uu)) if not isinstance(uu, Decimal) else uu
            if au is not None:
                model_item.approval_usage = Decimal(str(au)) if not isinstance(au, Decimal) else au

        updated += 1

    db.session.commit()
    return jsonify({"success": True, "updated": updated})

@missing_material_purchase_bp.get('/missing_material_purchase/purchase_form')
def purchase_form():
    record_id = request.args.get('id', type=int)
    if not record_id:
        return jsonify({'message': '缺少参数 id'}), 400

    rec = db.session.query(WMR).filter(WMR.id==record_id).first()
    if not rec:
        return jsonify({'message':'记录不存在'}), 404

    order = db.session.query(Order).filter(Order.order_id==rec.order_id).first()
    customer_name = getattr(order, 'customer_name', None)
    order_rid = getattr(order, 'order_rid', None)

    # shoeRid
    shoe_rid = (
        db.session.query(Shoe.shoe_rid)
        .join(OrderShoe, OrderShoe.shoe_id==Shoe.shoe_id)
        .filter(OrderShoe.order_shoe_id==rec.order_shoe_id)
        .scalar()
        if rec.order_shoe_id else None
    )

    record = {
        'id': int(rec.id),
        'orderId': int(rec.order_id),
        'orderRid': order_rid,
        'orderShoeId': int(rec.order_shoe_id) if rec.order_shoe_id else None,
        'shoeRid': shoe_rid,
        'customerName': customer_name,
        'createdAt': _fmt_time(rec.created_at),
        'stageText': _stage_text(rec.status),
        'reason': rec.reason,
        'remark': rec.remark,
    }

    items = db.session.query(WMRItem).filter(WMRItem.record_id==rec.id).all()

    # 批量构造 颜色名 & 订单数量
    ost_ids = {it.order_shoe_type_id for it in items if it.order_shoe_type_id}
    color_map, qty_map = {}, {}
    if ost_ids:
        rows = (
            db.session.query(OrderShoeType, ShoeType, Color)
            .join(ShoeType, ShoeType.shoe_type_id==OrderShoeType.shoe_type_id)
            .join(Color, Color.color_id==ShoeType.color_id)
            .filter(OrderShoeType.order_shoe_type_id.in_(ost_ids))
            .all()
        )
        for ost, st, col in rows:
            k = int(ost.order_shoe_type_id)
            color_map[k] = getattr(col, 'color_name', '') or ''
            # 你项目里订单数获取逻辑
            qty_map[k] = float(getattr(ost, 'order_qty', 0) or 0)

    out_items = []
    mat_name_map = {}
    try:
        from models import Material
        mat_ids = {it.material_id for it in items if it.material_id}
        if mat_ids:
            mrows = (
                db.session.query(Material.material_id, Material.material_name)
                .filter(Material.material_id.in_(mat_ids))
                .all()
            )
            mat_name_map = {int(mid): name for (mid, name) in mrows}
    except Exception:
        pass
    for it in items:
        ost_id = int(it.order_shoe_type_id) if it.order_shoe_type_id else None
        shoe_color = color_map.get(ost_id or -1, '')
        order_qty  = qty_map.get(ost_id or -1, 0.0)

        mat_type_name = MAT_TYPE_NAME.get(it.material_type, '')
        is_size_based = it.material_type in SIZE_BASED_TYPES

        # 基本字段
        row = {
            'id': int(it.id),
            'orderShoeTypeId': ost_id,
            'shoeColorName': shoe_color,
            'materialType': mat_type_name,
            'materialName': mat_name_map.get(int(it.material_id), '') if it.material_id else '',
            'materialModel': it.material_model or '',
            'materialSpecification': it.material_specification or '',
            'color': it.color or '',
            'orderQty': _to_f4(order_qty),
            'unitUsage': _to_f4(it.unit_usage),
            'approvalUsage': _to_f4(it.approval_usage),
        }

        if is_size_based:
            # 优先核定尺码数组：用来默认采购
            size_approval = None
            if hasattr(it, 'size_qty_arr') and it.size_qty_arr:
                size_approval = list(it.size_qty_arr)

            # 采购尺码数组：如已保存则回显；否则默认=核定尺码数组
            size_purchase = None
            if hasattr(it, 'size_purchase_amount_arr') and it.size_purchase_amount_arr:
                size_purchase = list(it.size_purchase_amount_arr)
            elif size_approval:
                size_purchase = list(size_approval)

            row['size_approval_amount_arr'] = size_approval or []
            row['size_purchase_amount_arr'] = size_purchase or []

            # 采购用量 = 采购尺码数组合计（若为空则 0）
            row['purchaseUsage'] = _to_f4(_sum_list(size_purchase or []))
            row['manualPurchase'] = False  # 尺码材料不需要“手动采购”概念
        else:
            # 普通材料：采购用量 = 已存采购用量；若空 => 默认等于核定用量
            p = it.purchase_amount
            row['purchaseUsage'] = _to_f4(p if p is not None else it.approval_usage)
            row['manualPurchase'] = True  # 允许手动编辑

        out_items.append(row)

    return jsonify({'record': record, 'items': out_items})


def _fix4(n) -> Decimal:
    """保留4位小数（用于金额/用量），确保 Decimal 类型。"""
    return Decimal(str(round(Decimal(str(n or 0)), 4)))

def _sum_list(nums: List) -> Decimal:
    s = Decimal("0")
    for v in (nums or []):
        s += Decimal(str(v or 0))
    return _fix4(s)

def gen_divide_order_rid(supplier_id: Optional[int]) -> str:
    """BC + yyyyMMddHHmmss + rand6 + 'F' + supplier_id(4位补零)"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand6 = randomIdGenerater(6)
    sid = str(int(supplier_id or 0)).zfill(4)
    return f"BC{ts}{rand6}F{sid}"

def get_or_create_purchase_order(order_id: int, order_shoe_id: Optional[int]) -> PurchaseOrder:
    po = (
        db.session.query(PurchaseOrder)
        .filter(
            PurchaseOrder.order_id == order_id,
            PurchaseOrder.order_shoe_id == (order_shoe_id or None),
        )
        .order_by(PurchaseOrder.purchase_order_id.asc())
        .first()
    )
    if po:
        return po
    po = PurchaseOrder(
        bom_id=None,
        purchase_order_rid=f"PO{datetime.now().strftime('%Y%m%d%H%M%S')}{randomIdGenerater(4)}",
        purchase_order_type="N",
        purchase_order_issue_date=date.today(),
        order_id=order_id,
        order_shoe_id=order_shoe_id,
        purchase_order_status="0",
    )
    db.session.add(po)
    db.session.flush()
    return po

def resolve_supplier_id(item: WMRItem) -> Optional[int]:

    sid = getattr(item, "supplier_id", None)
    if sid:
        return int(sid)
    try:
        if getattr(item, "material_id", None):
            m = db.session.query(Material).filter(Material.material_id == item.material_id).first()
            if m and getattr(m, "supplier_id", None):
                return int(m.material_supplier)
    except Exception:
        pass
    return None  # 未找到则归为 None 组，RID 尾部 0000

def get_material_unit_map(material_ids: set) -> Dict[int, Optional[str]]:
    if not material_ids:
        return {}
    rows = (
        db.session.query(Material.material_id, Material.material_unit)
        .filter(Material.material_id.in_(list(material_ids)))
        .all()
    )
    return {int(mid): unit for (mid, unit) in rows}

def parse_size_purchase_arr(row: dict) -> Optional[List[int]]:
    """
    从前端 items[*] 中解析尺寸采购数组（兼容多键名）：
    优先：size_purchase_amount_arr
    """
    for k in ("size_purchase_amount_arr", "purchase_amount_arr", "sizePurchaseArr"):
        arr = row.get(k)
        if isinstance(arr, list):
            return [int(n or 0) for n in arr]
    return None

def fill_item_size_columns(po_item: PurchaseOrderItem, arr: List[int]):
    """把数组按 34..46 写入 PurchaseOrderItem 的 size_xx_purchase_amount 列。"""
    arr = list(arr or [])
    # pad/truncate 到和 SIZE_COLS 一致
    if len(arr) < len(SIZE_COLS):
        arr = arr + [0] * (len(SIZE_COLS) - len(arr))
    if len(arr) > len(SIZE_COLS):
        arr = arr[: len(SIZE_COLS)]

    for idx, size in enumerate(SIZE_COLS):
        colname = f"size_{size}_purchase_amount"
        setattr(po_item, colname, int(arr[idx] or 0))

# ======== 提交/保存接口 ========

@missing_material_purchase_bp.post("/missing_material_purchase/purchase_save")
def purchase_save():
    data = request.get_json(force=True) or {}
    record_id = data.get("recordId")
    submit_flag = int(data.get("submit") or 0)
    items_in = data.get("items") or []
    if not record_id or not isinstance(items_in, list):
        return jsonify({"success": False, "message": "参数不合法"}), 400

    rec: WMR = db.session.query(WMR).filter(WMR.id == int(record_id)).first()
    if not rec:
        return jsonify({"success": False, "message": "记录不存在"}), 404

    item_map: Dict[int, WMRItem] = {
        int(x.id): x
        for x in db.session.query(WMRItem).filter(WMRItem.record_id == rec.id).all()
    }
    if not item_map:
        return jsonify({"success": False, "message": "无明细可处理"}), 400

    updated = 0
    staged_rows: List[Tuple[WMRItem, Decimal, Optional[List[int]]]] = []

    # 1) 先把草稿值写回（无论是否提交）
    for row in items_in:
        iid = row.get("id")
        if not iid:
            continue
        model_item: WMRItem = item_map.get(int(iid))
        if not model_item:
            continue

        mat_type_code = (getattr(model_item, "material_type", "") or "").strip()
        is_size_based = mat_type_code in ("O", "M", "H")  # 大底/中底/烫底

        size_arr = parse_size_purchase_arr(row)
        if is_size_based:
            if not size_arr:
                size_arr = getattr(model_item, "size_approval_amount_arr", None)
                if isinstance(size_arr, list):
                    size_arr = [int(n or 0) for n in size_arr]
            total = _sum_list(size_arr or [])
            if hasattr(model_item, "size_purchase_amount_arr"):
                model_item.size_purchase_amount_arr = size_arr or []
            if hasattr(model_item, "purchase_amount"):
                model_item.purchase_amount = total
            updated += 1
            staged_rows.append((model_item, total, size_arr or []))
        else:
            pur = row.get("purchaseUsage", None)
            if pur is not None and hasattr(model_item, "purchase_amount"):
                model_item.purchase_amount = _fix4(pur)
            total = _fix4(pur or 0)
            updated += 1
            staged_rows.append((model_item, total, None))

    db.session.commit()  # ← 草稿阶段的独立提交

    if not submit_flag:
        return jsonify({"success": True, "updated": updated, "submitted": False})

    # 2) 提交：不要再显式 begin()，直接在 try 中做，末尾统一 commit
    # 2.1 校验 BOM
    ost_ids = set()
    for (wmr_item, _, __) in staged_rows:
        ost = getattr(wmr_item, "order_shoe_type_id", None)
        if not ost:
            return jsonify({"success": False, "message": f"明细 {wmr_item.id} 缺少 order_shoe_type_id"}), 400
        ost_ids.add(int(ost))

    bom_rows = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id.in_(list(ost_ids)), Bom.bom_type == 0)
        .all()
    )
    bom_map: Dict[int, Bom] = {int(b.order_shoe_type_id): b for b in bom_rows}
    missing = [str(oid) for oid in ost_ids if oid not in bom_map]
    if missing:
        return jsonify({"success": False, "message": f"BOM 不存在（bom_type=0）：order_shoe_type_id={','.join(missing)}"}), 400

    # 2.2 预取单位
    material_ids = {
        int(getattr(wmr_item, "material_id"))
        for (wmr_item, _, __) in staged_rows
        if getattr(wmr_item, "material_id", None)
    }
    mat_unit_map = get_material_unit_map(material_ids)

    try:
        # 获取/创建采购单（不显式 begin）
        po = get_or_create_purchase_order(
            order_id=int(rec.order_id),
            order_shoe_id=getattr(rec, "order_shoe_id", None),
        )

        # 先为每条明细创建 BomItem
        bom_item_id_map: Dict[int, int] = {}
        for (wmr_item, pur_amt, size_arr) in staged_rows:
            ost = int(getattr(wmr_item, "order_shoe_type_id"))
            bom = bom_map[ost]

            unit_usage_val = getattr(wmr_item, "unit_usage", None)
            try:
                unit_usage_val = _fix4(unit_usage_val)
            except Exception:
                unit_usage_val = _fix4(0)

            bi = BomItem(
                material_id=getattr(wmr_item, "material_id", None),
                material_specification=getattr(wmr_item, "material_specification", None),
                material_model=getattr(wmr_item, "material_model", None),
                unit_usage=unit_usage_val,
                total_usage=_fix4(pur_amt),
                department_id=getattr(wmr_item, "department_id", None),
                bom_item_add_type="0",  # 按你字典
                remark=getattr(wmr_item, "remark", None),
                bom_id=bom.bom_id,
                bom_item_color=getattr(wmr_item, "color", None),
                size_type=getattr(wmr_item, "size_type", "E"),
                material_second_type=getattr(wmr_item, "material_second_type", None),
                craft_name=getattr(wmr_item, "craft_name", None),
                pairs=None,
                production_instruction_item_id=getattr(wmr_item, "production_instruction_item_id", None),
            )
            db.session.add(bi)
            db.session.flush()

            if isinstance(size_arr, list) and size_arr:
                fill_bom_size_columns(bi, size_arr)

            bom_item_id_map[int(wmr_item.id)] = int(bi.bom_item_id)

        # 按供应商分组创建分单 + PO Item
        buckets: Dict[Optional[int], List[Tuple[WMRItem, Decimal, Optional[List[int]]]]] = {}
        for (wmr_item, pur_amt, size_arr) in staged_rows:
            sid = resolve_supplier_id(wmr_item)  # 下方函数已修正 supplier 字段
            buckets.setdefault(sid, []).append((wmr_item, pur_amt, size_arr))

        for supplier_id, group_rows in buckets.items():
            pdo = PurchaseDivideOrder(
                purchase_order_id=po.purchase_order_id,
                purchase_divide_order_rid=gen_divide_order_rid(supplier_id),
                purchase_divide_order_type="N",
                purchase_order_remark=None,
                purchase_order_environmental_request=None,
                shipment_address=None,
                shipment_deadline=None,
                total_purchase_order_id=None,
            )
            db.session.add(pdo)
            db.session.flush()

            for (wmr_item, pur_amt, size_arr) in group_rows:
                mid = getattr(wmr_item, "material_id", None)
                inbound_unit = mat_unit_map.get(int(mid)) if mid else None

                poi = PurchaseOrderItem(
                    bom_item_id=bom_item_id_map[int(wmr_item.id)],
                    purchase_divide_order_id=pdo.purchase_divide_order_id,
                    purchase_amount=_fix4(pur_amt),
                    adjust_purchase_amount=_fix4(0),
                    approval_amount=_fix4(getattr(wmr_item, "approval_usage", 0)),
                    inbound_material_id=mid,
                    inbound_unit=inbound_unit,
                    material_id=mid,
                    material_specification=getattr(wmr_item, "material_specification", None),
                    material_model=getattr(wmr_item, "material_model", None),
                    color=getattr(wmr_item, "color", None),
                    size_type=getattr(wmr_item, "size_type", "E"),
                    craft_name=getattr(wmr_item, "craft_name", None),
                    remark=getattr(wmr_item, "remark", None),
                    related_selected_material_storage=getattr(wmr_item, "related_selected_material_storage", "[]"),
                )
                db.session.add(poi)
                db.session.flush()

                if isinstance(size_arr, list) and size_arr:
                    fill_item_size_columns(poi, size_arr)

        # 流转状态
        rec.status = "2"
        db.session.add(rec)

        db.session.commit()  # ← 在这里统一提交
        return jsonify({
            "success": True,
            "submitted": True,
            "updated": updated,
            "purchase_order_id": po.purchase_order_id,
            "message": "提交成功，已生成分单与订单明细"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"提交失败：{str(e)}"}), 500






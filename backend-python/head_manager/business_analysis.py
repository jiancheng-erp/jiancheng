# business_analysis.py
from flask import Blueprint, request, jsonify
from sqlalchemy import and_, func, distinct, case, or_
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from collections import defaultdict
from app_config import db

from models import (
    Order,
    OrderShoe,
    OrderShoeType,
    Customer,
    OrderShoeBatchInfo,
    MaterialStorage,
    Shoe,
    OrderShoeProductionInfo,
    ProductionInstruction,
    ProductionInstructionItem,
    Supplier,
    Material,
    SPUMaterial,
)

business_analysis_bp = Blueprint("business_analysis", __name__)
TYPE_ID_TO_LABEL = {
    1: "面料",
    2: "里料",
    3: "辅料",
    5: "辅料",
    7: "底材",
}
CAT_LABEL_TO_TYPE_IDS = {
    "全部": None,  # 不限
    "面料": {1},
    "里料": {2},
    "辅料": {3, 5},
    "底材": {7},
}
CURRENCY_RATE = {
    "RMB": Decimal("1.00"),
    "CNY": Decimal("1.00"),
    "USD": Decimal("7.20"),
    "USA": Decimal("7.20"),
    "EUR": Decimal("7.80"),
    None: Decimal("1.00"),
}


def parse_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def to_rmb(amount: Decimal, currency: str) -> Decimal:
    rate = CURRENCY_RATE.get(currency, Decimal("1.00"))
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _order_filters(date_from, date_to, status):
    conds = []
    if status:
        conds.append(Order.last_status == status)  # 和你后面接口保持一致
    if date_from:
        conds.append(Order.start_date >= date_from)
    if date_to:
        conds.append(Order.start_date <= date_to)
    return conds


# ===== 通用：计算一批订单的 GMV & 成本，返回 dict =====
def _order_gmv_map(order_ids):
    """
    返回：{order_id: Decimal('gmv')}
    GMV = sum(batch.total_amount * unit_price[RMB]) over OrderShoeType
    """
    if not order_ids:
        return {}
    q = (
        db.session.query(
            Order.order_id,
            OrderShoeType.unit_price,
            OrderShoeType.currency_type,
            OrderShoeBatchInfo.total_amount,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .filter(Order.order_id.in_(order_ids))
    )
    g = defaultdict(lambda: Decimal("0.00"))
    for oid, price, cur, amt in q.all():
        if price is None or amt is None:
            continue
        g[oid] += to_rmb(Decimal(str(price)), cur) * Decimal(int(amt))
    # 统一量化
    return {k: v.quantize(Decimal("0.01")) for k, v in g.items()}


def _order_cost_map(order_ids):
    """
    返回：{order_id: Decimal('total_cost')}
    成本 = sum(MaterialStorage.unit_price * inbound_amount)
    """
    if not order_ids:
        return {}
    q = db.session.query(
        MaterialStorage.order_id,
        MaterialStorage.unit_price,
        MaterialStorage.inbound_amount,
    ).filter(MaterialStorage.order_id.in_(order_ids))
    g = defaultdict(lambda: Decimal("0.00"))
    for oid, unit_price, inbound_amount in q.all():
        if unit_price is None or inbound_amount is None:
            continue
        g[oid] += Decimal(str(unit_price)) * Decimal(str(inbound_amount))
    return {k: v.quantize(Decimal("0.01")) for k, v in g.items()}


# ===== /businessanalysis/kpis/overview =====
@business_analysis_bp.route("/businessanalysis/kpis/overview", methods=["GET"])
def ba_kpis_overview():
    date_from = parse_date(request.args.get("date_from", ""))
    date_to = parse_date(request.args.get("date_to", ""))
    status = request.args.get("status", type=str)

    conds = _order_filters(date_from, date_to, status)

    # 订单/客户/供应商数量
    orders_q = db.session.query(Order.order_id, Order.customer_id).filter(and_(*conds))
    order_rows = orders_q.all()
    order_ids = [r[0] for r in order_rows]
    customers_cnt = len(set(r[1] for r in order_rows))
    orders_cnt = len(order_ids)

    # 供应商数（在筛选订单范围内出现过的供应商）
    supplier_ids = set()
    if order_ids:
        s_q = (
            db.session.query(distinct(Supplier.supplier_id))
            .join(Material, Material.material_supplier == Supplier.supplier_id)
            .join(
                ProductionInstructionItem,
                ProductionInstructionItem.material_id == Material.material_id,
            )
            .join(
                ProductionInstruction,
                ProductionInstruction.production_instruction_id
                == ProductionInstructionItem.production_instruction_id,
            )
            .join(
                OrderShoe,
                OrderShoe.order_shoe_id == ProductionInstruction.order_shoe_id,
            )
            .filter(OrderShoe.order_id.in_(order_ids))
        )
        supplier_ids = {sid for (sid,) in s_q.all()}

    # 金额类
    gmv_map = _order_gmv_map(order_ids)
    cost_map = _order_cost_map(order_ids)
    gmv = sum(gmv_map.values(), Decimal("0.00"))
    total_cost = sum(cost_map.values(), Decimal("0.00"))
    gross_profit = (gmv - total_cost).quantize(Decimal("0.01"))
    gross_margin = (
        float((gross_profit / gmv).quantize(Decimal("0.0001"))) if gmv > 0 else None
    )

    resp = {
        "orders": orders_cnt,
        "customers": customers_cnt,
        "suppliers": len(supplier_ids),
        "gmv": float(gmv),
        "gross_profit": float(gross_profit),
        "gross_margin": gross_margin,
    }
    return jsonify(resp), 200


# ===== /businessanalysis/top/orders =====
@business_analysis_bp.route("/businessanalysis/top/orders", methods=["GET"])
def ba_top_orders():
    """
    metric = gmv | gross_profit | gross_margin
    """
    date_from = parse_date(request.args.get("date_from", ""))
    date_to = parse_date(request.args.get("date_to", ""))
    status = request.args.get("status", type=str)
    metric = request.args.get("metric", type=str, default="gross_profit")
    page = max(1, request.args.get("page", type=int, default=1))
    size = max(1, min(200, request.args.get("size", type=int, default=10)))

    conds = _order_filters(date_from, date_to, status)

    # 分页订单集合
    q = db.session.query(Order).filter(and_(*conds))
    total = q.count()
    orders_page = (
        q.order_by(
            case((Order.start_date.is_(None), 1), else_=0).asc(),
            Order.start_date.desc(),
            Order.order_id.desc(),
        )
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    if not orders_page:
        return jsonify({"rows": [], "total": total})

    order_ids = [o.order_id for o in orders_page]
    gmv_map = _order_gmv_map(order_ids)
    cost_map = _order_cost_map(order_ids)

    # 客户名/品牌
    cust_rows = dict(
        db.session.query(Customer.customer_id, Customer.customer_name).all()
    )
    brand_rows = dict(
        db.session.query(Customer.customer_id, Customer.customer_brand).all()
    )

    rows = []
    for o in orders_page:
        gmv = gmv_map.get(o.order_id, Decimal("0.00"))
        cost = cost_map.get(o.order_id, Decimal("0.00"))
        gp = (gmv - cost).quantize(Decimal("0.01"))
        gm = float((gp / gmv).quantize(Decimal("0.0001"))) if gmv > 0 else None
        cname = cust_rows.get(o.customer_id, f"客户{o.customer_id}")
        brand = brand_rows.get(o.customer_id)
        label = f"{cname}-{brand}" if brand else cname
        rows.append(
            {
                "order_rid": getattr(o, "order_rid", o.order_id),
                "customer": label,
                "customer_id": o.customer_id,
                "gmv": float(gmv),
                "gross_profit": float(gp),
                "gross_margin": gm,
            }
        )

    # 按 metric 排序（页面内排序）
    def keyf(r):
        v = r.get(metric)
        return (-1e18) if v is None else float(v)

    rows.sort(key=lambda r: keyf(r), reverse=True)

    return jsonify({"rows": rows, "total": total})


# ===== /businessanalysis/top/customers =====
@business_analysis_bp.route("/businessanalysis/top/customers", methods=["GET"])
def ba_top_customers():
    """
    metric = gmv | gross_profit | gross_margin | orders
    """
    date_from = parse_date(request.args.get("date_from", ""))
    date_to = parse_date(request.args.get("date_to", ""))
    status = request.args.get("status", type=str)
    metric = request.args.get("metric", type=str, default="gmv")
    page = max(1, request.args.get("page", type=int, default=1))
    size = max(1, min(200, request.args.get("size", type=int, default=10)))

    conds = _order_filters(date_from, date_to, status)
    # 先取符合条件的订单
    q = db.session.query(Order.order_id, Order.customer_id).filter(and_(*conds))
    raw = q.all()
    if not raw:
        return jsonify({"rows": [], "total": 0})

    # 聚合订单列表到客户
    by_customer = defaultdict(list)
    for oid, cid in raw:
        by_customer[cid].append(oid)

    # 计算每客户 GMV/Cost
    all_order_ids = [oid for lst in by_customer.values() for oid in lst]
    gmv_map_all = _order_gmv_map(all_order_ids)
    cost_map_all = _order_cost_map(all_order_ids)

    # 客户名/品牌
    name_map = dict(
        db.session.query(Customer.customer_id, Customer.customer_name).all()
    )
    brand_map = dict(
        db.session.query(Customer.customer_id, Customer.customer_brand).all()
    )

    items = []
    for cid, oids in by_customer.items():
        gmv = sum(
            (gmv_map_all.get(oid, Decimal("0.00")) for oid in oids), Decimal("0.00")
        )
        cost = sum(
            (cost_map_all.get(oid, Decimal("0.00")) for oid in oids), Decimal("0.00")
        )
        gp = (gmv - cost).quantize(Decimal("0.01"))
        gm = float((gp / gmv).quantize(Decimal("0.0001"))) if gmv > 0 else None
        label = name_map.get(cid, f"客户{cid}")
        brand = brand_map.get(cid)
        disp = f"{label}-{brand}" if brand else label
        items.append(
            {
                "customer": disp,
                "customer_id": cid,
                "orders": len(oids),
                "gmv": float(gmv),
                "gross_profit": float(gp),
                "gross_margin": gm,
            }
        )

    # 排序 + 分页
    def keyf(r):
        v = r.get(metric)
        return (-1e18) if v is None else float(v)

    items.sort(key=lambda r: keyf(r), reverse=True)

    total = len(items)
    start = (page - 1) * size
    rows = items[start : start + size]
    return jsonify({"rows": rows, "total": total})


@business_analysis_bp.route("/businessanalysis/top/suppliers", methods=["GET"])
def ba_top_suppliers():
    """
    metric = usage_count | related_gmv
    - usage_count：COUNT(DISTINCT PI)（基于 PII），按 material.material_type_id 做大类过滤；继续忽略 PII 的 H 类
    - related_gmv：从 MaterialStorage 汇总（unit_price * inbound_amount），
      通过 MS -> SPU -> Material -> Supplier 归因，并按 material.material_type_id 做大类过滤
    公共筛选：date_from/date_to/status（基于 Order.start_date / 状态）
    material_cat：全部 / 面料 / 里料 / 辅料 / 底材
    """
    # ------- 参数 -------
    date_from = parse_date(request.args.get("date_from", ""))
    date_to = parse_date(request.args.get("date_to", ""))
    status = request.args.get("status", type=str)
    metric = request.args.get("metric", default="usage_count", type=str)
    material_cat = request.args.get("material_cat", default="全部", type=str)
    page = max(1, request.args.get("page", default=1, type=int))
    size = max(1, min(200, request.args.get("size", default=10, type=int)))

    # 订单范围
    conds = _order_filters(date_from, date_to, status)
    sub_orders = db.session.query(Order.order_id).filter(and_(*conds)).subquery()

    # 大类 -> type_id 集
    sel_type_ids = CAT_LABEL_TO_TYPE_IDS.get(material_cat, None)  # None 表示不限

    # -------- A) usage_count / top_category（PII侧：按 Material.material_type_id 过滤；忽略 H）--------
    q_raw = (
        db.session.query(
            Supplier.supplier_id.label("supplier_id"),
            Supplier.supplier_name.label("supplier_name"),
            ProductionInstruction.production_instruction_id.label("pi_id"),
            OrderShoe.order_id.label("order_id"),
            ProductionInstructionItem.material_type.label("mtype"),  # H 判断仍需
            Material.material_type_id.label("type_id"),  # 用于大类过滤与统计
        )
        .join(Material, Material.material_id == ProductionInstructionItem.material_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .join(
            ProductionInstruction,
            ProductionInstruction.production_instruction_id
            == ProductionInstructionItem.production_instruction_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == ProductionInstruction.order_shoe_id)
        .join(sub_orders, sub_orders.c.order_id == OrderShoe.order_id)
    )
    if sel_type_ids:
        q_raw = q_raw.filter(Material.material_type_id.in_(sel_type_ids))

    rows = q_raw.all()
    if not rows:
        return jsonify({"rows": [], "total": 0})

    supplier_pi_set = defaultdict(set)  # sid -> set(pi_id)
    supplier_cat_cnt = defaultdict(lambda: defaultdict(int))  # sid -> {大类名: 次数}
    name_of = {}

    for sid, sname, pi_id, _, mtype, type_id in rows:
        # 忽略 H 类（不计usage/top_category）
        if mtype == "H":
            continue
        name_of[sid] = sname
        if pi_id:
            supplier_pi_set[sid].add(pi_id)
        cat_name = TYPE_ID_TO_LABEL.get(type_id, "未知")
        supplier_cat_cnt[sid][cat_name] += 1

    # 统计 top_category（在过滤后数据上）
    top_cat_of = {}
    for sid, cnt_map in supplier_cat_cnt.items():
        if cnt_map:
            top_cat_of[sid] = max(cnt_map.items(), key=lambda kv: kv[1])[0]

    valid_supplier_ids = [sid for sid in name_of.keys() if top_cat_of.get(sid)]
    if not valid_supplier_ids:
        return jsonify({"rows": [], "total": 0})

    # -------- B) related_gmv（MS 侧：Material.material_type_id 过滤）--------
    # 说明：GMV = sum(unit_price * inbound_amount)（基于 MaterialStorage）
    ms_q = (
        db.session.query(
            Supplier.supplier_id.label("supplier_id"),
            func.sum(
                (MaterialStorage.unit_price * MaterialStorage.inbound_amount)
            ).label("amount_sum"),
        )
        .join(
            SPUMaterial, SPUMaterial.spu_material_id == MaterialStorage.spu_material_id
        )
        .join(Material, Material.material_id == SPUMaterial.material_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .join(sub_orders, sub_orders.c.order_id == MaterialStorage.order_id)
        .group_by(Supplier.supplier_id)
    )
    if sel_type_ids:
        ms_q = ms_q.filter(Material.material_type_id.in_(sel_type_ids))

    ms_amount_map = {sid: (amt or 0) for sid, amt in ms_q.all()}

    # -------- 组装 + 排序分页 --------
    items = []
    for sid in valid_supplier_ids:
        usage_count = len(supplier_pi_set.get(sid, ()))
        # 注意：amount_sum 已在 SQL 层求和，这里转 Decimal 后量化
        related_gmv = Decimal(str(ms_amount_map.get(sid, 0)))
        items.append(
            {
                "supplier_id": sid,
                "supplier_name": name_of.get(sid, f"供应商{sid}"),
                "usage_count": usage_count,
                "related_gmv": float(related_gmv.quantize(Decimal("0.01"))),
                "top_category": top_cat_of.get(sid),
            }
        )

    key_field = "usage_count" if metric == "usage_count" else "related_gmv"
    items.sort(key=lambda r: r.get(key_field, 0), reverse=True)

    total = len(items)
    start = (page - 1) * size
    return jsonify({"rows": items[start : start + size], "total": total})


# ===== /businessanalysis/top/shoes =====
@business_analysis_bp.route("/businessanalysis/top/shoes", methods=["GET"])
def ba_top_shoes():
    """
    metric = count | avg_unit_price | gmv | gross_profit
    - count: OrderShoe 行计数
    - avg_unit_price: 所有 OST 单价(RMB) 的均值
    - gmv: 按 batch 数量 * OST 单价(RMB)
    - gross_profit: 订单成本按订单内的“鞋型 GMV 占比”进行分摊
    """
    date_from = parse_date(request.args.get("date_from", ""))
    date_to = parse_date(request.args.get("date_to", ""))
    status = request.args.get("status", type=str)
    metric = request.args.get("metric", default="count", type=str)
    page = max(1, request.args.get("page", default=1, type=int))
    size = max(1, min(200, request.args.get("size", default=10, type=int)))

    conds = _order_filters(date_from, date_to, status)
    sub_orders = db.session.query(Order.order_id).filter(and_(*conds)).subquery()

    # A) count：按鞋型（shoe_rid）次数（OrderShoe 行数）
    q_cnt = (
        db.session.query(
            func.coalesce(Shoe.shoe_rid, "（未命名）").label("rid"),
            func.count(OrderShoe.order_shoe_id).label("cnt"),
        )
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id, isouter=True)
        .join(sub_orders, sub_orders.c.order_id == OrderShoe.order_id)
        .group_by(func.coalesce(Shoe.shoe_rid, "（未命名）"))
    )
    count_map = {r.rid: int(r.cnt or 0) for r in q_cnt.all()}

    # B) avg_unit_price：聚合所有 OST 单价（RMB）
    q_price = (
        db.session.query(
            func.coalesce(Shoe.shoe_rid, "（未命名）").label("rid"),
            OrderShoeType.unit_price,
            OrderShoeType.currency_type,
        )
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id, isouter=True)
        .join(sub_orders, sub_orders.c.order_id == OrderShoe.order_id)
    )
    sum_price_map, num_price_map = defaultdict(lambda: Decimal("0.00")), defaultdict(
        int
    )
    for rid, price, cur in q_price.all():
        if price is None:
            continue
        sum_price_map[rid] += to_rmb(Decimal(str(price)), cur)
        num_price_map[rid] += 1

    # C) gmv：按 batch × 单价（RMB）汇总到鞋型 + 记录每订单内各鞋型 GMV（用于成本分摊）
    q_gmv = (
        db.session.query(
            func.coalesce(Shoe.shoe_rid, "（未命名）").label("rid"),
            OrderShoe.order_id.label("oid"),
            OrderShoeType.unit_price,
            OrderShoeType.currency_type,
            OrderShoeBatchInfo.total_amount,
        )
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id, isouter=True)
        .join(sub_orders, sub_orders.c.order_id == OrderShoe.order_id)
    )
    gmv_by_rid = defaultdict(lambda: Decimal("0.00"))
    gmv_by_order_rid = defaultdict(lambda: Decimal("0.00"))  # key: (oid,rid)
    gmv_by_order_total = defaultdict(lambda: Decimal("0.00"))
    for rid, oid, unit_price, cur, amt in q_gmv.all():
        if unit_price is None or amt is None:
            continue
        part = to_rmb(Decimal(str(unit_price)), cur) * Decimal(int(amt))
        gmv_by_rid[rid] += part
        gmv_by_order_rid[(oid, rid)] += part
        gmv_by_order_total[oid] += part

    # D) 订单成本 -> 分摊到鞋型
    order_ids = list(gmv_by_order_total.keys())
    cost_map = _order_cost_map(order_ids)
    cost_by_rid = defaultdict(lambda: Decimal("0.00"))
    for oid, order_total_gmv in gmv_by_order_total.items():
        if order_total_gmv <= 0:
            continue
        order_cost = cost_map.get(oid, Decimal("0.00"))
        # 分摊
        for (k_oid, rid), rid_gmv in list(gmv_by_order_rid.items()):
            if k_oid != oid:
                continue
            share = (rid_gmv / order_total_gmv) * order_cost
            cost_by_rid[rid] += share

    # 组装
    items = []
    all_rids = (
        set(count_map.keys()) | set(sum_price_map.keys()) | set(gmv_by_rid.keys())
    )
    for rid in all_rids:
        cnt = count_map.get(rid, 0)
        avg_price = None
        if num_price_map[rid] > 0:
            avg_price = float(
                (sum_price_map[rid] / Decimal(num_price_map[rid])).quantize(
                    Decimal("0.01")
                )
            )
        gmv_val = gmv_by_rid.get(rid, Decimal("0.00")).quantize(Decimal("0.01"))
        cost_val = cost_by_rid.get(rid, Decimal("0.00")).quantize(Decimal("0.01"))
        gp_val = (gmv_val - cost_val).quantize(Decimal("0.01"))
        items.append(
            {
                "shoe_type": rid,
                "count": cnt,
                "avg_unit_price": avg_price,
                "gmv": float(gmv_val),
                "gross_profit": float(gp_val),
            }
        )

    # 排序 + 分页
    key_field = metric

    def keyf(r):
        v = r.get(key_field)
        return (-1e18) if v is None else float(v)

    items.sort(key=lambda r: keyf(r), reverse=True)

    total = len(items)
    start = (page - 1) * size
    rows = items[start : start + size]
    return jsonify({"rows": rows, "total": total})


@business_analysis_bp.route("/businessanalysis/orders/series", methods=["GET"])
def ba_series_orders():
    """
    订单数量 + 下单鞋数量 时间分布（按 start_date）
    Query:
      - date_from=YYYY-MM-DD（可选）
      - date_to=YYYY-MM-DD（可选）
      - status=...（可选）
      - agg=day|week|month（默认 week）
    Return:
      {
        "rows": [
          { "date": "YYYY-MM-DD", "count": 12, "order_count": 12, "shoe_count": 360 },
          ...
        ]
      }
      - day:     date = 当天
      - week:    date = 该周周内最早的自然日（等同于周一）
      - month:   date = 当月第一天
    """
    agg = (request.args.get("agg") or "week").lower()
    date_from = parse_date(request.args.get("date_from", ""))
    date_to = parse_date(request.args.get("date_to", ""))
    status = request.args.get("status", type=str)

    conds = _order_filters(date_from, date_to, status)
    conds.append(Order.start_date.isnot(None))

    # —— 订单数分桶 —— #
    order_rows = []
    if agg == "day":
        bucket = func.date(Order.start_date).label("bucket")
        q = (
            db.session.query(bucket, func.count(Order.order_id).label("cnt"))
            .filter(and_(*conds))
            .group_by(bucket)
            .order_by(bucket.asc())
        )
        order_rows = [(str(b), int(c)) for b, c in q.all()]

    elif agg == "month":
        bucket = func.date_format(Order.start_date, "%Y-%m-01").label("bucket")
        q = (
            db.session.query(bucket, func.count(Order.order_id).label("cnt"))
            .filter(and_(*conds))
            .group_by(bucket)
            .order_by(bucket.asc())
        )
        order_rows = [(b, int(c)) for b, c in q.all()]

    else:
        # week：以该分组内最早自然日作为标签（基本等于周一）
        year_col = func.year(Order.start_date)
        week_col = func.week(Order.start_date, 3)
        week_start = func.min(func.date(Order.start_date)).label("week_start")
        q = (
            db.session.query(
                week_start,
                year_col.label("yy"),
                week_col.label("ww"),
                func.count(Order.order_id).label("cnt"),
            )
            .filter(and_(*conds))
            .group_by(year_col, week_col)
            .order_by(week_start.asc())
        )
        order_rows = [(str(ws), int(c)) for ws, _yy, _ww, c in q.all()]

    # —— 下单鞋数量分桶（sum(batch.total_amount)） —— #
    shoes_rows = []
    if agg == "day":
        bucket = func.date(Order.start_date).label("bucket")
        q = (
            db.session.query(
                bucket,
                func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label("amt"),
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(and_(*conds))
            .group_by(bucket)
            .order_by(bucket.asc())
        )
        shoes_rows = [(str(b), int(a or 0)) for b, a in q.all()]

    elif agg == "month":
        bucket = func.date_format(Order.start_date, "%Y-%m-01").label("bucket")
        q = (
            db.session.query(
                bucket,
                func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label("amt"),
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(and_(*conds))
            .group_by(bucket)
            .order_by(bucket.asc())
        )
        shoes_rows = [(b, int(a or 0)) for b, a in q.all()]

    else:
        # week：与订单数同分组键
        year_col = func.year(Order.start_date)
        week_col = func.week(Order.start_date, 3)
        week_start = func.min(func.date(Order.start_date)).label("week_start")
        q = (
            db.session.query(
                week_start,
                year_col.label("yy"),
                week_col.label("ww"),
                func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label(
                    "amt"
                ),
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(and_(*conds))
            .group_by(year_col, week_col)
            .order_by(week_start.asc())
        )
        shoes_rows = [(str(ws), int(a or 0)) for ws, _yy, _ww, a in q.all()]

    # —— 合并两个序列到同一时间轴 —— #
    order_map = {d: c for d, c in order_rows}
    shoes_map = {d: c for d, c in shoes_rows}
    all_dates = sorted(set(order_map.keys()) | set(shoes_map.keys()))
    rows = []
    for d in all_dates:
        oc = int(order_map.get(d, 0))
        sc = int(shoes_map.get(d, 0))
        rows.append(
            {"date": d, "count": oc, "order_count": oc, "shoe_count": sc}
        )

    return jsonify({"rows": rows}), 200

@business_analysis_bp.route("/businessanalysis/production/series", methods=["GET"])
def ba_series_in_production():
    agg = (request.args.get("agg") or "week").lower()
    date_from = parse_date(request.args.get("date_from", ""))
    date_to = parse_date(request.args.get("date_to", ""))
    status = request.args.get("status", type=str)

    OSP = OrderShoeProductionInfo
    OS  = OrderShoe

    # 订单范围（与你现有风格一致）
    conds = _order_filters(date_from, date_to, status)
    sub_orders = db.session.query(Order.order_id).filter(and_(*conds)).subquery()

    # === 关键：为每个 order_shoe_id 预计算总双数（汇总所有 OST -> Batch 的 total_amount）===
    qty_sub = (
        db.session.query(
            OS.order_shoe_id.label("osid"),
            func.coalesce(func.sum(OrderShoeBatchInfo.total_amount), 0).label("qty")
        )
        .select_from(OS)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OS.order_shoe_id)
        .join(OrderShoeBatchInfo, OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .group_by(OS.order_shoe_id)
        .subquery()
    )

    # === 根据 agg 生成时间桶 ===
    buckets = []
    if agg == "day":
        q = (
            db.session.query(func.date(Order.start_date).label("d"))
            .filter(and_(*conds, Order.start_date.isnot(None)))
            .group_by(func.date(Order.start_date))
            .order_by(func.date(Order.start_date))
        )
        for (d,) in q.all():
            # 当天 [d, d+1)
            b_start = d
            b_end   = d + timedelta(days=1)
            buckets.append((b_start, b_end, str(d)))
    elif agg == "month":
        q = (
            db.session.query(func.date_format(Order.start_date, "%Y-%m-01").label("m"))
            .filter(and_(*conds, Order.start_date.isnot(None)))
            .group_by(func.date_format(Order.start_date, "%Y-%m-01"))
            .order_by(func.date_format(Order.start_date, "%Y-%m-01"))
        )
        for (m,) in q.all():
            # 当月第一天 -> 下月第一天
            b_start = datetime.strptime(m, "%Y-%m-%d").date()
            if b_start.month == 12:
                b_end = b_start.replace(year=b_start.year + 1, month=1, day=1)
            else:
                b_end = b_start.replace(month=b_start.month + 1, day=1)
            buckets.append((b_start, b_end, m))
    else:
        # week：用最小日期作为周起（你前面 orders/series 的方式）
        year_col = func.year(Order.start_date)
        week_col = func.week(Order.start_date, 3)
        week_start = func.min(func.date(Order.start_date)).label("week_start")
        q = (
            db.session.query(week_start, year_col, week_col)
            .filter(and_(*conds, Order.start_date.isnot(None)))
            .group_by(year_col, week_col)
            .order_by(week_start.asc())
        )
        for (ws, _yy, _ww) in q.all():
            b_start = ws
            b_end   = ws + timedelta(days=7)
            buckets.append((b_start, b_end, str(ws)))

    rows = []
    for (b_start, b_end, label) in buckets:
        # 与生产期重叠：cutting_start_date < bucket_end 且 (molding_end_date IS NULL 或 >= bucket_start)
        time_overlaps = and_(
            OSP.cutting_start_date < b_end,
            or_(OSP.molding_end_date.is_(None), OSP.molding_end_date >= b_start),
        )

        # 在产订单数：distinct order_id
        q_order = (
            db.session.query(func.count(distinct(OS.order_id)))
            .select_from(OSP)
            .join(OS, OS.order_shoe_id == OSP.order_shoe_id)
            .join(sub_orders, sub_orders.c.order_id == OS.order_id)
            .filter(time_overlaps)
        )

        # 在产鞋总双数：关联 qty_sub，汇总 qty
        q_shoe_pairs = (
            db.session.query(func.coalesce(func.sum(qty_sub.c.qty), 0))
            .select_from(OSP)
            .join(OS, OS.order_shoe_id == OSP.order_shoe_id)
            .join(sub_orders, sub_orders.c.order_id == OS.order_id)
            .outerjoin(qty_sub, qty_sub.c.osid == OSP.order_shoe_id)
            .filter(time_overlaps)
        )

        rows.append({
            "date": label,
            "order_in_prod": int(q_order.scalar() or 0),
            "shoe_pairs_in_prod": int(q_shoe_pairs.scalar() or 0),
        })

    return jsonify({"rows": rows}), 200



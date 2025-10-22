from flask import Blueprint, request, jsonify
from sqlalchemy import and_, func, distinct, case
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from collections import defaultdict
from models import db, Order, OrderShoe, OrderShoeType, Customer, OrderShoeBatchInfo, MaterialStorage, Shoe, OrderShoeProductionInfo, ProductionInstruction, ProductionInstructionItem, Supplier, Material

customer_analysis_bp = Blueprint('customer_analysis', __name__)
MAT_TYPE_LABEL = {
    "S": "面料",
    "I": "里料",
    "A": "辅料",
    "O": "大底",
    "M": "中底"
}
# 简单汇率表（按 2025 年常见均值）
CURRENCY_RATE = {
    "RMB": Decimal("1.00"),
    "CNY": Decimal("1.00"),
    "USD": Decimal("7.20"),
    "USA": Decimal("7.20"),   # 兼容写法
    "EUR": Decimal("7.80"),
    None:  Decimal("1.00"),
}
def quantile_float(vals, q: float):
    if not vals:
        return None
    a = sorted(vals)
    n = len(a)
    pos = (n - 1) * q
    base = int(pos)
    rest = pos - base
    if base + 1 < n:
        return a[base] + rest * (a[base + 1] - a[base])
    return a[base]

def parse_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def to_rmb(amount: Decimal, currency: str) -> Decimal:
    rate = CURRENCY_RATE.get(currency, Decimal("1.00"))
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def quantile(vals, q: float):
    """线性插值分位数（输入：float list）"""
    n = len(vals)
    if n == 0:
        return None
    a = sorted(vals)
    pos = (n - 1) * q
    base = int(pos)
    rest = pos - base
    if base + 1 < n:
        return a[base] + rest * (a[base + 1] - a[base])
    return a[base]

def compute_kpis(values_float):
    """可选：KPI 返回（订单数、P50、P90）"""
    if not values_float:
        return {"order_count": 0, "unit_price_p50": None, "unit_price_p90": None}
    p50 = quantile(values_float, 0.5)
    p90 = quantile(values_float, 0.9)
    return {
        "order_count": len(values_float),
        "unit_price_p50": float(Decimal(str(p50)).quantize(Decimal("0.01"))) if p50 is not None else None,
        "unit_price_p90": float(Decimal(str(p90)).quantize(Decimal("0.01"))) if p90 is not None else None,
    }

def _range_filters(date_from, date_to, status):
    filt = []
    if status:
        filt.append(Order.status == status)
    if date_from:
        filt.append(Order.start_date >= date_from)
    if date_to:
        filt.append(Order.start_date <= date_to)
    return filt

def _fetch_prices_by_customer_ids(customer_ids, base_filters):
    """给定一组 customer_id，返回这些客户所有鞋型单价（已转 RMB）的列表（list[float])。"""
    if not customer_ids:
        return []
    q = (
        db.session.query(OrderShoeType.unit_price, OrderShoeType.currency_type)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .filter(and_(Order.customer_id.in_(customer_ids), *base_filters))
    )
    prices = []
    for price, currency in q.all():
        if price is None:
            continue
        prices.append(float(to_rmb(Decimal(str(price)), currency)))
    return prices

def _fetch_compare_series_by_customer_ids(compare_ids, base_filters, label_by='brand'):
    """
    组装对比序列：
    - label_by='brand'：按品牌（customer_id）输出 label => '客户名-品牌' 或 仅客户名/品牌
    - label_by='name' ：按客户名聚合，序列名为客户名
    返回：list[{"customer": str, "unit_prices": list[float]}]
    """
    if not compare_ids:
        return []

    rows = (
        db.session.query(
            Order.customer_id,
            Customer.customer_name,
            Customer.customer_brand,
            OrderShoeType.unit_price,
            OrderShoeType.currency_type
        )
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(and_(Order.customer_id.in_(compare_ids), *base_filters))
    ).all()

    if label_by == 'name':
        # 按客户名聚合
        agg_by_name = defaultdict(list)
        for cid, cname, cbrand, price, cur in rows:
            if price is None:
                continue
            agg_by_name[cname or f"客户{cid}"].append(float(to_rmb(Decimal(str(price)), cur)))
        return [{"customer": name, "unit_prices": plist} for name, plist in agg_by_name.items()]

    # 默认：按品牌（ID）逐个 series
    agg_by_id = defaultdict(list)
    name_map = {}
    brand_map = {}
    for cid, cname, cbrand, price, cur in rows:
        if price is None:
            continue
        agg_by_id[cid].append(float(to_rmb(Decimal(str(price)), cur)))
        name_map[cid] = cname
        brand_map[cid] = cbrand

    series = []
    for cid, plist in agg_by_id.items():
        label = name_map.get(cid) or f"客户{cid}"
        if brand_map.get(cid):
            # 如果有品牌，拼合下更清晰
            label = f"{label}-{brand_map[cid]}"
        series.append({"customer": label, "unit_prices": plist})
    return series
def _resolve_customer_ids(scope: str, customer_name: str, customer_id: int):
    """
    返回主查询所涉及的 customer_id 列表，以及显示用的主显示名。
    scope=name  => 所有同名客户 id 列表
    scope=brand => 单一 id 列表
    """
    if scope == "name":
        if not customer_name:
            return [], None
        ids = [cid for (cid,) in db.session.query(Customer.customer_id)
               .filter(Customer.customer_name == customer_name).all()]
        return ids, customer_name
    # brand
    if not customer_id:
        return [], None
    row = db.session.query(Customer.customer_name, Customer.customer_brand)\
                    .filter(Customer.customer_id == customer_id).first()
    display = None
    if row:
        display = row.customer_name if not row.customer_brand else f"{row.customer_name}-{row.customer_brand}"
    return [customer_id], display
@customer_analysis_bp.route("/customeranalysis/unitpricegraph", methods=["GET"])
def get_unit_price_graph():
    """
    支持两种模式：
    - scope='name':  主 customerName=xxx， 对比 compareCustomerNames[]=a&compareCustomerNames[]=b
      （将同名的所有 customer_id 一并聚合） 
    - scope='brand': 主 customerId=1，    对比 compareCustomerIds[]=2&compareCustomerIds[]=3
      （单品牌/商标维度）

    兼容：若 scope 缺省，会根据参数自动推断：
      - 有 customerName => 视为 name
      - 否则 => brand
    """
    scope = request.args.get("scope", type=str)
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)
    compare_names = request.args.getlist("compareCustomerNames[]") or request.args.getlist("compareCustomerNames")
    compare_ids   = request.args.getlist("compareCustomerIds[]", type=int) or request.args.getlist("compareCustomerIds", type=int)

    # 统一时间/状态过滤
    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)
    base_filters = _range_filters(date_from, date_to, status)

    # 自动推断 scope
    if not scope:
        scope = "name" if customer_name else "brand"

    # ====== 主序列 ======
    primary_prices = []
    primary_kpis = None

    if scope == "name":
        if not customer_name:
            return jsonify({"error": "customerName is required for scope=name"}), 400
        # 找到该客户名下的所有 customer_id
        ids = [cid for (cid,) in db.session.query(Customer.customer_id)
               .filter(Customer.customer_name == customer_name).all()]
        if ids:
            primary_prices = _fetch_prices_by_customer_ids(ids, base_filters)
        primary_kpis = compute_kpis(primary_prices)

        # 对比（按“客户名聚合”）
        compare_series = []
        if compare_names:
            all_ids = []
            name_to_ids = {}
            for nm in compare_names:
                cids = [cid for (cid,) in db.session.query(Customer.customer_id)
                        .filter(Customer.customer_name == nm).all()]
                if cids:
                    name_to_ids[nm] = cids
                    all_ids.extend(cids)

            # 直接用按 name 聚合的逻辑
            compare_series = []
            if all_ids:
                rows = (
                    db.session.query(
                        Order.customer_id,
                        Customer.customer_name,
                        OrderShoeType.unit_price,
                        OrderShoeType.currency_type
                    )
                    .join(Customer, Customer.customer_id == Order.customer_id)
                    .join(OrderShoe, Order.order_id == OrderShoe.order_id)
                    .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
                    .filter(and_(Order.customer_id.in_(all_ids), *base_filters))
                ).all()

                # 聚合到客户名
                temp = defaultdict(list)
                for cid, cname, price, cur in rows:
                    if price is None:
                        continue
                    temp[cname or f"客户{cid}"].append(float(to_rmb(Decimal(str(price)), cur)))

                # 只保留用户请求的 compare_names 的序列，顺序也可与请求一致
                for nm in compare_names:
                    plist = temp.get(nm, [])
                    compare_series.append({"customer": nm, "unit_prices": plist})

        result = {
            "primary": {"unit_prices": primary_prices, "kpis": primary_kpis},
            "compare": {"unit_prices": compare_series}
        }
        return jsonify(result), 200

    # scope == 'brand'
    if not customer_id:
        return jsonify({"error": "customerId is required for scope=brand"}), 400

    # 主：单品牌
    primary_prices = _fetch_prices_by_customer_ids([customer_id], base_filters)
    primary_kpis = compute_kpis(primary_prices)

    # 对比：多品牌
    compare_series = _fetch_compare_series_by_customer_ids(compare_ids, base_filters, label_by='brand')

    result = {
        "primary": {"unit_prices": primary_prices, "kpis": primary_kpis},
        "compare": {"unit_prices": compare_series}
    }
    return jsonify(result), 200

@customer_analysis_bp.route("/customeranalysis/kpis", methods=["GET"])
def get_kpis():
    """
    KPI 汇总接口（含成本计算）
    scope=name + customerName=xxx  -> 聚合同名多品牌
    scope=brand + customerId=xxx   -> 单品牌
    """
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)

    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)
    base_filters = _range_filters(date_from, date_to, status)

    customer_ids, display_name = _resolve_customer_ids(scope, customer_name, customer_id)
    if not customer_ids:
        return jsonify({"error": "invalid customer scope/identifier"}), 400

    # ========= 获取订单 =========
    orders = db.session.query(Order).filter(and_(Order.customer_id.in_(customer_ids), *base_filters)).all()
    order_ids = [o.order_id for o in orders]
    order_count = len(set(order_ids))

    # ========= 单价分布（转 RMB） =========
    ust_q = (
        db.session.query(OrderShoeType.unit_price, OrderShoeType.currency_type)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .filter(Order.order_id.in_(order_ids))
    )
    unit_prices_rmb = []
    for price, cur in ust_q.all():
        if price is not None:
            unit_prices_rmb.append(float(to_rmb(Decimal(str(price)), cur)))

    median_unit_price = quantile_float(unit_prices_rmb, 0.5)
    p90_unit_price    = quantile_float(unit_prices_rmb, 0.9)

    # ========= 耗时 =========
    lead_days = []
    ontime_numer = 0
    ontime_denom = 0
    for o in orders:
        if o.start_date and o.order_actual_end_date:
            days = (o.order_actual_end_date - o.start_date).days
            lead_days.append(days)
            if o.end_date:
                ontime_denom += 1
                if o.order_actual_end_date <= o.end_date:
                    ontime_numer += 1
    median_lead_days = quantile_float(lead_days, 0.5)
    on_time_rate = (ontime_numer / ontime_denom) if ontime_denom > 0 else None

    # ========= 销售金额（GMV） =========
    batch_q = (
        db.session.query(
            OrderShoeBatchInfo.order_shoe_type_id,
            OrderShoeBatchInfo.total_amount,
            OrderShoeType.unit_price,
            OrderShoeType.currency_type,
        )
        .join(OrderShoeType, OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .filter(Order.order_id.in_(order_ids))
    )

    amount_by_type = defaultdict(int)
    price_by_type_rmb = {}
    for type_id, total_amount, unit_price, cur in batch_q.all():
        amt = int(total_amount or 0)
        amount_by_type[type_id] += amt
        if unit_price is not None:
            price_by_type_rmb[type_id] = to_rmb(Decimal(str(unit_price)), cur)

    gmv = Decimal("0.00")
    for type_id, qty in amount_by_type.items():
        price_rmb = price_by_type_rmb.get(type_id)
        if price_rmb and qty > 0:
            gmv += (price_rmb * Decimal(qty))
    gmv = gmv.quantize(Decimal("0.01"))

    # ========= 成本（来自 material_storage） =========
    # 成本 = sum(unit_price * inbound_amount)
    ms_q = (
        db.session.query(MaterialStorage.unit_price, MaterialStorage.inbound_amount)
        .filter(MaterialStorage.order_id.in_(order_ids))
    )
    total_cost = Decimal("0.00")
    for unit_price, inbound_amount in ms_q.all():
        if unit_price is None or inbound_amount is None:
            continue
        cost = Decimal(str(unit_price)) * Decimal(str(inbound_amount))
        total_cost += cost
    total_cost = total_cost.quantize(Decimal("0.01"))

    # ========= 毛利 & 毛利率 =========
    gross_profit = (gmv - total_cost).quantize(Decimal("0.01"))
    gross_margin = float((gross_profit / gmv).quantize(Decimal("0.0001"))) if gmv > 0 else None

    # ========= 返回 =========
    kpis = {
        "order_count": order_count,
        "median_unit_price": float(median_unit_price or 0),
        "p90_unit_price": float(p90_unit_price or 0),
        "median_lead_days": int(median_lead_days or 0),
        "on_time_rate": float(on_time_rate or 0),
        "gmv": float(gmv),
        "total_cost": float(total_cost),
        "gross_profit": float(gross_profit),
        "gross_margin": gross_margin,
        "display": display_name,
        "scope": scope,
    }
    return jsonify({"primary": {"kpis": kpis}}), 200

@customer_analysis_bp.route("/customeranalysis/designerdistribution", methods=["GET"])
def designer_distribution():
    """
    设计师分布（主客户）
    - 通过 OrderShoe.shoe_id -> Shoe.shoe_id -> Shoe.shoe_designer 统计次数
    - 支持 scope=name/brand，日期、状态过滤
    - 可选 top_n 截断
    """
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)

    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)
    top_n     = request.args.get("top_n", type=int)

    base_filters = _range_filters(date_from, date_to, status)

    # 解析客户 ID 列表（同名聚合 or 单一品牌）
    customer_ids, display_name = _resolve_customer_ids(scope, customer_name, customer_id)
    if not customer_ids:
        return jsonify({"error": "invalid customer scope/identifier"}), 400

    # 先筛出订单（符合过滤条件 + 属于这些客户）
    orders_subq = (
        db.session.query(Order.order_id)
        .filter(and_(Order.customer_id.in_(customer_ids), *base_filters))
        .subquery()
    )

    # 连接 OrderShoe -> Shoe，基于订单集合统计设计师出现次数
    # 注意：Shoe 可能为 NULL（极端数据），使用外连接并将 None 合并到 "（未填写）"
    q = (
        db.session.query(
            func.coalesce(Shoe.shoe_designer, "（未填写）").label("designer"),
            func.count(OrderShoe.order_shoe_id).label("cnt")
        )
        .join(orders_subq, orders_subq.c.order_id == OrderShoe.order_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .group_by(func.coalesce(Shoe.shoe_designer, "（未填写）"))
        .order_by(func.count(OrderShoe.order_shoe_id).desc())
    )

    rows = q.all()
    if top_n and top_n > 0:
        rows = rows[:top_n]

    # 汇总总次数
    total_cnt = sum(int(r.cnt or 0) for r in rows)

    designers = [
        {"designer": r.designer, "count": int(r.cnt or 0)}
        for r in rows
    ]

    result = {
        "primary": {
            "designers": designers,
            "total": total_cnt,
            "display": display_name,
            "scope": scope
        }
    }
    return jsonify(result), 200

@customer_analysis_bp.route("/customeranalysis/topshoetypes", methods=["GET"])
def top_shoe_types():
    """
    最常用鞋型（Shoe 使用次数）
    - 统计口径：OrderShoe 行数（通过 Order 过滤客户、时间、状态；通过 Shoe 取 shoe_rid）
    - 支持 scope=name/brand
    - 支持可选对比 compareCustomerIds[]
    - 返回：primary.shoes: [{shoe_type, count}], total；compare 可选
    """
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)

    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)
    top_n     = request.args.get("top_n", type=int) or 15

    # 对比客户（brand 模式下常用，也允许在 name 模式下做其他名字/品牌的对比）
    compare_ids = request.args.getlist("compareCustomerIds[]", type=int)
    if not compare_ids:
        compare_ids = request.args.getlist("compareCustomerIds", type=int)

    base_filters = _range_filters(date_from, date_to, status)

    # 解析主客户 ID 列表
    primary_ids, display = _resolve_customer_ids(scope, customer_name, customer_id)
    if not primary_ids:
        return jsonify({"error": "invalid customer scope/identifier"}), 400

    # —— Primary：先筛出订单，再关联 OrderShoe -> Shoe，按 shoe_id 计数 ——
    orders_primary_sq = (
        db.session.query(Order.order_id)
        .filter(and_(Order.customer_id.in_(primary_ids), *base_filters))
        .subquery()
    )

    q_primary = (
        db.session.query(
            func.coalesce(Shoe.shoe_rid, "（未命名）").label("shoe_rid"),
            func.count(OrderShoe.order_shoe_id).label("cnt")
        )
        .join(orders_primary_sq, orders_primary_sq.c.order_id == OrderShoe.order_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .group_by(func.coalesce(Shoe.shoe_rid, "（未命名）"))
        .order_by(func.count(OrderShoe.order_shoe_id).desc())
    )
    rows_p = q_primary.all()
    total_p = sum(int(r.cnt or 0) for r in rows_p)
    shoes_p = [
        {"shoe_type": r.shoe_rid, "count": int(r.cnt or 0)}
        for r in rows_p[:top_n]
    ]

    result = {
        "primary": {
            "shoes": shoes_p,
            "total": total_p,
            "display": display,
            "scope": scope
        }
    }

    # —— Compare（可选）：每个 customer_id 单独统计 Top N ——
    if compare_ids:
        compare_list = []
        # 取对比客户名称便于显示
        name_map = {
            cid: (db.session.query(Customer.customer_name).filter(Customer.customer_id == cid).scalar() or f"客户{cid}")
            for cid in compare_ids
        }
        for cid in compare_ids:
            orders_cmp_sq = (
                db.session.query(Order.order_id)
                .filter(and_(Order.customer_id == cid, *base_filters))
                .subquery()
            )
            q_cmp = (
                db.session.query(
                    func.coalesce(Shoe.shoe_rid, "（未命名）").label("shoe_rid"),
                    func.count(OrderShoe.order_shoe_id).label("cnt")
                )
                .join(orders_cmp_sq, orders_cmp_sq.c.order_id == OrderShoe.order_id)
                .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
                .group_by(func.coalesce(Shoe.shoe_rid, "（未命名）"))
                .order_by(func.count(OrderShoe.order_shoe_id).desc())
            )
            rows_c = q_cmp.all()
            compare_list.append({
                "customer": name_map[cid],
                "shoes": [
                    {"shoe_type": r.shoe_rid, "count": int(r.cnt or 0)}
                    for r in rows_c[:top_n]
                ],
                "total": sum(int(r.cnt or 0) for r in rows_c)
            })
        result["compare"] = compare_list

    return jsonify(result), 200

@customer_analysis_bp.route("/customeranalysis/leadtimedistribution", methods=["GET"])
def leadtime_distribution():
    """
    生产耗时分布（客户维度 · 箱线图）
    通过 cutting_start_date 和 molding_end_date 相减得到耗时天数。
    支持 scope=name/brand、compareCustomerIds[] 对比。
    """
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)
    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)
    compare_ids = request.args.getlist("compareCustomerIds[]", type=int)
    if not compare_ids:
        compare_ids = request.args.getlist("compareCustomerIds", type=int)

    base_filters = _range_filters(date_from, date_to, status)

    # ========= 主客户 =========
    customer_ids, display = _resolve_customer_ids(scope, customer_name, customer_id)
    if not customer_ids:
        return jsonify({"error": "invalid customer scope/identifier"}), 400

    # 获取主客户 order_id
    order_subq = (
        db.session.query(Order.order_id)
        .filter(and_(Order.customer_id.in_(customer_ids), *base_filters))
        .subquery()
    )

    # 关联查询生产信息
    q_main = (
        db.session.query(
            OrderShoeProductionInfo.cutting_start_date,
            OrderShoeProductionInfo.molding_end_date
        )
        .join(OrderShoe, OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id)
        .join(order_subq, order_subq.c.order_id == OrderShoe.order_id)
    )

    lead_days_main = []
    for start, end in q_main.all():
        if start and end:
            delta = (end - start).days
            if delta >= 0:  # 过滤异常负数
                lead_days_main.append(delta)

    result = {
        "primary": {
            "customer": display,
            "lead_days": lead_days_main,
            "scope": scope,
            "count": len(lead_days_main)
        }
    }

    # ========= 对比客户 =========
    if compare_ids:
        compare_list = []
        name_map = {
            cid: (db.session.query(Customer.customer_name)
                  .filter(Customer.customer_id == cid)
                  .scalar() or f"客户{cid}")
            for cid in compare_ids
        }
        for cid in compare_ids:
            order_subq_cmp = (
                db.session.query(Order.order_id)
                .filter(and_(Order.customer_id == cid, *base_filters))
                .subquery()
            )
            q_cmp = (
                db.session.query(
                    OrderShoeProductionInfo.cutting_start_date,
                    OrderShoeProductionInfo.molding_end_date
                )
                .join(OrderShoe, OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id)
                .join(order_subq_cmp, order_subq_cmp.c.order_id == OrderShoe.order_id)
            )
            lead_days_cmp = []
            for start, end in q_cmp.all():
                if start and end:
                    d = (end - start).days
                    if d >= 0:
                        lead_days_cmp.append(d)
            compare_list.append({
                "customer": name_map[cid],
                "lead_days": lead_days_cmp,
                "count": len(lead_days_cmp)
            })
        result["compare"] = compare_list

    return jsonify(result), 200

def _get_customer_name_by_id(customer_id: int):
    c = db.session.query(Customer.customer_name).filter(Customer.customer_id == customer_id).first()
    return c[0] if c else None
def _base_order_filters(date_from, date_to, status):
    conds = []
    if status:
        # 这里按你系统真实字段调整；示例：Order.last_status / Order.status
        conds.append(Order.last_status == status)  # 如果你是另一个字段，请改这里
    if date_from:
        conds.append(Order.start_date >= date_from)
    if date_to:
        conds.append(Order.start_date <= date_to)
    return conds

def _expand_customer_ids_by_name(customer_name: str):
    if not customer_name:
        return []
    ids = db.session.query(Customer.customer_id).filter(Customer.customer_name == customer_name).all()
    return [i[0] for i in ids]
def _supplier_usage_query(customer_ids, date_from, date_to, status):
    """
    明细查询（不聚合）：
      customer_id, pi_id, supplier_id, supplier_name, mtype
    计数规则：COUNT(DISTINCT pi_id)
    """
    if not customer_ids:
        return None

    conds = [Order.customer_id.in_(customer_ids)]
    conds += _base_order_filters(date_from, date_to, status)

    q = (
        db.session.query(
            Order.customer_id.label("customer_id"),
            ProductionInstruction.production_instruction_id.label("pi_id"),
            Supplier.supplier_id.label("supplier_id"),
            Supplier.supplier_name.label("supplier_name"),
            ProductionInstructionItem.material_type.label("mtype")
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(ProductionInstruction, ProductionInstruction.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ProductionInstructionItem, ProductionInstructionItem.production_instruction_id == ProductionInstruction.production_instruction_id)
        .join(Material, Material.material_id == ProductionInstructionItem.material_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .filter(and_(*conds))
    )
    return q

def _aggregate_primary_by_category(q_raw):
    if q_raw is None:
        return {}
    sub = q_raw.subquery()
    rows = (
        db.session.query(
            sub.c.mtype, sub.c.supplier_id, sub.c.supplier_name,
            func.count(distinct(sub.c.pi_id)).label("usage_count")
        )
        .group_by(sub.c.mtype, sub.c.supplier_id, sub.c.supplier_name)
        .all()
    )

    by_cat = {}
    for mtype, sid, sname, cnt in rows:
        cat = MAT_TYPE_LABEL.get(mtype, mtype or "未知")
        by_cat.setdefault(cat, []).append({
            "supplier_id": sid,
            "supplier_name": sname,
            "usage_count": int(cnt or 0)
        })
    for cat in by_cat:
        by_cat[cat].sort(key=lambda x: x["usage_count"], reverse=True)
    return by_cat

def _aggregate_compare_by_category(q_raw):
    if q_raw is None:
        return {}

    sub = q_raw.subquery()
    rows = (
        db.session.query(
            sub.c.mtype, sub.c.supplier_id, sub.c.supplier_name,
            sub.c.customer_id,
            func.count(distinct(sub.c.pi_id)).label("usage_count")
        )
        .group_by(sub.c.mtype, sub.c.supplier_id, sub.c.supplier_name, sub.c.customer_id)
        .all()
    )

    name_map = dict(db.session.query(Customer.customer_id, Customer.customer_name).all())
    by_cat_map = {}
    for mtype, sid, sname, cid, cnt in rows:
        cat = MAT_TYPE_LABEL.get(mtype, mtype or "未知")
        by_cat_map.setdefault(cat, {})
        entry = by_cat_map[cat].setdefault(sid, {"supplier": sname, "counts": {}})
        cname = name_map.get(cid, f"客户{cid}")
        entry["counts"][cname] = int(cnt or 0)

    result = {}
    for cat, sup_map in by_cat_map.items():
        items = []
        for _, v in sup_map.items():
            total = sum(v["counts"].values())
            items.append({ "supplier": v["supplier"], "counts": v["counts"], "_total": total })
        items.sort(key=lambda x: x["_total"], reverse=True)
        for i in items:
            i.pop("_total", None)
        result[cat] = items

    return result

def _resolve_scope_to_ids(scope: str, customer_name: str, customer_id: int):
    """
    兼容前端两种模式：
      - scope='name'  -> 合并同名（传 customerName 或 customerId 反查）
      - scope='brand' -> 单商标（按 id）
    """
    if scope == "name":
        if not customer_name and customer_id:
            customer_name = _get_customer_name_by_id(customer_id)
        ids = _expand_customer_ids_by_name(customer_name) if customer_name else []
        return ids
    else:  # 'brand'
        return [customer_id] if customer_id else []

# === 路径兼容：/customeranalysis/supplierusage（前端使用） 与 /customeranalysis/supplier-usage（老路径）
@customer_analysis_bp.route("/customeranalysis/supplierusage", methods=["GET"])
def supplier_usage():
    """
    统计供应商使用次数（按材料类别拆分），一次计数 = 一个 PI 内同一 supplier 只算 1 次。
    前端参数（统一）：
      scope=name|brand
      // name 模式：
      customerName=xxx
      compareCustomerNames[]=a&compareCustomerNames[]=b
      // brand 模式：
      customerId=123
      compareCustomerIds[]=1&compareCustomerIds[]=2
      // 公共：
      date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&status=...

    返回：
    {
      "primary": { "by_category": { "面料":[{supplier_id, supplier_name, usage_count}], ... } },
      "compare": { "by_category": { "面料":[{"supplier":"X","counts":{"客户A":12,"客户B":7}}], ... } }
    }
    """
    scope = request.args.get("scope", "brand")   # name | brand
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)

    # 对比参数（两种模式都兼容）
    compare_names = request.args.getlist("compareCustomerNames[]", type=str) \
        or request.args.getlist("compareCustomerNames", type=str)
    compare_ids   = request.args.getlist("compareCustomerIds[]", type=int) \
        or request.args.getlist("compareCustomerIds", type=int)

    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)

    # 主体 customer_id 范围
    primary_ids = _resolve_scope_to_ids(scope, customer_name, customer_id)
    if not primary_ids:
        return jsonify({"primary": {"by_category": {}}, "compare": {"by_category": {}}}), 200

    # 主查询
    q_primary = _supplier_usage_query(primary_ids, date_from, date_to, status)
    primary_by_cat = _aggregate_primary_by_category(q_primary)

    # 对比
    compare_by_cat = {}
    if scope == "name" and compare_names:
        # 将同名列表展开为 id 列表
        comp_ids = []
        for nm in compare_names:
            comp_ids.extend(_resolve_scope_to_ids("name", nm, None))
        if comp_ids:
            q_compare = _supplier_usage_query(comp_ids, date_from, date_to, status)
            compare_by_cat = _aggregate_compare_by_category(q_compare)
    elif scope == "brand" and compare_ids:
        q_compare = _supplier_usage_query(compare_ids, date_from, date_to, status)
        compare_by_cat = _aggregate_compare_by_category(q_compare)

    return jsonify({"primary": {"by_category": primary_by_cat}, "compare": {"by_category": compare_by_cat}}), 200

@customer_analysis_bp.route("/customeranalysis/orders", methods=["GET"])
def orders_table():
    """
    列：订单号(order_rid)、鞋型(shoe_type)、设计师(designer)、单价(unit_price, RMB)、生产耗时(lead_days)、
        状态(status_name)、起止(start_end)
    支持分页：page,size
    过滤：scope=name/brand + customerName/customerId + 日期/状态
    """
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)
    page = max(1, request.args.get("page", type=int, default=1))
    size = max(1, min(200, request.args.get("size", type=int, default=20)))

    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)

    customer_ids, _ = _resolve_customer_ids(scope, customer_name, customer_id)
    if not customer_ids:
        return jsonify({"rows": [], "total": 0})

    base_filters = _range_filters(date_from, date_to, status)

    # 先筛订单
    q_order = db.session.query(Order).filter(and_(Order.customer_id.in_(customer_ids), *base_filters))

    total = q_order.count()

    # 分页后的订单 id
    orders_page = (
        q_order
        .order_by(
            case((Order.start_date.is_(None), 1), else_=0).asc(),  # 非空在前，空在后
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
    # 映射订单 -> (鞋型、设计师、单价、货币)
    rows_detail = (
        db.session.query(
            Order.order_id,
            func.coalesce(Shoe.shoe_rid, "（未命名）").label("shoe_rid"),
            func.coalesce(Shoe.shoe_designer, "（未填写）").label("designer"),
            OrderShoeType.unit_price,
            OrderShoeType.currency_type
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .outerjoin(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(Order.order_id.in_(order_ids))
        .all()
    )

    # 一个订单可能多个鞋款；这里取“第一条”为展示（也可以拼接多条）
    by_order = {}
    for oid, shoe_rid, designer, price, cur in rows_detail:
        if oid not in by_order:
            by_order[oid] = {
                "shoe_type": shoe_rid,
                "designer": designer,
                "unit_price": float(to_rmb(Decimal(str(price)), cur)) if price is not None else None
            }

    # 生产耗时
    prod_rows = (
        db.session.query(
            OrderShoe.order_id,
            OrderShoeProductionInfo.cutting_start_date,
            OrderShoeProductionInfo.molding_end_date
        )
        .join(OrderShoeProductionInfo, OrderShoe.order_shoe_id == OrderShoeProductionInfo.order_shoe_id)
        .filter(OrderShoe.order_id.in_(order_ids))
        .all()
    )
    lead_by_order = {}
    for oid, start, end in prod_rows:
        if start and end:
            d = (end - start).days
            if d >= 0:
                # 选择最小/最大/平均都可；这里取“最大”代表整体完工
                lead_by_order[oid] = max(d, lead_by_order.get(oid, 0))

    # 组装行
    rows = []
    for o in orders_page:
        meta = by_order.get(o.order_id, {})
        lead_days = lead_by_order.get(o.order_id)
        rows.append({
            "order_rid": getattr(o, "order_rid", o.order_id),
            "shoe_type": meta.get("shoe_type"),
            "designer": meta.get("designer"),
            "unit_price": meta.get("unit_price"),
            "lead_days": lead_days,
            "status_name": getattr(o, "status", None),
            "start_end": f"{o.start_date or ''} ~ {getattr(o, 'order_actual_end_date', None) or ''}"
        })

    return jsonify({"rows": rows, "total": total})

@customer_analysis_bp.route("/customeranalysis/designers-table", methods=["GET"])
def designers_table():
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)
    page = max(1, request.args.get("page", type=int, default=1))
    size = max(1, min(200, request.args.get("size", type=int, default=20)))
    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)

    customer_ids, _ = _resolve_customer_ids(scope, customer_name, customer_id)
    if not customer_ids:
        return jsonify({"rows": [], "total": 0})

    base_filters = _range_filters(date_from, date_to, status)

    orders_sq = (db.session.query(Order.order_id)
                 .filter(and_(Order.customer_id.in_(customer_ids), *base_filters))
                 .subquery())

    q = (
        db.session.query(
            func.coalesce(Shoe.shoe_designer, "（未填写）").label("designer"),
            func.count(OrderShoe.order_shoe_id).label("cnt")
        )
        .join(orders_sq, orders_sq.c.order_id == OrderShoe.order_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .group_by(func.coalesce(Shoe.shoe_designer, "（未填写）"))
        .order_by(func.count(OrderShoe.order_shoe_id).desc())
    )

    all_rows = q.all()
    total = len(all_rows)
    start = (page - 1) * size
    part = all_rows[start:start+size]

    sum_cnt = sum(int(r.cnt or 0) for r in all_rows) or 1
    rows = [{"designer": r.designer, "count": int(r.cnt or 0), "ratio": (int(r.cnt or 0) / sum_cnt)} for r in part]
    return jsonify({"rows": rows, "total": total})
@customer_analysis_bp.route("/customeranalysis/shoetypes-table", methods=["GET"])
def shoetypes_table():
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)
    page = max(1, request.args.get("page", type=int, default=1))
    size = max(1, min(200, request.args.get("size", type=int, default=20)))
    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)

    customer_ids, _ = _resolve_customer_ids(scope, customer_name, customer_id)
    if not customer_ids:
        return jsonify({"rows": [], "total": 0})

    base_filters = _range_filters(date_from, date_to, status)

    orders_sq = (db.session.query(Order.order_id)
                 .filter(and_(Order.customer_id.in_(customer_ids), *base_filters))
                 .subquery())

    # 次数
    q_cnt = (
        db.session.query(
            func.coalesce(Shoe.shoe_rid, "（未命名）").label("shoe_rid"),
            func.count(OrderShoe.order_shoe_id).label("cnt")
        )
        .join(orders_sq, orders_sq.c.order_id == OrderShoe.order_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .group_by(func.coalesce(Shoe.shoe_rid, "（未命名）"))
    )
    cnt_map = {r.shoe_rid: int(r.cnt or 0) for r in q_cnt.all()}

    # 平均单价（转 RMB）
    q_price = (
        db.session.query(
            func.coalesce(Shoe.shoe_rid, "（未命名）").label("shoe_rid"),
            OrderShoeType.unit_price, OrderShoeType.currency_type
        )
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(orders_sq, orders_sq.c.order_id == OrderShoe.order_id)
    )
    sum_map, num_map = {}, {}
    for rid, price, cur in q_price.all():
        if price is None: continue
        rmb = to_rmb(Decimal(str(price)), cur)
        sum_map[rid] = sum_map.get(rid, Decimal("0.00")) + rmb
        num_map[rid] = num_map.get(rid, 0) + 1

    items = []
    for rid, cnt in cnt_map.items():
        avg = None
        if num_map.get(rid):
            avg = float((sum_map[rid] / Decimal(num_map[rid])).quantize(Decimal("0.01")))
        items.append({"shoe_type": rid, "count": cnt, "avg_unit_price": avg})

    items.sort(key=lambda x: x["count"], reverse=True)
    total = len(items)
    start = (page - 1) * size
    rows = items[start:start+size]
    return jsonify({"rows": rows, "total": total})
@customer_analysis_bp.route("/customeranalysis/supplierusage-table", methods=["GET"])
def supplier_usage_table():
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)
    material_cat  = request.args.get("material_cat", type=str)  # 面料/里料/辅料/大底/中底
    page = max(1, request.args.get("page", type=int, default=1))
    size = max(1, min(200, request.args.get("size", type=int, default=20)))
    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)

    customer_ids, _ = _resolve_customer_ids(scope, customer_name, customer_id)
    if not customer_ids:
        return jsonify({"rows": [], "total": 0})

    q_raw = _supplier_usage_query(customer_ids, date_from, date_to, status)
    by_cat = _aggregate_primary_by_category(q_raw)  # {"面料":[{supplier_id,supplier_name,usage_count}],...}

    # 取选中类目（未传就并成一个大列表）
    if material_cat and material_cat in by_cat:
        items = by_cat[material_cat]
        chosen_cat = material_cat
    else:
        # 全部拼一起（保持显示也有类名）
        items = []
        for cat, arr in by_cat.items():
            for it in arr:
                it = dict(it)
                it["_cat"] = cat
                items.append(it)
        chosen_cat = None

    # 计算总次数（用于占比）
    total_cnt = sum(int(i["usage_count"] or 0) for i in items) or 1

    # 排序 + 分页
    items.sort(key=lambda x: int(x["usage_count"] or 0), reverse=True)
    total = len(items)
    start = (page - 1) * size
    part = items[start:start+size]

    rows = []
    for it in part:
        cat = chosen_cat or it.get("_cat") or "-"
        cnt = int(it["usage_count"] or 0)
        rows.append({
            "supplier_name": it["supplier_name"],
            "usage_count": cnt,
            "usage_ratio": cnt / total_cnt,
            "category_top": cat
        })

    return jsonify({"rows": rows, "total": total})
@customer_analysis_bp.route("/customeranalysis/compare-summary", methods=["GET"])
def compare_summary():
    scope = request.args.get("scope", type=str) or ("name" if request.args.get("customerName") else "brand")
    customer_name = request.args.get("customerName", type=str)
    customer_id   = request.args.get("customerId", type=int)

    # 对比对象
    compare_names = request.args.getlist("compareCustomerNames[]", type=str) or request.args.getlist("compareCustomerNames", type=str)
    compare_ids   = request.args.getlist("compareCustomerIds[]", type=int)   or request.args.getlist("compareCustomerIds", type=int)

    page = max(1, request.args.get("page", type=int, default=1))
    size = max(1, min(200, request.args.get("size", type=int, default=20)))

    date_from = parse_date(request.args.get("date_from", ""))
    date_to   = parse_date(request.args.get("date_to", ""))
    status    = request.args.get("status", type=str)
    base_filters = _range_filters(date_from, date_to, status)

    # 组装“比较目标”：[(显示名, [customer_id...]), ...]
    targets = []

    # 主客户也纳入第一行（表里要显示主对象）
    primary_ids, primary_display = _resolve_customer_ids(scope, customer_name, customer_id)
    if primary_ids:
        targets.append((primary_display or "主客户", primary_ids))

    if scope == "name" and compare_names:
        for nm in compare_names:
            ids = _resolve_scope_to_ids("name", nm, None)
            ids = ids if isinstance(ids, list) else ids  # 兼容旧函数返回
            if ids:
                targets.append((nm, ids))
    elif scope == "brand" and compare_ids:
        for cid in compare_ids:
            name = db.session.query(Customer.customer_name).filter(Customer.customer_id == cid).scalar() or f"客户{cid}"
            brand = db.session.query(Customer.customer_brand).filter(Customer.customer_id == cid).scalar()
            label = f"{name}-{brand}" if brand else name
            targets.append((label, [cid]))

    if not targets:
        return jsonify({"rows": [], "total": 0})

    # 逐目标计算指标
    rows_all = []
    for label, ids in targets:
        # 订单
        orders_q = db.session.query(Order).filter(and_(Order.customer_id.in_(ids), *base_filters))
        orders = orders_q.all()
        order_ids = [o.order_id for o in orders]
        orders_cnt = len(order_ids)

        # 单价分布（RMB）
        prices = []
        if order_ids:
            q_price = (
                db.session.query(OrderShoeType.unit_price, OrderShoeType.currency_type)
                .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
                .join(Order, OrderShoe.order_id == Order.order_id)
                .filter(Order.order_id.in_(order_ids))
            ).all()
            for p, cur in q_price:
                if p is not None:
                    prices.append(float(to_rmb(Decimal(str(p)), cur)))
        p50 = quantile_float(prices, 0.5) or 0.0
        p90 = quantile_float(prices, 0.9) or 0.0

        # 耗时分布
        leads = []
        prod_rows = (
            db.session.query(OrderShoeProductionInfo.cutting_start_date, OrderShoeProductionInfo.molding_end_date)
            .join(OrderShoe, OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id)
            .join(Order, OrderShoe.order_id == Order.order_id)
            .filter(Order.order_id.in_(order_ids))
        ).all()
        for s, e in prod_rows:
            if s and e:
                d = (e - s).days
                if d >= 0:
                    leads.append(d)
        l50 = quantile_float(leads, 0.5) or 0
        l90 = quantile_float(leads, 0.9) or 0

        # Top 设计师
        top_designer = None
        d_rows = (
            db.session.query(
                func.coalesce(Shoe.shoe_designer, "（未填写）").label("designer"),
                func.count(OrderShoe.order_shoe_id).label("cnt")
            )
            .select_from(OrderShoe)  # ⬅️ 指定主表
            .join(Order, OrderShoe.order_id == Order.order_id)  # ⬅️ 显式连接 Order
            .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)  # ⬅️ 只连一次 Shoe
            .filter(Order.order_id.in_(order_ids))
            .group_by(func.coalesce(Shoe.shoe_designer, "（未填写）"))
            .order_by(func.count(OrderShoe.order_shoe_id).desc())
        ).all()
        if d_rows:
            top_designer = d_rows[0].designer

        # Top 供应商（以 PI 去重计数）
        top_supplier = None
        q_raw = _supplier_usage_query(ids, date_from, date_to, status)
        by_cat = _aggregate_primary_by_category(q_raw)
        # 汇总所有类目后挑最大
        sup_counter = {}
        for arr in by_cat.values():
            for it in arr:
                sup_counter[it["supplier_name"]] = sup_counter.get(it["supplier_name"], 0) + int(it["usage_count"] or 0)
        if sup_counter:
            top_supplier = max(sup_counter.items(), key=lambda kv: kv[1])[0]

        rows_all.append({
          "customer": label,
          "orders": orders_cnt,
          "unit_price_p50": float(Decimal(str(p50)).quantize(Decimal("0.01"))),
          "unit_price_p90": float(Decimal(str(p90)).quantize(Decimal("0.01"))),
          "lead_days_p50": int(l50),
          "lead_days_p90": int(l90),
          "top_designer": top_designer,
          "top_supplier": top_supplier
        })

    # 分页（包含主客户 + 对比对象）
    total = len(rows_all)
    start = (page - 1) * size
    rows = rows_all[start:start+size]
    return jsonify({"rows": rows, "total": total})

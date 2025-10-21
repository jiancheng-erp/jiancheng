from datetime import datetime
from decimal import Decimal
from app_config import db
from constants import *
from flask import Blueprint, current_app, jsonify, request, send_file, abort, Response
import json
from models import *
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select, or_, and_, desc, literal, case, Integer, Select
from logger import logger
from sqlalchemy.sql import union_all
from file_locations import FILE_STORAGE_PATH
import os
import time
from general_document.accounting_warehouse_history_excel import (
    generate_accounting_warehouse_excel,
)
from datetime import datetime, timedelta, date
from decimal import Decimal
from flask import Blueprint, request, jsonify

material_storage_snapshot_bp = Blueprint("material_storage_snapshot_bp", __name__)


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _get_base_snapshot_date(target_date: date) -> date | None:
    stmt = select(func.max(MaterialStorageSnapshot.snapshot_date)).where(
        MaterialStorageSnapshot.snapshot_date <= target_date
    )
    return db.session.execute(stmt).scalar_one_or_none()


def add_filter_to_query(
    query: Select, filters: dict, base_or_change: str = "base"
) -> Select:
    warehouse_id = filters.get("warehouseIdFilter")
    supplier_name = filters.get("supplierNameFilter")
    material_name = filters.get("materialNameFilter")
    material_model = filters.get("materialModelFilter")
    material_specification = filters.get("materialSpecificationFilter")
    material_color = filters.get("materialColorFilter")
    customer_product_name = filters.get("customerProductNameFilter")
    order_rid = filters.get("orderRidFilter")
    shoe_rid = filters.get("shoeRidFilter")

    if warehouse_id:
        query = query.where(MaterialType.warehouse_id == warehouse_id)
    if supplier_name:
        query = query.where(Supplier.supplier_name.ilike(f"%{supplier_name}%"))
    if material_name:
        query = query.where(Material.material_name.ilike(f"%{material_name}%"))
    if material_model:
        query = query.where(SPUMaterial.material_model.ilike(f"%{material_model}%"))
    if material_specification:
        query = query.where(
            SPUMaterial.material_specification.ilike(f"%{material_specification}%")
        )
    if material_color:
        query = query.where(SPUMaterial.color.ilike(f"%{material_color}%"))
    if customer_product_name:
        query = query.where(
            OrderShoe.customer_product_name.ilike(f"%{customer_product_name}%")
        )
    if order_rid:
        query = query.where(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid:
        query = query.where(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))

    return query


def _paginate_msids(
    base_snapshot_date: date, target_date: date, filters: dict, paginate: bool
):
    """
    返回 (msids_on_page: list[int], total_count: int)
    集合 = { base快照当日出现的 msid } + { 变动区间内出现的 msid }
    """

    page = int(filters.get("page", 1))
    page_size = int(filters.get("page_size", 20))

    # 基准快照 msid
    base_q = (
        select(MaterialStorageSnapshot.material_storage_id.label("msid"))
        .join(
            SPUMaterial,
            SPUMaterial.spu_material_id == MaterialStorageSnapshot.spu_material_id,
        )
        .join(Material, SPUMaterial.material_id == Material.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(Order, MaterialStorageSnapshot.order_id == Order.order_id)
        .outerjoin(
            OrderShoe, MaterialStorageSnapshot.order_shoe_id == OrderShoe.order_shoe_id
        )
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .where(
            MaterialStorageSnapshot.snapshot_date == base_snapshot_date,
            or_(
                MaterialStorageSnapshot.pending_inbound > 0,
                MaterialStorageSnapshot.inbound_amount > 0,
            ),  # 剔除没有引用的库存记录
        )
    )

    if filters.get("displayZeroInventory", "true").lower() != "true":
        base_q = base_q.where(MaterialStorageSnapshot.current_amount != 0)
    # 过滤与主查询一致
    base_q = add_filter_to_query(base_q, filters, "base")

    # 变动区间 msid（若 base==target 则区间为空，不会返回结果）
    start_change_date = base_snapshot_date + timedelta(days=1)
    change_q = (
        select(DailyMaterialStorageChange.material_storage_id.label("msid"))
        .join(
            MaterialStorage,
            MaterialStorage.material_storage_id
            == DailyMaterialStorageChange.material_storage_id,
        )
        .join(
            SPUMaterial, SPUMaterial.spu_material_id == MaterialStorage.spu_material_id
        )
        .join(Material, SPUMaterial.material_id == Material.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(
            MaterialWarehouse,
            MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id,
        )
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(Order, MaterialStorage.order_id == Order.order_id)
        .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .where(
            and_(
                DailyMaterialStorageChange.snapshot_date >= start_change_date,
                DailyMaterialStorageChange.snapshot_date <= target_date,
            )
        )
    )

    # 过滤与主查询一致
    change_q = add_filter_to_query(change_q, filters, "change")

    # UNION (使用 union_all + 外层 DISTINCT 更稳)
    union_sub = union_all(base_q, change_q).subquery("u")

    # total
    total_stmt = select(func.count(func.distinct(union_sub.c.msid)))
    total = db.session.execute(total_stmt).scalar() or 0

    # 本页 msid 列表
    page_stmt = select(union_sub.c.msid).distinct()
    if paginate:
        page_stmt = page_stmt.offset((page - 1) * page_size).limit(page_size)
    msids_on_page = [r[0] for r in db.session.execute(page_stmt).all()]

    return msids_on_page, total


def compute_inventory_as_of(target_date: date, filters: dict, paginate: bool) -> dict:
    """
    计算 target_date 当日的库存状态（分页）。
    返回 dict: { items: [...], total: int, page: int, pageSize: int }
    """
    base_snapshot_date = _get_base_snapshot_date(target_date)
    if not base_snapshot_date:
        # 没有任何快照：返回错误
        abort(Response(json.dumps({"message": "没有该日期历史库存记录"}), 400))

    # 1) 先拿到本页 msid 列表 & total
    msids, total = _paginate_msids(base_snapshot_date, target_date, filters, paginate)
    # 空页
    if total == 0 or not msids:
        return {"items": [], "total": total}

    # 2) 取本页基准快照
    base_stmt = (
        select(
            MaterialStorageSnapshot,
            MaterialWarehouse.material_warehouse_name,
            Supplier.supplier_name,
            MaterialType.material_type_name,
            Material.material_name,
            SPUMaterial.material_model,
            SPUMaterial.material_specification,
            SPUMaterial.color,
            Order.order_rid,
            OrderShoe.customer_product_name,
            Shoe.shoe_rid,
        )
        .join(
            SPUMaterial,
            SPUMaterial.spu_material_id == MaterialStorageSnapshot.spu_material_id,
        )
        .join(Material, Material.material_id == SPUMaterial.material_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(
            MaterialWarehouse,
            MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id,
        )
        .outerjoin(Order, MaterialStorageSnapshot.order_id == Order.order_id)
        .outerjoin(
            OrderShoe, MaterialStorageSnapshot.order_shoe_id == OrderShoe.order_shoe_id
        )
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .where(
            MaterialStorageSnapshot.snapshot_date == base_snapshot_date,
            MaterialStorageSnapshot.material_storage_id.in_(msids),
        )
    )

    base_rows = db.session.execute(base_stmt).all()
    base_map = {}

    COLS = [c.name for c in MaterialStorageSnapshot.__table__.columns]

    for row in base_rows:
        snapshot = row.MaterialStorageSnapshot
        base_map[snapshot.material_storage_id] = {
            **{c: getattr(snapshot, c) for c in COLS},  # snapshot表所有列
            "material_warehouse_name": row.material_warehouse_name,
            "supplier_name": row.supplier_name,
            "material_type_name": row.material_type_name,
            "material_name": row.material_name,
            "material_model": row.material_model,
            "material_specification": row.material_specification,
            "material_color": row.color,
            "order_rid": row.order_rid,
            "customer_product_name": row.customer_product_name,
            "shoe_rid": row.shoe_rid,
        }
    # 3) 取本页变动汇总
    start_change_date = base_snapshot_date + timedelta(days=1)
    change_rows = []
    if start_change_date <= target_date:
        # 1) 先做聚合
        agg_base = (
            select(
                DailyMaterialStorageChange.material_storage_id.label("msid"),
                func.coalesce(
                    func.sum(DailyMaterialStorageChange.pending_inbound_sum), 0
                ).label("pending_inbound_sum"),
                func.coalesce(
                    func.sum(DailyMaterialStorageChange.pending_outbound_sum), 0
                ).label("pending_outbound_sum"),
                func.coalesce(
                    func.sum(DailyMaterialStorageChange.inbound_amount_sum), 0
                ).label("inbound_sum"),
                func.coalesce(
                    func.sum(DailyMaterialStorageChange.outbound_amount_sum), 0
                ).label("outbound_sum"),
                func.coalesce(func.sum(DailyMaterialStorageChange.net_change), 0).label(
                    "net_change_sum"
                ),
            )
            .where(
                DailyMaterialStorageChange.snapshot_date >= start_change_date,
                DailyMaterialStorageChange.snapshot_date <= target_date,
                DailyMaterialStorageChange.material_storage_id.in_(msids),
            )
            .group_by(DailyMaterialStorageChange.material_storage_id)
        )

        # 2) “不显示零库存”的过滤要么用 HAVING（在同一层聚合里），
        #    要么外包一层子查询后在外层 WHERE；两种二选一。我这里用 HAVING。
        if filters.get("displayZeroInventory", "true").lower() != "true":
            agg_base = agg_base.having(
                func.coalesce(func.sum(DailyMaterialStorageChange.net_change), 0) > 0
            )

        # 3) 包成子查询
        agg_table = agg_base.subquery()

        # 4) 外层查询：显式 select_from(agg_table)，再按外键一路 join
        change_stmt = (
            select(
                agg_table.c.msid,
                MaterialStorage.actual_inbound_unit,
                MaterialWarehouse.material_warehouse_name,
                Supplier.supplier_name,
                MaterialType.material_type_name,
                Material.material_name,
                SPUMaterial.material_model,
                SPUMaterial.material_specification,
                SPUMaterial.color,
                Order.order_rid,
                OrderShoe.customer_product_name,
                Shoe.shoe_rid,
                agg_table.c.pending_inbound_sum,
                agg_table.c.pending_outbound_sum,
                agg_table.c.inbound_sum,
                agg_table.c.outbound_sum,
                agg_table.c.net_change_sum,
            )
            .select_from(agg_table)  # 关键：明确起点，避免笛卡尔积
            .join(
                MaterialStorage, MaterialStorage.material_storage_id == agg_table.c.msid
            )
            .join(
                SPUMaterial,
                SPUMaterial.spu_material_id == MaterialStorage.spu_material_id,
            )
            .join(Material, SPUMaterial.material_id == Material.material_id)
            .join(
                MaterialType, MaterialType.material_type_id == Material.material_type_id
            )
            .join(
                MaterialWarehouse,
                MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id,
            )
            .join(Supplier, Supplier.supplier_id == Material.material_supplier)
            .outerjoin(Order, MaterialStorage.order_id == Order.order_id)
            .outerjoin(
                OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id
            )
            .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        )

        change_rows = db.session.execute(change_stmt).all()

    change_map = {dict(r._mapping)["msid"]: dict(r._mapping) for r in change_rows}

    # 获取每个 msid 在 target_date 之前（含当天）的最新记录
    latest_price_subq = (
        select(
            DailyMaterialStorageChange.material_storage_id.label("msid"),
            func.max(DailyMaterialStorageChange.snapshot_date).label("latest_date"),
        )
        .where(
            DailyMaterialStorageChange.snapshot_date <= target_date,
            DailyMaterialStorageChange.material_storage_id.in_(msids),
        )
        .group_by(DailyMaterialStorageChange.material_storage_id)
        .subquery()
    )

    # 联结子查询，取出对应日期的单价和均价
    price_stmt = (
        select(
            DailyMaterialStorageChange.material_storage_id.label("msid"),
            func.coalesce(DailyMaterialStorageChange.latest_unit_price, 0).label(
                "unit_price"
            ),
            func.coalesce(DailyMaterialStorageChange.avg_unit_price, 0).label(
                "average_price"
            ),
        )
        .join(
            latest_price_subq,
            and_(
                DailyMaterialStorageChange.material_storage_id
                == latest_price_subq.c.msid,
                DailyMaterialStorageChange.snapshot_date
                == latest_price_subq.c.latest_date,
            ),
        )
        .where(DailyMaterialStorageChange.material_storage_id.in_(msids))
    )
    price_rows = db.session.execute(price_stmt).all()
    price_map = {
        r.msid: {"unit_price": r.unit_price, "average_price": r.average_price}
        for r in price_rows
    }
    for msid in msids:
        if msid not in price_map:
            price_map[msid] = {
                "unit_price": Decimal("0"),
                "average_price": Decimal("0"),
            }
    # 4) 合并，生成本页 items
    items = []
    for msid in msids:
        base = base_map.get(msid)
        chg = change_map.get(msid, {})
        price_info = price_map.get(msid, {})
        # 0 基数兜底
        if not base:
            base = {
                "material_storage_id": msid,
                "material_warehouse_name": chg.get("material_warehouse_name"),
                "supplier_name": chg.get("supplier_name"),
                "material_type_name": chg.get("material_type_name"),
                "material_name": chg.get("material_name"),
                "material_model": chg.get("material_model"),
                "material_specification": chg.get("material_specification"),
                "material_color": chg.get("color"),
                "order_rid": chg.get("order_rid"),
                "customer_product_name": chg.get("customer_product_name"),
                "shoe_rid": chg.get("shoe_rid"),
                "actual_inbound_unit": chg.get("actual_inbound_unit"),
                "pending_inbound": Decimal("0"),
                "pending_outbound": Decimal("0"),
                "inbound_amount": Decimal("0"),
                "outbound_amount": Decimal("0"),
                "current_amount": Decimal("0"),
                "unit_price": price_info.get("unit_price"),
                "average_price": price_info.get("average_price"),
            }

        pending_inbound = base.get("pending_inbound") + chg.get(
            "pending_inbound_sum", 0
        )
        pending_outbound = base.get("pending_outbound") + chg.get(
            "pending_outbound_sum", 0
        )
        inbound_amount = base.get("inbound_amount") + chg.get("inbound_sum", 0)
        current_amount = base.get("current_amount") + chg.get("net_change_sum", 0)
        items.append(
            {
                "materialStorageId": msid,
                "warehouseName": base.get("material_warehouse_name"),
                "supplierName": base.get("supplier_name"),
                "materialType": base.get("material_type_name"),
                "materialName": base.get("material_name"),
                "materialModel": base.get("material_model"),
                "materialSpecification": base.get("material_specification"),
                "materialColor": base.get("color"),
                "orderRId": base.get("order_rid"),
                "customerProductName": base.get("customer_product_name"),
                "shoeRId": base.get("shoe_rid"),
                "actualInboundUnit": base.get("actual_inbound_unit"),
                "unitPrice": price_info.get("unit_price"),
                "averagePrice": price_info.get("average_price"),
                "pendingInbound": pending_inbound,
                "pendingOutbound": pending_outbound,
                "inboundAmount": inbound_amount,
                "outboundAmount": inbound_amount - current_amount,
                "currentAmount": current_amount,
                "inboundedItemTotalPrice": inbound_amount
                * price_info.get("average_price"),
                "currentItemTotalPrice": current_amount
                * price_info.get("average_price"),
            }
        )

    return {"items": items, "total": total}


@material_storage_snapshot_bp.route(
    "/warehouse/getmaterialstroagebydate", methods=["GET"]
)
def get_material_storage_by_date():
    """
    GET /api/inventory/as-of?date=2025-10-04&spu_material_id=...&material_storage_id=...
    返回：指定日期的库存状态列表（每个 material_storage_id 一条）
    """
    date_str = request.args.get("snapshotDate")
    if not date_str:
        return jsonify({"code": 400, "msg": "缺少参数 date(YYYY-MM-DD)"}), 400

    try:
        target_date = _parse_date(date_str)
    except Exception:
        return jsonify({"code": 400, "msg": "date 格式错误，需 YYYY-MM-DD"}), 400

    data = compute_inventory_as_of(target_date, filters=request.args, paginate=True)
    return jsonify({"code": 200, "msg": "success", "data": data})


@material_storage_snapshot_bp.route(
    "/warehouse/exportinventoryhistory", methods=["GET"]
)
def export_inventory_history():
    date_str = request.args.get("snapshotDate")
    warehouse_id = request.args.get("warehouseIdFilter")
    warehouse_name = (
        db.session.query(MaterialWarehouse.material_warehouse_name)
        .filter(MaterialWarehouse.material_warehouse_id == warehouse_id)
        .scalar()
    )
    suppplier_name_filter = request.args.get("supplierNameFilter")

    if not date_str:
        return jsonify({"code": 400, "msg": "缺少参数 date(YYYY-MM-DD)"}), 400

    try:
        target_date = _parse_date(date_str)
    except Exception:
        return jsonify({"code": 400, "msg": "date 格式错误，需 YYYY-MM-DD"}), 400

    data = compute_inventory_as_of(target_date, filters=request.args, paginate=False)
    template_path = os.path.join(FILE_STORAGE_PATH, "财务历史库存模板.xlsx")
    timestamp = str(time.time())
    new_file_name = f"财务历史库存输出_{timestamp}.xlsx"
    save_path = os.path.join(FILE_STORAGE_PATH, "财务部文件", "库存总单", new_file_name)
    time_range_string = date_str
    generate_accounting_warehouse_excel(
        template_path,
        save_path,
        warehouse_name,
        suppplier_name_filter,
        time_range_string,
        data["items"],
    )
    return send_file(save_path, as_attachment=True, download_name=new_file_name)

from __future__ import annotations

from datetime import datetime, timedelta, date
from decimal import Decimal
import json
import os
import time
from typing import Optional, Dict, List

from flask import Blueprint, current_app, jsonify, request, send_file, abort, Response

from app_config import db
from constants import *
from models import *
from sqlalchemy import func, select, or_, and_, desc, literal
from sqlalchemy.sql import union_all
from file_locations import FILE_STORAGE_PATH
from general_document.accounting_warehouse_history_excel import (
    generate_accounting_warehouse_excel,
)

material_storage_snapshot_bp = Blueprint("material_storage_snapshot_bp", __name__)


# -----------------------------
# Helpers
# -----------------------------

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _get_base_snapshot_date(target_date: date) -> Optional[date]:
    stmt = select(func.max(MaterialStorageSnapshot.snapshot_date)).where(
        MaterialStorageSnapshot.snapshot_date <= target_date
    )
    return db.session.execute(stmt).scalar_one_or_none()


def add_filter_to_query(query, filters: dict, _: str = "base"):
    """Apply optional filters to a SQLAlchemy selectable (no GROUP BY assumptions)."""
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


def _union_msids_subq(base_snapshot_date: date, target_date: date, filters: dict):
    """Return DISTINCT msid subquery entirely in DB (no roundtrip)."""
    # base-side msids (keep at least meaningful ones)
    base_q = (
        select(MaterialStorageSnapshot.material_storage_id.label("msid"))
        .join(SPUMaterial, SPUMaterial.spu_material_id == MaterialStorageSnapshot.spu_material_id)
        .join(Material, SPUMaterial.material_id == Material.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(Order, MaterialStorageSnapshot.order_id == Order.order_id)
        .outerjoin(OrderShoe, MaterialStorageSnapshot.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .where(
            MaterialStorageSnapshot.snapshot_date == base_snapshot_date,
            or_(
                MaterialStorageSnapshot.pending_inbound > 0,
                MaterialStorageSnapshot.inbound_amount > 0,
            ),
        )
    )
    base_q = add_filter_to_query(base_q, filters, "base")

    # change-window msids
    start_change_date = base_snapshot_date + timedelta(days=1)
    change_q = (
        select(DailyMaterialStorageChange.material_storage_id.label("msid"))
        .join(MaterialStorage, MaterialStorage.material_storage_id == DailyMaterialStorageChange.material_storage_id)
        .join(SPUMaterial, SPUMaterial.spu_material_id == MaterialStorage.spu_material_id)
        .join(Material, SPUMaterial.material_id == Material.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(MaterialWarehouse, MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(Order, MaterialStorage.order_id == Order.order_id)
        .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .where(
            DailyMaterialStorageChange.snapshot_date >= start_change_date,
            DailyMaterialStorageChange.snapshot_date <= target_date,
        )
    )
    change_q = add_filter_to_query(change_q, filters, "change")

    u = union_all(base_q, change_q).subquery("u_all")
    return select(u.c.msid).distinct().subquery("msids_all")


def _final_agg_for_msids_subq(msids_all, base_snapshot_date: date, start_change_date: date, target_date: date):
    """LEFT JOIN base + delta on full msid set, return final_agg subquery."""
    # base snapshot
    base_snap = (
        select(
            MaterialStorageSnapshot.material_storage_id.label("msid"),
            func.coalesce(MaterialStorageSnapshot.pending_inbound, 0).label("base_pending_in"),
            func.coalesce(MaterialStorageSnapshot.pending_outbound, 0).label("base_pending_out"),
            func.coalesce(MaterialStorageSnapshot.inbound_amount, 0).label("base_inbound"),
            func.coalesce(MaterialStorageSnapshot.current_amount, 0).label("base_current"),
        )
        .where(MaterialStorageSnapshot.snapshot_date == base_snapshot_date)
    ).subquery()

    # interval sums (including pending_*)
    delta_sum = (
        select(
            DailyMaterialStorageChange.material_storage_id.label("msid"),
            func.coalesce(func.sum(DailyMaterialStorageChange.inbound_amount_sum), 0).label("delta_in"),
            func.coalesce(func.sum(DailyMaterialStorageChange.outbound_amount_sum), 0).label("delta_out"),
            func.coalesce(func.sum(DailyMaterialStorageChange.net_change), 0).label("delta_net"),
            func.coalesce(func.sum(DailyMaterialStorageChange.pending_inbound_sum), 0).label("delta_pending_in"),
            func.coalesce(func.sum(DailyMaterialStorageChange.pending_outbound_sum), 0).label("delta_pending_out"),
        )
        .where(
            DailyMaterialStorageChange.snapshot_date >= start_change_date,
            DailyMaterialStorageChange.snapshot_date <= target_date,
        )
        .group_by(DailyMaterialStorageChange.material_storage_id)
    ).subquery()

    final_agg = (
        select(
            msids_all.c.msid,
            (func.coalesce(base_snap.c.base_pending_in, 0) + func.coalesce(delta_sum.c.delta_pending_in, 0)).label("final_pending_in"),
            (func.coalesce(base_snap.c.base_pending_out, 0) + func.coalesce(delta_sum.c.delta_pending_out, 0)).label("final_pending_out"),
            (func.coalesce(base_snap.c.base_inbound, 0) + func.coalesce(delta_sum.c.delta_in, 0)).label("final_inbound"),
            (func.coalesce(base_snap.c.base_current, 0) + func.coalesce(delta_sum.c.delta_net, 0)).label("final_current"),
        )
        .join(base_snap, base_snap.c.msid == msids_all.c.msid, isouter=True)
        .join(delta_sum, delta_sum.c.msid == msids_all.c.msid, isouter=True)
    ).subquery("final_agg")

    return final_agg


# -----------------------------
# Core
# -----------------------------

def compute_inventory_as_of(target_date: date, filters: dict, paginate: bool) -> dict:
    """
    DB-side DISTINCT + aggregate + filter + ORDER BY + LIMIT/OFFSET pagination.
    """
    page = filters.get("page", 1, type=int)
    page_size = filters.get("pageSize", 20, type=int)
    display_zero = (filters.get("displayZeroInventory", "true").lower() == "true")

    base_snapshot_date = _get_base_snapshot_date(target_date)
    if not base_snapshot_date:
        abort(Response(json.dumps({"message": "没有该日期历史库存记录"}), 400))

    start_change_date = base_snapshot_date + timedelta(days=1)

    # 1) Candidate msids in DB
    msids_all = _union_msids_subq(base_snapshot_date, target_date, filters)

    # 2) Final aggregation for all msids
    final_agg = _final_agg_for_msids_subq(msids_all, base_snapshot_date, start_change_date, target_date)

    # 3) Filter: when display_zero = false, keep only pending_in>0 OR current>0
    cond = literal(True) if display_zero else or_(
        final_agg.c.final_pending_in > 0,
        final_agg.c.final_current > 0,
    )

    # 4) Total count in DB
    total_stmt = select(func.count()).select_from(
        select(final_agg.c.msid).where(cond).subquery()
    )
    total = db.session.execute(total_stmt).scalar_one()

    # 5) ORDER & paginate in DB
    offset = (page - 1) * page_size if paginate else 0
    limit = page_size if paginate else None

    page_base = select(final_agg).where(cond).order_by(final_agg.c.msid.asc())
    if limit is not None:
        page_base = page_base.limit(limit).offset(offset)

    page_rows = db.session.execute(page_base).all()
    msids_page = [r.msid for r in page_rows]
    print(msids_page)
    # Map of final metrics
    final_map: Dict[int, Dict[str, Decimal]] = {
        r.msid: {
            "final_pending_in": r.final_pending_in,
            "final_pending_out": r.final_pending_out,
            "final_inbound": r.final_inbound,
            "final_current": r.final_current,
        }
        for r in page_rows
    }

    if total == 0 or not msids_page:
        return {"items": [], "total": total, "page": page, "pageSize": page_size}

    # 6) Base snapshot info for decorations
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
        .join(SPUMaterial, SPUMaterial.spu_material_id == MaterialStorageSnapshot.spu_material_id)
        .join(Material, Material.material_id == SPUMaterial.material_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(MaterialWarehouse, MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id)
        .outerjoin(Order, MaterialStorageSnapshot.order_id == Order.order_id)
        .outerjoin(OrderShoe, MaterialStorageSnapshot.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .where(
            MaterialStorageSnapshot.snapshot_date == base_snapshot_date,
            MaterialStorageSnapshot.material_storage_id.in_(msids_page),
        )
    )
    base_rows = db.session.execute(base_stmt).all()
    base_map: Dict[int, Dict[str, object]] = {}
    COLS = [c.name for c in MaterialStorageSnapshot.__table__.columns]
    for row in base_rows:
        snapshot = row.MaterialStorageSnapshot
        base_map[snapshot.material_storage_id] = {
            **{c: getattr(snapshot, c) for c in COLS},
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

    # 7) Fallback: for msids without base snapshot row, fetch from MaterialStorage
    missing_msids = [m for m in msids_page if m not in base_map]
    if missing_msids:
        storage_stmt = (
            select(
                MaterialStorage,
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
            .join(SPUMaterial, SPUMaterial.spu_material_id == MaterialStorage.spu_material_id)
            .join(Material, Material.material_id == SPUMaterial.material_id)
            .join(Supplier, Supplier.supplier_id == Material.material_supplier)
            .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
            .join(MaterialWarehouse, MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id)
            .outerjoin(Order, MaterialStorage.order_id == Order.order_id)
            .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
            .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
            .where(MaterialStorage.material_storage_id.in_(missing_msids))
        )
        storage_rows = db.session.execute(storage_stmt).all()
        for row in storage_rows:
            storage = row.MaterialStorage
            base_map[storage.material_storage_id] = {
                "material_storage_id": storage.material_storage_id,
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
                "actual_inbound_unit": getattr(storage, "actual_inbound_unit", None),
            }

    # 8) Prices (latest <= target_date)
    latest_price_subq = (
        select(
            DailyMaterialStorageChange.material_storage_id.label("msid"),
            func.max(DailyMaterialStorageChange.snapshot_date).label("latest_date"),
        )
        .where(
            DailyMaterialStorageChange.snapshot_date <= target_date,
            DailyMaterialStorageChange.material_storage_id.in_(msids_page),
        )
        .group_by(DailyMaterialStorageChange.material_storage_id)
        .subquery()
    )
    price_stmt = (
        select(
            DailyMaterialStorageChange.material_storage_id.label("msid"),
            func.coalesce(DailyMaterialStorageChange.latest_unit_price, 0).label("unit_price"),
            func.coalesce(DailyMaterialStorageChange.avg_unit_price, 0).label("average_price"),
        )
        .join(
            latest_price_subq,
            and_(
                DailyMaterialStorageChange.material_storage_id == latest_price_subq.c.msid,
                DailyMaterialStorageChange.snapshot_date == latest_price_subq.c.latest_date,
            ),
        )
        .where(DailyMaterialStorageChange.material_storage_id.in_(msids_page))
    )
    price_rows = db.session.execute(price_stmt).all()
    price_map = {r.msid: {"unit_price": r.unit_price, "average_price": r.average_price} for r in price_rows}
    for msid in msids_page:
        if msid not in price_map:
            price_map[msid] = {"unit_price": Decimal("0"), "average_price": Decimal("0")}

    # 9) Assemble items
    items: List[Dict[str, object]] = []
    for msid in msids_page:
        base = base_map.get(msid, None)
        fin = final_map.get(msid, {})
        price_info = price_map.get(msid, {"unit_price": Decimal("0"), "average_price": Decimal("0")})

        if not base:
            # Again, extreme fallback to avoid KeyError
            base = {
                "material_storage_id": msid,
                "material_warehouse_name": None,
                "supplier_name": None,
                "material_type_name": None,
                "material_name": None,
                "material_model": None,
                "material_specification": None,
                "material_color": None,
                "order_rid": None,
                "customer_product_name": None,
                "shoe_rid": None,
                "actual_inbound_unit": None,
            }

        final_pending_in = fin.get("final_pending_in", Decimal("0"))
        final_pending_out = fin.get("final_pending_out", Decimal("0"))
        final_inbound = fin.get("final_inbound", Decimal("0"))
        final_current = fin.get("final_current", Decimal("0"))

        items.append(
            {
                "materialStorageId": msid,
                "warehouseName": base.get("material_warehouse_name"),
                "supplierName": base.get("supplier_name"),
                "materialType": base.get("material_type_name"),
                "materialName": base.get("material_name"),
                "materialModel": base.get("material_model"),
                "materialSpecification": base.get("material_specification"),
                "materialColor": base.get("material_color"),
                "orderRId": base.get("order_rid"),
                "customerProductName": base.get("customer_product_name"),
                "shoeRId": base.get("shoe_rid"),
                "actualInboundUnit": base.get("actual_inbound_unit"),
                "unitPrice": price_info.get("unit_price"),
                "averagePrice": price_info.get("average_price"),
                "pendingInbound": final_pending_in,
                "pendingOutbound": final_pending_out,
                "inboundAmount": final_inbound,
                "outboundAmount": (final_inbound - final_current),
                "currentAmount": final_current,
                "inboundedItemTotalPrice": final_inbound * price_info.get("average_price"),
                "currentItemTotalPrice": final_current * price_info.get("average_price"),
            }
        )

    return {"items": items, "total": total, "page": page, "pageSize": page_size}


# -----------------------------
# Routes
# -----------------------------

@material_storage_snapshot_bp.route("/warehouse/getmaterialstroagebydate", methods=["GET"])
def get_material_storage_by_date():
    """
    GET /warehouse/getmaterialstroagebydate?snapshotDate=2025-10-04&...
    Return: inventory state list (one row per material_storage_id) for given date.
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


@material_storage_snapshot_bp.route("/warehouse/exportinventoryhistory", methods=["GET"])
def export_inventory_history():
    date_str = request.args.get("snapshotDate")
    warehouse_id = request.args.get("warehouseIdFilter")

    warehouse_name = None
    if warehouse_id:
        warehouse_name = (
            db.session.query(MaterialWarehouse.material_warehouse_name)
            .filter(MaterialWarehouse.material_warehouse_id == warehouse_id)
            .scalar()
        )

    supplier_name_filter = request.args.get("supplierNameFilter")

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
        supplier_name_filter,
        time_range_string,
        data["items"],
    )
    return send_file(save_path, as_attachment=True, download_name=new_file_name)

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
import csv

from flask import Blueprint, abort, jsonify, request, Response, current_app
from sqlalchemy import func, text

from app_config import db
from constants import FINISHED_STORAGE_STATUS
from models import (
    FinishedShoeStorageSnapshot,
    FinishedShoeSizeDetailSnapshot,
    DailyFinishedShoeStorageChange,
    DailyFinishedShoeSizeDetailChange,
    OrderShoeType,
    OrderShoe,
    Order,
    ShoeType,
    Shoe,
    Customer,
    Color,
)

finished_storage_snapshot_bp = Blueprint("finished_storage_snapshot_bp", __name__)


def _parse_date_or_default(value: str | None) -> date:
    if value:
        return date.fromisoformat(value)
    return date.today() - timedelta(days=1)


def _get_base_snapshot_date(target_date: date):
    return (
        db.session.query(func.max(FinishedShoeStorageSnapshot.snapshot_date))
        .filter(FinishedShoeStorageSnapshot.snapshot_date <= target_date)
        .scalar()
    )


def _create_snapshot_for_date(snapshot_date: date):
    """On-demand snapshot（以当日现有库存为基准补历史）"""
    current_app.logger.info(f"[finished_snapshot] create on-demand snapshot for {snapshot_date}")
    sql_storage = text(
        """
        INSERT INTO finished_shoe_storage_snapshot (
            snapshot_date,
            finished_shoe_storage_id,
            order_shoe_type_id,
            finished_estimated_amount,
            size_34_estimated_amount,
            size_35_estimated_amount,
            size_36_estimated_amount,
            size_37_estimated_amount,
            size_38_estimated_amount,
            size_39_estimated_amount,
            size_40_estimated_amount,
            size_41_estimated_amount,
            size_42_estimated_amount,
            size_43_estimated_amount,
            size_44_estimated_amount,
            size_45_estimated_amount,
            size_46_estimated_amount,
            finished_actual_amount,
            size_34_actual_amount,
            size_35_actual_amount,
            size_36_actual_amount,
            size_37_actual_amount,
            size_38_actual_amount,
            size_39_actual_amount,
            size_40_actual_amount,
            size_41_actual_amount,
            size_42_actual_amount,
            size_43_actual_amount,
            size_44_actual_amount,
            size_45_actual_amount,
            size_46_actual_amount,
            finished_amount,
            size_34_amount,
            size_35_amount,
            size_36_amount,
            size_37_amount,
            size_38_amount,
            size_39_amount,
            size_40_amount,
            size_41_amount,
            size_42_amount,
            size_43_amount,
            size_44_amount,
            size_45_amount,
            size_46_amount,
            finished_status
        )
        SELECT
            :snapshot_date AS snapshot_date,
            fss.finished_shoe_id,
            fss.order_shoe_type_id,
            fss.finished_estimated_amount,
            fss.size_34_estimated_amount,
            fss.size_35_estimated_amount,
            fss.size_36_estimated_amount,
            fss.size_37_estimated_amount,
            fss.size_38_estimated_amount,
            fss.size_39_estimated_amount,
            fss.size_40_estimated_amount,
            fss.size_41_estimated_amount,
            fss.size_42_estimated_amount,
            fss.size_43_estimated_amount,
            fss.size_44_estimated_amount,
            fss.size_45_estimated_amount,
            fss.size_46_estimated_amount,
            fss.finished_actual_amount,
            fss.size_34_actual_amount,
            fss.size_35_actual_amount,
            fss.size_36_actual_amount,
            fss.size_37_actual_amount,
            fss.size_38_actual_amount,
            fss.size_39_actual_amount,
            fss.size_40_actual_amount,
            fss.size_41_actual_amount,
            fss.size_42_actual_amount,
            fss.size_43_actual_amount,
            fss.size_44_actual_amount,
            fss.size_45_actual_amount,
            fss.size_46_actual_amount,
            fss.finished_amount,
            fss.size_34_amount,
            fss.size_35_amount,
            fss.size_36_amount,
            fss.size_37_amount,
            fss.size_38_amount,
            fss.size_39_amount,
            fss.size_40_amount,
            fss.size_41_amount,
            fss.size_42_amount,
            fss.size_43_amount,
            fss.size_44_amount,
            fss.size_45_amount,
            fss.size_46_amount,
            fss.finished_status
        FROM finished_shoe_storage fss
        ON DUPLICATE KEY UPDATE
            order_shoe_type_id        = VALUES(order_shoe_type_id),
            finished_estimated_amount = VALUES(finished_estimated_amount),
            size_34_estimated_amount  = VALUES(size_34_estimated_amount),
            size_35_estimated_amount  = VALUES(size_35_estimated_amount),
            size_36_estimated_amount  = VALUES(size_36_estimated_amount),
            size_37_estimated_amount  = VALUES(size_37_estimated_amount),
            size_38_estimated_amount  = VALUES(size_38_estimated_amount),
            size_39_estimated_amount  = VALUES(size_39_estimated_amount),
            size_40_estimated_amount  = VALUES(size_40_estimated_amount),
            size_41_estimated_amount  = VALUES(size_41_estimated_amount),
            size_42_estimated_amount  = VALUES(size_42_estimated_amount),
            size_43_estimated_amount  = VALUES(size_43_estimated_amount),
            size_44_estimated_amount  = VALUES(size_44_estimated_amount),
            size_45_estimated_amount  = VALUES(size_45_estimated_amount),
            size_46_estimated_amount  = VALUES(size_46_estimated_amount),
            finished_actual_amount    = VALUES(finished_actual_amount),
            size_34_actual_amount     = VALUES(size_34_actual_amount),
            size_35_actual_amount     = VALUES(size_35_actual_amount),
            size_36_actual_amount     = VALUES(size_36_actual_amount),
            size_37_actual_amount     = VALUES(size_37_actual_amount),
            size_38_actual_amount     = VALUES(size_38_actual_amount),
            size_39_actual_amount     = VALUES(size_39_actual_amount),
            size_40_actual_amount     = VALUES(size_40_actual_amount),
            size_41_actual_amount     = VALUES(size_41_actual_amount),
            size_42_actual_amount     = VALUES(size_42_actual_amount),
            size_43_actual_amount     = VALUES(size_43_actual_amount),
            size_44_actual_amount     = VALUES(size_44_actual_amount),
            size_45_actual_amount     = VALUES(size_45_actual_amount),
            size_46_actual_amount     = VALUES(size_46_actual_amount),
            finished_amount           = VALUES(finished_amount),
            size_34_amount            = VALUES(size_34_amount),
            size_35_amount            = VALUES(size_35_amount),
            size_36_amount            = VALUES(size_36_amount),
            size_37_amount            = VALUES(size_37_amount),
            size_38_amount            = VALUES(size_38_amount),
            size_39_amount            = VALUES(size_39_amount),
            size_40_amount            = VALUES(size_40_amount),
            size_41_amount            = VALUES(size_41_amount),
            size_42_amount            = VALUES(size_42_amount),
            size_43_amount            = VALUES(size_43_amount),
            size_44_amount            = VALUES(size_44_amount),
            size_45_amount            = VALUES(size_45_amount),
            size_46_amount            = VALUES(size_46_amount),
            finished_status           = VALUES(finished_status),
            update_time               = CURRENT_TIMESTAMP
        """
    )
    sql_size = text(
        """
        INSERT INTO finished_shoe_size_detail_snapshot (
            snapshot_date,
            finished_shoe_storage_id,
            size_value,
            order_number,
            estimated_amount,
            actual_amount,
            current_amount
        )
        SELECT
            :snapshot_date AS snapshot_date,
            fss.finished_shoe_id,
            sz.size_value,
            sz.order_number,
            CASE sz.order_number
                WHEN 0  THEN COALESCE(fss.size_34_estimated_amount, 0)
                WHEN 1  THEN COALESCE(fss.size_35_estimated_amount, 0)
                WHEN 2  THEN COALESCE(fss.size_36_estimated_amount, 0)
                WHEN 3  THEN COALESCE(fss.size_37_estimated_amount, 0)
                WHEN 4  THEN COALESCE(fss.size_38_estimated_amount, 0)
                WHEN 5  THEN COALESCE(fss.size_39_estimated_amount, 0)
                WHEN 6  THEN COALESCE(fss.size_40_estimated_amount, 0)
                WHEN 7  THEN COALESCE(fss.size_41_estimated_amount, 0)
                WHEN 8  THEN COALESCE(fss.size_42_estimated_amount, 0)
                WHEN 9  THEN COALESCE(fss.size_43_estimated_amount, 0)
                WHEN 10 THEN COALESCE(fss.size_44_estimated_amount, 0)
                WHEN 11 THEN COALESCE(fss.size_45_estimated_amount, 0)
                WHEN 12 THEN COALESCE(fss.size_46_estimated_amount, 0)
            END AS estimated_amount,
            CASE sz.order_number
                WHEN 0  THEN COALESCE(fss.size_34_actual_amount, 0)
                WHEN 1  THEN COALESCE(fss.size_35_actual_amount, 0)
                WHEN 2  THEN COALESCE(fss.size_36_actual_amount, 0)
                WHEN 3  THEN COALESCE(fss.size_37_actual_amount, 0)
                WHEN 4  THEN COALESCE(fss.size_38_actual_amount, 0)
                WHEN 5  THEN COALESCE(fss.size_39_actual_amount, 0)
                WHEN 6  THEN COALESCE(fss.size_40_actual_amount, 0)
                WHEN 7  THEN COALESCE(fss.size_41_actual_amount, 0)
                WHEN 8  THEN COALESCE(fss.size_42_actual_amount, 0)
                WHEN 9  THEN COALESCE(fss.size_43_actual_amount, 0)
                WHEN 10 THEN COALESCE(fss.size_44_actual_amount, 0)
                WHEN 11 THEN COALESCE(fss.size_45_actual_amount, 0)
                WHEN 12 THEN COALESCE(fss.size_46_actual_amount, 0)
            END AS actual_amount,
            CASE sz.order_number
                WHEN 0  THEN COALESCE(fss.size_34_amount, 0)
                WHEN 1  THEN COALESCE(fss.size_35_amount, 0)
                WHEN 2  THEN COALESCE(fss.size_36_amount, 0)
                WHEN 3  THEN COALESCE(fss.size_37_amount, 0)
                WHEN 4  THEN COALESCE(fss.size_38_amount, 0)
                WHEN 5  THEN COALESCE(fss.size_39_amount, 0)
                WHEN 6  THEN COALESCE(fss.size_40_amount, 0)
                WHEN 7  THEN COALESCE(fss.size_41_amount, 0)
                WHEN 8  THEN COALESCE(fss.size_42_amount, 0)
                WHEN 9  THEN COALESCE(fss.size_43_amount, 0)
                WHEN 10 THEN COALESCE(fss.size_44_amount, 0)
                WHEN 11 THEN COALESCE(fss.size_45_amount, 0)
                WHEN 12 THEN COALESCE(fss.size_46_amount, 0)
            END AS current_amount
        FROM finished_shoe_storage fss
        JOIN (
            SELECT 0 AS order_number, '34' AS size_value
            UNION ALL SELECT 1, '35'
            UNION ALL SELECT 2, '36'
            UNION ALL SELECT 3, '37'
            UNION ALL SELECT 4, '38'
            UNION ALL SELECT 5, '39'
            UNION ALL SELECT 6, '40'
            UNION ALL SELECT 7, '41'
            UNION ALL SELECT 8, '42'
            UNION ALL SELECT 9, '43'
            UNION ALL SELECT 10, '44'
            UNION ALL SELECT 11, '45'
            UNION ALL SELECT 12, '46'
        ) sz ON 1 = 1
        ON DUPLICATE KEY UPDATE
            estimated_amount = VALUES(estimated_amount),
            actual_amount    = VALUES(actual_amount),
            current_amount   = VALUES(current_amount),
            update_time      = CURRENT_TIMESTAMP
        """
    )
    db.session.execute(sql_storage, {"snapshot_date": snapshot_date})
    db.session.execute(sql_size, {"snapshot_date": snapshot_date})
    db.session.commit()


def _build_base_query(base_date: date, filters: dict):
    q = (
        db.session.query(
            FinishedShoeStorageSnapshot,
            Order,
            OrderShoe,
            Shoe,
            Color,
            Customer,
            OrderShoeType,
        )
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == FinishedShoeStorageSnapshot.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .filter(FinishedShoeStorageSnapshot.snapshot_date == base_date)
    )

    order_rid = filters.get("orderRId")
    shoe_rid = filters.get("shoeRId")
    customer_name = filters.get("customerName")
    customer_brand = filters.get("customerBrand")
    color_name = filters.get("colorName")

    if order_rid:
        q = q.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid:
        q = q.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if customer_name:
        q = q.filter(Customer.customer_name.ilike(f"%{customer_name}%"))
    if customer_brand:
        q = q.filter(Customer.customer_brand.ilike(f"%{customer_brand}%"))
    if color_name:
        q = q.filter(Color.color_name.ilike(f"%{color_name}%"))

    return q


def _fetch_delta_map(start_date: date, end_date: date):
    rows = (
        db.session.query(
            DailyFinishedShoeStorageChange.finished_shoe_storage_id.label("fsid"),
            func.coalesce(func.sum(DailyFinishedShoeStorageChange.inbound_amount_sum), 0).label("in_sum"),
            func.coalesce(func.sum(DailyFinishedShoeStorageChange.outbound_amount_sum), 0).label("out_sum"),
            func.coalesce(func.sum(DailyFinishedShoeStorageChange.net_change), 0).label("net_sum"),
        )
        .filter(
            DailyFinishedShoeStorageChange.snapshot_date >= start_date,
            DailyFinishedShoeStorageChange.snapshot_date <= end_date,
        )
        .group_by(DailyFinishedShoeStorageChange.finished_shoe_storage_id)
        .all()
    )
    return {
        r.fsid: {"in": int(r.in_sum), "out": int(r.out_sum), "net": int(r.net_sum)} for r in rows
    }


def _fetch_size_base_map(base_date: date, fsids: list[int]):
    size_rows = (
        db.session.query(FinishedShoeSizeDetailSnapshot)
        .filter(
            FinishedShoeSizeDetailSnapshot.snapshot_date == base_date,
            FinishedShoeSizeDetailSnapshot.finished_shoe_storage_id.in_(fsids),
        )
        .all()
    )
    result = {}
    for row in size_rows:
        result.setdefault(row.finished_shoe_storage_id, {})[row.order_number] = {
            "size_value": row.size_value,
            "estimated": row.estimated_amount or 0,
            "actual": row.actual_amount or 0,
            "current": row.current_amount or 0,
        }
    return result


def _fetch_size_delta_map(start_date: date, end_date: date, fsids: list[int]):
    rows = (
        db.session.query(
            DailyFinishedShoeStorageChange.finished_shoe_storage_id.label("fsid"),
            DailyFinishedShoeSizeDetailChange.order_number.label("order_number"),
            func.coalesce(func.sum(DailyFinishedShoeSizeDetailChange.inbound_amount_sum), 0).label("in_sum"),
            func.coalesce(func.sum(DailyFinishedShoeSizeDetailChange.outbound_amount_sum), 0).label("out_sum"),
            func.max(DailyFinishedShoeSizeDetailChange.size_value).label("size_value"),
        )
        .join(
            DailyFinishedShoeStorageChange,
            DailyFinishedShoeStorageChange.daily_change_id == DailyFinishedShoeSizeDetailChange.daily_change_id,
        )
        .filter(
            DailyFinishedShoeStorageChange.snapshot_date >= start_date,
            DailyFinishedShoeStorageChange.snapshot_date <= end_date,
            DailyFinishedShoeStorageChange.finished_shoe_storage_id.in_(fsids),
        )
        .group_by(DailyFinishedShoeStorageChange.finished_shoe_storage_id, DailyFinishedShoeSizeDetailChange.order_number)
        .all()
    )
    result = {}
    for row in rows:
        result.setdefault(row.fsid, {})[row.order_number] = {
            "in": int(row.in_sum),
            "out": int(row.out_sum),
            "size_value": row.size_value,
        }
    return result


def _normalize_row(snapshot_row, order, order_shoe, shoe, color, customer, delta_map, size_base, size_delta):
    fsid = snapshot_row.finished_shoe_storage_id
    delta = delta_map.get(fsid, {"in": 0, "out": 0, "net": 0})

    final_actual = (snapshot_row.finished_actual_amount or 0) + delta["in"]
    final_current = (snapshot_row.finished_amount or 0) + delta["net"]

    size_breakdown = []
    base_sizes = size_base.get(fsid, {})
    delta_sizes = size_delta.get(fsid, {})

    max_order_number = max(
        list(base_sizes.keys()) + list(delta_sizes.keys()) + list(range(0, 13)), default=0
    )
    for idx in range(max_order_number + 1):
        base = base_sizes.get(idx, {})
        delta_s = delta_sizes.get(idx, {})
        size_val = delta_s.get("size_value") or base.get("size_value")
        if size_val is None:
            continue
        estimated = base.get("estimated", 0)
        actual = base.get("actual", 0) + delta_s.get("in", 0)
        current = base.get("current", 0) + delta_s.get("in", 0) - delta_s.get("out", 0)
        size_breakdown.append(
            {
                "orderNumber": idx,
                "size": size_val,
                "estimatedAmount": estimated,
                "actualAmount": actual,
                "currentAmount": current,
            }
        )

    return {
        "storageId": fsid,
        "orderRId": order.order_rid,
        "orderCId": order.order_cid,
        "shoeRId": shoe.shoe_rid,
        "customerName": customer.customer_name,
        "customerBrand": customer.customer_brand,
        "customerProductName": order_shoe.customer_product_name,
        "colorName": color.color_name,
        "finishedEstimatedAmount": snapshot_row.finished_estimated_amount or 0,
        "finishedActualAmount": final_actual,
        "finishedAmount": final_current,
        "finishedStatus": snapshot_row.finished_status,
        "finishedStatusLabel": FINISHED_STORAGE_STATUS.get(snapshot_row.finished_status, ""),
        "sizeColumns": size_breakdown,
    }


def _query_inventory(filters: dict, paginate: bool = True):
    target_date = _parse_date_or_default(filters.get("snapshotDate"))
    base_date = _get_base_snapshot_date(target_date)
    if not base_date:
        _create_snapshot_for_date(target_date)
        base_date = target_date

    start_change_date = base_date + timedelta(days=1)
    base_q = _build_base_query(base_date, filters)
    snapshots = base_q.order_by(Order.order_rid.asc()).all()

    fsids = [snap.FinishedShoeStorageSnapshot.finished_shoe_storage_id for snap in snapshots]
    delta_map = _fetch_delta_map(start_change_date, target_date)
    size_base = _fetch_size_base_map(base_date, fsids)
    size_delta = _fetch_size_delta_map(start_change_date, target_date, fsids)

    display_zero = str(filters.get("displayZeroInventory", "false")).lower() == "true"

    # 先算全量，再做零库存过滤和分页，避免“空白页”问题
    items_all = []
    for snap, order, order_shoe, shoe, color, customer, order_shoe_type in snapshots:
        row = _normalize_row(
            snap,
            order,
            order_shoe,
            shoe,
            color,
            customer,
            delta_map,
            size_base,
            size_delta,
        )
        if not display_zero and row["finishedAmount"] <= 0:
            continue
        items_all.append(row)

    total = len(items_all)
    if not paginate:
        return {"total": total, "items": items_all}

    page = max(int(filters.get("page", 1)), 1)
    page_size = max(int(filters.get("pageSize", 20)), 1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return {"total": total, "items": items_all[start_idx:end_idx]}


@finished_storage_snapshot_bp.route("/warehouse/getfinishedinventoryhistory", methods=["GET"])
def get_finished_inventory_history():
    data = _query_inventory(request.args, paginate=True)
    return jsonify({"data": data})


@finished_storage_snapshot_bp.route("/warehouse/export/finished-inventory-history", methods=["GET"])
def export_finished_inventory_history():
    data = _query_inventory(request.args, paginate=False)
    output = StringIO()
    writer = csv.writer(output)
    headers = [
        "订单号",
        "工厂型号",
        "客户名称",
        "客户品牌",
        "客户鞋型",
        "颜色",
        "计划入库",
        "实际入库",
        "当前库存",
        "状态",
        # "尺码分布",
    ]
    writer.writerow(headers)
    for row in data["items"]:
        size_text = "; ".join([f"{c['size']}:{c['currentAmount']}" for c in row.get("sizeColumns", [])])
        writer.writerow(
            [
                row.get("orderRId"),
                row.get("shoeRId"),
                row.get("customerName"),
                row.get("customerBrand"),
                row.get("customerProductName"),
                row.get("colorName"),
                row.get("finishedEstimatedAmount"),
                row.get("finishedActualAmount"),
                row.get("finishedAmount"),
                row.get("finishedStatusLabel"),
                # size_text,
            ]
        )

    csv_bytes = output.getvalue().encode("utf-8-sig")
    filename = f"finished_inventory_history_{request.args.get('snapshotDate') or date.today().isoformat()}.csv"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "text/csv; charset=utf-8",
    }
    return Response(csv_bytes, headers=headers)

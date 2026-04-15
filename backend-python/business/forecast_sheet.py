import os
import shutil
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from app_config import db
from file_locations import FILE_STORAGE_PATH
from general_document.order_export import generate_excel_file, generate_amount_excel_file
from login.login import current_user_info
from models import (
    BatchInfoType,
    Customer,
    ForecastSheet,
    ForecastSheetItem,
    Order,
    OrderShoe,
    OrderShoeBatchInfo,
    OrderShoeProductionInfo,
    OrderShoeStatus,
    OrderShoeType,
    OrderStatus,
    PackagingInfo,
    Shoe,
    ShoeType,
)


forecast_sheet_bp = Blueprint("forecast_sheet_bp", __name__)

FORECAST_STATUS_DRAFT = 0
FORECAST_STATUS_DISPATCHED = 1
FORECAST_STATUS_PARTIAL = 2

FORECAST_PACKAGING_FILE_NAME = "包装资料.xlsx"


def _split_csv_values(raw_text):
    if raw_text is None:
        return []
    return [part.strip() for part in str(raw_text).split(",") if str(part).strip()]


def _parse_created_order_ids(raw_text):
    tokens = _split_csv_values(raw_text)
    parsed_ids = []
    unresolved_rids = []

    for token in tokens:
        if token.isdigit():
            parsed_ids.append(int(token))
        else:
            unresolved_rids.append(token)

    if unresolved_rids:
        rid_rows = (
            db.session.query(Order.order_id, Order.order_rid)
            .filter(Order.order_rid.in_(unresolved_rids))
            .all()
        )
        rid_to_id = {rid: int(order_id) for order_id, rid in rid_rows}
        for rid in unresolved_rids:
            mapped_id = rid_to_id.get(rid)
            if mapped_id is not None:
                parsed_ids.append(mapped_id)

    deduped_ids = []
    seen = set()
    for order_id in parsed_ids:
        if order_id in seen:
            continue
        seen.add(order_id)
        deduped_ids.append(order_id)
    return deduped_ids


def _build_unique_forecast_rid(seed_value: str = "YBD") -> str:
    base = (seed_value or "YBD").strip()[:20]
    serial = 1
    while True:
        now_text = datetime.now().strftime("%Y%m%d")
        rid = f"{base}-{now_text}-{serial:03d}"
        exists = db.session.query(ForecastSheet.forecast_sheet_id).filter(
            ForecastSheet.forecast_rid == rid
        ).first()
        if not exists:
            return rid
        serial += 1


def _build_unique_order_rid_from_forecast(forecast_rid: str, index: int) -> str:
    prefix = (forecast_rid or "YBD").strip()
    serial = 0
    while True:
        suffix = f"-S{index}" if serial == 0 else f"-S{index}-{serial}"
        candidate = f"{prefix}{suffix}"
        if len(candidate) > 40:
            candidate = candidate[:40]
        exists = db.session.query(Order.order_id).filter(Order.order_rid == candidate).first()
        if not exists:
            return candidate
        serial += 1


def _resolve_forecast_storage_path(forecast_rid: str) -> str:
    return os.path.join(FILE_STORAGE_PATH, str(forecast_rid or "").strip())


def _resolve_order_storage_dir_name(order_id, order_rid):
    rid = str(order_rid or "").strip()
    if rid:
        return rid
    return f"_NO_RID_{order_id}"


def _resolve_order_storage_path(order_id, order_rid):
    return os.path.join(FILE_STORAGE_PATH, _resolve_order_storage_dir_name(order_id, order_rid))


def _resolve_forecast_packaging_file_path(forecast_rid: str) -> str:
    return os.path.join(_resolve_forecast_storage_path(forecast_rid), FORECAST_PACKAGING_FILE_NAME)


def _ensure_forecast_storage_dir(forecast_rid: str):
    storage_path = _resolve_forecast_storage_path(forecast_rid)
    os.makedirs(storage_path, exist_ok=True)
    return storage_path


def _is_forecast_packaging_uploaded(forecast_rid: str) -> bool:
    file_path = _resolve_forecast_packaging_file_path(forecast_rid)
    return os.path.exists(file_path)


@forecast_sheet_bp.route("/forecastsheet/list", methods=["GET"])
def list_forecast_sheets():
    character, staff, _ = current_user_info()
    role_id = int(character.character_id)

    query = (
        db.session.query(ForecastSheet, Customer)
        .join(Customer, ForecastSheet.customer_id == Customer.customer_id)
    )
    if role_id == 21:
        query = query.filter(ForecastSheet.salesman_id == staff.staff_id)

    entities = query.order_by(ForecastSheet.forecast_sheet_id.desc()).all()
    sheet_ids = [sheet.forecast_sheet_id for sheet, _ in entities]
    item_count_map = {}
    if sheet_ids:
        rows = (
            db.session.query(
                ForecastSheetItem.forecast_sheet_id,
                db.func.count(ForecastSheetItem.forecast_sheet_item_id),
            )
            .filter(ForecastSheetItem.forecast_sheet_id.in_(sheet_ids))
            .group_by(ForecastSheetItem.forecast_sheet_id)
            .all()
        )
        item_count_map = {sheet_id: count for sheet_id, count in rows}

    sheet_order_ids_map = {}
    all_order_ids = set()
    for sheet, _ in entities:
        created_order_ids = _parse_created_order_ids(sheet.created_order_ids)
        sheet_order_ids_map[sheet.forecast_sheet_id] = created_order_ids
        all_order_ids.update(created_order_ids)

    order_rid_map = {}
    if all_order_ids:
        order_rows = (
            db.session.query(Order.order_id, Order.order_rid)
            .filter(Order.order_id.in_(all_order_ids))
            .all()
        )
        order_rid_map = {int(order_id): order_rid for order_id, order_rid in order_rows}

    result = []
    for sheet, customer in entities:
        created_order_ids = sheet_order_ids_map.get(sheet.forecast_sheet_id, [])
        created_order_rids = [order_rid_map.get(order_id) for order_id in created_order_ids]
        created_order_rids = [value for value in created_order_rids if value]
        result.append(
            {
                "forecastSheetId": sheet.forecast_sheet_id,
                "forecastRid": sheet.forecast_rid,
                "forecastCid": sheet.forecast_cid,
                "currencyType": (sheet.currency_type or "RMB"),
                "customerId": sheet.customer_id,
                "batchInfoTypeId": sheet.batch_info_type_id,
                "salesmanId": sheet.salesman_id,
                "supervisorId": sheet.supervisor_id,
                "customerName": customer.customer_name,
                "customerBrand": customer.customer_brand,
                "startDate": sheet.start_date.strftime("%Y-%m-%d") if sheet.start_date else "",
                "endDate": sheet.end_date.strftime("%Y-%m-%d") if sheet.end_date else "",
                "status": sheet.status,
                "statusText": "已下发" if sheet.status == FORECAST_STATUS_DISPATCHED else ("部分下发" if sheet.status == FORECAST_STATUS_PARTIAL else "草稿"),
                "itemCount": item_count_map.get(sheet.forecast_sheet_id, 0),
                "packagingUploaded": _is_forecast_packaging_uploaded(sheet.forecast_rid),
                "createdOrderIds": ",".join([str(order_id) for order_id in created_order_ids]),
                "createdOrderRids": ",".join(created_order_rids),
            }
        )
    return jsonify(result), 200


@forecast_sheet_bp.route("/forecastsheet/items", methods=["GET"])
def get_forecast_sheet_items():
    sheet_id = request.args.get("forecastSheetId", type=int)
    if not sheet_id:
        return jsonify({"error": "forecastSheetId is required"}), 400

    entities = (
        db.session.query(ForecastSheetItem)
        .filter(ForecastSheetItem.forecast_sheet_id == sheet_id)
        .order_by(ForecastSheetItem.sort_index.asc(), ForecastSheetItem.forecast_sheet_item_id.asc())
        .all()
    )
    packaging_ids = [
        int(item.packaging_info_id)
        for item in entities
        if item.packaging_info_id and int(item.packaging_info_id) > 0
    ]
    ratio_map = {}
    if packaging_ids:
        packaging_rows = (
            db.session.query(PackagingInfo.packaging_info_id, PackagingInfo.total_quantity_ratio)
            .filter(PackagingInfo.packaging_info_id.in_(list(set(packaging_ids))))
            .all()
        )
        ratio_map = {
            int(packaging_info_id): float(total_quantity_ratio or 0)
            for packaging_info_id, total_quantity_ratio in packaging_rows
        }
    result = []
    for item in entities:
        ratio_total = ratio_map.get(int(item.packaging_info_id or 0), 0)
        packaging_info_quantity = 0
        if ratio_total > 0:
            packaging_info_quantity = float(item.total_pairs or 0) / ratio_total
        result.append(
            {
                "forecastSheetItemId": item.forecast_sheet_item_id,
                "sortIndex": item.sort_index,
                "shoeTypeId": item.shoe_type_id,
                "shoeRid": item.shoe_rid,
                "colorName": item.color_name,
                "customerShoeName": item.customer_shoe_name,
                "customerColorName": item.customer_color_name,
                "packagingInfoId": item.packaging_info_id,
                "packagingInfoName": item.packaging_info_name,
                "totalQuantityRatio": ratio_total,
                "packagingInfoQuantity": packaging_info_quantity,
                "unitPrice": float(item.unit_price or 0),
                "totalPairs": item.total_pairs,
                "dispatchStatus": int(item.dispatch_status or 0),
            }
        )
    return jsonify(result), 200


@forecast_sheet_bp.route("/forecastsheet/downloadexcel", methods=["GET"])
def download_forecast_sheet_excel():
    sheet_id = request.args.get("forecastSheetId", type=int)
    output_type = request.args.get("outputType", default=0, type=int)
    if not sheet_id:
        return jsonify({"error": "forecastSheetId is required"}), 400

    sheet = (
        db.session.query(ForecastSheet)
        .filter(ForecastSheet.forecast_sheet_id == sheet_id)
        .first()
    )
    if not sheet:
        return jsonify({"error": "forecast sheet not found"}), 404

    items = (
        db.session.query(ForecastSheetItem)
        .filter(ForecastSheetItem.forecast_sheet_id == sheet_id)
        .order_by(ForecastSheetItem.sort_index.asc(), ForecastSheetItem.forecast_sheet_item_id.asc())
        .all()
    )
    if not items:
        return jsonify({"error": "预报单没有鞋型数据"}), 400

    batch_info_type = (
        db.session.query(BatchInfoType)
        .filter(BatchInfoType.batch_info_type_id == sheet.batch_info_type_id)
        .first()
    )
    size_names = []
    for size in range(34, 47):
        size_names.append(getattr(batch_info_type, f"size_{size}_name", "") if batch_info_type else "")

    packaging_ids = list(
        {
            int(item.packaging_info_id)
            for item in items
            if item.packaging_info_id and int(item.packaging_info_id) > 0
        }
    )
    packaging_map = {}
    if packaging_ids:
        packaging_rows = (
            db.session.query(PackagingInfo)
            .filter(PackagingInfo.packaging_info_id.in_(packaging_ids))
            .all()
        )
        packaging_map = {int(row.packaging_info_id): row for row in packaging_rows}

    shoe_type_ids = list(
        {
            int(item.shoe_type_id)
            for item in items
            if item.shoe_type_id and int(item.shoe_type_id) > 0
        }
    )
    shoe_type_map = {}
    if shoe_type_ids:
        shoe_type_rows = (
            db.session.query(ShoeType)
            .filter(ShoeType.shoe_type_id.in_(shoe_type_ids))
            .all()
        )
        shoe_type_map = {int(row.shoe_type_id): row for row in shoe_type_rows}

    forecast_mapping = {}
    currency_type = str(sheet.currency_type or "RMB").upper()

    grouped_items = {}
    for item in items:
        group_key = int(item.sort_index or 0)
        grouped_items.setdefault(group_key, []).append(item)

    for group_key in sorted(grouped_items.keys()):
        group_rows = grouped_items[group_key]
        first = group_rows[0]
        shoe_type = shoe_type_map.get(int(first.shoe_type_id or 0))
        shoe_meta = {
            "color": first.color_name or "",
            "colorName": first.customer_color_name or first.color_name or "",
            "imgUrl": getattr(shoe_type, "shoe_image_url", "") or "",
            "unitPrice": float(first.unit_price or 0),
            "packagingInfo": [],
            "currency_type": currency_type,
        }

        for row in group_rows:
            packaging = packaging_map.get(int(row.packaging_info_id or 0))
            ratio_total = float(getattr(packaging, "total_quantity_ratio", 0) or 0)
            count = (float(row.total_pairs or 0) / ratio_total) if ratio_total > 0 else 0
            packaging_obj = {
                "packagingInfoName": row.packaging_info_name or getattr(packaging, "packaging_info_name", "") or "",
                "packagingInfoLocale": getattr(packaging, "packaging_info_locale", "") if packaging else "",
                "totalQuantityRatio": ratio_total,
                "count": count,
                "sizeNames": size_names,
            }
            for size in range(34, 47):
                ratio_value = getattr(packaging, f"size_{size}_ratio", 0) if packaging else 0
                packaging_obj[f"size{size}Ratio"] = ratio_value
            shoe_meta["packagingInfo"].append(packaging_obj)

        forecast_mapping[group_key] = {
            "orderRId": sheet.forecast_rid,
            "customerProductName": first.customer_shoe_name or first.shoe_rid or "",
            "shoeRId": first.shoe_rid or "",
            "shoes": [shoe_meta],
            "remark": "",
            "currencyType": currency_type,
        }

    template_path = os.path.join(FILE_STORAGE_PATH, "订单模板.xlsx")
    if not os.path.exists(template_path):
        return jsonify({"error": "订单模板.xlsx 不存在"}), 404

    output_dir = os.path.join(FILE_STORAGE_PATH, "业务部文件", "导出预报单")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if output_type == 0:
        new_file_name = f"导出配码预报单_{sheet.forecast_rid}_{timestamp}.xlsx"
        send_name = f"导出配码预报单_{sheet.forecast_rid}.xlsx"
    else:
        new_file_name = f"导出数量预报单_{sheet.forecast_rid}_{timestamp}.xlsx"
        send_name = f"导出数量预报单_{sheet.forecast_rid}.xlsx"
    new_file_path = os.path.join(output_dir, new_file_name)

    if output_type == 0:
        generate_excel_file(template_path, new_file_path, forecast_mapping, {"sizeNames": size_names})
    else:
        generate_amount_excel_file(template_path, new_file_path, forecast_mapping, {"sizeNames": size_names})
    return send_file(new_file_path, as_attachment=True, download_name=send_name)


@forecast_sheet_bp.route("/forecastsheet/create", methods=["POST"])
def create_forecast_sheet():
    payload = request.json or {}
    info = payload.get("forecastInfo") or {}
    items = payload.get("items") or []

    if not items:
        return jsonify({"error": "预报单鞋型不能为空"}), 400

    forecast_rid = (info.get("forecastRid") or "").strip() or _build_unique_forecast_rid()
    existed = db.session.query(ForecastSheet.forecast_sheet_id).filter(
        ForecastSheet.forecast_rid == forecast_rid
    ).first()
    if existed:
        return jsonify({"error": "预报单号已存在"}), 400

    customer_id = info.get("customerId")
    batch_info_type_id = info.get("batchInfoTypeId")
    salesman_id = info.get("salesmanId")
    supervisor_id = info.get("supervisorId")
    currency_type = str(info.get("currencyType") or "RMB").strip().upper()
    today = datetime.now().date()
    start_date = info.get("startDate") or today
    end_date = info.get("endDate") or today
    forecast_cid = info.get("forecastCid")

    if not customer_id or not batch_info_type_id or not salesman_id or not supervisor_id:
        return jsonify({"error": "客户、配码种类、业务员、审批经理不能为空"}), 400

    sheet = ForecastSheet(
        forecast_rid=forecast_rid,
        forecast_cid=forecast_cid,
        customer_id=customer_id,
        batch_info_type_id=batch_info_type_id,
        start_date=start_date,
        end_date=end_date,
        salesman_id=salesman_id,
        supervisor_id=supervisor_id,
        currency_type=currency_type,
        status=FORECAST_STATUS_DRAFT,
        created_order_ids="",
    )
    db.session.add(sheet)
    db.session.flush()

    for idx, item in enumerate(items, start=1):
        shoe_type_id = item.get("shoeTypeId")
        packaging_info_id = item.get("packagingInfoId")
        sort_index = item.get("sortIndex")
        if sort_index is None:
            sort_index = item.get("sort_index")
        try:
            sort_index = int(sort_index)
        except (TypeError, ValueError):
            sort_index = idx
        unit_price = float(item.get("unitPrice") or 0)
        total_pairs = int(item.get("totalPairs") or 0)
        if unit_price < 0:
            db.session.rollback()
            return jsonify({"error": f"第{idx}行单价不能小于0"}), 400
        if not shoe_type_id or total_pairs <= 0:
            db.session.rollback()
            return jsonify({"error": f"第{idx}行鞋型数据不完整"}), 400

        row = ForecastSheetItem(
            forecast_sheet_id=sheet.forecast_sheet_id,
            shoe_type_id=shoe_type_id,
            shoe_rid=item.get("shoeRid"),
            color_name=item.get("colorName"),
            customer_shoe_name=item.get("customerShoeName") or "",
            customer_color_name=item.get("customerColorName") or "",
            packaging_info_id=packaging_info_id or 0,
            packaging_info_name=item.get("packagingInfoName") or "",
            unit_price=unit_price,
            total_pairs=total_pairs,
            sort_index=sort_index,
        )
        db.session.add(row)

    db.session.commit()
    _ensure_forecast_storage_dir(sheet.forecast_rid)
    return jsonify({"message": "ok", "forecastSheetId": sheet.forecast_sheet_id}), 200


@forecast_sheet_bp.route("/forecastsheet/update", methods=["POST"])
def update_forecast_sheet():
    payload = request.json or {}
    sheet_id = payload.get("forecastSheetId")
    info = payload.get("forecastInfo") or {}
    items = payload.get("items") or []

    if not sheet_id:
        return jsonify({"error": "forecastSheetId is required"}), 400
    if not items:
        return jsonify({"error": "预报单鞋型不能为空"}), 400

    sheet = db.session.query(ForecastSheet).filter(ForecastSheet.forecast_sheet_id == sheet_id).first()
    if not sheet:
        return jsonify({"error": "forecast sheet not found"}), 404
    if sheet.status in (FORECAST_STATUS_DISPATCHED, FORECAST_STATUS_PARTIAL):
        return jsonify({"error": "已下发（含部分下发）预报单不允许编辑"}), 400

    forecast_rid = (info.get("forecastRid") or "").strip()
    if not forecast_rid:
        return jsonify({"error": "预报单号不能为空"}), 400

    existed = (
        db.session.query(ForecastSheet.forecast_sheet_id)
        .filter(
            ForecastSheet.forecast_rid == forecast_rid,
            ForecastSheet.forecast_sheet_id != sheet.forecast_sheet_id,
        )
        .first()
    )
    if existed:
        return jsonify({"error": "预报单号已存在"}), 400

    customer_id = info.get("customerId")
    batch_info_type_id = info.get("batchInfoTypeId")
    salesman_id = info.get("salesmanId") or sheet.salesman_id
    supervisor_id = info.get("supervisorId")
    currency_type = str(info.get("currencyType") or sheet.currency_type or "RMB").strip().upper()
    start_date = info.get("startDate") or sheet.start_date
    end_date = info.get("endDate") or sheet.end_date
    forecast_cid = info.get("forecastCid")

    if not customer_id or not batch_info_type_id or not salesman_id or not supervisor_id:
        return jsonify({"error": "客户、配码种类、业务员、审批经理不能为空"}), 400

    try:
        old_forecast_rid = sheet.forecast_rid
        sheet.forecast_rid = forecast_rid
        sheet.forecast_cid = forecast_cid
        sheet.customer_id = customer_id
        sheet.batch_info_type_id = batch_info_type_id
        sheet.start_date = start_date
        sheet.end_date = end_date
        sheet.salesman_id = salesman_id
        sheet.supervisor_id = supervisor_id
        sheet.currency_type = currency_type

        db.session.query(ForecastSheetItem).filter(ForecastSheetItem.forecast_sheet_id == sheet.forecast_sheet_id).delete()

        for idx, item in enumerate(items, start=1):
            shoe_type_id = item.get("shoeTypeId")
            packaging_info_id = item.get("packagingInfoId")
            sort_index = item.get("sortIndex")
            if sort_index is None:
                sort_index = item.get("sort_index")
            try:
                sort_index = int(sort_index)
            except (TypeError, ValueError):
                sort_index = idx
            unit_price = float(item.get("unitPrice") or 0)
            total_pairs = int(item.get("totalPairs") or 0)
            if unit_price < 0:
                raise ValueError(f"第{idx}行单价不能小于0")
            if not shoe_type_id or total_pairs <= 0:
                raise ValueError(f"第{idx}行鞋型数据不完整")

            row = ForecastSheetItem(
                forecast_sheet_id=sheet.forecast_sheet_id,
                shoe_type_id=shoe_type_id,
                shoe_rid=item.get("shoeRid"),
                color_name=item.get("colorName"),
                customer_shoe_name=item.get("customerShoeName") or "",
                customer_color_name=item.get("customerColorName") or "",
                packaging_info_id=packaging_info_id or 0,
                packaging_info_name=item.get("packagingInfoName") or "",
                unit_price=unit_price,
                total_pairs=total_pairs,
                sort_index=sort_index,
            )
            db.session.add(row)

        db.session.commit()
        old_storage_path = _resolve_forecast_storage_path(old_forecast_rid)
        new_storage_path = _resolve_forecast_storage_path(sheet.forecast_rid)
        if old_forecast_rid != sheet.forecast_rid and os.path.exists(old_storage_path) and not os.path.exists(new_storage_path):
            os.rename(old_storage_path, new_storage_path)
        else:
            _ensure_forecast_storage_dir(sheet.forecast_rid)
    except Exception as ex:
        db.session.rollback()
        return jsonify({"error": str(ex)}), 400

    return jsonify({"message": "ok", "forecastSheetId": sheet.forecast_sheet_id}), 200


@forecast_sheet_bp.route("/forecastsheet/delete", methods=["POST"])
def delete_forecast_sheet():
    payload = request.json or {}
    sheet_id = payload.get("forecastSheetId")
    if not sheet_id:
        return jsonify({"error": "forecastSheetId is required"}), 400

    sheet = db.session.query(ForecastSheet).filter(ForecastSheet.forecast_sheet_id == sheet_id).first()
    if not sheet:
        return jsonify({"error": "forecast sheet not found"}), 404
    if sheet.status in (FORECAST_STATUS_DISPATCHED, FORECAST_STATUS_PARTIAL):
        return jsonify({"error": "已下发（含部分下发）预报单不允许删除"}), 400

    try:
        db.session.query(ForecastSheetItem).filter(ForecastSheetItem.forecast_sheet_id == sheet.forecast_sheet_id).delete()
        db.session.delete(sheet)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        return jsonify({"error": str(ex)}), 400

    return jsonify({"message": "ok"}), 200


@forecast_sheet_bp.route("/forecastsheet/dispatch", methods=["POST"])
def dispatch_forecast_sheet():
    sheet_id = request.json.get("forecastSheetId")
    start_date = request.json.get("startDate")
    end_date = request.json.get("endDate")
    order_rid_mappings = request.json.get("orderRidMappings") or []
    if not sheet_id:
        return jsonify({"error": "forecastSheetId is required"}), 400
    if not start_date or not end_date:
        return jsonify({"error": "startDate and endDate are required"}), 400
    if not order_rid_mappings:
        return jsonify({"error": "请至少选择一个鞋型进行下发"}), 400

    sheet = db.session.query(ForecastSheet).filter(ForecastSheet.forecast_sheet_id == sheet_id).first()
    if not sheet:
        return jsonify({"error": "forecast sheet not found"}), 404
    if sheet.status == FORECAST_STATUS_DISPATCHED:
        return jsonify({"error": "预报单已全部下发"}), 400

    items = (
        db.session.query(ForecastSheetItem)
        .filter(ForecastSheetItem.forecast_sheet_id == sheet_id)
        .order_by(ForecastSheetItem.sort_index.asc(), ForecastSheetItem.forecast_sheet_item_id.asc())
        .all()
    )
    if not items:
        return jsonify({"error": "预报单无鞋型，无法下发"}), 400

    # Build set of selected group keys from frontend
    selected_group_keys = set()
    for entry in order_rid_mappings:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("groupKey") or entry.get("shoeId") or entry.get("shoeRid") or "")
        if key:
            selected_group_keys.add(key)

    forecast_packaging_file_path = _resolve_forecast_packaging_file_path(sheet.forecast_rid)
    if not os.path.exists(forecast_packaging_file_path):
        return jsonify({"error": "预报单未上传包装资料，无法拆分订单"}), 400

    shoe_group_items = {}
    shoe_group_meta = {}
    all_items_by_group = {}
    for item in items:
        shoe_type = db.session.query(ShoeType).filter(ShoeType.shoe_type_id == item.shoe_type_id).first()
        if not shoe_type:
            return jsonify({"error": f"鞋型不存在，item={item.forecast_sheet_item_id}"}), 400
        shoe = db.session.query(Shoe).filter(Shoe.shoe_id == shoe_type.shoe_id).first()
        if not shoe:
            return jsonify({"error": f"鞋基础信息不存在，item={item.forecast_sheet_item_id}"}), 400

        group_key = str(shoe.shoe_id)
        all_items_by_group.setdefault(group_key, []).append(item)

        # Only process selected (non-dispatched) groups
        # Frontend may use shoeRid as groupKey, backend uses shoe_id
        is_selected = group_key in selected_group_keys or str(shoe.shoe_rid or "") in selected_group_keys
        if not is_selected:
            continue
        if int(item.dispatch_status or 0) == 1:
            continue

        shoe_group_items.setdefault(group_key, []).append(item)
        customer_shoe_name = str(item.customer_shoe_name or "").strip()
        existing_customer_shoe_name = str((shoe_group_meta.get(group_key) or {}).get("customerShoeName") or "").strip()
        shoe_group_meta[group_key] = {
            "shoeId": shoe.shoe_id,
            "shoeRid": shoe.shoe_rid,
            "customerShoeName": existing_customer_shoe_name or customer_shoe_name,
        }

    if not shoe_group_items:
        return jsonify({"error": "所选鞋型均已下发或无有效鞋型"}), 400

    # Only check packaging for selected items
    for group_key, group_items in shoe_group_items.items():
        for item in group_items:
            if not (item.packaging_info_id and int(item.packaging_info_id) > 0):
                return jsonify({"error": "请先在主页面完成鞋型配码编辑后再下发"}), 400

    order_rid_map = {}
    for entry in order_rid_mappings:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("groupKey") or entry.get("shoeId") or entry.get("shoeRid") or "")
        rid = str(entry.get("orderRid") or "").strip()
        if key and rid:
            order_rid_map[key] = rid

    duplicate_check = {}
    for group_key, meta in shoe_group_meta.items():
        candidates = [
            str(group_key),
            str(meta.get("shoeId") or ""),
            str(meta.get("shoeRid") or ""),
        ]
        order_rid = ""
        for candidate in candidates:
            if candidate and order_rid_map.get(candidate):
                order_rid = order_rid_map.get(candidate)
                break
        if not order_rid:
            return jsonify({"error": f"鞋型 {meta.get('shoeRid') or meta.get('shoeId')} 缺少订单号"}), 400
        if order_rid in duplicate_check:
            return jsonify({"error": f"订单号重复：{order_rid}"}), 400
        duplicate_check[order_rid] = True
        existed = db.session.query(Order.order_id).filter(Order.order_rid == order_rid).first()
        if existed:
            return jsonify({"error": f"订单号已存在：{order_rid}"}), 400

    created_order_ids = []
    created_order_rids = []
    try:
        for group_key, group_items in shoe_group_items.items():
            meta = shoe_group_meta.get(group_key) or {}
            order_rid = ""
            for candidate in [str(group_key), str(meta.get("shoeId") or ""), str(meta.get("shoeRid") or "")]:
                if candidate and order_rid_map.get(candidate):
                    order_rid = order_rid_map.get(candidate)
                    break
            if not order_rid:
                raise ValueError("缺少订单号")

            order = Order(
                order_rid=order_rid,
                order_cid=None,
                order_type="N",
                batch_info_type_id=sheet.batch_info_type_id,
                customer_id=sheet.customer_id,
                start_date=start_date,
                end_date=end_date,
                salesman_id=sheet.salesman_id,
                production_list_upload_status="2",
                amount_list_upload_status="0",
                supervisor_id=sheet.supervisor_id,
            )
            db.session.add(order)
            db.session.flush()

            order_storage_path = _resolve_order_storage_path(order.order_id, order.order_rid)
            os.makedirs(order_storage_path, exist_ok=True)
            shutil.copy2(
                forecast_packaging_file_path,
                os.path.join(order_storage_path, FORECAST_PACKAGING_FILE_NAME),
            )

            order_status = OrderStatus(
                order_id=order.order_id,
                order_current_status=6,
                order_status_value=0,
            )
            db.session.add(order_status)

            order_shoe = OrderShoe(
                order_id=order.order_id,
                shoe_id=meta.get("shoeId"),
                adjust_staff="",
                process_sheet_upload_status="0",
                production_order_upload_status="0",
                customer_product_name=str(meta.get("customerShoeName") or "").strip(),
                business_technical_remark="",
                business_material_remark="",
            )
            db.session.add(order_shoe)
            db.session.flush()

            if meta.get("shoeRid"):
                os.makedirs(os.path.join(order_storage_path, str(meta.get("shoeRid"))), exist_ok=True)

            order_shoe_status = OrderShoeStatus(
                order_shoe_id=order_shoe.order_shoe_id,
                current_status=0,
                current_status_value=0,
            )
            db.session.add(order_shoe_status)

            order_shoe_production_info = OrderShoeProductionInfo(
                is_cutting_outsourced=0,
                is_sewing_outsourced=0,
                is_molding_outsourced=0,
                is_material_arrived=0,
                order_shoe_id=order_shoe.order_shoe_id,
            )
            db.session.add(order_shoe_production_info)

            grouped_by_shoe_type = {}
            for item in group_items:
                grouped_by_shoe_type.setdefault(item.shoe_type_id, []).append(item)

            for shoe_type_id, shoe_type_items in grouped_by_shoe_type.items():
                shoe_type = db.session.query(ShoeType).filter(ShoeType.shoe_type_id == shoe_type_id).first()
                if not shoe_type:
                    raise ValueError(f"鞋型不存在，shoeTypeId={shoe_type_id}")

                first_item = shoe_type_items[0]
                first_unit_price = float(first_item.unit_price or 0)
                if first_unit_price < 0:
                    first_unit_price = 0
                order_shoe_type = OrderShoeType(
                    order_shoe_id=order_shoe.order_shoe_id,
                    shoe_type_id=shoe_type.shoe_type_id,
                    customer_color_name=first_item.customer_color_name or first_item.color_name or "",
                    unit_price=first_unit_price,
                    currency_type=(sheet.currency_type or "RMB"),
                )
                db.session.add(order_shoe_type)
                db.session.flush()

                for item in shoe_type_items:
                    packaging = db.session.query(PackagingInfo).filter(
                        PackagingInfo.packaging_info_id == item.packaging_info_id
                    ).first()
                    if not packaging:
                        raise ValueError(f"配码不存在，item={item.forecast_sheet_item_id}")

                    ratio_total = float(packaging.total_quantity_ratio or 0)
                    quantity_per_ratio = (float(item.total_pairs) / ratio_total) if ratio_total > 0 else 0

                    batch = OrderShoeBatchInfo(
                        order_shoe_type_id=order_shoe_type.order_shoe_type_id,
                        name=packaging.packaging_info_name,
                        size_34_amount=int((packaging.size_34_ratio or 0) * quantity_per_ratio),
                        size_35_amount=int((packaging.size_35_ratio or 0) * quantity_per_ratio),
                        size_36_amount=int((packaging.size_36_ratio or 0) * quantity_per_ratio),
                        size_37_amount=int((packaging.size_37_ratio or 0) * quantity_per_ratio),
                        size_38_amount=int((packaging.size_38_ratio or 0) * quantity_per_ratio),
                        size_39_amount=int((packaging.size_39_ratio or 0) * quantity_per_ratio),
                        size_40_amount=int((packaging.size_40_ratio or 0) * quantity_per_ratio),
                        size_41_amount=int((packaging.size_41_ratio or 0) * quantity_per_ratio),
                        size_42_amount=int((packaging.size_42_ratio or 0) * quantity_per_ratio),
                        size_43_amount=int((packaging.size_43_ratio or 0) * quantity_per_ratio),
                        size_44_amount=int((packaging.size_44_ratio or 0) * quantity_per_ratio),
                        size_45_amount=int((packaging.size_45_ratio or 0) * quantity_per_ratio),
                        size_46_amount=int((packaging.size_46_ratio or 0) * quantity_per_ratio),
                        total_price=0,
                        total_amount=int(item.total_pairs),
                        packaging_info_id=packaging.packaging_info_id,
                        packaging_info_quantity=quantity_per_ratio,
                    )
                    db.session.add(batch)

            created_order_ids.append(order.order_id)
            created_order_rids.append(order.order_rid)

            # Mark dispatched items
            for item in group_items:
                item.dispatch_status = 1

        # Determine if all items are dispatched or only partial
        existing_order_ids = [int(x) for x in str(sheet.created_order_ids or "").split(",") if x.strip().isdigit()]
        all_order_ids = existing_order_ids + created_order_ids
        sheet.created_order_ids = ",".join([str(order_id) for order_id in all_order_ids])

        all_dispatched = all(int(item.dispatch_status or 0) == 1 for item in items)
        if all_dispatched:
            sheet.status = FORECAST_STATUS_DISPATCHED
        else:
            sheet.status = FORECAST_STATUS_PARTIAL
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        return jsonify({"error": str(ex)}), 500

    return jsonify({"message": "ok", "createdOrderIds": created_order_ids, "createdOrderRids": created_order_rids}), 200


@forecast_sheet_bp.route("/forecastsheet/submitpackaging", methods=["POST"])
def submit_forecast_packaging():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    sheet_id = request.form.get("forecastSheetId", type=int)
    if not sheet_id:
        return jsonify({"error": "forecastSheetId is required"}), 400

    sheet = db.session.query(ForecastSheet).filter(ForecastSheet.forecast_sheet_id == sheet_id).first()
    if not sheet:
        return jsonify({"error": "forecast sheet not found"}), 404
    if sheet.status == FORECAST_STATUS_DISPATCHED:
        return jsonify({"error": "已下发预报单不允许上传包装资料"}), 400

    _ensure_forecast_storage_dir(sheet.forecast_rid)
    target_file_path = _resolve_forecast_packaging_file_path(sheet.forecast_rid)
    uploaded_file.save(target_file_path)
    return jsonify({"message": "ok"}), 200


@forecast_sheet_bp.route("/forecastsheet/updatepackaging", methods=["POST"])
def update_forecast_sheet_packaging():
    payload = request.json or {}
    sheet_id = payload.get("forecastSheetId")
    items = payload.get("items") or []
    if not sheet_id:
        return jsonify({"error": "forecastSheetId is required"}), 400
    if not items:
        return jsonify({"error": "items is required"}), 400

    sheet = db.session.query(ForecastSheet).filter(ForecastSheet.forecast_sheet_id == sheet_id).first()
    if not sheet:
        return jsonify({"error": "forecast sheet not found"}), 404
    if sheet.status == FORECAST_STATUS_DISPATCHED:
        return jsonify({"error": "已下发预报单不允许编辑配码"}), 400

    try:
        existing_items = (
            db.session.query(ForecastSheetItem)
            .filter(ForecastSheetItem.forecast_sheet_id == sheet_id)
            .all()
        )
        item_map = {entity.forecast_sheet_item_id: entity for entity in existing_items}
        rebuilt_rows = []

        for idx, item in enumerate(items, start=1):
            item_id = item.get("forecastSheetItemId")
            candidate_ids = item.get("forecastSheetItemIds") or []
            normalized_candidate_ids = []
            if item_id:
                normalized_candidate_ids.append(int(item_id))
            normalized_candidate_ids.extend(
                [int(candidate_id) for candidate_id in candidate_ids if candidate_id]
            )
            normalized_candidate_ids = list(dict.fromkeys(normalized_candidate_ids))

            if not normalized_candidate_ids:
                raise ValueError(f"第{idx}行参数缺失")

            base_entity = None
            for candidate_id in normalized_candidate_ids:
                base_entity = item_map.get(candidate_id)
                if base_entity:
                    break
            if not base_entity:
                raise ValueError(f"第{idx}行鞋型不存在")

            unit_price = item.get("unitPrice")
            if unit_price is None:
                unit_price_value = float(base_entity.unit_price or 0)
            else:
                unit_price_value = float(unit_price)
            if unit_price_value < 0:
                raise ValueError(f"第{idx}行单价不能小于0")

            packaging_info_ids = item.get("packagingInfoIds") or []
            if not packaging_info_ids:
                single_id = item.get("packagingInfoId")
                if single_id:
                    packaging_info_ids = [single_id]
            packaging_info_ids = [
                int(packaging_info_id)
                for packaging_info_id in packaging_info_ids
                if packaging_info_id and int(packaging_info_id) > 0
            ]
            if not packaging_info_ids:
                fallback_total_pairs_raw = float(item.get("totalPairs") or base_entity.total_pairs or 1)
                fallback_total_pairs = int(round(fallback_total_pairs_raw))
                if fallback_total_pairs <= 0:
                    fallback_total_pairs = 1
                rebuilt_rows.append(
                    ForecastSheetItem(
                        forecast_sheet_id=sheet.forecast_sheet_id,
                        shoe_type_id=base_entity.shoe_type_id,
                        shoe_rid=base_entity.shoe_rid,
                        color_name=base_entity.color_name,
                        customer_shoe_name=base_entity.customer_shoe_name,
                        customer_color_name=base_entity.customer_color_name,
                        packaging_info_id=0,
                        packaging_info_name="",
                        unit_price=unit_price_value,
                        total_pairs=fallback_total_pairs,
                        sort_index=base_entity.sort_index,
                        dispatch_status=int(base_entity.dispatch_status or 0),
                    )
                )
                continue

            has_valid_packaging = False
            for packaging_info_id in packaging_info_ids:
                quantity_map = item.get("packagingInfoQuantityMap") or {}
                quantity_value = quantity_map.get(str(packaging_info_id))
                if quantity_value is None:
                    quantity_value = quantity_map.get(packaging_info_id)
                if quantity_value is None:
                    quantity_value = 1
                quantity_value = float(quantity_value)
                if quantity_value <= 0:
                    continue

                packaging = (
                    db.session.query(PackagingInfo)
                    .filter(PackagingInfo.packaging_info_id == packaging_info_id)
                    .first()
                )
                if not packaging:
                    continue

                ratio_total = float(packaging.total_quantity_ratio or 0)
                if ratio_total > 0 and quantity_value > 0:
                    total_pairs = int(round(ratio_total * quantity_value))
                    if total_pairs <= 0:
                        total_pairs = 1
                else:
                    total_pairs = 0
                if total_pairs <= 0:
                    continue

                rebuilt_rows.append(
                    ForecastSheetItem(
                        forecast_sheet_id=sheet.forecast_sheet_id,
                        shoe_type_id=base_entity.shoe_type_id,
                        shoe_rid=base_entity.shoe_rid,
                        color_name=base_entity.color_name,
                        customer_shoe_name=base_entity.customer_shoe_name,
                        customer_color_name=base_entity.customer_color_name,
                        packaging_info_id=packaging.packaging_info_id,
                        packaging_info_name=packaging.packaging_info_name,
                        unit_price=unit_price_value,
                        total_pairs=total_pairs,
                        sort_index=base_entity.sort_index,
                        dispatch_status=int(base_entity.dispatch_status or 0),
                    )
                )
                has_valid_packaging = True

            if not has_valid_packaging:
                fallback_total_pairs_raw = float(item.get("totalPairs") or base_entity.total_pairs or 1)
                fallback_total_pairs = int(round(fallback_total_pairs_raw))
                if fallback_total_pairs <= 0:
                    fallback_total_pairs = 1
                rebuilt_rows.append(
                    ForecastSheetItem(
                        forecast_sheet_id=sheet.forecast_sheet_id,
                        shoe_type_id=base_entity.shoe_type_id,
                        shoe_rid=base_entity.shoe_rid,
                        color_name=base_entity.color_name,
                        customer_shoe_name=base_entity.customer_shoe_name,
                        customer_color_name=base_entity.customer_color_name,
                        packaging_info_id=0,
                        packaging_info_name="",
                        unit_price=unit_price_value,
                        total_pairs=fallback_total_pairs,
                        sort_index=base_entity.sort_index,
                        dispatch_status=int(base_entity.dispatch_status or 0),
                    )
                )

        db.session.query(ForecastSheetItem).filter(ForecastSheetItem.forecast_sheet_id == sheet_id).delete()
        for row in rebuilt_rows:
            db.session.add(row)

        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        return jsonify({"error": str(ex)}), 400

    return jsonify({"message": "ok"}), 200

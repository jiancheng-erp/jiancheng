from flask import Blueprint, jsonify, request, send_file
from sqlalchemy.dialects.mysql import insert
import pandas as pd
import datetime
import time
from werkzeug.utils import secure_filename
import os
import json
import shutil
from models import *
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH
from api_utility import format_date
from decimal import Decimal
from sqlalchemy import func, or_
from login.login import current_user_info

from app_config import db

from flask import current_app
from event_processor import EventProcessor
from wechat_api.send_message_api import send_configurable_message
from logger import logger
from api_utility import to_camel, to_snake

order_create_bp = Blueprint("order_create_bp", __name__)

NEW_ORDER_STATUS = 6
NEW_ORDER_STEP_OP = 12
NEW_ORDER_NEXT_STEP_OP = 13
NEW_ORDER_SHOE_OP = 2

department_name = "业务部"
# Allowed file extensions
ALLOWED_EXTENSIONS = {"xls", "xlsx"}
BUSINESS_MANAGER_ROLE = 4
BUSINESS_CLERK_ROLE = 21
ORDER_TYPE_NORMAL = "N"
ORDER_TYPE_FORECAST = "F"


def normalize_order_type(value):
    if not value:
        return ORDER_TYPE_NORMAL
    normalized = str(value).strip().upper()
    if normalized in {"F", "FORECAST", "PRE", "预报", "预报单"}:
        return ORDER_TYPE_FORECAST
    return ORDER_TYPE_NORMAL


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def resolve_order_storage_dir_name(order_id, order_rid):
    rid = (order_rid or "").strip()
    if rid:
        return rid
    return f"_NO_RID_{order_id}"


def _truncate_with_suffix(base_value: str, suffix: str, max_len: int = 40) -> str:
    value = (base_value or "").strip()
    if len(value) + len(suffix) <= max_len:
        return f"{value}{suffix}"
    trimmed = value[: max_len - len(suffix)]
    return f"{trimmed}{suffix}"


def _build_unique_split_order_rid(source_order_rid: str, split_index: int) -> str:
    base_value = (source_order_rid or "").strip() or "FORECAST"
    serial = 0
    while True:
        suffix = f"-S{split_index}" if serial == 0 else f"-S{split_index}-{serial}"
        candidate = _truncate_with_suffix(base_value, suffix, 40)
        existing = db.session.query(Order.order_id).filter(Order.order_rid == candidate).first()
        if not existing:
            return candidate
        serial += 1


def _build_unique_split_order_cid(source_order_cid: str, split_index: int):
    base_value = (source_order_cid or "").strip()
    if not base_value:
        return None
    serial = 0
    while True:
        suffix = f"-S{split_index}" if serial == 0 else f"-S{split_index}-{serial}"
        candidate = _truncate_with_suffix(base_value, suffix, 40)
        existing = db.session.query(Order.order_id).filter(Order.order_cid == candidate).first()
        if not existing:
            return candidate
        serial += 1


def _normalize_ratio_value(value):
    if value is None:
        return 0
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _build_order_template_payload_from_order(order_id: int):
    order_bundle = (
        db.session.query(Order, Customer, BatchInfoType)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(BatchInfoType, Order.batch_info_type_id == BatchInfoType.batch_info_type_id)
        .filter(Order.order_id == order_id)
        .first()
    )
    if not order_bundle:
        return None

    order_entity, customer_entity, batch_info_type = order_bundle
    meta = {
        "orderRid": order_entity.order_rid,
        "orderCid": order_entity.order_cid,
        "orderType": normalize_order_type(order_entity.order_type),
        "customerId": customer_entity.customer_id,
        "customerName": customer_entity.customer_name,
        "customerBrand": customer_entity.customer_brand,
        "batchInfoTypeId": batch_info_type.batch_info_type_id,
        "batchInfoTypeName": batch_info_type.batch_info_type_name,
        "sourceOrderRid": order_entity.order_rid,
        "sourceOrderId": order_entity.order_id,
    }

    shoes = []
    order_shoe_entities = (
        db.session.query(OrderShoe, Shoe)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(OrderShoe.order_id == order_entity.order_id)
        .order_by(OrderShoe.order_shoe_id.asc())
        .all()
    )
    shoe_id_to_colors = {}

    for order_shoe_entity, shoe_entity in order_shoe_entities:
        if shoe_entity.shoe_id not in shoe_id_to_colors:
            color_rows = (
                db.session.query(ShoeType, Color)
                .join(Color, ShoeType.color_id == Color.color_id)
                .filter(ShoeType.shoe_id == shoe_entity.shoe_id)
                .all()
            )
            shoe_id_to_colors[shoe_entity.shoe_id] = [
                {"label": color.color_name, "value": color.color_id}
                for _, color in color_rows
            ]

        order_shoe_type_entities = (
            db.session.query(OrderShoeType, ShoeType, Color)
            .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
            .join(Color, ShoeType.color_id == Color.color_id)
            .filter(OrderShoeType.order_shoe_id == order_shoe_entity.order_shoe_id)
            .order_by(OrderShoeType.order_shoe_type_id.asc())
            .all()
        )

        for order_shoe_type_entity, shoe_type_entity, color_entity in order_shoe_type_entities:
            batch_entities = (
                db.session.query(OrderShoeBatchInfo, PackagingInfo)
                .join(
                    PackagingInfo,
                    OrderShoeBatchInfo.packaging_info_id == PackagingInfo.packaging_info_id,
                )
                .filter(
                    OrderShoeBatchInfo.order_shoe_type_id
                    == order_shoe_type_entity.order_shoe_type_id
                )
                .order_by(OrderShoeBatchInfo.order_shoe_batch_info_id.asc())
                .all()
            )

            order_shoe_type_batch_info = []
            quantity_mapping = {}
            for batch_entity, packaging_info_entity in batch_entities:
                total_ratio = _normalize_ratio_value(packaging_info_entity.total_quantity_ratio)
                quantity_per_ratio = batch_entity.packaging_info_quantity
                if quantity_per_ratio is None and total_ratio:
                    quantity_per_ratio = Decimal(batch_entity.total_amount) / Decimal(total_ratio)

                normalized_quantity = _normalize_ratio_value(quantity_per_ratio)
                packaging_info_id = packaging_info_entity.packaging_info_id
                quantity_mapping[str(packaging_info_id)] = normalized_quantity
                order_shoe_type_batch_info.append(
                    {
                        "packagingInfoId": packaging_info_id,
                        "packagingInfoName": packaging_info_entity.packaging_info_name,
                        "packagingInfoLocale": packaging_info_entity.packaging_info_locale,
                        "size34Ratio": _normalize_ratio_value(packaging_info_entity.size_34_ratio),
                        "size35Ratio": _normalize_ratio_value(packaging_info_entity.size_35_ratio),
                        "size36Ratio": _normalize_ratio_value(packaging_info_entity.size_36_ratio),
                        "size37Ratio": _normalize_ratio_value(packaging_info_entity.size_37_ratio),
                        "size38Ratio": _normalize_ratio_value(packaging_info_entity.size_38_ratio),
                        "size39Ratio": _normalize_ratio_value(packaging_info_entity.size_39_ratio),
                        "size40Ratio": _normalize_ratio_value(packaging_info_entity.size_40_ratio),
                        "size41Ratio": _normalize_ratio_value(packaging_info_entity.size_41_ratio),
                        "size42Ratio": _normalize_ratio_value(packaging_info_entity.size_42_ratio),
                        "size43Ratio": _normalize_ratio_value(packaging_info_entity.size_43_ratio),
                        "size44Ratio": _normalize_ratio_value(packaging_info_entity.size_44_ratio),
                        "size45Ratio": _normalize_ratio_value(packaging_info_entity.size_45_ratio),
                        "size46Ratio": _normalize_ratio_value(packaging_info_entity.size_46_ratio),
                        "totalQuantityRatio": total_ratio,
                    }
                )

            shoes.append(
                {
                    "shoeRid": shoe_entity.shoe_rid,
                    "shoeId": shoe_entity.shoe_id,
                    "shoeTypeId": order_shoe_type_entity.shoe_type_id,
                    "shoeImageUrl": shoe_type_entity.shoe_image_url,
                    "orderShoeTypeBatchInfo": order_shoe_type_batch_info,
                    "quantityMapping": quantity_mapping,
                    "customerShoeName": order_shoe_entity.customer_product_name or "",
                    "customerColorName": order_shoe_type_entity.customer_color_name or color_entity.color_name or "",
                    "colorId": color_entity.color_id,
                    "colorName": color_entity.color_name,
                    "businessMaterialRemark": order_shoe_entity.business_material_remark or "",
                    "businessTechnicalRemark": order_shoe_entity.business_technical_remark or "",
                    "shoeTypeColors": shoe_id_to_colors.get(shoe_entity.shoe_id, []),
                }
            )

    return {
        "templateName": order_entity.order_rid or order_entity.order_cid or f"历史订单-{order_entity.order_id}",
        "templateDescription": "来自历史订单",
        "orderTemplate": {"orderData": meta, "orderShoeData": shoes},
        "sourceOrderId": order_entity.order_id,
    }


def _build_order_source_visibility_filter(current_user_role, staff_id):
    # if current_user_role == BUSINESS_MANAGER_ROLE:
        # filter manager order template ?
    if current_user_role == BUSINESS_CLERK_ROLE:
        return Order.salesman_id == staff_id
    return None


@order_create_bp.route("/ordercreate/createneworder", methods=["POST"])
def create_new_order():
    time_s = time.time()
    order_info = request.json.get("orderInfo")
    if not order_info:
        return jsonify({"error": "invalid request"}), 400
    order_rid = (order_info.get("orderRId") or "").strip()
    order_cid = order_info["orderCid"]
    batch_info_type_id = order_info["batchInfoTypeId"]
    customer_id = order_info["customerId"]
    order_start_date = order_info["orderStartDate"]
    order_end_date = order_info["orderEndDate"]
    # 订单对应下发业务经理, 应该为staff_id
    supervisor_id = order_info["supervisorId"]
    # new order status should be fixed
    order_status = NEW_ORDER_STATUS
    order_salesman_id = order_info["salesmanId"]
    order_shoe_type_list = order_info["orderShoeTypes"]
    customer_shoe_names = order_info["customerShoeName"]
    order_type = normalize_order_type(order_info.get("orderType"))
    rid_exist_order = Order.query.filter_by(order_rid=order_rid).first() if order_rid else None
    if rid_exist_order:
        logger.debug("order rid exists, must be unique")
        return jsonify({"message": "订单号或客户订单号已经存在 单号不可重复"}), 400

    new_order = Order(
        order_rid=order_rid,
        order_cid=order_cid,
        order_type=order_type,
        batch_info_type_id=batch_info_type_id,
        customer_id=customer_id,
        start_date=order_start_date,
        end_date=order_end_date,
        salesman_id=order_salesman_id,
        production_list_upload_status="0",
        amount_list_upload_status="0",
        supervisor_id=supervisor_id,
    )

    db.session.add(new_order)
    db.session.flush()
    ### os mkdir
    # os.mkdir(os.path.join(FILE_STORAGE_PATH, order_rid))

    new_order_id = new_order.order_id
    new_order_status = OrderStatus(
        order_id=new_order_id,
        order_current_status=order_status,
        order_status_value=0,
    )
    db.session.add(new_order_status)
    db.session.flush()

    shoe_type_id_to_shoe_type = {
        shoe_type["shoeTypeId"]: shoe_type for shoe_type in order_shoe_type_list
    }
    shoe_type_ids = shoe_type_id_to_shoe_type.keys()
    shoe_id_to_rid = {}
    shoe_type_id_to_shoe_id = {}
    for shoe_type_id in shoe_type_ids:
        db_shoe_entity = ShoeType.query.filter_by(shoe_type_id=shoe_type_id).first()
        shoe_type_id_to_shoe_id[shoe_type_id] = db_shoe_entity.shoe_id
        shoe_id_to_rid[db_shoe_entity.shoe_id] = shoe_type_id_to_shoe_type[
            shoe_type_id
        ]["shoeRid"]

    shoe_id_to_order_shoe_id = {}

    ### for every shoe
    for shoe_id in shoe_id_to_rid.keys():
        existing_order_shoe = OrderShoe.query.filter_by(
            order_id=new_order_id, shoe_id=shoe_id
        ).first()
        if not existing_order_shoe:
            customer_product_name = customer_shoe_names[shoe_id_to_rid[shoe_id]]
            # try to pick up remarks from incoming payload (order_shoe_type_list entries)
            material_remark = None
            technical_remark = None
            try:
                for ost in order_shoe_type_list:
                    # ost may be nested or flattened; match by shoeId
                    sid = ost.get('shoeId') if isinstance(ost, dict) else None
                    if sid is None:
                        sid = ost.get('shoe_id') if isinstance(ost, dict) else None
                    if sid is None:
                        continue
                    if int(sid) == int(shoe_id):
                        material_remark = ost.get('businessMaterialRemark') or ost.get('business_material_remark') or material_remark
                        technical_remark = ost.get('businessTechnicalRemark') or ost.get('business_technical_remark') or technical_remark
                        # prefer first match
                        break
            except Exception:
                pass
            new_order_shoe_entity = OrderShoe(
                order_id=new_order_id,
                shoe_id=shoe_id,
                customer_product_name=customer_product_name,
                production_order_upload_status="0",
                process_sheet_upload_status="0",
                adjust_staff="",
                business_material_remark=material_remark or "",
                business_technical_remark=technical_remark or "",
            )
            db.session.add(new_order_shoe_entity)
            db.session.flush()

            # os.mkdir(os.path.join(FILE_STORAGE_PATH, order_rid, shoe_id_to_rid[shoe_id]))

            new_order_shoe_status_entity = OrderShoeStatus(
                order_shoe_id=new_order_shoe_entity.order_shoe_id,
                current_status=0,
                current_status_value=0,
            )
            db.session.add(new_order_shoe_status_entity)
            db.session.flush()

            new_order_shoe_production_info_entity = OrderShoeProductionInfo(
                is_cutting_outsourced=0,
                is_sewing_outsourced=0,
                is_molding_outsourced=0,
                is_material_arrived=0,
                order_shoe_id=new_order_shoe_entity.order_shoe_id,
            )

            db.session.add(new_order_shoe_production_info_entity)
            db.session.flush()
            shoe_id_to_order_shoe_id[shoe_id] = new_order_shoe_entity.order_shoe_id

    ### for every shoe_type
    for shoe_type_id in shoe_type_ids:
        ## create ordershoetype
        shoe_type = shoe_type_id_to_shoe_type[shoe_type_id]
        shoe_id = shoe_type_id_to_shoe_id[shoe_type_id]
        order_shoe_id = shoe_id_to_order_shoe_id[shoe_id]
        quantity_mapping = shoe_type["quantityMapping"]
        batch_info = shoe_type["orderShoeTypeBatchInfo"]
        # 业务部改动 客户颜色
        customer_color_name = shoe_type["customerColorName"]
        existing_entity = OrderShoeType.query.filter_by(
            order_shoe_id=order_shoe_id, shoe_type_id=shoe_type_id
        ).first()
        if not existing_entity:
            new_entity = OrderShoeType(
                order_shoe_id=order_shoe_id,
                shoe_type_id=shoe_type_id,
                customer_color_name=customer_color_name,
            )
            db.session.add(new_entity)
            db.session.flush()
        else:
            new_entity = existing_entity
        batch_info_entity_array = []
        for batch in batch_info:
            quantity_per_ratio = float(quantity_mapping[str(batch["packagingInfoId"])])
            new_entity = OrderShoeBatchInfo(
                order_shoe_type_id=new_entity.order_shoe_type_id,
                name=batch["packagingInfoName"],
                size_34_amount=int(batch["size34Ratio"] * quantity_per_ratio),
                size_35_amount=int(batch["size35Ratio"] * quantity_per_ratio),
                size_36_amount=int(batch["size36Ratio"] * quantity_per_ratio),
                size_37_amount=int(batch["size37Ratio"] * quantity_per_ratio),
                size_38_amount=int(batch["size38Ratio"] * quantity_per_ratio),
                size_39_amount=int(batch["size39Ratio"] * quantity_per_ratio),
                size_40_amount=int(batch["size40Ratio"] * quantity_per_ratio),
                size_41_amount=int(batch["size41Ratio"] * quantity_per_ratio),
                size_42_amount=int(batch["size42Ratio"] * quantity_per_ratio),
                size_43_amount=int(batch["size43Ratio"] * quantity_per_ratio),
                size_44_amount=int(batch["size44Ratio"] * quantity_per_ratio),
                size_45_amount=int(batch["size45Ratio"] * quantity_per_ratio),
                size_46_amount=int(batch["size46Ratio"] * quantity_per_ratio),
                total_price=0,
                total_amount=int(batch["totalQuantityRatio"] * quantity_per_ratio),
                packaging_info_id=batch["packagingInfoId"],
                packaging_info_quantity=quantity_per_ratio,
            )
            batch_info_entity_array.append(new_entity)
        db.session.add_all(batch_info_entity_array)
    logger.debug("order added to DB")
    db.session.commit()
    order_storage_dir_name = resolve_order_storage_dir_name(new_order_id, order_rid)
    order_storage_path = os.path.join(FILE_STORAGE_PATH, order_storage_dir_name)
    os.makedirs(order_storage_path, exist_ok=True)
    for shoe_rid in set(shoe_id_to_rid.values()):
        os.makedirs(os.path.join(order_storage_path, shoe_rid), exist_ok=True)

    # If the request indicates this order is created from a template/source order,
    # copy packaging/related files from the source order directory into the new order folder.
    try:
        source_rid = None
        # frontend may provide either sourceOrderRid or sourceOrderId
        if isinstance(order_info, dict):
            source_rid = order_info.get("sourceOrderRid") or None
            source_id = order_info.get("sourceOrderId") or None
            if not source_rid and source_id:
                src_ent = db.session.query(Order).filter(Order.order_id == source_id).first()
                if src_ent:
                    source_rid = src_ent.order_rid
            source_order_entity = None
            if source_id:
                source_order_entity = db.session.query(Order).filter(Order.order_id == source_id).first()
            if not source_order_entity and source_rid is not None:
                source_order_entity = db.session.query(Order).filter(Order.order_rid == source_rid).first()
        if source_rid or source_order_entity:
            src_dir_name = resolve_order_storage_dir_name(
                source_order_entity.order_id if source_order_entity else "unknown",
                source_order_entity.order_rid if source_order_entity else source_rid,
            )
            src_path = os.path.join(FILE_STORAGE_PATH, str(src_dir_name))
            dst_path = order_storage_path
            if os.path.exists(src_path):
                # copy contents from src_path into dst_path, merge existing
                for name in os.listdir(src_path):
                    s = os.path.join(src_path, name)
                    d = os.path.join(dst_path, name)
                    try:
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                    except Exception:
                        # best effort copy; don't fail order creation on copy errors
                        logger.exception("copying template files failed for %s -> %s", s, d)
                # mark packaging files as uploaded for the new order
                try:
                    # 'new_order' is the Order instance created earlier
                    new_order.production_list_upload_status = "2"
                    db.session.flush()
                    db.session.commit()
                except Exception:
                    logger.exception("failed to set packaging_status on new order %s", new_order_id)
    except Exception:
        logger.exception("error while attempting to copy files from source template order")

    result = (
        jsonify({"message": "Order imported successfully", "newOrderId": new_order_id}),
        200,
    )
    # except Exception as e:
    # 	result = jsonify({"message": str(e)}, 500)
    time_t = time.time()
    logger.debug("time taken is " + str(time_t - time_s))
    return result


@order_create_bp.route("/ordercreate/updateprice", methods=["POST"])
def order_price_update():
    time_s = time.time()
    unit_price_form = request.json.get("unitPriceForm")
    currency_type_form = request.json.get("currencyTypeForm")
    staff_id = request.json.get("staffId")

    staff_entity = db.session.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not staff_entity:
        return jsonify({"error": "operator not found"}), 404
    if staff_entity.character_id != BUSINESS_MANAGER_ROLE:
        return jsonify({"error": "no permission to update price"}), 403

    for order_shoe_type_id in unit_price_form.keys():
        unit_price = float(unit_price_form[order_shoe_type_id])
        currency_type = str(currency_type_form[order_shoe_type_id])
        entity = (
            db.session.query(OrderShoeType)
            .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
            .first()
        )
        entity.unit_price = unit_price
        entity.currency_type = currency_type
    db.session.commit()
    # find all orderShoeTypes belong to this order
    # db.session.query(OrderShoeType)
    # .filter(OrderShoeType.order_shoe_type_id == )
    # sync_order_shoe_status(list(set(unit_price_form.keys()).union(set(currency_type_form.keys()))))
    time_t = time.time()
    logger.debug("time taken is update price is" + str(time_t - time_s))
    return jsonify({"msg": "ok"}), 200


@order_create_bp.route("/ordercreate/proceedevent", methods=["POST"])
def order_event_proceed():
    logger.debug("PROCEED")
    order_id = request.json.get("orderId")
    staff_id = request.json.get("staffId")
    logger.debug(order_id, staff_id)
    order_entity = db.session.query(Order).filter_by(order_id=order_id).first()
    print(order_entity)
    if (
        order_entity != None
        and int(order_entity.production_list_upload_status) == 2
    ):
        cur_time = format_date(datetime.datetime.now())
        new_event = Event(
            staff_id=staff_id,
            handle_time=cur_time,
            operation_id=NEW_ORDER_STEP_OP,
            event_order_id=order_id,
        )
        processor: EventProcessor = current_app.config["event_processor"]
        processor.processEvent(new_event)
        db.session.add(new_event)
        db.session.commit()
        return jsonify({"msg": "OK"}), 200

    else:
        return jsonify({"error": "order_shoe_type_id not found"}), 201


@order_create_bp.route("/ordercreate/sendprevious", methods=["POST"])
def order_send_previous():
    order_id = request.json.get("orderId")
    staff_id = request.json.get("staffId")
    staff_entity = db.session.query(Staff).filter_by(staff_id=staff_id).first()
    if staff_entity:
        staff_name = staff_entity.staff_name
    else:
        return jsonify({"msg": "operator not found"}), 404
    entity = (
        db.session.query(Order, OrderStatus)
        .filter_by(order_id=order_id)
        .join(OrderStatus, Order.order_id == OrderStatus.order_id)
        .first()
    )
    if entity:
        _, status_entity = entity
        if status_entity.order_current_status == 6:
            status_entity.order_status_value = 0
            cur_time = format_date(datetime.datetime.now())
            revert_event = RevertEvent(
                revert_reason="业务部退回",
                responsible_department=department_name,
                initialing_department=department_name + staff_name,
                event_time=cur_time,
                order_id=order_id,
            )
            db.session.add(revert_event)
            db.session.commit()
            return jsonify({"msg": "revert order"}), 200
        else:
            return jsonify({"error": "wrong status value for order"}), 400
    else:
        return jsonify({"error": "order not found"}), 404


@order_create_bp.route("/ordercreate/sendnext", methods=["POST"])
def order_next_step():
    order_id = request.json.get("orderId")
    staff_id = request.json.get("staffId")
    entity = db.session.query(Order).filter(Order.order_id == order_id).first()
    if not entity:
        return jsonify({"error": "order not found"}), 404
    order_rid = entity.order_rid
    order_shoe_rid = (
        db.session.query(OrderShoe, Shoe)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(OrderShoe.order_id == order_id)
        .first()
    ).Shoe.shoe_rid
    # Validate price info before allowing next step
    order_shoe_type_entities = (
        db.session.query(OrderShoeType)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoe.order_id == order_id)
        .all()
    )
    price_missing = []
    for entity_ost in order_shoe_type_entities:
        unit_price = entity_ost.unit_price or 0
        currency_type = entity_ost.currency_type
        if float(unit_price) <= 0 or not currency_type:
            price_missing.append(entity_ost.order_shoe_type_id)
    if price_missing:
        return (
            jsonify({"error": "订单存在未填写的鞋型价格，无法下发"}),
            400,
        )
    if entity:
        cur_time = format_date(datetime.datetime.now())
        new_event = Event(
            staff_id=staff_id,
            handle_time=cur_time,
            operation_id=NEW_ORDER_NEXT_STEP_OP,
            event_order_id=order_id,
        )
        processor: EventProcessor = current_app.config["event_processor"]
        processor.processEvent(new_event)
        db.session.add(new_event)
        db.session.commit()
    message = "订单已发出至总经理审核，订单号：{order_rid}，鞋型号：{order_shoe_rid}"
    send_configurable_message(
        "order_submit_to_gm",
        message,
        "070d09bbc28c2cec22535b7ec5d1316b",
        context={"order_rid": order_rid, "order_shoe_rid": order_shoe_rid},
    )
    db.session.commit()
    return "Event Processed In Order Create API CALL", 200


@order_create_bp.route("/ordercreate/sendnextsplitforecast", methods=["POST"])
def order_next_step_split_forecast():
    order_id = request.json.get("orderId")
    staff_id = request.json.get("staffId")
    if not order_id or not staff_id:
        return jsonify({"error": "orderId and staffId are required"}), 400

    order_entity = db.session.query(Order).filter(Order.order_id == order_id).first()
    if not order_entity:
        return jsonify({"error": "order not found"}), 404
    if normalize_order_type(order_entity.order_type) != ORDER_TYPE_FORECAST:
        return jsonify({"error": "only forecast order supports split dispatch"}), 400

    order_status = db.session.query(OrderStatus).filter(OrderStatus.order_id == order_id).first()
    if not order_status:
        return jsonify({"error": "order status not found"}), 404
    if order_status.order_current_status != 6 or order_status.order_status_value != 1:
        return jsonify({"error": "forecast order is not in dispatchable status"}), 400
    if str(order_entity.production_list_upload_status or "") != "2":
        return jsonify({"error": "包装材料待上传，无法下发拆分"}), 400

    order_shoe_entities = (
        db.session.query(OrderShoe)
        .filter(OrderShoe.order_id == order_id)
        .order_by(OrderShoe.order_shoe_id.asc())
        .all()
    )
    if not order_shoe_entities:
        return jsonify({"error": "forecast order has no shoe items"}), 400

    order_shoe_type_entities = (
        db.session.query(OrderShoeType)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoe.order_id == order_id)
        .all()
    )
    missing_price = []
    for entity_ost in order_shoe_type_entities:
        unit_price = entity_ost.unit_price or 0
        currency_type = entity_ost.currency_type
        if float(unit_price) <= 0 or not currency_type:
            missing_price.append(entity_ost.order_shoe_type_id)
    if missing_price:
        return jsonify({"error": "预报单存在未填写的鞋型价格，无法下发拆分"}), 400

    parent_storage_dir_name = resolve_order_storage_dir_name(
        order_entity.order_id, order_entity.order_rid
    )
    parent_storage_path = os.path.join(FILE_STORAGE_PATH, parent_storage_dir_name)

    created_order_ids = []
    created_order_rids = []

    try:
        for split_index, source_order_shoe in enumerate(order_shoe_entities, start=1):
            new_order_rid = _build_unique_split_order_rid(order_entity.order_rid, split_index)
            new_order_cid = _build_unique_split_order_cid(order_entity.order_cid, split_index)

            new_order = Order(
                order_rid=new_order_rid,
                order_cid=new_order_cid,
                order_type=ORDER_TYPE_NORMAL,
                batch_info_type_id=order_entity.batch_info_type_id,
                customer_id=order_entity.customer_id,
                start_date=order_entity.start_date,
                end_date=order_entity.end_date,
                salesman_id=order_entity.salesman_id,
                production_list_upload_status=order_entity.production_list_upload_status,
                amount_list_upload_status=order_entity.amount_list_upload_status,
                supervisor_id=order_entity.supervisor_id,
            )
            db.session.add(new_order)
            db.session.flush()

            new_order_status = OrderStatus(
                order_id=new_order.order_id,
                order_current_status=7,
                order_status_value=0,
            )
            db.session.add(new_order_status)

            source_prod_info = (
                db.session.query(OrderShoeProductionInfo)
                .filter(OrderShoeProductionInfo.order_shoe_id == source_order_shoe.order_shoe_id)
                .first()
            )

            new_order_shoe = OrderShoe(
                order_id=new_order.order_id,
                shoe_id=source_order_shoe.shoe_id,
                customer_product_name=source_order_shoe.customer_product_name,
                production_order_upload_status=source_order_shoe.production_order_upload_status,
                process_sheet_upload_status=source_order_shoe.process_sheet_upload_status,
                adjust_staff=source_order_shoe.adjust_staff,
                business_material_remark=source_order_shoe.business_material_remark,
                business_technical_remark=source_order_shoe.business_technical_remark,
            )
            db.session.add(new_order_shoe)
            db.session.flush()

            new_order_shoe_status = OrderShoeStatus(
                order_shoe_id=new_order_shoe.order_shoe_id,
                current_status=0,
                current_status_value=0,
            )
            db.session.add(new_order_shoe_status)

            if source_prod_info:
                new_order_shoe_production_info = OrderShoeProductionInfo(
                    cutting_line_group=source_prod_info.cutting_line_group,
                    pre_sewing_line_group=source_prod_info.pre_sewing_line_group,
                    sewing_line_group=source_prod_info.sewing_line_group,
                    molding_line_group=source_prod_info.molding_line_group,
                    is_cutting_outsourced=source_prod_info.is_cutting_outsourced,
                    is_sewing_outsourced=source_prod_info.is_sewing_outsourced,
                    is_molding_outsourced=source_prod_info.is_molding_outsourced,
                    cutting_start_date=source_prod_info.cutting_start_date,
                    cutting_end_date=source_prod_info.cutting_end_date,
                    sewing_start_date=source_prod_info.sewing_start_date,
                    sewing_end_date=source_prod_info.sewing_end_date,
                    molding_start_date=source_prod_info.molding_start_date,
                    molding_end_date=source_prod_info.molding_end_date,
                    pre_sewing_start_date=source_prod_info.pre_sewing_start_date,
                    pre_sewing_end_date=source_prod_info.pre_sewing_end_date,
                    is_material_arrived=source_prod_info.is_material_arrived,
                    scheduling_status=source_prod_info.scheduling_status,
                    order_shoe_id=new_order_shoe.order_shoe_id,
                )
            else:
                new_order_shoe_production_info = OrderShoeProductionInfo(
                    is_cutting_outsourced=0,
                    is_sewing_outsourced=0,
                    is_molding_outsourced=0,
                    is_material_arrived=0,
                    order_shoe_id=new_order_shoe.order_shoe_id,
                )
            db.session.add(new_order_shoe_production_info)

            source_order_shoe_types = (
                db.session.query(OrderShoeType)
                .filter(OrderShoeType.order_shoe_id == source_order_shoe.order_shoe_id)
                .all()
            )
            source_to_new_ost_mapping = {}
            for source_ost in source_order_shoe_types:
                new_ost = OrderShoeType(
                    order_shoe_id=new_order_shoe.order_shoe_id,
                    shoe_type_id=source_ost.shoe_type_id,
                    customer_color_name=source_ost.customer_color_name,
                    unit_price=source_ost.unit_price,
                    currency_type=source_ost.currency_type,
                )
                db.session.add(new_ost)
                db.session.flush()
                source_to_new_ost_mapping[source_ost.order_shoe_type_id] = new_ost.order_shoe_type_id

            source_batches = (
                db.session.query(OrderShoeBatchInfo)
                .filter(
                    OrderShoeBatchInfo.order_shoe_type_id.in_(
                        list(source_to_new_ost_mapping.keys())
                    )
                )
                .all()
            )
            for source_batch in source_batches:
                new_batch = OrderShoeBatchInfo(
                    name=source_batch.name,
                    total_amount=source_batch.total_amount,
                    size_34_amount=source_batch.size_34_amount,
                    size_35_amount=source_batch.size_35_amount,
                    size_36_amount=source_batch.size_36_amount,
                    size_37_amount=source_batch.size_37_amount,
                    size_38_amount=source_batch.size_38_amount,
                    size_39_amount=source_batch.size_39_amount,
                    size_40_amount=source_batch.size_40_amount,
                    size_41_amount=source_batch.size_41_amount,
                    size_42_amount=source_batch.size_42_amount,
                    size_43_amount=source_batch.size_43_amount,
                    size_44_amount=source_batch.size_44_amount,
                    size_45_amount=source_batch.size_45_amount,
                    size_46_amount=source_batch.size_46_amount,
                    packaging_info_id=source_batch.packaging_info_id,
                    packaging_info_quantity=source_batch.packaging_info_quantity,
                    order_shoe_type_id=source_to_new_ost_mapping[
                        source_batch.order_shoe_type_id
                    ],
                    total_price=source_batch.total_price,
                )
                db.session.add(new_batch)

            new_order_storage_dir_name = resolve_order_storage_dir_name(
                new_order.order_id, new_order.order_rid
            )
            new_order_storage_path = os.path.join(FILE_STORAGE_PATH, new_order_storage_dir_name)
            os.makedirs(new_order_storage_path, exist_ok=True)

            if os.path.exists(parent_storage_path):
                for name in os.listdir(parent_storage_path):
                    source_path = os.path.join(parent_storage_path, name)
                    target_path = os.path.join(new_order_storage_path, name)
                    if os.path.isfile(source_path):
                        try:
                            shutil.copy2(source_path, target_path)
                        except Exception:
                            logger.exception(
                                "copy parent file failed for forecast split: %s", source_path
                            )

            source_shoe = db.session.query(Shoe).filter(Shoe.shoe_id == source_order_shoe.shoe_id).first()
            if source_shoe and os.path.exists(parent_storage_path):
                source_shoe_dir = os.path.join(parent_storage_path, source_shoe.shoe_rid)
                target_shoe_dir = os.path.join(new_order_storage_path, source_shoe.shoe_rid)
                if os.path.exists(source_shoe_dir):
                    try:
                        shutil.copytree(source_shoe_dir, target_shoe_dir, dirs_exist_ok=True)
                    except Exception:
                        logger.exception(
                            "copy shoe dir failed for forecast split: %s", source_shoe_dir
                        )

            created_order_ids.append(new_order.order_id)
            created_order_rids.append(new_order.order_rid)

        order_status.order_current_status = 7
        order_status.order_status_value = 0
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.exception("forecast split dispatch failed, order_id=%s", order_id)
        return jsonify({"error": f"forecast split dispatch failed: {str(ex)}"}), 500

    return (
        jsonify(
            {
                "message": "forecast order dispatched and split successfully",
                "sourceOrderId": order_id,
                "createdOrderIds": created_order_ids,
                "createdOrderRids": created_order_rids,
            }
        ),
        200,
    )


@order_create_bp.route("/ordercreate/updateremark", methods=["POST"])
def order_remark_update():
    remark_form = request.json.get("orderShoeRemarkForm")
    order_shoe_id = remark_form["orderShoeId"]
    business_technical_remark = remark_form["technicalRemark"]
    business_material_remark = remark_form["materialRemark"]
    order_shoe_entity = (
        db.session.query(OrderShoe)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .first()
    )
    order_shoe_entity.business_material_remark = business_material_remark
    order_shoe_entity.business_technical_remark = business_technical_remark
    db.session.commit()
    return jsonify({"msg": "ok"}), 200


@order_create_bp.route("/ordercreate/updateordercid", methods=["POST"])
def order_cid_update():
    order_id = request.json.get("orderId")
    order_cid = request.json.get("orderCid")
    order_entity = db.session.query(Order).filter(Order.order_id == order_id).first()
    if order_entity:
        order_entity.order_cid = order_cid
    else:
        return jsonify({"error": "order not found"}), 400
    db.session.commit()
    return jsonify({"msg": "ok"}), 200


@order_create_bp.route("/ordercreate/updateorderrid", methods=["POST"])
def order_rid_update():
    order_id = request.json.get("orderId")
    order_new_rid = (request.json.get("orderNewRid") or "").strip()
    order_entity = db.session.query(Order).filter(Order.order_id == order_id).first()
    if order_entity:
        existing_entity = db.session.query(Order).filter(Order.order_rid == order_new_rid).first()
        if existing_entity and existing_entity.order_id != order_id:
            return jsonify({"error": "订单号已存在"}), 400

        old_dir_name = resolve_order_storage_dir_name(order_entity.order_id, order_entity.order_rid)
        order_entity.order_rid = order_new_rid
        db.session.commit()

        new_dir_name = resolve_order_storage_dir_name(order_entity.order_id, order_entity.order_rid)
        old_dir_path = os.path.join(FILE_STORAGE_PATH, old_dir_name)
        new_dir_path = os.path.join(FILE_STORAGE_PATH, new_dir_name)
        try:
            if old_dir_name != new_dir_name and os.path.exists(old_dir_path):
                if os.path.exists(new_dir_path):
                    for name in os.listdir(old_dir_path):
                        src = os.path.join(old_dir_path, name)
                        dst = os.path.join(new_dir_path, name)
                        if os.path.isdir(src):
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src, dst)
                else:
                    os.rename(old_dir_path, new_dir_path)
            os.makedirs(new_dir_path, exist_ok=True)
        except Exception:
            logger.exception("failed to migrate order storage dir for order_id=%s", order_id)

        return jsonify({"msg": "update OK"}), 200
    else:
        return jsonify({"error": "order not found"}), 404


@order_create_bp.route("/ordercreate/updateordertype", methods=["POST"])
def order_type_update():
    order_id = request.json.get("orderId")
    order_type_raw = request.json.get("orderType")
    if not order_id:
        return jsonify({"message": "orderId is required"}), 400
    normalized_type = normalize_order_type(order_type_raw)
    if normalized_type != ORDER_TYPE_NORMAL:
        return jsonify({"message": "only conversion to normal order is allowed"}), 400
    order_entity = db.session.query(Order).filter(Order.order_id == order_id).first()
    if not order_entity:
        return jsonify({"message": "order not found"}), 404
    if order_entity.order_type == ORDER_TYPE_NORMAL:
        return jsonify({"message": "order already normal"}), 200
    status_entity = (
        db.session.query(OrderStatus)
        .filter(OrderStatus.order_id == order_id)
        .first()
    )
    if not status_entity:
        return jsonify({"message": "order status not found"}), 404
    if status_entity.order_current_status < 7:
        return jsonify({"message": "order not approved by general manager"}), 400
    order_entity.order_type = ORDER_TYPE_NORMAL
    db.session.commit()
    return jsonify({"message": "order type updated successfully"}), 200


@order_create_bp.route("/ordercreate/updateordershoecustomername", methods=["POST"])
def order_shoe_customer_name_update():
    order_shoe_id = request.json.get("orderShoeId")
    order_shoe_customer_name = request.json.get("shoeCid")
    order_shoe_entity = (
        db.session.query(OrderShoe)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .first()
    )
    if order_shoe_entity:
        order_shoe_entity.customer_product_name = order_shoe_customer_name
    else:
        return jsonify({"error": "order shoe not found"}), 500
    db.session.commit()
    return jsonify({"msg": "OK"}), 200


@order_create_bp.route("/ordercreate/updatecustomercolorname", methods=["POST"])
def order_shoe_type_customer_color_update():
    type_id_to_cus_color = request.json.get("orderShoeTypeCustomerColorForm")
    order_shoe_type_ids = type_id_to_cus_color.keys()
    for order_shoe_type_id in order_shoe_type_ids:
        entity = (
            db.session.query(OrderShoeType)
            .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
            .first()
        )
        if entity:
            entity.customer_color_name = type_id_to_cus_color[order_shoe_type_id]
        else:
            return jsonify({"error": "order_shoe_type_id not found"}), 404
    db.session.commit()
    return jsonify({"msg": "customer color updated"}), 200


@order_create_bp.route("/ordercreate/template", methods=["GET"])
def order_create_template():
    salesman_id = request.args.get("staffId", type=str)
    orders = (
        db.session.query(
            Order.customer_id, Order.batch_info_type_id, func.count(Order.order_id)
        )
        .filter(Order.salesman_id == salesman_id)
        .join(
            BatchInfoType, Order.batch_info_type_id == BatchInfoType.batch_info_type_id
        )
        .join(Customer, Order.customer_id == Customer.customer_id)
        .group_by(Order.customer_id, Order.batch_info_type_id)
        .order_by(func.count(Order.order_id).desc())
    ).all()
    customer_entities = db.session.query(Customer).all()
    batch_info_entities = db.session.query(BatchInfoType).all()
    customer_mapping = {}
    batch_info_mapping = {}
    customer_attr_names = ["customer_name", "customer_brand", "customer_id"]
    batch_info_attr_names = ["batch_info_type_name", "batch_info_type_id"]
    for entity in customer_entities:
        customer_mapping[entity.customer_id] = entity
    for entity in batch_info_entities:
        batch_info_mapping[entity.batch_info_type_id] = entity
    response = []
    for cid, bid, count in orders:
        response_entity = {}
        for attr in customer_attr_names:
            response_entity[to_camel(attr)] = getattr(customer_mapping[cid], attr)
        for attr in batch_info_attr_names:
            response_entity[to_camel(attr)] = getattr(batch_info_mapping[bid], attr)
        response_entity["count"] = count
        response.append(response_entity)
    return jsonify(response), 200


@order_create_bp.route("/ordercreate/savebatchtemplate", methods=["POST"])
def save_batch_template():
    template_name = request.json.get("templateName")
    template_description = request.json.get("templateDescription", "")
    template_detail = request.json.get("templateDetail", [])
    customer_brand_id = template_detail[0].get("customerId")

    if not template_name:
        return (
            jsonify({"error": "Template name, customer name, and brand are required"}),
            400,
        )
    # Check if the template name already exists
    existing_template = (
        db.session.query(BatchInfoTemplate)
        .filter(
            BatchInfoTemplate.template_name == template_name,
            BatchInfoTemplate.customer_brand_id == customer_brand_id,
        )
        .first()
    )
    if existing_template:
        return (
			jsonify({"error": "Template name already exists for this customer brand"}),
			400,
		)
    # Validate template_detail structure
    pacakging_info_id_list = [
		detail.get("packagingInfoId") for detail in template_detail
	]

    # Create a new BatchInfoTemplate instance
    new_template = BatchInfoTemplate(
		customer_brand_id=customer_brand_id,
		pakaging_info_id_json=json.dumps(pacakging_info_id_list),
		template_name=template_name,
		template_description=template_description,
	)
    db.session.add(new_template)
    db.session.flush()
    db.session.commit()

    return jsonify({"message": "Batch template saved successfully"}), 200

@order_create_bp.route("/ordercreate/getallbatchtemplates", methods=["GET"])
def get_all_batch_templates():
	customer_name = request.args.get("customerName")
	customer_brand = request.args.get("customerBrand")
	if not customer_name or not customer_brand:
		return jsonify({"error": "Customer name and brand are required"}), 400
	# Query for templates based on customer name and brand
	customer_brand_id = (
		db.session.query(Customer.customer_id)
		.filter(
			Customer.customer_name == customer_name,
			Customer.customer_brand == customer_brand,
		)
		.first()
	)
	if not customer_brand_id:
		return jsonify({"error": "Customer not found"}), 404
	customer_brand_id = customer_brand_id.customer_id
	templates = (
		db.session.query(BatchInfoTemplate)
		.filter(BatchInfoTemplate.customer_brand_id == customer_brand_id)
		.all()
	)
	response = []
	for template in templates:
		packaging_infos = (
			db.session.query(PackagingInfo)
			.filter(PackagingInfo.packaging_info_id.in_(json.loads(template.pakaging_info_id_json)))
			.all()
		)
		pakaging_info_list = [
			{
				"batchInfoTypeId": packaging_info.batch_info_type_id,
				"customerId": packaging_info.customer_id,
				"packagingInfoLocale": packaging_info.packaging_info_locale,
				"packagingInfoId": packaging_info.packaging_info_id,
				"packagingInfoName": packaging_info.packaging_info_name,
				"size34Ratio": packaging_info.size_34_ratio,
				"size35Ratio": packaging_info.size_35_ratio,
				"size36Ratio": packaging_info.size_36_ratio,
				"size37Ratio": packaging_info.size_37_ratio,
				"size38Ratio": packaging_info.size_38_ratio,
				"size39Ratio": packaging_info.size_39_ratio,
				"size40Ratio": packaging_info.size_40_ratio,
				"size41Ratio": packaging_info.size_41_ratio,
				"size42Ratio": packaging_info.size_42_ratio,
				"size43Ratio": packaging_info.size_43_ratio,
				"size44Ratio": packaging_info.size_44_ratio,
				"size45Ratio": packaging_info.size_45_ratio,
				"size46Ratio": packaging_info.size_46_ratio,
				"totalQuantityRatio": packaging_info.total_quantity_ratio,
			}
			for packaging_info in packaging_infos
		]
		template_data = {
			"batchInfoTemplateId": template.batch_info_template_id,
			"customerName": customer_name,
			"customerBrand": customer_brand,
			"batchInfoData" : pakaging_info_list,
			"templateName": template.template_name,
			"templateDescription": template.template_description,
		}
		response.append(template_data)

	return jsonify(response), 200

@order_create_bp.route("/ordercreate/deletebatchtemplate", methods=["POST"])
def delete_batch_template():
    template_id = request.json.get("batchInfoTemplateId")
    if not template_id:
        return jsonify({"error": "Template ID is required"}), 400
    template_entity = db.session.query(BatchInfoTemplate).filter_by(batch_info_template_id=template_id).first()
    if not template_entity:
        return jsonify({"error": "Template not found"}), 404

    db.session.delete(template_entity)
    db.session.commit()
    return jsonify({"message": "Batch template deleted successfully"}), 200


@order_create_bp.route("/ordercreate/saveordertemplate", methods=["POST"])
def save_order_template():
    data = request.json or {}
    template_name = data.get("templateName")
    template_description = data.get("templateDescription", "")
    creator_staff_id = data.get("staffId") or data.get("creatorStaffId")
    order_data = data.get("orderData")
    order_shoe_data = data.get("orderShoeData")

    if not template_name or not order_data:
        return jsonify({"error": "templateName and orderData are required"}), 400

    # Ensure order_data contains customer identification; if missing, try to fetch from DB using orderId/orderRid
    customer_id = None
    customer_brand = None
    customer_name = None
    if isinstance(order_data, dict):
        customer_id = order_data.get("customerId")
        customer_brand = order_data.get("customerBrand")
        customer_name = order_data.get("customerName")

    # attempt to enrich from orderId/orderId in payload
    order_id_from_payload = data.get("orderId") or (order_data.get("orderId") if isinstance(order_data, dict) else None)
    order_rid_from_payload = data.get("orderRid") or (order_data.get("orderRid") if isinstance(order_data, dict) else None)
    if not customer_id and (order_id_from_payload or order_rid_from_payload):
        if order_id_from_payload:
            order_entity = db.session.query(Order).filter(Order.order_id == order_id_from_payload).first()
        else:
            order_entity = db.session.query(Order).filter(Order.order_rid == order_rid_from_payload).first()
        if order_entity:
            customer_id = order_entity.customer_id

    if customer_id and (not customer_brand or not customer_name):
        cust = db.session.query(Customer).filter(Customer.customer_id == customer_id).first()
        if cust:
            customer_brand = cust.customer_brand
            customer_name = cust.customer_name

    # Ensure order_data has these fields for easier frontend consumption
    if isinstance(order_data, dict):
        if customer_id:
            order_data["customerId"] = customer_id
        if customer_brand:
            order_data["customerBrand"] = customer_brand
        if customer_name:
            order_data["customerName"] = customer_name

    # Build a compact reference-based payload to save space.
    # We'll store minimal IDs and mappings; the GET endpoint will resolve to full objects.
    compact_shoes = []
    # collect packaging info objects found in the incoming payload so we can return them without DB lookups
    packaging_info_map = {}
    # If an order_id is provided, prefer building template from existing order records
    if order_id_from_payload:
        try:
            order_shoes = db.session.query(OrderShoe).filter(OrderShoe.order_id == order_id_from_payload).all()
            for os in order_shoes:
                shoe = db.session.query(Shoe).filter(Shoe.shoe_id == os.shoe_id).first()
                # fetch all shoe types for this order_shoe
                ost_rows = db.session.query(OrderShoeType).filter(OrderShoeType.order_shoe_id == os.order_shoe_id).all()
                for ost in ost_rows:
                    # resolve shoe_type entity
                    st = db.session.query(ShoeType).filter(ShoeType.shoe_type_id == ost.shoe_type_id).first()
                    # collect batch infos
                    batch_entities = db.session.query(OrderShoeBatchInfo).filter(OrderShoeBatchInfo.order_shoe_type_id == ost.order_shoe_type_id).all()
                    pkg_ids = []
                    norm_qmap = {}
                    for b in batch_entities:
                        pid = b.packaging_info_id
                        if pid:
                            pkg_ids.append(pid)
                            # unit per ratio or packaging_info_quantity used as quantity mapping
                            norm_qmap[str(pid)] = float(b.packaging_info_quantity) if b.packaging_info_quantity is not None else 0
                            # try to enrich packaging_info_map from PackagingInfo table
                            try:
                                p = db.session.query(PackagingInfo).filter(PackagingInfo.packaging_info_id == pid).first()
                                if p:
                                    packaging_info_map[str(pid)] = {
                                        "packagingInfoId": p.packaging_info_id,
                                        "packagingInfoName": p.packaging_info_name,
                                        "size34Ratio": p.size_34_ratio,
                                        "size35Ratio": p.size_35_ratio,
                                        "size36Ratio": p.size_36_ratio,
                                        "size37Ratio": p.size_37_ratio,
                                        "size38Ratio": p.size_38_ratio,
                                        "size39Ratio": p.size_39_ratio,
                                        "size40Ratio": p.size_40_ratio,
                                        "size41Ratio": p.size_41_ratio,
                                        "size42Ratio": p.size_42_ratio,
                                        "size43Ratio": p.size_43_ratio,
                                        "size44Ratio": p.size_44_ratio,
                                        "size45Ratio": p.size_45_ratio,
                                        "size46Ratio": p.size_46_ratio,
                                        "totalQuantityRatio": p.total_quantity_ratio,
                                    }
                            except Exception:
                                pass

                    compact_shoes.append({
                        "shoeRid": shoe.shoe_rid if shoe else None,
                        "shoeId": shoe.shoe_id if shoe else None,
                        "shoeTypeId": ost.shoe_type_id,
                        "colorId": (st.color_id if st and hasattr(st, 'color_id') else None),
                        "colorName": None,
                        "businessMaterialRemark": os.business_material_remark if hasattr(os, 'business_material_remark') else None,
                        "businessTechnicalRemark": os.business_technical_remark if hasattr(os, 'business_technical_remark') else None,
                        "packagingInfoIds": pkg_ids,
                        "quantityMapping": norm_qmap,
                        "customerShoeName": os.customer_product_name,
                        "customerColorName": ost.customer_color_name or "",
                    })
        except Exception as e:
            logger.exception("Failed to build template from order_id %s: %s", order_id_from_payload, e)
    elif isinstance(order_shoe_data, list):
        for s in order_shoe_data:
            # s may be either a shoe-type row or a parent shoe containing shoeTypes
            # Normalize to single shoe-type entries referencing IDs
            if s is None:
                continue
            if not isinstance(s, dict):
                continue
            # If item has nested shoeTypes, flatten references
            nested = s.get("shoeTypeData") or s.get("shoeTypes") or s.get("shoeTypeList")
            if isinstance(nested, list) and len(nested) > 0:
                for st in nested:
                    # helper to extract packagingInfoId from various field names
                    def _pack_id(b):
                        return b.get("packagingInfoId") or b.get("packaging_info_id") or b.get("id") or b.get("packagingId")

                    raw_batches = st.get("orderShoeTypeBatchInfo") or st.get("shoeTypeBatchInfoList") or st.get("batchInfo") or []
                    pkg_ids = []
                    if isinstance(raw_batches, list):
                        for b in raw_batches:
                            pid = _pack_id(b)
                            if pid is not None:
                                # capture packaging info object if present
                                try:
                                    p_obj = {
                                        "packagingInfoId": pid,
                                        "packagingInfoName": b.get("packagingInfoName") or b.get("packaging_info_name") or b.get("name"),
                                        "size34Ratio": b.get("size34Ratio") or b.get("size_34_ratio") or b.get("size34_ratio"),
                                        "size35Ratio": b.get("size35Ratio") or b.get("size_35_ratio"),
                                        "size36Ratio": b.get("size36Ratio") or b.get("size_36_ratio"),
                                        "size37Ratio": b.get("size37Ratio") or b.get("size_37_ratio"),
                                        "size38Ratio": b.get("size38Ratio") or b.get("size_38_ratio"),
                                        "size39Ratio": b.get("size39Ratio") or b.get("size_39_ratio"),
                                        "size40Ratio": b.get("size40Ratio") or b.get("size_40_ratio"),
                                        "size41Ratio": b.get("size41Ratio") or b.get("size_41_ratio"),
                                        "size42Ratio": b.get("size42Ratio") or b.get("size_42_ratio"),
                                        "size43Ratio": b.get("size43Ratio") or b.get("size_43_ratio"),
                                        "size44Ratio": b.get("size44Ratio") or b.get("size_44_ratio"),
                                        "size45Ratio": b.get("size45Ratio") or b.get("size_45_ratio"),
                                        "size46Ratio": b.get("size46Ratio") or b.get("size_46_ratio"),
                                        "totalQuantityRatio": b.get("totalQuantityRatio") or b.get("total_quantity_ratio") or b.get("totalRatio")
                                    }
                                    packaging_info_map[str(pid)] = p_obj
                                except Exception:
                                    pass
                                pkg_ids.append(pid)

                    # try multiple possible quantity mapping keys
                    qmap = st.get("quantityMapping") or st.get("batchQuantityMapping") or st.get("batchQuantityMap") or st.get("quantity_map") or {}
                    # normalize keys to strings
                    norm_qmap = {}
                    if isinstance(qmap, dict):
                        for k, v in qmap.items():
                            try:
                                key = str(int(k)) if isinstance(k, (int, str)) and str(k).isdigit() else str(k)
                            except Exception:
                                key = str(k)
                            norm_qmap[key] = v

                    compact_shoes.append({
                        "shoeRid": st.get("shoeRid") or s.get("shoeRid") or st.get("shoe_rid"),
                        "shoeId": st.get("shoeId") or s.get("shoeId") or st.get("shoe_id"),
                        "shoeTypeId": st.get("shoeTypeId") or st.get("shoe_type_id"),
                        "colorId": st.get("colorId") or st.get("color_id") or st.get("colorIdFromTemplate"),
                        "colorName": st.get("colorName") or st.get("color") or st.get("shoeTypeColorName"),
                        "businessMaterialRemark": st.get("businessMaterialRemark") or st.get("business_material_remark") or s.get("businessMaterialRemark") or s.get("business_material_remark") or None,
                        "businessTechnicalRemark": st.get("businessTechnicalRemark") or st.get("business_technical_remark") or s.get("businessTechnicalRemark") or s.get("business_technical_remark") or None,
                        "packagingInfoIds": pkg_ids,
                        "quantityMapping": norm_qmap,
                        "customerShoeName": st.get("customerShoeName") or st.get("customerProductName") or "",
                        "customerColorName": st.get("customerColorName") or "",
                    })
            else:
                # non-nested case: similar extraction
                raw_batches = s.get("orderShoeTypeBatchInfo") or s.get("shoeTypeBatchInfoList") or s.get("batchInfo") or []
                def _pack_id(b):
                    return b.get("packagingInfoId") or b.get("packaging_info_id") or b.get("id") or b.get("packagingId")

                pkg_ids = []
                if isinstance(raw_batches, list):
                    for b in raw_batches:
                        pid = _pack_id(b)
                        if pid is not None:
                            try:
                                p_obj = {
                                    "packagingInfoId": pid,
                                    "packagingInfoName": b.get("packagingInfoName") or b.get("packaging_info_name") or b.get("name"),
                                    "size34Ratio": b.get("size34Ratio") or b.get("size_34_ratio"),
                                    "size35Ratio": b.get("size35Ratio") or b.get("size_35_ratio"),
                                    "size36Ratio": b.get("size36Ratio") or b.get("size_36_ratio"),
                                    "size37Ratio": b.get("size37Ratio") or b.get("size_37_ratio"),
                                    "size38Ratio": b.get("size38Ratio") or b.get("size_38_ratio"),
                                    "size39Ratio": b.get("size39Ratio") or b.get("size_39_ratio"),
                                    "size40Ratio": b.get("size40Ratio") or b.get("size_40_ratio"),
                                    "size41Ratio": b.get("size41Ratio") or b.get("size_41_ratio"),
                                    "size42Ratio": b.get("size42Ratio") or b.get("size_42_ratio"),
                                    "size43Ratio": b.get("size43Ratio") or b.get("size_43_ratio"),
                                    "size44Ratio": b.get("size44Ratio") or b.get("size_44_ratio"),
                                    "size45Ratio": b.get("size45Ratio") or b.get("size_45_ratio"),
                                    "size46Ratio": b.get("size46Ratio") or b.get("size_46_ratio"),
                                    "totalQuantityRatio": b.get("totalQuantityRatio") or b.get("total_quantity_ratio") or b.get("totalRatio")
                                }
                                packaging_info_map[str(pid)] = p_obj
                            except Exception:
                                pass
                            pkg_ids.append(pid)

                qmap = s.get("quantityMapping") or s.get("batchQuantityMapping") or s.get("batchQuantityMap") or s.get("quantity_map") or {}
                norm_qmap = {}
                if isinstance(qmap, dict):
                    for k, v in qmap.items():
                        try:
                            key = str(int(k)) if isinstance(k, (int, str)) and str(k).isdigit() else str(k)
                        except Exception:
                            key = str(k)
                        norm_qmap[key] = v

                compact_shoes.append({
                    "shoeRid": s.get("shoeRid") or s.get("shoe_rid"),
                    "shoeId": s.get("shoeId") or s.get("shoe_id"),
                    "shoeTypeId": s.get("shoeTypeId") or s.get("shoe_type_id"),
                    "colorId": s.get("colorId") or s.get("color_id"),
                    "colorName": s.get("colorName") or s.get("color") or s.get("shoeTypeColorName"),
                    "businessMaterialRemark": s.get("businessMaterialRemark") or s.get("business_material_remark") or None,
                    "businessTechnicalRemark": s.get("businessTechnicalRemark") or s.get("business_technical_remark") or None,
                    "packagingInfoIds": pkg_ids,
                    "quantityMapping": norm_qmap,
                    "customerShoeName": s.get("customerShoeName") or s.get("customerProductName") or "",
                    "customerColorName": s.get("customerColorName") or "",
                })

    compact_payload = {
        "meta": {
            "customerId": customer_id,
            "customerBrand": customer_brand,
            "customerName": customer_name,
            "batchInfoTypeId": (order_data.get("batchInfoTypeId") if isinstance(order_data, dict) else None) or (order_data.get("batchInfoTypeId") if isinstance(order_data, dict) else None) or None,
            "batchInfoTypeName": (order_data.get("batchInfoTypeName") if isinstance(order_data, dict) else None) or (order_data.get("batchInfoTypeName") if isinstance(order_data, dict) else None) or None,
        },
        "shoes": compact_shoes,
        # compact: only store ids (shoeTypeId, packagingInfoIds, colorId). Do NOT persist packaging objects here to save space.
        "compact": True,
    }
    # Persist the compact ID-based payload directly to save DB space (no compression)
    new_template = OrderTemplate(
        template_name=template_name,
        template_description=template_description,
        creator_staff_id=creator_staff_id,
        customer_id=customer_id,
        customer_brand=customer_brand,
        order_template_json=compact_payload,
        source_order_id=order_id_from_payload if order_id_from_payload else None,
    )
    db.session.add(new_template)
    db.session.flush()
    db.session.commit()

    return jsonify({"message": "Order template saved successfully", "orderTemplateId": new_template.order_template_id}), 200


@order_create_bp.route("/ordercreate/getordertemplates", methods=["GET"])
def get_order_templates():
    # Return global templates. Optional: filter by customer_id when provided.
    customer_id = request.args.get("customerId", type=int)
    q = db.session.query(OrderTemplate)
    if customer_id:
        q = q.filter(OrderTemplate.customer_id == customer_id)

    templates = q.order_by(OrderTemplate.create_time.desc()).all()
    response = []
    for t in templates:
        # try to extract some metadata from stored json
        meta = t.order_template_json or {}
        if isinstance(meta, dict) and meta.get("compact"):
            order_data = meta.get("meta") or {}
        else:
            order_data = meta.get("orderData") if isinstance(meta, dict) else {}
        customer_name = order_data.get("customerName") if isinstance(order_data, dict) else None
        customer_brand = order_data.get("customerBrand") if isinstance(order_data, dict) else t.customer_brand
        response.append(
            {
                "orderTemplateId": t.order_template_id,
                "templateName": t.template_name,
                "templateDescription": t.template_description,
                "creatorStaffId": t.creator_staff_id,
                "customerId": t.customer_id,
                "sourceOrderId": getattr(t, 'source_order_id', None),
                "customerName": customer_name,
                "customerBrand": customer_brand,
                "createTime": t.create_time.isoformat() if t.create_time else None,
            }
        )
    return jsonify(response), 200


@order_create_bp.route("/ordercreate/getordertemplate", methods=["GET"])
def get_order_template_by_id():
    tid = request.args.get("orderTemplateId", type=int)
    if not tid:
        return jsonify({"error": "orderTemplateId is required"}), 400
    t = db.session.query(OrderTemplate).filter(OrderTemplate.order_template_id == tid).first()
    if not t:
        return jsonify({"error": "template not found"}), 404
    # If the stored template is compact (ID-only), resolve referenced entities to return
    # Load stored compact payload (saved as ID-only JSON)
    stored = t.order_template_json or {}

    if isinstance(stored, dict) and stored.get("compact"):
        meta = stored.get("meta") or {}
        shoes = []
        for sref in stored.get("shoes") or []:
            shoe_type = None
            shoe = None
            pkg_list = []
            color = None
            if sref.get("shoeTypeId"):
                shoe_type = db.session.query(ShoeType).filter(ShoeType.shoe_type_id == sref.get("shoeTypeId")).first()
            if sref.get("shoeId"):
                shoe = db.session.query(Shoe).filter(Shoe.shoe_id == sref.get("shoeId")).first()
            # resolve packaging infos
            pkg_ids = sref.get("packagingInfoIds") or []
            if pkg_ids:
                # prefer DB-resolved packaging info; fall back to packagingInfos stored in the template payload
                pkg_entities = db.session.query(PackagingInfo).filter(PackagingInfo.packaging_info_id.in_(pkg_ids)).all()
                if pkg_entities:
                    for p in pkg_entities:
                        pkg_list.append({
                            "packagingInfoId": p.packaging_info_id,
                            "packagingInfoName": p.packaging_info_name,
                            "size34Ratio": p.size_34_ratio,
                            "size35Ratio": p.size_35_ratio,
                            "size36Ratio": p.size_36_ratio,
                            "size37Ratio": p.size_37_ratio,
                            "size38Ratio": p.size_38_ratio,
                            "size39Ratio": p.size_39_ratio,
                            "size40Ratio": p.size_40_ratio,
                            "size41Ratio": p.size_41_ratio,
                            "size42Ratio": p.size_42_ratio,
                            "size43Ratio": p.size_43_ratio,
                            "size44Ratio": p.size_44_ratio,
                            "size45Ratio": p.size_45_ratio,
                            "size46Ratio": p.size_46_ratio,
                            "totalQuantityRatio": p.total_quantity_ratio,
                        })
                else:
                    stored_pkgs = stored.get("packagingInfos") or []
                    # stored_pkgs likely a list of dicts
                    for pid in pkg_ids:
                        for sp in stored_pkgs:
                            try:
                                spid = sp.get("packagingInfoId") or sp.get("packaging_info_id") or sp.get("id")
                            except Exception:
                                spid = None
                            if spid is None:
                                continue
                            if str(spid) == str(pid):
                                # normalize to a numeric packagingInfoId and standard keys
                                normalized_id = sp.get("packagingInfoId") if sp.get("packagingInfoId") is not None else sp.get("packaging_info_id") or sp.get("id")
                                pkg_list.append({
                                    "packagingInfoId": int(normalized_id) if (normalized_id is not None and str(normalized_id).isdigit()) else normalized_id,
                                    "packagingInfoName": sp.get("packagingInfoName") or sp.get("packaging_info_name") or sp.get("name"),
                                    "size34Ratio": sp.get("size34Ratio") or sp.get("size_34_ratio"),
                                    "size35Ratio": sp.get("size35Ratio") or sp.get("size_35_ratio"),
                                    "size36Ratio": sp.get("size36Ratio") or sp.get("size_36_ratio"),
                                    "size37Ratio": sp.get("size37Ratio") or sp.get("size_37_ratio"),
                                    "size38Ratio": sp.get("size38Ratio") or sp.get("size_38_ratio"),
                                    "size39Ratio": sp.get("size39Ratio") or sp.get("size_39_ratio"),
                                    "size40Ratio": sp.get("size40Ratio") or sp.get("size_40_ratio"),
                                    "size41Ratio": sp.get("size41Ratio") or sp.get("size_41_ratio"),
                                    "size42Ratio": sp.get("size42Ratio") or sp.get("size_42_ratio"),
                                    "size43Ratio": sp.get("size43Ratio") or sp.get("size_43_ratio"),
                                    "size44Ratio": sp.get("size44Ratio") or sp.get("size_44_ratio"),
                                    "size45Ratio": sp.get("size45Ratio") or sp.get("size_45_ratio"),
                                    "size46Ratio": sp.get("size46Ratio") or sp.get("size_46_ratio"),
                                    "totalQuantityRatio": sp.get("totalQuantityRatio") or sp.get("total_quantity_ratio") or sp.get("totalRatio"),
                                })
            # resolve color (selected) and available colors for this shoe
            if sref.get("colorId"):
                color = db.session.query(Color).filter(Color.color_id == sref.get("colorId")).first()

            # build shoeTypeColors by querying ShoeType -> Color for this shoeId
            shoe_type_colors = []
            try:
                if sref.get("shoeId"):
                    color_rows = (
                        db.session.query(ShoeType, Color)
                        .join(Color, ShoeType.color_id == Color.color_id)
                        .filter(ShoeType.shoe_id == sref.get("shoeId"))
                        .all()
                    )
                    for st, col in color_rows:
                        shoe_type_colors.append({"label": col.color_name, "value": col.color_id})
            except Exception:
                shoe_type_colors = []

            shoes.append({
                "shoeRid": sref.get("shoeRid"),
                "shoeId": sref.get("shoeId"),
                "shoeTypeId": sref.get("shoeTypeId"),
                "shoeImageUrl": shoe_type.shoe_image_url if shoe_type else None,
                "orderShoeTypeBatchInfo": pkg_list,
                "quantityMapping": sref.get("quantityMapping") or {},
                "customerShoeName": sref.get("customerShoeName") or (shoe and shoe.shoe_rid) or "",
                "customerColorName": sref.get("customerColorName") or (color and color.color_name) or sref.get("colorName") or "",
                "colorId": sref.get("colorId"),
                "colorName": (color and color.color_name) or sref.get("colorName") or None,
                "businessMaterialRemark": sref.get("businessMaterialRemark") or sref.get("business_material_remark") or None,
                "businessTechnicalRemark": sref.get("businessTechnicalRemark") or sref.get("business_technical_remark") or None,
                "shoeTypeColors": shoe_type_colors,
            })

        source_order_id = getattr(t, 'source_order_id', None)
        return jsonify({
            "orderTemplateId": t.order_template_id,
            "templateName": t.template_name,
            "templateDescription": t.template_description,
            "orderTemplate": {"orderData": meta, "orderShoeData": shoes},
            "sourceOrderId": source_order_id,
        }), 200

    # legacy: return stored json as-is
    return jsonify({"orderTemplateId": t.order_template_id, "templateName": t.template_name, "templateDescription": t.template_description, "orderTemplate": t.order_template_json, "sourceOrderId": getattr(t, 'source_order_id', None)}), 200


@order_create_bp.route("/ordercreate/gethistoryordertemplate", methods=["GET"])
def get_history_order_template():
    order_id = request.args.get("orderId", type=int)
    if not order_id:
        return jsonify({"error": "orderId is required"}), 400

    payload = _build_order_template_payload_from_order(order_id)
    if not payload:
        return jsonify({"error": "order not found"}), 404

    payload["historyOrderId"] = order_id
    return jsonify(payload), 200


@order_create_bp.route("/ordercreate/getordersourcelist", methods=["GET"])
def get_order_source_list():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 10, type=int)
    keyword = (request.args.get("keyword") or "").strip()

    character, staff, _ = current_user_info()
    if not character or not staff:
        return jsonify({"error": "current user not found"}), 401

    visibility_filter = _build_order_source_visibility_filter(character.character_id, staff.staff_id)
    if visibility_filter is None:
        return jsonify({"error": "invalid user role"}), 401

    query = (
        db.session.query(
            Order.order_id.label("orderDbId"),
            Order.order_rid.label("orderRid"),
            Order.order_cid.label("orderCid"),
            Order.order_type.label("orderType"),
            Order.start_date.label("orderStartDate"),
            Order.end_date.label("orderEndDate"),
            Order.salesman_id.label("salesmanId"),
            Order.supervisor_id.label("supervisorId"),
            Customer.customer_name.label("customerName"),
            Customer.customer_brand.label("customerBrand"),
            func.group_concat(func.distinct(Shoe.shoe_rid)).label("shoeRId"),
            func.group_concat(func.distinct(OrderShoe.customer_product_name)).label("customerProductName"),
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .filter(visibility_filter)
    )

    if keyword:
        like_keyword = f"%{keyword}%"
        query = query.filter(
            or_(
                Order.order_rid.like(like_keyword),
                Order.order_cid.like(like_keyword),
                Customer.customer_name.like(like_keyword),
                Customer.customer_brand.like(like_keyword),
                Shoe.shoe_rid.like(like_keyword),
                OrderShoe.customer_product_name.like(like_keyword),
            )
        )

    query = query.group_by(
        Order.order_id,
        Order.order_rid,
        Order.order_cid,
        Order.order_type,
        Order.start_date,
        Order.end_date,
        Order.salesman_id,
        Order.supervisor_id,
        Customer.customer_name,
        Customer.customer_brand,
    )

    total = db.session.query(func.count()).select_from(query.subquery()).scalar() or 0

    paged_rows = (
        query.order_by(Order.order_id.desc())
        .offset(max(page - 1, 0) * page_size)
        .limit(page_size)
        .all()
    )

    staff_ids = set()
    for row in paged_rows:
        if row.salesmanId is not None:
            staff_ids.add(row.salesmanId)
        if row.supervisorId is not None:
            staff_ids.add(row.supervisorId)

    staff_entities = db.session.query(Staff).filter(Staff.staff_id.in_(list(staff_ids))).all() if staff_ids else []
    staff_name_map = {entity.staff_id: entity.staff_name for entity in staff_entities}

    result = []
    for row in paged_rows:
        result.append(
            {
                "orderDbId": row.orderDbId,
                "orderRid": row.orderRid,
                "orderCid": row.orderCid,
                "orderType": row.orderType,
                "customerName": row.customerName,
                "customerBrand": row.customerBrand,
                "customerProductName": row.customerProductName or "",
                "shoeRId": row.shoeRId or "",
                "orderStartDate": row.orderStartDate.strftime("%Y-%m-%d") if row.orderStartDate else "",
                "orderEndDate": row.orderEndDate.strftime("%Y-%m-%d") if row.orderEndDate else "",
                "orderSalesman": staff_name_map.get(row.salesmanId, ""),
                "orderSupervisor": staff_name_map.get(row.supervisorId, ""),
            }
        )

    return jsonify({"items": result, "total": total, "page": page, "pageSize": page_size}), 200


@order_create_bp.route("/ordercreate/deleteordertemplate", methods=["POST"])
def delete_order_template():
    tid = request.json.get("orderTemplateId")
    if not tid:
        return jsonify({"error": "orderTemplateId is required"}), 400
    t = db.session.query(OrderTemplate).filter(OrderTemplate.order_template_id == tid).first()
    if not t:
        return jsonify({"error": "template not found"}), 404
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "Order template deleted successfully"}), 200


@order_create_bp.route("/ordercreate/updateordertemplate", methods=["POST"])
def update_order_template():
    tid = request.json.get("orderTemplateId")
    new_name = request.json.get("templateName")
    new_description = request.json.get("templateDescription")
    if not tid:
        return jsonify({"error": "orderTemplateId is required"}), 400
    t = db.session.query(OrderTemplate).filter(OrderTemplate.order_template_id == tid).first()
    if not t:
        return jsonify({"error": "template not found"}), 404
    if new_name:
        t.template_name = new_name
    if new_description is not None:
        t.template_description = new_description
    db.session.commit()
    return jsonify({"message": "Order template updated successfully"}), 200

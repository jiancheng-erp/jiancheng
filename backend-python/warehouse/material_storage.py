from datetime import datetime, date
from decimal import Decimal

from api_utility import format_date, format_datetime, to_camel
from app_config import db
from shared_apis.batch_info_type import get_order_batch_type_helper
from constants import (
    END_OF_PRODUCTION_NUMBER,
    IN_PRODUCTION_ORDER_NUMBER,
    PRODUCTION_LINE_REFERENCE,
    SHOESIZERANGE,
    MATERIAL_PURCHASE_PAYABLE_ID,
)
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request, abort, Response
from models import *
from sqlalchemy import desc, func, text, literal, cast, JSON, or_
import json
from script.refresh_spu_rid import generate_spu_rid
from logger import logger

material_storage_bp = Blueprint("material_storage_bp", __name__)


def outbound_size_material_helper(meta_data, outbound_list):
    for row in outbound_list:
        storage = SizeMaterialStorage.query.get(row["storageId"])
        for i, obj in enumerate(row["outboundAmounts"]):
            shoe_size = 34 + i
            if "amount" not in obj:
                outbound_amount = 0
                obj["amount"] = 0
            else:
                outbound_amount = obj["amount"]
            column_name = f"size_{shoe_size}_current_amount"
            current_value = getattr(storage, column_name)
            if current_value < int(outbound_amount):
                return jsonify({"message": "invalid outbound amount"}), 400
            new_value = current_value - int(outbound_amount)
            setattr(storage, column_name, new_value)
            storage.total_current_amount -= int(outbound_amount)
            if storage.total_current_amount == 0:
                storage.material_storage_status = 2

        record = OutboundRecord(
            outbound_datetime=meta_data["timestamp"],
            outbound_type=meta_data["type"],
            size_material_storage_id=row["storageId"],
        )
        for i, obj in enumerate(row["outboundAmounts"]):
            shoe_size = 34 + i
            column_name = f"size_{shoe_size}_outbound_amount"
            setattr(record, column_name, obj["amount"])
        if meta_data["type"] == 0:
            if meta_data["department"] not in PRODUCTION_LINE_REFERENCE:
                return jsonify({"message": "failed"}), 400
            record.outbound_department = meta_data["department"]
            record.picker = meta_data["picker"]
        elif meta_data == 2:
            record.outbound_address = meta_data["address"]
        db.session.add(record)
        db.session.flush()
        rid = (
            "OR"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + str(record.outbound_record_id)
        )
        record.outbound_rid = rid


@material_storage_bp.route(
    "/warehouse/warehousemanager/getallmaterialtypes", methods=["GET"]
)
def get_all_material_types():
    response = db.session.query(MaterialType.material_type_name).all()
    result = []
    for row in response:
        result.append(row[0])
    return result


@material_storage_bp.route(
    "/warehouse/warehousemanager/getallsuppliernames", methods=["GET"]
)
def get_all_supplier_names():
    response = db.session.query(Supplier.supplier_name).all()
    result = []
    for row in response:
        result.append(row[0])
    return result


@material_storage_bp.route(
    "/warehouse/warehousemanager/getallcompositesuppliers", methods=["GET"]
)
def get_all_composite_suppliers():
    response = db.session.query(Supplier).filter_by(supplier_type="W").all()
    result = []
    for row in response:
        obj = {
            "supplierId": row.supplier_id,
            "supplierName": row.supplier_name,
        }
        result.append(obj)
    return result


@material_storage_bp.route(
    "/warehouse/warehousemanager/getallmaterialinfo", methods=["GET"]
)
def get_all_material_info():
    """
    op_type:
        0: show all orders,
        1: means show inbound info,
        2: means show outbound info,
        3: composite inbound,
        4: composite outbound
    """
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    op_type = request.args.get("opType", default=0, type=int)
    sort_column = request.args.get("sortColumn")
    sort_order = request.args.get("sortOrder")
    is_non_order_material = request.args.get("isNonOrderMaterial", default=0, type=int)
    filters = {
        "material_type_name": request.args.get("materialType", ""),
        "material_name": request.args.get("materialName", ""),
        "material_spec": request.args.get("materialSpec", ""),
        "material_model": request.args.get("materialModel", ""),
        "material_color": request.args.get("materialColor", ""),
        "supplier": request.args.get("supplier", ""),
    }
    if is_non_order_material == 0:
        filters["order_rid"] = request.args.get("orderRId", "")
        filters["shoe_rid"] = request.args.get("shoeRId", "")
    material_filter_map = {
        "material_type_name": MaterialType.material_type_name,
        "material_name": Material.material_name,
        "material_spec": MaterialStorage.inbound_specification,
        "material_model": MaterialStorage.inbound_model,
        "material_color": MaterialStorage.material_storage_color,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
        "shoe_rid": Shoe.shoe_rid,
    }
    size_material_filter_map = {
        "material_type_name": MaterialType.material_type_name,
        "material_name": Material.material_name,
        "material_spec": SizeMaterialStorage.size_material_specification,
        "material_model": SizeMaterialStorage.size_material_model,
        "material_color": SizeMaterialStorage.size_material_color,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
        "shoe_rid": Shoe.shoe_rid,
    }
    query1 = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            OrderShoe.order_shoe_id,
            Shoe.shoe_rid,
            MaterialStorage.material_storage_id,
            MaterialStorage.estimated_inbound_amount,
            MaterialStorage.actual_inbound_amount,
            MaterialStorage.current_amount,
            MaterialStorage.inbound_specification,
            MaterialStorage.unit_price,
            MaterialStorage.inbound_model,
            MaterialStorage.actual_inbound_unit,
            MaterialStorage.actual_purchase_amount,
            MaterialStorage.average_price,
            Material.material_id,
            Material.material_name,
            Material.material_unit,
            MaterialType.material_type_name,
            Material.material_category,
            Supplier.supplier_name,
            MaterialStorage.material_storage_color,
            MaterialStorage.composite_unit_cost,
            cast(literal("{}"), JSON).label("shoe_size_columns"),
        )
        .join(
            Material, Material.material_id == MaterialStorage.actual_inbound_material_id
        )
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(Order, OrderShoe.order_id == Order.order_id)
    )
    query2 = (
        db.session.query(
            Order.order_id,
            Order.order_rid,
            OrderShoe.order_shoe_id,
            Shoe.shoe_rid,
            SizeMaterialStorage.size_material_storage_id.label("material_storage_id"),
            SizeMaterialStorage.total_estimated_inbound_amount.label(
                "estimated_inbound_amount"
            ),
            SizeMaterialStorage.total_actual_inbound_amount.label(
                "actual_inbound_amount"
            ),
            SizeMaterialStorage.total_current_amount.label("current_amount"),
            SizeMaterialStorage.size_material_specification.label(
                "material_specification"
            ),
            SizeMaterialStorage.unit_price,
            SizeMaterialStorage.size_material_model.label("size_material"),
            literal("双").label("actual_inbound_unit"),
            SizeMaterialStorage.total_estimated_inbound_amount.label(
                "actual_purchase_amount"
            ),
            SizeMaterialStorage.average_price,
            Material.material_id,
            Material.material_name,
            Material.material_unit,
            MaterialType.material_type_name,
            Material.material_category,
            Supplier.supplier_name,
            SizeMaterialStorage.size_material_color,
            literal(0).label("composite_unit_cost"),
            SizeMaterialStorage.shoe_size_columns,
        )
        .join(Material, Material.material_id == SizeMaterialStorage.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(
            OrderShoe, SizeMaterialStorage.order_shoe_id == OrderShoe.order_shoe_id
        )
        .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(Order, OrderShoe.order_id == Order.order_id)
    )

    for key, value in filters.items():
        if value and value != "":
            query1 = query1.filter(material_filter_map[key].ilike(f"%{value}%"))
            query2 = query2.filter(
                size_material_filter_map[key].ilike(f"%{value}%")
            )

    warehouse_id = request.args.get("warehouseId")
    if warehouse_id and warehouse_id != "":
        query1 = query1.filter(MaterialType.warehouse_id == warehouse_id)
        query2 = query2.filter(MaterialType.warehouse_id == warehouse_id)

    if is_non_order_material == 1:
        query1 = query1.filter(MaterialStorage.order_id.is_(None), MaterialStorage.order_shoe_id.is_(None))
        query2 = query2.filter(SizeMaterialStorage.order_id.is_(None), SizeMaterialStorage.order_shoe_id.is_(None))
    union_query = query1.union(query2)
    count_result = union_query.distinct().count()
    response = union_query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            order_id,
            order_rid,
            order_shoe_id,
            shoe_rid,
            material_storage_id,
            estimated_inbound_amount,
            actual_inbound_amount,
            current_amount,
            material_specification,
            unit_price,
            material_model,
            actual_inbound_unit,
            actual_purchase_amount,
            average_price,
            material_id,
            material_name,
            material_unit,
            material_type_name,
            material_category,
            supplier_name,
            color,
            composite_unit_cost,
            shoe_size_columns,
        ) = row
        obj = {
            "materialId": material_id,
            "materialType": material_type_name,
            "materialName": material_name,
            "materialSpecification": material_specification,
            "materialUnit": material_unit,
            "materialCategory": material_category,
            "estimatedInboundAmount": estimated_inbound_amount,
            "actualPurchaseAmount": actual_purchase_amount,
            "actualInboundAmount": actual_inbound_amount,
            "actualInboundUnit": actual_inbound_unit,
            "currentAmount": current_amount,
            "unitPrice": unit_price,
            "averagePrice": average_price,
            "totalPrice": (
                0 if not unit_price else round(actual_inbound_amount * unit_price, 2)
            ),
            "supplierName": supplier_name,
            "orderId": order_id,
            "orderRId": order_rid,
            "orderShoeId": order_shoe_id,
            "shoeRId": shoe_rid,
            "materialStorageId": material_storage_id,
            "colorName": color,
            "materialModel": material_model,
            "compositeUnitCost": round(composite_unit_cost, 2),
            "compositeTotalPrice": (
                0
                if not composite_unit_cost
                else round(actual_inbound_amount * composite_unit_cost, 2)
            ),
            "shoeSizeColumns": shoe_size_columns,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route("/warehouse/getsizematerialstoragebystorageid", methods=["GET"])
def get_size_material_storage_by_storage_id():
    """
    根据材料库存ID获取尺码材料库存信息
    """
    storage_id = request.args.get("storageId", None)
    if not storage_id:
        _no_storage_id_error()
    storage = db.session.query(SizeMaterialStorage).filter(
        SizeMaterialStorage.size_material_storage_id == storage_id
    ).first()
    if not storage:
        return jsonify({"message": "没有找到该材料库存"}), 404

    obj = {
        "materialStorageId": storage.size_material_storage_id,
        "estimatedInboundAmount": storage.total_estimated_inbound_amount,
        "actualInboundAmount": storage.total_actual_inbound_amount,
        "currentAmount": storage.total_current_amount,
        "shoeSizeColumns": storage.shoe_size_columns,
    }
    for i, shoe_size in enumerate(SHOESIZERANGE):
        estimated_inbound_amount = getattr(
            storage, f"size_{shoe_size}_estimated_inbound_amount"
        )
        actual_inbound_amount = getattr(
            storage, f"size_{shoe_size}_actual_inbound_amount"
        )
        current_amount = getattr(storage, f"size_{shoe_size}_current_amount")
        obj[f"estimatedInboundAmount{i}"] = estimated_inbound_amount
        obj[f"actualInboundAmount{i}"] = actual_inbound_amount
        obj[f"currentAmount{i}"] = current_amount
    return obj


@material_storage_bp.route("/warehouse/getsizematerials", methods=["GET"])
def get_size_materials():
    filters = {
        "material_name": request.args.get("materialName", ""),
        "material_spec": request.args.get("materialSpec", ""),
        "material_model": request.args.get("materialModel", ""),
        "material_color": request.args.get("materialColor", ""),
        "supplier": request.args.get("supplier", ""),
        "order_rid": request.args.get("orderRId", ""),
    }
    material_filter_map = {
        "material_name": Material.material_name,
        "material_spec": SizeMaterialStorage.size_material_specification,
        "material_model": SizeMaterialStorage.size_material_model,
        "material_color": SizeMaterialStorage.size_material_color,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
    }

    query = (
        db.session.query(SizeMaterialStorage, Material, Supplier, Order, Shoe)
        .join(Material, SizeMaterialStorage.material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .join(Order, SizeMaterialStorage.order_id == Order.order_id)
        .join(OrderShoe, SizeMaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .filter(OrderStatus.order_current_status == IN_PRODUCTION_ORDER_NUMBER)
    )
    for key, value in filters.items():
        if value and value != "":
            query = query.filter(material_filter_map[key].ilike(f"%{value}%"))
    response = query.all()
    result = []
    for row in response:
        (storage, material, supplier, order, shoe) = row
        obj = {
            "materialStorageId": storage.size_material_storage_id,
            "materialName": material.material_name,
            "materialModel": storage.size_material_model,
            "materialSpecification": storage.size_material_specification,
            "materialColor": storage.size_material_color,
            "actualInboundUnit": material.material_unit,
            "materialCategory": material.material_category,
            "supplierName": supplier.supplier_name,
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "shoeRId": shoe.shoe_rid,
            "estimatedInboundAmount": storage.total_estimated_inbound_amount,
            "actualInboundAmount": storage.total_actual_inbound_amount,
            "currentAmount": storage.total_current_amount,
            "unitPrice": storage.unit_price,
            "shoeSizeColumns": storage.shoe_size_columns,
        }
        for i, shoe_size in enumerate(SHOESIZERANGE):
            estimated_inbound_amount = getattr(
                storage, f"size_{shoe_size}_estimated_inbound_amount"
            )
            actual_inbound_amount = getattr(
                storage, f"size_{shoe_size}_actual_inbound_amount"
            )
            current_amount = getattr(storage, f"size_{shoe_size}_current_amount")
            obj[f"estimatedInboundAmount{i}"] = estimated_inbound_amount
            obj[f"actualInboundAmount{i}"] = actual_inbound_amount
            obj[f"currentAmount{i}"] = current_amount
        result.append(obj)
    return result


@material_storage_bp.route("/warehouse/getmaterials", methods=["GET"])
def get_materials():
    filters = {
        "material_name": request.args.get("materialName", ""),
        "material_spec": request.args.get("materialSpec", ""),
        "material_model": request.args.get("materialModel", ""),
        "material_color": request.args.get("materialColor", ""),
        "supplier": request.args.get("supplier", ""),
        # "order_rid": request.args.get("orderRId", ""),
    }
    material_filter_map = {
        "material_name": Material.material_name,
        "material_spec": MaterialStorage.material_specification,
        "material_model": MaterialStorage.material_model,
        "material_color": MaterialStorage.material_storage_color,
        "supplier": Supplier.supplier_name,
        # "order_rid": Order.order_rid,
    }
    query = (
        db.session.query(
            MaterialStorage.material_model,
            MaterialStorage.material_specification,
            MaterialStorage.material_storage_color,
            MaterialStorage.actual_inbound_unit,
            Material.material_name,
            Material.material_category,
            Supplier.supplier_name,
        )
        .join(
            Material,
            MaterialStorage.actual_inbound_material_id == Material.material_id,
        )
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .distinct()
    )
    for key, value in filters.items():
        if value and value != "":
            query = query.filter(material_filter_map[key].ilike(f"%{value}%"))
    response = query.all()
    result = []
    for row in response:
        (
            material_model,
            material_specification,
            color,
            unit,
            material_name,
            material_category,
            supplier_name,
        ) = row
        obj = {
            "materialName": material_name,
            "materialModel": material_model,
            "materialSpecification": material_specification,
            "materialColor": color,
            "actualInboundUnit": unit,
            "materialCategory": material_category,
            "supplierName": supplier_name,
        }
        result.append(obj)
    return result


@material_storage_bp.route("/warehouse/getordersbymaterialinfo", methods=["GET"])
def get_orders_by_material_info():
    """
    根据材料信息查找买这个材料的订单号
    """
    data = request.args.get("data", None)
    data_list = json.loads(data)
    result = []
    for input_row in data_list:
        material_name = input_row.get("materialName", None)
        material_specification = input_row.get("materialSpecification", None)
        material_model = input_row.get("materialModel", None)
        material_color = input_row.get("materialColor", None)
        supplier_name = input_row.get("supplierName", None)
        material_category = input_row.get("materialCategory", 0)
        unit = input_row.get("actualInboundUnit", None)

        target_material = (
            db.session.query(Material)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                Material.material_name == material_name,
                Supplier.supplier_name == supplier_name,
            )
            .first()
        )

        if not target_material:
            return jsonify({"message": "没有该材料"}), 404

        material_storages = (
            db.session.query(MaterialStorage, Order, Shoe)
            .outerjoin(Order, Order.order_id == MaterialStorage.order_id)
            .outerjoin(
                OrderShoe, OrderShoe.order_shoe_id == MaterialStorage.order_shoe_id
            )
            .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .filter(
                MaterialStorage.actual_inbound_material_id
                == target_material.material_id,
                MaterialStorage.material_specification == material_specification,
                MaterialStorage.material_model == material_model,
                MaterialStorage.material_storage_color == material_color,
                MaterialStorage.actual_inbound_unit == unit,
                or_(
                    OrderStatus.order_current_status == IN_PRODUCTION_ORDER_NUMBER,
                    OrderStatus.order_current_status == None,
                ),
            )
            .all()
        )
        for row in material_storages:
            storage, order, shoe = row
            obj = {
                "materialStorageId": storage.material_storage_id,
                "materialName": target_material.material_name,
                "materialModel": storage.material_model,
                "materialSpecification": storage.material_specification,
                "materialColor": storage.material_storage_color,
                "actualInboundUnit": storage.actual_inbound_unit,
                "inboundModel": storage.inbound_model,
                "inboundSpecification": storage.inbound_specification,
                "orderId": storage.order_id,
                "orderRId": order.order_rid if order else None,
                "shoeRId": shoe.shoe_rid if shoe else None,
                "estimatedInboundAmount": storage.estimated_inbound_amount,
                "actualInboundAmount": storage.actual_inbound_amount,
                "currentAmount": storage.current_amount,
                "materialCategory": material_category,
            }
            result.append(obj)
    return result


@material_storage_bp.route(
    "/warehouse/warehousemanager/getsizematerialbyid", methods=["GET"]
)
def get_size_material_info_by_id():
    id = request.args.get("sizeMaterialStorageId", None)
    order_id = request.args.get("orderId", None)
    purchase_divide_order_id = request.args.get("purchaseDivideOrderId", None)
    storage = SizeMaterialStorage.query.get(id)
    result = []
    shoe_size_names = []
    if purchase_divide_order_id:
        # find shoe size name by purchase_divide_order_id
        material_id = storage.material_id
        batch_info_type = (
            db.session.query(BatchInfoType)
            .join(
                AssetsPurchaseOrderItem,
                BatchInfoType.batch_info_type_name == AssetsPurchaseOrderItem.size_type,
            )
            .filter(
                AssetsPurchaseOrderItem.material_id == material_id,
                AssetsPurchaseOrderItem.purchase_divide_order_id
                == purchase_divide_order_id,
                BatchInfoType.batch_info_type_usage == 1,
            )
            .first()
        )
        if batch_info_type:
            for i in range(34, 47):
                locale = getattr(batch_info_type, f"size_{i}_name")
                type_name = getattr(batch_info_type, f"batch_info_type_name")
                id = getattr(batch_info_type, f"batch_info_type_id")
                if locale:
                    obj = {"id": id, "label": locale, "type": type_name, "usage": 1}
                    shoe_size_names.append(obj)
                if locale == None:
                    break

    if len(shoe_size_names) == 0:
        if order_id:
            # get shoe size name
            shoe_size_names = get_order_batch_type_helper(order_id)
        else:
            return jsonify({"message": "cannot find shoe size names"}), 404

    for i, shoe_size in enumerate(shoe_size_names):
        shoe_size_db_name = i + 34
        obj = {
            "typeId": shoe_size_names[i]["id"],
            "typeName": shoe_size_names[i]["type"],
            "shoeSizeName": shoe_size_names[i]["label"],
            "predictQuantity": getattr(
                storage, f"size_{shoe_size_db_name}_estimated_inbound_amount"
            ),
            "actualQuantity": getattr(
                storage, f"size_{shoe_size_db_name}_actual_inbound_amount"
            ),
            "currentQuantity": getattr(
                storage, f"size_{shoe_size_db_name}_current_amount"
            ),
        }
        result.append(obj)

    return result


def _find_order_shoe(order_rid) -> tuple[Order, OrderShoe]:
    entities = (
        db.session.query(Order, OrderShoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .filter(Order.order_rid == order_rid)
        .first()
    )
    if not entities:
        error_message = json.dumps({"message": "订单号不存在"})
        abort(Response(error_message, 400))
    return entities.Order, entities.OrderShoe


def _no_storage_id_error():
    error_message = json.dumps({"message": "没有选择材料库存"})
    abort(Response(error_message, 400))


def _empty_material_type():
    error_message = json.dumps({"message": "材料类型不能为空"})
    abort(Response(error_message, 400))


def _create_spu_record(material_id, model, specification, color):
    existed_spu = db.session.query(SPUMaterial).filter(
        SPUMaterial.material_id == material_id,
        SPUMaterial.material_model == model,
        SPUMaterial.material_specification == specification,
        SPUMaterial.color == color,
    ).first()
    if existed_spu:
        return existed_spu.spu_material_id
    rid = generate_spu_rid(material_id)
    spu_record = SPUMaterial(
        material_id=material_id,
        material_model=model,
        material_specification=specification,
        color=color,
        spu_rid=rid,
    )
    db.session.add(spu_record)
    db.session.flush()
    return spu_record.spu_material_id


def _find_storage_in_db(item: dict, material_type_id, supplier_id, batch_info_type_id):
    """
    处理用户手动输入的材料信息
    """
    material_name = item["materialName"]
    material = (
        db.session.query(Material)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(
            Material.material_name == material_name, Supplier.supplier_id == supplier_id
        )
        .first()
    )

    actual_inbound_unit = item["actualInboundUnit"]
    if not material:
        material = Material(
            material_name=material_name,
            material_supplier=supplier_id,
            material_type_id=material_type_id,
            material_unit=actual_inbound_unit,
            material_creation_date=date.today(),
        )
        # 处理材料是否带鞋码
        origin_material = (
            db.session.query(Material)
            .filter(
                Material.material_name == material_name,
            )
            .first()
        )
        material.material_category = origin_material.material_category
        db.session.add(material)
        db.session.flush()
    material_id = material.material_id
    material_model = item["inboundModel"]
    material_specification = item["inboundSpecification"]
    material_color = item["materialColor"]

    material_category = item.get("materialCategory", 0)
    spu_material_id = _create_spu_record(material_id, material_model, material_specification, material_color)

    order_id, order_shoe_id = None, None
    order_rid = item.get("orderRId", None)
    if order_rid:
        order, order_shoe = _find_order_shoe(order_rid)
        order_id = order.order_id
        order_shoe_id = order_shoe.order_shoe_id

    # 普通材料
    if material_category == 0:
        storage_query = db.session.query(MaterialStorage).filter(
            MaterialStorage.actual_inbound_material_id == material_id,
            MaterialStorage.inbound_specification == material_specification,
            MaterialStorage.inbound_model == material_model,
            MaterialStorage.material_storage_color == material_color,
            MaterialStorage.actual_inbound_unit == actual_inbound_unit,
        )
        if order_shoe_id:
            storage_query = storage_query.filter(
                MaterialStorage.order_shoe_id == order_shoe.order_shoe_id,
            )
        else:
            storage_query = storage_query.filter(
                MaterialStorage.order_shoe_id.is_(None),
            )
    # 尺码材料
    elif material_category == 1:
        storage_query = db.session.query(SizeMaterialStorage).filter(
            SizeMaterialStorage.material_id == material_id,
            SizeMaterialStorage.size_material_specification == material_specification,
            SizeMaterialStorage.size_material_model == material_model,
            SizeMaterialStorage.size_material_color == material_color,
        )
        if order_shoe_id:
            storage_query = storage_query.filter(
                SizeMaterialStorage.order_shoe_id == order_shoe.order_shoe_id,
            )
        else:
            storage_query = storage_query.filter(
                SizeMaterialStorage.order_shoe_id.is_(None),
            )
    # 根据材料信息查找对应的材料库存
    # 如果没有找到，则创建新的材料库存
    storage = storage_query.first()
    if not storage:
        if material_category == 0:
            unit = item["actualInboundUnit"]
            storage = MaterialStorage(
                material_id=material_id,
                actual_inbound_material_id=material_id,
                material_specification=material_specification,
                material_model=material_model,
                inbound_model=material_model,
                inbound_specification=material_specification,
                material_storage_color=material_color,
                actual_inbound_unit=unit,
                spu_material_id=spu_material_id,
                order_id=order_id,
                order_shoe_id=order_shoe_id,
            )
        elif material_category == 1:
            batch_info_type = (
                db.session.query(BatchInfoType)
                .filter(BatchInfoType.batch_info_type_id == batch_info_type_id)
                .first()
            )
            shoe_size_columns: list = item.get("shoeSizeColumns", [])
            if not shoe_size_columns and not batch_info_type and material_name == "大底":
                error_message = json.dumps({"message": "尺码材料没有鞋码"})
                abort(Response(error_message, 400))
            if shoe_size_columns == [] and batch_info_type:
                for i in range(len(SHOESIZERANGE)):
                    db_name = i + 34
                    size_name = getattr(batch_info_type, f"size_{db_name}_name")
                    if size_name:
                        shoe_size_columns.append(size_name)
                    else:
                        break
            storage = SizeMaterialStorage(
                material_id=material_id,
                size_material_specification=material_specification,
                size_material_model=material_model,
                size_material_color=material_color,
                shoe_size_columns=shoe_size_columns,
                spu_material_id=spu_material_id,
                order_id=order_id,
                order_shoe_id=order_shoe_id,
            )
        db.session.add(storage)
        db.session.flush()
    if material_category == 0:
        storage_id = storage.material_storage_id
    elif material_category == 1:
        storage_id = storage.size_material_storage_id
    return storage_id, storage


def _handle_supplier_obj(supplier_name: str):
    # sanitize the supplier name
    supplier_name = supplier_name.replace(" ", "")
    if supplier_name == "":
        error_message = json.dumps({"message": "供应商名称不能为空"})
        abort(Response(error_message, 400))
    supplier_obj = (
        db.session.query(Supplier)
        .filter(Supplier.supplier_name == supplier_name)
        .first()
    )
    if not supplier_obj:
        supplier_obj = Supplier(supplier_name=supplier_name)
        db.session.add(supplier_obj)
        db.session.flush()
    return supplier_obj


def _handle_purchase_inbound(data, next_group_id, is_warehouse_changed=False):
    timestamp = data["currentDateTime"]
    formatted_timestamp = (
        timestamp.replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
    )
    inbound_rid = "IR" + formatted_timestamp + "T0"
    supplier_name = data.get("supplierName", None)
    warehouse_id = data.get("warehouseId", None)
    batch_info_type_id = data.get("batchInfoTypeId", None)
    material_type_id = data.get("materialTypeId", None)
    remark = data.get("remark", None)
    items = data.get("items", [])

    if not material_type_id:
        _empty_material_type()

    supplier_obj = _handle_supplier_obj(supplier_name)

    # create inbound record
    inbound_record = InboundRecord(
        inbound_record_id=data.get("inboundRecordId", None),
        inbound_datetime=timestamp,
        inbound_type=0,
        inbound_rid=inbound_rid,
        inbound_batch_id=next_group_id,
        supplier_id=supplier_obj.supplier_id,
        warehouse_id=warehouse_id,
        remark=remark,
        pay_method=data.get("payMethod", None),
    )
    db.session.add(inbound_record)
    db.session.flush()

    total_price = 0
    for item in items:
        item: dict
        material_category = item.get("materialCategory", 0)
        storage_id = item.get("materialStorageId", None)
        material_model = item.get("inboundModel")
        material_specification = item.get("inboundSpecification")
        material_color = item.get("materialColor")

        # 用户手填材料或者更换仓库
        if not storage_id or (storage_id and is_warehouse_changed):
            logger.debug(storage_id)
            logger.debug(is_warehouse_changed)
            storage_id, storage = _find_storage_in_db(
                item, material_type_id, supplier_obj.supplier_id, batch_info_type_id
            )
        # 用户选择了材料，直接使用material storage id
        else:
            if item["materialCategory"] == 0:
                storage = (
                    db.session.query(MaterialStorage)
                    .filter(
                        MaterialStorage.material_storage_id == storage_id,
                    )
                    .first()
                )
                # 修改实际入库的型号和规格
                storage.inbound_model = material_model
                storage.inbound_specification = material_specification
                storage.material_storage_color = material_color
                material_id = storage.actual_inbound_material_id
            elif item["materialCategory"] == 1:
                storage = (
                    db.session.query(SizeMaterialStorage)
                    .filter(
                        SizeMaterialStorage.size_material_storage_id == storage_id,
                    )
                    .first()
                )
                material_id = storage.material_id
                storage.size_material_model = material_model
                storage.size_material_specification = material_specification
                storage.size_material_color = material_color
            else:
                error_message = json.dumps({"message": "材料类型错误"})
                abort(Response(error_message, 400))

            spu_material_id = _create_spu_record(material_id, material_model, material_specification, material_color)
            storage.spu_material_id = spu_material_id

        # set inbound quantity
        inbound_quantity = Decimal(item["inboundQuantity"])
        record_detail = InboundRecordDetail(
            inbound_record_id=inbound_record.inbound_record_id,
            inbound_amount=inbound_quantity,
            remark=item.get("remark", None),
            order_id=storage.order_id,
            spu_material_id=storage.spu_material_id,
        )

        # set cost
        unit_price = Decimal(item.get("unitPrice", 0))
        storage.unit_price = unit_price
        record_detail.unit_price = unit_price

        item_total_price = Decimal(item.get("itemTotalPrice", 0))
        total_price += item_total_price
        record_detail.item_total_price = item_total_price

        # 更新库存数量
        if material_category == 0:
            inbound_record.is_sized_material = 0
            record_detail.material_storage_id = storage_id
            storage.actual_inbound_amount += inbound_quantity
            storage.current_amount += inbound_quantity
        elif material_category == 1:
            inbound_record.is_sized_material = 1
            record_detail.size_material_storage_id = storage_id

            storage.total_actual_inbound_amount += inbound_quantity
            storage.total_current_amount += inbound_quantity

            for i, shoe_size in enumerate(SHOESIZERANGE):
                if f"amount{i}" not in item:
                    break
                column_name = f"size_{shoe_size}_actual_inbound_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value + int(item[f"amount{i}"])
                setattr(storage, column_name, new_value)

                column_name = f"size_{shoe_size}_current_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value + int(item[f"amount{i}"])
                setattr(storage, column_name, new_value)

                column_name = f"size_{shoe_size}_inbound_amount"
                setattr(record_detail, column_name, int(item[f"amount{i}"]))
        db.session.add(record_detail)
    inbound_record.total_price = total_price
    return inbound_record.inbound_rid, inbound_record.inbound_datetime


def _handle_production_remain_inbound(data, next_group_id):
    timestamp = data.get("currentDateTime", datetime.now())
    remark = data.get("remark", None)
    items = data.get("items", [])
    formatted_timestamp = (
        timestamp.replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
    )
    inbound_rid = "IR" + formatted_timestamp + "T1"
    warehouse_id = data.get("warehouseId", None)
    material_type_id = data.get("materialTypeId", None)
    if not material_type_id:
        _empty_material_type()

        # create inbound record
    inbound_record = InboundRecord(
        inbound_datetime=formatted_timestamp,
        inbound_type=1,
        inbound_rid=inbound_rid,
        inbound_batch_id=next_group_id,
        remark=remark,
        warehouse_id=warehouse_id,
    )
    db.session.add(inbound_record)
    db.session.flush()

    for item in items:
        item: dict
        material_category = item.get("materialCategory", 0)
        storage_id = item.get("materialStorageId", None)
        # 生产剩余入库，必定有storage id，不能用户手填材料
        if not storage_id:
            _no_storage_id_error()
        # 用户选择了材料
        else:
            if item["materialCategory"] == 0:
                storage = MaterialStorage.query.get(storage_id)
            elif item["materialCategory"] == 1:
                storage = SizeMaterialStorage.query.get(storage_id)

        # set inbound quantity
        inbound_quantity = Decimal(item["inboundQuantity"])
        record_detail = InboundRecordDetail(
            inbound_record_id=inbound_record.inbound_record_id,
            inbound_amount=inbound_quantity,
            remark=item.get("remark", None),
            order_id=storage.order_id,
            spu_material_id=storage.spu_material_id,
        )

        if material_category == 0:
            inbound_record.is_sized_material = 0
            record_detail.material_storage_id = storage_id
            storage.current_amount += inbound_quantity
        elif material_category == 1:
            inbound_record.is_sized_material = 1
            record_detail.size_material_storage_id = storage_id

            storage.total_current_amount += inbound_quantity

            for i, shoe_size in enumerate(SHOESIZERANGE):
                if f"amount{i}" not in item:
                    break

                column_name = f"size_{shoe_size}_current_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value + int(item[f"amount{i}"])
                setattr(storage, column_name, new_value)

                column_name = f"size_{shoe_size}_inbound_amount"
                setattr(record_detail, column_name, int(item[f"amount{i}"]))
        db.session.add(record_detail)
    return inbound_record.inbound_rid


def create_inbound_record(data, is_warehouse_changed=False):

    # 2) you’ll need supplier_id in data for purchase flow
    if data.get("inboundType", 0) == 0:
        supplier = data.get("supplierName")
        if not supplier:
            abort(Response(json.dumps({"message": "供应商名称不能为空"}), 400))
        # find or create supplier
        sup = db.session.query(Supplier).filter_by(supplier_name=supplier).first()
        if not sup:
            sup = Supplier(supplier_name=supplier)
            db.session.add(sup)
            db.session.flush()
        data["supplier_id"] = sup.supplier_id

    # 3) sanitize items (strip spaces & validate materialName…)
    # 检查数据
    items = data.get("items", [])
    for item in items:
        item: dict
        order_rid = item.get("orderRId", None)
        material_name = item.get("materialName", None)
        if not material_name:
            error_message = json.dumps({"message": "材料名称不能为空"})
            abort(Response(error_message, 400))

        inbound_material = item.get("inboundModel") if item.get("inboundModel") else ""
        inbound_specification = (
            item.get("inboundSpecification") if item.get("inboundSpecification") else ""
        )
        material_color = item.get("materialColor") if item.get("materialColor") else ""
        actual_inbound_unit = item.get("actualInboundUnit") if item.get("actualInboundUnit") else ""

        # sanitize the material information
        material_name = material_name.replace(" ", "")
        inbound_material = inbound_material.replace(" ", "")
        inbound_specification = inbound_specification.replace(" ", "")
        material_color = material_color.replace(" ", "")
        actual_inbound_unit = actual_inbound_unit.replace(" ", "")

        item["materialName"] = material_name
        item["inboundModel"] = inbound_material
        item["inboundSpecification"] = inbound_specification
        item["materialColor"] = material_color
        item["actualInboundUnit"] = actual_inbound_unit

    # 5) dispatch
    itype = data.get("inboundType", 0)
    if itype == 0:
        rid, ts = _handle_purchase_inbound(data, 0, is_warehouse_changed)
    elif itype == 1:
        rid, ts = _handle_production_remain_inbound(data, 0, is_warehouse_changed)
    else:
        abort(Response(json.dumps({"message": "invalid inbound type"}), 400))

    return rid, ts, 0


@material_storage_bp.route("/warehouse/inboundmaterial", methods=["POST"])
def inbound_material():
    data = request.get_json()
    data["currentDateTime"] = format_datetime(datetime.now())
    logger.debug(f"data: {data}")
    rid, ts, _ = create_inbound_record(data)
    db.session.commit()
    return jsonify({
        "message": "success",
        "inboundRId": rid,
        "inboundTime": ts
    })


def _handle_production_outbound(data, next_group_id):
    timestamp = data.get("currentDateTime", datetime.now())
    department = data.get("department", None)
    remark = data.get("remark", None)
    picker = data.get("picker", None)
    items = data.get("items", [])
    formatted_timestamp = (
        timestamp.replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
    )
    outbound_rid = "OR" + formatted_timestamp + "T0"
    # create outbound record
    outbound_record = OutboundRecord(
        outbound_datetime=formatted_timestamp,
        outbound_type=0,
        outbound_rid=outbound_rid,
        outbound_batch_id=next_group_id,
        outbound_department=department,
        picker=picker,
        remark=remark,
    )
    db.session.add(outbound_record)
    db.session.flush()

    for item in items:
        item: dict
        material_category = item.get("materialCategory", 0)
        storage_id = item.get("materialStorageId", None)
        # 用户必须选材料id
        if not storage_id:
            abort(Response(json.dumps({"message": "没有选择材料库存"}), 400))

        # set outbound quantity
        outbound_quantity = Decimal(item["outboundQuantity"])
        if outbound_quantity == 0:
            error_message = json.dumps({"message": "出库数量不能为0"})
            abort(Response(error_message, 400))

        # 用户选择了材料
        if item["materialCategory"] == 0:
            storage = db.session.query(MaterialStorage).filter(MaterialStorage.material_storage_id == storage_id).first()
        elif item["materialCategory"] == 1:
            storage = db.session.query(SizeMaterialStorage).filter(SizeMaterialStorage.size_material_storage_id == storage_id).first()

        selected_order_rid = item.get("selectedOrderRId", None)
        order_id, order_shoe_id = None, None
        if selected_order_rid:
            order, order_shoe = _find_order_shoe(selected_order_rid)
            order_id = order.order_id
            order_shoe_id = order_shoe.order_shoe_id
        record_detail = OutboundRecordDetail(
            outbound_record_id=outbound_record.outbound_record_id,
            outbound_amount=outbound_quantity,
            remark=item.get("remark", None),
            order_id=order_id,
            order_shoe_id=order_shoe_id,
            unit_price=storage.average_price,
            item_total_price=outbound_quantity * storage.average_price,
            spu_material_id=storage.spu_material_id,
        )

        if material_category == 0:
            outbound_record.is_sized_material = 0
            record_detail.material_storage_id = storage_id
            storage.current_amount -= outbound_quantity

            if storage.current_amount < 0:
                error_message = json.dumps({"message": "出库数量大于库存数量"})
                abort(Response(error_message, 400))
        elif material_category == 1:
            outbound_record.is_sized_material = 1
            record_detail.size_material_storage_id = storage_id

            for i, shoe_size in enumerate(SHOESIZERANGE):
                if f"amount{i}" not in item:
                    break

                column_name = f"size_{shoe_size}_current_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value - int(item[f"amount{i}"])
                if new_value < 0:
                    error_message = json.dumps({"message": "出库数量大于库存数量"})
                    abort(Response(error_message, 400))
                setattr(storage, column_name, new_value)
                storage.total_current_amount -= int(item[f"amount{i}"])

                column_name = f"size_{shoe_size}_outbound_amount"
                setattr(record_detail, column_name, int(item[f"amount{i}"]))
        db.session.add(record_detail)
    return outbound_record.outbound_rid


def _handle_waste_outbound(data, next_group_id):
    pass


def _handle_outsource_outbound(data, next_group_id):
    pass


def _handle_composite_outbound(data, next_group_id):
    timestamp = data.get("currentDateTime", datetime.now())
    supplier_name = data.get("supplierName", None)
    remark = data.get("remark", None)
    picker = data.get("picker", None)
    items = data.get("items", [])
    formatted_timestamp = (
        timestamp.replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
    )
    outbound_rid = "OR" + formatted_timestamp + "T3"

    supplier_obj = _handle_supplier_obj(supplier_name)
    # create outbound record
    outbound_record = OutboundRecord(
        outbound_datetime=formatted_timestamp,
        outbound_type=3,
        outbound_rid=outbound_rid,
        outbound_batch_id=next_group_id,
        composite_supplier_id=supplier_obj.supplier_id,
        picker=picker,
        remark=remark,
    )
    db.session.add(outbound_record)
    db.session.flush()

    for item in items:
        item: dict
        material_category = item.get("materialCategory", 0)
        storage_id = item.get("materialStorageId", None)
        # 用户必须选材料id
        if not storage_id:
            abort(Response(json.dumps({"message": "没有选择材料库存"}), 400))

        # set outbound quantity
        outbound_quantity = Decimal(item["outboundQuantity"])
        if outbound_quantity == 0:
            error_message = json.dumps({"message": "出库数量不能为0"})
            abort(Response(error_message, 400))

        # 用户选择了材料
        if item["materialCategory"] == 0:
            storage = MaterialStorage.query.get(storage_id)
        elif item["materialCategory"] == 1:
            storage = SizeMaterialStorage.query.get(storage_id)

        if outbound_quantity > storage.current_amount:
            error_message = json.dumps({"message": "出库数量大于库存数量"})
            abort(Response(error_message, 400))

        selected_order_rid = item.get("selectedOrderRId", None)
        order_id, order_shoe_id = None
        if selected_order_rid:
            order, order_shoe = _find_order_shoe(selected_order_rid)
            order_id = order.order_id
            order_shoe_id = order_shoe.order_shoe_id
        record_detail = OutboundRecordDetail(
            outbound_record_id=outbound_record.outbound_record_id,
            outbound_amount=outbound_quantity,
            remark=item.get("remark", None),
            order_id=order_id,
            order_shoe_id=order_shoe_id,
            spu_material_id=storage.spu_material_id,
        )

        if material_category == 0:
            outbound_record.is_sized_material = 0
            record_detail.material_storage_id = storage_id
            storage.current_amount -= outbound_quantity
        elif material_category == 1:
            outbound_record.is_sized_material = 1
            record_detail.size_material_storage_id = storage_id

            for i, shoe_size in enumerate(SHOESIZERANGE):
                if f"amount{i}" not in item:
                    break

                column_name = f"size_{shoe_size}_current_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value - int(item[f"amount{i}"])
                setattr(storage, column_name, new_value)
                storage.total_current_amount -= int(item[f"amount{i}"])

                column_name = f"size_{shoe_size}_outbound_amount"
                setattr(record_detail, column_name, int(item[f"amount{i}"]))
        db.session.add(record_detail)
    return outbound_record.outbound_rid


# check whether materials for order_shoe has inbounded
@material_storage_bp.route("/warehouse/outboundmaterial", methods=["POST"])
def outbound_material():
    data = request.get_json()
    # Determine the next available group_id
    next_group_id = (
        db.session.query(
            func.coalesce(func.max(OutboundRecord.outbound_batch_id), 0)
        ).scalar()
        + 1
    )
    outbound_type = data.get("outboundType", 0)
    # 工厂使用
    if outbound_type == 0:
        outbound_rid = _handle_production_outbound(data, next_group_id)
    # 废料处理
    elif outbound_type == 1:
        outbound_rid = _handle_waste_outbound(data, next_group_id)
    # 外包出库
    elif outbound_type == 2:
        outbound_rid = _handle_outsource_outbound(data, next_group_id)
    # 复合出库
    elif outbound_type == 3:
        outbound_rid = _handle_composite_outbound(data, next_group_id)
    else:
        return jsonify({"message": "invalid outbound type"}), 400

    db.session.commit()
    return jsonify({"message": "success", "outboundRId": outbound_rid})


# check whether materials for order_shoe has inbounded
@material_storage_bp.route(
    "/warehouse/warehousemanager/notifyrequiredmaterialarrival", methods=["GET"]
)
def notify_required_material_arrival():
    order_shoe_id = request.args.get("orderShoeId")
    production_info = OrderShoeProductionInfo.query.filter(
        OrderShoeProductionInfo.order_shoe_id == order_shoe_id
    ).first()
    is_material_arrived = production_info.is_material_arrived
    if is_material_arrived:
        return jsonify({"message": "no"})

    query1 = db.session.query(MaterialStorage.material_storage_status).filter(
        MaterialStorage.order_shoe_id == order_shoe_id
    )
    query2 = db.session.query(SizeMaterialStorage.material_storage_status).filter(
        SizeMaterialStorage.order_shoe_id == order_shoe_id
    )
    response = query1.union(query2).all()
    notify = True
    for row in response:
        if row.material_storage_status == 0:
            notify = False

    if notify:
        # set is_material_arrived to true
        production_info.is_material_arrived = True
        db.session.commit()
        return jsonify({"message": "yes"})
    return jsonify({"message": "no"})


@material_storage_bp.route("/warehouse/getmaterialinboundrecords", methods=["GET"])
def get_material_inbound_records():
    start_date_search = request.args.get("startDate")
    end_date_search = request.args.get("endDate")
    page = int(request.args.get("page", 1))
    number = int(request.args.get("pageSize", 10))
    inbound_rid = request.args.get("inboundRId")
    supplier_name = request.args.get("supplierName")
    warehouse_name = request.args.get("warehouseName")
    status = request.args.get("status", type=int)

    query1 = (
        db.session.query(InboundRecord, MaterialWarehouse, Supplier)
        .join(
            MaterialWarehouse,
            MaterialWarehouse.material_warehouse_id == InboundRecord.warehouse_id,
        )
        .outerjoin(
            Supplier,
            Supplier.supplier_id == InboundRecord.supplier_id,
        )
    )
    if start_date_search:
        query1 = query1.filter(InboundRecord.inbound_datetime >= start_date_search)
    if end_date_search:
        query1 = query1.filter(InboundRecord.inbound_datetime <= end_date_search)
    if inbound_rid:
        query1 = query1.filter(InboundRecord.inbound_rid.ilike(f"%{inbound_rid}%"))
    if supplier_name:
        query1 = query1.filter(Supplier.supplier_name.ilike(f"%{supplier_name}%"))
    if status in [0, 1, 2]:
        query1 = query1.filter(InboundRecord.approval_status == status)
    if warehouse_name:
        query1 = query1.filter(
            MaterialWarehouse.material_warehouse_name.ilike(f"%{warehouse_name}%")
        )

    query1 = query1.order_by(desc(InboundRecord.inbound_datetime))
    count_result = query1.distinct().count()
    response = query1.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        inbound_record, warehouse, supplier = row
        obj = {
            "timestamp": format_datetime(inbound_record.inbound_datetime),
            "inboundRecordId": inbound_record.inbound_record_id,
            "inboundType": inbound_record.inbound_type,
            "inboundBatchId": inbound_record.inbound_batch_id,
            "inboundRId": inbound_record.inbound_rid,
            "isSizedMaterial": inbound_record.is_sized_material,
            "supplierId": inbound_record.supplier_id,
            "supplierName": supplier.supplier_name if supplier else None,
            "payMethod": inbound_record.pay_method,
            "remark": inbound_record.remark,
            "approvalStatus": inbound_record.approval_status,
            "rejectReason": inbound_record.reject_reason,
            "totalPrice": inbound_record.total_price,
            "warehouseName": warehouse.material_warehouse_name,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route("/warehouse/getinboundrecordbybatchid", methods=["GET"])
def get_inbound_record_by_batch_id():
    inbound_record_id = request.args.get("inboundRecordId")
    is_sized_material = request.args.get("isSizedMaterial", type=int)
    if is_sized_material == 0:
        inbound_response = (
            db.session.query(
                InboundRecordDetail,
                MaterialStorage.material_storage_id,
                MaterialStorage.material_model,
                MaterialStorage.material_specification,
                MaterialStorage.inbound_model,
                MaterialStorage.inbound_specification,
                MaterialStorage.material_storage_color,
                MaterialStorage.actual_inbound_unit,
                literal(None).label("shoe_size_columns"),
                Material,
                Supplier,
                Order,
                Shoe
            )
            .join(
                InboundRecord,
                InboundRecord.inbound_record_id
                == InboundRecordDetail.inbound_record_id,
            )
            .join(
                MaterialStorage,
                InboundRecordDetail.material_storage_id
                == MaterialStorage.material_storage_id,
            )
            .join(
                Material,
                Material.material_id == MaterialStorage.actual_inbound_material_id,
            )
            .outerjoin(Supplier, Supplier.supplier_id == InboundRecord.supplier_id)
            .outerjoin(
                Order,
                Order.order_id == MaterialStorage.order_id,
            )
            .outerjoin(
                OrderShoe,
                OrderShoe.order_id == Order.order_id,
            )
            .outerjoin(
                Shoe,
                Shoe.shoe_id == OrderShoe.shoe_id,
            )
            .filter(
                InboundRecord.inbound_record_id == inbound_record_id,
            )
            .all()
        )
    else:
        inbound_response = (
            db.session.query(
                InboundRecordDetail,
                SizeMaterialStorage.size_material_storage_id,
                SizeMaterialStorage.size_material_model,
                SizeMaterialStorage.size_material_specification,
                SizeMaterialStorage.size_material_model.label("inbound_model"),
                SizeMaterialStorage.size_material_specification.label("inbound_specification"),
                SizeMaterialStorage.size_material_color,
                Material.material_unit,
                SizeMaterialStorage.shoe_size_columns,
                Material,
                Supplier,
                Order,
                Shoe
            )
            .join(
                InboundRecord,
                InboundRecord.inbound_record_id
                == InboundRecordDetail.inbound_record_id,
            )
            .join(
                SizeMaterialStorage,
                InboundRecordDetail.size_material_storage_id
                == SizeMaterialStorage.size_material_storage_id,
            )
            .join(Material, Material.material_id == SizeMaterialStorage.material_id)
            .outerjoin(Supplier, Supplier.supplier_id == InboundRecord.supplier_id)
            .outerjoin(
                Order,
                Order.order_id == SizeMaterialStorage.order_id,
            )
            .outerjoin(
                OrderShoe,
                OrderShoe.order_id == Order.order_id,
            )
            .outerjoin(
                Shoe,
                Shoe.shoe_id == OrderShoe.shoe_id,
            )
            .filter(
                InboundRecord.inbound_record_id == inbound_record_id,
            )
            .all()
        )

    if not inbound_response:
        return jsonify({"message": "record not found"}), 404
    result = []
    for row in inbound_response:
        (
            record_detail,
            material_storage_id,
            material_model,
            material_specification,
            inbound_model,
            inbound_specification,
            material_storage_color,
            material_unit,
            shoe_size_columns,
            material,
            supplier,
            order,
            shoe
        ) = row
        unit_price = (
            round(record_detail.unit_price, 3) if record_detail.unit_price else 0.00
        )
        composite_unit_cost = (
            round(record_detail.composite_unit_cost, 3)
            if record_detail.composite_unit_cost
            else 0.00
        )
        inbound_quantity = (
            round(record_detail.inbound_amount, 2)
            if record_detail.inbound_amount
            else 0.00
        )
        obj = {
            "inboundQuantity": inbound_quantity,
            "unitPrice": unit_price,
            "itemTotalPrice": record_detail.item_total_price,
            "compositeUnitCost": composite_unit_cost,
            "inboundRecordDetailId": record_detail.id,
            "remark": record_detail.remark,
            "materialName": material.material_name,
            "materialModel": material_model,
            "materialSpecification": material_specification,
            "inboundModel": inbound_model,
            "inboundSpecification": inbound_specification,
            "materialColor": material_storage_color,
            "materialUnit": material_unit,
            "materialTypeId": material.material_type_id,
            "materialStorageId": material_storage_id,
            "actualInboundUnit": material_unit,
            "orderRId": order.order_rid if order else None,
            "supplierName": supplier.supplier_name if supplier else None,
            "shoeSizeColumns": shoe_size_columns,
            "shoeRId": shoe.shoe_rid if shoe else None,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_inbound_amount"
            obj[f"amount{i}"] = (
                round(getattr(record_detail, column_name, None))
                if getattr(record_detail, column_name, None)
                else 0
            )
        result.append(obj)
    return result


@material_storage_bp.route("/warehouse/getmaterialoutboundrecords", methods=["GET"])
def get_material_outbound_records():
    start_date_search = request.args.get("startDate")
    end_date_search = request.args.get("endDate")
    page = int(request.args.get("page", 1))
    number = int(request.args.get("pageSize", 10))
    outbound_rid = request.args.get("outboundRId")

    query = (
        db.session.query(OutboundRecord, OutsourceFactory, Department, Supplier)
        .outerjoin(
            OutsourceInfo,
            OutboundRecord.outsource_info_id == OutsourceInfo.outsource_info_id,
        )
        .outerjoin(
            OutsourceFactory,
            OutsourceInfo.factory_id == OutsourceFactory.factory_id,
        )
        .outerjoin(
            Department,
            OutboundRecord.outbound_department == Department.department_id,
        )
        .outerjoin(
            Supplier,
            OutboundRecord.composite_supplier_id == Supplier.supplier_id,
        )
    )

    if start_date_search and end_date_search:
        try:
            start_date_search = datetime.strptime(start_date_search, "%Y-%m-%d")
            end_date_search = datetime.strptime(end_date_search, "%Y-%m-%d")
        except ValueError:
            return jsonify({"message": "invalid date range"}), 400
        query = query.filter(OutboundRecord.outbound_datetime >= start_date_search)
        query = query.filter(OutboundRecord.outbound_datetime <= end_date_search)
    if outbound_rid:
        query = query.filter(OutboundRecord.outbound_rid.ilike(f"%{outbound_rid}%"))

    query = query.order_by(desc(OutboundRecord.outbound_datetime))
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            outbound_record,
            outsource_factory,
            department,
            supplier,
        ) = row
        obj = {
            "outboundRecordId": outbound_record.outbound_record_id,
            "outboundBatchId": outbound_record.outbound_batch_id,
            "outboundRId": outbound_record.outbound_rid,
            "timestamp": format_datetime(outbound_record.outbound_datetime),
            "outboundType": outbound_record.outbound_type,
            "departmentName": department.department_name if department else None,
            "picker": outbound_record.picker,
            "compositeSupplierName": supplier.supplier_name if supplier else None,
            "outsourceFactoryName": (
                outsource_factory.factory_name if outsource_factory else None
            ),
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route("/warehouse/getoutboundrecordbybatchid", methods=["GET"])
def get_outbound_record_by_batch_id():
    outbound_batch_id = request.args.get("outboundBatchId")
    columns = [getattr(OutboundRecordDetail, f"size_{i+34}_outbound_amount") for i in range(len(SHOESIZERANGE))]
    query1 = (
        db.session.query(
            OutboundRecordDetail.id,
            OutboundRecordDetail.outbound_amount,
            OutboundRecordDetail.unit_price,
            OutboundRecordDetail.item_total_price,
            OutboundRecordDetail.remark,
            MaterialStorage.material_storage_id,
            MaterialStorage.inbound_model,
            MaterialStorage.inbound_specification,
            MaterialStorage.material_storage_color,
            MaterialStorage.actual_inbound_unit,
            cast(literal("{}"), JSON).label("shoe_size_columns"),
            Material.material_name,
            Order,
            Shoe,
            *columns
        )
        .join(
            OutboundRecord,
            OutboundRecord.outbound_record_id
            == OutboundRecordDetail.outbound_record_id,
        )
        .join(
            MaterialStorage,
            OutboundRecordDetail.material_storage_id
            == MaterialStorage.material_storage_id,
        )
        .join(
            Material,
            Material.material_id == MaterialStorage.actual_inbound_material_id,
        )
        .outerjoin(
            OrderShoe,
            OrderShoe.order_shoe_id == OutboundRecordDetail.order_shoe_id,
        )
        .outerjoin(
            Order,
            Order.order_id == OrderShoe.order_id,
        )
        .outerjoin(
            Shoe,
            Shoe.shoe_id == OrderShoe.shoe_id,
        )
        .filter(
            OutboundRecord.outbound_batch_id == outbound_batch_id,
        )
    )
    query2 = (
        db.session.query(
            OutboundRecordDetail.id,
            OutboundRecordDetail.outbound_amount,
            OutboundRecordDetail.unit_price,
            OutboundRecordDetail.item_total_price,
            OutboundRecordDetail.remark,
            SizeMaterialStorage.size_material_storage_id,
            SizeMaterialStorage.size_material_model,
            SizeMaterialStorage.size_material_specification,
            SizeMaterialStorage.size_material_color,
            Material.material_unit,
            SizeMaterialStorage.shoe_size_columns,
            Material.material_name,
            Order,
            Shoe,
            *columns
        )
        .join(
            OutboundRecord,
            OutboundRecord.outbound_record_id
            == OutboundRecordDetail.outbound_record_id,
        )
        .join(
            SizeMaterialStorage,
            OutboundRecordDetail.size_material_storage_id
            == SizeMaterialStorage.size_material_storage_id,
        )
        .join(Material, Material.material_id == SizeMaterialStorage.material_id)
        .outerjoin(
            OrderShoe,
            OrderShoe.order_shoe_id == OutboundRecordDetail.order_shoe_id,
        )
        .outerjoin(
            Order,
            Order.order_id == OrderShoe.order_id,
        )
        .outerjoin(
            Shoe,
            Shoe.shoe_id == OrderShoe.shoe_id,
        )
        .filter(
            OutboundRecord.outbound_batch_id == outbound_batch_id,
        )
    )
    union_query = query1.union(query2)
    response = union_query.all()
    result = []
    for row in response:
        (
            record_item_id,
            record_item_outbound_amount,
            unit_price,
            item_total_price,
            record_item_remark,
            material_storage_id,
            material_model,
            material_specification,
            material_storage_color,
            actual_inbound_unit,
            shoe_size_columns,
            material_name,
            order,
            shoe,
            *columns
        ) = row
        obj = {
            "outboundQuantity": record_item_outbound_amount,
            "unitPrice": unit_price,
            "itemTotalPrice": item_total_price,
            "outboundRecordDetailId": record_item_id,
            "remark": record_item_remark,
            "materialName": material_name,
            "materialModel": material_model,
            "materialSpecification": material_specification,
            "colorName": material_storage_color,
            "materialStorageId": material_storage_id,
            "actualInboundUnit": actual_inbound_unit,
            "shoeSizeColumns": shoe_size_columns,
            "orderRId": order.order_rid if order else None,
            "shoeRId": shoe.shoe_rid if shoe else None,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_outbound_amount"
            obj[f"amount{i}"] = (
                round(getattr(row, column_name, None))
                if getattr(row, column_name, None)
                else 0
            )
        result.append(obj)
    return result


@material_storage_bp.route("/warehouse/getinboundrecordsformaterial", methods=["GET"])
def get_inbound_records_for_material():
    storage_id = request.args.get("storageId")
    response = (
        db.session.query(InboundRecord, InboundRecordDetail)
        .join(
            InboundRecordDetail,
            InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id,
        )
        .filter(InboundRecordDetail.material_storage_id == storage_id)
        .order_by(desc(InboundRecord.inbound_datetime))
        .all()
    )
    result = []
    for row in response:
        record, item = row
        if record.inbound_type == 1:
            inbound_purpose = "生产剩余"
        elif record.inbound_type == 2:
            inbound_purpose = "复合入库"
        else:
            inbound_purpose = "采购入库"
        obj = {
            "inboundRId": record.inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "inboundType": inbound_purpose,
            "inboundAmount": item.inbound_amount,
            "unitPrice": item.unit_price,
            "itemTotalPrice": item.item_total_price,
            "remark": item.remark,
        }
        result.append(obj)
    return result


@material_storage_bp.route(
    "/warehouse/getinboundrecordsforsizematerial", methods=["GET"]
)
def get_inbound_records_for_size_material():
    storage_id = request.args.get("storageId")
    response = (
        db.session.query(InboundRecord, InboundRecordDetail)
        .join(
            InboundRecordDetail,
            InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id,
        )
        .filter(InboundRecordDetail.size_material_storage_id == storage_id)
        .order_by(desc(InboundRecord.inbound_datetime))
        .all()
    )
    result = []
    for row in response:
        record, item = row
        if record.inbound_type == 1:
            inbound_purpose = "生产剩余"
        elif record.inbound_type == 2:
            inbound_purpose = "复合入库"
        else:
            inbound_purpose = "采购入库"
        obj = {
            "inboundRId": record.inbound_rid,
            "timestamp": format_datetime(record.inbound_datetime),
            "inboundType": inbound_purpose,
            "inboundAmount": item.inbound_amount,
            "unitPrice": item.unit_price,
            "itemTotalPrice": item.item_total_price,
            "remark": item.remark,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_inbound_amount"
            obj[f"amount{i}"] = getattr(item, column_name)
        result.append(obj)
    return result


@material_storage_bp.route("/warehouse/getoutboundrecordsformaterial", methods=["GET"])
def get_outbound_records_for_material():
    storage_id = request.args.get("storageId")
    response = (
        db.session.query(OutboundRecord, OutboundRecordDetail, Supplier, Department)
        .join(
            OutboundRecordDetail,
            OutboundRecord.outbound_record_id
            == OutboundRecordDetail.outbound_record_id,
        )
        .outerjoin(
            Supplier, Supplier.supplier_id == OutboundRecord.composite_supplier_id
        )
        .outerjoin(
            Department, Department.department_id == OutboundRecord.outbound_department
        )
        .filter(OutboundRecordDetail.material_storage_id == storage_id)
        .order_by(desc(OutboundRecord.outbound_datetime))
        .all()
    )
    result = []
    for row in response:
        outbound_record, item, supplier, department = row
        outbound_destination = ""
        if outbound_record.outbound_type == 1:
            outbound_purpose = "废料处理"
        # elif row.outbound_type == 2:
        #     outbound_purpose = "外包发货"
        #     outbound_destination =
        # outbound_address = row.outbound_address
        elif outbound_record.outbound_type == 3:
            outbound_purpose = "外发复合"
            outbound_destination = supplier.supplier_name if supplier else None
        else:
            outbound_purpose = "生产使用"
            outbound_destination = department.department_name if department else None
        obj = {
            "outboundRId": outbound_record.outbound_rid,
            "timestamp": format_datetime(outbound_record.outbound_datetime),
            "outboundType": outbound_purpose,
            "unitPrice": item.unit_price,
            "outboundAmount": item.outbound_amount,
            "itemTotalPrice": item.item_total_price,
            "remark": item.remark,
            "outboundDestination": outbound_destination,
            "picker": outbound_record.picker,
        }
        result.append(obj)
    return result


@material_storage_bp.route(
    "/warehouse/getoutboundrecordsforsizematerial", methods=["GET"]
)
def get_outbound_records_for_size_material():
    storage_id = request.args.get("storageId")
    response = (
        db.session.query(OutboundRecord, OutboundRecordDetail, Supplier, Department)
        .join(
            OutboundRecordDetail,
            OutboundRecord.outbound_record_id
            == OutboundRecordDetail.outbound_record_id,
        )
        .outerjoin(
            Supplier, Supplier.supplier_id == OutboundRecord.composite_supplier_id
        )
        .outerjoin(
            Department, Department.department_id == OutboundRecord.outbound_department
        )
        .filter(OutboundRecordDetail.size_material_storage_id == storage_id)
        .order_by(desc(OutboundRecord.outbound_datetime))
        .all()
    )
    result = []
    for row in response:
        record, item, supplier, department = row
        outbound_destination = ""
        if record.outbound_type == 1:
            outbound_purpose = "废料处理"
        # elif row.outbound_type == 2:
        #     outbound_purpose = "外包发货"
        #     outbound_destination = db.session.query(Outsouce
        elif record.outbound_type == 3:
            outbound_purpose = "外发复合"
            outbound_destination = department.department_name if department else None
        else:
            outbound_purpose = "生产使用"
            outbound_destination = supplier.supplier_name if supplier else None
        obj = {
            "outboundRId": record.outbound_rid,
            "timestamp": format_datetime(record.outbound_datetime),
            "outboundType": outbound_purpose,
            "outboundAmount": item.outbound_amount,
            "remark": item.remark,
            "outboundDestination": outbound_destination,
            "picker": record.picker,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_outbound_amount"
            obj[f"amount{i}"] = getattr(item, column_name)
        result.append(obj)
    return result


@material_storage_bp.route(
    "/warehouse/warehousemanager/finishinboundmaterial", methods=["PATCH"]
)
def finish_inbound_material():
    data = request.get_json()
    unique_order_shoe_ids = set()
    for row in data:
        storage = None
        if row["materialCategory"] == 0:
            storage = MaterialStorage.query.get(row["storageId"])
        elif row["materialCategory"] == 1:
            storage = SizeMaterialStorage.query.get(row["storageId"])
        else:
            return jsonify({"message": "Invalid material category"}), 400
        if not storage:
            return jsonify({"message": "order shoe storage not found"}), 400
        unique_order_shoe_ids.add((row["orderId"], storage.order_shoe_id))
        storage.material_storage_status = 1
    db.session.flush()
    # check if all materials are inbounded for order shoe
    # TODO: join purchase divide order, bom, to find bom type
    # for order_id, order_shoe_id in unique_order_shoe_ids:
    #     material_filter = (MaterialStorage.order_shoe_id == order_shoe_id) & (
    #         MaterialStorage.material_storage_status != 1
    #     )
    #     result1 = db.session.query(
    #         db.session.query(MaterialStorage).filter(material_filter).exists()
    #     ).scalar()
    #     size_material_filter = (SizeMaterialStorage.order_shoe_id == order_shoe_id) & (
    #         SizeMaterialStorage.material_storage_status != 1
    #     )
    #     result2 = db.session.query(
    #         db.session.query(SizeMaterialStorage).filter(size_material_filter).exists()
    #     ).scalar()
    #     # if all material are arrived
    #     if not result1 and not result2:
    #         production_info = (
    #             db.session.query(OrderShoeProductionInfo)
    #             .filter_by(order_shoe_id=order_shoe_id)
    #             .first()
    #         )
    #         production_info.is_material_arrived = 1
    #         processor: EventProcessor = current_app.config["event_processor"]
    #         try:
    #             for operation_id in [54, 55]:
    #                 event = Event(
    #                     staff_id=11,
    #                     handle_time=datetime.now(),
    #                     operation_id=operation_id,
    #                     event_order_id=order_id,
    #                     event_order_shoe_id=order_shoe_id,
    #                 )
    #                 processor.processEvent(event)
    #                 db.session.add(event)
    #         except Exception:
    #             return jsonify({"message": "event processor error"}), 500

    db.session.commit()
    return jsonify({"message": "success"})


@material_storage_bp.route(
    "/warehouse/warehousemanager/finishoutboundmaterial", methods=["PATCH"]
)
def finish_outbound_material():
    data = request.get_json()
    for row in data:
        storage = None
        if row["materialCategory"] == 0:
            storage = MaterialStorage.query.get(row["storageId"])
        elif row["materialCategory"] == 1:
            storage = SizeMaterialStorage.query.get(row["storageId"])
        else:
            return jsonify({"message": "Invalid material category"}), 400
        if not storage:
            return jsonify({"message": "order shoe storage not found"}), 400
        storage.material_storage_status = 2
    db.session.commit()
    return jsonify({"message": "success"})


def _handle_delete_inbound_record_detail(
    inbound_record_detail, storage_id, is_sized_material
):
    if is_sized_material == 0:
        storage = MaterialStorage.query.get(storage_id)
        storage.actual_inbound_amount -= inbound_record_detail.inbound_amount
        storage.current_amount -= inbound_record_detail.inbound_amount
    else:
        storage: SizeMaterialStorage = SizeMaterialStorage.query.get(storage_id)
        storage.total_actual_inbound_amount -= inbound_record_detail.inbound_amount
        storage.total_current_amount -= inbound_record_detail.inbound_amount
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_inbound_amount"
            size_amount = getattr(inbound_record_detail, column_name, 0)

            db_column_name = f"size_{shoe_size}_current_amount"
            final_amount = (
                getattr(storage, db_column_name) - size_amount
                if getattr(storage, db_column_name) - size_amount >= 0
                else 0
            )
            setattr(storage, db_column_name, final_amount)

            db_column_name = f"size_{shoe_size}_actual_inbound_amount"
            final_amount = (
                getattr(storage, db_column_name) - size_amount
                if getattr(storage, db_column_name) - size_amount >= 0
                else 0
            )
            setattr(storage, db_column_name, final_amount)
    db.session.delete(inbound_record_detail)


def _handle_delete_storage(storage, is_sized_material):
    total_purchase_order_id = storage.total_purchase_order_id
    if is_sized_material == 0:
        # search dependency
        detail = db.session.query(InboundRecordDetail.material_storage_id == storage.material_storage_id).first()
    else:
        detail = db.session.query(InboundRecordDetail.size_material_storage_id == storage.size_material_storage_id).first()

    if not total_purchase_order_id and not detail:
        db.session.delete(storage)

@material_storage_bp.route("/warehouse/updateinboundrecord", methods=["PUT"])
def update_inbound_record():
    data = request.get_json()
    logger.debug(f"data: {data}")
    inbound_record_id = data.get("inboundRecordId")
    is_sized_material = data.get("isSizedMaterial", 0)
    warehouse_id = data.get("warehouseId")
    logger.debug(f"warehouse_id: {warehouse_id}")

    inbound_record = (
        db.session.query(InboundRecord)
        .filter(InboundRecord.inbound_record_id == inbound_record_id)
        .first()
    )
    if not inbound_record:
        return jsonify({"message": "inbound record not found"}), 404
    
    old_warehouse_id = inbound_record.warehouse_id

    is_warehouse_changed = False
    # 换仓库，对新的入库材料要创建新的库存
    if old_warehouse_id != warehouse_id:
        is_warehouse_changed = True

    inbound_timestamp: datetime = inbound_record.inbound_datetime
    inbound_rid = inbound_record.inbound_rid
    inbound_batch_id = inbound_record.inbound_batch_id

    details = (
        db.session.query(InboundRecordDetail)
        .filter(InboundRecordDetail.inbound_record_id == inbound_record_id)
        .all()
    )
    
    for detail in details:
        if detail.material_storage_id:
            storage = db.session.query(MaterialStorage).get(detail.material_storage_id)
            storage.actual_inbound_amount -= detail.inbound_amount
            storage.current_amount -= detail.inbound_amount
        elif detail.size_material_storage_id:
            storage = db.session.query(SizeMaterialStorage).get(detail.size_material_storage_id)
            storage.total_actual_inbound_amount -= detail.inbound_amount
            storage.total_current_amount -= detail.inbound_amount
            for i in range(len(SHOESIZERANGE)):
                shoe_size = SHOESIZERANGE[i]
                column_name = f"size_{shoe_size}_inbound_amount"
                size_amount = getattr(detail, column_name, 0) if getattr(detail, column_name, 0) else 0

                db_column_name = f"size_{shoe_size}_current_amount"
                final_amount = (
                    getattr(storage, db_column_name) - size_amount
                    if getattr(storage, db_column_name) - size_amount >= 0
                    else 0
                )
                setattr(storage, db_column_name, final_amount)

                db_column_name = f"size_{shoe_size}_actual_inbound_amount"
                final_amount = (
                    getattr(storage, db_column_name) - size_amount
                    if getattr(storage, db_column_name) - size_amount >= 0
                    else 0
                )
                setattr(storage, db_column_name, final_amount)

        db.session.delete(detail)
    
    db.session.delete(inbound_record)
    db.session.flush()

    # 4) recreate, reusing inbound_timestamp and inbound_record_id
    data = request.get_json()
    data["currentDateTime"] = format_datetime(inbound_timestamp)
    data["inboundRecordId"] = inbound_record_id

    new_rid, new_ts, _ = create_inbound_record(data, is_warehouse_changed)
    db.session.commit()

    return jsonify({
        "message": "updated",
        "inboundRId": new_rid,
        "inboundTime": new_ts
    })


@material_storage_bp.route("/warehouse/deleteinboundrecord", methods=["DELETE"])
def delete_inbound_record():
    inbound_record_id = request.args.get("inboundRecordId")
    inbound_record = (
        db.session.query(InboundRecord)
        .filter(InboundRecord.inbound_record_id == inbound_record_id)
        .first()
    )
    if not inbound_record:
        return jsonify({"message": "inbound record not found"}), 404

    is_sized_material = inbound_record.is_sized_material
    if is_sized_material == 0:
        entities = (
            db.session.query(InboundRecordDetail, MaterialStorage)
            .join(
                MaterialStorage,
                InboundRecordDetail.material_storage_id
                == MaterialStorage.material_storage_id,
            )
            .filter(InboundRecordDetail.inbound_record_id == inbound_record_id)
            .all()
        )
        for row in entities:
            inbound_record_detail, storage = row
            if inbound_record.inbound_type in [0, 2]:
                storage.actual_inbound_amount -= inbound_record_detail.inbound_amount
            storage.current_amount -= inbound_record_detail.inbound_amount
            db.session.delete(inbound_record_detail)
    else:
        entities = (
            db.session.query(InboundRecordDetail, SizeMaterialStorage)
            .join(
                SizeMaterialStorage,
                SizeMaterialStorage.size_material_storage_id
                == InboundRecordDetail.size_material_storage_id,
            )
            .filter(
                InboundRecordDetail.inbound_record_id == inbound_record_id,
            )
            .all()
        )
        for row in entities:
            inbound_record_detail, storage = row
            storage: SizeMaterialStorage
            if inbound_record.inbound_type in [0, 2]:
                storage.total_actual_inbound_amount -= (
                    inbound_record_detail.inbound_amount
                )
            storage.total_current_amount -= inbound_record_detail.inbound_amount
            for i in range(len(SHOESIZERANGE)):
                shoe_size = SHOESIZERANGE[i]
                column_name = f"size_{shoe_size}_current_amount"
                current_value = getattr(storage, column_name)

                record_detail_column_name = f"size_{shoe_size}_inbound_amount"
                inbound_value = getattr(
                    inbound_record_detail, record_detail_column_name
                )
                if inbound_value is None:
                    continue
                new_value = current_value - inbound_value
                setattr(storage, column_name, new_value)

            if inbound_record.inbound_type in [0, 2]:
                for i in range(len(SHOESIZERANGE)):
                    shoe_size = SHOESIZERANGE[i]
                    column_name = f"size_{shoe_size}_actual_inbound_amount"
                    current_value = getattr(storage, column_name)

                    record_detail_column_name = f"size_{shoe_size}_inbound_amount"
                    inbound_value = getattr(
                        inbound_record_detail, record_detail_column_name
                    )
                    if inbound_value is None:
                        continue
                    new_value = current_value - inbound_value
                    setattr(storage, column_name, new_value)
            db.session.delete(inbound_record_detail)
    db.session.delete(inbound_record)
    db.session.commit()
    return jsonify({"message": "success"})


@material_storage_bp.route("/warehouse/getinboundrecordbyrid", methods=["GET"])
def get_inbound_record_by_rid():
    inbound_rid = request.args.get("inboundRId")
    inbound_record = (
        db.session.query(InboundRecord)
        .filter(InboundRecord.inbound_rid == inbound_rid)
        .first()
    )
    if not inbound_record:
        return jsonify({"message": "inbound record not found"}), 404

    record_items = (
        db.session.query(InboundRecordDetail)
        .filter(
            InboundRecordDetail.inbound_record_id == inbound_record.inbound_record_id
        )
        .all()
    )
    result = {
        "metadata": {
            "inboundRId": inbound_record.inbound_rid,
            "currentDateTime": format_datetime(inbound_record.inbound_datetime),
            "inboundType": inbound_record.inbound_type,
            "remark": inbound_record.remark,
            "payMethod": inbound_record.pay_method,
            "supplierName": inbound_record.supplier_name,
        },
        "items": [],
    }
    TABLE_ATTRNAMES = InboundRecordDetail.__table__.columns.keys()
    for item in record_items:
        for db_attr in TABLE_ATTRNAMES:
            result["items"][to_camel(db_attr)] = getattr(item, db_attr, None)

    return result

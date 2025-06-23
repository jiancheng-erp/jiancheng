from datetime import datetime, date
from decimal import Decimal

from api_utility import format_date, format_datetime, to_camel
from app_config import db
from shared_apis.batch_info_type import get_order_batch_type_helper
from constants import *
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request, abort, Response
from models import *
from sqlalchemy import desc, func, text, literal, cast, JSON, or_, and_
import json
from script.refresh_spu_rid import generate_spu_rid
from logger import logger
from login.login import current_user_info

material_storage_bp = Blueprint("material_storage_bp", __name__)


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
    is_non_order_material = request.args.get("isNonOrderMaterial", default=0, type=int)
    filters = {
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
        "material_name": Material.material_name,
        "material_spec": SPUMaterial.material_specification,
        "material_model": SPUMaterial.material_model,
        "material_color": SPUMaterial.color,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
        "shoe_rid": Shoe.shoe_rid,
    }
    query1 = (
        db.session.query(
            MaterialStorage,
            SPUMaterial,
            Material,
            MaterialType,
            Supplier,
            Order,
            OrderShoe,
            Shoe,
            PurchaseOrderItem,
        )
        .join(
            SPUMaterial, MaterialStorage.spu_material_id == SPUMaterial.spu_material_id
        )
        .join(Material, Material.material_id == SPUMaterial.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(Order, OrderShoe.order_id == Order.order_id)
        .outerjoin(
            PurchaseOrderItem,
            MaterialStorage.purchase_order_item_id
            == PurchaseOrderItem.purchase_order_item_id,
        )
    )

    for key, value in filters.items():
        if value and value != "":
            query1 = query1.filter(material_filter_map[key].ilike(f"%{value}%"))

    warehouse_id = request.args.get("warehouseId")
    if warehouse_id and warehouse_id != "":
        query1 = query1.filter(MaterialType.warehouse_id == warehouse_id)

    material_type_id = request.args.get("materialTypeId")
    if material_type_id and material_type_id != "":
        query1 = query1.filter(Material.material_type_id == material_type_id)

    if is_non_order_material == 1:
        query1 = query1.filter(
            MaterialStorage.order_id.is_(None), MaterialStorage.order_shoe_id.is_(None)
        )
    count_result = query1.distinct().count()
    response = query1.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            storage,
            spu_material,
            material,
            material_type,
            supplier,
            order,
            order_shoe,
            shoe,
            purchase_order_item,
        ) = row
        obj = {
            "materialId": spu_material.material_id,
            "materialType": material_type.material_type_name,
            "materialName": material.material_name,
            "materialModel": spu_material.material_model,
            "materialSpecification": spu_material.material_specification,
            "colorName": spu_material.color,
            "materialCategory": material.material_category,
            "estimatedInboundAmount": (
                purchase_order_item.purchase_amount if purchase_order_item else 0
            ),
            "actualInboundAmount": storage.inbound_amount,
            "actualInboundUnit": storage.actual_inbound_unit,
            "currentAmount": storage.current_amount,
            "unitPrice": storage.unit_price,
            "averagePrice": storage.average_price,
            "totalPrice": (
                0
                if not storage.unit_price
                else round(storage.inbound_amount * storage.unit_price, 2)
            ),
            "supplierName": supplier.supplier_name,
            "orderId": order.order_id if order else None,
            "orderRId": order.order_rid if order else None,
            "orderShoeId": order_shoe.order_shoe_id if order_shoe else None,
            "shoeRId": shoe.shoe_rid if shoe else None,
            "materialStorageId": storage.material_storage_id,
            "shoeSizeColumns": storage.shoe_size_columns,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            estimated_amount = (
                getattr(purchase_order_item, f"size_{shoe_size}_purchase_amount", None)
                or 0
                if purchase_order_item
                else 0
            )
            inbound_amount = (
                getattr(storage, f"size_{shoe_size}_inbound_amount", None) or 0
                if storage is not None
                else 0
            )
            current_amount = (
                getattr(storage, f"size_{shoe_size}_current_amount", None) or 0
                if storage is not None
                else 0
            )
            obj[f"estimatedInboundAmount{i}"] = estimated_amount
            obj[f"actualInboundAmount{i}"] = inbound_amount
            obj[f"currentAmount{i}"] = current_amount
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route(
    "/warehouse/getsizematerialstoragebystorageid", methods=["GET"]
)
def get_size_material_storage_by_storage_id():
    """
    根据材料库存ID获取尺码材料库存信息
    """
    storage_id = request.args.get("storageId", None)
    if not storage_id:
        _no_storage_id_error()
    storage = (
        db.session.query(MaterialStorage)
        .filter(MaterialStorage.material_storage_id == storage_id)
        .first()
    )
    if not storage:
        return jsonify({"message": "没有找到该材料库存"}), 404

    obj = {
        "materialStorageId": storage.material_storage_id,
        "estimatedInboundAmount": 0,
        "actualInboundAmount": storage.inbound_amount,
        "currentAmount": storage.current_amount,
        "shoeSizeColumns": storage.shoe_size_columns,
    }
    for i, shoe_size in enumerate(SHOESIZERANGE):
        estimated_inbound_amount = 0
        inbound_amount = getattr(storage, f"size_{shoe_size}_inbound_amount")
        current_amount = getattr(storage, f"size_{shoe_size}_current_amount")
        obj[f"estimatedInboundAmount{i}"] = estimated_inbound_amount
        obj[f"actualInboundAmount{i}"] = inbound_amount
        obj[f"currentAmount{i}"] = current_amount
    return obj


@material_storage_bp.route("/warehouse/getsizematerials", methods=["GET"])
def get_size_materials():
    filters = {
        "material_name": request.args.get("materialName", ""),
        "material_spec": request.args.get("materialSpec", ""),
        "material_model": request.args.get("materialModel", ""),
        "material_color": request.args.get("materialColor", ""),
        "supplierName": request.args.get("supplierName", ""),
        "order_rid": request.args.get("orderRId", ""),
    }
    material_filter_map = {
        "material_name": Material.material_name,
        "material_spec": PurchaseOrderItem.material_specification,
        "material_model": PurchaseOrderItem.material_model,
        "material_color": PurchaseOrderItem.color,
        "supplierName": Supplier.supplier_name,
        "order_rid": Order.order_rid,
    }

    query = (
        db.session.query(
            PurchaseOrderItem,
            Material,
            Supplier,
            Order,
            Shoe,
            MaterialStorage,
        )
        .join(
            Material,
            PurchaseOrderItem.inbound_material_id == Material.material_id,
        )
        .join(
            PurchaseDivideOrder,
            PurchaseOrderItem.purchase_divide_order_id
            == PurchaseDivideOrder.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .join(Order, Order.order_id == PurchaseOrder.order_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(
            MaterialStorage,
            and_(MaterialStorage.purchase_order_item_id
            == PurchaseOrderItem.purchase_order_item_id,
            MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        )
    )
    for key, value in filters.items():
        if value and value != "":
            query = query.filter(material_filter_map[key].ilike(f"%{value}%"))

    material_type_id = request.args.get("materialTypeId")
    if material_type_id and material_type_id != "":
        query = query.filter(Material.material_type_id == material_type_id)

    response = query.all()
    result = []
    for row in response:
        (purchase_order_item, material, supplier, order, shoe, storage) = row
        actual_inbound_amount = storage.inbound_amount if storage else 0
        size_table = json.loads(order.order_size_table)
        if material.material_name == "大底":
            shoe_size_columns = size_table["大底"]
        elif material.material_name == "中底":
            shoe_size_columns = size_table["中底"]
        else:
            shoe_size_columns = []
        obj = {
            "orderRId": order.order_rid,
            "shoeRId": shoe.shoe_rid,
            "materialName": material.material_name,
            "materialModel": purchase_order_item.material_model,
            "materialSpecification": purchase_order_item.material_specification,
            "materialColor": purchase_order_item.color,
            "actualInboundUnit": purchase_order_item.inbound_unit,
            "inboundModel": purchase_order_item.material_model,
            "inboundSpecification": purchase_order_item.material_specification,
            "materialCategory": material.material_category,
            "supplierName": supplier.supplier_name,
            "estimatedInboundAmount": purchase_order_item.purchase_amount,
            "actualInboundAmount": actual_inbound_amount,
            "currentAmount": storage.current_amount if storage else 0,
            "remainingAmount": purchase_order_item.purchase_amount
            - actual_inbound_amount,
            "purchaseOrderItemId": purchase_order_item.purchase_order_item_id,
            "shoeSizeColumns": shoe_size_columns,
        }
        for i, shoe_size in enumerate(SHOESIZERANGE):
            estimated_amount = (
                getattr(purchase_order_item, f"size_{shoe_size}_purchase_amount", None)
                or 0
            )
            inbound_amount = (
                getattr(storage, f"size_{shoe_size}_inbound_amount", None) or 0
                if storage is not None
                else 0
            )
            current_amount = (
                getattr(storage, f"size_{shoe_size}_current_amount", None) or 0
                if storage is not None
                else 0
            )
            obj[f"estimatedInboundAmount{i}"] = estimated_amount
            obj[f"actualInboundAmount{i}"] = inbound_amount
            obj[f"currentAmount{i}"] = current_amount
            obj[f"remainingAmount{i}"] = estimated_amount - inbound_amount
        result.append(obj)
    return result


@material_storage_bp.route("/warehouse/getmaterials", methods=["GET"])
def get_materials():
    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("pageSize", type=int, default=10)
    show_unfinished_orders = request.args.get("showUnfinishedOrders")
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
        "material_spec": PurchaseOrderItem.material_specification,
        "material_model": PurchaseOrderItem.material_model,
        "material_color": PurchaseOrderItem.color,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
    }
    query = (
        db.session.query(
            PurchaseOrderItem,
            Material,
            Supplier,
            Order,
            Shoe,
            MaterialStorage,
        )
        .join(
            Material,
            PurchaseOrderItem.inbound_material_id == Material.material_id,
        )
        .join(
            PurchaseDivideOrder,
            PurchaseOrderItem.purchase_divide_order_id
            == PurchaseDivideOrder.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .join(Order, Order.order_id == PurchaseOrder.order_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(
            MaterialStorage,
            and_(MaterialStorage.purchase_order_item_id
            == PurchaseOrderItem.purchase_order_item_id,
            MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        )
    )
    for key, value in filters.items():
        if value and value != "":
            query = query.filter(material_filter_map[key].ilike(f"%{value}%"))
    if show_unfinished_orders == "true":
        query = query.filter(
            PurchaseOrderItem.purchase_amount
            - func.coalesce(MaterialStorage.inbound_amount, 0)
            > 0
        )
    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()
    result = []
    for row in response:
        (purchase_order_item, material, supplier, order, shoe, storage) = row
        actual_inbound_amount = storage.inbound_amount if storage else 0
        size_table = json.loads(order.order_size_table)
        if material.material_name == "大底":
            shoe_size_columns = size_table["大底"]
        elif material.material_name == "中底":
            shoe_size_columns = size_table["中底"]
        else:
            shoe_size_columns = []
        obj = {
            "orderRId": order.order_rid,
            "shoeRId": shoe.shoe_rid,
            "materialName": material.material_name,
            "materialModel": purchase_order_item.material_model,
            "materialSpecification": purchase_order_item.material_specification,
            "materialColor": purchase_order_item.color,
            "actualInboundUnit": purchase_order_item.inbound_unit,
            "inboundModel": purchase_order_item.material_model,
            "inboundSpecification": purchase_order_item.material_specification,
            "materialCategory": material.material_category,
            "supplierName": supplier.supplier_name,
            "estimatedInboundAmount": purchase_order_item.purchase_amount,
            "actualInboundAmount": actual_inbound_amount,
            "currentAmount": storage.current_amount if storage else 0,
            "remainingAmount": purchase_order_item.purchase_amount
            - actual_inbound_amount,
            "purchaseOrderItemId": purchase_order_item.purchase_order_item_id,
            "shoeSizeColumns": shoe_size_columns,
        }
        for i, shoe_size in enumerate(SHOESIZERANGE):
            estimated_amount = (
                getattr(purchase_order_item, f"size_{shoe_size}_purchase_amount", None)
                or 0
            )
            inbound_amount = (
                getattr(storage, f"size_{shoe_size}_inbound_amount", None) or 0
                if storage is not None
                else 0
            )
            current_amount = (
                getattr(storage, f"size_{shoe_size}_current_amount", None) or 0
                if storage is not None
                else 0
            )
            obj[f"estimatedInboundAmount{i}"] = estimated_amount
            obj[f"actualInboundAmount{i}"] = inbound_amount
            obj[f"currentAmount{i}"] = current_amount
            obj[f"remainingAmount{i}"] = estimated_amount - inbound_amount
        result.append(obj)
    return {"result": result, "total": count_result}


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
            db.session.query(MaterialStorage, SPUMaterial, Order, Shoe)
            .join(
                SPUMaterial,
                MaterialStorage.spu_material_id == SPUMaterial.spu_material_id,
            )
            .outerjoin(Order, Order.order_id == MaterialStorage.order_id)
            .outerjoin(
                OrderShoe, OrderShoe.order_shoe_id == MaterialStorage.order_shoe_id
            )
            .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .filter(
                SPUMaterial.material_id == target_material.material_id,
                SPUMaterial.material_specification == material_specification,
                SPUMaterial.material_model == material_model,
                SPUMaterial.color == material_color,
                MaterialStorage.actual_inbound_unit == unit,
                or_(
                    OrderStatus.order_current_status == IN_PRODUCTION_ORDER_NUMBER,
                    OrderStatus.order_current_status == None,
                ),
            )
            .all()
        )
        for row in material_storages:
            storage, spu_material, order, shoe = row
            obj = {
                "materialStorageId": storage.material_storage_id,
                "materialName": target_material.material_name,
                "materialModel": spu_material.material_model,
                "materialSpecification": spu_material.material_specification,
                "materialColor": spu_material.color,
                "actualInboundUnit": storage.actual_inbound_unit,
                "inboundModel": spu_material.material_model,
                "inboundSpecification": spu_material.material_specification,
                "orderId": storage.order_id,
                "orderRId": order.order_rid if order else None,
                "shoeRId": shoe.shoe_rid if shoe else None,
                "estimatedInboundAmount": 0,
                "actualInboundAmount": storage.inbound_amount,
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
    storage = db.session.query(MaterialStorage).get(id)
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
                storage, f"size_{shoe_size_db_name}_inbound_amount"
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
    existed_spu = (
        db.session.query(SPUMaterial)
        .filter(
            SPUMaterial.material_id == material_id,
            SPUMaterial.material_model == model,
            SPUMaterial.material_specification == specification,
            SPUMaterial.color == color,
        )
        .first()
    )
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


def _find_storage_in_db(
    item: dict, material_type_id, supplier_id, batch_info_type_id=None
):
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
        db.session.add(material)
        db.session.flush()
    material_id = material.material_id
    material_model = item["inboundModel"]
    material_specification = item["inboundSpecification"]
    material_color = item["materialColor"]

    material_category = item.get("materialCategory", 0)
    spu_material_id = _create_spu_record(
        material_id, material_model, material_specification, material_color
    )

    order_id, order_shoe_id = None, None
    order_rid = item.get("orderRId", None)
    if order_rid:
        order, order_shoe = _find_order_shoe(order_rid)
        order_id = order.order_id
        order_shoe_id = order_shoe.order_shoe_id

    storage_query = db.session.query(MaterialStorage).filter(
        MaterialStorage.spu_material_id == spu_material_id,
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
    # 根据材料信息查找对应的材料库存
    # 如果没有找到，则创建新的材料库存
    storage = storage_query.first()
    if not storage:
        storage = MaterialStorage(
            actual_inbound_unit=actual_inbound_unit,
            order_id=order_id,
            order_shoe_id=order_shoe_id,
            spu_material_id=spu_material_id
        )
        # 余量不需要采购单子项id
        if order_id:
            storage.purchase_order_item_id = item.get("purchaseOrderItemId", None)
        shoe_size_columns: list = item.get("shoeSizeColumns", [])
        if not shoe_size_columns:
            shoe_size_columns = []
            result = (
                db.session.query(BatchInfoType)
                .filter(BatchInfoType.batch_info_type_id == batch_info_type_id)
                .first()
            )
            if not result and material_name == "大底":
                error_message = json.dumps({"message": "无效尺码ID"})
                abort(Response(error_message, 400))
            for i in range(len(SHOESIZERANGE)):
                db_name = i + 34
                column_name = f"size_{db_name}_name"
                size_name = getattr(result, column_name, "")
                if not size_name:
                    break
                shoe_size_columns.append(size_name)
        storage.shoe_size_columns = shoe_size_columns
        db.session.add(storage)
        db.session.flush()
    storage_id = storage.material_storage_id
    storage.spu_material_id = spu_material_id
    return storage_id, storage


def _handle_supplier_obj(supplier_name: str):
    # sanitize the supplier name
    if not supplier_name:
        error_message = json.dumps({"message": "供应商名称不能为空"})
        abort(Response(error_message, 400))
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


def _handle_purchase_inbound(data, next_group_id):
    timestamp = data["currentDateTime"]
    formatted_timestamp = (
        timestamp.replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
    )
    inbound_rid = "IR" + formatted_timestamp + "T0"
    supplier_name = data.get("supplierName", None)
    warehouse_id = data.get("warehouseId", None)
    supplier_id = data.get("supplierId")
    batch_info_type_id = data.get("batchInfoTypeId", None)
    material_type_id = data.get("materialTypeId", None)
    remark = data.get("remark", None)
    items = data.get("items", [])

    if not material_type_id:
        _empty_material_type()

    # create inbound record
    inbound_record = InboundRecord(
        inbound_record_id=data.get("inboundRecordId", None),
        inbound_datetime=timestamp,
        inbound_type=0,
        inbound_rid=inbound_rid,
        inbound_batch_id=next_group_id,
        supplier_id=supplier_id,
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
        storage_id, storage = _find_storage_in_db(
            item, material_type_id, supplier_id, batch_info_type_id
        )

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
        record_detail.material_storage_id = storage_id
        storage.inbound_amount += inbound_quantity
        storage.current_amount += inbound_quantity

        for i, shoe_size in enumerate(SHOESIZERANGE):
            if f"amount{i}" not in item:
                break
            column_name = f"size_{shoe_size}_inbound_amount"
            current_value = (
                getattr(storage, column_name) if getattr(storage, column_name) else 0
            )
            new_value = current_value + int(item[f"amount{i}"])
            setattr(storage, column_name, new_value)

            column_name = f"size_{shoe_size}_current_amount"
            current_value = (
                getattr(storage, column_name) if getattr(storage, column_name) else 0
            )
            new_value = current_value + int(item[f"amount{i}"])
            setattr(storage, column_name, new_value)

            column_name = f"size_{shoe_size}_inbound_amount"
            setattr(record_detail, column_name, int(item[f"amount{i}"]))
        db.session.add(record_detail)
    inbound_record.total_price = total_price
    return inbound_record


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
        inbound_record_id=data.get("inboundRecordId", None),
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
        storage = db.session.query(MaterialStorage).get(storage_id)

        # set inbound quantity
        inbound_quantity = Decimal(item["inboundQuantity"])
        record_detail = InboundRecordDetail(
            inbound_record_id=inbound_record.inbound_record_id,
            inbound_amount=inbound_quantity,
            remark=item.get("remark", None),
            order_id=storage.order_id,
            spu_material_id=storage.spu_material_id,
        )

        inbound_record.is_sized_material = 0
        record_detail.material_storage_id = storage_id

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


def create_inbound_record(data):

    # 1) check if material_type_id is provided
    material_type_id = data.get("materialTypeId", None)
    if not material_type_id:
        _empty_material_type()

    # get warehouse_id
    warehouse_id = db.session.query(MaterialType).filter(
        MaterialType.material_type_id == material_type_id
    ).first().warehouse_id

    data["warehouseId"] = warehouse_id
    warehouse_name = db.session.query(MaterialWarehouse).filter(
        MaterialWarehouse.material_warehouse_id == warehouse_id
    ).first().material_warehouse_name

    # 2) you’ll need supplier_id in data for purchase flow
    if data.get("inboundType", 0) == 0:
        supplier = data.get("supplierName")
        supplier_obj = _handle_supplier_obj(supplier)
        data["supplierId"] = supplier_obj.supplier_id

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
        actual_inbound_unit = (
            item.get("actualInboundUnit") if item.get("actualInboundUnit") else ""
        )

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
        record = _handle_purchase_inbound(data, 0)
    elif itype == 1:
        record = _handle_production_remain_inbound(data, 0)
    else:
        abort(Response(json.dumps({"message": "invalid inbound type"}), 400))

    _, staff, _ = current_user_info()
    record.staff_id = staff.staff_id
    rid = record.inbound_rid
    ts = record.inbound_datetime
    return rid, ts, warehouse_name


@material_storage_bp.route("/warehouse/inboundmaterial", methods=["POST"])
def inbound_material():
    data = request.get_json()
    data["currentDateTime"] = format_datetime(datetime.now())
    logger.debug(f"inbound data: {data}")
    rid, ts, warehouse_name = create_inbound_record(data)
    db.session.commit()
    return jsonify({"message": "success", "inboundRId": rid, "inboundTime": ts, "warehouseName": warehouse_name}), 200


def _handle_reject_material_outbound(data):
    supplier_name = data.get("supplierName", None)
    supplier_obj = _handle_supplier_obj(supplier_name)
    data["supplierId"] = supplier_obj.supplier_id
    data["outsourceInfoId"] = None
    outbound_record = _create_outbound_record(data, 0)
    items = data.get("items", [])

    _create_outbound_record_details(items, outbound_record)
    return outbound_record


def _create_outbound_record(data, approval_status):
    timestamp = data.get("currentDateTime")
    department_id = data.get("departmentId", None)
    remark = data.get("remark", None)
    picker = data.get("picker", None)
    outbound_type = data.get("outboundType", 0)
    outsource_info_id = data.get("outsourceInfoId", None)
    supplier_id = data.get("supplierId", None)

    formatted_timestamp = (
        timestamp.replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
    )
    outbound_rid = "OR" + formatted_timestamp + "T" + str(outbound_type)

    # create outbound record
    outbound_record = OutboundRecord(
        outbound_datetime=formatted_timestamp,
        outbound_type=outbound_type,
        outbound_rid=outbound_rid,
        supplier_id=supplier_id,
        picker=picker,
        remark=remark,
        outbound_department=department_id,
        approval_status=approval_status,
        outsource_info_id=outsource_info_id,
    )
    db.session.add(outbound_record)
    db.session.flush()
    return outbound_record


def _create_outbound_record_details(items, outbound_record):
    total_price = 0
    for item in items:
        item: dict
        material_category = item.get("materialCategory", 0)
        storage_id = item.get("materialStorageId", None)
        # 用户必须选材料id
        if not storage_id:
            abort(Response(json.dumps({"message": "没有选择材料库存"}), 400))

        # set outbound quantity
        outbound_quantity = Decimal(item["outboundQuantity"])

        # 用户选择了材料
        storage = (
            db.session.query(MaterialStorage)
            .filter(MaterialStorage.material_storage_id == storage_id)
            .first()
        )

        order_rid = item.get("orderRId", None)
        order_id, order_shoe_id = None, None
        if order_rid:
            order, order_shoe = _find_order_shoe(order_rid)
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

        # set cost
        if outbound_record.outbound_type == 4:
            unit_price = Decimal(item.get("unitPrice", 0))
            record_detail.unit_price = (unit_price,)
            record_detail.item_total_price = Decimal(item.get("itemTotalPrice", 0))
        else:
            record_detail.unit_price = storage.unit_price
            record_detail.item_total_price = outbound_quantity * storage.unit_price

        total_price += record_detail.item_total_price

        outbound_record.is_sized_material = 0
        record_detail.material_storage_id = storage_id
        storage.current_amount -= outbound_quantity

        if storage.current_amount < 0:
            error_message = json.dumps({"message": "出库数量大于库存数量"})
            abort(Response(error_message, 400))

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

            column_name = f"size_{shoe_size}_outbound_amount"
            setattr(record_detail, column_name, int(item[f"amount{i}"]))
        db.session.add(record_detail)
    outbound_record.total_price = total_price


def _handle_production_outbound(data):
    items = data.get("items", [])
    data["supplierId"] = None
    outbound_record = _create_outbound_record(data, 1)
    _create_outbound_record_details(items, outbound_record)
    return outbound_record


def _handle_waste_outbound(data):
    items = data.get("items", [])
    data["supplierId"] = None
    data["outsourceInfoId"] = None
    outbound_record = _create_outbound_record(data, 1)
    _create_outbound_record_details(items, outbound_record)
    return outbound_record


def _handle_outsource_outbound(data):
    items = data.get("items", [])
    data["supplierId"] = None
    outbound_record = _create_outbound_record(data, 1)
    _create_outbound_record_details(items, outbound_record)
    return outbound_record


def _handle_composite_outbound(data):
    items = data.get("items", [])
    supplier_name = data.get("supplierName", None)
    supplier_obj = _handle_supplier_obj(supplier_name)
    data["supplierId"] = supplier_obj.supplier_id
    data["outsourceInfoId"] = None
    outbound_record = _create_outbound_record(data, 1)
    _create_outbound_record_details(items, outbound_record)
    return outbound_record


def _outbound_material_helper(data):
    data = request.get_json()
    outbound_type = data.get("outboundType", 0)
    data["currentDateTime"] = format_datetime(datetime.now())
    # 工厂使用
    if outbound_type == 0:
        record = _handle_production_outbound(data)
    # 废料处理
    elif outbound_type == 1:
        record = _handle_waste_outbound(data)
    # 外包出库
    elif outbound_type == 2:
        record = _handle_outsource_outbound(data)
    # 复合出库
    elif outbound_type == 3:
        record = _handle_composite_outbound(data)
    # 材料退回
    elif outbound_type == 4:
        record = _handle_reject_material_outbound(data)
    else:
        error_message = json.dumps({"message": "无效的出库类型"})
        abort(Response(error_message, 400))

    record.staff_id = current_user_info()[1].staff_id
    return record.outbound_rid, data["currentDateTime"]


@material_storage_bp.route("/warehouse/outboundmaterial", methods=["POST"])
def outbound_material():
    data = request.get_json()
    logger.debug(f"outbound data: {data}")
    outbound_rid, timestamp = _outbound_material_helper(data)

    db.session.commit()
    return jsonify(
        {"message": "success", "outboundRId": outbound_rid, "outboundTime": timestamp}
    )


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
    response = query1.all()
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
    character, staff, department = current_user_info()
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
    # 如果是仓库文员角色，入库记录只能查询自己的
    character_id = character.character_id
    if character_id == WAREHOUSE_CLERK_ROLE:
        query = query.filter(InboundRecord.staff_id == staff.staff_id)
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
            "warehouseId": inbound_record.warehouse_id,
            "warehouseName": warehouse.material_warehouse_name,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route("/warehouse/getinboundrecordbyid", methods=["GET"])
def get_inbound_record_by_id():
    inbound_record_id = request.args.get("inboundRecordId")

    inbound_record = db.session.query(InboundRecord).get(inbound_record_id)
    is_sized_material = inbound_record.is_sized_material
    inbound_response = (
        db.session.query(
            InboundRecordDetail,
            InboundRecord,
            MaterialStorage,
            SPUMaterial,
            Material,
            MaterialType,
            MaterialWarehouse,
            Supplier,
            Order,
            Shoe,
        )
        .join(
            InboundRecord,
            InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id,
        )
        .join(
            MaterialStorage,
            InboundRecordDetail.material_storage_id
            == MaterialStorage.material_storage_id,
        )
        .join(
            SPUMaterial,
            SPUMaterial.spu_material_id == MaterialStorage.spu_material_id,
        )
        .join(
            Material,
            Material.material_id == SPUMaterial.material_id,
        )
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(
            MaterialWarehouse,
            MaterialWarehouse.material_warehouse_id == InboundRecord.warehouse_id,
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

    if not inbound_response:
        return jsonify({"message": "record not found"}), 404
    first_row = inbound_response[0]
    result = {
        "metadata": {
            "inboundRecordId": first_row.InboundRecord.inbound_record_id,
            "inboundRId": first_row.InboundRecord.inbound_rid,
            "warehouseId": first_row.InboundRecord.warehouse_id,
            "payMethod": first_row.InboundRecord.pay_method,
            "remark": first_row.InboundRecord.remark,
            "supplierName": first_row.Supplier.supplier_name,
            "materialTypeId": first_row.MaterialType.material_type_id,
            "inboundType": first_row.InboundRecord.inbound_type,
            "warehouseName": first_row.MaterialWarehouse.material_warehouse_name,
            "timestamp": format_datetime(first_row.InboundRecord.inbound_datetime),
        },
        "items": [],
    }
    for row in inbound_response:
        (
            record_detail,
            record,
            material_storage,
            spu_material,
            material,
            material_type,
            material_warehouse,
            supplier,
            order,
            shoe,
        ) = row
        obj = {
            "inboundQuantity": record_detail.inbound_amount,
            "unitPrice": record_detail.unit_price,
            "itemTotalPrice": record_detail.item_total_price,
            "inboundRecordDetailId": record_detail.id,
            "remark": record_detail.remark,
            "materialName": material.material_name,
            "materialModel": spu_material.material_model,
            "materialSpecification": spu_material.material_specification,
            "materialCategory": material.material_category,
            "inboundModel": spu_material.material_model,
            "inboundSpecification": spu_material.material_specification,
            "materialColor": spu_material.color,
            "materialUnit": material_storage.actual_inbound_unit,
            "materialTypeId": material.material_type_id,
            "materialStorageId": material_storage.material_storage_id,
            "actualInboundUnit": material_storage.actual_inbound_unit,
            "orderRId": order.order_rid if order else None,
            "supplierName": supplier.supplier_name if supplier else None,
            "shoeSizeColumns": material_storage.shoe_size_columns,
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
        result["items"].append(obj)
    return result


@material_storage_bp.route("/warehouse/getoutboundrecordbyid", methods=["GET"])
def get_outbound_record_by_id():
    outbound_record_id = request.args.get("outboundRecordId")

    outbound_record = db.session.query(OutboundRecord).get(outbound_record_id)
    response = (
        db.session.query(
            OutboundRecordDetail,
            OutboundRecord,
            SPUMaterial,
            MaterialStorage,
            Material,
            MaterialType,
            Supplier,
            Order,
            Shoe,
        )
        .join(
            OutboundRecord,
            OutboundRecord.outbound_record_id
            == OutboundRecordDetail.outbound_record_id,
        )
        .join(
            SPUMaterial,
            SPUMaterial.spu_material_id == OutboundRecordDetail.spu_material_id,
        )
        .join(
            MaterialStorage,
            OutboundRecordDetail.material_storage_id
            == MaterialStorage.material_storage_id,
        )
        .join(
            Material,
            Material.material_id == SPUMaterial.material_id,
        )
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .outerjoin(Supplier, Supplier.supplier_id == OutboundRecord.supplier_id)
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
            OutboundRecord.outbound_record_id == outbound_record_id,
        )
        .all()
    )

    if not response:
        return jsonify({"message": "record not found"}), 404
    first_row = response[0]
    result = {
        "metadata": {
            "outboundRecordId": first_row.OutboundRecord.outbound_record_id,
            "outboundRId": first_row.OutboundRecord.outbound_rid,
            "remark": first_row.OutboundRecord.remark,
            "supplierName": first_row.Supplier.supplier_name,
            "materialTypeId": first_row.MaterialType.material_type_id,
            "outboundType": first_row.OutboundRecord.outbound_type,
            "timestamp": format_datetime(first_row.OutboundRecord.outbound_datetime),
        },
        "items": [],
    }
    for row in response:
        (
            record_detail,
            record,
            spu_material,
            material_storage,
            material,
            material_type,
            supplier,
            order,
            shoe,
        ) = row
        obj = {
            "outboundQuantity": record_detail.outbound_amount,
            "unitPrice": record_detail.unit_price,
            "itemTotalPrice": record_detail.item_total_price,
            "outboundRecordDetailId": record_detail.id,
            "remark": record_detail.remark,
            "materialName": material.material_name,
            "materialModel": spu_material.material_model,
            "materialSpecification": spu_material.material_specification,
            "materialCategory": material.material_category,
            "inboundModel": spu_material.material_model,
            "inboundSpecification": spu_material.material_specification,
            "materialColor": spu_material.color,
            "materialUnit": material_storage.actual_inbound_unit,
            "materialTypeId": material.material_type_id,
            "materialStorageId": material_storage.material_storage_id,
            "actualInboundUnit": material_storage.actual_inbound_unit,
            "orderRId": order.order_rid if order else None,
            "supplierName": supplier.supplier_name if supplier else None,
            "shoeSizeColumns": material_storage.shoe_size_columns,
            "shoeRId": shoe.shoe_rid if shoe else None,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_outbound_amount"
            obj[f"amount{i}"] = (
                getattr(record_detail, column_name, None)
                if getattr(record_detail, column_name, None)
                else 0
            )
            column_name = f"size_{shoe_size}_current_amount"
            obj[f"currentAmount{i}"] = (
                getattr(material_storage, column_name, None)
                if getattr(material_storage, column_name, None)
                else 0
            )
        result["items"].append(obj)
    return result


@material_storage_bp.route("/warehouse/getmaterialoutboundrecords", methods=["GET"])
def get_material_outbound_records():
    character, staff, department = current_user_info()
    start_date_search = request.args.get("startDate")
    end_date_search = request.args.get("endDate")
    page = int(request.args.get("page", 1))
    number = int(request.args.get("pageSize", 10))
    outbound_rid = request.args.get("outboundRId")
    status = request.args.get("status", type=int, default=0)
    destination = request.args.get("destination")
    outbound_type = request.args.get("outboundType", type=int, default=0)

    query = (
        db.session.query(
            OutboundRecord, OutsourceFactory, Department, Supplier
        )
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
            OutboundRecord.supplier_id == Supplier.supplier_id,
        )
    )
    # 如果是仓库文员角色，出库记录只能查询自己的
    character_id = character.character_id
    if character_id == WAREHOUSE_CLERK_ROLE:
        query = query.filter(OutboundRecord.staff_id == staff.staff_id)

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
    if status in [0, 1, 2]:
        query = query.filter(OutboundRecord.approval_status == status)
    if character.character_id == ACCOUNTING_AUDIT_ROLE:
        query = query.filter(OutboundRecord.outbound_type == 4)
    if destination:
        query = query.filter(
            or_(
                Department.department_name.ilike(f"%{destination}%"),
                OutsourceFactory.factory_name.ilike(f"%{destination}%"),
                Supplier.supplier_name.ilike(f"%{destination}%"),
            )
        )
    if outbound_type and outbound_type in OUTBOUND_TYPE_MAPPING:
        query = query.filter(OutboundRecord.outbound_type == outbound_type)

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
        if outbound_record.outbound_type == 0:
            destination = department.department_name
        elif outbound_record.outbound_type == 2:
            destination = outsource_factory.factory_name
        elif outbound_record.outbound_type == 3 or outbound_record.outbound_type == 4:
            destination = supplier.supplier_name
        else:
            destination = None
        outbound_type = OUTBOUND_TYPE_MAPPING.get(
            outbound_record.outbound_type, "生产出库"
        )
        obj = {
            "outboundRecordId": outbound_record.outbound_record_id,
            "outboundBatchId": outbound_record.outbound_batch_id,
            "outboundRId": outbound_record.outbound_rid,
            "timestamp": format_datetime(outbound_record.outbound_datetime),
            "outboundType": outbound_type,
            "destination": destination,
            "picker": outbound_record.picker,
            "totalPrice": outbound_record.total_price,
            "remark": outbound_record.remark,
            "approvalStatus": outbound_record.approval_status,
            "rejectReason": outbound_record.reject_reason,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route("/warehouse/getoutboundrecordbyrecordid", methods=["GET"])
def get_outbound_record_by_record_id():
    outbound_record_id = request.args.get("outboundRecordId")
    columns = [
        getattr(OutboundRecordDetail, f"size_{i+34}_outbound_amount")
        for i in range(len(SHOESIZERANGE))
    ]
    query1 = (
        db.session.query(
            OutboundRecordDetail,
            MaterialStorage,
            SPUMaterial,
            Material,
            Order,
            Shoe,
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
            SPUMaterial,
            SPUMaterial.spu_material_id == MaterialStorage.spu_material_id,
        )
        .join(
            Material,
            Material.material_id == SPUMaterial.material_id,
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
            OutboundRecord.outbound_record_id == outbound_record_id,
        )
    )
    response = query1.all()
    result = []
    for row in response:
        (record_item, material_storage, spu_material, material, order, shoe) = row
        obj = {
            "outboundQuantity": record_item.outbound_amount,
            "unitPrice": record_item.unit_price,
            "itemTotalPrice": record_item.item_total_price,
            "outboundRecordDetailId": record_item.id,
            "remark": record_item.remark,
            "materialName": material.material_name,
            "materialModel": spu_material.material_model,
            "materialSpecification": spu_material.material_specification,
            "colorName": spu_material.color,
            "materialStorageId": material_storage.material_storage_id,
            "actualInboundUnit": material_storage.actual_inbound_unit,
            "shoeSizeColumns": material_storage.shoe_size_columns,
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
        .outerjoin(Supplier, Supplier.supplier_id == OutboundRecord.supplier_id)
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
        storage = db.session.query(MaterialStorage).get(row["storageId"])
        if not storage:
            return jsonify({"message": "order shoe storage not found"}), 400
        unique_order_shoe_ids.add((row["orderId"], storage.order_shoe_id))
        storage.material_storage_status = 1
    db.session.commit()
    return jsonify({"message": "success"})


@material_storage_bp.route(
    "/warehouse/warehousemanager/finishoutboundmaterial", methods=["PATCH"]
)
def finish_outbound_material():
    data = request.get_json()
    for row in data:
        storage = db.session.query(MaterialStorage).get(row["storageId"])
        if not storage:
            return jsonify({"message": "order shoe storage not found"}), 400
        storage.material_storage_status = 2
    db.session.commit()
    return jsonify({"message": "success"})


def _handle_delete_inbound_record_detail(
    inbound_record_detail, storage_id, is_sized_material
):
    storage = db.session.query(MaterialStorage).get(storage_id)
    storage.inbound_amount -= inbound_record_detail.inbound_amount
    storage.current_amount -= inbound_record_detail.inbound_amount
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

        db_column_name = f"size_{shoe_size}_inbound_amount"
        final_amount = (
            getattr(storage, db_column_name) - size_amount
            if getattr(storage, db_column_name) - size_amount >= 0
            else 0
        )
        setattr(storage, db_column_name, final_amount)
    db.session.delete(inbound_record_detail)


def _handle_delete_storage(storage, is_sized_material):
    total_purchase_order_id = storage.total_purchase_order_id
    # search dependency
    detail = db.session.query(
        InboundRecordDetail.material_storage_id == storage.material_storage_id
    ).first()

    if not total_purchase_order_id and not detail:
        db.session.delete(storage)


@material_storage_bp.route("/warehouse/updateinboundrecord", methods=["PUT"])
def update_inbound_record():
    data = request.get_json()
    logger.debug(f"update data: {data}")
    inbound_record_id = data.get("inboundRecordId")
    is_sized_material = data.get("isSizedMaterial", 0)

    inbound_record = (
        db.session.query(InboundRecord)
        .filter(InboundRecord.inbound_record_id == inbound_record_id)
        .first()
    )
    if not inbound_record:
        return jsonify({"message": "inbound record not found"}), 404

    inbound_timestamp: datetime = inbound_record.inbound_datetime

    details = (
        db.session.query(InboundRecordDetail)
        .filter(InboundRecordDetail.inbound_record_id == inbound_record_id)
        .all()
    )

    for detail in details:
        storage = db.session.query(MaterialStorage).get(detail.material_storage_id)
        storage.inbound_amount -= detail.inbound_amount
        storage.current_amount -= detail.inbound_amount
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_inbound_amount"
            size_amount = (
                getattr(detail, column_name, 0)
                if getattr(detail, column_name, 0)
                else 0
            )

            db_column_name = f"size_{shoe_size}_current_amount"
            final_amount = (
                getattr(storage, db_column_name) - size_amount
                if getattr(storage, db_column_name) - size_amount >= 0
                else 0
            )
            setattr(storage, db_column_name, final_amount)

            db_column_name = f"size_{shoe_size}_inbound_amount"
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

    new_rid, new_ts, warehouse_name = create_inbound_record(data)
    db.session.commit()

    return jsonify({"message": "updated", "inboundRId": new_rid, "inboundTime": new_ts, "warehouseName": warehouse_name}), 200


@material_storage_bp.route("/warehouse/updateoutboundrecord", methods=["PUT"])
def update_outbound_record():
    data = request.get_json()
    logger.debug(f"update outbound data: {data}")
    outbound_record_id = data.get("outboundRecordId")

    outbound_record = (
        db.session.query(OutboundRecord)
        .filter(OutboundRecord.outbound_record_id == outbound_record_id)
        .first()
    )
    if not outbound_record:
        return jsonify({"message": "inbound record not found"}), 404

    outbound_timestamp: datetime = outbound_record.outbound_datetime
    outbound_rid = outbound_record.outbound_rid

    details = (
        db.session.query(OutboundRecordDetail)
        .filter(OutboundRecordDetail.outbound_record_id == outbound_record_id)
        .all()
    )

    for detail in details:
        storage = db.session.query(MaterialStorage).get(detail.material_storage_id)
        storage.inbound_amount += detail.outbound_amount
        storage.current_amount += detail.outbound_amount
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_inbound_amount"
            size_amount = (
                getattr(detail, column_name, 0)
                if getattr(detail, column_name, 0)
                else 0
            )

            db_column_name = f"size_{shoe_size}_current_amount"
            final_amount = (
                getattr(storage, db_column_name) + size_amount
                if getattr(storage, db_column_name) + size_amount >= 0
                else 0
            )
            setattr(storage, db_column_name, final_amount)

            db_column_name = f"size_{shoe_size}_inbound_amount"
            final_amount = (
                getattr(storage, db_column_name) + size_amount
                if getattr(storage, db_column_name) + size_amount >= 0
                else 0
            )
            setattr(storage, db_column_name, final_amount)

        db.session.delete(detail)

    db.session.delete(outbound_record)
    db.session.flush()

    # 4) recreate, reusing inbound_timestamp and outbound_record_id
    data = request.get_json()
    data["currentDateTime"] = format_datetime(outbound_timestamp)
    data["outboundRecordId"] = outbound_record_id

    new_rid, new_ts = _outbound_material_helper(data)
    db.session.commit()

    return jsonify(
        {"message": "updated", "outboundRId": new_rid, "outboundTime": new_ts}
    )


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
            storage.inbound_amount -= inbound_record_detail.inbound_amount
        storage.current_amount -= inbound_record_detail.inbound_amount
        db.session.delete(inbound_record_detail)

        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_current_amount"
            current_value = getattr(storage, column_name)

            record_detail_column_name = f"size_{shoe_size}_inbound_amount"
            inbound_value = getattr(inbound_record_detail, record_detail_column_name)
            if inbound_value is None:
                continue
            new_value = current_value - inbound_value
            setattr(storage, column_name, new_value)

        if inbound_record.inbound_type in [0, 2]:
            for i in range(len(SHOESIZERANGE)):
                shoe_size = SHOESIZERANGE[i]
                column_name = f"size_{shoe_size}_inbound_amount"
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


@material_storage_bp.route("/warehouse/getallmaterialmodels", methods=["GET"])
def get_all_material_models():
    material_model = request.args.get("materialModel")
    if not material_model or material_model == "":
        return jsonify([])
    # get all material models from material storage
    material_models = (
        db.session.query(
            SPUMaterial.material_model,
        )
        .filter(SPUMaterial.material_model.ilike(f"%{material_model}%"))
        .distinct()
    )
    result = []
    for model in material_models:
        obj = {"value": model[0], "name": model[0]}
        result.append(obj)
    return jsonify(result)

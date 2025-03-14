from datetime import datetime, date
from decimal import Decimal

from api_utility import format_date, format_datetime
from app_config import db
from shared_apis.batch_info_type import get_order_batch_type_helper
from constants import (
    END_OF_PRODUCTION_NUMBER,
    IN_PRODUCTION_ORDER_NUMBER,
    PRODUCTION_LINE_REFERENCE,
    SHOESIZERANGE,
)
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request
from models import *
from sqlalchemy import and_, asc, desc, exists, func, not_, or_, text, literal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
import json
from accounting.accounting_transaction import add_payable_entity, material_inbound_accounting_event

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
    filters = {
        "material_type_name": request.args.get("materialType", ""),
        "material_name": request.args.get("materialName", ""),
        "material_spec": request.args.get("materialSpec", ""),
        "material_model": request.args.get("materialModel", ""),
        "material_color": request.args.get("materialColor", ""),
        "supplier": request.args.get("supplier", ""),
        "order_rid": request.args.get("orderRId", ""),
        "shoe_rid": request.args.get("shoeRId", ""),
    }
    material_filter_map = {
        "material_type_name": MaterialType.material_type_name,
        "material_name": Material.material_name,
        "material_spec": MaterialStorage.material_specification,
        "material_model": MaterialStorage.material_model,
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
    direct_order = aliased(Order)
    indirect_order = aliased(Order)
    direct_order_status = aliased(OrderStatus)
    indirect_order_status = aliased(OrderStatus)
    query1 = (
        db.session.query(
            direct_order.order_id,
            direct_order.order_rid,
            indirect_order.order_id,
            indirect_order.order_rid,
            OrderShoe.order_shoe_id,
            Shoe.shoe_rid,
            MaterialStorage.material_storage_id,
            MaterialStorage.estimated_inbound_amount,
            MaterialStorage.actual_inbound_amount,
            MaterialStorage.current_amount,
            MaterialStorage.material_specification,
            MaterialStorage.unit_price,
            MaterialStorage.material_estimated_arrival_date,
            MaterialStorage.material_model,
            MaterialStorage.material_storage_status,
            MaterialStorage.actual_inbound_unit,
            MaterialStorage.actual_purchase_amount,
            Material.material_id,
            Material.material_name,
            Material.material_unit,
            MaterialType.material_type_name,
            Material.material_category,
            Supplier.supplier_name,
            TotalPurchaseOrder.total_purchase_order_id,
            TotalPurchaseOrder.total_purchase_order_rid,
            TotalPurchaseOrder.create_date,
            MaterialStorage.material_storage_color,
            MaterialStorage.craft_name,
            MaterialStorage.composite_unit_cost,
        )
        .join(
            Material, Material.material_id == MaterialStorage.actual_inbound_material_id
        )
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(
            TotalPurchaseOrder,
            TotalPurchaseOrder.total_purchase_order_id
            == MaterialStorage.total_purchase_order_id,
        )
        .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(indirect_order, OrderShoe.order_id == indirect_order.order_id)
        .outerjoin(direct_order, MaterialStorage.order_id == direct_order.order_id)
        .outerjoin(
            direct_order_status, direct_order.order_id == direct_order_status.order_id
        )
        .outerjoin(
            indirect_order_status,
            indirect_order.order_id == indirect_order_status.order_id,
        )
    )
    query2 = (
        db.session.query(
            direct_order.order_id,
            direct_order.order_rid,
            indirect_order.order_id,
            indirect_order.order_rid,
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
            SizeMaterialStorage.material_estimated_arrival_date,
            SizeMaterialStorage.size_material_model.label("size_material"),
            SizeMaterialStorage.material_storage_status,
            literal("双").label("actual_inbound_unit"),
            SizeMaterialStorage.total_estimated_inbound_amount.label(
                "actual_purchase_amount"
            ),
            Material.material_id,
            Material.material_name,
            Material.material_unit,
            MaterialType.material_type_name,
            Material.material_category,
            Supplier.supplier_name,
            TotalPurchaseOrder.total_purchase_order_id,
            TotalPurchaseOrder.total_purchase_order_rid,
            TotalPurchaseOrder.create_date,
            SizeMaterialStorage.size_material_color,
            SizeMaterialStorage.craft_name,
            literal(0).label("composite_unit_cost"),
        )
        .join(Material, Material.material_id == SizeMaterialStorage.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(
            TotalPurchaseOrder,
            TotalPurchaseOrder.total_purchase_order_id
            == SizeMaterialStorage.total_purchase_order_id,
        )
        .outerjoin(
            OrderShoe, SizeMaterialStorage.order_shoe_id == OrderShoe.order_shoe_id
        )
        .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(indirect_order, OrderShoe.order_id == indirect_order.order_id)
        .outerjoin(direct_order, SizeMaterialStorage.order_id == direct_order.order_id)
        .outerjoin(
            direct_order_status, direct_order.order_id == direct_order_status.order_id
        )
        .outerjoin(
            indirect_order_status,
            indirect_order.order_id == indirect_order_status.order_id,
        )
    )
    # allow inbound operation when the order is in production
    if op_type == 1 or op_type == 3:
        query1 = query1.filter(
            and_(
                or_(
                    direct_order_status.order_current_status
                    == IN_PRODUCTION_ORDER_NUMBER,
                    indirect_order_status.order_current_status
                    == IN_PRODUCTION_ORDER_NUMBER,
                    direct_order_status.order_current_status.is_(None),
                    indirect_order_status.order_current_status.is_(None),
                ),
                MaterialStorage.material_storage_status == 0,
            )
        )
        query2 = query2.filter(
            and_(
                or_(
                    direct_order_status.order_current_status
                    == IN_PRODUCTION_ORDER_NUMBER,
                    indirect_order_status.order_current_status
                    == IN_PRODUCTION_ORDER_NUMBER,
                    direct_order_status.order_current_status.is_(None),
                    indirect_order_status.order_current_status.is_(None),
                ),
                SizeMaterialStorage.material_storage_status == 0,
            )
        )
    # allow outbound operation if material is in stock
    # in case of the material needs to be outbounded as waste
    if op_type == 2 or op_type == 4:
        query1 = query1.filter(
            and_(
                or_(
                    direct_order_status.order_current_status
                    == IN_PRODUCTION_ORDER_NUMBER,
                    indirect_order_status.order_current_status
                    == IN_PRODUCTION_ORDER_NUMBER,
                    direct_order_status.order_current_status.is_(None),
                    indirect_order_status.order_current_status.is_(None),
                ),
                MaterialStorage.current_amount > 0,
                MaterialStorage.material_storage_status < 2,
            )
        )
        query2 = query2.filter(
            or_(
                direct_order_status.order_current_status == IN_PRODUCTION_ORDER_NUMBER,
                indirect_order_status.order_current_status
                == IN_PRODUCTION_ORDER_NUMBER,
                direct_order_status.order_current_status.is_(None),
                indirect_order_status.order_current_status.is_(None),
            ),
            SizeMaterialStorage.total_current_amount > 0,
            SizeMaterialStorage.material_storage_status < 2,
        )

    if op_type == 1 or op_type == 2:
        query1 = query1.filter(MaterialType.material_type_id != 9)
        query2 = query2.filter(MaterialType.material_type_id != 9)
    # if it is composite inbound and outbound
    elif op_type == 3 or op_type == 4:
        query1 = query1.filter(MaterialType.material_type_id == 9)
        query2 = query2.filter(MaterialType.material_type_id == 9)

    for key, value in filters.items():
        if value and value != "":
            query1 = query1.filter(material_filter_map[key].ilike(f"%{value}%"))
            query2 = query2.filter(size_material_filter_map[key].ilike(f"%{value}%"))
    union_query = query1.union(query2)
    if sort_column and sort_column == "purchaseOrderIssueDate":
        if sort_order == "ascending":
            union_query = union_query.order_by(
                asc(PurchaseOrder.purchase_order_issue_date)
            )
        elif sort_order == "descending":
            union_query = union_query.order_by(
                desc(PurchaseOrder.purchase_order_issue_date)
            )
    count_result = union_query.distinct().count()
    response = union_query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        (
            direct_order_id,
            direct_order_rid,
            indirect_order_id,
            indirect_order_rid,
            order_shoe_id,
            shoe_rid,
            material_storage_id,
            estimated_inbound_amount,
            actual_inbound_amount,
            current_amount,
            material_specification,
            unit_price,
            material_estimated_arrival_date,
            material_model,
            material_storage_status,
            actual_inbound_unit,
            actual_purchase_amount,
            material_id,
            material_name,
            material_unit,
            material_type_name,
            material_category,
            supplier_name,
            total_purchase_order_id,
            total_purchase_order_rid,
            create_date,
            color,
            craft_name,
            composite_unit_cost,
        ) = row
        if material_storage_status == 0:
            status = "未完成入库"
        elif material_storage_status == 1:
            status = "已完成入库"
        elif material_storage_status == 2:
            status = "已完成出库"
        if not material_estimated_arrival_date:
            date_value = ""
        else:
            date_value = format_date(material_estimated_arrival_date)
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
            "totalPrice": (
                0 if not unit_price else round(actual_inbound_amount * unit_price, 2)
            ),
            "supplierName": supplier_name,
            "orderId": direct_order_id if not order_shoe_id else indirect_order_id,
            "orderRId": direct_order_rid if not order_shoe_id else indirect_order_rid,
            "orderShoeId": order_shoe_id,
            "shoeRId": shoe_rid,
            "materialStorageId": material_storage_id,
            "status": status,
            "colorName": color,
            "materialArrivalDate": date_value,
            "totalPurchaseOrderId": total_purchase_order_id,
            "totalPurchaseOrderRId": total_purchase_order_rid,
            "totalPurchaseOrderCreateDate": format_date(create_date),
            "materialModel": material_model,
            "craftName": craft_name,
            "compositeUnitCost": round(composite_unit_cost, 2),
            "compositeTotalPrice": (
                0
                if not composite_unit_cost
                else round(actual_inbound_amount * composite_unit_cost, 2)
            ),
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route("/warehouse/getmaterials", methods=["GET"])
def get_materials():
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
        "material_spec": MaterialStorage.material_specification,
        "material_model": MaterialStorage.material_model,
        "material_color": MaterialStorage.material_storage_color,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
    }
    size_material_filter_map = {
        "material_name": Material.material_name,
        "material_spec": SizeMaterialStorage.size_material_specification,
        "material_model": SizeMaterialStorage.size_material_model,
        "material_color": SizeMaterialStorage.size_material_color,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
    }

    # find out material is sized or not
    material_query = db.session.query(Material, Supplier).join(
        Supplier, Material.material_supplier == Supplier.supplier_id
    )
    if filters["material_name"] and filters["material_name"] != "":
        material_query = material_query.filter(
            Material.material_name.ilike(f"%{filters['material_name']}%")
        )
    if filters["supplier"] and filters["supplier"] != "":
        material_query = material_query.filter(
            Supplier.supplier_name.ilike(f"%{filters["supplier"]}%")
        )
    entities = material_query.first()

    if not entities:
        return jsonify({"message": "没有该材料"}), 404

    db_material, db_supplier = entities
    if db_material.material_category == 0:
        query = (
            db.session.query(MaterialStorage, Material, Supplier, Order)
            .join(
                Material,
                MaterialStorage.actual_inbound_material_id == Material.material_id,
            )
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .outerjoin(Order, Order.order_id == MaterialStorage.order_id)
        )
        for key, value in filters.items():
            if value and value != "":
                query = query.filter(material_filter_map[key].ilike(f"%{value}%"))
        response = query.all()
    else:
        query = (
            db.session.query(SizeMaterialStorage, Material, Supplier, Order)
            .join(
                Material,
                SizeMaterialStorage.material_id == Material.material_id,
            )
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .outerjoin(Order, Order.order_id == SizeMaterialStorage.order_id)
        )
        for key, value in filters.items():
            if value and value != "":
                query = query.filter(size_material_filter_map[key].ilike(f"%{value}%"))
        response = query.all()
    result = []
    for row in response:
        storage, material, supplier, order = row
        if material.material_category == 0:
            obj = {
                "materialStorageId": storage.material_storage_id,
                "materialId": material.material_id,
                "materialName": material.material_name,
                "materialModel": storage.material_model,
                "materialSpecification": storage.material_specification,
                "materialColor": storage.material_storage_color,
                "materialUnit": material.material_unit,
                "materialCategory": material.material_category,
                "estimatedInboundAmount": storage.estimated_inbound_amount,
                "actualInboundAmount": storage.actual_inbound_amount,
                "actualInboundUnit": storage.actual_inbound_unit,
                "currentAmount": storage.current_amount,
                "unitPrice": storage.unit_price,
                "compositeUnitCost": storage.composite_unit_cost,
                "supplierName": supplier.supplier_name,
                "orderRId": order.order_rid if order else None,
            }
        else:
            obj = {
                "materialStorageId": storage.size_material_storage_id,
                "materialId": material.material_id,
                "materialName": material.material_name,
                "materialModel": storage.size_material_model,
                "materialSpecification": storage.size_material_specification,
                "materialColor": storage.size_material_color,
                "materialUnit": material.material_unit,
                "materialCategory": material.material_category,
                "estimatedInboundAmount": storage.total_estimated_inbound_amount,
                "actualInboundAmount": storage.total_actual_inbound_amount,
                "actualInboundUnit": material.material_unit,
                "currentAmount": storage.total_current_amount,
                "unitPrice": storage.unit_price,
                "supplierName": supplier.supplier_name,
                "orderRId": order.order_rid if order else None,
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


# @material_storage_bp.route(
#     "/warehouse/warehousemanager/checkinboundoptions", methods=["GET"]
# )
# def check_inbound_options():
#     """
#     1: 采购入库
#     2: 生产剩余
#     """
#     order_shoe_id = request.args.get("orderShoeId")
#     if not order_shoe_id:
#         return {1: True, 2: True}
#     status_list = (
#         db.session.query(OrderShoeStatus)
#         .filter(OrderShoeStatus.order_shoe_id == order_shoe_id)
#         .all()
#     )
#     result = {1: False, 2: True}
#     for status_obj in status_list:
#         if status_obj.current_status in [8, 15] and status_obj.current_status_value in [
#             0,
#             1,
#         ]:
#             result[1] = True
#             break
#     return result


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


@material_storage_bp.route(
    "/warehouse/warehousemanager/oldinboundmaterial", methods=["PATCH"]
)
def old_inbound_material():
    data = request.get_json()
    # Determine the next available group_id
    next_group_id = (
        db.session.query(
            func.coalesce(func.max(InboundRecord.inbound_batch_id), 0)
        ).scalar()
        + 1
    )
    counter = 0
    for inbound_row in data:
        inbound_type = inbound_row.get("inboundType", None)
        timestamp = inbound_row.get("inboundTimestamp", None)
        formatted_timestamp = (
            timestamp.replace("-", "").replace(" ", "").replace(":", "")
        )
        inbound_rid = "IR" + formatted_timestamp + f"{counter:02}"
        for item in inbound_row["items"]:
            # material storage
            if item["materialCategory"] == 0:
                storage = MaterialStorage.query.get(item["materialStorageId"])
            elif item["materialCategory"] == 1:
                storage = SizeMaterialStorage.query.get(item["materialStorageId"])

            # set cost
            if inbound_type != 2:
                storage.unit_price = item["unitPrice"]
            if inbound_type == 2:
                storage.composite_unit_cost = item["compositeUnitCost"]

            # set inbound quantity
            record = InboundRecord(
                inbound_amount=Decimal(item["inboundQuantity"]),
                inbound_datetime=timestamp,
                inbound_type=inbound_type,
                remark=item["remark"],
                inbound_rid=inbound_rid,
                inbound_batch_id=next_group_id,
            )
            if item["materialCategory"] == 0:
                record.material_storage_id = item["materialStorageId"]
                storage.actual_inbound_amount += Decimal(item["inboundQuantity"])
                storage.current_amount += Decimal(item["inboundQuantity"])
                if storage.actual_inbound_amount >= storage.estimated_inbound_amount:
                    storage.material_storage_status = 1
            elif item["materialCategory"] == 1:
                record.size_material_storage_id = item["materialStorageId"]

                for i, shoe_size in enumerate(SHOESIZERANGE):
                    if f"amount{i}" not in item:
                        break
                    column_name = f"size_{shoe_size}_actual_inbound_amount"
                    current_value = getattr(storage, column_name)
                    new_value = current_value + int(item[f"amount{i}"])
                    setattr(storage, column_name, new_value)
                    storage.total_actual_inbound_amount += new_value

                    column_name = f"size_{shoe_size}_current_amount"
                    current_value = getattr(storage, column_name)
                    new_value = current_value + int(item[f"amount{i}"])
                    setattr(storage, column_name, new_value)
                    storage.total_current_amount += new_value

                    column_name = f"size_{shoe_size}_inbound_amount"
                    setattr(record, column_name, int(item[f"amount{i}"]))
            db.session.add(record)
        next_group_id += 1
        counter += 1
    db.session.commit()
    return jsonify({"message": "success"})


def _find_order_shoe(order_rid):
    print(order_rid)
    entities = (
        db.session.query(Order, OrderShoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .filter(Order.order_rid == order_rid)
        .first()
    )
    if not entities:
        return None, None
    return entities.Order, entities.OrderShoe


def _find_storage_in_db(item, supplier_name, batch_info_type_id):
    """
    处理用户手动输入的材料信息
    """
    item: dict
    material_name = item.get("materialName", None)
    material = (
        db.session.query(Material)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(
            Material.material_name == material_name,
            Supplier.supplier_name == supplier_name,
        )
        .first()
    )

    material_id = material.material_id
    material_model = item.get("materialModel", "")
    material_specification = item.get("materialSpecification", "")
    material_color = item.get("materialColor", "")
    material_category = item.get("materialCategory", 0)
    material_model = "" if not material_model else material_model
    material_specification = (
        "" if not material_specification else material_specification
    )
    material_color = "" if not material_color else material_color
    order_rid: str = item.get("orderRId", None)
    order_id, order_shoe_id = None, None
    # 如果用户输入了订单号
    if order_rid:
        # trim the order_rid
        order_rid = order_rid.strip().upper()
        order, order_shoe = _find_order_shoe(order_rid)
        if not order_shoe:
            return jsonify({"message": "订单号不存在"}), 400
        order_id = order.order_id
        order_shoe_id = order_shoe.order_shoe_id

    # 普通材料
    if material_category == 0:
        storage_query = db.session.query(MaterialStorage).filter(
            MaterialStorage.material_id == material_id,
            MaterialStorage.material_specification == material_specification,
            MaterialStorage.material_model == material_model,
            MaterialStorage.material_storage_color == material_color,
        )
        if order_shoe_id:
            storage_query = storage_query.filter(
                MaterialStorage.order_shoe_id == order_shoe_id
            )
        else:
            storage_query = storage_query.filter(
                MaterialStorage.order_shoe_id.is_(None)
            )
    # 尺码材料
    elif material_category == 1:
        storage_query = db.session.query(SizeMaterialStorage).filter(
            SizeMaterialStorage.material_id == material_id,
            SizeMaterialStorage.size_material_specification
            == material_specification,
            SizeMaterialStorage.size_material_model == material_model,
            SizeMaterialStorage.size_material_color == material_color,
        )
        if order_shoe_id:
            storage_query = storage_query.filter(
                SizeMaterialStorage.order_shoe_id == order_shoe_id
            )
        else:
            storage_query = storage_query.filter(
                SizeMaterialStorage.order_shoe_id.is_(None)
            )
    # 根据材料信息查找对应的材料库存
    # 如果没有找到，则创建新的材料库存
    storage = storage_query.first()
    if not storage:
        if material_category == 0:
            storage = MaterialStorage(
                material_id=material_id,
                actual_inbound_material_id=material_id,
                material_specification=material_specification,
                material_model=material_model,
                material_storage_color=material_color,
                actual_inbound_unit=item["actualInboundUnit"],
                order_id=order_id,
                order_shoe_id=order_shoe_id,
            )
        elif material_category == 1:
            batch_info_type = db.session.query(BatchInfoType).filter(
                BatchInfoType.batch_info_type_id == batch_info_type_id
            ).first()
            shoe_size_columns = []
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
                order_id=order_id,
                order_shoe_id=order_shoe_id,
                shoe_size_columns=shoe_size_columns,
            )
        db.session.add(storage)
        db.session.flush()
    if material_category == 0:
        storage_id = storage.material_storage_id
    elif material_category == 1:
        storage_id = storage.size_material_storage_id
    return storage_id, storage


@material_storage_bp.route("/warehouse/inboundmaterial", methods=["POST"])
def inbound_material():
    data = request.get_json()
    # Determine the next available group_id
    next_group_id = (
        db.session.query(
            func.coalesce(func.max(InboundRecord.inbound_batch_id), 0)
        ).scalar()
        + 1
    )
    counter = 0
    inbound_type = data.get("inboundType", 0)
    timestamp = data.get("currentDateTime", datetime.now())
    remark = data.get("remark", None)
    items = data.get("items", [])
    formatted_timestamp = (
        timestamp.replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
    )
    inbound_rid = "IR" + formatted_timestamp + f"{counter:02}"

    supplier_name = data.get("supplierName", None)
    
    batch_info_type_id = data.get("batchInfoTypeId", None)

    supplier = (
        db.session.query(Supplier)
        .filter(Supplier.supplier_name == supplier_name)
        .first()
    )

    # create inbound record
    inbound_record = InboundRecord(
        inbound_datetime=formatted_timestamp,
        inbound_type=inbound_type,
        inbound_rid=inbound_rid,
        inbound_batch_id=next_group_id,
        supplier_id=supplier.supplier_id,
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
        # 用户手填材料
        if not storage_id:
            storage_id, storage = _find_storage_in_db(item, supplier_name, batch_info_type_id)
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
        )

        # set cost
        unit_price = Decimal(item.get("unitPrice", 0))
        if inbound_type != 2:
            storage.unit_price = unit_price
            record_detail.unit_price = unit_price
        if inbound_type == 2:
            storage.composite_unit_cost = unit_price
            record_detail.composite_unit_cost = unit_price

        total_price += unit_price * inbound_quantity

        if material_category == 0:
            inbound_record.is_sized_material = 0
            record_detail.material_storage_id = storage_id
            if inbound_type != 1:
                storage.actual_inbound_amount += inbound_quantity
            storage.current_amount += inbound_quantity
            if storage.actual_inbound_amount >= storage.estimated_inbound_amount:
                storage.material_storage_status = 1
        elif material_category == 1:
            inbound_record.is_sized_material = 1
            record_detail.size_material_storage_id = storage_id

            for i, shoe_size in enumerate(SHOESIZERANGE):
                if f"amount{i}" not in item:
                    break
                column_name = f"size_{shoe_size}_actual_inbound_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value + int(item[f"amount{i}"])
                setattr(storage, column_name, new_value)
                storage.total_actual_inbound_amount += int(item[f"amount{i}"])

                column_name = f"size_{shoe_size}_current_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value + int(item[f"amount{i}"])
                setattr(storage, column_name, new_value)
                storage.total_current_amount += int(item[f"amount{i}"])

                column_name = f"size_{shoe_size}_inbound_amount"
                setattr(record_detail, column_name, int(item[f"amount{i}"]))
        db.session.add(record_detail)
    inbound_record.total_price = total_price

    # 财务
    code = material_inbound_accounting_event(supplier_name, total_price, inbound_record.inbound_record_id)
    # create payee if not exist
    if code == 1:
        payable_entity_code = add_payable_entity(supplier_name)
        if payable_entity_code == 0:
            material_inbound_accounting_event(supplier_name, total_price, inbound_record.inbound_record_id)
    elif code == 2:
        return jsonify(
            {"message": "payable entity not exist"}, 400
        )
    db.session.commit()
    return jsonify({"message": "success", "inboundRId": inbound_rid})


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


def _create_composite_materials(new_material_list):
    columns = ", ".join(new_material_list[0].keys())
    values_placeholder = ", ".join([f":{key}" for key in new_material_list[0].keys()])
    table_name = "jiancheng.material"
    sql = text(
        f"""INSERT IGNORE INTO {table_name} ({columns}) VALUES ({values_placeholder})"""
    )
    db.session.execute(sql, new_material_list)

    # create material storage for new composite material
    composite_keys = [
        (row["material_supplier"], row["material_name"]) for row in new_material_list
    ]
    id_query = text(
        f"""
        SELECT material.material_id, material.material_name FROM {table_name} WHERE (material_supplier, material_name) IN :composite_keys;
    """
    )
    # Execute the query to fetch the IDs
    result = db.session.execute(id_query, {"composite_keys": composite_keys}).fetchall()
    return result


def process_composite_materials(composite_material_list):
    new_material_list = []
    storage_id_list = [row["materialStorageId"] for row in composite_material_list]
    # 原材料仓库
    response = (
        db.session.query(MaterialStorage, Material)
        .join(Material, Material.material_id == MaterialStorage.material_id)
        .filter(MaterialStorage.material_storage_id.in_(storage_id_list))
        .all()
    )
    storage_material_cache = {}
    for row in response:
        storage, material = row
        if not storage.craft_name:
            return None
        storage_material_cache[storage.material_storage_id] = {
            "storage": storage,
            "material": material,
        }
    storage_mapping = {}
    for row in composite_material_list:
        for composite in row["craftNameList"]:
            storage = storage_material_cache[row["materialStorageId"]]["storage"]
            material = storage_material_cache[row["materialStorageId"]]["material"]
            if composite["outboundQuantity"] > 0:
                composite_material_name = (
                    material.material_name + composite["craftName"]
                )
                new_material = Material(
                    material_name=composite_material_name,
                    material_type_id=9,
                    material_unit=material.material_unit,
                    material_supplier=row["compositeSupplierId"],
                    material_creation_date=date.today(),
                    material_category=material.material_category,
                )
                new_material_list.append(new_material.to_dict())
                storage_mapping[composite_material_name] = [
                    storage,
                    composite["outboundQuantity"],
                    row,
                ]
    composite_storage_result = []
    if len(new_material_list) > 0:
        material_result = _create_composite_materials(new_material_list)
        new_storage_list = []
        for material_id, material_name in material_result:
            storage = storage_mapping[material_name][0]
            existed_storage = (
                db.session.query(MaterialStorage)
                .filter_by(
                    order_shoe_id=storage.order_shoe_id,
                    material_id=material_id,
                    material_specification=storage.material_specification,
                    material_model=storage.material_model,
                    material_storage_color=storage.material_storage_color,
                )
                .first()
            )
            if existed_storage:
                existed_storage.estimated_inbound_amount += storage_mapping[
                    material_name
                ][1]
                composite_storage_result.append(
                    (
                        existed_storage,
                        storage_mapping[material_name][1],
                        storage_mapping[material_name][2],
                    )
                )
            else:
                new_storage = MaterialStorage(
                    order_shoe_id=storage.order_shoe_id,
                    material_id=material_id,
                    estimated_inbound_amount=storage_mapping[material_name][1],
                    material_specification=storage.material_specification,
                    material_model=storage.material_model,
                    material_storage_color=storage.material_storage_color,
                    material_storage_status=0,
                )
                new_storage_list.append(new_storage)
                composite_storage_result.append(
                    (
                        new_storage,
                        storage_mapping[material_name][1],
                        storage_mapping[material_name][2],
                    )
                )
        db.session.add_all(new_storage_list)
        db.session.flush()
    return composite_storage_result


@material_storage_bp.route(
    "/warehouse/warehousemanager/outboundmaterial", methods=["PATCH"]
)
def outbound_material():
    data = request.get_json()
    composite_material_rows = []
    record_list = []
    # Determine the next available group_id
    next_group_id = (
        db.session.query(
            func.coalesce(func.max(OutboundRecord.outbound_batch_id), 0)
        ).scalar()
        + 1
    )
    for outbound_row in data:
        outbound_row: dict
        # get parameters from outbound row
        # could be material or size material storage
        outbound_timestamp = outbound_row.get("outboundTimestamp", None)
        formatted_timestamp = (
            outbound_timestamp.replace("-", "").replace(" ", "").replace(":", "")
        )
        outbound_type = outbound_row.get("outboundType", None)
        outbound_department = outbound_row.get("outboundDepartment", None)
        outbound_address = outbound_row.get("outboundAddress", None)
        picker = outbound_row.get("picker", None)
        order_shoe_id = outbound_row.get("orderShoeId", None)
        outsource_info_id = outbound_row.get("outsourceInfoId", None)
        composite_supplier_id = outbound_row.get("compositeSupplierId", None)

        counter = 0
        # handle non-sized items
        for item in outbound_row["nonSizedItems"]:
            outbound_rid = "NOR" + formatted_timestamp + "C" + str(counter)

            material_storage_id = item.get("materialStorageId", None)
            outbound_quantity = item.get("outboundQuantity", None)
            remark = item.get("remark", None)
            size_material_outbound_list = item.get("sizeMaterialOutboundList", None)
            craft_name_list = item.get("craftNameList", None)
            material_category = item.get("materialCategory", None)
            if not outbound_quantity or outbound_quantity == 0:
                continue
            storage = MaterialStorage.query.get(material_storage_id)
            if not storage:
                return jsonify({"message": "invalid storage id"}), 400

            record = OutboundRecord(
                outbound_rid=outbound_rid,
                outbound_datetime=outbound_timestamp,
                outbound_type=outbound_type,
                outbound_amount=outbound_quantity,
                order_shoe_id=order_shoe_id,
                outbound_batch_id=next_group_id,
                remark=remark,
            )
            if storage.current_amount < outbound_quantity:
                return jsonify({"message": "invalid outbound amount"}), 400

            record.material_storage_id = material_storage_id
            storage.current_amount -= Decimal(outbound_quantity)

            if outbound_type == 0:
                record.outbound_department = outbound_department
                record.picker = picker
                record_list.append(record)

            elif outbound_type == 1:
                record_list.append(record)

            elif outbound_type == 2:
                record.outbound_address = outbound_address
                record.outsource_info_id = outsource_info_id
                record_list.append(record)

            elif outbound_type == 3:
                # 新增复合材料
                if len(craft_name_list) == 0:
                    return jsonify({"message": "该材料无复合工艺"}), 400
                composite_material_rows.append(
                    {
                        "materialStorageId": material_storage_id,
                        "craftNameList": craft_name_list,
                        "compositeSupplierId": composite_supplier_id,
                    }
                )
        # handle composite material
        if len(composite_material_rows) > 0:
            composite_storage_result = process_composite_materials(
                composite_material_rows
            )
            # add record to db
            for (
                composite_storage,
                outbound_amount,
                outbound_row,
            ) in composite_storage_result:
                record = OutboundRecord(
                    outbound_rid=outbound_rid,
                    outbound_amount=outbound_amount,
                    outbound_datetime=outbound_timestamp,
                    outbound_type=3,
                    outbound_address=outbound_address,
                    composite_supplier_id=composite_supplier_id,
                    material_storage_id=composite_storage.material_storage_id,
                    remark=remark,
                    order_shoe_id=order_shoe_id,
                    outbound_batch_id=next_group_id,
                )
                record_list.append(record)
                # print(vars(record))

        # handle size material
        for size_type_id, items in outbound_row["sizedItems"].items():
            counter += 1
            next_group_id += 1
            for item in items:
                outbound_rid = (
                    "SOR"
                    + formatted_timestamp
                    + "C"
                    + str(counter)
                    + "T"
                    + size_type_id
                )
                material_storage_id = item.get("materialStorageId", None)
                outbound_quantity = item.get("outboundQuantity", None)
                remark = item.get("remark", None)
                size_material_outbound_list = item.get("sizeMaterialOutboundList", None)
                craft_name_list = item.get("craftNameList", None)
                material_category = item.get("materialCategory", None)
                if outbound_quantity == 0:
                    continue

                storage = SizeMaterialStorage.query.get(material_storage_id)
                if not storage:
                    return jsonify({"message": "invalid storage id"}), 400

                record = OutboundRecord(
                    outbound_rid=outbound_rid,
                    outbound_datetime=outbound_timestamp,
                    outbound_type=outbound_type,
                    outbound_amount=outbound_quantity,
                    order_shoe_id=order_shoe_id,
                    outbound_batch_id=next_group_id,
                    remark=remark,
                )

                if storage.total_current_amount < outbound_quantity:
                    return jsonify({"message": "invalid outbound amount"}), 400

                record.size_material_storage_id = material_storage_id

                # update size material storage
                for i, amount in enumerate(size_material_outbound_list):
                    column_name = f"size_{i + 34}_current_amount"
                    current_value = getattr(storage, column_name)
                    new_value = current_value - amount
                    setattr(storage, column_name, new_value)

                # update total current amount
                storage.total_current_amount -= sum(size_material_outbound_list)

                # add shoe size amount to record
                for i, amount in enumerate(size_material_outbound_list):
                    column_name = f"size_{i + 34}_outbound_amount"
                    setattr(record, column_name, amount)

                if outbound_type == 0:
                    record.outbound_department = outbound_department
                    record.picker = picker
                    record_list.append(record)

                elif outbound_type == 1:
                    record_list.append(record)

                elif outbound_type == 2:
                    record.outbound_address = outbound_address
                    record.outsource_info_id = outsource_info_id
                    record_list.append(record)

        db.session.add_all(record_list)
        next_group_id += 1
    db.session.commit()
    return jsonify({"message": "success"})


@material_storage_bp.route("/warehouse/getmaterialinboundrecords", methods=["GET"])
def get_material_inbound_records():
    start_date_search = request.args.get("startDate")
    end_date_search = request.args.get("endDate")
    page = int(request.args.get("page", 1))
    number = int(request.args.get("pageSize", 10))
    inbound_rid = request.args.get("inboundRId")

    query1 = db.session.query(InboundRecord, Supplier).join(
        Supplier,
        Supplier.supplier_id == InboundRecord.supplier_id,
    )
    if start_date_search:
        query1 = query1.filter(InboundRecord.inbound_datetime >= start_date_search)
    if end_date_search:
        query1 = query1.filter(InboundRecord.inbound_datetime <= end_date_search)
    if inbound_rid:
        query1 = query1.filter(InboundRecord.inbound_rid.ilike(f"%{inbound_rid}%"))

    query1 = query1.order_by(desc(InboundRecord.inbound_datetime))
    count_result = query1.distinct().count()
    response = query1.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        inbound_record, supplier = row
        obj = {
            "timestamp": format_datetime(inbound_record.inbound_datetime),
            "inboundType": inbound_record.inbound_type,
            "inboundBatchId": inbound_record.inbound_batch_id,
            "inboundRId": inbound_record.inbound_rid,
            "isSizedMaterial": inbound_record.is_sized_material,
            "supplierName": supplier.supplier_name,
            "payMethod": inbound_record.pay_method,
            "remark": inbound_record.remark,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route("/warehouse/getinboundrecordbybatchid", methods=["GET"])
def get_inbound_record_by_batch_id():
    inbound_batch_id = request.args.get("inboundBatchId")
    is_sized_material = request.args.get("isSizedMaterial", type=int)
    if is_sized_material == 0:
        inbound_response = (
            db.session.query(
                InboundRecord, 
                InboundRecordDetail, 
                MaterialStorage.material_storage_id,
                MaterialStorage.material_model,
                MaterialStorage.material_specification,
                MaterialStorage.material_storage_color,
                literal(None).label("shoe_size_columns"),
                Material,
                Supplier,
                Order,
            )
            .join(InboundRecordDetail, InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id)
            .join(
                MaterialStorage,
                InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id
            )
            .join(Material, Material.material_id == MaterialStorage.actual_inbound_material_id)
            .outerjoin(
                Supplier, Supplier.supplier_id == InboundRecord.supplier_id
            )
            .outerjoin(
                Order,
                Order.order_id == MaterialStorage.order_id,
            )
            .filter(
                InboundRecord.inbound_batch_id == inbound_batch_id,
            )
            .all()
        )
    else:
        inbound_response = (
            db.session.query(
                InboundRecord, 
                InboundRecordDetail, 
                SizeMaterialStorage.size_material_storage_id,
                SizeMaterialStorage.size_material_model,
                SizeMaterialStorage.size_material_specification,
                SizeMaterialStorage.size_material_color,
                SizeMaterialStorage.shoe_size_columns,
                Material,
                Supplier,
                Order,
            )
            .join(InboundRecordDetail, InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id)
            .join(
                SizeMaterialStorage,
                InboundRecordDetail.size_material_storage_id == SizeMaterialStorage.size_material_storage_id
            )
            .join(Material, Material.material_id == SizeMaterialStorage.material_id)
            .outerjoin(
                Supplier, Supplier.supplier_id == InboundRecord.supplier_id
            )
            .outerjoin(
                Order,
                Order.order_id == SizeMaterialStorage.order_id,
            )
            .filter(
                InboundRecord.inbound_batch_id == inbound_batch_id,
            )
            .all()
        )

    if not inbound_response:
        return jsonify({"message": "record not found"}), 404
    result = []
    for row in inbound_response:
        (
            record_meta,
            record_detail,
            material_storage_id,
            material_model,
            material_specification,
            material_storage_color,
            shoe_size_columns,
            material,
            supplier,
            order,
        ) = row
        obj = {
            "timestamp": record_meta.inbound_datetime,
            "inboundRId": record_meta.inbound_rid,
            "inboundRecordId": record_meta.inbound_record_id,
            "inboundType": record_meta.inbound_type,
            "batchId": record_meta.inbound_batch_id,
            "inboundQuantity": record_detail.inbound_amount,
            "unitPrice": record_detail.unit_price,
            "compositeUnitCost": record_detail.composite_unit_cost,
            "metaRemark": record_meta.remark,
            "remark": record_detail.remark,
            "materialName": material.material_name,
            "materialModel": material_model,
            "materialSpecification": material_specification,
            "colorName": material_storage_color,
            "materialUnit": material.material_unit,
            "materialStorageId": material_storage_id,
            "actualInboundUnit": material.material_unit,
            "orderRId": order.order_rid if order else None,
            "supplierName": supplier.supplier_name if supplier else None,
            "shoeSizeColumns": shoe_size_columns,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_inbound_amount"
            obj[f"amount{i}"] = getattr(record_detail, column_name, None)
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
        db.session.query(
            OutboundRecord.outbound_batch_id,
            OutboundRecord.outbound_datetime,
            OutboundRecord.outbound_type,
            OutboundRecord.outbound_rid,
            Department.department_name,
            OutboundRecord.outbound_address,
            OutboundRecord.picker,
            Supplier.supplier_name,
            Order.order_id,
            Order.order_rid,
            Shoe.shoe_rid,
            OutsourceFactory.factory_name,
        )
        .join(
            OrderShoe,
            OutboundRecord.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(
            Order,
            OrderShoe.order_id == Order.order_id,
        )
        .join(
            Shoe,
            OrderShoe.shoe_id == Shoe.shoe_id,
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
            OutboundRecord.composite_supplier_id == Supplier.supplier_id,
        )
        .distinct(OutboundRecord.outbound_batch_id)
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
            outbound_batch_id,
            outbound_datetime,
            outbound_type,
            outbound_rid,
            department_name,
            outbound_address,
            picker,
            supplier_name,
            order_id,
            order_rid,
            shoe_rid,
            factory_name,
        ) = row
        obj = {
            "outboundBatchId": outbound_batch_id,
            "timestamp": format_datetime(outbound_datetime),
            "outboundType": outbound_type,
            "outboundRId": outbound_rid,
            "outboundDepartment": department_name,
            "outboundAddress": outbound_address,
            "picker": picker,
            "compositeSupplierName": supplier_name,
            "orderId": order_id,
            "orderRId": order_rid,
            "shoeRId": shoe_rid,
            "outsourceFactoryName": factory_name,
        }
        result.append(obj)
    return {"result": result, "total": count_result}


@material_storage_bp.route("/warehouse/getoutboundrecordbybatchid", methods=["GET"])
def get_outbound_record_by_batch_id():

    def add_response_to_result(response):
        result = []
        for row in response:
            (
                record,
                material,
                material_storage_id,
                material_model,
                material_specification,
                material_storage_color,
                actual_inbound_unit,
                supplier,
            ) = row
            obj = {
                "timestamp": record.outbound_datetime,
                "outboundRId": record.outbound_rid,
                "outboundRecordId": record.outbound_record_id,
                "outboundType": record.outbound_type,
                "batchId": record.outbound_batch_id,
                "outboundQuantity": record.outbound_amount,
                "recordDatetime": record.outbound_datetime,
                "remark": record.remark,
                "materialName": material.material_name,
                "materialModel": material_model,
                "materialSpecification": material_specification,
                "colorName": material_storage_color,
                "materialUnit": material.material_unit,
                "actualInboundUnit": actual_inbound_unit,
                "materialStorageId": material_storage_id,
                "supplierName": supplier.supplier_name,
            }
            for i in range(len(SHOESIZERANGE)):
                shoe_size = SHOESIZERANGE[i]
                column_name = f"size_{shoe_size}_outbound_amount"
                obj[f"amount{i}"] = getattr(record, column_name)
            result.append(obj)
        return result

    outbound_batch_id = request.args.get("outboundBatchId", None)
    outbound_rid = request.args.get("outboundRId", None)
    material_category = request.args.get("materialCategory", 0, type=int)
    response = None
    # extract shoe size columns from outbound rid
    shoe_size_columns = []
    if material_category == 0:
        response = (
            db.session.query(
                OutboundRecord,
                Material,
                MaterialStorage.material_storage_id.label("material_storage_id"),
                MaterialStorage.material_model.label("material_model"),
                MaterialStorage.material_specification.label("material_specification"),
                MaterialStorage.material_storage_color.label("material_storage_color"),
                MaterialStorage.actual_inbound_unit,
                Supplier,
            )
            .join(
                MaterialStorage,
                OutboundRecord.material_storage_id
                == MaterialStorage.material_storage_id,
            )
            .join(Material, Material.material_id == MaterialStorage.material_id)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                OutboundRecord.outbound_batch_id == outbound_batch_id,
                OutboundRecord.outbound_rid.ilike("N%"),
            )
            .all()
        )
    else:
        response = (
            db.session.query(
                OutboundRecord,
                Material,
                SizeMaterialStorage.size_material_storage_id.label(
                    "material_storage_id"
                ),
                SizeMaterialStorage.size_material_model.label("material_model"),
                SizeMaterialStorage.size_material_specification.label(
                    "material_specification"
                ),
                SizeMaterialStorage.size_material_color.label("material_storage_color"),
                literal("双").label("actual_inbound_unit"),
                Supplier,
            )
            .join(
                SizeMaterialStorage,
                OutboundRecord.size_material_storage_id
                == SizeMaterialStorage.size_material_storage_id,
            )
            .join(Material, Material.material_id == SizeMaterialStorage.material_id)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                OutboundRecord.outbound_batch_id == outbound_batch_id,
                OutboundRecord.outbound_rid.ilike("S%"),
            )
            .all()
        )
        if outbound_rid and outbound_rid.find("T") != -1:
            batch_info_type_id = outbound_rid[outbound_rid.find("T") + 1 :]
            size_name_response = (
                db.session.query(BatchInfoType)
                .filter(BatchInfoType.batch_info_type_id == batch_info_type_id)
                .first()
            )
            for i in range(len(SHOESIZERANGE)):
                shoe_size = SHOESIZERANGE[i]
                size_name_column = f"size_{shoe_size}_name"
                value = getattr(size_name_response, size_name_column)
                if not value:
                    break
                shoe_size_columns.append(value)

    result = {"material": [], "sizeMaterial": [], "shoeSizeColumns": []}
    if material_category == 0:
        result["material"] = add_response_to_result(response)
    else:
        result["sizeMaterial"] = add_response_to_result(response)
        resulted_filtered_columns = []
        for i in range(len(shoe_size_columns)):
            resulted_filtered_columns.append(
                {"label": shoe_size_columns[i], "prop": f"amount{i}"}
            )
        result["shoeSizeColumns"] = resulted_filtered_columns
    print(result)
    return result


@material_storage_bp.route("/warehouse/getinboundrecordsformaterial", methods=["GET"])
def get_inbound_records_for_material():
    storage_id = request.args.get("storageId")
    response = (
        db.session.query(InboundRecord)
        .filter(InboundRecord.material_storage_id == storage_id)
        .order_by(desc(InboundRecord.inbound_datetime))
        .all()
    )
    result = []
    for row in response:
        if row.inbound_type == 1:
            inbound_purpose = "生产剩余"
        elif row.inbound_type == 2:
            inbound_purpose = "复合入库"
        else:
            inbound_purpose = "采购入库"
        obj = {
            "inboundRId": row.inbound_rid,
            "timestamp": format_datetime(row.inbound_datetime),
            "inboundType": inbound_purpose,
            "inboundAmount": row.inbound_amount,
            "remark": row.remark,
        }
        result.append(obj)
    return result


@material_storage_bp.route(
    "/warehouse/getinboundrecordsforsizematerial", methods=["GET"]
)
def get_inbound_records_for_size_material():
    storage_id = request.args.get("storageId")
    response = (
        db.session.query(InboundRecord)
        .filter(InboundRecord.size_material_storage_id == storage_id)
        .order_by(desc(InboundRecord.inbound_datetime))
        .all()
    )
    result = []
    for row in response:
        if row.inbound_type == 1:
            inbound_purpose = "生产剩余"
        elif row.inbound_type == 2:
            inbound_purpose = "复合入库"
        else:
            inbound_purpose = "采购入库"
        obj = {
            "inboundRId": row.inbound_rid,
            "timestamp": format_datetime(row.inbound_datetime),
            "inboundType": inbound_purpose,
            "inboundAmount": row.inbound_amount,
            "remark": row.remark,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_inbound_amount"
            obj[f"amount{i}"] = getattr(row, column_name)
        result.append(obj)
    return result


@material_storage_bp.route("/warehouse/getoutboundrecordsformaterial", methods=["GET"])
def get_outbound_records_for_material():
    storage_id = request.args.get("storageId")
    response = (
        db.session.query(OutboundRecord)
        .filter(OutboundRecord.material_storage_id == storage_id)
        .order_by(desc(OutboundRecord.outbound_datetime))
        .all()
    )
    result = []
    for row in response:
        outbound_destination = ""
        outbound_address = ""
        if row.outbound_type == 1:
            outbound_purpose = "废料处理"
        elif row.outbound_type == 2:
            outbound_purpose = "外包发货"
            outbound_destination = (
                db.session.query(OutsourceFactory.factory_id)
                .join(
                    OutsourceInfo,
                    OutsourceInfo.factory_id == OutsourceFactory.factory_id,
                )
                .filter(OutsourceInfo.outsource_info_id == row.outsource_info_id)
                .scalar()
            )
            outbound_address = row.outbound_address
        elif row.outbound_type == 3:
            outbound_purpose = "外发复合"
            outbound_destination = (
                db.session.query(Supplier.supplier_name)
                .filter(Supplier.supplier_id == row.composite_supplier_id)
                .scalar()
            )
            outbound_address = row.outbound_address
        else:
            outbound_purpose = "生产使用"
            outbound_destination = (
                db.session.query(Department.department_name)
                .filter(Department.department_id == row.outbound_department)
                .scalar()
            )
        obj = {
            "outboundRId": row.outbound_rid,
            "timestamp": format_datetime(row.outbound_datetime),
            "outboundType": outbound_purpose,
            "outboundAmount": row.outbound_amount,
            "remark": row.remark,
            "outboundDestination": outbound_destination,
            "picker": row.picker,
            "outboundAddress": outbound_address,
        }
        result.append(obj)
    return result


@material_storage_bp.route(
    "/warehouse/getoutboundrecordsforsizematerial", methods=["GET"]
)
def get_outbound_records_for_size_material():
    storage_id = request.args.get("storageId")
    response = (
        db.session.query(OutboundRecord)
        .filter(OutboundRecord.size_material_storage_id == storage_id)
        .order_by(desc(OutboundRecord.outbound_datetime))
        .all()
    )
    result = []
    for row in response:
        outbound_destination = ""
        outbound_address = ""
        if row.outbound_type == 1:
            outbound_purpose = "废料处理"
        # elif row.outbound_type == 2:
        #     outbound_purpose = "外包发货"
        #     outbound_destination = db.session.query(Outsouce
        elif row.outbound_type == 3:
            outbound_purpose = "外发复合"
            outbound_destination = (
                db.session.query(Supplier.supplier_name)
                .filter(Supplier.supplier_id == row.composite_supplier_id)
                .scalar()
            )
            outbound_address = row.outbound_address
        else:
            outbound_purpose = "生产使用"
            outbound_destination = (
                db.session.query(Department.department_name)
                .filter(Department.department_id == row.outbound_department)
                .scalar()
            )
        obj = {
            "outboundRId": row.outbound_rid,
            "timestamp": format_datetime(row.outbound_datetime),
            "outboundType": outbound_purpose,
            "outboundAmount": row.outbound_amount,
            "remark": row.remark,
            "outboundDestination": outbound_destination,
            "picker": row.picker,
            "outboundAddress": outbound_address,
        }
        for i in range(len(SHOESIZERANGE)):
            shoe_size = SHOESIZERANGE[i]
            column_name = f"size_{shoe_size}_outbound_amount"
            obj[f"amount{i}"] = getattr(row, column_name)
        result.append(obj)
    return result


@material_storage_bp.route(
    "/warehouse/warehousemanager/getmaterialinoutboundrecords", methods=["GET"]
)
def get_material_in_out_bound_records():
    storage_id = request.args.get("storageId")
    name = request.args.get("storageName")
    if name == "material":
        inbound_response = InboundRecord.query.filter(
            InboundRecord.material_storage_id == storage_id
        ).all()
        outbound_response = OutboundRecord.query.filter(
            OutboundRecord.material_storage_id == storage_id
        ).all()
    elif name == "sizeMaterial":
        inbound_response = InboundRecord.query.filter(
            InboundRecord.size_material_storage_id == storage_id
        ).all()
        outbound_response = OutboundRecord.query.filter(
            OutboundRecord.size_material_storage_id == storage_id
        ).all()
    else:
        return jsonify({"message": "failed"}), 400

    result = []
    for row in inbound_response:
        if row.inbound_type == 1:
            inbound_purpose = "生产剩余"
        elif row.inbound_type == 2:
            inbound_purpose = "复合入库"
        else:
            inbound_purpose = "采购入库"
        obj = {
            "operation": "入库",
            "purpose": inbound_purpose,
            "date": row.inbound_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if name == "sizeMaterial":
            for shoe_size in SHOESIZERANGE:
                column_name = f"size_{shoe_size}_inbound_amount"
                obj[f"size{shoe_size}Amount"] = getattr(row, column_name)
        else:
            obj["amount"] = row.inbound_amount
        result.append(obj)

    for row in outbound_response:
        if row.outbound_type == 1:
            outbound_purpose = "废料处理"
        elif row.outbound_type == 2:
            outbound_purpose = "外包发货"
        elif row.outbound_type == 3:
            outbound_purpose = "外发复合"
        else:
            outbound_purpose = "生产使用"
        obj = {
            "operation": "出库",
            "purpose": outbound_purpose,
            "date": row.outbound_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if name == "sizeMaterial":
            for shoe_size in SHOESIZERANGE:
                column_name = f"size_{shoe_size}_outbound_amount"
                obj[f"size{shoe_size}Amount"] = getattr(row, column_name)
        else:
            obj["amount"] = row.outbound_amount
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

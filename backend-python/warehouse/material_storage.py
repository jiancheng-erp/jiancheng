from datetime import datetime, date
from decimal import Decimal

from api_utility import format_date
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
        "supplier": request.args.get("supplier", ""),
        "order_rid": request.args.get("orderRId", ""),
        "shoe_rid": request.args.get("shoeRId", ""),
        "purchase_divide_order_rid": request.args.get("purchaseDivideOrderRId", ""),
    }
    material_filter_map = {
        "material_type_name": MaterialType.material_type_name,
        "material_name": Material.material_name,
        "material_spec": MaterialStorage.material_specification,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
        "shoe_rid": Shoe.shoe_rid,
        "purchase_divide_order_rid": PurchaseDivideOrder.purchase_divide_order_rid,
    }
    size_material_filter_map = {
        "material_type_name": MaterialType.material_type_name,
        "material_name": Material.material_name,
        "material_spec": SizeMaterialStorage.size_material_specification,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
        "shoe_rid": Shoe.shoe_rid,
        "purchase_divide_order_rid": PurchaseDivideOrder.purchase_divide_order_rid,
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
            Material.material_name,
            Material.material_unit,
            MaterialType.material_type_name,
            Material.material_category,
            Supplier.supplier_name,
            PurchaseDivideOrder.purchase_divide_order_id,
            PurchaseDivideOrder.purchase_divide_order_rid,
            PurchaseDivideOrder.purchase_divide_order_type,
            PurchaseOrder.purchase_order_issue_date,
            MaterialStorage.material_storage_color,
            MaterialStorage.craft_name,
            MaterialStorage.composite_unit_cost,
        )
        .join(Material, Material.material_id == MaterialStorage.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(
            PurchaseDivideOrder,
            PurchaseDivideOrder.purchase_divide_order_id
            == MaterialStorage.purchase_divide_order_id,
        )
        .outerjoin(
            PurchaseOrder,
            PurchaseOrder.purchase_order_id == PurchaseDivideOrder.purchase_order_id,
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
            Material.material_name,
            Material.material_unit,
            MaterialType.material_type_name,
            Material.material_category,
            Supplier.supplier_name,
            PurchaseDivideOrder.purchase_divide_order_id,
            PurchaseDivideOrder.purchase_divide_order_rid,
            PurchaseDivideOrder.purchase_divide_order_type,
            PurchaseOrder.purchase_order_issue_date,
            SizeMaterialStorage.size_material_color,
            SizeMaterialStorage.craft_name,
            SizeMaterialStorage.composite_unit_cost,
        )
        .join(Material, Material.material_id == SizeMaterialStorage.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(
            PurchaseDivideOrder,
            PurchaseDivideOrder.purchase_divide_order_id
            == SizeMaterialStorage.purchase_divide_order_id,
        )
        .outerjoin(
            PurchaseOrder,
            PurchaseOrder.purchase_order_id == PurchaseDivideOrder.purchase_order_id,
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
            material_name,
            material_unit,
            material_type_name,
            material_category,
            supplier_name,
            purchase_divide_order_id,
            purchase_divide_order_rid,
            purchase_divide_order_type,
            purchase_order_issue_date,
            color,
            craft_name,
            composite_unit_cost,
            *size_columns,
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
            "materialType": material_type_name,
            "materialName": material_name,
            "materialSpecification": material_specification,
            "materialUnit": material_unit,
            "materialCategory": material_category,
            "estimatedInboundAmount": estimated_inbound_amount,
            "actualInboundAmount": actual_inbound_amount,
            "currentAmount": current_amount,
            "unitPrice": unit_price,
            "totalPrice": (
                0 if not unit_price else round(estimated_inbound_amount * unit_price, 2)
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
            "purchaseDivideOrderId": purchase_divide_order_id,
            "purchaseDivideOrderRId": purchase_divide_order_rid,
            "purchaseDivideOrderType": purchase_divide_order_type,
            "purchaseOrderIssueDate": format_date(purchase_order_issue_date),
            "materialModel": material_model,
            "craftName": craft_name,
            "compositeUnitCost": composite_unit_cost,
            "compositeTotalPrice": (
                0
                if not composite_unit_cost
                else round(estimated_inbound_amount * composite_unit_cost, 2)
            ),
            "sizeMaterialEstimatedInboundAmount": [],
            "sizeMaterialActualInboundAmount": [],
            "sizeMaterialCurrentAmount": [],
        }
        result.append(obj)
    return {"result": result, "total": count_result}


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
    id = request.args.get("sizeMaterialStorageId")
    order_id = request.args.get("orderId")
    purchase_divide_order_id = request.args.get("purchaseDivideOrderId")
    storage = SizeMaterialStorage.query.get(id)
    result = []
    if order_id:
        # get shoe size name
        shoe_size_names = get_order_batch_type_helper(order_id)
    else:
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
        shoe_size_names = []
        for i in range(34, 47):
            locale = getattr(batch_info_type, f"size_{i}_name")
            type_name = getattr(batch_info_type, f"batch_info_type_name")
            if locale:
                obj = {"label": locale, "type": type_name}
                shoe_size_names.append(obj)
            if locale == None:
                break
    for i, shoe_size in enumerate(shoe_size_names):
        shoe_size_db_name = i + 34
        obj = {
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
    "/warehouse/warehousemanager/inboundmaterial", methods=["PATCH"]
)
def inbound_material():
    data = request.get_json()
    for inbound_row in data:
        # material storage
        if inbound_row["materialCategory"] == 0:
            storage = MaterialStorage.query.get(inbound_row["materialStorageId"])
        elif inbound_row["materialCategory"] == 1:
            storage = SizeMaterialStorage.query.get(inbound_row["materialStorageId"])

        # set cost
        if inbound_row["inboundType"] != 2:
            storage.unit_price = inbound_row["unitPrice"]
        if inbound_row["inboundType"] == 2:
            storage.composite_unit_cost = inbound_row["compositeUnitCost"]

        # set inbound quantity
        record = InboundRecord(
            inbound_amount=Decimal(inbound_row["inboundQuantity"]),
            inbound_datetime=inbound_row["inboundTimestamp"],
            inbound_type=inbound_row["inboundType"],
            remark=inbound_row["remark"],
        )
        if inbound_row["materialCategory"] == 0:
            record.material_storage_id = inbound_row["materialStorageId"]
            storage.actual_inbound_amount += Decimal(inbound_row["inboundQuantity"])
            storage.current_amount += Decimal(inbound_row["inboundQuantity"])
            if storage.actual_inbound_amount >= storage.estimated_inbound_amount:
                storage.material_storage_status = 1
        elif inbound_row["materialCategory"] == 1:
            record.size_material_storage_id = inbound_row["materialStorageId"]
            storage.total_actual_inbound_amount += Decimal(
                inbound_row["inboundQuantity"]
            )
            storage.total_current_amount += Decimal(inbound_row["inboundQuantity"])

            for i, shoe_size in enumerate(SHOESIZERANGE):
                column_name = f"size_{shoe_size}_actual_inbound_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value + int(inbound_row[f"amount{i}"])
                setattr(storage, column_name, new_value)
                storage.total_actual_inbound_amount += new_value

                column_name = f"size_{shoe_size}_current_amount"
                current_value = getattr(storage, column_name)
                new_value = current_value + int(inbound_row[f"amount{i}"])
                setattr(storage, column_name, new_value)
                storage.total_current_amount += new_value

                column_name = f"size_{shoe_size}_inbound_amount"
                setattr(record, column_name, int(inbound_row[f"amount{i}"]))
        db.session.add(record)
        db.session.flush()
        rid = (
            "IR"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + str(record.inbound_record_id)
        )
        record.inbound_rid = rid
    db.session.commit()
    return jsonify({"message": "success"})


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


@material_storage_bp.route(
    "/warehouse/warehousemanager/inboundsizematerial", methods=["PATCH"]
)
def inbound_size_material():
    data = request.get_json()
    storage = SizeMaterialStorage.query.get(data["sizeMaterialStorageId"])
    storage.total_actual_inbound_amount = 0
    storage.total_current_amount = 0

    if data["inboundType"] != 2:
        storage.unit_price = data["unitPrice"]
    if data["inboundType"] == 2:
        storage.composite_unit_cost = data["compositeUnitCost"]

    for i, shoe_size in enumerate(SHOESIZERANGE):
        # actual inbound amount
        column_name = f"size_{shoe_size}_actual_inbound_amount"
        current_value = getattr(storage, column_name)
        new_value = current_value + int(data[f"size{i}Amount"])
        setattr(storage, column_name, new_value)
        storage.total_actual_inbound_amount += new_value

        # current_amount
        column_name = f"size_{shoe_size}_current_amount"
        current_value = getattr(storage, column_name)
        new_value = current_value + int(data[f"size{i}Amount"])
        setattr(storage, column_name, new_value)
        storage.total_current_amount += new_value

    flag = True
    for shoe_size in SHOESIZERANGE:
        if getattr(storage, f"size_{shoe_size}_estimated_inbound_amount") > getattr(
            storage, f"size_{shoe_size}_actual_inbound_amount"
        ):
            flag = False
    if flag:
        storage.material_storage_status = 1

    record = InboundRecord(
        inbound_datetime=data["date"],
        inbound_type=data["inboundType"],
        size_material_storage_id=data["sizeMaterialStorageId"],
    )
    for shoe_size in SHOESIZERANGE:
        column_name = f"size_{shoe_size}_inbound_amount"
        setattr(record, column_name, int(data[f"size{i}Amount"]))
    db.session.add(record)
    db.session.flush()
    rid = "IR" + datetime.now().strftime("%Y%m%d%H%M%S") + str(record.inbound_record_id)
    record.inbound_rid = rid
    db.session.commit()
    return jsonify({"message": "success"})


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


def _create_new_material_storage(new_storage_list):
    columns = ", ".join(new_storage_list[0].keys())
    values_placeholder = ", ".join([f":{key}" for key in new_storage_list[0].keys()])
    table_name = "jiancheng.material_storage"
    sql = text(
        f"""INSERT IGNORE INTO {table_name} ({columns}) VALUES ({values_placeholder})"""
    )
    db.session.execute(sql, new_storage_list)


def outbound_composite_materials(material_outbound_list, supplier_id):
    new_material_list = []
    print(material_outbound_list)
    storage_id_list = [row["storageId"] for row in material_outbound_list]
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
            return False
        storage_material_cache[storage.material_storage_id] = {
            "storage": storage,
            "material": material,
        }
    storage_mapping = {}

    print(storage_material_cache)
    for row in material_outbound_list:
        print(row)
        for composite in row["craftNameList"]:
            storage = storage_material_cache[row["storageId"]]["storage"]
            material = storage_material_cache[row["storageId"]]["material"]
            if composite["outboundAmount"] > 0:
                composite_material_name = (
                    material.material_name + composite["craftName"]
                )
                new_material = Material(
                    material_name=composite_material_name,
                    material_type_id=9,
                    material_unit=material.material_unit,
                    material_supplier=supplier_id,
                    material_creation_date=date.today(),
                    material_category=material.material_category,
                )
                new_material_list.append(new_material.to_dict())
                storage_mapping[composite_material_name] = [
                    storage,
                    composite["outboundAmount"],
                ]
    print(storage_mapping)
    if len(new_material_list) > 0:
        material_result = _create_composite_materials(new_material_list)
        print(material_result)
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
        db.session.add_all(new_storage_list)
    return True


def create_composite_size_materials(size_material_outbound_list):
    new_material_list = []
    storage_id_list = [row["storageId"] for row in size_material_outbound_list]
    response = (
        db.session.query(SizeMaterialStorage, Material)
        .join(Material, Material.material_id == SizeMaterialStorage.material_id)
        .filter(SizeMaterialStorage.size_material_storage_id.in_(storage_id_list))
        .all()
    )
    storage_mapping = {}
    for i, row in enumerate(response):
        storage, material = row
        if not storage.craft_name:
            return False
        crafts = storage.craft_name.split("@")
        for name in crafts:
            composite_material_name = material.material_name + name
            new_material = Material(
                material_name=composite_material_name,
                material_type_id=9,
                material_unit=material.material_unit,
                material_supplier=1,
                material_creation_date=date.today(),
                material_category=material.material_category,
            )
            new_material_list.append(new_material.to_dict())
            storage_mapping[composite_material_name] = [storage, []]
            for _, obj in enumerate(size_material_outbound_list[i]["outboundAmounts"]):
                amount = 0 if "amount" not in obj else obj["amount"]
                storage_mapping[composite_material_name][1].append(amount)

    if len(new_material_list) > 0:
        columns = ", ".join(new_material_list[0].keys())
        values_placeholder = ", ".join(
            [f":{key}" for key in new_material_list[0].keys()]
        )
        table_name = "jiancheng.material"
        sql = text(
            f"""INSERT IGNORE INTO {table_name} ({columns}) VALUES ({values_placeholder})"""
        )
        db.session.execute(sql, new_material_list)

        # create material storage for new composite material
        composite_keys = [
            (row["material_supplier"], row["material_name"])
            for row in new_material_list
        ]
        id_query = text(
            f"""
            SELECT material.material_id, material.material_name FROM {table_name} WHERE (material_supplier, material_name) IN :composite_keys;
        """
        )
        # Execute the query to fetch the IDs
        result = db.session.execute(
            id_query, {"composite_keys": composite_keys}
        ).fetchall()
        new_storage_list = []
        for material_id, material_name in result:
            storage = storage_mapping[material_name][0]
            new_storage = SizeMaterialStorage(
                material_specification=storage.size_material_specification,
                material_model=storage.size_material_model,
                order_shoe_id=storage.order_shoe_id,
                material_id=material_id,
            )
            total_estimated_inbound_amount = 0
            for i, size in enumerate(SHOESIZERANGE):
                setattr(
                    new_storage,
                    f"size_{size}_estimated_inbound_amount",
                    storage_mapping[material_name][1][i],
                )
                total_estimated_inbound_amount += storage_mapping[material_name][1][i]
            setattr(
                new_storage,
                "total_estimated_inbound_amount",
                total_estimated_inbound_amount,
            )
            new_storage_list.append(new_storage)
        db.session.add_all(new_storage_list)
        print(new_storage_list)
    return True


@material_storage_bp.route(
    "/warehouse/warehousemanager/outboundmaterial", methods=["PATCH"]
)
def outbound_material():
    data = request.get_json()
    # get meta data
    meta_data = {
        "timestamp": data["timestamp"],
        "type": data["type"],
        "department": data["outboundDepartment"],
        "address": data["outboundAddress"],
        "picker": data["picker"],
        "outsource_info_id": (
            None if "outsourceInfoId" not in data else data["outsourceInfoId"]
        ),
        "composite_supplier_id": (
            None if "compositeSupplierId" not in data else data["compositeSupplierId"]
        ),
    }
    # material amount info
    material_outbound_list = data["materialOutboundList"]
    size_material_outbound_list = data["sizeMaterialOutboundList"]

    # 新增复合材料
    if data["type"] == 3:
        result1 = outbound_composite_materials(
            material_outbound_list, meta_data["composite_supplier_id"]
        )
        # result2 = create_composite_size_materials(size_material_outbound_list)
        # if not (result1 and result2):
        #     return jsonify({"message": "该材料无复合工艺"}), 400

    # material
    for row in material_outbound_list:
        storage = db.session.query(MaterialStorage).get(row["storageId"])
        if not storage:
            return jsonify({"message": "invalid storage id"}), 400
        if storage.current_amount < row["amount"]:
            return jsonify({"message": "invalid outbound amount"}), 400
        storage.current_amount -= row["amount"]
        if storage.current_amount == 0:
            storage.material_storage_status = 2
        record = OutboundRecord(
            outbound_amount=row["amount"],
            outbound_datetime=meta_data["timestamp"],
            outbound_type=meta_data["type"],
            material_storage_id=row["storageId"],
        )
        if data["type"] == 0:
            if data["outboundDepartment"] not in PRODUCTION_LINE_REFERENCE:
                return jsonify({"message": "failed"}), 400
            record.outbound_department = meta_data["department"]
            record.picker = meta_data["picker"]
        elif data["type"] == 2:
            record.outbound_address = meta_data["address"]
            record.outsource_info_id = meta_data["outsource_info_id"]
        elif data["type"] == 3:
            record.outbound_address = meta_data["address"]
        db.session.add(record)
        rid = (
            "OR"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + str(record.outbound_record_id)
        )
        record.outbound_rid = rid

    # size material
    outbound_size_material_helper(meta_data, size_material_outbound_list)
    db.session.commit()
    return jsonify({"message": "success"})


@material_storage_bp.route(
    "/warehouse/warehousemanager/outboundsizematerial", methods=["PATCH"]
)
def outbound_size_material():
    data = request.get_json()
    storage = SizeMaterialStorage.query.get(data["sizeMaterialStorageId"])
    for shoe_size in SHOESIZERANGE:
        column_name = f"size_{shoe_size}_current_amount"
        current_value = getattr(storage, column_name)
        if current_value < int(data[f"size{shoe_size}Amount"]):
            return jsonify({"message": "invalid outbound amount"}), 400
        new_value = current_value - int(data[f"size{shoe_size}Amount"])
        setattr(storage, column_name, new_value)
        storage.total_current_amount -= int(data[f"size{shoe_size}Amount"])
    record = OutboundRecord(
        outbound_datetime=data["date"],
        outbound_type=data["type"],
        size_material_storage_id=data["sizeMaterialStorageId"],
    )
    for shoe_size in SHOESIZERANGE:
        column_name = f"size_{shoe_size}_outbound_amount"
        setattr(record, column_name, int(data[f"size{shoe_size}Amount"]))
    if data["type"] == "1":
        record.outbound_department = data["outboundDepartment"]
        if data["outboundDepartment"] not in PRODUCTION_LINE_REFERENCE:
            return jsonify({"message": "failed"}), 400
        record.picker = data["picker"]
    elif data == "2":
        record.outbound_address = data["outboundAddress"]
    db.session.add(record)
    db.session.flush()
    rid = (
        "OR" + datetime.now().strftime("%Y%m%d%H%M%S") + str(record.outbound_record_id)
    )
    record.outbound_rid = rid
    db.session.commit()
    return jsonify({"message": "success"})


@material_storage_bp.route(
    "/warehouse/warehousemanager/getmaterialinoutboundrecords", methods=["GET"]
)
def get_material_in_out_bound_records():
    db.session.query()
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

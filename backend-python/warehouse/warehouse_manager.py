from datetime import datetime, timedelta
from decimal import Decimal

from app_config import db
from constants import SHOESIZEINFO
from event_processor import EventProcessor
from flask import Blueprint, jsonify, request
from models import *
from sqlalchemy import or_

warehouse_manager_bp = Blueprint("warehouse_manager_bp", __name__)


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/getallmaterialtypes", methods=["GET"]
)
def get_all_material_types():
    response = db.session.query(MaterialType.material_type_name).all()
    result = []
    for row in response:
        result.append(row[0])
    return result


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/getallsuppliernames", methods=["GET"]
)
def get_all_supplier_names():
    response = db.session.query(Supplier.supplier_name).all()
    result = []
    for row in response:
        result.append(row[0])
    return result


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/getmaterialinboundoverview", methods=["GET"]
)
def get_material_inbound_overview():
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    filters = {
        "material_type_name": request.args.get("materialType"),
        "material_name": request.args.get("materialName"),
        "material_spec": request.args.get("materialSpec"),
        "supplier": request.args.get("supplier"),
        "order_rid": request.args.get("orderRId"),
        "shoe_rid": request.args.get("shoeRId"),
    }
    material_filter_map = {
        "material_type_name": MaterialType.material_type_name,
        "material_name": Material.material_name,
        "material_spec": MaterialStorage.material_specification,
        "supplier": Supplier.supplier_name,
        "order_rid": Order.order_rid,
        "shoe_rid": Shoe.shoe_rid,
    }
    size_material_filter_map = {
        "material_type_name": MaterialType.material_type_name,
        "material_name": Material.material_name,
        "material_spec": SizeMaterialStorage.size_material_specification,
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
            MaterialStorage.material_specification,
            MaterialStorage.unit_price,
            Material.material_name,
            Material.material_unit,
            MaterialType.material_type_name,
            MaterialType.material_category,
            Supplier.supplier_name,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(MaterialStorage, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Material, Material.material_id == MaterialStorage.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
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
            Material.material_name,
            Material.material_unit,
            MaterialType.material_type_name,
            MaterialType.material_category,
            Supplier.supplier_name,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(SizeMaterialStorage, SizeMaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Material, Material.material_id == SizeMaterialStorage.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
    )
    for key, value in filters.items():
        if value and value != "":
            query1 = query1.filter(material_filter_map[key] == value)
            query2 = query2.filter(size_material_filter_map[key] == value)
    response = (
        query1.union(query2)
        .limit(number)
        .offset((page - 1) * number)
        .all()
    )
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
            material_name,
            material_unit,
            material_type_name,
            material_category,
            supplier_name,
        ) = row
        if actual_inbound_amount >= estimated_inbound_amount:
            status = "已完成入库"
        else:
            status = "未完成入库"
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
            "totalPrice": round(current_amount * unit_price, 2),
            "supplierName": supplier_name,
            "orderId": order_id,
            "orderRId": order_rid,
            "order_shoe_id": order_shoe_id,
            "shoeRId": shoe_rid,
            "materialStorageId": material_storage_id,
            "status": status,
        }
        result.append(obj)
    return result


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/getsizematerialbyid", methods=["GET"]
)
def get_size_material_info_by_id():
    id = request.args.get("sizeMaterialStorageId")
    response = SizeMaterialStorage.query.get(id)
    result = []
    for info in SHOESIZEINFO:
        obj = {
            "shoeSize": info["shoe_size"],
            'internalSize': info["internal_size"],
            'externalSize': info["external_size"],
            "predictQuantity": getattr(
                response, f"size_{info["shoe_size"]}_estimated_inbound_amount"
            ),
            "actualQuantity": getattr(response, f"size_{info["shoe_size"]}_actual_inbound_amount"),
            "currentQuantity": getattr(response, f"size_{info["shoe_size"]}_current_amount"),
        }
        result.append(obj)
    return result


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/inboundmatieral", methods=["PATCH"]
)
def inbound_material():
    data = request.get_json()
    storage = MaterialStorage.query.get(data["materialStorageId"])
    storage.current_amount += Decimal(data["amount"])
    record = InboundRecord(
        inbound_amount=Decimal(data["amount"]),
        inbound_date=data["date"],
        inbound_type=data["type"],
        material_storage_id=data["materialStorageId"],
    )
    db.session.add(record)
    db.session.flush()
    rid = "IR" + datetime.now().strftime("%Y%m%d%H%M%S") + str(record.inbound_record_id)
    record.inbound_rid = rid
    db.session.commit()
    return jsonify({"message": "success"})


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/inboundsizematieral", methods=["PATCH"]
)
def inbound_size_material():
    data = request.get_json()
    storage = SizeMaterialStorage.query.get(data["sizeMaterialStorageId"])
    storage.total_current_amount = 0
    for info in SHOESIZEINFO:
        column_name = f"size_{info['shoe_size']}_current_amount"
        current_value = getattr(storage, column_name)
        new_value = current_value + int(data[f"size{info['shoe_size']}Amount"])
        setattr(storage, column_name, new_value)
        storage.total_current_amount += new_value
    record = InboundRecord(
        inbound_date=data["date"],
        inbound_type=data["type"],
        size_material_storage_id=data["sizeMaterialStorageId"],
    )
    for info in SHOESIZEINFO:
        column_name = f"size_{info['shoe_size']}_inbound_amount"
        setattr(record, column_name, int(data[f"size{info['shoe_size']}Amount"]))
    db.session.add(record)
    db.session.flush()
    rid = "IR" + datetime.now().strftime("%Y%m%d%H%M%S") + str(record.inbound_record_id)
    record.inbound_rid = rid
    db.session.commit()
    return jsonify({"message": "success"})


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/outboundmatieral", methods=["PATCH"]
)
def outbound_material():
    data = request.get_json()
    storage = MaterialStorage.query.get(data["materialStorageId"])
    storage.current_amount -= data["amount"]
    record = OutboundRecord(
        outbound_amount=data["amount"],
        outbound_date=data["date"],
        outbound_type=data["type"],
        material_storage_id=data["materialStorageId"],
    )
    if data["type"] == "P":
        record.outbound_department = data["outboundDepartment"]
        record.picker = data["picker"]
    elif data == "O":
        record.outbound_address = data["outboundAddress"]
    rid = "IR" + datetime.now().strftime("%Y%m%d%H%M%S") + record.inbound_record_id
    record.inbound_rid = rid
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "success"})


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/outboundsizematieral", methods=["PATCH"]
)
def outbound_size_material():
    data = request.get_json()
    storage = SizeMaterialStorage.query.get(data["sizeMaterialStorageId"])
    for i in range(34, 47):
        column_name = f"size_{i}_outbound_amount"
        current_value = getattr(storage, column_name)
        new_value = current_value - data[f"size{i}Amount"]
        setattr(storage, column_name, new_value)
    record = OutboundRecord(
        outbound_date=data["date"],
        outbound_type=data["type"],
        size_material_storage_id=data["sizeMaterialStorageId"],
    )
    for i in range(34, 47):
        column_name = f"size_{i}_outbound_amount"
        setattr(record, column_name, data[f"size{i}Amount"])
    if data["type"] == "P":
        record.outbound_department = data["outboundDepartment"]
        record.picker = data["picker"]
    elif data == "O":
        record.outbound_address = data["outboundAddress"]
    rid = "IR" + datetime.now().strftime("%Y%m%d%H%M%S") + record.inbound_record_id
    record.inbound_rid = rid
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "success"})


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/getsemifinishedinoutoverview", methods=["GET"]
)
def get_semifinished_in_out_overview():
    page = request.args.get("page")
    number = request.args.get("number")
    response = (
        db.session.query(
            Order,
            OrderShoe,
            Shoe,
            OrderShoeBatchInfo.total_amount,
            SemifinishedShoeStorage.semifinished_amount,
            OrderShoeStatus,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(SemifinishedShoeStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoeStatus.current_status.in_([25, 26]))
        .limit(number)
        .offset((page - 1) * number)
        .all()
    )
    result = []
    for row in response:
        order, order_shoe, shoe, total_amount, semifinished_amount, status = row
        if status == 25:
            status_name = "未入库"
        else:
            status_name = "已入库"
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "productionInfo": total_amount,
            "semifinishedAmount": semifinished_amount,
            "statusName": status_name,
        }
        result.append(obj)
    return result


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/semifinishedinbound", methods=["POST"]
)
def semifinished_inbound():
    data = request.get_json()
    storage = SemifinishedShoeStorage.query.filter(
        OrderShoe.order_shoe_id == data["orderShoeId"]
    ).first()
    if not storage:
        storage = SemifinishedShoeStorage(
            semifinished_inbound_date=data["inboundDate"],
            order_shoe_id=data["orderShoeId"],
            semifinished_amount=data["amount"],
            semifinished_type=data["type"],
        )
        db.session.add(storage)
    else:
        storage.semifinished_amount += data["amount"]
        storage.semifinished_type = data["type"]
        storage.semifinished_inbound_date = data["inboundDate"]

    record = ShoeInboundRecord(
        inbound_amount=data["amount"],
        inbound_date=data["inboundDate"],
        inbound_type=data["type"],
        semifinished_shoe_storage_id=storage.semifinished_shoe_id,
    )
    rid = (
        "SIR" + datetime.now().strftime("%Y%m%d%H%M%S") + record.shoe_inbound_record_id
    )
    record.shoe_inbound_rid = rid
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "success"})


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/semifinishedoutbound", methods=["POST"]
)
def semifinished_outbound():
    data = request.get_json()
    storage = SemifinishedShoeStorage.query.filter(
        OrderShoe.order_shoe_id == data["orderShoeId"]
    ).first()
    rid = (
        "SOR" + datetime.now().strftime("%Y%m%d%H%M%S") + record.shoe_outbound_record_id
    )
    if data["outboundType"] == "P":
        record = ShoeOutboundRecord(
            outbound_amount=storage.semifinished_amount,
            outbound_date=data["outboundDate"],
            outbound_department=data["outboundDest"],
            picker=data["picker"],
            outbound_type=data["outboundType"],
            semifinished_shoe_storage_id=storage.semifinished_shoe_id,
        )
    elif data["outboundType"] == "O":
        record = ShoeOutboundRecord(
            outbound_amount=storage.semifinished_amount,
            outbound_date=data["outboundDate"],
            outbound_address=data["outboundAddress"],
            outbound_type=data["outboundType"],
            semifinished_shoe_storage_id=storage.semifinished_shoe_id,
        )
    else:
        return jsonify({"message": "failed"}), 400
    rid = (
        "SOR" + datetime.now().strftime("%Y%m%d%H%M%S") + record.shoe_outbound_record_id
    )
    record.shoe_outbound_rid = rid
    storage.semifinished_amount = 0
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "success"})


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/getfinishedinoutoverview", methods=["GET"]
)
def get_finished_in_out_overview():
    page = request.args.get("page")
    number = request.args.get("number")
    response = (
        db.session.query(
            Order,
            OrderShoe,
            Shoe,
            OrderShoeBatchInfo.total_amount,
            FinishedShoeStorage.finished_amount,
            OrderShoeStatus.current_status,
            OrderStatus.order_status_id,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(FinishedShoeStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .filter(
            or_(
                (
                    OrderShoeStatus.current_status == 42,
                    OrderStatus.order_status_id == 9,
                ),
                OrderStatus.order_status_id == 15,
            )
        )
        .limit(number)
        .offset((page - 1) * number)
        .all()
    )
    result = []
    for row in response:
        (
            order,
            order_shoe,
            shoe,
            total_amount,
            finished_amount,
            order_shoe_status,
            order_status,
        ) = row
        if order_shoe_status == 42 and order_status == 9:
            status_name = "未入库"
        else:
            status_name = "已入库"
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "productionInfo": total_amount,
            "finishedAmount": finished_amount,
            "statusName": status_name,
        }
        result.append(obj)
    return result


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/inboundfinished", methods=["POST"]
)
def inbound_finished():
    data = request.get_json()
    storage = FinishedShoeStorage.query.filter(
        OrderShoe.order_shoe_id == data["orderShoeId"]
    ).first()
    storage.finished_amount += data["amount"]
    storage.finished_type = data["type"]
    storage.finished_inbound_date = data["inboundDate"]

    record = ShoeInboundRecord(
        inbound_amount=data["amount"],
        inbound_date=data["inboundDate"],
        inbound_type=data["type"],
        finished_shoe_storage_id=storage.finished_shoe_id,
    )
    rid = (
        "FIR" + datetime.now().strftime("%Y%m%d%H%M%S") + record.shoe_inbound_record_id
    )
    record.shoe_inbound_rid = rid
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "success"})


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/outboundfinished", methods=["POST"]
)
def outbound_finished():
    data = request.get_json()
    storage = FinishedShoeStorage.query.filter(
        OrderShoe.order_shoe_id == data["orderShoeId"]
    ).first()
    rid = (
        "FOR" + datetime.now().strftime("%Y%m%d%H%M%S") + record.shoe_outbound_record_id
    )
    record = ShoeOutboundRecord(
        outbound_amount=storage.finished_amount,
        outbound_date=data["outboundDate"],
        outbound_address=data["outboundAddress"],
        outbound_type="P",
        finished_shoe_storage_id=storage.finished_shoe_id,
    )
    rid = (
        "SOR" + datetime.now().strftime("%Y%m%d%H%M%S") + record.shoe_outbound_record_id
    )
    record.shoe_outbound_rid = rid
    storage.finished_amount = 0
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "success"})


@warehouse_manager_bp.route(
    "/warehouse/warehousemanager/getinoutboundrecords", methods=["GET"]
)
def get_in_out_bound_records():
    storage_id = request.args.get("storageId")
    name = request.args.get("storageName")
    if name == "material":
        inbound_response = InboundRecord.query.filter(InboundRecord.material_storage_id == storage_id).all()
        outbound_response = OutboundRecord.query.filter(OutboundRecord.material_storage_id == storage_id).all()
    elif name == "sizeMaterial":
        inbound_response = InboundRecord.query.filter(InboundRecord.size_material_storage_id == storage_id).all()
        outbound_response = OutboundRecord.query.filter(OutboundRecord.size_material_storage_id == storage_id).all()
    elif name == "semifinished":
        inbound_response = ShoeInboundRecord.query.filter(ShoeInboundRecord.semifinished_shoe_storage_id == storage_id).all()
        outbound_response = ShoeOutboundRecord.query.filter(ShoeOutboundRecord.semifinished_shoe_storage_id == storage_id).all()
    elif name == "finished":
        inbound_response = ShoeInboundRecord.query.filter(ShoeInboundRecord.finished_shoe_storage_id == storage_id).all()
        outbound_response = ShoeOutboundRecord.query.filter(ShoeOutboundRecord.finished_shoe_storage_id == storage_id).all()
    else:
        return jsonify({"message": "failed"}), 400
    
    result = []
    for row in inbound_response:
        obj = {
            "opType": "入库",
            "amount": row.inbound_amount,
            "date": row.inbound_date
        }
        result.append(obj)
    for row in outbound_response:
        obj = {
            "opType": "出库",
            "amount": row.outbound_amount,
            "date": row.outbound_date
        }
        result.append(obj)
    return result

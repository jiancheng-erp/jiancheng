from flask import Blueprint, jsonify, request
import datetime
from app_config import app, db
from models import *
from constants import SHOESIZERANGE
from api_utility import randomIdGenerater
from decimal import Decimal
from operator import itemgetter
from sqlalchemy.exc import SQLAlchemyError
from itertools import groupby
import os
from general_document.purchase_divide_order import generate_excel_file
from general_document.size_purchase_divide_order import generate_size_excel_file
from constants import SHOESIZERANGE
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH

cut_model_api_bp = Blueprint("cut_model_api", __name__)

@cut_model_api_bp.route("/logistics/getnewcutmodelpurchaseorderid", methods=["GET"])
def get_new_last_purchase_order_id():
    department = "01"
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    new_id = department + current_time_stamp + random_string + "C"
    return jsonify({"purchaseOrderRid": new_id})

@cut_model_api_bp.route("/logistics/searchcutmodelmaterialinfo", methods=["GET"])
def search_last_material_info():
    materialModel = request.args.get("materialModel")
    material_storage = (
        db.session.query(SizeMaterialStorage, Material, MaterialType, Supplier)
        .join(Material, SizeMaterialStorage.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(SizeMaterialStorage.size_material_model.ilike(f"%{materialModel}%"),
                MaterialType.material_type_id == 11,)
        .all()
    )
    material_storage_list = []
    material_size_type = ''
    for material in material_storage:
        obj = {
            "materialName": material.Material.material_name,
            "materialModel": material.SizeMaterialStorage.size_material_model,
            "materialSpecification": material.SizeMaterialStorage.size_material_specification,
            "materialType": material.MaterialType.material_type_name,
            "materialSupplier": material.Supplier.supplier_name,
            "purchaseAmount": material.SizeMaterialStorage.total_current_amount,
        }
        for size in SHOESIZERANGE:
            obj[f"size{size}Amount"] = getattr(
                material.SizeMaterialStorage, f"size_{size}_current_amount"
            )
        material_size_type = material.SizeMaterialStorage.size_storage_type
        material_storage_list.append(obj)
    return jsonify({"data": material_storage_list,"shoeSizeType": material_size_type})

@cut_model_api_bp.route("/logistics/getcutmodelpurchaseorderitems", methods=["GET"])
def get_last_purchase_order_items():
    order_id = request.args.get("orderid")
    purchase_order = (
        db.session.query(PurchaseOrder)
        .filter(PurchaseOrder.order_id == order_id,
                PurchaseOrder.purchase_order_type == "C")
        .first()
    )
    if not purchase_order:
        return jsonify({"status": "error", "message": "Purchase order not found"}), 404
    purchase_order_id = purchase_order.purchase_order_id
    purchase_order_rid = purchase_order.purchase_order_rid
    purchase_divide_orders = (
        db.session.query(PurchaseDivideOrder)
        .filter(PurchaseDivideOrder.purchase_order_id == purchase_order_id)
        .all()
    )
    purchase_order_items = []
    for purchase_divide_order in purchase_divide_orders:
        purchase_divide_order_id = purchase_divide_order.purchase_divide_order_id
        purchase_divide_order_size_type = purchase_divide_order.purchase_divide_order_type
        purchase_divide_order_items = (
            db.session.query(AssetsPurchaseOrderItem)
            .filter(
                AssetsPurchaseOrderItem.purchase_divide_order_id
                == purchase_divide_order_id
            )
            .all()
        )
        for item in purchase_divide_order_items:
            material_info = (
                db.session.query(Material, MaterialType, MaterialWarehouse)
                .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
                .join(MaterialWarehouse, MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id)
                .filter(Material.material_id == item.material_id)
                .first()
            )
            supplier_info = (
                db.session.query(Supplier)
                .filter(Supplier.supplier_id == material_info.Material.material_supplier)
                .first()
            )
            purchase_order_items.append(
                {
                    "materialName": material_info.Material.material_name,
                    "materialType": {
                        "materialTypeId": material_info.Material.material_type_id,
                        "materialTypeName": material_info.MaterialType.material_type_name,
                    },
                    "warehouseName": material_info.MaterialWarehouse.material_warehouse_name,
                    "unit": material_info.Material.material_unit,
                    "supplierName": supplier_info.supplier_name,
                    "purchaseAmount": item.purchase_amount,
                    "materialSpecification": item.material_specification,
                    "materialModel": item.material_model,
                    "materialCategory": 0 if purchase_divide_order_size_type == "N" else 1,
                    "color": item.color,
                    "comment": item.remark,
                    "craftName": item.craft_name,
                    "sizeInfo": [
                        {
                            "size": i,
                            "purchaseAmount": getattr(item, f"size_{i}_purchase_amount"),
                        }
                        for i in SHOESIZERANGE
                    ],
                }
            )
    return jsonify({"status": "success", "purchaseOrderRid": purchase_order_rid, "purchaseOrderItems": purchase_order_items})

@cut_model_api_bp.route("/logistics/newcutmodelpurchaseordersave", methods=["POST"])
def new_last_purchase_order_save():
    try:
        sub_purchase_order_id = request.json.get("purchaseOrderRId")
        material_list = request.json.get("data")
        purchase_order_type = request.json.get("purchaseOrderType")
        shoe_batch_type = request.json.get("batchInfoType", None)
        order_id = request.json.get("orderId")
        order_shoe_id = request.json.get("orderShoeId")
        purchase_order_rid = sub_purchase_order_id
        purchase_order_issue_date = datetime.datetime.now().strftime("%Y%m%d")
        purchase_order_status = "1"
        material_list_sorted = sorted(material_list, key=itemgetter("supplierName"))

        # Group the list by 'supplierName'
        grouped_materials = {}
        for supplier_name, items in groupby(
            material_list_sorted, key=itemgetter("supplierName")
        ):
            grouped_materials[supplier_name] = list(items)

        purchase_order = PurchaseOrder(
            purchase_order_rid=purchase_order_rid,
            purchase_order_type=purchase_order_type,
            purchase_order_issue_date=purchase_order_issue_date,
            purchase_order_status=purchase_order_status,
        )
        # if it is order-related purchase
        if purchase_order_type == "C":
            purchase_order.order_id = order_id

        db.session.add(purchase_order)
        db.session.flush()
        purchase_order_id = purchase_order.purchase_order_id

        for supplier_name, items in grouped_materials.items():
            supplier = (
                db.session.query(Supplier)
                .filter(Supplier.supplier_name == supplier_name)
                .first()
            )
            if not supplier:
                supplier = Supplier(supplier_name=supplier_name, supplier_type="N")
                db.session.add(supplier)
                db.session.flush()
            supplier_id = supplier.supplier_id
            supplier_id_str = str(supplier_id).zfill(4)

            purchase_divide_order_rid = purchase_order_rid + supplier_id_str
            purchase_divide_order = PurchaseDivideOrder(
                purchase_divide_order_rid=purchase_divide_order_rid,
                purchase_order_id=purchase_order_id,
                purchase_divide_order_type=(
                    "N" if items[0]["materialCategory"] == 0 else "S"
                ),
                shipment_address="温州市瓯海区梧田工业基地镇南路8号（健诚集团）",
                shipment_deadline="请在7-10日内交货",
            )
            db.session.add(purchase_divide_order)
            db.session.flush()
            purchase_divide_order_id = purchase_divide_order.purchase_divide_order_id
            order = db.session.query(Order).filter(Order.order_id == order_id).first()
            order.cutting_model_status = '1'
            db.session.flush()
            for item in items:
                print(item)
                material_name = item["materialName"]
                material_info = (
                    db.session.query(Material)
                    .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                    .filter(
                        Material.material_name == material_name,
                        Supplier.supplier_name == supplier_name,
                    )
                    .first()
                )
                if not material_info:
                    material_info = Material(
                        material_name=material_name,
                        material_type_id=item["materialType"]["materialTypeId"],
                        material_unit=item["unit"],
                        material_supplier=supplier_id,
                        material_creation_date=datetime.datetime.now(),
                    )
                    db.session.add(material_info)
                    db.session.flush()
                material_id = material_info.material_id
                material_quantity = item["purchaseAmount"]
                material_specification = item["materialSpecification"]
                material_model = item["materialModel"]
                color = item["color"]
                remark = item["comment"]
                if items[0]["materialCategory"] == 0:
                    assets_item = AssetsPurchaseOrderItem(
                        purchase_divide_order_id=purchase_divide_order_id,
                        material_id=material_id,
                        purchase_amount=material_quantity,
                        material_specification=material_specification,
                        material_model=material_model,
                        color=color,
                        remark=remark,
                        size_type=shoe_batch_type,
                        craft_name=item["craftName"],
                    )
                    db.session.add(assets_item)
                elif items[0]["materialCategory"] == 1:
                    assets_item = AssetsPurchaseOrderItem(
                        purchase_divide_order_id=purchase_divide_order_id,
                        material_id=material_id,
                        purchase_amount=material_quantity,
                        material_specification=material_specification,
                        material_model=material_model,
                        color=color,
                        remark=remark,
                        size_type=shoe_batch_type,
                        craft_name=item["craftName"],
                    )
                    for i in SHOESIZERANGE:
                        if i - 34 < len(item["sizeInfo"]):
                            setattr(
                                assets_item,
                                f"size_{i}_purchase_amount",
                                item["sizeInfo"][i - 34]["purchaseAmount"],
                            )
                    db.session.add(assets_item)
                else:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "invalid purchase divide order type",
                            }
                        ),
                        400,
                    )
        db.session.commit()
        return jsonify({"status": "success"})
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session to undo changes
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@cut_model_api_bp.route("/logistics/editsavedcutmodelpurchaseorderitems", methods=["POST"])
def edit_saved_last_purchase_order_items():
    try:
        sub_purchase_order_id = request.json.get("purchaseOrderRId")
        material_list = request.json.get("data")
        purchase_order_type = request.json.get("purchaseOrderType")
        shoe_batch_type = request.json.get("batchInfoType", None)
        order_id = request.json.get("orderId")
        order_shoe_id = request.json.get("orderShoeId")
        purchase_order_rid = sub_purchase_order_id
        purchase_order_issue_date = datetime.datetime.now().strftime("%Y%m%d")
        purchase_order_status = "1"
        material_list_sorted = sorted(material_list, key=itemgetter("supplierName"))

        # Group the list by 'supplierName'
        grouped_materials = {}
        for supplier_name, items in groupby(
            material_list_sorted, key=itemgetter("supplierName")
        ):
            grouped_materials[supplier_name] = list(items)
        print(purchase_order_rid)
        purchase_order = (
            db.session.query(PurchaseOrder)
            .filter(PurchaseOrder.purchase_order_rid == purchase_order_rid)
            .first()
        )
        if not purchase_order:
            return jsonify({"status": "error", "message": "Purchase order not found"}), 404
        purchase_order_id = purchase_order.purchase_order_id
        purchase_order.purchase_order_type = purchase_order_type
        purchase_order.purchase_order_issue_date = purchase_order_issue_date
        purchase_order.purchase_order_status = purchase_order_status
        db.session.flush()
        
        #delete the old purchase divide order and items
        purchase_divide_orders = (
            db.session.query(PurchaseDivideOrder)
            .filter(PurchaseDivideOrder.purchase_order_id == purchase_order_id)
            .all()
        )
        for purchase_divide_order in purchase_divide_orders:
            purchase_divide_order_id = purchase_divide_order.purchase_divide_order_id
            purchase_divide_order_items = (
                db.session.query(AssetsPurchaseOrderItem)
                .filter(
                    AssetsPurchaseOrderItem.purchase_divide_order_id
                    == purchase_divide_order_id
                )
                .all()
            )
            for item in purchase_divide_order_items:
                db.session.delete(item)
            db.session.delete(purchase_divide_order)
        db.session.flush()
        
        #same as new_package_purchase_order_save
        for supplier_name, items in grouped_materials.items():
            supplier = (
                db.session.query(Supplier)
                .filter(Supplier.supplier_name == supplier_name)
                .first()
            )
            if not supplier:
                supplier = Supplier(supplier_name=supplier_name, supplier_type="N")
                db.session.add(supplier)
                db.session.flush()
            supplier_id = supplier.supplier_id
            supplier_id_str = str(supplier_id).zfill(4)

            purchase_divide_order_rid = purchase_order_rid + supplier_id_str
            purchase_divide_order = PurchaseDivideOrder(
                purchase_divide_order_rid=purchase_divide_order_rid,
                purchase_order_id=purchase_order_id,
                purchase_divide_order_type=(
                    "N" if items[0]["materialCategory"] == 0 else "S"
                ),
                shipment_address="温州市瓯海区梧田工业基地镇南路8号（健诚集团）",
                shipment_deadline="请在7-10日内交货",
            )
            db.session.add(purchase_divide_order)
            db.session.flush()
            purchase_divide_order_id = purchase_divide_order.purchase_divide_order_id
            order = db.session.query(Order).filter(Order.order_id == order_id).first()
            order.cutting_model_status = '1'
            db.session.flush()
            for item in items:
                material_name = item["materialName"]
                material_info = (
                    db.session.query(Material)
                    .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                    .filter(
                        Material.material_name == material_name,
                        Supplier.supplier_name == supplier_name,
                    )
                    .first()
                )
                if not material_info:
                    material_info = Material(
                        material_name=material_name,
                        material_type_id=item["materialType"]["materialTypeId"],
                        material_unit=item["unit"],
                        material_supplier=supplier_id,
                        material_creation_date=datetime.datetime.now(),
                    )
                    db.session.add(material_info)
                    db.session.flush()
                material_id = material_info.material_id
                material_quantity = item["purchaseAmount"]
                material_specification = item["materialSpecification"]
                material_model = item["materialModel"]
                color = item["color"]
                remark = item["comment"]
                if items[0]["materialCategory"] == 0:
                    assets_item = AssetsPurchaseOrderItem(
                        purchase_divide_order_id=purchase_divide_order_id,
                        material_id=material_id,
                        purchase_amount=material_quantity,
                        material_specification=material_specification,
                        material_model=material_model,
                        color=color,
                        remark=remark,
                        size_type=shoe_batch_type,
                        craft_name=item["craftName"],
                    )
                    db.session.add(assets_item)
                elif items[0]["materialCategory"] == 1:
                    assets_item = AssetsPurchaseOrderItem(
                        purchase_divide_order_id=purchase_divide_order_id,
                        material_id=material_id,
                        purchase_amount=material_quantity,
                        material_specification=material_specification,
                        material_model=material_model,
                        color=color,
                        remark=remark,
                        size_type=shoe_batch_type,
                        craft_name=item["craftName"],
                    )
                    for i in SHOESIZERANGE:
                        if i - 34 < len(item["sizeInfo"]):
                            setattr(
                                assets_item,
                                f"size_{i}_purchase_amount",
                                item["sizeInfo"][i - 34]["purchaseAmount"],
                            )
                    db.session.add(assets_item)
                else:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "invalid purchase divide order type",
                            }
                        ),
                        400,
                    )
        db.session.commit()
        return jsonify({"status": "success"})
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
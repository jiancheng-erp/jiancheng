from flask import Blueprint, jsonify, request
import datetime
from app_config import db
from models import *
from constants import SHOESIZERANGE
from api_utility import randomIdGenerater
from decimal import Decimal
from operator import itemgetter
from sqlalchemy.exc import SQLAlchemyError
from itertools import groupby
import os
import json
from general_document.purchase_divide_order import generate_excel_file
from general_document.size_purchase_divide_order import generate_size_excel_file
from constants import SHOESIZERANGE
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from business.batch_info_type import get_order_batch_type_helper
from general_document.cutmodel_purchase_divide_order import generate_cut_model_excel_file
import zipfile

cut_model_api_bp = Blueprint("cut_model_api", __name__)


@cut_model_api_bp.route("/logistics/getnewcutmodelpurchaseorderid", methods=["GET"])
def get_new_cut_model_purchase_order_id():
    department = "01"
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    new_id = department + current_time_stamp + random_string + "C"
    return jsonify({"purchaseOrderRid": new_id})


@cut_model_api_bp.route("/logistics/getcutmodelinfo", methods=["GET"])
def get_cut_model_info():
    order_id = request.args.get("orderid")
    order_shoe = (
        db.session.query(OrderShoe).filter(OrderShoe.order_id == order_id).first()
    )
    craft_sheet = (
        db.session.query(CraftSheet)
        .filter(CraftSheet.order_shoe_id == order_shoe.order_shoe_id)
        .first()
    )
    cut_model_type = craft_sheet.cut_die_staff
    return jsonify({"cutModelType": cut_model_type})


@cut_model_api_bp.route("/logistics/searchcutmodelmaterialinfo", methods=["GET"])
def search_cut_model_material_info():
    materialModel = request.args.get("materialModel")
    material_storage = (
        db.session.query(SizeMaterialStorage, Material, MaterialType, Supplier)
        .join(Material, SizeMaterialStorage.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(SizeMaterialStorage.size_material_model.ilike(f"%{materialModel}%"),
        MaterialType.material_type_id == 12,)
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
def get_cut_model_purchase_order_items():
    order_id = request.args.get("orderid")
    purchase_order = (
        db.session.query(PurchaseOrder)
        .filter(PurchaseOrder.order_id == order_id,
                PurchaseOrder.purchase_order_type == "C")
        .first()
    )
    if not purchase_order:
        return jsonify({"purchaseOrderItems": [], "purchaseOrderId": None, "purchaseOrderRid": None})
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
    return jsonify({"status": "success", "purchaseOrderRid": purchase_order_rid, "purchaseOrderItems": purchase_order_items, "purchaseOrderId": purchase_order_id})

@cut_model_api_bp.route("/logistics/newcutmodelpurchaseordersave", methods=["POST"])
def new_cut_model_purchase_order_save():
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
        if purchase_order_type == "L":
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
def edit_saved_cut_model_purchase_order_items():
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

@cut_model_api_bp.route("/logistics/submitcutmodelindividualpurchaseorders", methods=["POST"])
def submit_purchase_divide_orders():
    purchase_order_id = request.json.get("purchaseOrderId")
    order_info = (
        db.session.query(PurchaseOrder, Order)
        .join(Order, PurchaseOrder.order_id == Order.order_id)
        .filter(PurchaseOrder.purchase_order_id == purchase_order_id)
        .first()
    )
    order_id = order_info.Order.order_id
    order_rid = order_info.Order.order_rid
    materials_data = []
    query = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrder,
            AssetsPurchaseOrderItem,
            Material,
            MaterialType,
            Supplier,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(
            AssetsPurchaseOrderItem,
            PurchaseDivideOrder.purchase_divide_order_id
            == AssetsPurchaseOrderItem.purchase_divide_order_id,
        )
        .join(Material, AssetsPurchaseOrderItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_id == purchase_order_id)
        .all()
    )
    for (
        purchase_divide_order,
        purchase_order,
        assets_purchase_order_item,
        material,
        material_type,
        supplier,
    ) in query:
        current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
        random_string = randomIdGenerater(6)
        supplier_id_string = str(supplier.supplier_id).zfill(4)
        total_purchase_order_rid = (
            "T" + current_time_stamp + random_string + "C" + supplier_id_string
        )
        total_purchase_order = TotalPurchaseOrder(
            total_purchase_order_rid=total_purchase_order_rid,
            supplier_id=supplier.supplier_id,
            create_date=datetime.datetime.now(),
            total_purchase_order_remark="",
            total_purchase_order_environmental_request="",
            shipment_address="温州市瓯海区梧田工业基地镇南路8号（健诚集团）",
            shipment_deadline="请在7-10日内交货",
            total_purchase_order_status="2",
        )
        db.session.add(total_purchase_order)
        db.session.flush()
        purchase_divide_order.total_purchase_order_id = total_purchase_order.total_purchase_order_id
        materials_data.append(
            {
                "supplier_name": supplier.supplier_name,
                "material_name": material.material_name,
                "model": assets_purchase_order_item.material_model or "",
                "specification": assets_purchase_order_item.material_specification or "",
                "purchase_amount": assets_purchase_order_item.purchase_amount,
            }
        )

        material_id = assets_purchase_order_item.material_id
        material_quantity = assets_purchase_order_item.purchase_amount
        material_specification = assets_purchase_order_item.material_specification
        material_model = assets_purchase_order_item.material_model
        color = assets_purchase_order_item.color
        remark = assets_purchase_order_item.remark
        size_type = assets_purchase_order_item.size_type
        craft_name = assets_purchase_order_item.craft_name
        if purchase_divide_order.purchase_divide_order_type == "N":
            material_storage = MaterialStorage(
                order_id = order_id,
                material_id=material_id,
                estimated_inbound_amount=material_quantity,
                actual_inbound_amount=0,
                current_amount=0,
                unit_price=0,
                material_outsource_status="0",
                material_model=material_model,
                material_specification=material_specification,
                material_storage_color=color,
                total_purchase_order_id=total_purchase_order.total_purchase_order_id,
                craft_name=craft_name,
                actual_inbound_material_id=assets_purchase_order_item.inbound_material_id if assets_purchase_order_item.inbound_material_id else assets_purchase_order_item.material_id,
                actual_inbound_unit=assets_purchase_order_item.inbound_unit if assets_purchase_order_item.inbound_unit else material.material_unit,
            )
            db.session.add(material_storage)
        elif purchase_divide_order.purchase_divide_order_type == "S":
            quantity_map = {}
            for size in SHOESIZERANGE:
                quantity_map[f"size_{size}_quantity"] = getattr(
                    assets_purchase_order_item, f"size_{size}_purchase_amount"
                )

            size_material_storage = SizeMaterialStorage(
                order_id=order_id,
                material_id=material_id,
                total_estimated_inbound_amount=material_quantity,
                unit_price=0,
                material_outsource_status="0",
                size_material_model=material_model,
                size_material_specification=material_specification,
                size_material_color=color,
                total_purchase_order_id=total_purchase_order.total_purchase_order_id,
                craft_name=craft_name,
            )
            for size in SHOESIZERANGE:
                setattr(
                    size_material_storage,
                    f"size_{size}_estimated_inbound_amount",
                    quantity_map[f"size_{size}_quantity"],
                )
            db.session.add(size_material_storage)
    purchase_order_status = "2"
    db.session.query(PurchaseOrder).filter(
        PurchaseOrder.purchase_order_id == purchase_order_id
    ).update({"purchase_order_status": purchase_order_status})
    db.session.flush()
    purchase_divide_orders = (
        db.session.query(
            PurchaseDivideOrder,
            AssetsPurchaseOrderItem,
            PurchaseOrder,
            Material,
            Supplier,
        )
        .join(
            AssetsPurchaseOrderItem,
            PurchaseDivideOrder.purchase_divide_order_id
            == AssetsPurchaseOrderItem.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(Material, AssetsPurchaseOrderItem.material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_id == purchase_order_id)
        .all()
    )

    # Dictionary to keep track of processed PurchaseDivideOrders
    purchase_divide_order_dict = {}
    size_purchase_divide_order_dict = {}
    if (
        os.path.exists(
            os.path.join(FILE_STORAGE_PATH, order_rid)
        )
        == False
    ):
        os.mkdir(
            os.path.join(FILE_STORAGE_PATH, order_rid)
        )
    customer_name = (
        db.session.query(Customer)
        .join(Order, Order.customer_id == Customer.customer_id)
        .filter(Order.order_id == order_id)
        .first()
        .customer_name
    )

    # Iterate through the query results and group items by PurchaseDivideOrder
    for (
        purchase_divide_order,
        assets_purchase_order_item,
        purchase_order,
        material,
        supplier,
    ) in purchase_divide_orders:
        purchase_order_id = purchase_divide_order.purchase_divide_order_rid
        if purchase_divide_order.purchase_divide_order_type == "N":
            if purchase_order_id not in purchase_divide_order_dict:
                purchase_divide_order_dict[purchase_order_id] = {
                    "供应商": supplier.supplier_name,
                    "日期": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "备注": purchase_divide_order.purchase_order_remark,
                    "环保要求": purchase_divide_order.purchase_order_environmental_request,
                    "发货地址": purchase_divide_order.shipment_address,
                    "交货期限": purchase_divide_order.shipment_deadline,
                    "客户名": customer_name,
                    "订单信息": order_rid,
                    "seriesData": [],
                }

            # Append the current PurchaseOrderItem to the 'seriesData' list of the relevant order
            purchase_divide_order_dict[purchase_order_id]["seriesData"].append(
                {
                    "物品名称": (
                        material.material_name
                        + " "
                        + (assets_purchase_order_item.material_model if assets_purchase_order_item.material_model else "")
                        + " "
                        + (
                            assets_purchase_order_item.material_specification
                            if assets_purchase_order_item.material_specification
                            else ""
                        )
                        + " "
                        + (assets_purchase_order_item.color if assets_purchase_order_item.color else "")
                    ),
                    "型号" : assets_purchase_order_item.material_model if assets_purchase_order_item.material_model else "",
                    "类别" : material.material_name,
                    "数量": assets_purchase_order_item.purchase_amount,
                    "单位": material.material_unit,
                    "备注": assets_purchase_order_item.remark,
                    "用途说明": "",
                }
            )
        elif purchase_divide_order.purchase_divide_order_type == "S":
# 获取 order_size_table 并转换为字典
            order_size_table = (
                db.session.query(Order)
                .filter(Order.order_id == order_id)
                .first()
                .order_size_table
            )
            if order_size_table:
                order_size_table = json.loads(order_size_table)
            else:
                order_size_table = {}  # 确保是字典

            # 获取 batch_info_type 信息
            batch_info_type = (
                db.session.query(BatchInfoType, Order)
                .join(Order, Order.batch_info_type_id == BatchInfoType.batch_info_type_id)
                .filter(Order.order_id == order_id)
                .first()
            )

            # 1️⃣ 创建 "客人码" -> "实际尺码" 映射
            customer_size_map = {}  # { "7.5": 34, "8.0": 35, "8.5": 36 }
            for i in SHOESIZERANGE:
                size_name = getattr(batch_info_type.BatchInfoType, f"size_{i}_name", None)
                if size_name:
                    customer_size_map[size_name] = i  # 例如 {"7.5": 34, "8.0": 35, "8.5": 36}

            # 2️⃣ 确保 `order_size_table` 至少有 `客人码`
            if "客人码" not in order_size_table or not order_size_table["客人码"]:
                order_size_table["客人码"] = list(customer_size_map.keys())  # 从 batch_info_type 生成客人码

            # 3️⃣ 根据 `material_name` 选择合适的尺码来源
            if "大底" in material.material_name:
                size_values = order_size_table.get("大底", order_size_table["客人码"])  # 兜底使用 `客人码`
            elif "中底" in material.material_name:
                size_values = order_size_table.get("中底", order_size_table["客人码"])
            elif "楦头" in material.material_name:
                size_values = order_size_table.get("楦头", order_size_table["客人码"])
            else:
                size_values = order_size_table["客人码"]
            print(size_values)

            # 4️⃣ 转换为实际尺码并构造最终的 obj
            obj = {
                "物品名称": (
                    material.material_name
                    + " "
                    + (assets_purchase_order_item.material_model if assets_purchase_order_item.material_model else "")
                    + " "
                    + (
                        assets_purchase_order_item.material_specification
                        if assets_purchase_order_item.material_specification
                        else ""
                    )
                    + " "
                    + (assets_purchase_order_item._color if assets_purchase_order_item.color else "")
                ),
                "型号" : assets_purchase_order_item.material_model if assets_purchase_order_item.material_model else "",
                "类别" : material.material_name,
                "备注": assets_purchase_order_item.remark,
            }
            for index, size_value in enumerate(size_values):
                customer_value = order_size_table["客人码"][index]
                if customer_value in customer_size_map:
                    actual_size = customer_size_map[customer_value]  # 例如 7.5 -> 34
                    obj[size_value] = getattr(assets_purchase_order_item, f"size_{actual_size}_purchase_amount", 0)

            # 5️⃣ 添加到 seriesData
            if purchase_order_id not in size_purchase_divide_order_dict:
                size_purchase_divide_order_dict[purchase_order_id] = {
                    "供应商": supplier.supplier_name,
                    "日期": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "备注": purchase_divide_order.purchase_order_remark,
                    "客户名": customer_name,
                    "环保要求": purchase_divide_order.purchase_order_environmental_request,
                    "发货地址": purchase_divide_order.shipment_address,
                    "交货期限": purchase_divide_order.shipment_deadline,
                    "订单信息": order_rid,
                    "seriesData": [],
                }

            size_purchase_divide_order_dict[purchase_order_id]["seriesData"].append(obj)
            print(size_purchase_divide_order_dict)
    customer_name = (
        db.session.query(Order, Customer)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .filter(Order.order_id == order_id)
        .first()
        .Customer.customer_name
    )
    generated_files = []
    # Convert the dictionary to a list
    template_path = os.path.join(FILE_STORAGE_PATH, "标准采购订单.xlsx")
    size_template_path = os.path.join(FILE_STORAGE_PATH, "新标准采购订单尺码版.xlsx")
    for purchase_order_id, data in purchase_divide_order_dict.items():
        new_file_path = os.path.join(
            FILE_STORAGE_PATH,
            order_rid,
            purchase_order_id + "_刀模采购订单_" + data["供应商"] + ".xlsx",
        )
        generate_excel_file(template_path, new_file_path, data)
        generated_files.append(new_file_path)
    shoe_size_names = get_order_batch_type_helper(order_id)
    for purchase_order_id, data in size_purchase_divide_order_dict.items():
        new_file_path = os.path.join(
            FILE_STORAGE_PATH,
            order_rid,
            purchase_order_id + "_刀模采购订单_" + data["供应商"] + ".xlsx",
        )
        data["shoe_size_names"] = shoe_size_names
        generate_cut_model_excel_file(
                size_template_path, new_file_path, data
            )
        generated_files.append(new_file_path)
    zip_file_path = os.path.join(
        FILE_STORAGE_PATH,
        order_rid,
        "楦头采购订单.zip",
    )
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        for file in generated_files:
            # Extract purchase_order_id from the filename and check if it ends with 'F'
            filename = os.path.basename(file)
            purchase_order_id = filename.split("_")[0]  # Get the part before "_供应商"
            if len(purchase_order_id) >= 5 and purchase_order_id[-5] == "C":
                zipf.write(file, filename)  # Add the file to the zip
    order = db.session.query(Order).filter(Order.order_id == order_id).first()
    order.cutting_model_status = '2'
    db.session.commit()
    return jsonify({"status": "success"})
    

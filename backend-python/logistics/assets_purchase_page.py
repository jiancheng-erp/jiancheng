from flask import Blueprint, jsonify, request, send_file
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from app_config import app, db
from api_utility import randomIdGenerater
import datetime
from itertools import groupby
from operator import itemgetter
from models import *
from constants import SHOESIZERANGE
from file_locations import *
import os
import zipfile
from general_document.size_purchase_divide_order import generate_size_excel_file
from general_document.purchase_divide_order import generate_excel_file

assets_purchase_page_bp = Blueprint("assets_purchase_page_bp", __name__)


@assets_purchase_page_bp.route(
    "/logistics/assetsmaterialpurchaseorder", methods=["GET"]
)
def get_assets_material_purchase_order():
    purchase_order_status = str(request.args.get("purchaseorderstatus"))
    query = (
        db.session.query(PurchaseOrder, Order, Shoe)
        .outerjoin(Order, PurchaseOrder.order_id == Order.order_id)
        .outerjoin(OrderShoe, PurchaseOrder.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(PurchaseOrder.purchase_order_status == purchase_order_status)
        .filter(PurchaseOrder.purchase_order_type.in_(["I", "O", "X"]))
    )
    response = query.all()
    result = []
    for row in response:
        purchase_order, order, shoe = row
        purchase_order_type = ""
        if purchase_order.purchase_order_type == "I":
            purchase_order_type = "独立采购"
        elif purchase_order.purchase_order_type == "O":
            purchase_order_type = "随订单采购"
        elif purchase_order.purchase_order_type == "X":
            purchase_order_type = "随订单鞋型采购"
        result.append(
            {
                "purchaseOrderId": purchase_order.purchase_order_id,
                "purchaseOrderRId": purchase_order.purchase_order_rid,
                "createDate": purchase_order.purchase_order_issue_date.isoformat(),
                "purchaseOrderType": purchase_order_type,
                "orderRId": order.order_rid if order else None,
                "shoeRId": shoe.shoe_rid if shoe else None,
            }
        )
    return jsonify(result)


@assets_purchase_page_bp.route(
    "/logistics/getassetsnewpurchaseorderid", methods=["POST"]
)
def get_assets_new_purchase_order_id():
    department = request.json.get("department")
    print(department)
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    new_id = department + current_time_stamp + random_string
    return jsonify({"newId": new_id})


@assets_purchase_page_bp.route("/logistics/getmaterialtypeandname", methods=["GET"])
def get_material_type_and_name():
    material_type = request.args.get("materialtype")
    material_name = request.args.get("materialname")
    supplier_name = request.args.get("suppliername")
    print(material_type, material_name, supplier_name)
    query = (
        db.session.query(Material, MaterialType, MaterialWarehouse, Supplier)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(
            MaterialWarehouse,
            MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id,
        )
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
    )
    if material_type:
        query = query.filter(MaterialType.material_type_name.like(f"%{material_type}%"))
    if material_name:
        query = query.filter(Material.material_name.like(f"%{material_name}%"))
    if supplier_name:
        query = query.filter(Supplier.supplier_name.like(f"%{supplier_name}%"))
    result = []
    for row in query:
        result.append(
            {
                "materialId": row.Material.material_id,
                "materialType": row.MaterialType.material_type_name,
                "materialName": row.Material.material_name,
                "warehouseName": row.MaterialWarehouse.material_warehouse_name,
                "unit": row.Material.material_unit,
                "supplierName": row.Supplier.supplier_name,
                "materialCategory": row.Material.material_category,
            }
        )
    return jsonify(result)

@assets_purchase_page_bp.route("/logistics/getallmaterialname", methods=["GET"])
def get_all_material_name():
    # Query for all material names and their types
    material_department = request.args.get("department")
    material_name_list = db.session.query(Material).filter(Material.material_usage_department == material_department).all()
    
    # Use a dictionary to store unique material names
    unique_materials = {}
    for material in material_name_list:
        if material.material_name not in unique_materials:
            unique_materials[material.material_name] = {
                "value": material.material_name,
                "label": material.material_name,
                "type": material.material_type_id,
            }
    
    # Convert the dictionary values into a list
    result = list(unique_materials.values())
    
    # Print and return the result
    print(result)
    return jsonify(result)

@assets_purchase_page_bp.route("/logistics/newpurchaseordersave", methods=["POST"])
def new_purchase_order_save():
    try:
        sub_purchase_order_id = request.json.get("purchaseOrderRId")
        material_list = request.json.get("data")
        print(material_list)
        purchase_order_type = request.json.get("purchaseOrderType")
        shoe_batch_type = request.json.get("batchInfoType")
        order_id = request.json.get("orderId")
        order_shoe_id = request.json.get("orderShoeId")
        purchase_order_rid = sub_purchase_order_id + purchase_order_type
        purchase_order_issue_date = datetime.datetime.now().strftime("%Y%m%d")
        purchase_order_status = "0"
        material_list_sorted = sorted(material_list, key=itemgetter("supplierName"))
        print(shoe_batch_type)

        # Group the list by 'supplierName'
        grouped_materials = {}
        for supplier_name, items in groupby(
            material_list_sorted, key=itemgetter("supplierName")
        ):
            grouped_materials[supplier_name] = list(items)
        print(grouped_materials)

        purchase_order = PurchaseOrder(
            purchase_order_rid=purchase_order_rid,
            purchase_order_type=purchase_order_type,
            purchase_order_issue_date=purchase_order_issue_date,
            purchase_order_status=purchase_order_status,
        )
        # if it is order-related purchase
        if purchase_order_type == "O":
            purchase_order.order_id = order_id
        # if it is order shoe related purchase
        elif purchase_order_type == "X":
            purchase_order.order_id = order_id
            purchase_order.order_shoe_id = order_shoe_id

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
                        if i -34 < len(item["sizeInfo"]):
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


@assets_purchase_page_bp.route(
    "/logistics/getassetspurchaseorderitems", methods=["GET"]
)
def get_assets_purchase_order_items():
    purchase_order_id = request.args.get("purchaseOrderId")

    # Fetch the data from the database
    query = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrder,
            AssetsPurchaseOrderItem,
            Material,
            MaterialType,
            MaterialWarehouse,
            Supplier,
            Order,
            OrderShoe,
            Shoe,
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
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(
            MaterialWarehouse,
            MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id,
        )
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .outerjoin(Order, PurchaseOrder.order_id == Order.order_id)
        .outerjoin(OrderShoe, PurchaseOrder.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(PurchaseOrder.purchase_order_id == purchase_order_id)
        .all()
    )
    purchase_divide_order_type = 'N'
    # Group the results by purchase_divide_order_rid
    result = []
    for (
        purchase_divide_order,
        purchase_order,
        assets_item,
        material,
        material_type,
        material_warehouse,
        supplier,
        order,
        order_shoe,
        shoe,
    ) in query:
        purchase_divide_order_type = purchase_divide_order.purchase_divide_order_type
        if purchase_divide_order_type == "N":
            result.append(
                {
                    "purchaseDivideOrderId": purchase_divide_order.purchase_divide_order_rid,
                    "purchaseOrderId": purchase_order.purchase_order_id,
                    "purchaseOrderRId": purchase_order.purchase_order_rid,
                    "purchaseOrderType": purchase_order.purchase_order_type,
                    "supplierName": supplier.supplier_name,
                    "warehouseName": material_warehouse.material_warehouse_name,
                    "isPurchaseOrder": purchase_order.purchase_order_type,
                    "materialType": material_type.material_type_name,
                    "materialName": material.material_name,
                    "materialSpecification": assets_item.material_specification,
                    "materialModel": assets_item.material_model,
                    "color": assets_item.color,
                    "unit": material.material_unit,
                    "craftName": assets_item.craft_name,
                    "purchaseAmount": float(assets_item.purchase_amount),
                    "comment": assets_item.remark if assets_item.remark else "",
                    "orderId": order.order_id if order else None,
                    "orderRId": order.order_rid if order else None,
                    "orderShoeId": order_shoe.order_shoe_id if order_shoe else None,
                    "shoeRId": shoe.shoe_rid if shoe else None,
                }
            )
        elif purchase_divide_order_type == "S":
            result.append(
                {
                    "purchaseDivideOrderId": purchase_divide_order.purchase_divide_order_rid,
                    "purchaseOrderId": purchase_divide_order.purchase_order_id,
                    "supplierName": supplier.supplier_name,
                    "warehouseName": material_warehouse.material_warehouse_name,
                    "isPurchaseOrder": purchase_order.purchase_order_type,
                    "orderId": order.order_rid if order else "",
                    "materialType": material_type.material_type_name,
                    "materialName": material.material_name,
                    "materialSpecification": assets_item.material_specification,
                    "color": assets_item.color,
                    "craftName": assets_item.craft_name,
                    "unit": material.material_unit,
                    "comment": assets_item.remark if assets_item.remark else "",
                    "sizeInfo": [
                        {
                            "size": "35",
                            "innerSize": "7",
                            "outterSize": "7",
                            "purchaseAmount": assets_item.size_35_purchase_amount,
                        },
                        {
                            "size": "36",
                            "innerSize": "7",
                            "outterSize": "7.5",
                            "purchaseAmount": assets_item.size_36_purchase_amount,
                        },
                        {
                            "size": "37",
                            "innerSize": "8",
                            "outterSize": "8",
                            "purchaseAmount": assets_item.size_37_purchase_amount,
                        },
                        {
                            "size": "38",
                            "innerSize": "8",
                            "outterSize": "8.5",
                            "purchaseAmount": assets_item.size_38_purchase_amount,
                        },
                        {
                            "size": "39",
                            "innerSize": "9",
                            "outterSize": "9",
                            "purchaseAmount": assets_item.size_39_purchase_amount,
                        },
                        {
                            "size": "40",
                            "innerSize": "9",
                            "outterSize": "9.5",
                            "purchaseAmount": assets_item.size_40_purchase_amount,
                        },
                        {
                            "size": "41",
                            "innerSize": "10",
                            "outterSize": "10",
                            "purchaseAmount": assets_item.size_41_purchase_amount,
                        },
                        {
                            "size": "42",
                            "innerSize": "10",
                            "outterSize": "10.5",
                            "purchaseAmount": assets_item.size_42_purchase_amount,
                        },
                        {
                            "size": "43",
                            "innerSize": "11",
                            "outterSize": "11",
                            "purchaseAmount": assets_item.size_43_purchase_amount,
                        },
                        {
                            "size": "44",
                            "innerSize": "12",
                            "outterSize": "12",
                            "purchaseAmount": assets_item.size_44_purchase_amount,
                        },
                        {
                            "size": "45",
                            "innerSize": "13",
                            "outterSize": "13",
                            "purchaseAmount": assets_item.size_45_purchase_amount,
                        },
                    ],
                }
            )
    fin_result = {
        "purchaseDivideOrderType": purchase_divide_order_type,
        "data": result,
    }
    print(result)
    return jsonify(fin_result)


@assets_purchase_page_bp.route(
    "/logistics/getassetspurchasedivideorders", methods=["GET"]
)
def get_purchase_divide_orders():
    purchase_order_id = request.args.get("purchaseOrderId")

    # Fetch the data from the database
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
            AssetsPurchaseOrderItem,
            PurchaseDivideOrder.purchase_divide_order_id
            == AssetsPurchaseOrderItem.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(Material, AssetsPurchaseOrderItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_id == purchase_order_id)
        .all()
    )

    # Group the results by purchase_divide_order_rid
    grouped_results = {}
    for (
        purchase_divide_order,
        purchase_order,
        assets_item,
        material,
        material_type,
        supplier,
    ) in query:
        divide_order_rid = purchase_divide_order.purchase_divide_order_rid
        if divide_order_rid not in grouped_results:
            grouped_results[divide_order_rid] = {
                "purchaseDivideOrderId": divide_order_rid,
                "purchaseOrderId": purchase_divide_order.purchase_order_id,
                "supplierName": supplier.supplier_name,
                "assetsItems": [],
                "purchaseDivideOrderType": purchase_divide_order.purchase_divide_order_type,
                "remark": purchase_divide_order.purchase_order_remark,
                "evironmentalRequest": purchase_divide_order.purchase_order_environmental_request,
                "shipmentAddress": purchase_divide_order.shipment_address,
                "shipmentDeadline": purchase_divide_order.shipment_deadline,
            }

        # Append the assets item details to the corresponding group
        obj = {
            "materialId": assets_item.material_id,
            "materialType": material_type.material_type_name,
            "materialName": material.material_name,
            "materialModel": assets_item.material_model,
            "materialSpecification": assets_item.material_specification,
            "color": assets_item.color,
            "unit": material.material_unit,
            "purchaseAmount": assets_item.purchase_amount,
            "remark": assets_item.remark,
            "sizeType": assets_item.size_type,
        }
        batch_info_type = db.session.query(BatchInfoType).filter(BatchInfoType.batch_info_type_name == assets_item.size_type).first()
        if batch_info_type:
            for shoe_size in SHOESIZERANGE:
                if getattr(batch_info_type, f"size_{shoe_size}_name") is not None:
                    obj[getattr(batch_info_type, f"size_{shoe_size}_name")] = getattr(assets_item, f"size_{shoe_size}_purchase_amount")
            print(obj)
        grouped_results[divide_order_rid]["assetsItems"].append(obj)

    # Convert the grouped results to a list
    result = list(grouped_results.values())

    return jsonify(result)


@assets_purchase_page_bp.route("/logistics/unsubmitpurchaseordersave", methods=["POST"])
def unsubmit_purchase_order_save():
    purchase_divide_order_data = request.json.get("data")
    print(purchase_divide_order_data)
    for item in purchase_divide_order_data:
        purchase_divide_order_rid = item["purchaseDivideOrderId"]
        purchase_order_remark = item["remark"]
        purchase_order_environmental_request = item["evironmentalRequest"]
        shipment_address = item["shipmentAddress"]
        shipment_deadline = item["shipmentDeadline"]
        db.session.query(PurchaseDivideOrder).filter(
            PurchaseDivideOrder.purchase_divide_order_rid == purchase_divide_order_rid
        ).update(
            {
                "purchase_order_remark": purchase_order_remark,
                "purchase_order_environmental_request": purchase_order_environmental_request,
                "shipment_address": shipment_address,
                "shipment_deadline": shipment_deadline,
            }
        )
    db.session.commit()
    return jsonify({"status": "success"})


@assets_purchase_page_bp.route("/logistics/submitpurchaseorder", methods=["POST"])
def submit_purchase_order():
    purchase_order_id = request.json.get("purchaseOrderId")
    purchase_order_status = "1"
    db.session.query(PurchaseOrder).filter(
        PurchaseOrder.purchase_order_id == purchase_order_id
    ).update(
        {
            "purchase_order_status": purchase_order_status,
        }
    )
    db.session.flush()
    purchase_order_rid = db.session.query(PurchaseOrder).filter(
        PurchaseOrder.purchase_order_id == purchase_order_id
    ).first().purchase_order_rid
    query = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrder,
            AssetsPurchaseOrderItem,
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
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_id == purchase_order_id)
        .all()
    )
    for (
        purchase_divide_order,
        purchase_order,
        assets_item,
    ) in query:
        material_id = assets_item.material_id
        material_quantity = assets_item.purchase_amount
        material_specification = assets_item.material_specification
        material_model = assets_item.material_model
        color = assets_item.color
        if purchase_divide_order.purchase_divide_order_type == "N":
            material_storage = MaterialStorage(
                material_id=material_id,
                estimated_inbound_amount=material_quantity,
                actual_inbound_amount=0,
                current_amount=0,
                unit_price=0,
                material_outsource_status="0",
                material_specification=material_specification,
                material_model=material_model,
                material_storage_color=color,
                purchase_divide_order_id=purchase_divide_order.purchase_divide_order_id,
                order_id=purchase_order.order_id,
                order_shoe_id=purchase_order.order_shoe_id,
                craft_name=assets_item.craft_name,
            )
            db.session.add(material_storage)
        elif purchase_divide_order.purchase_divide_order_type == "S":
            quantity_list = [0 for _ in SHOESIZERANGE]
            for i, shoe_size in enumerate(SHOESIZERANGE):
                quantity_list[i] = getattr(assets_item, f"size_{shoe_size}_purchase_amount", 0) or 0
            print(quantity_list)
            material_total_quantity = sum(quantity_list)
            size_material_storage = SizeMaterialStorage(
                material_id=material_id,
                total_estimated_inbound_amount=material_total_quantity,
                unit_price=0,
                material_outsource_status="0",
                size_material_specification=material_specification,
                size_material_color=color,
                purchase_divide_order_id=purchase_divide_order.purchase_divide_order_id,
                order_id=purchase_order.order_id,
                order_shoe_id=purchase_order.order_shoe_id,
                craft_name=assets_item.craft_name,
                size_storage_type=assets_item.size_type,
            )
            for i, shoe_size in enumerate(SHOESIZERANGE):
                setattr(size_material_storage, f"size_{shoe_size}_estimated_inbound_amount", quantity_list[i])
            db.session.add(size_material_storage)
    purchase_divide_orders = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrder,
            AssetsPurchaseOrderItem,
            Material,
            Supplier,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(AssetsPurchaseOrderItem, AssetsPurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id)
        .join(Material, AssetsPurchaseOrderItem.material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_rid == purchase_order_rid)
        .all()
    )

    # Dictionary to keep track of processed PurchaseDivideOrders
    purchase_divide_order_dict = {}
    size_purchase_divide_order_dict = {}
    

    # Iterate through the query results and group items by PurchaseDivideOrder
    for (
        purchase_divide_order,
        purchase_order,
        assets_item,
        material,
        supplier,
    ) in purchase_divide_orders:
        purchase_order_id = purchase_divide_order.purchase_divide_order_rid
        print(purchase_order_id)
        if not os.path.exists(
            os.path.join(FILE_STORAGE_PATH, "单独采购订单", purchase_order_rid)
        ):
            os.makedirs(os.path.join(FILE_STORAGE_PATH, "单独采购订单", purchase_order_rid)) 
        if purchase_divide_order.purchase_divide_order_type == "N":
            if purchase_order_id not in purchase_divide_order_dict:
                purchase_divide_order_dict[purchase_order_id] = {
                    "供应商": supplier.supplier_name,
                    "日期": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "备注": purchase_divide_order.purchase_order_remark,
                    "环保要求": purchase_divide_order.purchase_order_environmental_request,
                    "发货地址": purchase_divide_order.shipment_address,
                    "交货期限": purchase_divide_order.shipment_deadline,
                    "订单信息": purchase_order_id,
                    "seriesData": [],
                }

            # Append the current PurchaseOrderItem to the 'seriesData' list of the relevant order
            purchase_divide_order_dict[purchase_order_id]["seriesData"].append(
                {
                    "物品名称": (
                        material.material_name
                        + " "
                        + (assets_item.material_model if assets_item.material_model else "")
                        + " "
                        + (
                            assets_item.material_specification
                            if assets_item.material_specification
                            else ""
                        )
                        + " "
                        + (assets_item.color if assets_item.color else "")
                    ),
                    "数量": assets_item.purchase_amount,
                    "单位": material.material_unit,
                    "备注": assets_item.remark,
                    "用途说明": "",
                }
            )
        elif purchase_divide_order.purchase_divide_order_type == "S":
            batch_info_type = db.session.query(BatchInfoType).filter(BatchInfoType.batch_info_type_name == assets_item.size_type).first()
            shoe_size_list = []
            for i in SHOESIZERANGE:
                if getattr(batch_info_type, f"size_{i}_name") is not None:
                    shoe_size_list.append({i:getattr(batch_info_type, f"size_{i}_name")})

            if purchase_order_id not in size_purchase_divide_order_dict:
                size_purchase_divide_order_dict[purchase_order_id] = {
                    "供应商": supplier.supplier_name,
                    "日期": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "备注": purchase_divide_order.purchase_order_remark,
                    "环保要求": purchase_divide_order.purchase_order_environmental_request,
                    "发货地址": purchase_divide_order.shipment_address,
                    "交货期限": purchase_divide_order.shipment_deadline,
                    "订单信息": purchase_order_id,
                    "seriesData": [],
                }

            # Append the current PurchaseOrderItem to the 'seriesData' list of the relevant order
            obj = {
                "物品名称": (
                    material.material_name
                    + " "
                    + (assets_item.material_model if assets_item.material_model else "")
                    + " "
                    + (
                        assets_item.material_specification
                        if assets_item.material_specification
                        else ""
                    )
                    + " "
                    + (assets_item.color if assets_item.color else "")
                ),
                "备注": assets_item.remark,
            }
            for size_dic in shoe_size_list:
                for size, size_name in size_dic.items():
                    obj[size_name] = getattr(assets_item, f"size_{size}_purchase_amount")
            size_purchase_divide_order_dict[purchase_order_id]["seriesData"].append(obj)
    generated_files = []
    # Convert the dictionary to a list
    template_path = os.path.join(FILE_STORAGE_PATH, "标准采购订单.xlsx")
    size_template_path = os.path.join(FILE_STORAGE_PATH, "新标准采购订单尺码版.xlsx")
    for purchase_order_id, data in purchase_divide_order_dict.items():
        new_file_path = os.path.join(
            FILE_STORAGE_PATH,
            "单独采购订单",
            purchase_order_rid,
            purchase_order_id + "_" + data["供应商"] + ".xlsx",
        )
        generate_excel_file(template_path, new_file_path, data)
        generated_files.append(new_file_path)
    for purchase_order_id, data in size_purchase_divide_order_dict.items():
        if not os.path.exists(
            os.path.join(FILE_STORAGE_PATH, "单独采购订单", purchase_order_id)
        ):
            os.makedirs(os.path.join(FILE_STORAGE_PATH, "单独采购订单", purchase_order_id)) 
        new_file_path = os.path.join(
            FILE_STORAGE_PATH,
            "单独采购订单",
            purchase_order_rid,
            purchase_order_id + "_" + data["供应商"] + ".xlsx",
        )
        generate_size_excel_file(size_template_path, new_file_path, data)
        generated_files.append(new_file_path)
    zip_file_path = os.path.join(
        FILE_STORAGE_PATH,
        "单独采购订单",
        str(purchase_order_rid),
        "独立采购订单.zip",
    )
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        for file in generated_files:
            filename = os.path.basename(file)
            purchase_order_id = filename.split("_")[0]  # Get the part before "_供应商"
            zipf.write(file, filename)  # Add the file to the zip
    db.session.commit()
    return jsonify({"status": "success"})


@assets_purchase_page_bp.route(
    "/logistics/editsavedpurchaseorderitems", methods=["POST"]
)
def edit_saved_purchase_order_items():
    try:
        purchase_order_id = request.json.get("purchaseOrderId")
        material_list = request.json.get("data")
        purchase_divide_order_type = request.json.get("purchaseDivideOrderType")

        # Fetch the corresponding purchase_order
        purchase_order = (
            db.session.query(PurchaseOrder)
            .filter(PurchaseOrder.purchase_order_id == purchase_order_id)
            .first()
        )

        if not purchase_order:
            return (
                jsonify({"status": "error", "message": "Purchase order not found"}),
                404,
            )

        # change purchase order
        purchase_order.purchase_order_type = request.json.get("purchaseOrderType")
        if purchase_order.purchase_order_type == "O":
            purchase_order.order_id = request.json.get("orderId")
            purchase_order.order_shoe_id = None
            purchase_order.purchase_order_rid = (
                purchase_order.purchase_order_rid[:-1] + "O"
            )
        elif purchase_order.purchase_order_type == "X":
            purchase_order.order_id = request.json.get("orderId")
            purchase_order.order_shoe_id = request.json.get("orderShoeId")
            purchase_order.purchase_order_rid = (
                purchase_order.purchase_order_rid[:-1] + "X"
            )
        elif purchase_order.purchase_order_type == "I":
            purchase_order.order_id = None
            purchase_order.order_shoe_id = None
            purchase_order.purchase_order_rid = (
                purchase_order.purchase_order_rid[:-1] + "I"
            )
        else:
            return jsonify({"message": "invalid purchase type"}), 400

        # Delete all related AssetsPurchaseOrderItems and PurchaseDivideOrders
        db.session.query(AssetsPurchaseOrderItem).filter(
            AssetsPurchaseOrderItem.purchase_divide_order_id.in_(
                db.session.query(PurchaseDivideOrder.purchase_divide_order_id).filter(
                    PurchaseDivideOrder.purchase_order_id
                    == purchase_order.purchase_order_id
                )
            )
        ).delete()

        db.session.query(PurchaseDivideOrder).filter(
            PurchaseDivideOrder.purchase_order_id == purchase_order.purchase_order_id
        ).delete()

        db.session.flush()

        # Add new items as per the new data
        material_list_sorted = sorted(material_list, key=itemgetter("supplierName"))

        # Group the list by 'supplierName'
        grouped_materials = {}
        for supplier_name, items in groupby(
            material_list_sorted, key=itemgetter("supplierName")
        ):
            grouped_materials[supplier_name] = list(items)

        for supplier_name, items in grouped_materials.items():
            supplier_id = (
                db.session.query(Supplier)
                .filter(Supplier.supplier_name == supplier_name)
                .first()
                .supplier_id
            )
            supplier_id_str = str(supplier_id).zfill(4)

            purchase_divide_order_rid = (
                purchase_order.purchase_order_rid + supplier_id_str
            )
            purchase_divide_order = PurchaseDivideOrder(
                purchase_divide_order_rid=purchase_divide_order_rid,
                purchase_order_id=purchase_order.purchase_order_id,
                purchase_divide_order_type=purchase_divide_order_type,
            )
            db.session.add(purchase_divide_order)
            db.session.flush()

            purchase_divide_order_id = purchase_divide_order.purchase_divide_order_id

            # Add assets items
            for item in items:
                material_name = item["materialName"]
                material_info = (
                    db.session.query(Material, Supplier)
                    .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                    .filter(
                        Material.material_name == material_name,
                        Supplier.supplier_name == supplier_name,
                    )
                    .first()
                )

                material_id = material_info.Material.material_id
                material_specification = item["materialSpecification"]
                material_model = item["materialModel"]
                color = item["color"]
                remark = item["comment"]

                if purchase_divide_order_type == "N":
                    material_quantity = item["purchaseAmount"]
                    assets_item = AssetsPurchaseOrderItem(
                        purchase_divide_order_id=purchase_divide_order_id,
                        material_id=material_id,
                        purchase_amount=material_quantity,
                        material_specification=material_specification,
                        material_model=material_model,
                        color=color,
                        remark=remark,
                        craft_name=item["craftName"],
                        size_type="N",
                    )
                    db.session.add(assets_item)
                elif purchase_divide_order_type == "S":
                    material_quantities = [
                        item["sizeInfo"][i]["purchaseAmount"] for i in range(11)
                    ]
                    total_quantity = sum(material_quantities)
                    assets_item = AssetsPurchaseOrderItem(
                        purchase_divide_order_id=purchase_divide_order_id,
                        material_id=material_id,
                        purchase_amount=total_quantity,
                        size_35_purchase_amount=material_quantities[0],
                        size_36_purchase_amount=material_quantities[1],
                        size_37_purchase_amount=material_quantities[2],
                        size_38_purchase_amount=material_quantities[3],
                        size_39_purchase_amount=material_quantities[4],
                        size_40_purchase_amount=material_quantities[5],
                        size_41_purchase_amount=material_quantities[6],
                        size_42_purchase_amount=material_quantities[7],
                        size_43_purchase_amount=material_quantities[8],
                        size_44_purchase_amount=material_quantities[9],
                        size_45_purchase_amount=material_quantities[10],
                        material_specification=material_specification,
                        material_model=material_model,
                        color=color,
                        remark=remark,
                        craft_name=item["craftName"],
                        size_type="E",
                    )
                    db.session.add(assets_item)

        db.session.commit()
        return jsonify({"status": "success"})

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        db.session.close()


@assets_purchase_page_bp.route(
    "/logistics/deleteunsubmitpurchaseorder", methods=["DELETE"]
)
def delete_unsubmit_purchase_order():
    try:
        purchase_order_id = request.args.get("purchaseOrderId")

        # Fetch the corresponding purchase_order
        purchase_order = (
            db.session.query(PurchaseOrder)
            .filter(PurchaseOrder.purchase_order_id == purchase_order_id)
            .first()
        )

        if not purchase_order:
            return (
                jsonify({"status": "error", "message": "Purchase order not found"}),
                404,
            )

        # Delete all related AssetsPurchaseOrderItems and PurchaseDivideOrders
        db.session.query(AssetsPurchaseOrderItem).filter(
            AssetsPurchaseOrderItem.purchase_divide_order_id.in_(
                db.session.query(PurchaseDivideOrder.purchase_divide_order_id).filter(
                    PurchaseDivideOrder.purchase_order_id
                    == purchase_order.purchase_order_id
                )
            )
        ).delete()

        db.session.query(PurchaseDivideOrder).filter(
            PurchaseDivideOrder.purchase_order_id == purchase_order.purchase_order_id
        ).delete()

        # Delete the purchase_order
        db.session.delete(purchase_order)

        # Commit the deletions
        db.session.commit()
        return jsonify({"status": "success"})
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@assets_purchase_page_bp.route("/logistics/getallmaterialtypes", methods=["GET"])
def get_all_material_types():
    try:
        response = (
            db.session.query(MaterialType, MaterialWarehouse)
            .join(
                MaterialWarehouse,
                MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id,
            )
            .all()
        )
        result = []
        for row in response:
            material_type, warehouse = row
            result.append(
                {
                    "materialTypeId": material_type.material_type_id,
                    "materialTypeName": material_type.material_type_name,
                    "warehouseId": warehouse.material_warehouse_id,
                    "warehouseName": warehouse.material_warehouse_name,
                }
            )
        return result
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@assets_purchase_page_bp.route("/logistics/downloadassetzip", methods=["GET"])
def download_asset_zip():
    purchase_order_rid = request.args.get("purchaseOrderRId")
    zip_file_path = os.path.join(
        FILE_STORAGE_PATH,
        "单独采购订单",
        purchase_order_rid,
        "独立采购订单.zip",
    )
    new_file_name = f"{purchase_order_rid}_独立采购订单.zip"
    return send_file(zip_file_path, as_attachment=True, download_name=new_file_name)

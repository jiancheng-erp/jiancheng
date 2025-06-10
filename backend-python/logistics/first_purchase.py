import copy
import datetime
import os
import zipfile
from itertools import groupby
from operator import itemgetter
import json
from decimal import Decimal

from api_utility import randomIdGenerater
from app_config import db
from business.batch_info_type import get_order_batch_type_helper
from constants import SHOESIZERANGE, PO_STATUS, PO_STATUS_TO_INT
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from flask import Blueprint, jsonify, request, send_file, current_app
from general_document.material_statistics import generate_material_statistics_file
from general_document.purchase_divide_order import generate_excel_file
from general_document.size_purchase_divide_order import generate_size_excel_file
from general_document.cutmodel_purchase_divide_order import (
    generate_cut_model_excel_file,
)
from general_document.last_purchase_divide_order import generate_last_excel_file
from general_document.package_purchase_divide_order import generate_package_excel_file
from models import *
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.expression import case

first_purchase_bp = Blueprint("first_purrchase_bp", __name__)

material_order = case(
    (ProductionInstructionItem.material_type == "S", 1),
    (ProductionInstructionItem.material_type == "I", 2),
    (ProductionInstructionItem.material_type == "O", 3),
    (ProductionInstructionItem.material_type == "M", 4),
    (ProductionInstructionItem.material_type == "H", 5),
    else_=6,  # Default for any other values (if any)
)


@first_purchase_bp.route("/firstpurchase/getordershoelist", methods=["GET"])
def get_order_shoe_list():
    order_id = request.args.get("orderid")

    # Querying the necessary data with joins and filters
    entities = (
        db.session.query(
            Order,
            OrderShoe,
            OrderShoeType,
            Shoe,
            ShoeType,
            Color,
            Bom,
            TotalBom,
            PurchaseOrder,
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Shoe, Shoe.shoe_id == ShoeType.shoe_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .outerjoin(TotalBom, OrderShoe.order_shoe_id == TotalBom.order_shoe_id)
        .outerjoin(
            Bom, OrderShoeType.order_shoe_type_id == Bom.order_shoe_type_id
        )  # Assuming BOM is optional
        .outerjoin(
            PurchaseOrder,
            (
                (PurchaseOrder.bom_id == TotalBom.total_bom_id)
                & (PurchaseOrder.purchase_order_type == "F")
            ),
        )
        .filter(Order.order_id == order_id)
        .filter(TotalBom.total_bom_rid.like("%TF"))
        .all()
    )

    # Initialize the result list
    result_dict = {}

    # Loop through the entities to build the result
    for entity in entities:
        (
            order,
            order_shoe,
            order_shoe_type,
            shoe,
            shoe_type,
            color,
            bom,
            total_bom,
            purchase_order,
        ) = entity
        status_string = ""
        statuses = (
            db.session.query(OrderShoeStatus, OrderShoeStatusReference)
            .join(
                OrderShoeStatusReference,
                OrderShoeStatus.current_status == OrderShoeStatusReference.status_id,
            )
            .filter(OrderShoeStatus.order_shoe_id == order_shoe.order_shoe_id)
            .all()
        )
        for status in statuses:
            status_string = (
                status_string + status.OrderShoeStatusReference.status_name + " "
            )
        if purchase_order:
            if purchase_order.purchase_order_status == "1":
                current_status = "已保存"
            elif purchase_order.purchase_order_status == "2":
                current_status = "已提交"
        else:
            current_status = "未填写"
        # Grouping by shoe_rid (inheritId) to avoid duplicate shoes
        # Initialize the result dictionary for the shoe if not already present
        if shoe.shoe_rid not in result_dict:
            result_dict[shoe.shoe_rid] = {
                "orderId": order.order_rid,
                "orderShoeId": order_shoe.order_shoe_id,
                "inheritId": shoe.shoe_rid,
                "currentStatus": current_status,
                "totalBomId": total_bom.total_bom_rid if total_bom else "未填写",
                "purchaseOrderId": (
                    purchase_order.purchase_order_rid if purchase_order else "未填写"
                ),
                "status": status_string,
                "customerId": order_shoe.customer_product_name,
                "designer": shoe.shoe_designer,
                "editter": order_shoe.adjust_staff,
                "typeInfos": [],  # Initialize list for type info (colors, etc.)
                "colorSet": set(),  # Initialize set to track colors and prevent duplicate entries
            }

        # Check if this color already exists in typeInfos
        existing_entry = next(
            (
                info
                for info in result_dict[shoe.shoe_rid]["typeInfos"]
                if info["color"] == color.color_name
            ),
            None,
        )

        # Prepare BOM and PurchaseOrder details
        first_bom_id = None
        first_bom_status = "未填写"
        first_purchase_order_id = None
        first_purchase_order_status = "未填写"
        second_bom_id = None
        second_bom_status = "未填写"
        second_purchase_order_id = None
        second_purchase_order_status = "未填写"

        # Set BOM details based on bom_type
        if bom:
            if bom.bom_type == 0:
                first_bom_id = bom.bom_rid
                first_bom_status = {
                    "1": "材料已保存",
                    "2": "材料已提交",
                    "3": "等待用量填写",
                    "4": "用量填写已保存",
                    "5": "用量填写已提交",
                    "6": "用量填写已下发",
                }.get(bom.bom_status, "未填写")
            elif bom.bom_type == 1:
                second_bom_id = bom.bom_rid
                second_bom_status = {"1": "已保存", "2": "已提交", "3": "已下发"}.get(
                    bom.bom_status, "未填写"
                )

        # Set PurchaseOrder details based on purchase_order_type
        if purchase_order:
            if purchase_order.purchase_order_type == "F":
                first_purchase_order_id = purchase_order.purchase_order_rid
                first_purchase_order_status = {
                    "1": "已保存",
                    "2": "已提交",
                    "3": "已下发",
                }.get(purchase_order.purchase_order_status, "未填写")
            elif purchase_order.purchase_order_type == "S":
                second_purchase_order_id = purchase_order.purchase_order_rid
                second_purchase_order_status = {
                    "1": "已保存",
                    "2": "已提交",
                    "3": "已下发",
                }.get(purchase_order.purchase_order_status, "未填写")

        # If the color entry already exists, update it with BOM details
        if existing_entry:
            print(existing_entry)
            # Update only if fields are not already filled to prevent overwriting
            if first_bom_id and existing_entry.get("firstBomId") == "未填写":
                existing_entry["firstBomId"] = first_bom_id
                existing_entry["firstBomStatus"] = first_bom_status
            if (
                first_purchase_order_id
                and existing_entry.get("firstPurchaseOrderId") == "未填写"
            ):
                existing_entry["firstPurchaseOrderId"] = first_purchase_order_id
                existing_entry["firstPurchaseOrderStatus"] = first_purchase_order_status

            if second_bom_id and existing_entry.get("secondBomId") == "未填写":
                existing_entry["secondBomId"] = second_bom_id
                existing_entry["secondBomStatus"] = second_bom_status
            if (
                second_purchase_order_id
                and existing_entry.get("secondPurchaseOrderId") == "未填写"
            ):
                existing_entry["secondPurchaseOrderId"] = second_purchase_order_id
                existing_entry["secondPurchaseOrderStatus"] = (
                    second_purchase_order_status
                )
        else:
            # If the color doesn't exist, create a new entry in typeInfos
            result_dict[shoe.shoe_rid]["typeInfos"].append(
                {
                    "orderShoeTypeId": order_shoe_type.order_shoe_type_id,
                    "orderShoeRid": shoe.shoe_rid,
                    "color": color.color_name,
                    "image": (
                        IMAGE_STORAGE_PATH + shoe_type.shoe_image_url
                        if shoe_type.shoe_image_url
                        else None
                    ),
                    "firstBomId": first_bom_id if first_bom_id else "未填写",
                    "firstBomStatus": first_bom_status,
                    "firstPurchaseOrderId": (
                        first_purchase_order_id if first_purchase_order_id else "未填写"
                    ),
                    "firstPurchaseOrderStatus": first_purchase_order_status,
                    "secondBomId": second_bom_id if second_bom_id else "未填写",
                    "secondBomStatus": second_bom_status,
                    "secondPurchaseOrderId": (
                        second_purchase_order_id
                        if second_purchase_order_id
                        else "未填写"
                    ),
                    "secondPurchaseOrderStatus": second_purchase_order_status,
                }
            )

        # Add the color to colorSet to prevent future duplicates
        result_dict[shoe.shoe_rid]["colorSet"].add(color.color_name)

    # Remove the colorSet before returning the result
    for shoe_rid in result_dict:
        result_dict[shoe_rid].pop("colorSet")

    # Convert result_dict to a list of values
    result = list(result_dict.values())

    return jsonify(result)


@first_purchase_bp.route("/firstpurchase/getnewpurchaseorderid", methods=["GET"])
def get_new_purchase_order_id():
    department_id = "01"
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    purchase_order_id = department_id + current_time_stamp + random_string + "F"
    return jsonify({"purchaseOrderId": purchase_order_id})


@first_purchase_bp.route("/firstpurchase/getshoebomitems", methods=["GET"])
def get_shoe_bom_items():
    bom_rid = request.args.get("bomrid")
    order_id = request.args.get("orderid")
    # get shoe size names
    size_name_info = get_order_batch_type_helper(order_id)
    material_order = case(
        (ProductionInstructionItem.material_type == "S", 1),
        (ProductionInstructionItem.material_type == "I", 2),
        (ProductionInstructionItem.material_type == "O", 3),
        (ProductionInstructionItem.material_type == "M", 4),
        (ProductionInstructionItem.material_type == "H", 5),
        else_=6,  # Default for any other values (if any)
    )
    # Query all Bom items under the given TotalBom, based on the bom_rid
    entities = (
        db.session.query(
            BomItem,
            Material,
            MaterialType,
            Supplier,
            PurchaseOrderItem,
            ProductionInstructionItem,
        )
        .join(Bom, BomItem.bom_id == Bom.bom_id)
        .join(TotalBom, Bom.total_bom_id == TotalBom.total_bom_id)
        .join(Material, Material.material_id == BomItem.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .outerjoin(
            PurchaseOrderItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id
        )
        .outerjoin(
            ProductionInstructionItem,
            ProductionInstructionItem.production_instruction_item_id
            == BomItem.production_instruction_item_id,
        )
        .filter(
            TotalBom.total_bom_rid == bom_rid,
            ProductionInstructionItem.material_type.in_(["S", "I", "O", "M", "H"]),
            Material.material_name != "烫底"
        )
        .order_by(material_order, Supplier.supplier_name, Material.material_name)
        .all()
    )

    # Dictionary to combine duplicated items
    combined_items = {}
    for entity in entities:
        (
            bom_item,
            material,
            material_type,
            supplier,
            purchase_order_item,
            production_instruction_item,
        ) = entity

        # Create a unique key for each item based on essential attributes
        key = (
            material_type.material_type_name,
            material.material_name,
            bom_item.material_model,
            bom_item.material_specification,
            bom_item.bom_item_color if bom_item.bom_item_color else "",
            supplier.supplier_name,
        )

        # Initialize sizeInfo structure for this item
        size_info_template = {
            f"{name_obj['label']}": {"approvalAmount": 0.00, "purchaseAmount": 0.00}
            for name_obj in size_name_info
        }
        inbound_material_id = (
            purchase_order_item.inbound_material_id
            if purchase_order_item
            else material.material_id
        )
        inbound_material_name = (
            db.session.query(Material)
            .filter(Material.material_id == inbound_material_id)
            .first()
            .material_name
        )
        # If key already exists, accumulate the data; otherwise, initialize
        if key not in combined_items:
            combined_items[key] = {
                "bomItemId": bom_item.bom_item_id,
                "purchaseOrderItemId": (
                    purchase_order_item.purchase_order_item_id
                    if purchase_order_item
                    else None
                ),
                "materialTypeId": material.material_type_id,
                "materialType": material_type.material_type_name,
                "materialProductionInstructionType": production_instruction_item.material_type,
                "materialId": material.material_id,
                "inboundMaterialId": inbound_material_id,
                "inboundUnit": (
                    purchase_order_item.inbound_unit
                    if purchase_order_item
                    else material.material_unit
                ),
                "materialName": material.material_name,
                "inboundMaterialName": inbound_material_name,
                "materialModel": (
                    purchase_order_item.material_model
                    if purchase_order_item
                    else bom_item.material_model
                ),
                "materialSpecification": (
                    purchase_order_item.material_specification
                    if purchase_order_item
                    else bom_item.material_specification
                ),
                "color": (
                    purchase_order_item.color
                    if purchase_order_item
                    else bom_item.bom_item_color
                ),
                "unit": material.material_unit,
                "unitUsage": bom_item.unit_usage
                or (0.00 if material.material_category == 0 else None),
                "approvalUsage": bom_item.total_usage or Decimal(0.00),
                "useDepart": bom_item.department_id,
                "purchaseAmount": (
                    purchase_order_item.purchase_amount
                    if purchase_order_item
                    else bom_item.total_usage
                ),
                "supplierId": supplier.supplier_id,
                "supplierName": supplier.supplier_name,
                "materialCategory": material.material_category,
                "remark": (
                    purchase_order_item.remark
                    if purchase_order_item
                    else bom_item.remark
                ),
                "sizeInfo": copy.deepcopy(
                    size_info_template
                ),  # Deep copy to ensure independence
                "warehouseUsageInfo": (
                    json.loads(purchase_order_item.related_selected_material_storage)
                    if purchase_order_item
                    else []
                ),
            }
        else:
            if combined_items[key]["purchaseOrderItemId"] is None:
                combined_items[key]["purchaseOrderItemId"] = (
                    purchase_order_item.purchase_order_item_id
                    if purchase_order_item
                    else None
                )
                combined_items[key]["bomItemId"] = (
                    bom_item.bom_item_id
                    if purchase_order_item
                    else combined_items[key]["bomItemId"]
                )
            combined_items[key]["approvalUsage"] += (
                bom_item.total_usage if bom_item.total_usage else Decimal(0.00)
            )
            combined_items[key]["purchaseAmount"] += (
                purchase_order_item.purchase_amount
                if purchase_order_item
                else bom_item.total_usage
            )

        # Accumulate data for each size in sizeInfo
        for i in range(len(size_name_info)):
            db_name = i + 34
            size_field = f"size_{db_name}_total_usage"
            purchase_field = f"size_{db_name}_purchase_amount"

            approval_amount = getattr(bom_item, size_field, 0.00) or 0.00
            purchase_amount = (
                getattr(purchase_order_item, purchase_field, 0.00)
                if purchase_order_item
                else 0.00
            )
            approval_amount = approval_amount if approval_amount is not None else 0.00
            purchase_amount = purchase_amount if purchase_amount is not None else 0.00

            combined_items[key]["sizeInfo"][f"{size_name_info[i]['label']}"][
                "approvalAmount"
            ] += approval_amount
            combined_items[key]["sizeInfo"][f"{size_name_info[i]['label']}"][
                "purchaseAmount"
            ] += purchase_amount

    # Format result for JSON response
    result = [
        {
            **value,
            "sizeInfo": [
                {
                    "size": size,
                    "approvalAmount": info["approvalAmount"],
                    "purchaseAmount": info["purchaseAmount"],
                }
                for size, info in value["sizeInfo"].items()
            ],
        }
        for value in combined_items.values()
    ]

    return jsonify(result)


@first_purchase_bp.route("/firstpurchase/savepurchase", methods=["POST"])
def save_purchase():
    bom_rid = request.json.get("bomRid")
    purchase_order_items = request.json.get("purchaseItems")
    purchase_order_rid = request.json.get("purchaseRid")
    total_bom = (
        db.session.query(TotalBom).filter(TotalBom.total_bom_rid == bom_rid).first()
    )
    total_bom_id = total_bom.total_bom_id
    order_shoe_id = total_bom.order_shoe_id
    order_shoe = (
        db.session.query(OrderShoe)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .first()
    )
    order_id = order_shoe.order_id
    purchase_order = PurchaseOrder(
        purchase_order_rid=purchase_order_rid,
        bom_id=total_bom_id,
        purchase_order_issue_date=datetime.datetime.now().strftime("%Y%m%d"),
        purchase_order_type="F",
        purchase_order_status="1",
        order_id=order_id,
        order_shoe_id=order_shoe_id,
    )
    db.session.add(purchase_order)
    db.session.flush()
    purchase_order_id = purchase_order.purchase_order_id
    material_list_sorted = sorted(purchase_order_items, key=itemgetter("supplierName"))
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

        purchase_divide_order_rid = purchase_order_rid + supplier_id_str
        purchase_divide_order = PurchaseDivideOrder(
            purchase_divide_order_rid=purchase_divide_order_rid,
            purchase_order_id=purchase_order_id,
            purchase_divide_order_type=(
                "N" if items[0]["materialCategory"] == 0 else "S"
            ),
            purchase_order_remark="",
            purchase_order_environmental_request="",
            shipment_address="温州市瓯海区梧田工业基地镇南路8号（健诚集团）",
            shipment_deadline="请在7-10日内交货",
        )
        db.session.add(purchase_divide_order)
        db.session.flush()

        purchase_divide_order_id = purchase_divide_order.purchase_divide_order_id

        for item in items:
            purchase_order_item = PurchaseOrderItem(
                purchase_divide_order_id=purchase_divide_order_id,
                bom_item_id=item["bomItemId"],
            )
            if items[0]["materialCategory"] == 0:
                purchase_order_item.purchase_amount = item["purchaseAmount"]
                purchase_order_item.approval_amount = item["approvalUsage"]
            else:
                material_quantity = 0
                approval_quantity = 0
                for i in range(len(item["sizeInfo"])):
                    name = i + 34
                    material_quantity += item["sizeInfo"][i]["purchaseAmount"]
                    approval_quantity += item["sizeInfo"][i]["approvalAmount"]
                    setattr(
                        purchase_order_item,
                        f"size_{name}_purchase_amount",
                        item["sizeInfo"][i]["purchaseAmount"],
                    )
                setattr(purchase_order_item, "purchase_amount", material_quantity)
                setattr(purchase_order_item, "approval_amount", approval_quantity)

            # find bom item
            bom_item = (
                db.session.query(BomItem)
                .filter(BomItem.bom_item_id == item["bomItemId"])
                .first()
            )
            # in case of switching new material and supplier, update the bom item
            purchase_order_item.material_specification = item["materialSpecification"]
            purchase_order_item.material_model = item["materialModel"]
            purchase_order_item.color = item["color"]
            purchase_order_item.inbound_unit = item["inboundUnit"]
            purchase_order_item.material_id = bom_item.material_id
            purchase_order_item.size_type = bom_item.size_type
            purchase_order_item.craft_name = bom_item.craft_name
            purchase_order_item.remark = item["remark"]
            purchase_order_item.related_selected_material_storage = json.dumps(
                item["warehouseUsageInfo"]
            )
            # find supplier id
            supplier_id = (
                db.session.query(Supplier)
                .filter(Supplier.supplier_name == item["supplierName"])
                .first()
                .supplier_id
            )
            # find material with supplier id
            material = (
                db.session.query(Material)
                .filter(Material.material_name == item["inboundMaterialName"])
                .filter(Material.material_supplier == supplier_id)
                .first()
            )
            if not material:
                material = Material(
                    material_name=item["inboundMaterialName"],
                    material_supplier=supplier_id,
                    material_unit=item["inboundUnit"],
                    material_type_id=item["materialTypeId"],
                    material_usage_department="1",
                )
                db.session.add(material)
                db.session.flush()
            purchase_order_item.inbound_material_id = material.material_id
            db.session.add(purchase_order_item)
            # use warehouseUsageInfo to update the storage
            if len(item["warehouseUsageInfo"]) > 0:
                for storage in item["warehouseUsageInfo"]:
                    storage_id = storage["materialStorageId"]
                    storage_amount = storage["useAmount"]
                    if storage["type"] == 0:
                        material_storage = (
                            db.session.query(MaterialStorage)
                            .filter(MaterialStorage.material_storage_id == storage_id)
                            .first()
                        )
                        material_storage.current_amount -= storage_amount
                    else:
                        size_material_storage = (
                            db.session.query(SizeMaterialStorage)
                            .filter(
                                SizeMaterialStorage.size_material_storage_id
                                == storage_id
                            )
                            .first()
                        )
                        size_material_storage.total_current_amount -= storage_amount
                db.session.flush()
    # set the order shoe status to 1
    order_shoe_status = (
        db.session.query(OrderShoeStatus)
        .filter(OrderShoeStatus.order_shoe_id == order_shoe_id, OrderShoeStatus.current_status == 6)
        .first()
    )
    if not order_shoe_status:
        return jsonify({"message": "Order shoe status not found"}), 404
    order_shoe_status.current_status_value = 1
    db.session.commit()
    return jsonify({"status": "success"})


@first_purchase_bp.route("/firstpurchase/getpurchasedivideorders", methods=["GET"])
def get_purchase_divide_orders():
    purchase_order_id = request.args.get("purchaseOrderId")

    # Fetch the data from the database
    query = (
        db.session.query(
            PurchaseDivideOrder,
            TotalPurchaseOrder,
            PurchaseOrder,
            PurchaseOrderItem,
            BomItem,
            ProductionInstructionItem,
            Material,
            MaterialType,
            Supplier,
        )
        .outerjoin(
            TotalPurchaseOrder,
            PurchaseDivideOrder.total_purchase_order_id
            == TotalPurchaseOrder.total_purchase_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(
            PurchaseOrderItem,
            PurchaseDivideOrder.purchase_divide_order_id
            == PurchaseOrderItem.purchase_divide_order_id,
        )
        .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .join(
            ProductionInstructionItem,
            BomItem.production_instruction_item_id
            == ProductionInstructionItem.production_instruction_item_id,
        )
        .join(Material, PurchaseOrderItem.inbound_material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_rid == purchase_order_id)
        .order_by(
            material_order,
        )
        .all()
    )

    # Group the results by purchase_divide_order_rid
    grouped_results = {}
    for (
        purchase_divide_order,
        total_purchase_order,
        purchase_order,
        purchase_order_item,
        bom_item,
        production_instruction_item,
        material,
        material_type,
        supplier,
    ) in query:
        divide_order_rid = purchase_divide_order.purchase_divide_order_rid
        if divide_order_rid not in grouped_results:
            if total_purchase_order:
                if total_purchase_order.total_purchase_order_status == "1":
                    purchase_divide_order_status = "已保存"
                elif total_purchase_order.total_purchase_order_status == "2":
                    purchase_divide_order_status = "已下发"
                else:
                    purchase_divide_order_status = "未处理"
            else:
                purchase_divide_order_status = "未处理"
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
                "purchaseDivideOrderStatus": purchase_divide_order_status,
            }

        # Append the assets item details to the corresponding group
        obj = {
            "materialId": purchase_order_item.inbound_material_id,
            "materialType": material_type.material_type_name,
            "materialName": material.material_name,
            "materialModel": purchase_order_item.material_model,
            "materialSpecification": purchase_order_item.material_specification,
            "color": purchase_order_item.color,
            "unit": material.material_unit,
            "purchaseAmount": purchase_order_item.purchase_amount,
            "remark": purchase_order_item.remark,
            "sizeType": purchase_order_item.size_type,
        }
        for size in SHOESIZERANGE:
            obj[f"size{size}Amount"] = getattr(
                purchase_order_item, f"size_{size}_purchase_amount"
            )
        grouped_results[divide_order_rid]["assetsItems"].append(obj)

    # Convert the grouped results to a list
    result = list(grouped_results.values())

    return jsonify(result)


@first_purchase_bp.route("/firstpurchase/editpurchaseitems", methods=["POST"])
def edit_purchase_items():
    purchase_items = request.json.get("purchaseItems")
    for item in purchase_items:
        entities = (
            db.session.query(PurchaseOrderItem, Material)
            .join(Material, PurchaseOrderItem.material_id == Material.material_id)
            .filter(
                PurchaseOrderItem.purchase_order_item_id == item["purchaseOrderItemId"]
            )
            .first()
        )
        purchase_order_item, material = entities
        purchase_order_item.purchase_amount = item["purchaseAmount"]
        for i in range(len(item["sizeInfo"])):
            setattr(
                purchase_order_item,
                f"size_{i}_purchase_amount",
                item["sizeInfo"][i]["purchaseAmount"],
            )
        purchase_order_item.material_specification = item["materialSpecification"]
        purchase_order_item.material_model = item["materialModel"]
        purchase_order_item.color = item["color"]
        purchase_order_item.inbound_unit = item["inboundUnit"]
        purchase_order_item.remark = item["remark"]
        # find supplier id
        supplier_id = (
            db.session.query(Supplier)
            .filter(Supplier.supplier_name == item["supplierName"])
            .first()
            .supplier_id
        )
        # find material with supplier id
        material = (
            db.session.query(Material)
            .filter(Material.material_name == item["inboundMaterialName"])
            .filter(Material.material_supplier == supplier_id)
            .first()
        )
        if not material:
            material = Material(
                material_name=item["inboundMaterialName"],
                material_supplier=supplier_id,
                material_unit=item["inboundUnit"],
                material_type_id=item["materialTypeId"],
                material_usage_department="1",
            )
            db.session.add(material)
            db.session.flush()
        purchase_order_item.inbound_material_id = material.material_id
        if purchase_order_item.related_selected_material_storage:
            # revert the storage
            for storage in json.loads(
                purchase_order_item.related_selected_material_storage
            ):
                storage_id = storage["materialStorageId"]
                storage_amount = storage["useAmount"]
                material_storage = (
                    db.session.query(MaterialStorage)
                    .filter(MaterialStorage.material_storage_id == storage_id)
                    .first()
                )
                material_storage.current_amount += storage_amount
            db.session.flush()
        purchase_order_item.related_selected_material_storage = json.dumps(
            item["warehouseUsageInfo"]
        )
        if len(item["warehouseUsageInfo"]) > 0:
            for storage in item["warehouseUsageInfo"]:
                storage_id = storage["materialStorageId"]
                storage_amount = storage["useAmount"]
                if storage["type"] == 0:
                    material_storage = (
                        db.session.query(MaterialStorage)
                        .filter(MaterialStorage.material_storage_id == storage_id)
                        .first()
                    )
                    material_storage.current_amount -= storage_amount
                else:
                    size_material_storage = (
                        db.session.query(SizeMaterialStorage)
                        .filter(
                            SizeMaterialStorage.size_material_storage_id == storage_id
                        )
                        .first()
                    )
                    size_material_storage.total_current_amount -= storage_amount
            db.session.flush()

    db.session.commit()
    return jsonify({"status": "success"})


@first_purchase_bp.route("/purchaseorder/reverttooriginalbomitem", methods=["PATCH"])
def revert_to_original_bom_item():
    bom_ids = request.get_json()
    response = (
        db.session.query(PurchaseOrderItem, BomItem, ProductionInstructionItem)
        .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .join(
            ProductionInstructionItem,
            BomItem.production_instruction_item_id
            == ProductionInstructionItem.production_instruction_item_id,
        )
        .filter(BomItem.bom_item_id.in_(bom_ids))
        .all()
    )
    for purchase_order_item, bom_item, production_instruction_item in response:
        bom_item.material_specification = (
            production_instruction_item.material_specification
        )
        bom_item.material_model = production_instruction_item.material_model
        bom_item.bom_item_color = production_instruction_item.color
        bom_item.material_id = production_instruction_item.material_id
        bom_item.material_second_type = production_instruction_item.material_second_type
    db.session.commit()
    return jsonify({"status": "success"})


@first_purchase_bp.route("/firstpurchase/savepurchasedivideorders", methods=["POST"])
def save_purchase_divide_orders():
    purchase_divide_orders = request.json.get("purchaseDivideOrders")
    for order in purchase_divide_orders:
        purchase_divide_order = (
            db.session.query(PurchaseDivideOrder)
            .filter(
                PurchaseDivideOrder.purchase_divide_order_rid
                == order["purchaseDivideOrderId"]
            )
            .first()
        )
        purchase_divide_order.purchase_order_remark = order["remark"]
        purchase_divide_order.purchase_order_environmental_request = order[
            "evironmentalRequest"
        ]
        purchase_divide_order.shipment_address = order["shipmentAddress"]
        purchase_divide_order.shipment_deadline = order["shipmentDeadline"]
        db.session.commit()
    return jsonify({"status": "success"})


@first_purchase_bp.route("/firstpurchase/submitpurchasedivideorders", methods=["POST"])
def submit_purchase_divide_orders():
    purchase_order_id = request.json.get("purchaseOrderId")
    order_info = (
        db.session.query(PurchaseOrder, TotalBom, OrderShoe, Order, Shoe)
        .join(TotalBom, TotalBom.total_bom_id == PurchaseOrder.bom_id)
        .join(OrderShoe, OrderShoe.order_shoe_id == TotalBom.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(PurchaseOrder.purchase_order_rid == purchase_order_id)
        .first()
    )
    order_id = order_info.Order.order_id
    order_shoe_id = order_info.OrderShoe.order_shoe_id
    order_rid = order_info.Order.order_rid
    order_shoe_rid = order_info.Shoe.shoe_rid
    order_size_table = order_info.Order.order_size_table
    order_size_dict = json.loads(order_size_table)
    is_craft_existed = (
        db.session.query(CraftSheet)
        .filter(CraftSheet.order_shoe_id == order_shoe_id)
        .first()
    )
    batch_info_type_name = (
        db.session.query(BatchInfoType)
        .join(Order, BatchInfoType.batch_info_type_id == Order.batch_info_type_id)
        .filter(Order.order_id == order_id)
        .first()
        .batch_info_type_name
    )
    materials_data = []
    query = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrder,
            PurchaseOrderItem,
            BomItem,
            ProductionInstructionItem,
            CraftSheetItem,
            Material,
            MaterialType,
            Supplier,
        )
        .join(
            PurchaseOrderItem,
            PurchaseDivideOrder.purchase_divide_order_id
            == PurchaseOrderItem.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .join(
            ProductionInstructionItem,
            BomItem.production_instruction_item_id
            == ProductionInstructionItem.production_instruction_item_id,
        )
        .outerjoin(
            CraftSheetItem,
            ProductionInstructionItem.production_instruction_item_id == CraftSheetItem.production_instruction_item_id,
        )
        .join(Material, PurchaseOrderItem.inbound_material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_rid == purchase_order_id)
        .all()
    )
    for (
        purchase_divide_order,
        purchase_order,
        purchase_order_item,
        bom_item,
        production_instruction_item,
        craft_sheet_item,
        material,
        material_type,
        supplier,
    ) in query:
        current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
        random_string = randomIdGenerater(6)
        supplier_id_string = str(supplier.supplier_id).zfill(4)
        total_purchase_order_rid = (
            "T" + current_time_stamp + random_string + "F" + supplier_id_string
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
        purchase_divide_order.total_purchase_order_id = (
            total_purchase_order.total_purchase_order_id
        )
        materials_data.append(
            {
                "supplier_name": supplier.supplier_name,
                "material_name": material.material_name,
                "model": purchase_order_item.material_model or "",
                "specification": purchase_order_item.material_specification or "",
                "approval_amount": purchase_order_item.approval_amount,  # Assuming bom_item has approval quantity
                "purchase_amount": purchase_order_item.purchase_amount,
            }
        )

        material_id = purchase_order_item.material_id
        material_quantity = purchase_order_item.purchase_amount
        material_specification = purchase_order_item.material_specification if purchase_order_item.material_specification else ''
        material_model = purchase_order_item.material_model if purchase_order_item.material_model else ''
        color = purchase_order_item.color if purchase_order_item.color else bom_item.bom_item_color
        remark = purchase_order_item.remark
        size_type = purchase_order_item.size_type
        if is_craft_existed:
            # Find the craft name from craft sheet item. If not exist, fallback to BOM item.
            craft_sheet_item = (
                db.session.query(CraftSheetItem)
                .filter(
                    CraftSheetItem.production_instruction_item_id == bom_item.production_instruction_item_id
                )
                .first()
            )

            if craft_sheet_item:
                original_crafts = set(filter(None, (craft_sheet_item.craft_name or "").split("@")))
            else:
                original_crafts = set()

            if production_instruction_item.material_type == "I":
                # Get all matching hotsole items
                similiar_hotsoles = (
                    db.session.query(ProductionInstructionItem)
                    .filter(
                        ProductionInstructionItem.material_id == production_instruction_item.material_id,
                        ProductionInstructionItem.material_model == production_instruction_item.material_model,
                        ProductionInstructionItem.material_specification == production_instruction_item.material_specification,
                        ProductionInstructionItem.color == production_instruction_item.color,
                        ProductionInstructionItem.order_shoe_type_id == production_instruction_item.order_shoe_type_id,
                        ProductionInstructionItem.material_type == "H",
                    )
                    .all()
                )

                hotsole_craft_names = set()
                for hotsole in similiar_hotsoles:
                    if hotsole.pre_craft_name:
                        hotsole_craft_names.update(hotsole.pre_craft_name.split("@"))

                combined_crafts = original_crafts.union(hotsole_craft_names)
                craft_name = "@".join(sorted(combined_crafts)) if combined_crafts else None
            else:
                craft_name = "@".join(sorted(original_crafts)) if original_crafts else None
        else:
            craft_name = bom_item.craft_name
        # don't create material storage if the quantity is 0
        if material_quantity == 0:
            continue
        if purchase_divide_order.purchase_divide_order_type == "N":
            material_storage = MaterialStorage(
                order_id=order_id,
                order_shoe_id=order_shoe_id,
                material_id=material_id,
                estimated_inbound_amount=material_quantity,
                actual_inbound_amount=0,
                department_id=bom_item.department_id,
                current_amount=0,
                unit_price=0,
                material_outsource_status="0",
                material_model=material_model,
                material_specification=material_specification,
                inbound_model=material_model,
                inbound_specification=material_specification,
                material_storage_color=color,
                total_purchase_order_id=total_purchase_order.total_purchase_order_id,
                craft_name=craft_name,
                production_instruction_item_id=bom_item.production_instruction_item_id,
                actual_inbound_material_id=purchase_order_item.inbound_material_id,
                actual_inbound_unit=purchase_order_item.inbound_unit,
            )
            db.session.add(material_storage)
        elif purchase_divide_order.purchase_divide_order_type == "S":
            quantity_map = {}
            for size in SHOESIZERANGE:
                quantity_map[f"size_{size}_quantity"] = getattr(
                    purchase_order_item, f"size_{size}_purchase_amount"
                )
            if "中底" in material.material_name:
                material_size_table = order_size_dict["中底"]
            elif "大底" in material.material_name:
                material_size_table = order_size_dict["大底"]
            else:
                material_size_table = order_size_dict["客人码"]
            size_material_storage = SizeMaterialStorage(
                order_id=order_id,
                order_shoe_id=order_shoe_id,
                material_id=material_id,
                total_estimated_inbound_amount=material_quantity,
                unit_price=0,
                material_outsource_status="0",
                department_id=bom_item.department_id,
                size_material_model=material_model,
                size_material_specification=material_specification,
                size_material_color=color,
                total_purchase_order_id=total_purchase_order.total_purchase_order_id,
                size_storage_type=batch_info_type_name,
                craft_name=craft_name,
                production_instruction_item_id=bom_item.production_instruction_item_id,
                shoe_size_columns=material_size_table,
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
        PurchaseOrder.purchase_order_rid == purchase_order_id
    ).update({"purchase_order_status": purchase_order_status})
    db.session.flush()
    purchase_divide_orders = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrderItem,
            PurchaseOrder,
            BomItem,
            ProductionInstructionItem,
            Material,
            Supplier,
        )
        .join(
            PurchaseOrderItem,
            PurchaseDivideOrder.purchase_divide_order_id
            == PurchaseOrderItem.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .join(
            ProductionInstructionItem,
            ProductionInstructionItem.production_instruction_item_id
            == BomItem.production_instruction_item_id,
        )
        .join(Material, PurchaseOrderItem.inbound_material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_rid == purchase_order_id)
        .all()
    )

    # Dictionary to keep track of processed PurchaseDivideOrders
    purchase_divide_order_dict = {}
    size_purchase_divide_order_dict = {}
    if (
        os.path.exists(
            os.path.join(FILE_STORAGE_PATH, order_rid, order_shoe_rid, "purchase_order")
        )
        == False
    ):
        os.mkdir(
            os.path.join(FILE_STORAGE_PATH, order_rid, order_shoe_rid, "purchase_order")
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
        purchase_order_item,
        purchase_order,
        bom_item,
        production_instruction_item,
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
                        + (
                            purchase_order_item.material_model
                            if purchase_order_item.material_model
                            else ""
                        )
                        + " "
                        + (
                            purchase_order_item.material_specification
                            if purchase_order_item.material_specification
                            else ""
                        )
                        + " "
                        + (
                            purchase_order_item.color
                            if purchase_order_item.color
                            else ""
                        )
                    ),
                    "型号": (
                        material.material_name
                        + " "
                        + purchase_order_item.material_model
                        if purchase_order_item.material_model
                        else ""
                    ),
                    "类别": (
                        purchase_order_item.material_specification
                        if purchase_order_item.material_specification
                        else ""
                    ),
                    "数量": purchase_order_item.purchase_amount,
                    "单位": material.material_unit,
                    "备注": purchase_order_item.remark,
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
                .join(
                    Order, Order.batch_info_type_id == BatchInfoType.batch_info_type_id
                )
                .filter(Order.order_id == order_id)
                .first()
            )

            # 1️⃣ 创建 "客人码" -> "实际尺码" 映射
            customer_size_map = {}  # { "7.5": 34, "8.0": 35, "8.5": 36 }
            for i in SHOESIZERANGE:
                size_name = getattr(
                    batch_info_type.BatchInfoType, f"size_{i}_name", None
                )
                if size_name:
                    customer_size_map[size_name] = (
                        i  # 例如 {"7.5": 34, "8.0": 35, "8.5": 36}
                    )

            # 2️⃣ 确保 `order_size_table` 至少有 `客人码`
            if "客人码" not in order_size_table or not order_size_table["客人码"]:
                order_size_table["客人码"] = list(
                    customer_size_map.keys()
                )  # 从 batch_info_type 生成客人码

            # 3️⃣ 根据 `material_name` 选择合适的尺码来源
            if "大底" in material.material_name:
                size_values = order_size_table.get(
                    "大底", order_size_table["客人码"]
                )  # 兜底使用 `客人码`
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
                    + (bom_item.material_model if bom_item.material_model else "")
                    + " "
                    + (
                        bom_item.material_specification
                        if bom_item.material_specification
                        else ""
                    )
                    + " "
                    + (bom_item.bom_item_color if bom_item.bom_item_color else "")
                ),
                "型号": (
                    material.material_name + " " + purchase_order_item.material_model
                    if purchase_order_item.material_model
                    else ""
                ),
                "类别": (
                    purchase_order_item.material_specification
                    if purchase_order_item.material_specification
                    else ""
                ),
                "备注": bom_item.remark,
            }
            for index, size_value in enumerate(size_values):
                customer_value = order_size_table["客人码"][index]
                if customer_value in customer_size_map:
                    actual_size = customer_size_map[customer_value]  # 例如 7.5 -> 34
                    obj[size_value] = getattr(
                        purchase_order_item, f"size_{actual_size}_purchase_amount", 0
                    )

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
    template_path = os.path.join(FILE_STORAGE_PATH, "材料统计表模板.xlsx")

    materials_output_path = os.path.join(
        FILE_STORAGE_PATH,
        order_rid,
        order_shoe_rid,
        "purchase_order",
        "材料统计表.xlsx",
    )

    generate_material_statistics_file(
        template_path=template_path,
        save_path=materials_output_path,
        order_rid=order_rid,
        order_shoe_rid=order_shoe_rid,
        customer_name=customer_name,
        materials_data=materials_data,
    )
    generated_files = []
    # Convert the dictionary to a list
    template_path = os.path.join(FILE_STORAGE_PATH, "标准采购订单.xlsx")
    size_template_path = os.path.join(FILE_STORAGE_PATH, "新标准采购订单尺码版.xlsx")
    for purchase_order_id, data in purchase_divide_order_dict.items():
        new_file_path = os.path.join(
            FILE_STORAGE_PATH,
            order_rid,
            order_shoe_rid,
            "purchase_order",
            purchase_order_id + "_" + data["供应商"] + ".xlsx",
        )
        generate_excel_file(template_path, new_file_path, data)
        generated_files.append(new_file_path)
    shoe_size_names = get_order_batch_type_helper(order_id)
    for purchase_order_id, data in size_purchase_divide_order_dict.items():
        new_file_path = os.path.join(
            FILE_STORAGE_PATH,
            order_rid,
            order_shoe_rid,
            "purchase_order",
            purchase_order_id + "_" + data["供应商"] + ".xlsx",
        )
        data["shoe_size_names"] = shoe_size_names
        generate_size_excel_file(size_template_path, new_file_path, data)
        generated_files.append(new_file_path)
    zip_file_path = os.path.join(
        FILE_STORAGE_PATH,
        order_rid,
        order_shoe_rid,
        "purchase_order",
        "一次采购订单.zip",
    )
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        for file in generated_files:
            # Extract purchase_order_id from the filename and check if it ends with 'F'
            filename = os.path.basename(file)
            purchase_order_id = filename.split("_")[0]  # Get the part before "_供应商"
            if len(purchase_order_id) >= 5 and purchase_order_id[-5] == "F":
                zipf.write(file, filename)  # Add the file to the zip

    processor: EventProcessor = current_app.config["event_processor"]
    try:
        event_arr = []
        for operation_id in [50, 51]:
            event = Event(
                staff_id=3,
                handle_time=datetime.datetime.now(),
                operation_id=operation_id,
                event_order_id=order_id,
                event_order_shoe_id=order_shoe_id,
            )
            processor.processEvent(event)
            event_arr.append(event)
    except Exception:
        return jsonify({"status": "event processor error"}), 500
    db.session.add_all(event_arr)
    db.session.commit()
    return jsonify({"status": "success"})


@first_purchase_bp.route("/firstpurchase/advanceprocess", methods=["POST"])
def advance_process():
    purchase_order_id = request.json.get("purchaseOrderId")
    purchase_order = (
        db.session.query(PurchaseOrder)
        .filter(PurchaseOrder.purchase_order_rid == purchase_order_id)
        .first()
    )
    purchase_order.purchase_order_status = "2"
    order_shoe_id = purchase_order.order_shoe_id
    order_id = purchase_order.order_id
    order_shoe_rid = (
        db.session.query(OrderShoe, Shoe)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .first()
        .Shoe.shoe_rid
    )
    order_rid = (
        db.session.query(Order).filter(Order.order_id == order_id).first().order_rid
    )
    materials_data = []
    query = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrder,
            PurchaseOrderItem,
            BomItem,
            Material,
            MaterialType,
            Supplier,
        )
        .join(
            PurchaseOrderItem,
            PurchaseDivideOrder.purchase_divide_order_id
            == PurchaseOrderItem.purchase_divide_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(PurchaseOrder.purchase_order_rid == purchase_order_id)
        .all()
    )
    for (
        purchase_divide_order,
        purchase_order,
        purchase_order_item,
        bom_item,
        material,
        material_type,
        supplier,
    ) in query:
        materials_data.append(
            {
                "supplier_name": supplier.supplier_name,
                "material_name": material.material_name,
                "model": purchase_order_item.material_model or "",
                "specification": purchase_order_item.material_specification or "",
                "approval_amount": purchase_order_item.total_usage,  # Assuming bom_item has approval quantity
                "purchase_amount": purchase_order_item.purchase_amount,
            }
        )
    customer_name = (
        db.session.query(Order, Customer)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .filter(Order.order_id == order_id)
        .first()
        .Customer.customer_name
    )
    template_path = os.path.join(FILE_STORAGE_PATH, "材料统计表模板.xlsx")

    materials_output_path = os.path.join(
        FILE_STORAGE_PATH,
        order_rid,
        order_shoe_rid,
        "purchase_order",
        "材料统计表.xlsx",
    )

    generate_material_statistics_file(
        template_path=template_path,
        save_path=materials_output_path,
        order_rid=order_rid,
        order_shoe_rid=order_shoe_rid,
        customer_name=customer_name,
        materials_data=materials_data,
    )
    db.session.flush()
    processor: EventProcessor = current_app.config["event_processor"]
    try:
        event_arr = []
        for operation_id in [50, 51]:
            event = Event(
                staff_id=3,
                handle_time=datetime.datetime.now(),
                operation_id=operation_id,
                event_order_id=order_id,
                event_order_shoe_id=order_shoe_id,
            )
            processor.processEvent(event)
            event_arr.append(event)
    except Exception:
        return jsonify({"status": "event processor error"}), 500
    db.session.add_all(event_arr)
    db.session.commit()
    return jsonify({"status": "success"})


@first_purchase_bp.route("/logistics/getmaterialstoragesimiliar", methods=["GET"])
def get_material_storage_similiar():
    material_id = request.args.get("materialId")
    material_model = request.args.get("materialModel")
    material = (
        db.session.query(Material).filter(Material.material_id == material_id).first()
    )
    material_category = material.material_category
    if material_category == 0:
        material_storage = (
            db.session.query(
                MaterialStorage, Material, Supplier, Order, OrderStatus, OrderShoe, Shoe
            )
            .join(Material, MaterialStorage.material_id == Material.material_id)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .outerjoin(Order, MaterialStorage.order_id == Order.order_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .outerjoin(
                OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id
            )
            .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(MaterialStorage.material_id == material_id)
            .filter(MaterialStorage.material_model == material_model)
            .filter(MaterialStorage.current_amount > 0)
            .filter(OrderStatus.order_current_status > 9)
            .all()
        )
        result = [
            {
                "similiarType": 0,
                "materialStorageId": storage.MaterialStorage.material_storage_id,
                "actualInboundAmount": storage.MaterialStorage.current_amount,
                "unitPrice": storage.MaterialStorage.unit_price,
                "craftName": storage.MaterialStorage.craft_name,
                "materialName": material.material_name,
                "materialModel": storage.MaterialStorage.material_model,
                "materialSpecification": storage.MaterialStorage.material_specification,
                "color": storage.MaterialStorage.material_storage_color,
                "unit": material.material_unit,
                "supplierName": storage.Supplier.supplier_name,
                "purchaseAmount": storage.MaterialStorage.current_amount,
                "orderRid": storage.Order.order_rid if storage.Order else "",
                "orderShoeRid": storage.Shoe.shoe_rid if storage.Shoe else "",
            }
            for storage in material_storage
        ]
    else:
        size_material_storage = (
            db.session.query(
                SizeMaterialStorage,
                Material,
                Supplier,
                Order,
                OrderStatus,
                OrderShoe,
                Shoe,
            )
            .join(Material, SizeMaterialStorage.material_id == Material.material_id)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .outerjoin(Order, SizeMaterialStorage.order_id == Order.order_id)
            .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
            .outerjoin(
                OrderShoe, SizeMaterialStorage.order_shoe_id == OrderShoe.order_shoe_id
            )
            .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(SizeMaterialStorage.material_id == material_id)
            .filter(SizeMaterialStorage.size_material_model == material_model)
            .filter(SizeMaterialStorage.total_current_amount > 0)
            .filter(OrderStatus.order_current_status > 9)
            .all()
        )
        result = [
            {
                "similiarType": 1,
                "materialStorageId": storage.SizeMaterialStorage.size_material_storage_id,
                "actualInboundAmount": storage.SizeMaterialStorage.total_current_amount,
                "unitPrice": storage.SizeMaterialStorage.unit_price,
                "craftName": storage.SizeMaterialStorage.craft_name,
                "materialName": material.material_name,
                "materialModel": storage.SizeMaterialStorage.size_material_model,
                "materialSpecification": storage.SizeMaterialStorage.size_material_specification,
                "color": storage.SizeMaterialStorage.size_material_color,
                "unit": material.material_unit,
                "supplierName": storage.Supplier.supplier_name,
                "purchaseAmount": storage.SizeMaterialStorage.total_current_amount,
                "orderRid": storage.Order.order_rid if storage.Order else "",
                "orderShoeRid": storage.Shoe.shoe_rid if storage.Shoe else "",
            }
            for storage in size_material_storage
        ]
    return jsonify(result)


@first_purchase_bp.route("/logistics/getselectedmaterialstorage", methods=["GET"])
def get_selected_material_storage():
    warehouseUsageInfo = request.args.get("warehouseUsageInfo")
    warehouseUsageInfo = json.loads(warehouseUsageInfo)
    result = []
    for item in warehouseUsageInfo:
        material_storage_id = item["materialStorageId"]
        similiar_type = item["similiarType"]
        if similiar_type == 0:
            material_storage = (
                db.session.query(
                    MaterialStorage,
                    Material,
                    Supplier,
                    Order,
                    OrderStatus,
                    OrderShoe,
                    Shoe,
                )
                .join(Material, MaterialStorage.material_id == Material.material_id)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .outerjoin(Order, MaterialStorage.order_id == Order.order_id)
                .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
                .outerjoin(
                    OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id
                )
                .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
                .filter(MaterialStorage.material_storage_id == material_storage_id)
                .first()
            )
            result.append(
                {
                    "similiarType": 0,
                    "materialStorageId": material_storage.MaterialStorage.material_storage_id,
                    "actualInboundAmount": material_storage.MaterialStorage.current_amount,
                    "unitPrice": material_storage.MaterialStorage.unit_price,
                    "craftName": material_storage.MaterialStorage.craft_name,
                    "materialName": material_storage.Material.material_name,
                    "materialModel": material_storage.MaterialStorage.material_model,
                    "materialSpecification": material_storage.MaterialStorage.material_specification,
                    "color": material_storage.MaterialStorage.material_storage_color,
                    "unit": material_storage.Material.material_unit,
                    "supplierName": material_storage.Supplier.supplier_name,
                    "purchaseAmount": material_storage.MaterialStorage.current_amount,
                    "orderRid": (
                        material_storage.Order.order_rid
                        if material_storage.Order
                        else ""
                    ),
                    "orderShoeRid": (
                        material_storage.Shoe.shoe_rid if material_storage.Shoe else ""
                    ),
                }
            )
        else:
            size_material_storage = (
                db.session.query(
                    SizeMaterialStorage,
                    Material,
                    Supplier,
                    Order,
                    OrderStatus,
                    OrderShoe,
                    Shoe,
                )
                .join(Material, SizeMaterialStorage.material_id == Material.material_id)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .outerjoin(Order, SizeMaterialStorage.order_id == Order.order_id)
                .outerjoin(OrderStatus, OrderStatus.order_id == Order.order_id)
                .outerjoin(
                    OrderShoe,
                    SizeMaterialStorage.order_shoe_id == OrderShoe.order_shoe_id,
                )
                .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
                .filter(
                    SizeMaterialStorage.size_material_storage_id == material_storage_id
                )
                .first()
            )
            result.append(
                {
                    "similiarType": 1,
                    "materialStorageId": size_material_storage.SizeMaterialStorage.size_material_storage_id,
                    "actualInboundAmount": size_material_storage.SizeMaterialStorage.total_current_amount,
                    "unitPrice": size_material_storage.SizeMaterialStorage.unit_price,
                    "craftName": size_material_storage.SizeMaterialStorage.craft_name,
                    "materialName": size_material_storage.Material.material_name,
                    "materialModel": size_material_storage.SizeMaterialStorage.size_material_model,
                    "materialSpecification": size_material_storage.SizeMaterialStorage.size_material_specification,
                    "color": size_material_storage.SizeMaterialStorage.size_material_color,
                    "unit": size_material_storage.Material.material_unit,
                    "supplierName": size_material_storage.Supplier.supplier_name,
                    "purchaseAmount": size_material_storage.SizeMaterialStorage.total_current_amount,
                    "orderRid": (
                        size_material_storage.Order.order_rid
                        if size_material_storage.Order
                        else ""
                    ),
                    "orderShoeRid": (
                        size_material_storage.Shoe.shoe_rid
                        if size_material_storage.Shoe
                        else ""
                    ),
                }
            )
    return jsonify(result)


@first_purchase_bp.route("/firstpurchase/downloadpurchaseorderzip", methods=["GET"])
def download_purchase_order_zip():
    order_rid = request.args.get("orderrid")
    order_shoe_rid = request.args.get("ordershoerid")
    zip_file_path = os.path.join(
        FILE_STORAGE_PATH,
        order_rid,
        order_shoe_rid,
        "purchase_order",
        "一次采购订单.zip",
    )
    new_name = order_rid + "_" + order_shoe_rid + "_一次采购订单.zip"
    return send_file(zip_file_path, as_attachment=True, download_name=new_name)


@first_purchase_bp.route("/firstpurchase/downloadmaterialstatistics", methods=["GET"])
def download_material_statistics():
    order_rid = request.args.get("orderrid")
    order_shoe_rid = request.args.get("ordershoerid")
    file_path = os.path.join(
        FILE_STORAGE_PATH,
        order_rid,
        order_shoe_rid,
        "purchase_order",
        "材料统计表.xlsx",
    )
    new_name = order_rid + "_" + order_shoe_rid + "_材料统计表.xlsx"
    return send_file(file_path, as_attachment=True, download_name=new_name)


@first_purchase_bp.route("/logistics/getallunit", methods=["GET"])
def get_all_unit():
    units = db.session.query(Unit).all()
    result = [{"label": unit.unit_name, "value": unit.unit_name} for unit in units]
    return jsonify(result)



@first_purchase_bp.route("/logistics/getallpurchaseorderitems", methods=["GET"])
def get_all_purchase_order_items():
    page = request.args.get("page", type=int, default=1)
    page_size = request.args.get("pageSize", type=int, default=10)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    material_name = request.args.get("materialName")
    material_model = request.args.get("materialModel")
    material_specification = request.args.get("materialSpecification")
    material_color = request.args.get("materialColor")
    supplier_name = request.args.get("supplierName")
    status = request.args.get("status")

    query = (
        db.session.query(PurchaseOrderItem, PurchaseOrder, Order, Shoe, Material, Supplier)
        .join(
            PurchaseDivideOrder, PurchaseDivideOrder.purchase_divide_order_id == PurchaseOrderItem.purchase_divide_order_id
        )
        .join(PurchaseOrder, PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id)
        .join(OrderShoe, PurchaseOrder.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(Material, PurchaseOrderItem.material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .order_by(Order.order_rid)
    )

    if order_rid:
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid:
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if material_name:
        query = query.filter(Material.material_name.ilike(f"%{material_name}%"))
    if material_model:
        query = query.filter(
            PurchaseOrderItem.material_model.ilike(f"%{material_model}%")
        )
    if material_specification:
        query = query.filter(
            PurchaseOrderItem.material_specification.ilike(
                f"%{material_specification}%"
            )
        )
    if material_color:
        query = query.filter(PurchaseOrderItem.color.ilike(f"%{material_color}%"))
    if supplier_name:
        query = query.filter(Supplier.supplier_name.ilike(f"%{supplier_name}%"))
    if status:
        query = query.filter(PurchaseOrder.purchase_order_status == PO_STATUS_TO_INT.get(status, 0))

    # Pagination
    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()

    result = []
    for row in response:
        item, purchase_order, order, shoe, material, supplier = row
        obj = {
            "orderRId": order.order_rid,
            "shoeRId": shoe.shoe_rid,
            "materialName": material.material_name,
            "materialModel": item.material_model,
            "materialSpecification": item.material_specification,
            "materialColor": item.color,
            "supplierName": supplier.supplier_name,
            "purchaseAmount": item.purchase_amount,
            "materialUnit": material.material_unit,
            "purchaseOrderStatus": PO_STATUS.get(
                purchase_order.purchase_order_status, "未填写"
            ),
        }
        result.append(obj)
    return {"result": result, "totalLength": count_result}
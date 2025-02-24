from flask import Blueprint, jsonify, request, send_file, current_app
from sqlalchemy.dialects.mysql import insert
import datetime
from app_config import app, db
from models import *
import os
from api_utility import randomIdGenerater
from event_processor import EventProcessor
from file_locations import IMAGE_STORAGE_PATH, FILE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from general_document.bom import generate_excel_file
from collections import defaultdict
from business.batch_info_type import get_order_batch_type_helper
from constants import SHOESIZERANGE

second_bom_bp = Blueprint("second_bom_bp", __name__)


@second_bom_bp.route("/secondbom/getnewbomid", methods=["GET"])
def get_new_bom_id():
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    bom_id = current_time_stamp + random_string + "F"
    return jsonify({"bomId": bom_id})


@second_bom_bp.route("/secondbom/getordershoes", methods=["GET"])
def get_order_second_bom():
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
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .outerjoin(
            Bom, OrderShoeType.order_shoe_type_id == Bom.order_shoe_type_id
        )  # Assuming BOM is optional
        .outerjoin(TotalBom, Bom.total_bom_id == TotalBom.total_bom_id)
        .outerjoin(PurchaseOrder, PurchaseOrder.bom_id == TotalBom.total_bom_id)
        .filter(Order.order_id == order_id)
        .all()
    )

    print(entities)

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

        # Grouping by shoe_rid (inheritId) to avoid duplicate shoes
        # Initialize the result dictionary for the shoe if not already present
        if shoe.shoe_rid not in result_dict:
            result_dict[shoe.shoe_rid] = {
                "orderId": order.order_rid,
                "orderShoeId": order_shoe.order_shoe_id,
                "inheritId": shoe.shoe_rid,
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
                existing_entry["firstPurchaseOrderId"] = first_purchase_order_id
                existing_entry["firstPurchaseOrderStatus"] = first_purchase_order_status

            if second_bom_id and existing_entry.get("secondBomId") == "未填写":
                existing_entry["secondBomId"] = second_bom_id
                existing_entry["secondBomStatus"] = second_bom_status
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


@second_bom_bp.route("/secondbom/getcurrentbom", methods=["GET"])
def get_current_bom():
    order_shoe_type_id = request.args.get("ordershoetypeid")
    bom = (
        db.session.query(Bom, OrderShoeType)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == "1")
        .first()
    )
    bom_id = bom.Bom.bom_id
    result = {
        "bomId": bom.Bom.bom_rid,
    }
    return jsonify(result)


@second_bom_bp.route("/secondbom/getcurrentbomitem", methods=["GET"])
def get_current_bom_item():
    order_shoe_type_id = request.args.get("ordershoetypeid")
    bom = (
        db.session.query(Bom, OrderShoeType)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == "1")
        .first()
    )
    bom_items = (
        db.session.query(BomItem, Material, MaterialType, Department, Supplier)
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .outerjoin(Department, BomItem.department_id == Department.department_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(BomItem.bom_id == bom.Bom.bom_id)
        .all()
    )
    # get shoe size name
    order_id = (
        db.session.query(Order.order_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
        .scalar()
    )
    shoe_size_names = get_order_batch_type_helper(order_id)
    result = []
    for row in bom_items:
        bom_item, material, material_type, department, supplier = row
        sizeInfo = []
        first_bom_item_record = (
            db.session.query(BomItem, Bom)
            .join(Bom, BomItem.bom_id == Bom.bom_id)
            .filter(
                Bom.order_shoe_type_id == order_shoe_type_id,
                Bom.bom_type == 0,
                BomItem.material_id == material.material_id,
                BomItem.material_model == bom_item.material_model,
                BomItem.material_specification == bom_item.material_specification,
            )
            .first()
        )
        if first_bom_item_record:
            first_bom_usage = first_bom_item_record.BomItem.unit_usage
        else:
            first_bom_usage = 0
        for i in range(len(shoe_size_names)):
            index = i + 34
            obj = {
                "size": shoe_size_names[i]["label"],
                "approvalAmount": (
                    getattr(bom_item, f"size_{index}_total_usage")
                    if getattr(bom_item, f"size_{index}_total_usage")
                    else 0.00
                ),
            }
            sizeInfo.append(obj)
        result.append(
            {
                "bomItemId": bom_item.bom_item_id,
                "materialName": material.material_name,
                "materialType": material_type.material_type_name,
                "materialModel": bom_item.material_model,
                "materialSpecification": bom_item.material_specification,
                "supplierName": supplier.supplier_name,
                "firstBomUsage": first_bom_usage,
                "useDepart": department.department_id if department else None,
                "pairs": bom_item.pairs if bom_item.pairs else 0.00,
                "craftName": bom_item.craft_name,
                "unitUsage": (
                    bom_item.unit_usage
                    if bom_item.unit_usage
                    else 0.00 if material.material_category == 0 else None
                ),
                "approvalUsage": bom_item.total_usage if bom_item.total_usage else 0.00,
                "unit": material.material_unit,
                "color": bom_item.bom_item_color,
                "comment": bom_item.remark,
                "materialCategory": material.material_category,
                "sizeInfo": sizeInfo,
            }
        )
    return jsonify(result)


@second_bom_bp.route("/secondbom/savebom", methods=["POST"])
def save_bom_usage():
    bom_rid = request.json.get("bomRid")
    bom_items = request.json.get("bomItems")
    bom = db.session.query(Bom).filter(Bom.bom_rid == bom_rid).first()
    bom.bom_status = "1"
    db.session.flush()
    for bom_item in bom_items:
        if not bom_item["bomItemId"]:
            material_id = (
                db.session.query(Material, Supplier)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .filter(
                    Material.material_name == bom_item["materialName"],
                    Supplier.supplier_name == bom_item["supplierName"],
                )
                .first()
                .Material.material_id
            )
            bom_item_entity = BomItem(
                bom_id=bom.bom_id,
                material_id=material_id,
                unit_usage=bom_item["unitUsage"],
                total_usage=bom_item["approvalUsage"],
                department_id=bom_item["useDepart"],
                material_model=(
                    bom_item["materialModel"] if bom_item["materialModel"] else ""
                ),
                remark=bom_item["comment"],
                material_specification=(
                    bom_item["materialSpecification"]
                    if bom_item["materialSpecification"]
                    else ""
                ),
                bom_item_add_type=1,
                bom_item_color=bom_item["color"] if bom_item["color"] else None,
                pairs=bom_item["pairs"] if bom_item["pairs"] else 0.00,
            )
            for i in range(len(bom_item["sizeInfo"])):
                setattr(
                    bom_item_entity,
                    f"size_{i}_total_usage",
                    bom_item["sizeInfo"][i]["approvalAmount"],
                )
            db.session.add(bom_item_entity)
            db.session.flush()
            bom_item["bomItemId"] = bom_item_entity.bom_item_id
        else:
            entity = (
                db.session.query(BomItem)
                .filter(BomItem.bom_item_id == bom_item["bomItemId"])
                .first()
            )
            for i in range(len(bom_item["sizeInfo"])):
                setattr(
                    entity,
                    f"size_{i}_total_usage",
                    bom_item["sizeInfo"][i]["approvalAmount"],
                )
            entity.total_usage = bom_item["approvalUsage"]
            entity.unit_usage = bom_item["unitUsage"]
            entity.remark = bom_item["comment"] if bom_item["comment"] else ""
            entity.department_id = bom_item["useDepart"]
            entity.material_model = (
                bom_item["materialModel"] if bom_item["materialModel"] else None
            )
            entity.material_specification = (
                bom_item["materialSpecification"]
                if bom_item["materialSpecification"]
                else None
            )
            entity.bom_item_color = bom_item["color"] if bom_item["color"] else None
            entity.bom_item_add_type = 1
            entity.pairs = bom_item["pairs"] if bom_item["pairs"] else 0.00
            db.session.flush()
    order_shoe_status = (
        db.session.query(OrderShoeStatus)
        .join(OrderShoe, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == bom.order_shoe_type_id)
        .filter(OrderShoeStatus.current_status == 11)
        .first()
    )
    order_shoe_status.current_status_value = 1
    db.session.commit()
    return jsonify({"status": "success"})


@second_bom_bp.route("/secondbom/getbomdetails", methods=["GET"])
def get_bom_details():
    order_id = request.args.get("orderid")
    order_shoe_id = request.args.get("ordershoeid")
    bom_id = (
        db.session.query(Bom, OrderShoe, Order, Shoe)
        .join(OrderShoe, Bom.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(
            Order.order_rid == order_id,
            Shoe.shoe_rid == order_shoe_id,
            Bom.bom_type == 1,
        )
        .first()
        .Bom.bom_id
    )
    bom_rid = db.session.query(Bom).filter(Bom.bom_id == bom_id).first().bom_rid
    bom_items = (
        db.session.query(BomItem, Material, MaterialType, Department, Supplier)
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Department, BomItem.department_id == Department.department_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(BomItem.bom_id == bom_id)
        .all()
    )

    shoe_size_names = get_order_batch_type_helper(order_id)
    result = []
    for bom_item in bom_items:
        item, material, material_type, department, supplier = bom_item
        sizeInfo = []
        first_bom_item_record = (
            db.session.query(BomItem, Bom)
            .join(Bom, BomItem.bom_id == Bom.bom_id)
            .filter(
                Bom.order_shoe_type_id == order_shoe_type_id,
                Bom.bom_type == 0,
                BomItem.material_id == material.material_id,
                BomItem.material_model == bom_item.material_model,
                BomItem.material_specification == bom_item.material_specification,
            )
            .first()
        )
        if first_bom_item_record:
            first_bom_usage = first_bom_item_record.BomItem.unit_usage
        else:
            first_bom_usage = 0
        for i in range(len(shoe_size_names)):
            index = i + 34
            obj = {
                "size": shoe_size_names[i]["label"],
                "approvalAmount": (
                    getattr(bom_item, f"size_{index}_total_usage")
                    if getattr(bom_item, f"size_{index}_total_usage")
                    else 0.00
                ),
            }
            sizeInfo.append(obj)
        result.append(
            {
                "materialName": material.material_name,
                "materialType": material_type.material_type_name,
                "materialSpecification": item.material_specification,
                "supplierName": supplier.supplier_name,
                "useDepart": department.department_id,
                "craftName": item.craft_name,
                "firstBomUsage": first_bom_usage,
                "pairs": item.pairs if item.pairs else 0.00,
                "unitUsage": (
                    item.unit_usage
                    if item.unit_usage
                    else 0.00 if material.material_category == 0 else None
                ),
                "approvalUsage": item.total_usage if item.total_usage else 0.00,
                "unit": material.material_unit,
                "color": item.bom_item_color,
                "comment": item.remark,
                "materialCategory": material.material_category,
                "sizeInfo": sizeInfo,
            }
        )
    fin_result = {"bomId": bom_rid, "bomData": result}
    print(fin_result)
    return jsonify(fin_result)


@second_bom_bp.route("/secondbom/editbom", methods=["POST"])
def edit_bom():
    bom_rid = request.json.get("bomId")
    bom_data = request.json.get("bomData")
    bom_id = Bom.query.filter(Bom.bom_rid == bom_rid, Bom.bom_type == 1).first().bom_id
    print(bom_data)
    for item in bom_data:
        material_id = (
            db.session.query(Material, Supplier)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                Material.material_name == item["materialName"],
                Supplier.supplier_name == item["supplierName"],
            )
            .first()
            .Material.material_id
        )
        bom_item = (
            db.session.query(BomItem)
            .filter(BomItem.bom_item_id == item["bomItemId"])
            .first()
        )
        bom_item.material_id = material_id
        bom_item.unit_usage = item["unitUsage"]
        bom_item.total_usage = item["approvalUsage"]
        bom_item.pairs = item["pairs"]
        for i, size in enumerate(SHOESIZERANGE):
            setattr(
                bom_item,
                f"size_{size}_total_usage",
                item["sizeInfo"][i]["approvalAmount"],
            )
        db.session.flush()
    db.session.commit()
    return jsonify({"status": "success"})


@second_bom_bp.route("/secondbom/submitbom", methods=["POST"])
def submit_bom():
    order_rid = request.json.get("orderid")
    order_shoe_rid = request.json.get("ordershoerid")
    order_shoe_type_id = request.json.get("ordershoetypeid")
    bom = (
        db.session.query(Bom, OrderShoeType, OrderShoe)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 1)
        .first()
    )
    order_shoe_id = bom.OrderShoe.order_shoe_id
    bom_id = bom.Bom.bom_id
    bom.Bom.bom_status = 2
    db.session.commit()

    return jsonify({"status": "success"})


@second_bom_bp.route("/secondbom/issueboms", methods=["POST"])
def issue_boms():
    order_rid = request.json.get("orderId")
    order_shoes = request.json.get("orderShoeIds")
    colors = request.json.get("colors")
    order_id = (
        db.session.query(Order).filter(Order.order_rid == order_rid).first().order_id
    )
    material_dict = defaultdict(lambda: {"total_usage": 0})
    series_data = []
    for order_shoe_rid in order_shoes:
        index = order_shoes.index(order_shoe_rid)
        color = colors[index]
        entities = (
            db.session.query(OrderShoe, Shoe)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(OrderShoe.order_id == order_id, Shoe.shoe_rid == order_shoe_rid)
            .first()
        )
        order_shoe_id = entities.OrderShoe.order_shoe_id
        craft_sheet_id = (
            db.session.query(CraftSheet)
            .join(OrderShoe, CraftSheet.order_shoe_id == OrderShoe.order_shoe_id)
            .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
            .filter(OrderShoe.order_shoe_id == order_shoe_id)
            .first()
            .craft_sheet_id
        )
        entities.OrderShoe.process_sheet_upload_status = "3"
        current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
        random_string = randomIdGenerater(6)
        total_bom_rid = current_time_stamp + random_string + "TS"
        total_bom = TotalBom(total_bom_rid=total_bom_rid, order_shoe_id=order_shoe_id)
        db.session.add(total_bom)
        db.session.flush()
        for color_item in color:
            order_shoe_type_id = (
                db.session.query(Order, OrderShoe, Shoe, ShoeType, OrderShoeType, Color)
                .join(OrderShoe, Order.order_id == OrderShoe.order_id)
                .join(
                    OrderShoeType,
                    OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id,
                )
                .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
                .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
                .join(Color, ShoeType.color_id == Color.color_id)
                .filter(
                    Order.order_rid == order_rid,
                    Shoe.shoe_rid == order_shoe_rid,
                )
                .filter(Color.color_name == color_item)
                .first()
                .OrderShoeType.order_shoe_type_id
            )
            bom = (
                db.session.query(Bom)
                .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 1)
                .first()
            )
            bom.bom_status = "3"
            bom.total_bom_id = total_bom.total_bom_id

            db.session.flush()
            bom_id = bom.bom_id
            bom_items = (
                db.session.query(BomItem, Material, MaterialType, Supplier, Department)
                .join(Material, Material.material_id == BomItem.material_id)
                .join(
                    MaterialType,
                    MaterialType.material_type_id == Material.material_type_id,
                )
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .outerjoin(
                    Department, Department.department_id == BomItem.department_id
                )
                .filter(BomItem.bom_id == bom_id)
                .all()
            )
            for bom_item in bom_items:
                print(
                    bom_item.Material.material_name,
                    bom_item.BomItem.material_model,
                    bom_item.BomItem.material_specification,
                    craft_sheet_id,
                )
                craft_sheet_item = (
                    db.session.query(CraftSheetItem)
                    .filter(
                        CraftSheetItem.craft_sheet_id == craft_sheet_id,
                        CraftSheetItem.order_shoe_type_id == order_shoe_type_id,
                        CraftSheetItem.material_id == bom_item.Material.material_id,
                        CraftSheetItem.material_model
                        == bom_item.BomItem.material_model,
                        CraftSheetItem.material_specification
                        == bom_item.BomItem.material_specification,
                        CraftSheetItem.after_usage_symbol == 0,
                    )
                    .first()
                )
                material_id = craft_sheet_item.material_id
                material_model = craft_sheet_item.material_model
                material_specification = craft_sheet_item.material_specification
                material_color = craft_sheet_item.color
                remark = craft_sheet_item.remark
                department_id = craft_sheet_item.department_id
                material_type = craft_sheet_item.material_type
                order_shoe_type_id = craft_sheet_item.order_shoe_type_id
                material_second_type = craft_sheet_item.material_second_type
                craft_name = bom_item.BomItem.craft_name
                new_craft_sheet_item = CraftSheetItem(
                    craft_sheet_id=craft_sheet_id,
                    material_id=material_id,
                    material_model=material_model,
                    material_specification=material_specification,
                    color=material_color,
                    remark=remark,
                    department_id=department_id,
                    material_type=material_type,
                    order_shoe_type_id=order_shoe_type_id,
                    material_second_type=material_second_type,
                    craft_name=craft_name,
                    pairs=bom_item.BomItem.pairs,
                    unit_usage=bom_item.BomItem.unit_usage,
                    total_usage=bom_item.BomItem.total_usage,
                    after_usage_symbol=1,
                )
                db.session.add(new_craft_sheet_item)
                db.session.flush()
                # Create a unique key based on the attributes
                key = (
                    bom_item.MaterialType.material_type_name,
                    bom_item.Material.material_name,
                    bom_item.BomItem.material_model,
                    bom_item.BomItem.material_specification,
                    bom_item.Supplier.supplier_name,
                    bom_item.BomItem.bom_item_color,
                )

                # Update the dictionary: sum the total_usage and add other details
                if key not in material_dict:
                    material_dict[key] = {
                        "材料类型": bom_item.MaterialType.material_type_name,
                        "材料名称": bom_item.Material.material_name,
                        "材料型号": bom_item.BomItem.material_model,
                        "材料规格": bom_item.BomItem.material_specification,
                        "颜色": bom_item.BomItem.bom_item_color,
                        "单位": bom_item.Material.material_unit,
                        "厂家名称": bom_item.Supplier.supplier_name,
                        "单位用量": (
                            bom_item.BomItem.unit_usage
                            if bom_item.BomItem.unit_usage
                            else ""
                        ),
                        "核定用量": 0,  # Initialize "核定用量" for summing
                        "使用工段": (
                            bom_item.Department.department_name
                            if bom_item.Department
                            else ""
                        ),
                        "备注": bom_item.BomItem.remark,
                    }

                # Update the total usage (核定用量)
                material_dict[key]["核定用量"] += bom_item.BomItem.total_usage
        before_usage_craft_sheet_items = (
            db.session.query(CraftSheetItem)
            .filter(
                CraftSheetItem.craft_sheet_id == craft_sheet_id,
                CraftSheetItem.after_usage_symbol == 0,
            )
            .all()
        )
        for item in before_usage_craft_sheet_items:
            db.session.delete(item)
        index = 1
        for material_info in material_dict.values():
            material_info["序号"] = index
            series_data.append(material_info)
            index += 1
        if (
            os.path.exists(
                os.path.join(FILE_STORAGE_PATH, order_rid, order_shoe_rid, "secondbom")
            )
            == False
        ):
            os.mkdir(
                os.path.join(FILE_STORAGE_PATH, order_rid, order_shoe_rid, "secondbom")
            )

        image_save_path = os.path.join(
            FILE_STORAGE_PATH, order_rid, order_shoe_rid, "secondbom", "shoe_image.jpg"
        )
        print(image_save_path)
        order_shoe_id = (
            db.session.query(OrderShoe, Shoe)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(OrderShoe.order_id == order_id, Shoe.shoe_rid == order_shoe_rid)
            .first()
            .OrderShoe.order_shoe_id
        )
        shoe_directory = os.path.join(IMAGE_UPLOAD_PATH, "shoe", order_shoe_rid)

        # Get the list of folders inside the directory
        folders = os.listdir(shoe_directory)

        # Filter out any non-folder entries (just in case)
        folders = [f for f in folders if os.path.isdir(os.path.join(shoe_directory, f))]

        # Get the first folder in the directory
        if folders:
            first_folder = folders[0]
            image_path = os.path.join(
                IMAGE_UPLOAD_PATH,
                "shoe",
                order_shoe_rid,
                first_folder,
                "shoe_image.jpg",
            )
        else:
            image_path = os.path.join(
                IMAGE_UPLOAD_PATH, "shoe", order_shoe_rid, "shoe_image.jpg"
            )
        generate_excel_file(
            FILE_STORAGE_PATH + "/BOM-V1.0-temp.xlsx",
            os.path.join(
                FILE_STORAGE_PATH,
                order_rid,
                order_shoe_rid,
                "secondbom",
                "二次BOM表.xlsx",
            ),
            {
                "order_id": order_rid,
                "last_type": "",
                "input_person": "",
                "order_finish_time": db.session.query(Order)
                .filter(Order.order_rid == order_rid)
                .first()
                .end_date,
                "inherit_id": order_shoe_rid,
                "customer_id": db.session.query(OrderShoe)
                .filter(OrderShoe.order_shoe_id == order_shoe_id)
                .first()
                .customer_product_name,
            },
            series_data,
            image_path,
            image_save_path,
        )
        processor: EventProcessor = current_app.config["event_processor"]
        event_list = []
        try:
            operation_ids = [60, 61, 62, 63]
            for operation_id in operation_ids:
                event = Event(
                    staff_id=1,
                    handle_time=datetime.datetime.now(),
                    operation_id=operation_id,
                    event_order_id=order_id,
                    event_order_shoe_id=order_shoe_id,
                )
                processor.processEvent(event)
                event_list.append(event)
        except Exception as e:
                return jsonify({"message": "failed"}), 400
        db.session.add_all(event_list)
    db.session.commit()
    return jsonify({"status": "success"})


@second_bom_bp.route("/secondbom/download", methods=["GET"])
def download_bom():
    order_shoe_rid = request.args.get("ordershoerid")
    order_id = request.args.get("orderid")
    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid)
    file_path = os.path.join(folder_path, "secondbom", "二次BOM表.xlsx")
    new_name = order_id + "-" + order_shoe_rid + "_二次BOM表.xlsx"
    return send_file(file_path, as_attachment=True, download_name=new_name)

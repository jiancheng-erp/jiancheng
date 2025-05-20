import datetime

from html import entities
import os
import shutil
from app_config import db
from constants import BOM_STATUS, BOM_STATUS_TO_INT
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import func
from models import *
from event_processor import EventProcessor
from general_document.bom import generate_excel_file
from file_locations import IMAGE_STORAGE_PATH, FILE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from api_utility import randomIdGenerater
from collections import defaultdict
from business.batch_info_type import get_order_batch_type_helper
from sqlalchemy.sql.expression import case
from wechat_api.send_message_api import send_massage_to_users

usage_calculation_bp = Blueprint("usage_calculation_bp", __name__)


@usage_calculation_bp.route("/usagecalculation/getallboms", methods=["GET"])
def get_order_first_bom():
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


@usage_calculation_bp.route("/usagecalculation/getshoebomitems", methods=["GET"])
def get_shoe_bom_items():
    bom_rid = request.args.get("bomrid")
    material_order = case(
        (ProductionInstructionItem.material_type == "S", 1),
        (ProductionInstructionItem.material_type == "I", 2),
        (ProductionInstructionItem.material_type == "A", 3),
        (ProductionInstructionItem.material_type == "O", 4),
        (ProductionInstructionItem.material_type == "M", 5),
        (ProductionInstructionItem.material_type == "H", 6),
        else_=6,  # Default for any other values (if any)
    )
    entities = (
        db.session.query(
            BomItem, Material, MaterialType, Supplier, ProductionInstructionItem
        )
        .join(Bom, Bom.bom_id == BomItem.bom_id)
        .join(Material, Material.material_id == BomItem.material_id)
        .join(MaterialType, MaterialType.material_type_id == Material.material_type_id)
        .join(Supplier, Supplier.supplier_id == Material.material_supplier)
        .outerjoin(
            ProductionInstructionItem,
            BomItem.production_instruction_item_id
            == ProductionInstructionItem.production_instruction_item_id,
        )
        .filter(Bom.bom_rid == bom_rid)
        .order_by(material_order, Supplier.supplier_name, Material.material_name)
        .all()
    )
    result = []
    # get shoe size name
    order_id = (
        db.session.query(Order.order_id)
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Bom, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(Bom.bom_rid == bom_rid)
        .first()
        .order_id
    )
    shoe_size_names = get_order_batch_type_helper(order_id)
    for entity in entities:
        bom_item, material, material_type, supplier, production_instruction = entity
        sizeInfo = []
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
                "materialDetailType": bom_item.material_second_type,
                "materialType": material_type.material_type_name,
                "materialName": material.material_name,
                "materialModel": bom_item.material_model,
                "materialSpecification": bom_item.material_specification,
                "color": bom_item.bom_item_color,
                "unit": material.material_unit,
                "unitUsage": (
                    bom_item.unit_usage
                    if bom_item.unit_usage
                    else 0.00 if material.material_category == 0 else None
                ),
                "approvalUsage": bom_item.total_usage if bom_item.total_usage else 0.00,
                "useDepart": bom_item.department_id,
                "supplierName": supplier.supplier_name,
                "materialCategory": material.material_category,
                "remark": bom_item.remark,
                "sizeInfo": sizeInfo,
            }
        )
    return jsonify(result)


@usage_calculation_bp.route("/usagecalculation/savebomusage", methods=["POST"])
def save_bom_usage():
    bom_rid = request.json.get("bomRid")
    bom_items = request.json.get("bomItems")
    bom = db.session.query(Bom).filter(Bom.bom_rid == bom_rid).first()
    bom.bom_status = "4"
    for bom_item in bom_items:
        entity = (
            db.session.query(BomItem)
            .filter(BomItem.bom_item_id == bom_item["bomItemId"])
            .first()
        )
        for i in range(len(bom_item["sizeInfo"])):
            name = i + 34
            setattr(
                entity,
                f"size_{name}_total_usage",
                bom_item["sizeInfo"][i]["approvalAmount"],
            )
            entity.total_usage = bom_item["approvalUsage"]
            entity.unit_usage = bom_item["unitUsage"]
            entity.remark = bom_item["remark"]
    order_shoe_status = (
        db.session.query(OrderShoeStatus)
        .join(OrderShoe, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == bom.order_shoe_type_id)
        .filter(OrderShoeStatus.current_status == 4)
        .first()
    )
    if order_shoe_status:
        order_shoe_status.current_status_value = 1
    db.session.commit()
    return jsonify({"status": "success"})


@usage_calculation_bp.route("/usagecalculation/submitbomusage", methods=["POST"])
def submit_bom_usage():
    bom_rid = request.json.get("bomRid")
    bom = db.session.query(Bom).filter(Bom.bom_rid == bom_rid).first()
    bom.bom_status = "5"
    db.session.commit()

    return jsonify({"status": "success"})


@usage_calculation_bp.route("/usagecalculation/issuebomusage", methods=["POST"])
def issue_bom_usage():
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
        order_shoe_id = (
            db.session.query(OrderShoe, Shoe)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(OrderShoe.order_id == order_id, Shoe.shoe_rid == order_shoe_rid)
            .first()
            .OrderShoe.order_shoe_id
        )

        current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
        random_string = randomIdGenerater(6)
        total_bom_rid = current_time_stamp + random_string + "TF"
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
                .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 0)
                .first()
            )
            bom.bom_status = "6"
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
        index = 1
        for material_info in material_dict.values():
            material_info["序号"] = index
            series_data.append(material_info)
            index += 1
        if (
            os.path.exists(
                os.path.join(FILE_STORAGE_PATH, order_rid, order_shoe_rid, "firstbom")
            )
            == False
        ):
            os.mkdir(
                os.path.join(FILE_STORAGE_PATH, order_rid, order_shoe_rid, "firstbom")
            )

        image_save_path = os.path.join(
            FILE_STORAGE_PATH, order_rid, order_shoe_rid, "firstbom", "shoe_image.jpg"
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
                "firstbom",
                "一次BOM表.xlsx",
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
        event_arr = []
        try:
            for operation_id in [46, 47, 48, 49]:
                event = Event(
                    staff_id=1,
                    handle_time=datetime.datetime.now(),
                    operation_id=operation_id,
                    event_order_id=order_id,
                    event_order_shoe_id=order_shoe_id,
                )
                processor.processEvent(event)
                event_arr.append(event)
        except Exception:
            return jsonify({"status": "failed"})
        db.session.add_all(event_arr)
        db.session.flush()
    message = f"订单已发出至一次采购订单阶段，订单号：{order_rid}，鞋型号：{order_shoe_rid}"
    users = "XieShuWa"
    send_massage_to_users(message, users)
    message = f"订单已发出至二次采购订单阶段，订单号：{order_rid}，鞋型号：{order_shoe_rid}"
    users = "FanJianMing"
    send_massage_to_users(message, users)
    db.session.commit()
    return jsonify({"status": "success"})


@usage_calculation_bp.route(("/usagecalculation/copyusagetoallcheck"), methods=["GET"])
def copy_usage_to_all_check():
    order_shoe_type_id = request.args.get("orderShoeTypeId")
    order_shoe_id = (
        db.session.query(OrderShoe)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
        .first()
    ).order_shoe_id
    bom = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 0)
        .first()
    )
    bom_items = db.session.query(BomItem).filter(BomItem.bom_id == bom.bom_id).all()
    same_order_shoe_types = (
        db.session.query(OrderShoeType)
        .filter(OrderShoeType.order_shoe_id == order_shoe_id)
        .all()
    )
    different_order_shoe_type_list = []
    for same_order_shoe_type in same_order_shoe_types:
        same_bom = (
            db.session.query(Bom)
            .filter(
                Bom.order_shoe_type_id == same_order_shoe_type.order_shoe_type_id,
                Bom.bom_type == 0,
            )
            .first()
        )
        same_bom_id = same_bom.bom_id
        if same_bom_id == bom.bom_id:
            continue
        same_bom_items = (
            db.session.query(BomItem).filter(BomItem.bom_id == same_bom_id).all()
        )
        if len(same_bom_items) != len(bom_items):
            color_name = (
                db.session.query(Color)
                .join(ShoeType, ShoeType.color_id == Color.color_id)
                .join(
                    OrderShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id
                )
                .filter(
                    OrderShoeType.order_shoe_type_id
                    == same_order_shoe_type.order_shoe_type_id
                )
                .first()
                .color_name
            )
            different_order_shoe_type_list.append(color_name)
            continue
    if len(different_order_shoe_type_list) == 0:
        result = {
            "checkResult": 0,
            "reason": "各颜色材料数量一致，复制后注意核对",
        }
        return jsonify(result)
    else:
        result = {
            "checkResult": 1,
            "reason": "颜色为"
            + "、".join(different_order_shoe_type_list)
            + "的材料数量不一致，请核对后再确认！",
        }
        return jsonify(result)

    return 200


@usage_calculation_bp.route("/usagecalculation/copyusagetoall", methods=["POST"])
def copy_usage_to_all():
    order_shoe_type_id = request.json.get("orderShoeTypeId")
    order_shoe_id = (
        db.session.query(OrderShoe)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
        .first()
    ).order_shoe_id
    bom = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 0)
        .first()
    )
    bom_items = db.session.query(BomItem).filter(BomItem.bom_id == bom.bom_id).all()
    same_order_shoe_types = (
        db.session.query(OrderShoeType)
        .filter(OrderShoeType.order_shoe_id == order_shoe_id)
        .all()
    )
    for same_order_shoe_type in same_order_shoe_types:
        same_bom = (
            db.session.query(Bom)
            .filter(
                Bom.order_shoe_type_id == same_order_shoe_type.order_shoe_type_id,
                Bom.bom_type == 0,
            )
            .first()
        )
        same_bom_id = same_bom.bom_id
        if same_bom_id == bom.bom_id:
            continue
        same_bom_items = (
            db.session.query(BomItem).filter(BomItem.bom_id == same_bom_id).all()
        )
        for bom_item in bom_items:
            for same_bom_item in same_bom_items:
                material_name = (
                    db.session.query(Material)
                    .filter(Material.material_id == bom_item.material_id)
                    .first()
                    .material_name
                )
                same_material_name = (
                    db.session.query(Material)
                    .filter(Material.material_id == same_bom_item.material_id)
                    .first()
                    .material_name
                )
                supplier_name = (
                    db.session.query(Supplier)
                    .join(Material, Material.material_supplier == Supplier.supplier_id)
                    .filter(Material.material_id == bom_item.material_id)
                    .first()
                    .supplier_name
                )
                same_supplier_name = (
                    db.session.query(Supplier)
                    .join(Material, Material.material_supplier == Supplier.supplier_id)
                    .filter(Material.material_id == same_bom_item.material_id)
                    .first()
                    .supplier_name
                )
                if (
                    material_name == same_material_name
                    and supplier_name == same_supplier_name
                    and are_material_models_similar(
                        bom_item.material_model, same_bom_item.material_model
                    )
                ):
                    for i in range(34, 47):
                        setattr(
                            same_bom_item,
                            f"size_{i}_total_usage",
                            getattr(bom_item, f"size_{i}_total_usage"),
                        )
                    same_bom_item.total_usage = bom_item.total_usage
                    same_bom_item.unit_usage = bom_item.unit_usage
                    db.session.flush()
                    break
        same_bom.bom_status = "4"
        db.session.flush()

    db.session.commit()
    return jsonify({"status": "success"})


@usage_calculation_bp.route("/usagecalculation/loadpastusage", methods=["GET"])
def load_past_usage():
    current_bom_rid = request.args.get("currentBomRid")
    current_shoe_type_id = (
        db.session.query(Bom, OrderShoeType, ShoeType)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .filter(
            Bom.bom_rid == current_bom_rid,
        )
        .first()
    )
    if current_shoe_type_id is None:
        return jsonify({"status": "failed", "message": "No previous BOM found."})
    default_bom = (
        db.session.query(DefaultBom)
        .filter(DefaultBom.shoe_type_id == current_shoe_type_id.ShoeType.shoe_type_id, DefaultBom.bom_type == 0)
        .first()
    )
    if default_bom is None:
        return jsonify({"status": "failed", "message": "No previous BOM found."})
    past_bom_id = default_bom.bom_id
    entities = (
        db.session.query(BomItem, Material, MaterialType, Supplier, Department)
        .join(Material, Material.material_id == BomItem.material_id)
        .join(
            MaterialType,
            MaterialType.material_type_id == Material.material_type_id,
        )
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .outerjoin(Department, Department.department_id == BomItem.department_id)
        .filter(BomItem.bom_id == past_bom_id)
        .all()
    )
    result = []
    for entity in entities:
        bom_item, material, material_type, supplier, department = entity
        sizeInfo = []
        for i in range(34, 47):
            index = i + 1
            obj = {
                "size": index,
                "approvalAmount": (
                    getattr(bom_item, f"size_{i}_total_usage")
                    if getattr(bom_item, f"size_{i}_total_usage")
                    else 0.00
                ),
            }
            sizeInfo.append(obj)

        result.append(
            {
                "bomItemId": bom_item.bom_item_id,
                "materialDetailType": bom_item.material_second_type,
                "materialType": material_type.material_type_name,
                "materialName": material.material_name,
                "materialModel": bom_item.material_model,
                "materialSpecification": bom_item.material_specification,
                "color": bom_item.bom_item_color,
                "unit": material.material_unit,
                "unitUsage": (
                    bom_item.unit_usage
                    if bom_item.unit_usage
                    else 0.00 if material.material_category == 0 else None
                ),
                "approvalUsage": bom_item.total_usage if bom_item.total_usage else 0.00,
                "useDepart": department.department_name if department else "",
                "supplierName": supplier.supplier_name,
                "materialCategory": material.material_category,
                "remark": bom_item.remark,
                "sizeInfo": sizeInfo,
            }
        )
    return jsonify({"status": "success", "data": result})


import re


def are_material_models_similar(model1, model2):
    """
    Determine if two material model strings are similar.
    Similarity rules:
    1. If both contain a hyphen (`-`), compare the prefix before the last hyphen.
    2. If no hyphen, check if they differ only in the last 1 or 2 digits.
    """
    # Pattern for detecting prefix before the last hyphen
    pattern = r"^(.*?)-\d+$"

    match1 = re.match(pattern, model1)
    match2 = re.match(pattern, model2)

    if match1 and match2:
        return match1.group(1) == match2.group(1)  # Compare prefixes if hyphen exists

    # If no hyphen, check numeric similarity
    if model1.isdigit() and model2.isdigit() and len(model1) == len(model2):
        return (
            model1[:-1] == model2[:-1] or model1[:-2] == model2[:-2]
        )  # Allow last 1-2 digit differences

    # General similarity check for mixed alphanumeric models
    prefix1 = re.match(r"^\D*(\d+)", model1)  # Extract leading numbers
    prefix2 = re.match(r"^\D*(\d+)", model2)

    if prefix1 and prefix2:
        return prefix1.group(1) == prefix2.group(1)  # Compare extracted leading numbers
    if model1 == model2:
        return True

    return False  # If no clear similarity pattern found


@usage_calculation_bp.route(
    "/usagecalculation/getallbomitems", methods=["GET"]
)
def get_all_bom_items():
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

    order_amount_query = (
        db.session.query(
            Order.order_id,
            func.sum(OrderShoeBatchInfo.total_amount).label("total_amount"),
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(OrderShoeBatchInfo, OrderShoeType.order_shoe_type_id == OrderShoeBatchInfo.order_shoe_type_id)
        .group_by(Order.order_id)
        .subquery()
    )

    query = (
        db.session.query(BomItem, Bom, Order, Shoe, Material, Supplier, order_amount_query.c.total_amount)
        .join(
            Bom, BomItem.bom_id == Bom.bom_id
        )
        .join(
            OrderShoeType,
            Bom.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(Material, BomItem.material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .join(order_amount_query, Order.order_id == order_amount_query.c.order_id)
        .filter(Bom.bom_type == 0)
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
            BomItem.material_model.ilike(f"%{material_model}%")
        )
    if material_specification:
        query = query.filter(
            BomItem.material_specification.ilike(
                f"%{material_specification}%"
            )
        )
    if material_color:
        query = query.filter(BomItem.bom_item_color.ilike(f"%{material_color}%"))
    if supplier_name:
        query = query.filter(Supplier.supplier_name.ilike(f"%{supplier_name}%"))
    if status:
        query = query.filter(Bom.bom_status == BOM_STATUS_TO_INT.get(status, 1))

    # Pagination
    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()

    result = []
    for row in response:
        item, bom, order, shoe, material, supplier, order_amount = row
        obj = {
            "orderRId": order.order_rid,
            "shoeRId": shoe.shoe_rid,
            "materialName": material.material_name,
            "materialModel": item.material_model,
            "materialSpecification": item.material_specification,
            "materialColor": item.bom_item_color,
            "supplierName": supplier.supplier_name,
            "bomRId": bom.bom_rid,
            "bomStatus": BOM_STATUS.get(bom.bom_status, "未填写"),
            "orderAmount": order_amount,
            "unitUsage": item.unit_usage,
            "totalUsage": item.total_usage,
            "materialUnit": material.material_unit,
        }
        result.append(obj)
    return {"result": result, "totalLength": count_result}

from flask import Blueprint, jsonify, request, send_file, current_app
import os
import datetime
from app_config import db
from models import *
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from api_utility import randomIdGenerater
from general_document.prodution_instruction import generate_instruction_excel_file
from logger import logger
process_sheet_review = Blueprint("process_sheet_review", __name__)

@process_sheet_review.route("/craftsheetreview/getcraftsheetinfo", methods=["GET"])
def getCraftSheetInfo():
    order_id = request.args.get("orderid")
    order_shoe_rid = request.args.get("ordershoeid")
    order_shoe = (
        db.session.query(OrderShoe)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )

    # Fetch order_shoe_id based on order_id and order_shoe_rid
    # Get the production instruction
    craft_sheet = (
        db.session.query(CraftSheet)
        .join(OrderShoe, CraftSheet.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )
    logger.debug(craft_sheet)

    craft_sheet_id = craft_sheet.craft_sheet_id
    craft_sheet_rid = craft_sheet.craft_sheet_rid

    craft_sheet_items = (
        db.session.query(CraftSheetItem, Color)
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id == CraftSheetItem.order_shoe_type_id,
        )
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .join(Material, CraftSheetItem.material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(CraftSheetItem.craft_sheet_id == craft_sheet_id)
        .all()
    )
    logger.debug(craft_sheet_items)
    
    result_dict = {}
    for row in craft_sheet_items:
        item = row
        color_name = item.Color.color_name
        # Initialize color entry if it doesn't exist
        if color_name not in result_dict:
            result_dict[color_name] = {
                "color": color_name,
                "surfaceMaterialData": [],
                "insideMaterialData": [],
                "accessoryMaterialData": [],
                "outsoleMaterialData": [],
                "midsoleMaterialData": [],
                "lastMaterialData": [],
                "hotsoleMaterialData": [],
            }
        material = (
            db.session.query(Material, MaterialType, Supplier)
            .join(
                MaterialType, Material.material_type_id == MaterialType.material_type_id
            )
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(Material.material_id == item.CraftSheetItem.material_id)
            .first()
        )
        if item.CraftSheetItem.craft_name != None:
            material_craft_list = item.CraftSheetItem.craft_name.split("@")
            material_craft_name = ",".join(material_craft_list)
        else:
            material_craft_list = []
            material_craft_name = ""
        # Map material type to the appropriate array in the dictionary
        material_data = {
            "materialId": item.CraftSheetItem.material_id,
            "materialType": material.MaterialType.material_type_name,
            "materialName": material.Material.material_name,
            "materialModel": item.CraftSheetItem.material_model,
            "materialSpecification": item.CraftSheetItem.material_specification,
            "color": item.CraftSheetItem.color,
            "unit": material.Material.material_unit,
            "pairs": item.CraftSheetItem.pairs,
            "unitUsage": item.CraftSheetItem.unit_usage,
            "supplierName": material.Supplier.supplier_name,
            "comment": item.CraftSheetItem.remark,
            "useDepart": item.CraftSheetItem.department_id,
            "materialCraftName": material_craft_name,
            "materialCraftNameList": material_craft_list,
            "materialDetailType": item.CraftSheetItem.material_second_type,
            "materialSource": item.CraftSheetItem.material_source,
            "totalUsage": item.CraftSheetItem.total_usage,
        }

        if item.CraftSheetItem.material_type == "S":
            result_dict[color_name]["surfaceMaterialData"].append(material_data)
        elif item.CraftSheetItem.material_type == "I":
            result_dict[color_name]["insideMaterialData"].append(material_data)
        elif item.CraftSheetItem.material_type == "A":
            result_dict[color_name]["accessoryMaterialData"].append(material_data)
        elif item.CraftSheetItem.material_type == "O":
            result_dict[color_name]["outsoleMaterialData"].append(material_data)
        elif item.CraftSheetItem.material_type == "M":
            result_dict[color_name]["midsoleMaterialData"].append(material_data)
        elif item.CraftSheetItem.material_type == "L":
            result_dict[color_name]["lastMaterialData"].append(material_data)
        elif item.CraftSheetItem.material_type == "H":
            result_dict[color_name]["hotsoleMaterialData"].append(material_data)
    
    result = list(result_dict.values())
    craft_sheet_detail = {
        "adjuster": order_shoe.adjust_staff,
        "reviewer": craft_sheet.reviewer,
        "cutDie": craft_sheet.cut_die_staff,
        "productionRemark": craft_sheet.production_remark,
        "cuttingSpecialCraft": craft_sheet.cutting_special_process,
        "sewingSpecialCraft": craft_sheet.sewing_special_process,
        "moldingSpecialCraft": craft_sheet.molding_special_process,
        "postProcessing": craft_sheet.post_processing_comment,
        "oilyGlue": craft_sheet.oily_glue,
        "cutDieImgPath": craft_sheet.cut_die_img_path,
        "picNoteImgPath": craft_sheet.pic_note_img_path,



        
    }
    fin_result = {
        "craftSheetId": craft_sheet_rid,
        "uploadData": result,
        "craftSheetDetail": craft_sheet_detail,
    }
    return jsonify(fin_result)

@process_sheet_review.route("/craftsheetreview/issue", methods=["POST"])
def issue_craft_sheet():
    order_shoe_rids = request.json.get("orderShoeIds")
    order_rid = request.json.get("orderId")
    for order_shoe_rid in order_shoe_rids:
        order_shoe = (
            db.session.query(Order, OrderShoe, Shoe)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(Order.order_rid == order_rid, Shoe.shoe_rid == order_shoe_rid)
            .first()
        )
        order_id = order_shoe.Order.order_id
        order_shoe_id = order_shoe.OrderShoe.order_shoe_id
        logger.debug(order_shoe.OrderShoe.process_sheet_upload_status)
        if order_shoe.OrderShoe.process_sheet_upload_status != "3":
            return jsonify({"error": "Unit usage not uploaded yet"}), 500
        order_shoe.OrderShoe.process_sheet_upload_status = "4"
        craft_sheet = db.session.query(CraftSheet).filter(
            CraftSheet.order_shoe_id == order_shoe_id
        ).first()
        craft_sheet.craft_sheet_status = "3"
        event_arr = []
        processor: EventProcessor = current_app.config["event_processor"]
        try:
            for operation_id in [64,65,66,67]:
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
            return jsonify({"error": "Failed to issue production order"}), 500
        db.session.add_all(event_arr)
    db.session.commit()
    return jsonify({"message": "Production order issued successfully"})
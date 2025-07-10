from flask import Blueprint, jsonify, request, send_file, current_app
import os
import datetime
from app_config import db
from models import *
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from api_utility import randomIdGenerater
from general_document.prodution_instruction import generate_instruction_excel_file
import json
from constants import DEFAULT_SUPPLIER

craft_sheet_revert_api = Blueprint("craft_sheet_revert_api", __name__)

@craft_sheet_revert_api.route("/craftsheet/editrevertcraftsheet", methods=["POST"])
def edit_revert_craft_sheet():
    order_id = request.json.get("orderId")
    order_shoe_rid = request.json.get("orderShoeId")
    craft_sheet_rid = request.json.get("craftSheetId")
    upload_data = request.json.get("uploadData")
    craft_sheet_detail = request.json.get("craftSheetDetail")

    # Get OrderShoe object
    order_shoe = (
        db.session.query(OrderShoe)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )

    if not order_shoe:
        return jsonify({"error": "Order shoe not found"}), 404

    order_shoe_id = order_shoe.order_shoe_id

    # Get Craft Sheet
    craft_sheet = db.session.query(CraftSheet).filter(
        CraftSheet.craft_sheet_rid == craft_sheet_rid
    ).first()

    if not craft_sheet:
        return jsonify({"error": "Craft sheet not found"}), 404

    craft_sheet_id = craft_sheet.craft_sheet_id

    # Get Second BOM (bom_type=1)
    second_bom = (
        db.session.query(Bom)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .filter(Order.order_rid == order_id, Bom.bom_type == 1)
        .first()
    )

    # Update Craft Sheet Details
    craft_sheet.cut_die_staff = craft_sheet_detail.get("cutDie")
    craft_sheet.production_remark = craft_sheet_detail.get("productionRemark")
    craft_sheet.cutting_special_process = craft_sheet_detail.get("cuttingSpecialCraft")
    craft_sheet.sewing_special_process = craft_sheet_detail.get("sewingSpecialCraft")
    craft_sheet.molding_special_process = craft_sheet_detail.get("moldingSpecialCraft")
    craft_sheet.post_processing_comment = craft_sheet_detail.get("postProcessing")
    craft_sheet.oily_glue = craft_sheet_detail.get("oilyGlue")
    craft_sheet.cut_die_img_path = craft_sheet_detail.get("cutDieImgPath")
    craft_sheet.pic_note_img_path = craft_sheet_detail.get("picNoteImgPath")
    db.session.flush()

    # Get Existing CraftSheetItems
    existing_items = {
        item.craft_sheet_item_id: item for item in db.session.query(CraftSheetItem).filter(
            CraftSheetItem.craft_sheet_id == craft_sheet_id
        ).all()
    }

    uploaded_item_ids = set()

    for data in upload_data:
        shoe_color = data.get("color")

        # Get Shoe Type ID
        shoe_type_id = (
            db.session.query(ShoeType)
            .join(Shoe, ShoeType.shoe_id == Shoe.shoe_id)
            .join(Color, ShoeType.color_id == Color.color_id)
            .filter(Shoe.shoe_rid == order_shoe_rid, Color.color_name == shoe_color)
            .first()
            .shoe_type_id
        )

        # Get Order Shoe Type ID
        order_shoe_type_id = (
            db.session.query(OrderShoeType)
            .filter(
                OrderShoeType.order_shoe_id == order_shoe_id,
                OrderShoeType.shoe_type_id == shoe_type_id,
            )
            .first()
            .order_shoe_type_id
        )

        # Iterate Over Material Types
        for material_type, material_data in {
            "S": data.get("surfaceMaterialData", []),
            "I": data.get("insideMaterialData", []),
            "A": data.get("accessoryMaterialData", []),
            "O": data.get("outsoleMaterialData", []),
            "M": data.get("midsoleMaterialData", []),
            "H": data.get("hotsoleMaterialData", []),
            "L": data.get("lastMaterialData", []),
        }.items():
            for material in material_data:
                craft_item_id = material.get("craftSheetItemId")
                item_id = material.get("productionInstructionItemId")
                uploaded_item_ids.add(craft_item_id)

                # Ensure Material & Supplier Exist
                material_id = _get_or_create_material(material)

                # Construct `craft_name`
                craft_name_list = material.get("materialCraftNameList", [])
                craft_name = "@".join(craft_name_list) if craft_name_list else ""

                if craft_item_id in existing_items:
                    # Update Existing Item
                    item = existing_items[craft_item_id]
                    item.material_id = material_id
                    item.material_model = material.get("materialModel")
                    item.material_specification = material.get("materialSpecification")
                    item.color = material.get("color")
                    item.remark = material.get("comment")
                    item.department_id = material.get("useDepart")
                    item.material_source = material.get("materialSource", "C")
                    item.material_second_type = material.get("materialDetailType")
                    item.processing_remark = material.get("processingRemark")
                    item.craft_name = craft_name  # Update `craft_name`
                else:
                    # Insert New Item
                    new_item = CraftSheetItem(
                        craft_sheet_id=craft_sheet_id,
                        material_id=material_id,
                        material_model=material.get("materialModel"),
                        material_specification=material.get("materialSpecification"),
                        color=material.get("color"),
                        remark=material.get("comment"),
                        department_id=material.get("useDepart"),
                        material_source=material.get("materialSource", "C"),
                        material_type=material_type,
                        order_shoe_type_id=order_shoe_type_id,
                        material_second_type=material.get("materialDetailType"),
                        craft_name=craft_name,
                        after_usage_symbol=0,
                        production_instruction_item_id=item_id,
                    )
                    db.session.add(new_item)

                # Update Second BOM if it exists
                if second_bom:
                    _update_or_insert_bom_item(item_id, material, material_id, order_shoe_type_id, bom_type=1)

    # Delete Removed Items
    for existing_id in existing_items.keys():
        if existing_id not in uploaded_item_ids:
            db.session.delete(existing_items[existing_id])

    # Update Order Shoe Status
    order_shoe.adjust_staff = craft_sheet_detail.get("adjuster")

    db.session.commit()
    return jsonify({"message": "Craft sheet updated successfully"}), 200


def _update_or_insert_bom_item(item_id, material, material_id, order_shoe_type_id, bom_type):
    """
    Update or Insert BOM Item(s) for the specified bom_type (usually 1 for second BOM).
    If `bom_type == 1`, then multiple BOM items may be created based on the `craft_name` string.
    """
    bom = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == bom_type)
        .first()
    )
    if not bom:
        return

    bom_id = bom.bom_id

    # Key fields for identifying related bom_items
    key_filter = (
        BomItem.production_instruction_item_id == item_id,
        BomItem.material_id == material_id,
        BomItem.material_model == material.get("materialModel"),
        BomItem.material_specification == material.get("materialSpecification"),
        BomItem.bom_item_color == material.get("color"),
        BomItem.bom_item_add_type == str(bom_type),
    )

    # Delete old BomItems for second BOM (generated from old craft_name)
    if bom_type == 1:
        old_bom_items = db.session.query(BomItem).filter(*key_filter).all()
        for old_item in old_bom_items:
            db.session.delete(old_item)

        # Split new craft_name list and add each as separate BomItem
        craft_name_list = material.get("materialCraftNameList", [])
        for craft_name in craft_name_list:
            new_bom_item = BomItem(
                bom_id=bom_id,
                production_instruction_item_id=item_id,
                material_id=material_id,
                material_model=material.get("materialModel"),
                material_specification=material.get("materialSpecification"),
                bom_item_color=material.get("color"),
                unit_usage=material.get("unitUsage", 0),
                total_usage=material.get("totalUsage", 0),
                remark=material.get("comment"),
                bom_item_add_type=str(bom_type),
                craft_name=craft_name,
            )
            db.session.add(new_bom_item)



def _get_or_create_material(material):
    """ Ensure the material and supplier exist, create if not found """
    supplier_name = material.get("supplierName") or "DEFAULT_SUPPLIER"
    material_name = material.get("materialName")

    # Check if supplier exists
    supplier = db.session.query(Supplier).filter(Supplier.supplier_name == supplier_name).first()
    if not supplier:
        supplier = Supplier(supplier_name=supplier_name)
        db.session.add(supplier)
        db.session.flush()

    supplier_id = supplier.supplier_id

    # Check if material exists
    material_record = db.session.query(Material).filter(
        Material.material_name == material_name,
        Material.material_supplier == supplier_id
    ).first()

    if not material_record:
        material_type_id = db.session.query(MaterialType).filter(
            MaterialType.material_type_name == material.get("materialType")
        ).first().material_type_id

        material_record = Material(
            material_name=material_name,
            material_supplier=supplier_id,
            material_unit=material.get("unit"),
            material_creation_date=datetime.datetime.now(),
            material_type_id=material_type_id,
            material_category=1 if material.get("materialType") == "烫底" else 0
        )
        db.session.add(material_record)
        db.session.flush()

    return material_record.material_id

    
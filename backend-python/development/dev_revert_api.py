from flask import Blueprint, jsonify, request, send_file, current_app
import os
import datetime
from app_config import app, db
from models import *
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from api_utility import randomIdGenerater
from general_document.prodution_instruction import generate_instruction_excel_file
import json
from constants import DEFAULT_SUPPLIER

dev_revert_api = Blueprint("dev_revert_api", __name__)


@dev_revert_api.route(
    "/devproductionorder/editrevertproductioninstruction", methods=["POST"]
)
def edit_revert_production_instruction():
    order_id = request.json.get("orderId")
    production_instruction_rid = request.json.get("productionInstructionId")
    order_shoe_rid = request.json.get("orderShoeId")
    upload_data = request.json.get("uploadData")
    production_instruction_details = request.json.get("productionInstructionDetail")
    order_shoe_id = (
        db.session.query(OrderShoe)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )

    # Get production instruction
    production_instruction = (
        db.session.query(ProductionInstruction)
        .filter(
            ProductionInstruction.production_instruction_rid
            == production_instruction_rid
        )
        .first()
    )

    if not production_instruction:
        return jsonify({"error": "Production Instruction not found"}), 404

    production_instruction_id = production_instruction.production_instruction_id

    # Get existing ProductionInstructionItems
    existing_items = {
        item.production_instruction_item_id: item
        for item in db.session.query(ProductionInstructionItem)
        .filter(
            ProductionInstructionItem.production_instruction_id
            == production_instruction_id
        )
        .all()
    }

    uploaded_item_ids = set()
    craft_sheet = (
        db.session.query(CraftSheet)
        .filter(CraftSheet.order_shoe_id == order_shoe_id.order_shoe_id)
        .first()
    )
    second_bom = (
        db.session.query(Bom, OrderShoeType, OrderShoe, Order)
        .filter(
            Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
            OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            OrderShoe.order_id == Order.order_id,
            Order.order_rid == order_id,
        )
        .filter(Bom.bom_type == 1)
        .first()
    )

    for data in upload_data:
        shoe_color = data.get("color")
        for material_type, material_data in {
            "S": data.get("surfaceMaterialData", []),
            "I": data.get("insideMaterialData", []),
            "A": data.get("accessoryMaterialData", []),
            "O": data.get("outsoleMaterialData", []),
            "M": data.get("midsoleMaterialData", []),
            "H": data.get("hotsoleMaterialData", []),
        }.items():
            for material in material_data:
                item_id = material.get("productionInstructionItemId")
                uploaded_item_ids.add(item_id)

                # Ensure material & supplier exist
                material_id = _get_or_create_material(material)

                # Query existing item
                if item_id in existing_items:
                    item = existing_items[item_id]
                    item.material_id = material_id
                    item.material_model = material.get("materialModel")
                    item.material_specification = material.get("materialSpecification")
                    item.color = material.get("color")
                    item.remark = material.get("comment")
                    item.department_id = material.get("useDepart")
                    item.is_pre_purchase = material.get("isPurchase", False)
                    item.material_type = material_type
                    item.material_second_type = material.get("materialDetailType")
                    item.processing_remark = material.get("processingRemark")
                else:
                    # Insert new ProductionInstructionItem
                    new_item = ProductionInstructionItem(
                        production_instruction_id=production_instruction_id,
                        material_id=material_id,
                        material_model=material.get("materialModel"),
                        material_specification=material.get("materialSpecification"),
                        color=material.get("color"),
                        remark=material.get("comment"),
                        department_id=material.get("useDepart"),
                        is_pre_purchase=material.get("isPurchase", False),
                        material_type=material_type,
                        material_second_type=material.get("materialDetailType"),
                        processing_remark=material.get("processingRemark"),
                    )
                    db.session.add(new_item)
                    db.session.flush()
                    item_id = new_item.production_instruction_item_id
                    uploaded_item_ids.add(item_id)

                # Update/Add BomItem (for both bom_type = 0 and bom_type = 1)
                _update_or_insert_bom_item(item_id, material, material_id,  bom_type=0)

                if craft_sheet:
                    _update_or_insert_craft_sheet_item(item_id, material, material_id)
                if second_bom:
                    _update_or_insert_bom_item(item_id, material, material_id, bom_type=1)

    # Delete removed items
    for existing_id in existing_items.keys():
        if existing_id not in uploaded_item_ids:
            db.session.delete(existing_items[existing_id])

    db.session.commit()
    return jsonify({"message": "Production instruction updated successfully"}), 200


def _get_or_create_material(material):
    """Ensure the material and supplier exist, create if not found"""
    supplier_name = material.get("supplierName") or "DEFAULT_SUPPLIER"
    material_name = material.get("materialName")

    # Check if supplier exists
    supplier = (
        db.session.query(Supplier)
        .filter(Supplier.supplier_name == supplier_name)
        .first()
    )
    if not supplier:
        supplier = Supplier(supplier_name=supplier_name)
        db.session.add(supplier)
        db.session.flush()  # Get supplier ID immediately
    supplier_id = supplier.supplier_id

    # Check if material exists
    material_record = (
        db.session.query(Material)
        .filter(
            Material.material_name == material_name,
            Material.material_supplier == supplier_id,
        )
        .first()
    )

    if not material_record:
        material_type_id = (
            db.session.query(MaterialType)
            .filter(MaterialType.material_type_name == material.get("materialType"))
            .first()
            .material_type_id
        )

        material_record = Material(
            material_name=material_name,
            material_supplier=supplier_id,
            material_unit=material.get("unit"),
            material_creation_date=datetime.datetime.now(),
            material_type_id=material_type_id,
            material_category=(
                1
                if (
                    material.get("materialType") == "烫底"
                    or material.get("materialType") == "底材"
                )
                else 0
            ),
        )
        db.session.add(material_record)
        db.session.flush()

    return material_record.material_id


def _update_or_insert_bom_item(item_id, material, material_id, bom_type):
    """Update or Insert BOM Item for the specified bom_type (0 or 1)"""
    bom_item = (
        db.session.query(BomItem)
        .filter(
            BomItem.production_instruction_item_id == item_id,
            BomItem.bom_item_add_type == str(bom_type),
        )
        .first()
    )

    if bom_item:
        # Update existing BOM item (except craft_name)
        bom_item.material_id = material_id
        bom_item.material_specification = material.get("materialSpecification")
        bom_item.material_model = material.get("materialModel")
        bom_item.bom_item_color = material.get("color")
        bom_item.remark = material.get("comment")
    else:
        # Insert new BOM item
        new_bom_item = BomItem(
            material_id=material_id,
            material_specification=material.get("materialSpecification"),
            material_model=material.get("materialModel"),
            bom_item_color=material.get("color"),
            unit_usage=material.get("unitUsage", 0),
            total_usage=material.get("totalUsage", 0),
            remark=material.get("comment"),
            production_instruction_item_id=item_id,
            bom_item_add_type=str(bom_type),
        )
        db.session.add(new_bom_item)


def _update_or_insert_craft_sheet_item(item_id, material, material_id):
    """Update or Insert Craft Sheet Item (without updating craft_name)"""
    craft_sheet_item = (
        db.session.query(CraftSheetItem)
        .filter(CraftSheetItem.production_instruction_item_id == item_id)
        .first()
    )

    if craft_sheet_item:
        # Update existing Craft Sheet item (except craft_name)
        craft_sheet_item.material_id = material_id
        craft_sheet_item.material_specification = material.get("materialSpecification")
        craft_sheet_item.material_model = material.get("materialModel")
        craft_sheet_item.color = material.get("color")
        craft_sheet_item.remark = material.get("comment")
        craft_sheet_item.pairs = material.get("pairs", 0)
        craft_sheet_item.total_usage = material.get("totalUsage", 0)
    else:
        # Insert new Craft Sheet item
        new_craft_item = CraftSheetItem(
            material_id=material_id,
            material_specification=material.get("materialSpecification"),
            material_model=material.get("materialModel"),
            color=material.get("color"),
            remark=material.get("comment"),
            pairs=material.get("pairs", 0),
            total_usage=material.get("totalUsage", 0),
            production_instruction_item_id=item_id,
        )
        db.session.add(new_craft_item)


def transform_standard_size_dict_to_grid(standard_size_dict):
    # Determine the maximum length of the lists in the dictionary
    max_len = (
        max(len(lst) for lst in standard_size_dict.values())
        if standard_size_dict
        else 0
    )

    # Build the columns array:
    # The first column is for the row header (the dictionary key).
    columns = [{"field": "col1", "width": 100}]
    # The rest of the columns are for the list values.
    for i in range(max_len):
        columns.append(
            {"field": f"col{i+2}", "minWidth": 160, "editRender": {"name": "input"}}
        )

    # Build the data array:
    # Each key in the dictionary becomes a row.
    data = []
    for key, lst in standard_size_dict.items():
        row = {}
        # First column contains the key (row header)
        row["col1"] = key
        # The following columns are the corresponding values from the list.
        for i in range(max_len):
            row[f"col{i+2}"] = lst[i] if i < len(lst) else ""
        data.append(row)

    # Build the final gridOptions dictionary.
    gridOptions = {
        "editConfig": {"trigger": "click", "mode": "cell"},
        "border": True,
        "showOverflow": True,
        "size": "small",
        "showHeader": False,
        "align": "center",
        "columns": columns,
        "data": data,
        "mergeCells": [
            {"row": 4, "col": 1, "rowspan": 1, "colspan": max_len},
        ],
    }
    return gridOptions


def transform_grid_to_standard_size_dict(grid_options):
    """
    Reverse the grid transformation by converting the grid options back to a dictionary.
    Expected grid_options format:
    {
      "columns": [ { "field": "col1", ... }, { "field": "col2", ... }, ... ],
      "data": [
         { "col1": "客人码", "col2": "S", "col3": "M", ... },
         { "col1": "大底", "col2": "", "col3": "", ... },
         ...
      ]
    }
    Returns a dict like:
    {
       "客人码": ["S", "M", ...],
       "大底": ["", "", ...],
       ...
    }
    """
    standard_size_dict = {}
    # Number of data columns is the total columns minus the header column
    columns = grid_options.get("columns", [])
    num_data_cols = len(columns) - 1

    for row in grid_options.get("data", []):
        key = row.get("col1")
        # Build the list of values using the subsequent columns
        values = [row.get(f"col{i+2}", "") for i in range(num_data_cols)]
        standard_size_dict[key] = values

    return standard_size_dict

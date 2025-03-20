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
@dev_revert_api.route("/devproductionorder/editrevertproductioninstruction", methods=["POST"])
def edit_revert_production_instruction():
    order_id = request.json.get("orderId")
    production_instruction_id = request.json.get("productionInstructionDbId")
    order_shoe_rid = request.json.get("orderShoeId")
    upload_data = request.json.get("uploadData")

    # Fetch the relevant Order Shoe record
    order_shoe = (
        db.session.query(OrderShoe)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )

    if not order_shoe:
        return jsonify({"error": "Order shoe not found"}), 404

    # Get production instruction
    production_instruction = (
        db.session.query(ProductionInstruction)
        .filter(
            ProductionInstruction.production_instruction_id
            == production_instruction_id
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
        .filter(ProductionInstructionItem.production_instruction_id == production_instruction_id)
        .all()
    }

    uploaded_item_ids = set()
    craft_sheet = db.session.query(CraftSheet).filter(CraftSheet.order_shoe_id == order_shoe.order_shoe_id).first()
    second_bom = (
        db.session.query(Bom)
        .join(OrderShoeType, Bom.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(OrderShoeType.order_shoe_id == order_shoe.order_shoe_id, Bom.bom_type == 1)
        .first()
    )

    for data in upload_data:
        shoe_color = data.get("color")

        # Fetch shoe_type_id
        shoe_type = (
            db.session.query(ShoeType)
            .join(Shoe, ShoeType.shoe_id == Shoe.shoe_id)
            .join(Color, ShoeType.color_id == Color.color_id)
            .filter(Shoe.shoe_rid == order_shoe_rid, Color.color_name == shoe_color)
            .first()
        )
        if not shoe_type:
            continue

        shoe_type_id = shoe_type.shoe_type_id

        # Fetch order_shoe_type_id
        order_shoe_type = (
            db.session.query(OrderShoeType)
            .filter(
                OrderShoeType.order_shoe_id == order_shoe.order_shoe_id,
                OrderShoeType.shoe_type_id == shoe_type_id,
            )
            .first()
        )

        if not order_shoe_type:
            continue

        order_shoe_type_id = order_shoe_type.order_shoe_type_id

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

                if item_id in existing_items:
                    # Update existing item
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
                        order_shoe_type_id=order_shoe_type_id,
                    )
                    db.session.add(new_item)
                    db.session.flush()
                    item_id = new_item.production_instruction_item_id
                    uploaded_item_ids.add(item_id)

                # Update/Add BOM Items
                first_bom_item_id = _update_or_insert_bom_item(
                    item_id, material, material_id, bom_type=0, order_shoe_type_id=order_shoe_type_id
                )

                if second_bom:
                    _update_or_insert_bom_item(
                        item_id, material, material_id, bom_type=1, order_shoe_type_id=order_shoe_type_id
                    )

                # Update/Add Craft Sheet Items
                if craft_sheet:
                    _update_or_insert_craft_sheet_item(item_id, material, material_id)

                # Update/Add Purchase Order Items
                if first_bom_item_id:
                    if material_type in ["S", "I", "O", "M", "H"]:
                        purchase_order_type = "F"
                    else:
                        purchase_order_type = "S"
                        
                    _update_or_insert_purchase_order_item(
                        item_id, material, material_id, first_bom_item_id, purchase_order_type
                    )

    for existing_id in list(existing_items.keys()):
        if existing_id not in uploaded_item_ids:
            # Delete associated BOM Items
            db.session.query(BomItem).filter(BomItem.production_instruction_item_id == existing_id).delete()

            # Delete associated Craft Sheet Items
            db.session.query(CraftSheetItem).filter(CraftSheetItem.production_instruction_item_id == existing_id).delete()

            # Delete ProductionInstructionItem
            db.session.delete(existing_items[existing_id])

    # Delete unreferenced Purchase Order Items for this order
    _delete_unreferenced_purchase_order_items(order_id)

    # Delete empty Purchase Divide Orders
    _delete_empty_purchase_divide_orders()

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


def _update_or_insert_bom_item(item_id, material, material_id, bom_type, order_shoe_type_id):
    """
    Update or Insert BOM Item for the specified bom_type (0 or 1).
    - Uses `order_shoe_type_id` to find the correct `bom_id`.
    """

    # Find the correct BOM for this shoe type
    bom = db.session.query(Bom).filter(
        Bom.bom_type == bom_type,
        Bom.order_shoe_type_id == order_shoe_type_id
    ).first()

    if not bom:
        return  # If no BOM exists, do not create a BOM item

    bom_id = bom.bom_id

    # Check if a BOM item already exists
    bom_item = db.session.query(BomItem).filter(
        BomItem.production_instruction_item_id == item_id,
        BomItem.bom_item_add_type == str(bom_type),
    ).first()

    if bom_item:
        # Update existing BOM item (except craft_name)
        bom_item.material_id = material_id
        bom_item.material_specification = material.get("materialSpecification")
        bom_item.material_model = material.get("materialModel")
        bom_item.bom_item_color = material.get("color")
        bom_item.remark = material.get("comment")
        bom_item_id = bom_item.bom_item_id  # Get existing bom_item_id
    else:
        # Insert new BOM item with correct bom_id
        new_bom_item = BomItem(
            material_id=material_id,
            bom_id=bom_id,  # Correct BOM ID assigned here
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
        db.session.flush()  # Get the newly created bom_item_id

        bom_item_id = new_bom_item.bom_item_id

    return bom_item_id  # Return the `bom_item_id`


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
        
def _update_or_insert_purchase_order_item(item_id, material, material_id, bom_item_id, purchase_order_type):
    """
    Update or Insert Purchase Order Item based on the Total BOM (`total_bom_id`).
    - Ensures the item is linked to a valid `PurchaseDivideOrder`
    - If an item with the same material properties exists, update its `approval_amount`
    - `approval_amount` is recalculated dynamically by summing values from all BOM items in the `total_bom`
    """

    # Fetch `bom_id` from the given `bom_item_id`
    bom_id = db.session.query(BomItem.bom_id).filter(BomItem.bom_item_id == bom_item_id).scalar()
    
    # Fetch the `total_bom_id` related to this `bom_id`
    total_bom_id = db.session.query(TotalBom.total_bom_id) \
        .join(Bom, Bom.total_bom_id == TotalBom.total_bom_id) \
        .filter(Bom.bom_id == bom_id).scalar()
    
    # Find the corresponding `purchase_order` (DO NOT create a new one)
    purchase_order = db.session.query(PurchaseOrder).filter(
        PurchaseOrder.bom_id == total_bom_id,
        PurchaseOrder.purchase_order_type == purchase_order_type
    ).first()

    if not purchase_order:
        # If no purchase order exists, exit without making changes.
        return

    # Ensure supplier exists
    supplier_id = _get_or_create_supplier(material.get("supplierName"))

    # Determine material category (0 = Normal, 1 = Special)
    material_category = db.session.query(Material.material_category) \
        .filter(Material.material_id == material_id).scalar() or 0  # Default to 0 if not found

    # Find or create a `PurchaseDivideOrder` using `purchase_order_rid + supplier_id`
    purchase_divide_order = _get_or_create_purchase_divide_order(purchase_order, supplier_id, material_category)

    # Craft name processing
    craft_name_list = material.get("materialCraftNameList", [])
    craft_name = "@".join(craft_name_list) if craft_name_list else ""

    # Check if a purchase order item with the same material properties exists
    existing_purchase_order_item = db.session.query(PurchaseOrderItem).filter(
        PurchaseOrderItem.purchase_divide_order_id == purchase_divide_order.purchase_divide_order_id,
        PurchaseOrderItem.material_id == material_id,
        PurchaseOrderItem.material_specification == material.get("materialSpecification"),
        PurchaseOrderItem.material_model == material.get("materialModel"),
        PurchaseOrderItem.color == material.get("color"),
    ).first()

    # Dynamically get all BOM items in the `total_bom_id` that contribute to this purchase order item
    matching_bom_items = db.session.query(BomItem).join(Bom, BomItem.bom_id == Bom.bom_id).filter(
        Bom.total_bom_id == total_bom_id,  # Ensure it's part of the same Total BOM
        BomItem.material_id == material_id,
        BomItem.material_specification == material.get("materialSpecification"),
        BomItem.material_model == material.get("materialModel"),
        BomItem.bom_item_color == material.get("color")
    ).all()

    # Sum up the total `approval_amount` from all matching BOM items in the `total_bom`
    total_approval_amount = sum(item.total_usage for item in matching_bom_items)

    if existing_purchase_order_item:
        # Update existing purchase order item
        existing_purchase_order_item.material_id = material_id
        existing_purchase_order_item.inbound_material_id = material_id  # Assuming inbound material matches
        existing_purchase_order_item.inbound_unit = material.get("unit")
        existing_purchase_order_item.material_specification = material.get("materialSpecification")
        existing_purchase_order_item.material_model = material.get("materialModel")
        existing_purchase_order_item.color = material.get("color")
        existing_purchase_order_item.craft_name = craft_name
        existing_purchase_order_item.remark = material.get("comment")
        existing_purchase_order_item.approval_amount = total_approval_amount  # Recalculate approval amount

    else:
        # Create a new purchase order item if no matching item is found
        new_purchase_order_item = PurchaseOrderItem(
            bom_item_id=bom_item_id,  # This is the first BOM item linked
            material_id=material_id,
            inbound_material_id=material_id,  # Assuming inbound material matches
            inbound_unit=material.get("unit"),
            material_specification=material.get("materialSpecification"),
            material_model=material.get("materialModel"),
            color=material.get("color"),
            craft_name=craft_name,
            remark=material.get("comment"),
            approval_amount=total_approval_amount,  # Set the recalculated approval amount
            purchase_divide_order_id=purchase_divide_order.purchase_divide_order_id,
            related_selected_material_storage=json.dumps([])
            
        )
        db.session.add(new_purchase_order_item)

    db.session.flush()  # Ensure ID gets assigned before commit


        
def _get_or_create_purchase_divide_order(purchase_order, supplier_id, material_category):
    """
    Finds or creates a `PurchaseDivideOrder` for the given `purchase_order` and `supplier_id`.
    - `purchase_divide_order_rid` = `purchase_order_rid + supplier_id`
    - `purchase_divide_order_type`: "N" (General Materials) or "S" (Special Materials)
    """
    purchase_divide_order_rid = f"{purchase_order.purchase_order_rid}{str(supplier_id).zfill(4)}"
    
    # Determine the divide order type based on material category
    purchase_divide_order_type = "N" if material_category == 0 else "S"

    purchase_divide_order = db.session.query(PurchaseDivideOrder).filter(
        PurchaseDivideOrder.purchase_order_id == purchase_order.purchase_order_id,
        PurchaseDivideOrder.purchase_divide_order_rid == purchase_divide_order_rid
    ).first()

    if not purchase_divide_order:
        purchase_divide_order = PurchaseDivideOrder(
            purchase_order_id=purchase_order.purchase_order_id,
            purchase_divide_order_rid=purchase_divide_order_rid,
            purchase_divide_order_type=purchase_divide_order_type
        )
        db.session.add(purchase_divide_order)
        db.session.flush()

    return purchase_divide_order

def _get_or_create_supplier(supplier_name):
    """
    Finds or creates a supplier and returns its `supplier_id`.
    """
    if not supplier_name:
        supplier_name = "DEFAULT_SUPPLIER"

    supplier = db.session.query(Supplier).filter(Supplier.supplier_name == supplier_name).first()
    
    if not supplier:
        supplier = Supplier(supplier_name=supplier_name)
        db.session.add(supplier)
        db.session.flush()

    return supplier.supplier_id

def _delete_empty_purchase_divide_orders():
    """
    Deletes any `PurchaseDivideOrder` that no longer has associated `PurchaseOrderItem`.
    """
    empty_divide_orders = db.session.query(PurchaseDivideOrder).filter(
        ~db.session.query(PurchaseOrderItem)
        .filter(PurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id)
        .exists()
    ).all()

    for divide_order in empty_divide_orders:
        db.session.delete(divide_order)
        
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

def _delete_unreferenced_purchase_order_items(order_id):
    """
    Deletes Purchase Order Items that do not exist in the Total BOM for a given order.
    - Processes only Purchase Orders related to `order_id`.
    """

    # Get all purchase orders linked to this order
    purchase_orders = db.session.query(PurchaseOrder, Order).join(Order, PurchaseOrder.order_id == Order.order_id) \
        .filter(Order.order_rid == order_id).all()
    for purchase_order, order in purchase_orders:
        total_bom_id = purchase_order.bom_id

        # Get all valid BomItems in this Total BOM
        valid_bom_items = db.session.query(BomItem).join(Bom, BomItem.bom_id == Bom.bom_id) \
            .filter(Bom.total_bom_id == total_bom_id).all()
        # Create a lookup set of valid materials
        valid_materials = {
            (item.material_id, item.material_specification, item.material_model, item.bom_item_color)
            for item in valid_bom_items
        }
        # Get purchase order items linked to this order’s purchase orders
        purchase_order_items = db.session.query(PurchaseOrderItem) \
            .join(PurchaseDivideOrder, PurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id) \
            .filter(PurchaseDivideOrder.purchase_order_id == purchase_order.purchase_order_id) \
            .all()
        for po_item in purchase_order_items:
            po_key = (po_item.material_id, po_item.material_specification, po_item.material_model, po_item.color)
            # If the purchase order item does not exist in the valid BOM items, delete it
            if po_key not in valid_materials:
                db.session.delete(po_item)


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

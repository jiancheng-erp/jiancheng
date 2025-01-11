from flask import Blueprint, jsonify, request, send_file, current_app
import os
import datetime
from app_config import app, db
from models import *
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from api_utility import randomIdGenerater
from general_document.prodution_instruction import generate_instruction_excel_file

process_sheet_upload_bp = Blueprint("process_sheet_upload", __name__)


@process_sheet_upload_bp.route("/craftsheet/getordershoelist", methods=["GET"])
def get_order_list():
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
        if order_shoe.process_sheet_upload_status == "0":
            status_string = "未上传"
        elif order_shoe.process_sheet_upload_status == "1":
            status_string = "已上传"
        elif order_shoe.process_sheet_upload_status == "2":
            status_string = "等待用量填写"
        elif order_shoe.process_sheet_upload_status == "3":
            status_string = "完成用量填写"
        elif order_shoe.process_sheet_upload_status == "4":
            status_string = "已审核并下发"

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


@process_sheet_upload_bp.route("/craftsheet/getnewcraftsheetid", methods=["GET"])
def get_new_production_instruction_id():
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    craft_sheet_id = current_time_stamp + random_string + "CS"
    return jsonify({"craftSheetId": craft_sheet_id})


@process_sheet_upload_bp.route("/devproductionorder/getordershoeinfo", methods=["GET"])
def get_order_shoe_info():
    order_id = request.args.get("orderid")
    order_shoe_rid = request.args.get("ordershoeid")
    order_shoe = (
        db.session.query(Order, Customer, OrderShoe, Shoe)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(Order.order_id == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )
    customer_name = order_shoe.Customer.customer_name
    customer_product_name = order_shoe.OrderShoe.customer_product_name
    shoe_designer = order_shoe.Shoe.shoe_designer
    brand_name = order_shoe.Customer.customer_brand
    shoe_adjuster = order_shoe.OrderShoe.adjust_staff
    order_shoe_type = (
        db.session.query(OrderShoeType, ShoeType, Color)
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(OrderShoeType.order_shoe_id == order_shoe.OrderShoe.order_shoe_id)
        .all()
    )
    color_list = []
    for shoe_type in order_shoe_type:
        color_list.append(shoe_type.Color.color_name)
    color_str = ", ".join(color_list)
    result = {
        "customerName": customer_name,
        "customerProductName": customer_product_name,
        "shoeDesigner": shoe_designer,
        "brandName": brand_name,
        "shoeAdjuster": shoe_adjuster,
        "color": color_str,
    }
    return jsonify(result)


def create_craft_sheet_item(
    input_material_data, input_material_type, order_shoe_type_id, craft_sheet_id
):
    for material_data in input_material_data:
        material_id = material_data.get("materialId", None)
        if not material_id:
            return jsonify({"message": "材料不存在"})
        material_variant_id = material_data.get("materialVariantId", None)
        if not material_variant_id:
            is_material_variant_exist = (
                db.session.query(MaterialVariant, Material, Supplier)
                .join(
                    Material,
                    MaterialVariant.material_id == Material.material_id,
                )
                .join(
                    Supplier, MaterialVariant.material_supplier == Supplier.supplier_id
                )
                .filter(
                    Material.material_name == material_data.get("materialName"),
                    MaterialVariant.material_model
                    == material_data.get("materialModel"),
                    MaterialVariant.material_specification
                    == material_data.get("materialSpecification"),
                    MaterialVariant.color == material_data.get("color"),
                    Supplier.supplier_name == material_data.get("supplierName"),
                )
                .first()
            )
            if is_material_variant_exist:
                material_variant_id = (
                    is_material_variant_exist.MaterialVariant.material_variant_id
                )
            else:
                is_supplier_exist = (
                    db.session.query(Supplier)
                    .filter(Supplier.supplier_name == material_data.get("supplierName"))
                    .first()
                )
                if is_supplier_exist:
                    supplier_id = is_supplier_exist.supplier_id
                else:
                    supplier = Supplier(supplier_name=material_data.get("supplierName"))
                    db.session.add(supplier)
                    db.session.flush()
                    supplier_id = supplier.supplier_id
                material_variant = MaterialVariant(
                    material_id=material_data.get("materialId"),
                    material_model=material_data.get("materialModel", None),
                    material_specification=material_data.get(
                        "materialSpecification", None
                    ),
                    color=material_data.get("color", None),
                    material_supplier=supplier_id,
                )
                db.session.add(material_variant)
                db.session.flush()
                material_variant_id = material_variant.material_variant_id
        material_color = (
            (material_data.get("color") if material_data.get("color") else None),
        )
        material_source = (
            material_data.get("materialSource")
            if material_data.get("materialSource")
            and material_data.get("materialSource") != None
            else "C"
        )
        remark = material_data.get("comment") if material_data.get("comment") else None
        department_id = (
            material_data.get("useDepart") if material_data.get("useDepart") else None
        )
        is_pre_purchase = (
            material_data.get("isPurchase") if material_data.get("isPurchase") else None
        )
        material_second_type = (
            material_data.get("materialDetailType")
            if material_data.get("materialDetailType")
            else None
        )
        material_type = input_material_type
        craft_name_list = material_data.get("materialCraftNameList", None)
        if craft_name_list != [] and craft_name_list != None:
            craft_name = "@".join(craft_name_list)
        else:
            craft_name = ""

        craft_sheet_item = CraftSheetItem(
            craft_sheet_id=craft_sheet_id,
            material_variant_id=material_variant_id,
            color=material_color,
            remark=remark,
            department_id=department_id,
            material_type=material_type,
            order_shoe_type_id=order_shoe_type_id,
            material_second_type=material_second_type,
            material_source=material_source,
            craft_name=craft_name,
            after_usage_symbol=0,
            production_instruction_item_id=material_data.get(
                "productionInstructionItemId", None
            ),
        )
        db.session.add(craft_sheet_item)


@process_sheet_upload_bp.route("/craftsheet/savecraftsheet", methods=["POST"])
def save_craft_sheet():
    order_id = request.json.get("orderId")
    order_shoe_rid = request.json.get("orderShoeId")
    craft_sheet_rid = request.json.get("craftSheetId")
    upload_data = request.json.get("uploadData")
    craft_sheet_detail = request.json.get("craftSheetDetail")
    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
        .OrderShoe
    )
    order_shoe_id = order_shoe.order_shoe_id
    craft_sheet = (
        db.session.query(CraftSheet)
        .filter(CraftSheet.craft_sheet_rid == craft_sheet_rid)
        .first()
    )
    craft_sheet_id = craft_sheet.craft_sheet_id
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
    craft_sheet_items = (
        db.session.query(CraftSheetItem)
        .filter(CraftSheetItem.craft_sheet_id == craft_sheet_id)
        .all()
    )
    for item in craft_sheet_items:
        db.session.delete(item)
    for data in upload_data:
        shoe_color = data.get("color")
        print(shoe_color)
        shoe_type_id = (
            db.session.query(Shoe, ShoeType, Color)
            .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
            .join(Color, ShoeType.color_id == Color.color_id)
            .filter(Shoe.shoe_rid == order_shoe_rid, Color.color_name == shoe_color)
            .first()
            .ShoeType.shoe_type_id
        )
        order_shoe_type_id = (
            db.session.query(OrderShoeType)
            .filter(
                OrderShoeType.order_shoe_id == order_shoe_id,
                OrderShoeType.shoe_type_id == shoe_type_id,
            )
            .first()
            .order_shoe_type_id
        )
        if len(data.get("surfaceMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("surfaceMaterialData"), "S", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("insideMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("insideMaterialData"), "I", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("accessoryMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("accessoryMaterialData"),
                "A",
                order_shoe_type_id,
                craft_sheet_id,
            )
        if len(data.get("outsoleMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("outsoleMaterialData"), "O", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("midsoleMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("midsoleMaterialData"), "M", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("lastMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("lastMaterialData"), "L", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("hotsoleMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("hotsoleMaterialData"), "H", order_shoe_type_id, craft_sheet_id
            )
    order_shoe.adjust_staff = craft_sheet_detail.get("adjuster")
    order_shoe.process_sheet_upload_status = "1"
    db.session.commit()
    return jsonify({"message": "Production order uploaded successfully"})


@process_sheet_upload_bp.route("/craftsheet/getoriginmaterialinfo", methods=["GET"])
def get_origin_material_info():
    order_id = request.args.get("orderid")
    order_shoe_rid = request.args.get("ordershoeid")

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

    if not craft_sheet:
        craft_sheet_id = None
        craft_sheet_rid = None
    else:
        craft_sheet_id = craft_sheet.craft_sheet_id
        craft_sheet_rid = craft_sheet.craft_sheet_rid
    production_instruction = (
        db.session.query(ProductionInstruction)
        .join(OrderShoe, ProductionInstruction.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )

    production_instruction_id = production_instruction.production_instruction_id
    production_instruction_rid = production_instruction.production_instruction_rid

    # Fetch all items related to the production instruction
    production_instruction_items = (
        db.session.query(ProductionInstructionItem, Color)
        .join(
            OrderShoeType,
            OrderShoeType.order_shoe_type_id
            == ProductionInstructionItem.order_shoe_type_id,
        )
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(
            ProductionInstructionItem.production_instruction_id
            == production_instruction_id
        )
        .all()
    )
    # Dictionary to hold the organized data by color
    result_dict = {}
    for row in production_instruction_items:
        item, color = row
        color_name = color.color_name
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
            db.session.query(MaterialVariant, Material, MaterialType, Supplier)
            .join(Material, MaterialVariant.material_id == Material.material_id)
            .join(
                MaterialType, Material.material_type_id == MaterialType.material_type_id
            )
            .join(Supplier, MaterialVariant.material_supplier == Supplier.supplier_id)
            .filter(Material.material_id == item.material_id)
            .first()
        )
        if item.craft_name != None:
            material_craft_list = item.craft_name.split("@")
            material_craft_name = ",".join(material_craft_list)
        else:
            material_craft_list = []
            material_craft_name = ""
        # Map material type to the appropriate array in the dictionary
        material_data = {
            "materialVariantId": item.material_variant_id,
            "materialId": material.Material.material_id,
            "materialType": material.MaterialType.material_type_name,
            "materialName": material.Material.material_name,
            "materialModel": material.MaterialVariant.material_model,
            "materialSpecification": material.MaterialVariant.material_specification,
            "color": material.MaterialVariant.color,
            "unit": material.MaterialVariant.material_unit,
            "supplierName": material.Supplier.supplier_name,
            "comment": item.remark,
            "useDepart": item.department_id,
            "isPurchase": item.is_pre_purchase,
            "materialCraftName": material_craft_name,
            "materialCraftNameList": material_craft_list,
            "materialDetailType": item.material_second_type,
            "materialSource": "P",
            "productionInstructionItemId": item.production_instruction_item_id,
        }

        if item.material_type == "S":
            result_dict[color_name]["surfaceMaterialData"].append(material_data)
        elif item.material_type == "I":
            result_dict[color_name]["insideMaterialData"].append(material_data)
        elif item.material_type == "A":
            result_dict[color_name]["accessoryMaterialData"].append(material_data)
        elif item.material_type == "O":
            result_dict[color_name]["outsoleMaterialData"].append(material_data)
        elif item.material_type == "M":
            result_dict[color_name]["midsoleMaterialData"].append(material_data)
        elif item.material_type == "L":
            result_dict[color_name]["lastMaterialData"].append(material_data)
        elif item.material_type == "H":
            result_dict[color_name]["hotsoleMaterialData"].append(material_data)

    # Convert result dictionary to list for JSON response
    result = list(result_dict.values())
    production_instruction_detail = {
        "originSize": production_instruction.origin_size,
        "sizeRange": production_instruction.size_range,
        "lastType": production_instruction.last_type,
        "sizeDifference": production_instruction.size_difference,
    }
    fin_result = {
        "productionInstructionId": production_instruction_rid,
        "instructionData": result,
        "productionInstructionDetail": production_instruction_detail,
    }

    return jsonify(fin_result)


@process_sheet_upload_bp.route("/craftsheet/getcraftsheetinfo", methods=["GET"])
def get_craft_sheet_info():
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
        .filter(CraftSheetItem.craft_sheet_id == craft_sheet_id)
        .all()
    )

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
            db.session.query(MaterialVariant, Material, MaterialType, Supplier)
            .join(Material, MaterialVariant.material_id == Material.material_id)
            .join(
                MaterialType, Material.material_type_id == MaterialType.material_type_id
            )
            .join(Supplier, MaterialVariant.material_supplier == Supplier.supplier_id)
            .filter(
                MaterialVariant.material_variant_id
                == item.CraftSheetItem.material_variant_id
            )
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
            "materialId": material.Material.material_id,
            "materialType": material.MaterialType.material_type_name,
            "materialName": material.Material.material_name,
            "materialModel": material.MaterialVariant.material_model,
            "materialSpecification": material.MaterialVariant.material_specification,
            "color": material.MaterialVariant.color,
            "unit": material.MaterialVariant.material_unit,
            "supplierName": material.Supplier.supplier_name,
            "comment": item.CraftSheetItem.remark,
            "useDepart": item.CraftSheetItem.department_id,
            "pairs": item.CraftSheetItem.pairs,
            "unitUsage": item.CraftSheetItem.unit_usage,
            "materialCraftName": material_craft_name,
            "materialCraftNameList": material_craft_list,
            "materialDetailType": item.CraftSheetItem.material_second_type,
            "materialSource": item.CraftSheetItem.material_source,
            "productionInstructionItemId": item.CraftSheetItem.production_instruction_item_id,
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


@process_sheet_upload_bp.route("/craftsheet/editcraftsheet", methods=["POST"])
def edit_craft_sheet():
    order_id = request.json.get("orderId")
    order_shoe_rid = request.json.get("orderShoeId")
    craft_sheet_rid = request.json.get("craftSheetId")
    upload_data = request.json.get("uploadData")
    craft_sheet_detail = request.json.get("craftSheetDetail")
    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
        .OrderShoe
    )
    order_shoe_id = order_shoe.order_shoe_id
    craft_sheet = (
        db.session.query(CraftSheet)
        .filter(CraftSheet.craft_sheet_rid == craft_sheet_rid)
        .first()
    )
    craft_sheet_id = craft_sheet.craft_sheet_id
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
    craft_sheet_items = (
        db.session.query(CraftSheetItem)
        .filter(CraftSheetItem.craft_sheet_id == craft_sheet_id)
        .all()
    )
    for item in craft_sheet_items:
        db.session.delete(item)
    for data in upload_data:
        shoe_color = data.get("color")
        print(shoe_color)
        shoe_type_id = (
            db.session.query(Shoe, ShoeType, Color)
            .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
            .join(Color, ShoeType.color_id == Color.color_id)
            .filter(Shoe.shoe_rid == order_shoe_rid, Color.color_name == shoe_color)
            .first()
            .ShoeType.shoe_type_id
        )
        order_shoe_type_id = (
            db.session.query(OrderShoeType)
            .filter(
                OrderShoeType.order_shoe_id == order_shoe_id,
                OrderShoeType.shoe_type_id == shoe_type_id,
            )
            .first()
            .order_shoe_type_id
        )
        if len(data.get("surfaceMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("surfaceMaterialData"), "S", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("insideMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("insideMaterialData"), "I", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("accessoryMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("accessoryMaterialData"),
                "A",
                order_shoe_type_id,
                craft_sheet_id,
            )
        if len(data.get("outsoleMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("outsoleMaterialData"), "O", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("midsoleMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("midsoleMaterialData"), "M", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("lastMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("lastMaterialData"), "L", order_shoe_type_id, craft_sheet_id
            )
        if len(data.get("hotsoleMaterialData")) > 0:
            create_craft_sheet_item(
                data.get("hotsoleMaterialData"), "H", order_shoe_type_id, craft_sheet_id
            )
    order_shoe.adjust_staff = craft_sheet_detail.get("adjuster")
    order_shoe.process_sheet_upload_status = "1"
    db.session.commit()
    return jsonify({"message": "Production instruction updated successfully"}), 200


@process_sheet_upload_bp.route("/craftsheet/uploadcutdieimg", methods=["POST"])
def upload_cut_die_img():
    order_id = request.form.get("orderId")
    order_shoe_rid = request.form.get("orderShoeId")
    craft_sheet_rid = request.form.get("craftSheetId")
    file = request.files["file"]
    file_name = file.filename
    folder_path = os.path.join(IMAGE_UPLOAD_PATH, order_id, order_shoe_rid, "刀模图")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    file.save(file_path)
    craft_sheet = (
        db.session.query(CraftSheet)
        .filter(CraftSheet.craft_sheet_rid == craft_sheet_rid)
        .first()
    )
    online_path = (
        IMAGE_STORAGE_PATH + order_id + "/" + order_shoe_rid + "/刀模图/" + file_name
    )
    craft_sheet.cut_die_img_path = online_path
    db.session.commit()
    return jsonify({"filePath": online_path}), 200


@process_sheet_upload_bp.route("/craftsheet/uploadpicnoteimg", methods=["POST"])
def upload_pic_note_img():
    order_id = request.form.get("orderId")
    order_shoe_rid = request.form.get("orderShoeId")
    craft_sheet_rid = request.form.get("craftSheetId")
    file = request.files["file"]
    file_name = file.filename
    folder_path = os.path.join(IMAGE_UPLOAD_PATH, order_id, order_shoe_rid, "图样备注")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    file.save(file_path)
    craft_sheet = (
        db.session.query(CraftSheet)
        .filter(CraftSheet.craft_sheet_rid == craft_sheet_rid)
        .first()
    )
    online_path = (
        IMAGE_STORAGE_PATH + order_id + "/" + order_shoe_rid + "/图样备注/" + file_name
    )
    craft_sheet.pic_note_img_path = online_path
    db.session.commit()
    return jsonify({"filePath": online_path}), 200


@process_sheet_upload_bp.route("/craftsheet/uploadprocesssheet", methods=["POST"])
def upload_process_sheet():
    order_id = request.form.get("orderId")
    order_shoe_rid = request.form.get("orderShoeId")
    craft_sheet_rid = request.form.get("craftSheetId")
    file = request.files["file"]
    file_name = file.filename
    new_file_ext = file_name.split(".")[-1]
    new_file_name = order_id + "_" + order_shoe_rid + "_工艺单." + new_file_ext
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid, "工艺单")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, new_file_name)
    file.save(file_path)
    return jsonify({"filePath": file_path}), 200


@process_sheet_upload_bp.route("/craftsheet/issue", methods=["POST"])
def issue_production_order():
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
        print(order_shoe.OrderShoe.process_sheet_upload_status)
        if order_shoe.OrderShoe.process_sheet_upload_status != "1":
            return jsonify({"error": "Production order not uploaded yet"}), 500
        order_shoe.OrderShoe.process_sheet_upload_status = "2"
        craft_sheet = (
            db.session.query(CraftSheet)
            .filter(CraftSheet.order_shoe_id == order_shoe_id)
            .first()
        )
        craft_sheet.craft_sheet_status = "2"
        craft_sheet_items = (
            db.session.query(CraftSheetItem)
            .filter(CraftSheetItem.craft_sheet_id == craft_sheet.craft_sheet_id)
            .all()
        )
        order_shoe_types = (
            db.session.query(OrderShoeType)
            .filter(OrderShoeType.order_shoe_id == order_shoe_id)
            .all()
        )
        for order_shoe_type in order_shoe_types:
            order_shoe_type_id = order_shoe_type.order_shoe_type_id
            current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
            random_string = randomIdGenerater(6)
            second_bom_rid = current_time_stamp + random_string + "S"
            second_bom = Bom(
                order_shoe_type_id=order_shoe_type_id,
                bom_rid=second_bom_rid,
                bom_type=1,
                bom_status=0,
            )
            db.session.add(second_bom)
            db.session.flush()
            second_bom_id = second_bom.bom_id
            for item in craft_sheet_items:
                material_storage = (
                    db.session.query(MaterialStorage)
                    .filter(
                        MaterialStorage.order_shoe_id == order_shoe_id,
                        MaterialStorage.material_variant_id == item.material_variant_id,
                    )
                    .first()
                )
                if material_storage:
                    material_storage.craft_name = item.craft_name
                size_material_storage = (
                    db.session.query(SizeMaterialStorage)
                    .filter(
                        SizeMaterialStorage.order_shoe_id == order_shoe_id,
                        SizeMaterialStorage.material_variant_id == item.material_variant_id,
                    )
                    .first()
                )
                if size_material_storage:
                    size_material_storage.craft_name = item.craft_name
                if item.order_shoe_type_id == order_shoe_type.order_shoe_type_id:
                    craft_list = item.craft_name.split("@")
                    for craft in craft_list:
                        bom_item = BomItem(
                            bom_id=second_bom_id,
                            material_id=item.material_id,
                            material_model=item.material_model,
                            material_specification=item.material_specification,
                            bom_item_color=item.color,
                            remark=item.remark,
                            department_id=item.department_id,
                            size_type="E",
                            bom_item_add_type="1",
                            total_usage=0,
                            material_second_type=item.material_second_type,
                            craft_name=craft,
                        )
                        db.session.add(bom_item)
        # create excel file
        # insert_data = []
        # transdict = {
        #     "S": "面料",
        #     "I": "里料",
        #     "A": "辅料",
        #     "O": "底材",
        #     "M": "中底",
        #     "L": "楦头",
        #     "H": "复合",
        # }
        # order_rid = order_rid
        # order_shoe_rid = order_shoe_rid
        # customer_shoe_name = order_shoe.OrderShoe.customer_product_name
        # last_type = production_instruction.last_type
        # size_range = production_instruction.size_range
        # size_difference = production_instruction.size_difference
        # origin_size = production_instruction.origin_size
        # designer = order_shoe.Shoe.shoe_designer
        # brand = (
        #     db.session.query(Customer)
        #     .filter(Customer.customer_id == order_shoe.Order.customer_id)
        #     .first()
        #     .customer_brand
        # )
        # colors = []
        # for item in production_instruction_items:
        #     order_shoe_type_id = item.order_shoe_type_id
        #     shoe_color = (
        #         db.session.query(OrderShoeType, ShoeType, Color)
        #         .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        #         .join(Color, ShoeType.color_id == Color.color_id)
        #         .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
        #         .first()
        #     )
        #     if shoe_color.Color.color_name not in colors:
        #         colors.append(shoe_color.Color.color_name)
        #     color_name = shoe_color.Color.color_name
        #     material_type = transdict[item.material_type]
        #     material_second_type = item.material_second_type
        #     material = (
        #         db.session.query(Material, Supplier)
        #         .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        #         .filter(Material.material_id == item.material_id)
        #         .first()
        #     )
        #     material_name = material.Material.material_name
        #     unit = material.Material.material_unit
        #     material_model = item.material_model
        #     material_specification = item.material_specification
        #     color = item.color
        #     remark = item.remark
        #     supplier_name = material.Supplier.supplier_name
        #     insert_data.append(
        #         {
        #             "鞋型颜色": color_name,
        #             "材料类型": material_type,
        #             "材料二级类型": material_second_type,
        #             "材料名称": material_name,
        #             "单位": unit,
        #             "材料型号": material_model,
        #             "材料规格": material_specification,
        #             "颜色": color,
        #             "备注": remark,
        #             "厂家名称": supplier_name,
        #         }
        #     )
        # color_string = "、".join(colors)
        # image_save_path = os.path.join(
        #     FILE_STORAGE_PATH, order_rid, order_shoe_rid, "shoe_image.jpg"
        # )
        # shoe_directory = os.path.join(IMAGE_UPLOAD_PATH, "shoe", order_shoe_rid)

        # # Get the list of folders inside the directory
        # folders = os.listdir(shoe_directory)

        # # Filter out any non-folder entries (just in case)
        # folders = [f for f in folders if os.path.isdir(os.path.join(shoe_directory, f))]

        # # Get the first folder in the directory
        # if folders:
        #     first_folder = folders[0]
        #     image_path = os.path.join(
        #         IMAGE_UPLOAD_PATH,
        #         "shoe",
        #         order_shoe_rid,
        #         first_folder,
        #         "shoe_image.jpg",
        #     )
        # else:
        #     image_path = os.path.join(
        #         IMAGE_UPLOAD_PATH, "shoe", order_shoe_rid, "shoe_image.jpg"
        #     )
        # try:
        #     generate_instruction_excel_file(
        #         os.path.join(FILE_STORAGE_PATH, "投产指令单模版.xlsx"),
        #         os.path.join(
        #             FILE_STORAGE_PATH, order_rid, order_shoe_rid, "投产指令单.xlsx"
        #         ),
        #         {
        #             "order_id": order_rid,
        #             "inherit_id": order_shoe_rid,
        #             "customer_id": customer_shoe_name,
        #             "last_type": last_type,
        #             "size_range": size_range,
        #             "size_difference": size_difference,
        #             "origin_size": origin_size,
        #             "designer": designer,
        #             "brand": brand,
        #             "colors": color_string,
        #         },
        #         insert_data,
        #         image_path,
        #         image_save_path,
        #     )
        # except Exception:
        #     return jsonify({"error": "Failed to issue production order"}), 500
        event_arr = []
        processor: EventProcessor = current_app.config["event_processor"]
        try:
            for operation_id in [56, 57, 58, 59]:
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
        db.session.flush()
    db.session.commit()
    return jsonify({"message": "Production order issued successfully"})


@process_sheet_upload_bp.route("/devproductionorder/uploadpicnotes", methods=["POST"])
def upload_pic_notes():
    order_shoe_rid = request.form.get("orderShoeRId")
    order_id = request.form.get("orderId")
    pic_note = request.files["file"]
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid)
    _, file_extension = os.path.splitext(pic_note.filename)
    # Construct the new filename
    new_filename = f"投产指令单备注图片{file_extension}"
    if os.path.exists(folder_path) == False:
        os.mkdir(folder_path)
    file_path = os.path.join(folder_path, new_filename)
    pic_note.save(file_path)
    return jsonify({"message": "Picture notes uploaded successfully"}), 200


@process_sheet_upload_bp.route(
    "/devproductionorder/getautofinishedmaterialname", methods=["GET"]
)
def get_auto_finished_material_name():
    material_name = request.args.get("materialName")
    material = (
        db.session.query(Material)
        .filter(
            Material.material_name.like(f"%{material_name}%"),
        )
        .distinct()
        .all()
    )
    material_list = []
    if material:
        for item in material:
            material_list.append(
                {
                    "name": item.material_name,
                }
            )
        return jsonify(material_list), 200
    else:
        return jsonify([]), 200


@process_sheet_upload_bp.route(
    "/devproductionorder/getautofinishedsuppliername", methods=["GET"]
)
def get_auto_finished_supplier_name():
    supplier_name = request.args.get("supplierName")
    supplier = (
        db.session.query(Supplier)
        .filter(
            Supplier.supplier_name.like(f"%{supplier_name}%"),
        )
        .distinct()
        .all()
    )
    supplier_list = []
    if supplier:
        for item in supplier:
            supplier_list.append(
                {
                    "name": item.supplier_name,
                }
            )
        return jsonify(supplier_list), 200
    else:
        return jsonify([]), 200


@process_sheet_upload_bp.route("/craftsheet/downloadcraftsheet", methods=["GET"])
def download_craft_sheet():
    # Get parameters from request
    order_id = request.args.get("orderid")
    order_shoe_rid = request.args.get("ordershoeid")
    print(order_id, order_shoe_rid)

    # Query the database for the order and shoe details
    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )

    # Define folder and potential file paths
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid, "工艺单")
    file_name_prefix = f"{order_id}_{order_shoe_rid}_工艺单"
    possible_files = [f"{file_name_prefix}.xlsx", f"{file_name_prefix}.xls"]

    # Check which file exists
    file_path = None
    for file_name in possible_files:
        candidate_path = os.path.join(folder_path, file_name)
        if os.path.exists(candidate_path):
            file_path = candidate_path
            break

    if file_path is None:
        return {"error": "File not found"}, 404

    # Define the downloadable file name
    new_name = f"{order_id}-{order_shoe_rid}_工艺单.xlsx"

    # Send the file
    return send_file(file_path, as_attachment=True, download_name=new_name)


@process_sheet_upload_bp.route(
    "/devproductionorder/downloadproductioninstruction", methods=["GET"]
)
def download_production_instruction():
    order_shoe_rid = request.args.get("ordershoerid")
    order_id = request.args.get("orderid")
    print(order_shoe_rid, order_id)
    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid)
    file_path = os.path.join(folder_path, "投产指令单.xlsx")
    new_name = order_id + "-" + order_shoe_rid + "_投产指令单.xlsx"
    return send_file(file_path, as_attachment=True, download_name=new_name)


@process_sheet_upload_bp.route("/devproductionorder/downloadpicnotes", methods=["GET"])
def download_pic_notes():
    order_shoe_rid = request.args.get("ordershoerid")
    order_id = request.args.get("orderid")
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid)
    file_path = os.path.join(folder_path, "投产指令单备注图片.jpg")
    new_name = order_id + "-" + order_shoe_rid + "_投产指令单备注图片.jpg"
    return send_file(file_path, as_attachment=True, download_name=new_name)

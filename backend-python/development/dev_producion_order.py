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

dev_producion_order_bp = Blueprint("dev_producion_order_bp", __name__)


@dev_producion_order_bp.route("/devproductionorder/getordershoelist", methods=["GET"])
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
        if order_shoe.production_order_upload_status == "0":
            status_string = "未上传"
        elif order_shoe.production_order_upload_status == "1":
            status_string = "已上传"
        elif order_shoe.production_order_upload_status == "2":
            status_string = "已下发"

        # Grouping by shoe_rid (inheritId) to avoid duplicate shoes
        # Initialize the result dictionary for the shoe if not already present
        if shoe.shoe_rid not in result_dict:
            result_dict[shoe.shoe_rid] = {
                "orderId": order.order_rid,
                "orderShoeId": order_shoe.order_shoe_id,
                "inheritId": shoe.shoe_rid,
                "status": status_string,
                "customerProductName": order_shoe.customer_product_name,
                "designer": shoe.shoe_designer,
                "editter": order_shoe.adjust_staff,
                "typeInfos": [],  # Initialize list for type info (colors, etc.)
                "colorSet": set(),  # Initialize set to track colors and prevent duplicate entries
                "businessTechnicalRemark": order_shoe.business_technical_remark,
                "businessMaterialRemark": order_shoe.business_material_remark,
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


@dev_producion_order_bp.route(
    "/devproductionorder/getnewproductioninstructionid", methods=["GET"]
)
def get_new_production_instruction_id():
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    production_instruction_id = current_time_stamp + random_string + "PI"
    return jsonify({"productionInstructionId": production_instruction_id})


@dev_producion_order_bp.route("/devproductionorder/getordershoeinfo", methods=["GET"])
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


def _save_instruction_helper(
    input_data,
    input_production_instruction_id,
    input_material_type,
    input_order_shoe_type_id,
    input_material_category=0,
):
    for material_data in input_data:
        supplier_name = material_data.get("supplierName", None)
        material_name = material_data.get("materialName", None)
        # if supplier_name not provided, default to DEFAULT_SUPPLIER
        if not supplier_name:
            supplier_name = DEFAULT_SUPPLIER

        # query db to check if material exists
        is_material_exist = (
            db.session.query(Material, Supplier)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                Material.material_name == material_name,
                Supplier.supplier_name == supplier_name,
            )
            .first()
        )

        # if no such material of supplier exists, create new material
        if not is_material_exist:
            is_supplier_exist = (
                db.session.query(Supplier)
                .filter(Supplier.supplier_name == supplier_name)
                .first()
            )
            if is_supplier_exist:
                supplier_id = is_supplier_exist.supplier_id
            else:
                supplier = Supplier(supplier_name=supplier_name)
                db.session.add(supplier)
                db.session.flush()
                supplier_id = supplier.supplier_id
            material_type_id = (
                db.session.query(MaterialType)
                .filter(
                    MaterialType.material_type_name
                    == material_data.get("materialType")
                )
                .first()
                .material_type_id
            )
            if material_data.get("materialType") == "烫底":
                input_material_category = 1

            material = Material(
                material_name=material_name,
                material_supplier=supplier_id,
                material_unit=material_data.get("unit"),
                material_creation_date=datetime.datetime.now(),
                material_type_id=material_type_id,
                material_category=input_material_category,
            )
            db.session.add(material)
            db.session.flush()
            material_id = material.material_id
        else:
            material_id = is_material_exist.Material.material_id

        material_model = material_data.get("materialModel", None)
        material_spec = material_data.get("materialSpecification", None)
        material_color = material_data.get("color", None)
        remark = material_data.get("comment", None)
        processing_remark = material_data.get("processingRemark", None)
        department_id = material_data.get("useDepart", None)
        is_pre_purchase = material_data.get("isPurchase", None)
        material_second_type = material_data.get("materialDetailType", None)
        pre_craft_name = material_data.get("craftName", None)
        production_instruction_item = ProductionInstructionItem(
            production_instruction_id=input_production_instruction_id,
            material_id=material_id,
            material_model=material_model,
            material_specification=material_spec,
            color=material_color,
            remark=remark,
            department_id=department_id,
            is_pre_purchase=is_pre_purchase if is_pre_purchase else False,
            material_type=input_material_type,
            order_shoe_type_id=input_order_shoe_type_id,
            material_second_type=material_second_type,
            pre_craft_name=pre_craft_name,
            processing_remark=processing_remark,
        )
        db.session.add(production_instruction_item)


@dev_producion_order_bp.route(
    "/devproductionorder/saveproductioninstruction", methods=["POST"]
)
def save_production_instruction():
    order_id = request.json.get("orderId")
    order_shoe_rid = request.json.get("orderShoeId")
    production_instruction_rid = request.json.get("productionInstructionId")
    upload_data = request.json.get("uploadData")
    production_instruction_details = request.json.get("productionInstructionDetail")

    size_table = request.json.get("sizeTable", None)
    standard_size_dict = transform_grid_to_standard_size_dict(size_table)
    json_table = json.dumps(standard_size_dict, ensure_ascii=False)
    order = db.session.query(Order).filter(Order.order_rid == order_id).first()
    if order:
        order.order_size_table = json_table
        db.session.flush()

    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe, OrderShoeStatus)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .filter(OrderShoeStatus.current_status == 0)
        .first()
    )
    order_shoe_id = order_shoe.OrderShoe.order_shoe_id
    order_shoe_status = order_shoe.OrderShoeStatus
    order_shoe.Shoe.shoe_designer = production_instruction_details.get("designer", None)
    db.session.flush()
    production_instruction = ProductionInstruction(
        production_instruction_rid=production_instruction_rid,
        order_shoe_id=order_shoe_id,
        production_instruction_status="1",
        origin_size=production_instruction_details.get("originSize", None),
        size_range=production_instruction_details.get("sizeRange", None),
        last_type=production_instruction_details.get("lastType", None),
        size_difference=production_instruction_details.get("sizeDifference", None),
        burn_sole_craft=production_instruction_details.get("burnSoleCraft", None),
        craft_remark=production_instruction_details.get("craftRemark", None),
    )

    db.session.add(production_instruction)
    db.session.flush()
    production_instruction_id = production_instruction.production_instruction_id
    for data in upload_data:
        shoe_color = data.get("color")
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
        _save_instruction_helper(
            data.get("surfaceMaterialData", []),
            production_instruction_id,
            "S",
            order_shoe_type_id,
            0,
        )
        _save_instruction_helper(
            data.get("insideMaterialData", []),
            production_instruction_id,
            "I",
            order_shoe_type_id,
            0,
        )
        _save_instruction_helper(
            data.get("accessoryMaterialData", []),
            production_instruction_id,
            "A",
            order_shoe_type_id,
            0,
        )
        _save_instruction_helper(
            data.get("outsoleMaterialData", []),
            production_instruction_id,
            "O",
            order_shoe_type_id,
            1,
        )
        _save_instruction_helper(
            data.get("midsoleMaterialData", []),
            production_instruction_id,
            "M",
            order_shoe_type_id,
            1,
        )
        _save_instruction_helper(
            data.get("hotsoleMaterialData", []),
            production_instruction_id,
            "H",
            order_shoe_type_id,
        )
    order_shoe = (
        db.session.query(OrderShoe)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .first()
    )
    order_shoe.production_order_upload_status = "1"
    order_shoe_status.current_status_value = 1
    db.session.commit()

    return jsonify({"message": "Production order uploaded successfully"})


@dev_producion_order_bp.route(
    "/devproductionorder/getproductioninstruction", methods=["GET"]
)
def get_production_instruction():
    order_id = request.args.get("orderid")
    order_shoe_rid = request.args.get("ordershoeid")

    # Fetch order_shoe_id based on order_id and order_shoe_rid
    # Get the production instruction
    production_instruction = (
        db.session.query(ProductionInstruction)
        .join(OrderShoe, ProductionInstruction.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )

    if not production_instruction:
        return jsonify({"message": "No production instruction found"}), 404

    production_instruction_id = production_instruction.production_instruction_id
    production_instruction_rid = production_instruction.production_instruction_rid

    production_instruction_items = (
        db.session.query(ProductionInstructionItem)
        .filter(
            ProductionInstructionItem.production_instruction_id
            == production_instruction_id
        )
        .all()
    )

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
                "hotsoleMaterialData": [],
            }
        material = (
            db.session.query(Material, MaterialType, Supplier)
            .join(
                MaterialType, Material.material_type_id == MaterialType.material_type_id
            )
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(Material.material_id == item.material_id)
            .first()
        )
        # Map material type to the appropriate array in the dictionary
        material_data = {
            "productionInstructionItemId": item.production_instruction_item_id,
            "materialId": item.material_id,
            "materialType": material.MaterialType.material_type_name,
            "materialName": material.Material.material_name,
            "materialModel": item.material_model,
            "materialSpecification": item.material_specification,
            "craftName": item.pre_craft_name,
            "color": item.color,
            "unit": material.Material.material_unit,
            "supplierName": material.Supplier.supplier_name,
            "comment": item.remark,
            "useDepart": item.department_id,
            "isPurchase": item.is_pre_purchase,
            "materialDetailType": item.material_second_type,
            "processingRemark": item.processing_remark,
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
        elif item.material_type == "H":
            result_dict[color_name]["hotsoleMaterialData"].append(material_data)

    # Convert result dictionary to list for JSON response
    result = list(result_dict.values())
    production_instruction_detail = {
        "originSize": production_instruction.origin_size,
        "sizeRange": production_instruction.size_range,
        "lastType": production_instruction.last_type,
        "sizeDifference": production_instruction.size_difference,
        "burnSoleCraft": production_instruction.burn_sole_craft,
        "craftRemark": production_instruction.craft_remark,
    }
    fin_result = {
        "productionInstructionDbId": production_instruction_id,
        "productionInstructionId": production_instruction_rid,
        "instructionData": result,
        "productionInstructionDetail": production_instruction_detail,
    }

    return jsonify(fin_result)


@dev_producion_order_bp.route(
    "/devproductionorder/editproductioninstruction", methods=["POST"]
)
def edit_production_instruction():
    order_id = request.json.get("orderId")
    production_instruction_rid = request.json.get("productionInstructionId")
    order_shoe_rid = request.json.get("orderShoeId")
    upload_data = request.json.get("uploadData")
    production_instruction_details = request.json.get("productionInstructionDetail")

    size_table = request.json.get("sizeTable", None)
    standard_size_dict = transform_grid_to_standard_size_dict(size_table)
    json_table = json.dumps(standard_size_dict, ensure_ascii=False)
    order = db.session.query(Order).filter(Order.order_rid == order_id).first()
    if order:
        order.order_size_table = json_table
        db.session.flush()

    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )
    order_shoe_id = order_shoe.OrderShoe.order_shoe_id
    order_shoe.Shoe.shoe_designer = production_instruction_details.get("designer")
    db.session.flush()
    production_instruction = (
        db.session.query(ProductionInstruction)
        .filter(
            ProductionInstruction.production_instruction_rid
            == production_instruction_rid
        )
        .first()
    )
    production_instruction_id = production_instruction.production_instruction_id
    production_instruction.origin_size = production_instruction_details.get(
        "originSize"
    )
    production_instruction.size_range = production_instruction_details.get("sizeRange")
    production_instruction.last_type = production_instruction_details.get("lastType")
    production_instruction.size_difference = production_instruction_details.get(
        "sizeDifference"
    )
    production_instruction.burn_sole_craft = production_instruction_details.get(
        "burnSoleCraft"
    )
    production_instruction.craft_remark = production_instruction_details.get(
        "craftRemark"
    )
    db.session.flush()
    production_instruction_items = (
        db.session.query(ProductionInstructionItem)
        .filter(
            ProductionInstructionItem.production_instruction_id
            == production_instruction_id
        )
        .all()
    )
    for item in production_instruction_items:
        db.session.delete(item)
    for data in upload_data:
        shoe_color = data.get("color")
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
        _save_instruction_helper(
            data.get("surfaceMaterialData", []),
            production_instruction_id,
            "S",
            order_shoe_type_id,
            0,
        )
        _save_instruction_helper(
            data.get("insideMaterialData", []),
            production_instruction_id,
            "I",
            order_shoe_type_id,
            0,
        )
        _save_instruction_helper(
            data.get("accessoryMaterialData", []),
            production_instruction_id,
            "A",
            order_shoe_type_id,
            0,
        )
        _save_instruction_helper(
            data.get("outsoleMaterialData", []),
            production_instruction_id,
            "O",
            order_shoe_type_id,
            1,
        )
        _save_instruction_helper(
            data.get("midsoleMaterialData", []),
            production_instruction_id,
            "M",
            order_shoe_type_id,
            1,
        )
        _save_instruction_helper(
            data.get("hotsoleMaterialData", []),
            production_instruction_id,
            "H",
            order_shoe_type_id,
        )
    db.session.commit()
    return jsonify({"message": "Production instruction updated successfully"}), 200


@dev_producion_order_bp.route("/devproductionorder/upload", methods=["POST"])
def upload_production_order():
    order_shoe_rid = request.form.get("orderShoeRId")
    order_id = request.form.get("orderId")
    print(order_shoe_rid, order_id)
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 500
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 500
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid)
    if os.path.exists(folder_path) == False:
        os.mkdir(folder_path)
    file_path = os.path.join(folder_path, "投产指令单.xlsx")
    file.save(file_path)
    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )
    order_shoe.OrderShoe.production_order_upload_status = "1"
    db.session.commit()

    return jsonify({"message": "Production order uploaded successfully"})


@dev_producion_order_bp.route("/devproductionorder/download", methods=["GET"])
def download_production_order():
    order_shoe_rid = request.args.get("ordershoerid")
    order_id = request.args.get("orderid")
    print(order_shoe_rid)
    print(order_id)
    order_shoe = (
        db.session.query(Order, OrderShoe, Shoe)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(Order.order_rid == order_id, Shoe.shoe_rid == order_shoe_rid)
        .first()
    )
    if order_shoe.OrderShoe.production_order_upload_status == "0":
        return jsonify({"error": "Production order not uploaded yet"}), 500
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid)
    file_path = os.path.join(folder_path, "投产指令单.xlsx")
    new_name = order_id + "-" + order_shoe_rid + "_投产指令单.xlsx"
    return send_file(file_path, as_attachment=True, download_name=new_name)


@dev_producion_order_bp.route("/devproductionorder/issue", methods=["POST"])
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
        print(order_shoe.OrderShoe.production_order_upload_status)
        if order_shoe.OrderShoe.production_order_upload_status != "1":
            return jsonify({"error": "Production order not uploaded yet"}), 500
        order_shoe.OrderShoe.production_order_upload_status = "2"
        production_instruction = (
            db.session.query(ProductionInstruction)
            .filter(ProductionInstruction.order_shoe_id == order_shoe_id)
            .first()
        )
        production_instruction.production_instruction_status = "2"
        production_instruction_items = (
            db.session.query(ProductionInstructionItem)
            .filter(
                ProductionInstructionItem.production_instruction_id
                == production_instruction.production_instruction_id
            )
            .all()
        )
        order_shoe_types = (
            db.session.query(OrderShoeType)
            .filter(OrderShoeType.order_shoe_id == order_shoe_id)
            .all()
        )
        random_string = randomIdGenerater(6)
        current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
        craft_sheet_rid = current_time_stamp + random_string + "CS"
        craft_sheet = CraftSheet(
            craft_sheet_rid=craft_sheet_rid,
            order_shoe_id=order_shoe_id,
            craft_sheet_status="1",
        )
        db.session.add(craft_sheet)
        db.session.flush()
        for order_shoe_type in order_shoe_types:
            random_string = randomIdGenerater(6)
            order_shoe_type_id = order_shoe_type.order_shoe_type_id
            first_bom_rid = current_time_stamp + random_string + "F"
            second_bom_rid = current_time_stamp + random_string + "S"
            first_bom = Bom(
                order_shoe_type_id=order_shoe_type_id,
                bom_rid=first_bom_rid,
                bom_type=0,
                bom_status=3,
            )
            db.session.add(first_bom)
            db.session.flush()
            first_bom_id = first_bom.bom_id
            craft_sheet_id = craft_sheet.craft_sheet_id
            for item in production_instruction_items:
                if item.order_shoe_type_id == order_shoe_type.order_shoe_type_id:
                    first_bom_item = BomItem(
                        bom_id=first_bom_id,
                        material_id=item.material_id,
                        material_model=item.material_model,
                        material_specification=item.material_specification,
                        bom_item_color=item.color,
                        remark=item.remark,
                        department_id=item.department_id,
                        size_type="E",
                        bom_item_add_type="0",
                        total_usage=0,
                        material_second_type=item.material_second_type,
                        production_instruction_item_id=item.production_instruction_item_id,
                        craft_name=item.pre_craft_name,
                    )
                    db.session.add(first_bom_item)
                    craft_sheet_item = CraftSheetItem(
                        craft_sheet_id=craft_sheet_id,
                        material_id=item.material_id,
                        material_model=item.material_model,
                        material_specification=item.material_specification,
                        color=item.color,
                        remark=item.remark,
                        department_id=item.department_id,
                        pairs=0,
                        total_usage=0,
                        unit_usage=0,
                        material_type=item.material_type,
                        material_second_type=item.material_second_type,
                        order_shoe_type_id=item.order_shoe_type_id,
                        craft_name=item.pre_craft_name,
                        material_source="P",
                        after_usage_symbol=0,
                        production_instruction_item_id=item.production_instruction_item_id,
                    )
                    db.session.add(craft_sheet_item)
        db.session.flush()
        # create excel file
        insert_data = []
        transdict = {
            "S": "面料",
            "I": "里料",
            "A": "辅料",
            "O": "底材",
            "M": "中底",
            "L": "楦头",
            "H": "复合",
        }
        order_rid = order_rid
        order_shoe_rid = order_shoe_rid
        customer_shoe_name = order_shoe.OrderShoe.customer_product_name
        last_type = production_instruction.last_type
        size_range = production_instruction.size_range
        size_difference = production_instruction.size_difference
        origin_size = production_instruction.origin_size
        designer = order_shoe.Shoe.shoe_designer
        brand = (
            db.session.query(Customer)
            .filter(Customer.customer_id == order_shoe.Order.customer_id)
            .first()
            .customer_brand
        )
        colors = []
        for item in production_instruction_items:
            order_shoe_type_id = item.order_shoe_type_id
            shoe_color = (
                db.session.query(OrderShoeType, ShoeType, Color)
                .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
                .join(Color, ShoeType.color_id == Color.color_id)
                .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
                .first()
            )
            if shoe_color.Color.color_name not in colors:
                colors.append(shoe_color.Color.color_name)
            color_name = shoe_color.Color.color_name
            material_type = transdict[item.material_type]
            material_second_type = item.material_second_type
            material = (
                db.session.query(Material, Supplier)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .filter(Material.material_id == item.material_id)
                .first()
            )
            material_name = material.Material.material_name
            unit = material.Material.material_unit
            material_model = item.material_model
            material_specification = item.material_specification
            color = item.color
            remark = item.remark
            supplier_name = material.Supplier.supplier_name
            insert_data.append(
                {
                    "鞋型颜色": color_name,
                    "材料类型": material_type,
                    "材料二级类型": material_second_type,
                    "材料名称": material_name,
                    "单位": unit,
                    "材料型号": material_model,
                    "材料规格": material_specification,
                    "颜色": color,
                    "备注": remark,
                    "厂家名称": supplier_name,
                }
            )
        color_string = "、".join(colors)
        image_save_path = os.path.join(
            FILE_STORAGE_PATH, order_rid, order_shoe_rid, "shoe_image.jpg"
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
        generate_instruction_excel_file(
            os.path.join(FILE_STORAGE_PATH, "投产指令单模版.xlsx"),
            os.path.join(
                FILE_STORAGE_PATH, order_rid, order_shoe_rid, "投产指令单.xlsx"
            ),
            {
                "order_id": order_rid,
                "inherit_id": order_shoe_rid,
                "customer_id": customer_shoe_name,
                "last_type": last_type,
                "size_range": size_range,
                "size_difference": size_difference,
                "origin_size": origin_size,
                "designer": designer,
                "brand": brand,
                "colors": color_string,
            },
            insert_data,
            image_path,
            image_save_path,
        )
        event_arr = []
        processor: EventProcessor = current_app.config["event_processor"]
        try:
            for operation_id in [38, 39, 40, 41, 42, 43, 44, 45]:
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
            return jsonify({"error": "EVENT PROCESSOR FAILED"}), 500
        db.session.add_all(event_arr)
        db.session.flush()
    db.session.commit()
    return jsonify({"message": "Production order issued successfully"})


@dev_producion_order_bp.route("/devproductionorder/uploadpicnotes", methods=["POST"])
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


@dev_producion_order_bp.route(
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


@dev_producion_order_bp.route(
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


@dev_producion_order_bp.route(
    "/devproductionorder/getautocompeletedata", methods=["GET"]
)
def get_auto_complete_data():
    data = request.args
    material_name = data.get("materialName")
    material_model = data.get("materialModel", None)
    material_spec = data.get("materialSpecification", None)
    search_type = int(data.get("searchType"))
    material_supplier = data.get("materialSupplier", None)
    if search_type == 0:
        elements = (
            db.session.query(ProductionInstructionItem.material_model)
            .join(
                Material, ProductionInstructionItem.material_id == Material.material_id
            )
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                Material.material_name == material_name,
                ProductionInstructionItem.material_model.ilike(f"%{material_model}%"),
                Supplier.supplier_name == material_supplier,
            )
            .distinct()
            .all()
        )
        model_result = []
        for element in elements:
            model_result.append(element.material_model)
        return jsonify(model_result), 200
    elif search_type == 1:
        elements = (
            db.session.query(ProductionInstructionItem.material_specification)
            .join(
                Material, ProductionInstructionItem.material_id == Material.material_id
            )
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                Material.material_name == material_name,
                ProductionInstructionItem.material_model == material_model,
                ProductionInstructionItem.material_specification.ilike(
                    f"%{material_spec}%"
                ),
                Supplier.supplier_name == material_supplier,
            )
            .distinct()
            .all()
        )
        spec_result = []
        for element in elements:
            spec_result.append(element.material_specification)
        return jsonify(spec_result), 200
    else:
        return jsonify([]), 200


@dev_producion_order_bp.route("/devproductionorder/getpastshoeinfo", methods=["GET"])
def get_past_shoe_info():
    order_shoe_rid = request.args.get("ordershoeid")
    if order_shoe_rid.find("-") != -1:
        order_shoe_rid = order_shoe_rid.split("-")[0]
    similar_shoes = (
        db.session.query(Shoe, ShoeType, Color, OrderShoe)
        .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .join(OrderShoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(Shoe.shoe_rid.like(f"%{order_shoe_rid}%"))
        .all()
    )
    result_list = []
    shoe_list = []
    for shoe in similar_shoes:
        if shoe.Shoe.shoe_rid not in shoe_list:
            shoe_list.append(shoe.Shoe.shoe_rid)
            print(shoe_list)
            result_list.append(
                {
                    "inheritId": shoe.Shoe.shoe_rid,
                    "designer": shoe.Shoe.shoe_designer,
                    "shoeColors": [
                        {
                            "color": shoe.Color.color_name,
                            "shoeId": shoe.Shoe.shoe_rid,
                            "shoeTypeId": shoe.ShoeType.shoe_type_id,
                            "shoeImageUrl": shoe.ShoeType.shoe_image_url,
                        }
                    ],
                }
            )
        else:
            for item in result_list:
                if item["inheritId"] == shoe.Shoe.shoe_rid:
                    if {
                        "color": shoe.Color.color_name,
                        "shoeId": shoe.Shoe.shoe_rid,
                        "shoeTypeId": shoe.ShoeType.shoe_type_id,
                        "shoeImageUrl": shoe.ShoeType.shoe_image_url,
                    } not in item["shoeColors"]:
                        item["shoeColors"].append(
                            {
                                "color": shoe.Color.color_name,
                                "shoeId": shoe.Shoe.shoe_rid,
                                "shoeTypeId": shoe.ShoeType.shoe_type_id,
                                "shoeImageUrl": shoe.ShoeType.shoe_image_url,
                            }
                        )
                    break

    return jsonify(result_list), 200


@dev_producion_order_bp.route(
    "/devproductionorder/getpastmaterialdata", methods=["GET"]
)
def get_past_material_data():
    shoe_type_id = request.args.get("shoetypeid")
    production_instruction = db.session.query(OrderShoeType, OrderShoe, ProductionInstruction).join(
        OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id
    ).join(ProductionInstruction, OrderShoe.order_shoe_id == ProductionInstruction.order_shoe_id).filter(
        OrderShoeType.shoe_type_id == shoe_type_id
    ).first()
    if production_instruction is None:
        return jsonify({"message": "该鞋型无过往投产指令单"}), 404
    production_instruction_id = production_instruction.ProductionInstruction.production_instruction_id
    bom_items = (
        db.session.query(
            OrderShoeType,
            ShoeType,
            Bom,
            BomItem,
            ProductionInstructionItem,
            Material,
            MaterialType,
            Supplier,
        )
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .outerjoin(Bom, OrderShoeType.order_shoe_type_id == Bom.order_shoe_type_id)
        .outerjoin(BomItem, BomItem.bom_id == Bom.bom_id)
        .outerjoin(
            ProductionInstructionItem,
            BomItem.production_instruction_item_id
            == ProductionInstructionItem.production_instruction_item_id,
        )
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(ProductionInstructionItem.production_instruction_id == production_instruction_id)
        .filter(ShoeType.shoe_type_id == shoe_type_id)
        .filter(Bom.bom_type == 0)
        .all()
    )
    result_list = []
    for item in bom_items:
        result_list.append(
            {
                "materialType": item.MaterialType.material_type_name,
                "materialId": item.Material.material_id if item.Material else None,
                "materialName": item.Material.material_name if item.Material else None,
                "supplierName": item.Supplier.supplier_name if item.Supplier else None,
                "unit": item.Material.material_unit if item.Material else None,
                "materialModel": item.BomItem.material_model if item.BomItem else None,
                "materialSpecification": (
                    item.BomItem.material_specification if item.BomItem else None
                ),
                "color": item.BomItem.bom_item_color if item.BomItem else None,
                "comment": item.BomItem.remark if item.BomItem else None,
                "useDepart": item.BomItem.department_id if item.BomItem else None,
                "materialDetailType": (
                    item.BomItem.material_second_type if item.BomItem else None
                ),
                "craftName": (
                    item.ProductionInstructionItem.pre_craft_name
                    if item.ProductionInstructionItem
                    else None
                ),
            }
        )
    return jsonify(result_list), 200


@dev_producion_order_bp.route("/devproductionorder/getformatpastmaterialdata", methods=["GET"])
def get_format_past_material_data():
    shoe_type_id = request.args.get("shoeTypeId")
    order_shoe_id = db.session.query(OrderShoeType).filter(OrderShoeType.shoe_type_id == shoe_type_id).first().order_shoe_id
    production_instruction = db.session.query(OrderShoeType, OrderShoe, ProductionInstruction).join(
        OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id
    ).join(ProductionInstruction, OrderShoe.order_shoe_id == ProductionInstruction.order_shoe_id).filter(
        OrderShoeType.shoe_type_id == shoe_type_id
    ).first()
    if production_instruction is None:
        return jsonify({"message": "该鞋型无过往投产指令单"}), 404
    production_instruction_id = production_instruction.ProductionInstruction.production_instruction_id
    bom_items = (
        db.session.query(
            OrderShoe,
            OrderShoeType,
            ShoeType,
            Color,
            Bom,
            BomItem,
            ProductionInstructionItem,
            Material,
            MaterialType,
            Supplier,
        )
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .outerjoin(Bom, OrderShoeType.order_shoe_type_id == Bom.order_shoe_type_id)
        .outerjoin(BomItem, BomItem.bom_id == Bom.bom_id)
        .outerjoin(
            ProductionInstructionItem,
            BomItem.production_instruction_item_id == ProductionInstructionItem.production_instruction_item_id,
        )
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(ProductionInstructionItem.production_instruction_id == production_instruction_id)
        .filter(Bom.bom_type == 0)
        .all()
    )

    # Group materials by color name
    grouped_by_color = {}

    for item in bom_items:
        color_name = item.Color.color_name  # Group key
        if color_name not in grouped_by_color:
            grouped_by_color[color_name] = {
                "color": color_name,
                "surfaceMaterialData": [],
                "insideMaterialData": [],
                "accessoryMaterialData": [],
                "outsoleMaterialData": [],
                "midsoleMaterialData": [],
                "hotsoleMaterialData": [],
            }

        if item.ProductionInstructionItem is None:
            continue

        data = {
            "materialType": item.MaterialType.material_type_name,
            "materialId": item.Material.material_id if item.Material else None,
            "materialName": item.Material.material_name if item.Material else None,
            "supplierName": item.Supplier.supplier_name if item.Supplier else None,
            "unit": item.Material.material_unit if item.Material else None,
            "materialModel": item.BomItem.material_model if item.BomItem else None,
            "materialSpecification": item.BomItem.material_specification if item.BomItem else None,
            "color": item.BomItem.bom_item_color if item.BomItem else None,
            "comment": item.BomItem.remark if item.BomItem else None,
            "useDepart": item.BomItem.department_id if item.BomItem else None,
            "materialDetailType": item.BomItem.material_second_type if item.BomItem else None,
            "craftName": item.ProductionInstructionItem.pre_craft_name if item.ProductionInstructionItem else None,
            "processingRemark": item.ProductionInstructionItem.processing_remark if item.ProductionInstructionItem else None,
        }

        material_type = item.ProductionInstructionItem.material_type
        if material_type == "S":
            grouped_by_color[color_name]["surfaceMaterialData"].append(data)
        elif material_type == "I":
            grouped_by_color[color_name]["insideMaterialData"].append(data)
        elif material_type == "A":
            grouped_by_color[color_name]["accessoryMaterialData"].append(data)
        elif material_type == "O":
            grouped_by_color[color_name]["outsoleMaterialData"].append(data)
        elif material_type == "M":
            grouped_by_color[color_name]["midsoleMaterialData"].append(data)
        elif material_type == "H":
            grouped_by_color[color_name]["hotsoleMaterialData"].append(data)

    result = list(grouped_by_color.values())
    return jsonify(result), 200

@dev_producion_order_bp.route("/devproductionorder/getpastproductioninstructioninfo", methods=["GET"])
def get_past_production_instruction_info():
    shoe_type_id = request.args.get("shoeTypeId")
    order_shoe_id = db.session.query(OrderShoeType).filter(OrderShoeType.shoe_type_id == shoe_type_id).first().order_shoe_id
    designer = db.session.query(OrderShoe, Shoe).join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id).filter(OrderShoe.order_shoe_id == order_shoe_id).first().Shoe.shoe_designer
    production_instruction = (
        db.session.query(ProductionInstruction)
        .filter(ProductionInstruction.order_shoe_id == order_shoe_id)
        .first()
    )
    if production_instruction:
        return jsonify(
            {
                "originSize": production_instruction.origin_size,
                "sizeRange": production_instruction.size_range,
                "lastType": production_instruction.last_type,
                "sizeDifference": production_instruction.size_difference,
                "burnSoleCraft": production_instruction.burn_sole_craft,
                "craftRemark": production_instruction.craft_remark,
                "designer": designer,
            }
        ), 200
    return jsonify(
        {
            "originSize": "",
            "sizeRange": "",
            "lastType": "",
            "sizeDifference": "",
            "burnSoleCraft": "",
            "craftRemark": "",
            "designer": designer,
        }
    )
    


@dev_producion_order_bp.route(("/devproductionorder/getsizetable"), methods=["GET"])
def get_size_table():
    order_id = request.args.get("orderId")
    json_table = (
        db.session.query(Order).filter(Order.order_id == order_id).first()
    ).order_size_table
    if json_table == None:
        customer_size = (
            db.session.query(Order, BatchInfoType)
            .join(
                BatchInfoType,
                Order.batch_info_type_id == BatchInfoType.batch_info_type_id,
            )
            .filter(Order.order_id == order_id)
            .first()
        )
        customer_size_list = []
        if customer_size:
            order, batch_info = customer_size
            # Extract values from the BatchInfoType model
            for col in BatchInfoType.__table__.columns:
                size = getattr(batch_info, col.name)
                if size != "":
                    customer_size_list.append(getattr(batch_info, col.name))
        customer_size_list = customer_size_list[3:]
        standard_size_dict = {
            "客人码": customer_size_list,
            "大底": customer_size_list,
            "中底": customer_size_list,
            "楦头": customer_size_list,
            "备注": [""],
        }
        grid_options = transform_standard_size_dict_to_grid(standard_size_dict)
        order.order_size_table = json.dumps(standard_size_dict, ensure_ascii=False)
        db.session.commit()
        return jsonify(grid_options), 200
    else:
        table_dict = (
            json.loads(json_table) if isinstance(json_table, str) else json_table
        )
        grid_options = transform_standard_size_dict_to_grid(table_dict)
        return jsonify(grid_options), 200


@dev_producion_order_bp.route(
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


@dev_producion_order_bp.route("/devproductionorder/downloadpicnotes", methods=["GET"])
def download_pic_notes():
    order_shoe_rid = request.args.get("ordershoerid")
    order_id = request.args.get("orderid")
    folder_path = os.path.join(FILE_STORAGE_PATH, order_id, order_shoe_rid)
    file_path = os.path.join(folder_path, "投产指令单备注图片.jpg")
    new_name = order_id + "-" + order_shoe_rid + "_投产指令单备注图片.jpg"
    return send_file(file_path, as_attachment=True, download_name=new_name)


@dev_producion_order_bp.route("/devproductionorder/getmaterialdetail", methods=["GET"])
def get_material_detail():
    material_name = request.args.get("materialName")
    material = (
        db.session.query(Material, MaterialType)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .filter(Material.material_name == material_name)
        .first()
    )
    if material:
        return jsonify(
            {
                "materialId": material.Material.material_id,
                "unit": material.Material.material_unit,
                "materialType": material.MaterialType.material_type_name,
                "materialCategory": material.Material.material_category
            }
        )
    else:
        return jsonify({}), 200


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
            { "row": 4, "col": 1, "rowspan": 1, "colspan": max_len },
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

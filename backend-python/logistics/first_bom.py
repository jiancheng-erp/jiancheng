from flask import Blueprint, jsonify, request, send_file
from sqlalchemy.dialects.mysql import insert
import datetime
from app_config import db
from models import *
from api_utility import randomIdGenerater
from event_processor import EventProcessor
from file_locations import IMAGE_STORAGE_PATH, FILE_STORAGE_PATH, IMAGE_UPLOAD_PATH
import os
from logger import logger

first_bom_bp = Blueprint("first_bom_bp", __name__)


@first_bom_bp.route("/firstbom/getnewbomid", methods=["GET"])
def get_new_bom_id():
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    bom_id = current_time_stamp + random_string + "F"
    return jsonify({"bomId": bom_id})


@first_bom_bp.route("/firstbom/getordershoes", methods=["GET"])
def get_order_first_bom():
    order_id = request.args.get("orderid")

    # Querying the necessary data with joins and filters
    entities = (
        db.session.query(
            Order, OrderShoe, OrderShoeType, Shoe, ShoeType, Color, Bom, TotalBom, PurchaseOrder
        )
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .outerjoin(
            Bom, OrderShoeType.order_shoe_type_id == Bom.order_shoe_type_id
        )  # Assuming BOM is optional
        .outerjoin(
            TotalBom, Bom.total_bom_id == TotalBom.total_bom_id
        )  # Assuming TotalBom is optional
        .outerjoin(
            PurchaseOrder, PurchaseOrder.bom_id == TotalBom.total_bom_id
        ).filter(
            Order.order_id == order_id
        )
        .all()
    )

    logger.debug(entities)

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
                "colorSet": set(),  # Initialize a set to track colors for each shoe
            }

        if color.color_name not in result_dict[shoe.shoe_rid]["colorSet"]:
            # Only link BOM information to the color associated with the correct OrderShoeType
            first_bom_id = None
            first_bom_status = None
            first_purchase_order_id = None
            first_purchase_order_status = None
            second_bom_id = None
            second_bom_status = None
            second_purchase_order_id = None
            second_purchase_order_status = None

            # Only attach BOM and PurchaseOrder if it's associated with the correct OrderShoeType
            if bom and bom.bom_type == 0:
                first_bom_id = bom.bom_rid
                if bom.bom_status == "1":
                    first_bom_status = "已保存"
                elif bom.bom_status == "2":
                    first_bom_status = "已提交"
                elif bom.bom_status == "3":
                    first_bom_status = "已下发"

            # Similarly, attach PurchaseOrder if applicable
            if purchase_order and purchase_order.purchase_order_type == "F":
                first_purchase_order_id = purchase_order.purchase_order_rid
                if purchase_order.purchase_order_status == "1":
                    first_purchase_order_status = "已保存"
                elif purchase_order.purchase_order_status == "2":
                    first_purchase_order_status = "已提交"
                elif purchase_order.purchase_order_status == "3":
                    first_purchase_order_status = "已下发"

            # Same logic for second BOM and PurchaseOrder
            if bom and bom.bom_type != 0:
                second_bom_id = bom.bom_rid
                if bom.bom_status == "1":
                    second_bom_status = "已保存"
                elif bom.bom_status == "2":
                    second_bom_status = "已提交"
                elif bom.bom_status == "3":
                    second_bom_status = "已下发"

            if purchase_order and purchase_order.purchase_order_type == "S":
                second_purchase_order_id = purchase_order.purchase_order_rid
                if purchase_order.purchase_order_status == "1":
                    second_purchase_order_status = "已保存"
                elif purchase_order.purchase_order_status == "2":
                    second_purchase_order_status = "已提交"
                elif purchase_order.purchase_order_status == "3":
                    second_purchase_order_status = "已下发"

            # Append the correct BOM and PurchaseOrder data to typeInfos
            result_dict[shoe.shoe_rid]["typeInfos"].append(
                {
                    "orderShoeRid": shoe.shoe_rid,
                    "color": color.color_name,
                    "image": (
                        IMAGE_STORAGE_PATH + shoe_type.shoe_image_url
                        if shoe_type.shoe_image_url
                        else None
                    ),
                    "firstBomId": first_bom_id if first_bom_id else "未填写",
                    "firstBomStatus": first_bom_status if first_bom_id else "未填写",
                    "firstPurchaseOrderId": (
                        first_purchase_order_id if first_purchase_order_id else "未填写"
                    ),
                    "firstPurchaseOrderStatus": (
                        first_purchase_order_status
                        if first_purchase_order_id
                        else "未填写"
                    ),
                    "secondBomId": second_bom_id if second_bom_id else "未填写",
                    "secondBomStatus": second_bom_status if second_bom_id else "未填写",
                    "secondPurchaseOrderId": (
                        second_purchase_order_id
                        if second_purchase_order_id
                        else "未填写"
                    ),
                    "secondPurchaseOrderStatus": (
                        second_purchase_order_status
                        if second_purchase_order_id
                        else "未填写"
                    ),
                }
            )

            # Add the color to the colorSet to prevent future duplicates
            result_dict[shoe.shoe_rid]["colorSet"].add(color.color_name)

    # Remove the colorSet before returning the result
    for shoe_rid in result_dict:
        result_dict[shoe_rid].pop("colorSet")

    # Convert result_dict to a list of values
    result = list(result_dict.values())

    return jsonify(result)


@first_bom_bp.route("/firstbom/savebom", methods=["POST"])
def save_bom():
    bom_rid = request.json.get("bomId")
    order_id = request.json.get("orderId")
    order_shoe_rid = request.json.get("orderShoeId")
    bom_data = request.json.get("bomData")
    color = request.json.get("color")
    logger.debug(order_id, order_shoe_rid, bom_data, color)
    order_shoe_type_id = (
        db.session.query(Order, OrderShoe, Shoe, ShoeType, OrderShoeType, Color)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(
            Order.order_rid == order_id,
            Shoe.shoe_rid == order_shoe_rid,
        )
        .filter(Color.color_name == color)
        .first()
        .OrderShoeType.order_shoe_type_id
    )
    logger.debug(order_shoe_type_id)

    bom = Bom(
        bom_rid=bom_rid, order_shoe_type_id=order_shoe_type_id, bom_status=1, bom_type=0
    )
    db.session.add(bom)
    db.session.commit()
    bom_id = db.session.query(Bom).filter(Bom.bom_rid == bom_rid).first().bom_id
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
        bom_item = BomItem(
            bom_id=bom_id,
            material_id=material_id,
            total_usage=0,
            department_id=item["useDepart"] if "useDepart" in item else None,
            remark=item["comment"] if "comment" in item else None,
            material_model=item["materialModel"] if "materialModel" in item else None,
            material_specification=(
                item["materialSpecification"]
                if "materialSpecification" in item
                else None
            ),
            bom_item_add_type=0,
            bom_item_color=item["color"] if "color" in item else None,
        )
        db.session.add(bom_item)
    db.session.commit()

    return jsonify({"status": "success"})


@first_bom_bp.route("/firstbom/getbomdetails", methods=["GET"])
def get_bom_details():
    order_id = request.args.get("orderid")
    order_shoe_id = request.args.get("ordershoeid")
    color = request.args.get("color")
    logger.debug(order_id, order_shoe_id, color)
    order_shoe_type_id = (
        db.session.query(Order, OrderShoe, Shoe, ShoeType, OrderShoeType, Color)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(
            Order.order_rid == order_id,
            Shoe.shoe_rid == order_shoe_id,
        )
        .filter(Color.color_name == color)
        .first()
        .OrderShoeType.order_shoe_type_id
    )
    logger.debug(order_shoe_type_id)
    bom_id = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 0)
        .first()
        .bom_id
    )
    logger.debug(bom_id)
    bom_rid = db.session.query(Bom).filter(Bom.bom_id == bom_id).first().bom_rid
    bom_items = (
        db.session.query(BomItem, Bom, Material, MaterialType, Department, Supplier)
        .join(Bom, BomItem.bom_id == Bom.bom_id)
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Department, BomItem.department_id == Department.department_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(BomItem.bom_id == bom_id, Bom.bom_type == 0)
        .all()
    )
    result = []
    for bom_item in bom_items:
        item, bom, material, material_type, department, supplier = bom_item
        result.append(
            {
                "materialName": material.material_name,
                "materialType": material_type.material_type_name,
                "materialModel": item.material_model,
                "materialSpecification": item.material_specification,
                "supplierName": supplier.supplier_name,
                "useDepart": department.department_id,
                "unit": material.material_unit,
                "color": item.bom_item_color,
                "comment": item.remark,
            }
        )
    fin_result = {"bomId": bom_rid, "bomData": result}
    return jsonify(fin_result)


@first_bom_bp.route("/firstbom/editbom", methods=["POST"])
def edit_bom():
    bom_rid = request.json.get("bomId")
    order_id = request.json.get("orderId")
    order_shoe_rid = request.json.get("orderShoeId")
    color = request.json.get("color")
    bom_data = request.json.get("bomData")
    logger.debug(order_id, order_shoe_rid, bom_data)
    order_shoe_type_id = (
        db.session.query(Order, OrderShoe, Shoe, ShoeType, OrderShoeType, Color)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(
            Order.order_rid == order_id,
            Shoe.shoe_rid == order_shoe_rid,
        )
        .filter(Color.color_name == color)
        .first()
        .OrderShoeType.order_shoe_type_id
    )
    bom_id = Bom.query.filter(Bom.bom_rid == bom_rid).first().bom_id
    db.session.query(BomItem).filter(BomItem.bom_id == bom_id).delete()
    db.session.commit()

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
        bom_item = BomItem(
            bom_id=bom_id,
            material_id=material_id,
            total_usage=0,
            department_id=item["useDepart"] if "useDepart" in item else None,
            remark=item["comment"] if "comment" in item else None,
            material_model=item["materialModel"] if "materialModel" in item else None,
            material_specification=(
                item["materialSpecification"]
                if "materialSpecification" in item
                else None
            ),
            bom_item_add_type=0,
            bom_item_color=item["color"] if "color" in item else None,
        )
        db.session.add(bom_item)
    db.session.commit()

    return jsonify({"status": "success"})


@first_bom_bp.route("/firstbom/submitbom", methods=["POST"])
def submit_bom():
    order_shoe_rid = request.json.get("orderShoeId")
    order_rid = request.json.get("orderId")
    color = request.json.get("color")
    order_shoe_type_id = (
        db.session.query(Order, OrderShoe, Shoe, ShoeType, OrderShoeType, Color)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(
            Order.order_rid == order_rid,
            Shoe.shoe_rid == order_shoe_rid,
        )
        .filter(Color.color_name == color)
        .first()
        .OrderShoeType.order_shoe_type_id
    )
    bom = (
        db.session.query(Bom)
        .filter(Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 0)
        .first()
    )
    bom.bom_status = 2
    db.session.commit()

    return jsonify({"status": "success"})


@first_bom_bp.route("/firstbom/issueboms", methods=["POST"])
def issue_boms():
    order_rid = request.json.get("orderId")
    order_shoe_rids = request.json.get("orderShoeIds")
    colors = request.json.get("colors")
    logger.debug(order_rid, order_shoe_rids, colors)
    order_id = (
        db.session.query(Order).filter(Order.order_rid == order_rid).first().order_id
    )
    for order_shoe_rid in order_shoe_rids:
        index = order_shoe_rids.index(order_shoe_rid)
        color = colors[index]
        for color_item in color:
            order_shoe_type_id = (
                db.session.query(Order, OrderShoe, Shoe, ShoeType, OrderShoeType, Color)
                .join(OrderShoe, Order.order_id == OrderShoe.order_id)
                .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
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
                .filter(
                    Bom.order_shoe_type_id == order_shoe_type_id, Bom.bom_type == 0
                )
                .first()
            )
            bom.bom_status = 3
            db.session.commit()
        order_shoe_id = (
            db.session.query(OrderShoe, Shoe)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(OrderShoe.order_id == order_id, Shoe.shoe_rid == order_shoe_rid)
            .first()
            .OrderShoe.order_shoe_id
        )
        processor = EventProcessor()
        event = Event(
            staff_id=1,
            handle_time=datetime.datetime.now(),
            operation_id=42,
            event_order_id=order_id,
            event_order_shoe_id=order_shoe_id,
        )
        result = processor.processEvent(event)
        if not result:
            return jsonify({"message": "failed"}), 400
        db.session.add(event)
        db.session.commit()
        processor = EventProcessor()
        event = Event(
            staff_id=1,
            handle_time=datetime.datetime.now(),
            operation_id=43,
            event_order_id=order_id,
            event_order_shoe_id=order_shoe_id,
        )
        result = processor.processEvent(event)
        if not result:
            return jsonify({"message": "failed"}), 400
        db.session.add(event)
        db.session.commit()
        processor = EventProcessor()
        event = Event(
            staff_id=1,
            handle_time=datetime.datetime.now(),
            operation_id=44,
            event_order_id=order_id,
            event_order_shoe_id=order_shoe_id,
        )
        result = processor.processEvent(event)
        if not result:
            return jsonify({"message": "failed"}), 400
        db.session.add(event)
        db.session.commit()
        processor = EventProcessor()
        event = Event(
            staff_id=1,
            handle_time=datetime.datetime.now(),
            operation_id=45,
            event_order_id=order_id,
            event_order_shoe_id=order_shoe_id,
        )
        result = processor.processEvent(event)
        if not result:
            return jsonify({"message": "failed"}), 400
        db.session.add(event)
        db.session.commit()
    return jsonify({"status": "success"})


@first_bom_bp.route("/firstbom/download", methods=["GET"])
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
    file_path = os.path.join(folder_path, "firstbom", "一次BOM表.xlsx")
    new_name = order_id + "-" + order_shoe_rid + "_一次BOM表.xlsx"
    return send_file(file_path, as_attachment=True, download_name=new_name)

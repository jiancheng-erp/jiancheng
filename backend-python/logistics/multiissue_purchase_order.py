from flask import Blueprint, jsonify, request
import datetime
from app_config import app, db
from models import *
from constants import SHOESIZERANGE
from api_utility import randomIdGenerater
from decimal import Decimal
import os
from general_document.purchase_divide_order import generate_excel_file
from general_document.size_purchase_divide_order import generate_size_excel_file
from constants import SHOESIZERANGE
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH


multiissue_purchase_order_bp = Blueprint("multiissue_purchase_order", __name__)


@multiissue_purchase_order_bp.route(
    "/multiissue/getalltotalpurchaseorder", methods=["GET"]
)
def get_all_total_purchase_order():
    """Get all total purchase orders with their associated divide orders and purchase orders."""
    total_purchase_orders = (
        db.session.query(
            TotalPurchaseOrder,
            Supplier,
            PurchaseDivideOrder,
            PurchaseOrder,
            Order,
            Customer,
            OrderShoe,
            Shoe,
        )
        .join(Supplier, TotalPurchaseOrder.supplier_id == Supplier.supplier_id)
        .join(
            PurchaseDivideOrder,
            TotalPurchaseOrder.total_purchase_order_id
            == PurchaseDivideOrder.total_purchase_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(
            Order,
            PurchaseOrder.order_id == Order.order_id,
        )
        .join(
            Customer,
            Order.customer_id == Customer.customer_id,
        )
        .join(
            OrderShoe,
            Order.order_id == OrderShoe.order_id,
        )
        .join(
            Shoe,
            OrderShoe.shoe_id == Shoe.shoe_id,
        )
        .all()
    )

    # Temporary storage to group divide orders under their respective total purchase order
    order_map = {}

    for tpo, supplier, pdo, po, order, customer, os, shoe in total_purchase_orders:
        if tpo.total_purchase_order_id not in order_map:
            order_map[tpo.total_purchase_order_id] = {
                "totalPurchaseOrderId": tpo.total_purchase_order_id,
                "totalPurchaseOrderRid": tpo.total_purchase_order_rid,
                "totalPurchaseOrderStatus": tpo.total_purchase_order_status,
                "supplierId": supplier.supplier_id,
                "supplierName": supplier.supplier_name,
                "purchaseDivideOrders": [],
            }

        # Append divide order details to the respective total purchase order
        order_map[tpo.total_purchase_order_id]["purchaseDivideOrders"].append(
            {
                "purchaseDivideOrderId": pdo.purchase_divide_order_rid,
                "orderId": order.order_id,
                "orderRid": order.order_rid,
                "shoeRid": shoe.shoe_rid,
                "customerName": customer.customer_name,
            }
        )

    # Convert the map to a list of results
    result = list(order_map.values())
    return result


@multiissue_purchase_order_bp.route(
    "/multiissue/getallpurchasedivideorder", methods=["GET"]
)
def get_all_purchase_divide_order():
    """Get all purchase divide orders."""
    purchase_divide_orders = (
        db.session.query(
            PurchaseDivideOrder, PurchaseOrder, Order, Customer, OrderShoe, Shoe
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(
            Order,
            PurchaseOrder.order_id == Order.order_id,
        )
        .join(
            Customer,
            Order.customer_id == Customer.customer_id,
        )
        .join(
            OrderShoe,
            Order.order_id == OrderShoe.order_id,
        )
        .join(
            Shoe,
            OrderShoe.shoe_id == Shoe.shoe_id,
        )
        .filter(PurchaseOrder.purchase_order_status == 1)
        .filter(PurchaseDivideOrder.total_purchase_order_id == None)
        .all()
    )
    print(purchase_divide_orders)
    result = []
    for pdo, po, order, customer, os, shoe in purchase_divide_orders:
        supplier_id = int(pdo.purchase_divide_order_rid[-4:])
        supplier_name = (
            db.session.query(Supplier)
            .filter(Supplier.supplier_id == supplier_id)
            .first()
            .supplier_name
        )
        result.append(
            {
                "purchaseDivideOrderId": pdo.purchase_divide_order_rid,
                "orderId": order.order_id,
                "orderRid": order.order_rid,
                "shoeRid": shoe.shoe_rid,
                "customerName": customer.customer_name,
                "supplierId": supplier_id,
                "supplierName": supplier_name,
            }
        )

    return jsonify(result)


@multiissue_purchase_order_bp.route(
    "/multiissue/getsinglepurchasedivideorder", methods=["GET"]
)
def get_single_purchase_divide_order():
    """Get a single purchase divide order."""
    purchase_divide_order_id = request.args.get("purchaseDivideOrderId")
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
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(
            PurchaseOrderItem,
            PurchaseDivideOrder.purchase_divide_order_id
            == PurchaseOrderItem.purchase_divide_order_id,
        )
        .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(
            PurchaseDivideOrder.purchase_divide_order_rid == purchase_divide_order_id
        )
        .all()
    )
    grouped_results = {}
    for (
        purchase_divide_order,
        purchase_order,
        purchase_order_item,
        bom_item,
        material,
        material_type,
        supplier,
    ) in query:
        divide_order_rid = purchase_divide_order.purchase_divide_order_rid
        if divide_order_rid not in grouped_results:
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
            }

        # Append the assets item details to the corresponding group
        obj = {
            "materialId": bom_item.material_id,
            "materialTypeId": material_type.material_type_id,
            "materialType": material_type.material_type_name,
            "materialName": material.material_name,
            "materialModel": bom_item.material_model,
            "materialSpecification": bom_item.material_specification,
            "color": bom_item.bom_item_color,
            "unit": material.material_unit,
            "purchaseAmount": purchase_order_item.purchase_amount,
            "approvalAmount": purchase_order_item.approval_amount,
            "remark": bom_item.remark,
            "sizeType": bom_item.size_type,
        }
        for size in SHOESIZERANGE:
            obj[f"size{size}Amount"] = getattr(
                purchase_order_item, f"size_{size}_purchase_amount"
            )
        grouped_results[divide_order_rid]["assetsItems"].append(obj)

    # Convert the grouped results to a list
    result = list(grouped_results.values())
    return jsonify(result)


@multiissue_purchase_order_bp.route(
    "/multiissue/createtotalpurchaseorder", methods=["POST"]
)
def create_total_purchase_order():
    """Create a total purchase order."""
    data = request.json
    print(data)
    supplier_id = data["purchaseDivideOrders"][0]["supplierId"]
    purchase_divide_orders = data["purchaseDivideOrders"]
    current_time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-5]
    random_string = randomIdGenerater(6)
    supplier_id_string = str(supplier_id).zfill(4)
    total_purchase_order_rid = (
        "T" + current_time_stamp + random_string + "F" + supplier_id_string
    )
    total_purchase_order = TotalPurchaseOrder(
        total_purchase_order_rid=total_purchase_order_rid,
        supplier_id=supplier_id,
        create_date=datetime.datetime.now(),
        total_purchase_order_remark="",
        total_purchase_order_environmental_request="",
        shipment_address="温州市瓯海区梧田工业基地镇南路8号（健诚集团）",
        shipment_deadline="请在7-10日内交货",
        total_purchase_order_status="1",
    )
    db.session.add(total_purchase_order)
    db.session.flush()
    total_purchase_order_id = total_purchase_order.total_purchase_order_id

    # Update the purchase divide orders with the total purchase order id
    for purchase_divide_order in purchase_divide_orders:
        purchase_divide_order_id = purchase_divide_order["purchaseDivideOrderId"]
        db.session.query(PurchaseDivideOrder).filter(
            PurchaseDivideOrder.purchase_divide_order_rid == purchase_divide_order_id
        ).update({"total_purchase_order_id": total_purchase_order_id})

    db.session.commit()
    return jsonify({"totalPurchaseOrderId": total_purchase_order_id})


@multiissue_purchase_order_bp.route(
    "/multiissue/getsingletotalpurchaseorder", methods=["GET"]
)
def get_single_total_purchase_order():
    """Get a single total purchase order with aggregated materials."""
    total_purchase_order_id = request.args.get("totalPurchaseOrderId")

    # Query to join related tables and fetch all required details
    query = (
        db.session.query(
            TotalPurchaseOrder,
            PurchaseDivideOrder,
            PurchaseOrder,
            PurchaseOrderItem,
            BomItem,
            Material,
            MaterialType,
            Supplier,
        )
        .join(
            PurchaseDivideOrder,
            TotalPurchaseOrder.total_purchase_order_id
            == PurchaseDivideOrder.total_purchase_order_id,
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
        .join(Material, BomItem.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(TotalPurchaseOrder.total_purchase_order_id == total_purchase_order_id)
        .all()
    )

    # Initialize result structure
    grouped_results = {
        "totalPurchaseOrderId": total_purchase_order_id,
        "totalPurchaseOrderRid": None,
        "remark": None,
        "supplierName": None,
        "shipmentAddress": None,
        "shipmentDeadline": None,
        "environmentalRequest": None,
        "assetsItems": [],
        "totalPurchaseOrderType": None,
    }
    material_map = {}

    for (
        total_purchase_order,
        purchase_divide_order,
        purchase_order,
        purchase_order_item,
        bom_item,
        material,
        material_type,
        supplier,
    ) in query:
        # Set supplier name for the total purchase order
        if not grouped_results["totalPurchaseOrderRid"]:
            grouped_results["totalPurchaseOrderRid"] = (
                total_purchase_order.total_purchase_order_rid
            )
        if not grouped_results["supplierName"]:
            grouped_results["supplierName"] = supplier.supplier_name
        if not grouped_results["remark"]:
            grouped_results["remark"] = total_purchase_order.total_purchase_order_remark
        if not grouped_results["shipmentAddress"]:
            grouped_results["shipmentAddress"] = total_purchase_order.shipment_address
        if not grouped_results["shipmentDeadline"]:
            grouped_results["shipmentDeadline"] = total_purchase_order.shipment_deadline
        if not grouped_results["environmentalRequest"]:
            grouped_results["environmentalRequest"] = (
                total_purchase_order.total_purchase_order_environmental_request
            )
        if not grouped_results["totalPurchaseOrderType"]:
            grouped_results["totalPurchaseOrderType"] = (
                purchase_divide_order.purchase_divide_order_type
            )
        # Create a unique key for the material based on its attributes
        material_key = (
            bom_item.material_id,
            material_type.material_type_name,
            material.material_name,
            bom_item.material_model,
            bom_item.material_specification,
            bom_item.bom_item_color,
        )

        # Check if the material already exists in the material map
        if material_key not in material_map:
            material_map[material_key] = {
                "materialId": bom_item.material_id,
                "materialTypeId": material_type.material_type_id,
                "materialType": material_type.material_type_name,
                "materialName": material.material_name,
                "materialModel": bom_item.material_model,
                "materialSpecification": bom_item.material_specification,
                "color": bom_item.bom_item_color,
                "unit": material.material_unit,
                "purchaseAmount": 0,
                "approvalAmount": 0,
                "adjustPurchaseAmount": 0,
                "isInboundSperate": (
                    True if purchase_order_item.inbound_material_id else False
                ),
                "remark": bom_item.remark,
                "sizeType": bom_item.size_type,
                "materialInboundId": purchase_order_item.inbound_material_id,
                "materialInboundUnit": purchase_order_item.inbound_unit,
                "materialInboundName": (
                    db.session.query(Material)
                    .filter(
                        Material.material_id == purchase_order_item.inbound_material_id
                    )
                    .first()
                    .material_name
                    if purchase_order_item.inbound_material_id
                    else None
                ),
                **{f"size{size}Amount": 0 for size in SHOESIZERANGE},
            }

        # Update the purchase amount and size-specific amounts
        current_material = material_map[material_key]
        current_material["purchaseAmount"] += purchase_order_item.purchase_amount
        current_material["approvalAmount"] += purchase_order_item.approval_amount
        current_material[
            "adjustPurchaseAmount"
        ] += purchase_order_item.adjust_purchase_amount
        for size in SHOESIZERANGE:
            current_material[f"size{size}Amount"] += (
                getattr(purchase_order_item, f"size_{size}_purchase_amount", 0)
                if getattr(purchase_order_item, f"size_{size}_purchase_amount", 0)
                else 0
            )

    # Convert materials map to a list
    grouped_results["assetsItems"] = list(material_map.values())

    return jsonify([grouped_results])


@multiissue_purchase_order_bp.route(
    "/multiissue/savetotalpurchaseorder", methods=["POST"]
)
def save_total_purchase_order():
    """Save a total purchase order with material details."""
    data = request.json.get("totalPurchaseOrders")

    for order_data in data:
        # Update total purchase order details
        total_purchase_order_id = order_data["totalPurchaseOrderId"]
        total_purchase_order = (
            db.session.query(TotalPurchaseOrder)
            .filter(
                TotalPurchaseOrder.total_purchase_order_id == total_purchase_order_id
            )
            .first()
        )
        if total_purchase_order:
            total_purchase_order.total_purchase_order_remark = order_data["remark"]
            total_purchase_order.total_purchase_order_environmental_request = (
                order_data["environmentalRequest"]
            )
            total_purchase_order.shipment_address = order_data["shipmentAddress"]
            total_purchase_order.shipment_deadline = order_data["shipmentDeadline"]

        for material in order_data["assetsItems"]:
            purchase_items = (
                db.session.query(
                    PurchaseOrderItem, BomItem, PurchaseDivideOrder, TotalPurchaseOrder
                )
                .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
                .join(
                    PurchaseDivideOrder,
                    PurchaseOrderItem.purchase_divide_order_id
                    == PurchaseDivideOrder.purchase_divide_order_id,
                )
                .join(
                    TotalPurchaseOrder,
                    PurchaseDivideOrder.total_purchase_order_id
                    == TotalPurchaseOrder.total_purchase_order_id,
                )
                .filter(
                    TotalPurchaseOrder.total_purchase_order_id
                    == total_purchase_order_id,
                    BomItem.material_id == material["materialId"],
                    BomItem.material_model == material["materialModel"],
                    BomItem.material_specification == material["materialSpecification"],
                    BomItem.bom_item_color == material["color"],
                )
                .all()
            )
            if purchase_items:
                # 例：买两包拉链，分给两个订单，每个订单一包
                distributed_amount = float(material["adjustPurchaseAmount"]) / len(
                    purchase_items
                )
                for (
                    item,
                    bom_item,
                    purchase_divide_order,
                    total_purchase_order,
                ) in purchase_items:
                    item.adjust_purchase_amount = distributed_amount
                    if material["isInboundSperate"]:
                        if material["materialInboundId"]:
                            item.inbound_material_id = material["materialInboundId"]
                            item.inbound_unit = material["materialInboundUnit"]
                        else:
                            return jsonify({"message": "Material ID is required."})
                    else:
                        item.inbound_material_id = material["materialId"]
                        item.inbound_unit = material["materialUnit"]

    db.session.commit()
    return jsonify(
        {"message": "Total purchase order and materials saved successfully."}
    )


@multiissue_purchase_order_bp.route(
    "/multiissue/submittotalpurchaseorder", methods=["POST"]
)
def submit_total_purchase_order():
    """Submit a total purchase order."""
    total_purchase_order_id = request.json.get("totalPurchaseOrderId")
    total_purchase_order = (
        db.session.query(TotalPurchaseOrder)
        .filter(TotalPurchaseOrder.total_purchase_order_id == total_purchase_order_id)
        .first()
    )
    total_purchase_order.total_purchase_order_status = "2"
    purchase_order_items = (
        db.session.query(
            PurchaseOrderItem,
            BomItem,
            Bom,
            TotalBom,
            PurchaseDivideOrder,
            TotalPurchaseOrder,
            PurchaseOrder,
            Material,
            MaterialType,
            Supplier,
        )
        .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .join(Bom, BomItem.bom_id == Bom.bom_id)
        .join(TotalBom, Bom.total_bom_id == TotalBom.total_bom_id)
        .join(
            PurchaseDivideOrder,
            PurchaseOrderItem.purchase_divide_order_id
            == PurchaseDivideOrder.purchase_divide_order_id,
        )
        .join(
            TotalPurchaseOrder,
            PurchaseDivideOrder.total_purchase_order_id
            == TotalPurchaseOrder.total_purchase_order_id,
        )
        .join(
            PurchaseOrder,
            PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
        )
        .join(
            Material,
            BomItem.material_id == Material.material_id,
        )
        .join(
            MaterialType,
            Material.material_type_id == MaterialType.material_type_id,
        )
        .join(
            Supplier,
            Material.material_supplier == Supplier.supplier_id,
        )
        .filter(TotalPurchaseOrder.total_purchase_order_id == total_purchase_order_id)
        .all()
    )
    # Dictionary to track existing materials by their unique identifiers
    material_storage_map = {}

    for (
        purchase_order_item,
        bom_item,
        bom,
        total_bom,
        purchase_divide_order,
        total_purchase_order,
        purchase_order,
        material,
        material_type,
        supplier,
    ) in purchase_order_items:
        order_shoe_id = purchase_order.order_shoe_id
        material_id = bom_item.material_id
        material_model = bom_item.material_model
        material_specification = bom_item.material_specification
        material_color = bom_item.bom_item_color
        material_quantity = purchase_order_item.purchase_amount
        actual_purchase_amount = purchase_order_item.adjust_purchase_amount
        total_bom_id = bom.total_bom_id
        actual_inbound_material_id = purchase_order_item.inbound_material_id
        actual_inbound_unit = purchase_order_item.inbound_unit
        batch_info_type_name = (
            db.session.query(BatchInfoType, Order)
            .join(Order, Order.batch_info_type_id == BatchInfoType.batch_info_type_id)
            .filter(Order.order_id == purchase_order.order_id)
            .first()
            .BatchInfoType.batch_info_type_name
        )

        # Create a unique key for the material
        material_key = (
            total_purchase_order.total_purchase_order_id,
            order_shoe_id,
            material_id,
            material_model,
            material_specification,
            material_color,
        )

        # Build the craft name list from the same material
        new_craft_name_list = []
        same_materials = (
            db.session.query(BomItem, Bom)
            .join(Bom, BomItem.bom_id == Bom.bom_id)
            .filter(
                BomItem.material_id == material_id,
                BomItem.material_model == material_model,
                BomItem.material_specification == material_specification,
                BomItem.bom_item_color == material_color,
            )
            .all()
        )

        for bom_item1, bom1 in same_materials:
            if (
                bom1.total_bom_id == total_bom_id
                and bom_item1.material_id == material_id
                and bom_item1.material_model == material_model
                and bom_item1.material_specification == material_specification
                and bom_item1.bom_item_color == material_color
                and bom_item1.craft_name
                and bom_item1.craft_name not in new_craft_name_list
            ):
                new_craft_name_list.append(bom_item1.craft_name)

        # Combine the craft names into a single string
        new_craft_name_string = "@".join(new_craft_name_list)
        print(new_craft_name_string)

        # Check if the material is already in the map
        if material_key in material_storage_map:
            # Update the estimated inbound amount
            material_storage_map[
                material_key
            ].estimated_inbound_amount += material_quantity
        else:
            # Create a new MaterialStorage record and add it to the map
            if purchase_divide_order.purchase_divide_order_type == "N":
                material_storage = MaterialStorage(
                    order_shoe_id=order_shoe_id,
                    material_id=material_id,
                    estimated_inbound_amount=material_quantity,
                    actual_purchase_amount=actual_purchase_amount,
                    actual_inbound_amount=0,
                    department_id=bom_item.department_id,
                    current_amount=0,
                    unit_price=0,
                    material_outsource_status="0",
                    material_model=material_model,
                    material_specification=material_specification,
                    material_storage_color=material_color,
                    total_purchase_order_id=total_purchase_order.total_purchase_order_id,
                    craft_name=new_craft_name_string,
                    production_instruction_item_id=bom_item.production_instruction_item_id,
                    actual_inbound_material_id=(
                        actual_inbound_material_id
                        if actual_inbound_material_id
                        else None
                    ),
                    actual_inbound_unit=(
                        actual_inbound_unit if actual_inbound_unit else None
                    ),
                )
                material_storage_map[material_key] = material_storage
            elif purchase_divide_order.purchase_divide_order_type == "S":
                quantity_map = {
                    f"size_{size}_quantity": getattr(
                        purchase_order_item, f"size_{size}_purchase_amount"
                    )
                    for size in SHOESIZERANGE
                }
                size_material_storage = SizeMaterialStorage(
                    order_shoe_id=order_shoe_id,
                    material_id=material_id,
                    total_estimated_inbound_amount=material_quantity,
                    unit_price=0,
                    material_outsource_status="0",
                    department_id=bom_item.department_id,
                    size_material_specification=material_specification,
                    size_material_color=material_color,
                    total_purchase_order_id=total_purchase_order.total_purchase_order_id,
                    size_storage_type=batch_info_type_name,
                    craft_name=new_craft_name_string,
                    production_instruction_item_id=bom_item.production_instruction_item_id,
                )
                for size in SHOESIZERANGE:
                    setattr(
                        size_material_storage,
                        f"size_{size}_estimated_inbound_amount",
                        quantity_map[f"size_{size}_quantity"],
                    )
                material_storage_map[material_key] = size_material_storage

    # Add all material storage objects to the session
    db.session.add_all(material_storage_map.values())
    db.session.flush()
    total_purchase_order_data = {
        "供应商": None,
        "日期": datetime.datetime.now().strftime("%Y-%m-%d"),
        "备注": None,
        "环保要求": None,
        "发货地址": None,
        "交货期限": None,
        "订单信息": None,
        "seriesData": [],
    }
    is_size_based = False  # Flag to determine if it's a size-based order
    total_purchase_orders = (
        db.session.query(
            TotalPurchaseOrder,
            PurchaseDivideOrder,
            PurchaseOrderItem,
            PurchaseOrder,
            BomItem,
            Material,
            Supplier,
        )
        .join(
            PurchaseDivideOrder,
            TotalPurchaseOrder.total_purchase_order_id
            == PurchaseDivideOrder.total_purchase_order_id,
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
        .join(Material, BomItem.material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(TotalPurchaseOrder.total_purchase_order_id == total_purchase_order_id)
        .all()
    )

    for (
        total_purchase_order,
        purchase_divide_order,
        purchase_order_item,
        purchase_order,
        bom_item,
        material,
        supplier,
    ) in total_purchase_orders:
        if total_purchase_order_data["供应商"] is None:
            total_purchase_order_data["供应商"] = supplier.supplier_name
            total_purchase_order_data["备注"] = (
                total_purchase_order.total_purchase_order_remark
            )
            total_purchase_order_data["环保要求"] = (
                total_purchase_order.total_purchase_order_environmental_request
            )
            total_purchase_order_data["发货地址"] = (
                total_purchase_order.shipment_address
            )
            total_purchase_order_data["交货期限"] = (
                total_purchase_order.shipment_deadline
            )
            total_purchase_order_data["订单信息"] = (
                f"{total_purchase_order.total_purchase_order_rid}"
            )

        if purchase_divide_order.purchase_divide_order_type == "S":
            is_size_based = True
            batch_info_type = (
                db.session.query(BatchInfoType, Order)
                .join(
                    Order, Order.batch_info_type_id == BatchInfoType.batch_info_type_id
                )
                .filter(Order.order_id == purchase_order.order_id)
                .first()
            )
            shoe_size_list = [
                {i: getattr(batch_info_type.BatchInfoType, f"size_{i}_name")}
                for i in SHOESIZERANGE
                if getattr(batch_info_type.BatchInfoType, f"size_{i}_name")
            ]

            obj = {
                "物品名称": (
                    f"{material.material_name} "
                    f"{bom_item.material_model or ''} "
                    f"{bom_item.material_specification or ''} "
                    f"{bom_item.bom_item_color or ''}"
                ).strip(),
                "备注": bom_item.remark,
            }
            for size_dic in shoe_size_list:
                for size, size_name in size_dic.items():
                    obj[size_name] = getattr(
                        purchase_order_item, f"size_{size}_purchase_amount", 0
                    )
            total_purchase_order_data["seriesData"].append(obj)
        else:
            # Normal total purchase order data
            total_purchase_order_data["seriesData"].append(
                {
                    "物品名称": (
                        f"{material.material_name} "
                        f"{bom_item.material_model or ''} "
                        f"{bom_item.material_specification or ''} "
                        f"{bom_item.bom_item_color or ''}"
                    ).strip(),
                    "数量": purchase_order_item.adjust_purchase_amount,
                    "单位": purchase_order_item.inbound_unit,
                    "备注": bom_item.remark,
                    "用途说明": "",
                }
            )

    # Consolidate quantities for normal orders
    if not is_size_based:
        consolidated_series_data = {}
        for item in total_purchase_order_data["seriesData"]:
            key = (item["物品名称"], item["单位"])
            if key not in consolidated_series_data:
                consolidated_series_data[key] = {
                    "物品名称": item["物品名称"],
                    "数量": item["数量"],
                    "单位": item["单位"],
                    "备注": item["备注"],
                    "用途说明": item["用途说明"],
                }
            else:
                consolidated_series_data[key]["数量"] += item["数量"]
        total_purchase_order_data["seriesData"] = list(
            consolidated_series_data.values()
        )

    template_path = os.path.join(FILE_STORAGE_PATH, "标准采购订单.xlsx")
    size_template_path = os.path.join(FILE_STORAGE_PATH, "新标准采购订单尺码版.xlsx")

    os.makedirs(os.path.join(FILE_STORAGE_PATH, "批量采购订单"), exist_ok=True)
    output_path = os.path.join(
        FILE_STORAGE_PATH,
        "批量采购订单",
        f"{total_purchase_order_data['订单信息']}.xlsx",
    )

    # Choose the correct generation function
    if is_size_based:
        generate_size_excel_file(
            size_template_path, output_path, total_purchase_order_data
        )
    else:
        generate_excel_file(template_path, output_path, total_purchase_order_data)
    db.session.commit()

    return jsonify({"message": "Total purchase order submitted successfully."})

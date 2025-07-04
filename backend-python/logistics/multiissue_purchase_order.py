from flask import Blueprint, jsonify, request, send_file
import datetime
from app_config import db
from models import *
from constants import SHOESIZERANGE
from api_utility import randomIdGenerater
from decimal import Decimal
import os
from general_document.purchase_divide_order import generate_excel_file
from general_document.size_purchase_divide_order import generate_size_excel_file
from general_document.cutmodel_purchase_divide_order import generate_cut_model_excel_file
from general_document.last_purchase_divide_order import generate_last_excel_file
from general_document.package_purchase_divide_order import generate_package_excel_file
from constants import SHOESIZERANGE
from event_processor import EventProcessor
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from sqlalchemy.orm import aliased
from logger import logger

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
    logger.debug(purchase_divide_orders)
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
    purchase_divide_order_type = purchase_divide_order_id[-5]
    if purchase_divide_order_type in ["F", "S"]:
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
    elif purchase_divide_order_type in ["X","O","I","P","C","L"]:
        query = (
            db.session.query(
                PurchaseDivideOrder,
                PurchaseOrder,
                AssetsPurchaseOrderItem,
                Material,
                MaterialType,
                Supplier,
            )
            .join(
                PurchaseOrder,
                PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id,
            )
            .join(
                AssetsPurchaseOrderItem,
                PurchaseDivideOrder.purchase_divide_order_id
                == AssetsPurchaseOrderItem.purchase_divide_order_id,
            )
            .join(Material, AssetsPurchaseOrderItem.material_id == Material.material_id)
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
            assets_purchase_order_item,
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
                "materialId": material.material_id,
                "materialTypeId": material_type.material_type_id,
                "materialType": material_type.material_type_name,
                "materialName": material.material_name,
                "materialModel": assets_purchase_order_item.material_model,
                "materialSpecification": assets_purchase_order_item.material_specification,
                "color": assets_purchase_order_item.color,
                "unit": material.material_unit,
                "purchaseAmount": assets_purchase_order_item.purchase_amount,
                "remark": assets_purchase_order_item.remark,
                "sizeType": assets_purchase_order_item.size_type,
            }
            for size in SHOESIZERANGE:
                obj[f"size{size}Amount"] = getattr(
                    assets_purchase_order_item, f"size_{size}_purchase_amount"
                )
            grouped_results[divide_order_rid]["assetsItems"].append(obj)
        result = list(grouped_results.values())
        return jsonify(result)
    return jsonify({"message": "Invalid purchase divide order type."})
            
                


@multiissue_purchase_order_bp.route(
    "/multiissue/createtotalpurchaseorder", methods=["POST"]
)
def create_total_purchase_order():
    """Create a total purchase order."""
    data = request.json
    logger.debug(data)
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

    # Ensure AssetsPurchaseOrderItem is correctly aliased
    AliasedAssetsPurchaseOrderItem = aliased(AssetsPurchaseOrderItem)  # ✅ Corrected alias

    # Query with both BOM-based and asset-based purchase orders
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
            AliasedAssetsPurchaseOrderItem,  # ✅ Use alias
        )
        .join(PurchaseDivideOrder, TotalPurchaseOrder.total_purchase_order_id == PurchaseDivideOrder.total_purchase_order_id)
        .join(PurchaseOrder, PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id)
        .outerjoin(PurchaseOrderItem, PurchaseDivideOrder.purchase_divide_order_id == PurchaseOrderItem.purchase_divide_order_id)
        .outerjoin(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
        .outerjoin(AliasedAssetsPurchaseOrderItem, PurchaseDivideOrder.purchase_divide_order_id == AliasedAssetsPurchaseOrderItem.purchase_divide_order_id)
        .outerjoin(Material, db.or_(
            BomItem.material_id == Material.material_id, 
            AliasedAssetsPurchaseOrderItem.material_id == Material.material_id  # ✅ Ensure correct mapping
        ))
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

    logger.debug(query)

    for (
        total_purchase_order,
        purchase_divide_order,
        purchase_order,
        purchase_order_item,
        bom_item,
        material,
        material_type,
        supplier,
        assets_purchase_order_item,
    ) in query:
        # Set order-level details (only once)
        if not grouped_results["totalPurchaseOrderRid"]:
            grouped_results["totalPurchaseOrderRid"] = total_purchase_order.total_purchase_order_rid
        if not grouped_results["supplierName"]:
            grouped_results["supplierName"] = supplier.supplier_name
        if not grouped_results["remark"]:
            grouped_results["remark"] = total_purchase_order.total_purchase_order_remark
        if not grouped_results["shipmentAddress"]:
            grouped_results["shipmentAddress"] = total_purchase_order.shipment_address
        if not grouped_results["shipmentDeadline"]:
            grouped_results["shipmentDeadline"] = total_purchase_order.shipment_deadline
        if not grouped_results["environmentalRequest"]:
            grouped_results["environmentalRequest"] = total_purchase_order.total_purchase_order_environmental_request
        if not grouped_results["totalPurchaseOrderType"]:
            grouped_results["totalPurchaseOrderType"] = purchase_divide_order.purchase_divide_order_type

        # Determine whether to use BOM-based or asset-based items
        if purchase_order.purchase_order_type in ["F", "S"]:
            material_id = bom_item.material_id if bom_item else None
            material_model = bom_item.material_model if bom_item else None
            material_specification = bom_item.material_specification if bom_item else None
            color = bom_item.bom_item_color if bom_item else None
            current_purchase_order_item = purchase_order_item
            approval_amount = purchase_order_item.approval_amount if purchase_order_item else 0  # ✅ Approval amount only for BOM-based orders
        else:  # Handle asset-based purchase orders
            material_id = assets_purchase_order_item.material_id if assets_purchase_order_item else None
            material_model = assets_purchase_order_item.material_model if assets_purchase_order_item else None
            material_specification = assets_purchase_order_item.material_specification if assets_purchase_order_item else None
            color = assets_purchase_order_item.color if assets_purchase_order_item else None
            current_purchase_order_item = assets_purchase_order_item
            approval_amount = 0

        # Ensure material_id is set, otherwise skip this iteration
        if material_id is None:
            continue  

        # Create a unique key for the material
        material_key = (
            material_id,
            material_type.material_type_name,
            material.material_name,
            material_model,
            material_specification,
            color,
        )
        logger.debug(material_key)

        # Initialize material entry if not exists
        if material_key not in material_map:
            material_map[material_key] = {
                "materialId": material_id,
                "materialTypeId": material_type.material_type_id,
                "materialType": material_type.material_type_name,
                "materialName": material.material_name,
                "materialModel": material_model,
                "materialSpecification": material_specification,
                "color": color,
                "unit": material.material_unit,
                "purchaseAmount": 0,
                "approvalAmount": 0,
                "adjustPurchaseAmount": 0,
                "isInboundSperate": (
                    True if current_purchase_order_item and current_purchase_order_item.inbound_material_id else False
                ),
                "remark": bom_item.remark if bom_item else None,
                "sizeType": bom_item.size_type if bom_item else None,
                "materialInboundId": current_purchase_order_item.inbound_material_id if current_purchase_order_item else None,
                "materialInboundUnit": current_purchase_order_item.inbound_unit if current_purchase_order_item else None,
                "materialInboundName": (
                    db.session.query(Material)
                    .filter(Material.material_id == current_purchase_order_item.inbound_material_id)
                    .first()
                    .material_name
                    if current_purchase_order_item and current_purchase_order_item.inbound_material_id
                    else None
                ),
                **{f"size{size}Amount": 0 for size in SHOESIZERANGE},
            }

        # Update amounts
        current_material = material_map[material_key]
        if current_purchase_order_item:
            current_material["purchaseAmount"] += current_purchase_order_item.purchase_amount
            current_material["approvalAmount"] += approval_amount
            current_material["adjustPurchaseAmount"] += current_purchase_order_item.adjust_purchase_amount if current_purchase_order_item.adjust_purchase_amount else current_purchase_order_item.purchase_amount

            # Handle size-based quantities for BOM-based orders
            if purchase_divide_order.purchase_divide_order_type in ["F", "S"]:
                for size in SHOESIZERANGE:
                    current_material[f"size{size}Amount"] += (
                        getattr(current_purchase_order_item, f"size_{size}_purchase_amount", 0)
                        if getattr(current_purchase_order_item, f"size_{size}_purchase_amount", 0)
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
            # ✅ Retrieve `purchase_order_type` dynamically
            purchase_order_type_query = (
                db.session.query(PurchaseOrder.purchase_order_type)
                .join(PurchaseDivideOrder, PurchaseOrder.purchase_order_id == PurchaseDivideOrder.purchase_order_id)
                .filter(PurchaseDivideOrder.total_purchase_order_id == total_purchase_order_id)
                .first()
            )
            purchase_order_type = purchase_order_type_query[0] if purchase_order_type_query else None

            if not purchase_order_type:
                return jsonify({"message": "Purchase order type not found."}), 400

            # ✅ Determine if it's BOM-based or Asset-based based on `purchase_order_type`
            if purchase_order_type in ["F", "S"]:
                # BOM-based order (Join using `BomItem`)
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
                        TotalPurchaseOrder.total_purchase_order_id == total_purchase_order_id,
                        BomItem.material_id == material["materialId"],
                        BomItem.material_model == material["materialModel"],
                        BomItem.material_specification == material["materialSpecification"],
                        BomItem.bom_item_color == material["color"],
                    )
                    .all()
                )
            else:
                # Asset-based order (`O, X, I, L, C, P`)
                purchase_items = (
                    db.session.query(
                        AssetsPurchaseOrderItem, PurchaseDivideOrder, TotalPurchaseOrder
                    )
                    .join(
                        PurchaseDivideOrder,
                        AssetsPurchaseOrderItem.purchase_divide_order_id
                        == PurchaseDivideOrder.purchase_divide_order_id,
                    )
                    .join(
                        TotalPurchaseOrder,
                        PurchaseDivideOrder.total_purchase_order_id
                        == TotalPurchaseOrder.total_purchase_order_id,
                    )
                    .filter(
                        TotalPurchaseOrder.total_purchase_order_id == total_purchase_order_id,
                        AssetsPurchaseOrderItem.material_id == material["materialId"],
                        AssetsPurchaseOrderItem.material_model == material["materialModel"],
                        AssetsPurchaseOrderItem.material_specification == material["materialSpecification"],
                        AssetsPurchaseOrderItem.color == material["color"],
                    )
                    .all()
                )

            if purchase_items:
                # ✅ Distribute `adjust_purchase_amount` evenly among the matched items
                distributed_amount = float(material["adjustPurchaseAmount"]) / len(purchase_items)

                for purchase_item in purchase_items:
                    # ✅ Determine if it's BOM-based or Asset-based
                    if purchase_order_type in ["F", "S"]:
                        purchase_order_item = purchase_item # `PurchaseOrderItem`
                        purchase_order_item.PurchaseOrderItem.adjust_purchase_amount = distributed_amount  # ✅ Explicit reference
                    else:
                        purchase_order_item = purchase_item  # `AssetsPurchaseOrderItem`
                        purchase_order_item.AssetsPurchaseOrderItem.adjust_purchase_amount = distributed_amount  # ✅ Explicit reference

                    # ✅ Handle inbound material ID and unit
                    if material["isInboundSperate"]:
                        if material["materialInboundId"]:
                            if purchase_order_type in ["F", "S"]:
                                purchase_order_item.PurchaseOrderItem.inbound_material_id = material["materialInboundId"]
                                purchase_order_item.PurchaseOrderItem.inbound_unit = material["materialInboundUnit"]
                            else:
                                purchase_order_item.AssetsPurchaseOrderItem.inbound_material_id = material["materialInboundId"]
                                purchase_order_item.AssetsPurchaseOrderItem.inbound_unit = material["materialInboundUnit"]
                        else:
                            return jsonify({"message": "Material ID is required for inbound material."}), 400

    db.session.commit()
    return jsonify(
        {"message": "Total purchase order and materials saved successfully."}
    )



@multiissue_purchase_order_bp.route(
    "/multiissue/submittotalpurchaseorder", methods=["POST"]
)
def submit_total_purchase_order():
    """Submit a total purchase order, create MaterialStorage/SizeMaterialStorage records, and generate an Excel file."""
    total_purchase_order_id = request.json.get("totalPurchaseOrderId")

    # Fetch total purchase order
    total_purchase_order = (
        db.session.query(TotalPurchaseOrder)
        .filter(TotalPurchaseOrder.total_purchase_order_id == total_purchase_order_id)
        .first()
    )

    if not total_purchase_order:
        return jsonify({"message": "Total purchase order not found."}), 404

    total_purchase_order.total_purchase_order_status = "2"

    # Fetch all `purchase_divide_orders` and their `purchase_order_type`
    purchase_divide_orders = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrder.purchase_order_type
        )
        .join(PurchaseOrder, PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id)
        .filter(PurchaseDivideOrder.total_purchase_order_id == total_purchase_order_id)
        .all()
    )

    material_storage_map = {}
    is_size_based = False  # Flag to determine if it's a size-based order
    total_purchase_order_data = {
        "供应商": None,
        "日期": datetime.datetime.now().strftime("%Y-%m-%d"),
        "备注": total_purchase_order.total_purchase_order_remark,
        "环保要求": total_purchase_order.total_purchase_order_environmental_request,
        "发货地址": total_purchase_order.shipment_address,
        "交货期限": total_purchase_order.shipment_deadline,
        "订单信息": f"{total_purchase_order.total_purchase_order_rid}",
        "seriesData": [],
    }
    completed_purchase_orders = set()  # Track purchase orders where all materials are added
    completed_divide_orders_L = set()  # Track `L` type purchase divide orders
    completed_divide_orders_P = set()  # Track `P` type purchase divide orders
    completed_divide_orders_C = set()  # Track `C` type purchase divide orders

    # Loop through each `purchase_divide_order`
    for purchase_divide_order in purchase_divide_orders:
    # Retrieve `purchase_order_type` from `PurchaseOrder` via `PurchaseDivideOrder`
        purchase_order_type_query = (
            db.session.query(PurchaseOrder.purchase_order_type)
            .join(PurchaseDivideOrder, PurchaseOrder.purchase_order_id == PurchaseDivideOrder.purchase_order_id)
            .filter(PurchaseDivideOrder.purchase_divide_order_id == purchase_divide_order.PurchaseDivideOrder.purchase_divide_order_id)
            .first()
        )
        purchase_order_type = purchase_order_type_query[0] if purchase_order_type_query else None

        if not purchase_order_type:
            return jsonify({"message": "Purchase order type not found for some orders."}), 400

        # **Fetch items correctly based on `purchase_order_type`**
        if purchase_order_type in ["F", "S"]:
            # BOM-based orders (Use `PurchaseOrderItem`)
            purchase_order_items = (
                db.session.query(
                    PurchaseOrderItem,
                    BomItem,
                    PurchaseOrder,
                    Material,
                    Supplier,
                )
                .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
                .join(PurchaseDivideOrder, PurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id)
                .join(PurchaseOrder, PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id)
                .join(Material, BomItem.material_id == Material.material_id)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .filter(PurchaseOrderItem.purchase_divide_order_id == purchase_divide_order.PurchaseDivideOrder.purchase_divide_order_id)
                .all()
            )
        else:
            # Asset-based orders (Use `AssetsPurchaseOrderItem`)
            purchase_order_items = (
                db.session.query(
                    AssetsPurchaseOrderItem,
                    PurchaseOrder,
                    Material,
                    Supplier,
                )
                .join(PurchaseDivideOrder, AssetsPurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id)
                .join(PurchaseOrder, PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id)
                .join(Material, AssetsPurchaseOrderItem.material_id == Material.material_id)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .filter(AssetsPurchaseOrderItem.purchase_divide_order_id == purchase_divide_order.PurchaseDivideOrder.purchase_divide_order_id)
                .all()
            )

        # Process each item
        for purchase_item in purchase_order_items:
            if purchase_order_type in ["F", "S"]:
                # ✅ BOM-based orders: Use `PurchaseOrderItem` + `BomItem`
                purchase_order_item = purchase_item.PurchaseOrderItem  # ✅ Explicit reference
                bom_item = purchase_item.BomItem  # ✅ Explicit reference

                material_id = purchase_item.BomItem.material_id  # ✅ Fetch from `BomItem`
                material_model = purchase_item.BomItem.material_model
                material_specification = purchase_item.BomItem.material_specification
                material_color = purchase_item.BomItem.bom_item_color
                order_shoe_id = purchase_item.PurchaseOrder.order_shoe_id   # ✅ Use `purchase_order`
                order_id = purchase_item.PurchaseOrder.order_id
                production_instruction_item_id = purchase_item.BomItem.production_instruction_item_id
                craft_name = purchase_item.BomItem.craft_name

            else:
                # ✅ Asset-based orders: Use `AssetsPurchaseOrderItem`
                purchase_order_item = purchase_item.AssetsPurchaseOrderItem  # ✅ Explicit reference
                bom_item = None  # ❌ No BOM item for assets

                material_id = purchase_item.AssetsPurchaseOrderItem.material_id  # ✅ Fetch directly from `AssetsPurchaseOrderItem`
                material_model = purchase_item.AssetsPurchaseOrderItem.material_model
                material_specification = purchase_item.AssetsPurchaseOrderItem.material_specification
                material_color = purchase_item.AssetsPurchaseOrderItem.color
                order_shoe_id = purchase_item.PurchaseOrder.order_shoe_id  # ✅ Use `purchase_divide_order` relationship
                order_id = purchase_item.PurchaseOrder.order_id
                production_instruction_item_id = None
                craft_name = purchase_order_item.craft_name

            # ✅ Shared Fields (Common for both BOM & Asset-based)
            material_quantity = purchase_order_item.purchase_amount
            actual_inbound_material_id = purchase_order_item.inbound_material_id
            actual_inbound_unit = purchase_order_item.inbound_unit
            


            # Determine if size-based
            if purchase_divide_order.PurchaseDivideOrder.purchase_divide_order_type == "S":
                is_size_based = True
                size_material_storage = SizeMaterialStorage(
                    order_id=order_id,
                    order_shoe_id=order_shoe_id,
                    material_id=material_id,
                    total_estimated_inbound_amount=material_quantity,
                    unit_price=0,
                    material_outsource_status="0",
                    size_material_model=material_model,
                    size_material_specification=material_specification,
                    size_material_color=material_color,
                    total_purchase_order_id=total_purchase_order.total_purchase_order_id,
                    craft_name=craft_name,
                    production_instruction_item_id=production_instruction_item_id
                )

                for size in SHOESIZERANGE:
                    setattr(
                        size_material_storage,
                        f"size_{size}_estimated_inbound_amount",
                        getattr(purchase_order_item, f"size_{size}_purchase_amount", 0),
                    )

                db.session.add(size_material_storage)

            else:
                material_key = (total_purchase_order.total_purchase_order_id, order_shoe_id, material_id, material_model, material_specification, material_color)
                if material_key not in material_storage_map:
                    material_storage = MaterialStorage(
                        order_id=order_id,
                        order_shoe_id=order_shoe_id,
                        material_id=material_id,
                        estimated_inbound_amount=material_quantity,
                        actual_inbound_amount=0,
                        unit_price=0,
                        material_outsource_status="0",
                        material_model=material_model,
                        material_specification=material_specification,
                        material_storage_color=material_color,
                        total_purchase_order_id=total_purchase_order.total_purchase_order_id,
                        actual_inbound_material_id=actual_inbound_material_id if actual_inbound_material_id else material_id,
                        # TODO: delete actual inbound unit
                        actual_inbound_unit=actual_inbound_unit if actual_inbound_unit else None,
                        craft_name=craft_name,
                        production_instruction_item_id=production_instruction_item_id
                    )
                    material_storage_map[material_key] = material_storage
            # completed_purchase_orders.add(purchase_divide_order.PurchaseDivideOrder.purchase_order_id)
        if purchase_order_type == "L":
            completed_divide_orders_L.add(purchase_divide_order.PurchaseDivideOrder.purchase_divide_order_id)
        elif purchase_order_type == "P":
            completed_divide_orders_P.add(purchase_divide_order.PurchaseDivideOrder.purchase_divide_order_id)
        elif purchase_order_type == "C":
            completed_divide_orders_C.add(purchase_divide_order.PurchaseDivideOrder.purchase_divide_order_id)

    db.session.add_all(material_storage_map.values())
    db.session.flush()
    # db.session.query(PurchaseOrder).filter(PurchaseOrder.purchase_order_id.in_(completed_purchase_orders)).update(
    #     {"purchase_order_status": "2"}, synchronize_session=False
    # )

    # ✅ Update separate statuses
# ✅ Update `last_status` where `purchase_order_type = L`
    db.session.query(Order).filter(
        Order.order_id.in_(
            db.session.query(PurchaseOrder.order_id)
            .join(PurchaseDivideOrder, PurchaseOrder.purchase_order_id == PurchaseDivideOrder.purchase_order_id)
            .filter(PurchaseDivideOrder.purchase_divide_order_id.in_(completed_divide_orders_L))
        )
    ).update({"last_status": "2"}, synchronize_session=False)

    # ✅ Update `package_status` where `purchase_order_type = P`
    db.session.query(Order).filter(
        Order.order_id.in_(
            db.session.query(PurchaseOrder.order_id)
            .join(PurchaseDivideOrder, PurchaseOrder.purchase_order_id == PurchaseDivideOrder.purchase_order_id)
            .filter(PurchaseDivideOrder.purchase_divide_order_id.in_(completed_divide_orders_P))
        )
    ).update({"packaging_status": "2"}, synchronize_session=False)

    # ✅ Update `cutting_model_status` where `purchase_order_type = C`
    db.session.query(Order).filter(
        Order.order_id.in_(
            db.session.query(PurchaseOrder.order_id)
            .join(PurchaseDivideOrder, PurchaseOrder.purchase_order_id == PurchaseDivideOrder.purchase_order_id)
            .filter(PurchaseDivideOrder.purchase_divide_order_id.in_(completed_divide_orders_C))
        )
    ).update({"cutting_model_status": "2"}, synchronize_session=False)
    total_purchase_order_data = {
        "供应商": None,
        "日期": datetime.datetime.now().strftime("%Y-%m-%d"),
        "备注": total_purchase_order.total_purchase_order_remark,
        "环保要求": total_purchase_order.total_purchase_order_environmental_request,
        "发货地址": total_purchase_order.shipment_address,
        "交货期限": total_purchase_order.shipment_deadline,
        "订单信息": db.session.query(Order).filter(Order.order_id == order_id).first().order_rid if order_id else None,
        "客人名": db.session.query(Order,Customer).join(Customer,Order.customer_id == Customer.customer_id).filter(Order.order_id == order_id).first().Customer.customer_name if order_id else None,
        "seriesData": [],
    }

    is_size_based = False  # Flag to determine if it's a size-based order

    # Fetch all `purchase_divide_orders` and their `purchase_order_type`
    purchase_divide_orders = (
        db.session.query(
            PurchaseDivideOrder,
            PurchaseOrder.purchase_order_type
        )
        .join(PurchaseOrder, PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id)
        .filter(PurchaseDivideOrder.total_purchase_order_id == total_purchase_order_id)
        .all()
    )

    for purchase_divide_order, purchase_order_type in purchase_divide_orders:
        if purchase_order_type in ["F", "S"]:
            # ✅ BOM-based orders (Use `PurchaseOrderItem`)
            purchase_order_items = (
                db.session.query(
                    PurchaseOrderItem,
                    BomItem,
                    PurchaseOrder,
                    Material,
                    Supplier,
                )
                .join(BomItem, PurchaseOrderItem.bom_item_id == BomItem.bom_item_id)
                .join(PurchaseDivideOrder, PurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id)
                .join(PurchaseOrder, PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id)
                .join(Material, BomItem.material_id == Material.material_id)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .filter(PurchaseOrderItem.purchase_divide_order_id == purchase_divide_order.purchase_divide_order_id)
                .all()
            )
        else:
            # ✅ Asset-based orders (Use `AssetsPurchaseOrderItem`)
            purchase_order_items = (
                db.session.query(
                    AssetsPurchaseOrderItem,
                    PurchaseOrder,
                    Material,
                    Supplier,
                )
                .join(PurchaseDivideOrder, AssetsPurchaseOrderItem.purchase_divide_order_id == PurchaseDivideOrder.purchase_divide_order_id)
                .join(PurchaseOrder, PurchaseDivideOrder.purchase_order_id == PurchaseOrder.purchase_order_id)
                .join(Material, AssetsPurchaseOrderItem.material_id == Material.material_id)
                .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                .filter(AssetsPurchaseOrderItem.purchase_divide_order_id == purchase_divide_order.purchase_divide_order_id)
                .all()
            )

        for purchase_item in purchase_order_items:
            if purchase_order_type in ["F", "S"]:
                # ✅ BOM-based orders
                purchase_order_item = purchase_item.PurchaseOrderItem
                bom_item = purchase_item.BomItem
                material_id = bom_item.material_id
                purchase_order = purchase_item.PurchaseOrder
                material_name = purchase_item.Material.material_name
                material_model = bom_item.material_model
                material_specification = bom_item.material_specification
                material_color = bom_item.bom_item_color
                order_shoe_id = purchase_item.PurchaseOrder.order_shoe_id
                order_id = purchase_item.PurchaseOrder.order_id
                production_instruction_item_id = bom_item.production_instruction_item_id
            else:
                # ✅ Asset-based orders
                purchase_order_item = purchase_item.AssetsPurchaseOrderItem
                bom_item = None  # ❌ No BOM item for assets
                material_id = purchase_order_item.material_id
                purchase_order = purchase_item.PurchaseOrder
                material_name = purchase_item.Material.material_name
                material_model = purchase_order_item.material_model
                material_specification = purchase_order_item.material_specification
                material_color = purchase_order_item.color
                order_shoe_id = purchase_item.PurchaseOrder.order_shoe_id
                order_id = purchase_item.PurchaseOrder.order_id
                production_instruction_item_id = None

            material_quantity = purchase_order_item.purchase_amount
            actual_inbound_material_id = purchase_order_item.inbound_material_id
            actual_inbound_unit = purchase_order_item.inbound_unit
            supplier_name = purchase_item.Supplier.supplier_name

            # ✅ Determine if size-based
            if purchase_divide_order.purchase_divide_order_type == "S":
                is_size_based = True
                batch_info_type = (
                    db.session.query(BatchInfoType, Order)
                    .join(Order, Order.batch_info_type_id == BatchInfoType.batch_info_type_id)
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
                        f"{material_name} "
                        f"{material_model or ''} "
                        f"{material_specification or ''} "
                        f"{material_color or ''}"
                    ).strip(),
                    "型号": material_name + " " + material_model if material_model else "",
                    "类别": material_specification or "",
                    "备注": bom_item.remark if bom_item else "",
                }
                for size_dic in shoe_size_list:
                    for size, size_name in size_dic.items():
                        obj[size_name] = getattr(
                            purchase_order_item, f"size_{size}_purchase_amount", 0
                        )
                total_purchase_order_data["seriesData"].append(obj)
            else:
                # ✅ Normal total purchase order data
                total_purchase_order_data["seriesData"].append(
                    {
                        "物品名称": (
                            f"{material_name} "
                            f"{material_model or ''} "
                            f"{material_specification or ''} "
                            f"{material_color or ''}"
                        ).strip(),
                        "数量": purchase_order_item.adjust_purchase_amount,
                        "型号": material_name + " " + material_model if material_model else "",
                        "类别": material_specification or "",
                        "单位": purchase_order_item.inbound_unit,
                        "备注": bom_item.remark if bom_item else "",
                        "用途说明": "",
                    }
                )

    # ✅ Consolidate quantities for normal orders
    total_purchase_order_data["供应商"] = supplier_name
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
                    "型号": item["型号"],
                    "类别": item["类别"],
                }
            else:
                consolidated_series_data[key]["数量"] += item["数量"]
        total_purchase_order_data["seriesData"] = list(consolidated_series_data.values())

    # ✅ Determine correct Excel template
    template_path = os.path.join(FILE_STORAGE_PATH, "标准采购订单.xlsx")
    size_template_path = os.path.join(FILE_STORAGE_PATH, "新标准采购订单尺码版.xlsx")

    os.makedirs(os.path.join(FILE_STORAGE_PATH, "批量采购订单"), exist_ok=True)
    output_path = os.path.join(
        FILE_STORAGE_PATH,
        "批量采购订单",
        f"{total_purchase_order_data['订单信息']}.xlsx",
    )

    # ✅ Choose the correct generation function
    if is_size_based:
        if purchase_order.purchase_order_type in ["F", "S"]: 
            generate_size_excel_file(
                size_template_path, output_path, total_purchase_order_data
            )
        elif purchase_order.purchase_order_type in ["L"]:
            # for the last, the 类别 should be the material name, the 型号 should be the material model
            for item in total_purchase_order_data["seriesData"]:
                item["类别"] = item["物品名称"].split(" ")[0]  # ✅ 类别 = Material Name (first part)
                item["型号"] = " ".join(item["物品名称"].split(" ")[1:])  # ✅ 型号 = Remaining parts
            generate_last_excel_file(
                size_template_path, output_path, total_purchase_order_data
            )
        elif purchase_order.purchase_order_type in ["C"]:
            generate_size_excel_file(
                size_template_path, output_path, total_purchase_order_data
            )
    else:
        if purchase_order.purchase_order_type in ["F", "S"]:
            generate_excel_file(template_path, output_path, total_purchase_order_data)
        elif purchase_order.purchase_order_type in ["P"]:
            order_rid = total_purchase_order_data["订单信息"]
            package_info_file_path = os.path.join(
                FILE_STORAGE_PATH, order_rid, "包装资料.xlsx"
            )
            generate_package_excel_file(
                template_path, output_path, package_info_file_path, total_purchase_order_data
            )
    db.session.commit()

    return jsonify({"message": "Total purchase order submitted successfully."})

@multiissue_purchase_order_bp.route("/multiissue/downloadtotalpurchaseorder", methods=["GET"])
def download_total_purchase_order():
    """Download a total purchase order Excel file."""
    total_purchase_order_id = request.args.get("totalPurchaseOrderRid")
    file_path = os.path.join(
        FILE_STORAGE_PATH, "批量采购订单", f"{total_purchase_order_id}.xlsx"
    )

    if not os.path.exists(file_path):
        return jsonify({"message": "File not found."}), 404

    return send_file(file_path, as_attachment=True)

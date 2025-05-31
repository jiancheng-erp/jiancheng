from flask import Blueprint, jsonify, request, current_app
from models import *
from sqlalchemy import func
from datetime import datetime
from event_processor import EventProcessor
import time
from decimal import Decimal
from collections import defaultdict
from wechat_api.send_message_api import send_massage_to_users
from login.login import current_user_info
from constants import *


head_manager_bp = Blueprint("head_manager_bp", __name__)


@head_manager_bp.route("/headmanager/getcostinfo", methods=["GET"])
def get_cost_info():
    """Get the cost information of the shoes."""
    time_s = time.time()
    order_rid = request.args.get("orderRid", None)
    if not order_rid:
        orders = Order.query.all()
    else:
        orders = Order.query.filter_by(order_rid=order_rid).all()

    if not orders:
        return jsonify({"msg": "No order found."}), 404

    order_ids = [o.order_id for o in orders]
    customer_ids = [o.customer_id for o in orders]

    # Customers
    customers = {
        c.customer_id: c.customer_name
        for c in db.session.query(Customer).filter(Customer.customer_id.in_(customer_ids))
    }

    # OrderShoe and Shoe
    order_shoes = (
        db.session.query(OrderShoe, Shoe)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .filter(OrderShoe.order_id.in_(order_ids))
        .all()
    )
    order_shoes_by_order = defaultdict(list)
    order_shoe_ids = []
    for os, shoe in order_shoes:
        order_shoes_by_order[os.order_id].append((os, shoe))
        order_shoe_ids.append(os.order_shoe_id)

    # MaterialStorage and SizeMaterialStorage
    material_storages = defaultdict(list)
    for ms in db.session.query(MaterialStorage).filter(MaterialStorage.order_shoe_id.in_(order_shoe_ids)):
        material_storages[ms.order_shoe_id].append(ms)

    size_storages = defaultdict(list)
    for ss in db.session.query(SizeMaterialStorage).filter(SizeMaterialStorage.order_shoe_id.in_(order_shoe_ids)):
        size_storages[ss.order_shoe_id].append(ss)

    # UnitPriceReports
    cutting_prices = defaultdict(float)
    sewing_prices = defaultdict(float)
    for upr in db.session.query(UnitPriceReport).filter(UnitPriceReport.order_shoe_id.in_(order_shoe_ids)):
        if upr.team == "裁断":
            cutting_prices[upr.order_shoe_id] += upr.price_sum
        elif upr.team == "针车":
            sewing_prices[upr.order_shoe_id] += upr.price_sum

    # Production amounts
    prod_amounts = defaultdict(lambda: {"cutting": 0, "sewing": 0})
    for ipa, ost, os in (
        db.session.query(OrderShoeProductionAmount, OrderShoeType, OrderShoe)
        .join(OrderShoeType, OrderShoeProductionAmount.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoe.order_shoe_id.in_(order_shoe_ids))
    ):
        if ipa.production_team == 0:
            prod_amounts[os.order_shoe_id]["cutting"] += ipa.total_production_amount
        elif ipa.production_team == 1:
            prod_amounts[os.order_shoe_id]["sewing"] += ipa.total_production_amount

    # OutsourceInfo
    outsources = {
        o.order_shoe_id: o.total_cost
        for o in db.session.query(OutsourceInfo).filter(OutsourceInfo.order_shoe_id.in_(order_shoe_ids))
    }

    # BatchInfo (for amount and price)
    batch_infos = defaultdict(list)
    for os, ost, osbi in (
        db.session.query(OrderShoe, OrderShoeType, OrderShoeBatchInfo)
        .join(OrderShoeType, OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id)
        .join(OrderShoeBatchInfo, OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(OrderShoe.order_shoe_id.in_(order_shoe_ids))
    ):
        batch_infos[os.order_shoe_id].append((ost.unit_price, osbi.total_amount))

    cost_info = []

    for o in orders:
        customer_name = customers.get(o.customer_id, "")
        order_shoe_list = []

        order_totals = {
            "material_cost": 0, "admin_exp": 0, "logistics": 0,
            "outsource": 0, "price": 0, "shoe_amount": 0,
            "labor": 0, "cutting": 0, "sewing": 0, "molding": 0,
            "cost": 0, "profit": 0
        }

        for os, shoe in order_shoes_by_order[o.order_id]:
            sid = os.order_shoe_id

            # Calculate material costs
            material_cost = sum(
                (max(ms.actual_inbound_amount, ms.estimated_inbound_amount or 0) or 0) * (ms.unit_price or 0)
                for ms in material_storages[sid]
            )
            size_cost = sum(
                (max(ss.total_actual_inbound_amount, ss.total_estimated_inbound_amount or 0) or 0) * (ss.unit_price or 0)
                for ss in size_storages[sid]
            )
            total_material_cost = material_cost + size_cost

            # Cutting and sewing
            cutting_unit_cost = cutting_prices[sid]
            sewing_unit_cost = sewing_prices[sid]
            cutting_amt = prod_amounts[sid]["cutting"]
            sewing_amt = prod_amounts[sid]["sewing"]
            cutting_cost = cutting_unit_cost * cutting_amt
            sewing_cost = sewing_unit_cost * sewing_amt
            molding_cost = 0  # Placeholder
            inside_labor_cost = cutting_cost + sewing_cost + molding_cost

            # Admin, logistics, outsource
            admin_exp = 0
            logistics_cost = 0
            outsource_cost = outsources.get(sid, 0)

            # Sale price and amount
            price_of_shoes = sum((unit_price or 0) * (amount or 0) for unit_price, amount in batch_infos[sid])
            shoe_total_amount = sum(amount or 0 for _, amount in batch_infos[sid])

            total_cost = Decimal(total_material_cost) + Decimal(admin_exp) + Decimal(logistics_cost) + Decimal(outsource_cost) + Decimal(inside_labor_cost)
            cost_per_shoe = total_cost / shoe_total_amount if shoe_total_amount else 0
            profit = Decimal(price_of_shoes) - Decimal(total_cost)
            profit_per_shoe = profit / shoe_total_amount if shoe_total_amount else 0

            # Append to order shoe list
            order_shoe_list.append({
                "shoeRId": shoe.shoe_rid,
                "shoeName": os.customer_product_name,
                "totalMaterialCost": round(total_material_cost, 3),
                "administrativeExpenses": round(admin_exp, 3),
                "logisticsCost": round(logistics_cost, 3),
                "outsouceCost": round(outsource_cost, 3),
                "priceOfShoes": round(price_of_shoes, 3),
                "labourCost": round(inside_labor_cost, 3),
                "cuttingCost": round(cutting_cost, 3),
                "sewingCost": round(sewing_cost, 3),
                "moldingCost": round(molding_cost, 3),
                "shoeTotalAmount": shoe_total_amount,
                "profit": round(profit, 3),
                "profitPerShoe": round(profit_per_shoe, 3),
                "costPerShoe": round(cost_per_shoe, 3),
            })

            # Update totals
            order_totals["material_cost"] += total_material_cost
            order_totals["admin_exp"] += admin_exp
            order_totals["logistics"] += logistics_cost
            order_totals["outsource"] += outsource_cost
            order_totals["price"] += price_of_shoes
            order_totals["shoe_amount"] += shoe_total_amount
            order_totals["labor"] += inside_labor_cost
            order_totals["cutting"] += cutting_cost
            order_totals["sewing"] += sewing_cost
            order_totals["molding"] += molding_cost
            order_totals["cost"] += total_cost
            order_totals["profit"] += profit

        cost_info.append({
            "orderId": o.order_id,
            "orderRid": o.order_rid,
            "customerName": customer_name,
            "orderStartDate": o.start_date.strftime("%Y-%m-%d"),
            "orderShoes": order_shoe_list,
            "orderTotalMaterialCost": round(order_totals["material_cost"], 3),
            "orderTotalAdministrativeExpenses": round(order_totals["admin_exp"], 3),
            "orderTotalLogisticsCost": round(order_totals["logistics"], 3),
            "orderTotalOutsouceCost": round(order_totals["outsource"], 3),
            "orderTotalPriceOfShoes": round(order_totals["price"], 3),
            "orderTotalShoeAmount": order_totals["shoe_amount"],
            "orderTotalLabourCost": round(order_totals["labor"], 3),
            "orderTotalCuttingCost": round(order_totals["cutting"], 3),
            "orderTotalSewingCost": round(order_totals["sewing"], 3),
            "orderTotalMoldingCost": round(order_totals["molding"], 3),
            "orderTotalProfit": round(order_totals["profit"], 3),
            "orderTotalCost": round(order_totals["cost"], 3),
            "orderTotalCostPerShoe": round(order_totals["cost"] / order_totals["shoe_amount"], 3) if order_totals["shoe_amount"] else 0,
            "orderTotalProfitPerShoe": round(order_totals["profit"] / order_totals["shoe_amount"], 3) if order_totals["shoe_amount"] else 0,
        })

    print("time taken for get cost info is", time.time() - time_s)
    return jsonify(cost_info)


@head_manager_bp.route("/headmanager/getorderstatusinfo", methods=["GET"])
def get_order_status_info():
    """Get the status information of the orders."""
    time_s = time.time()
    order_rid = request.args.get("orderRid")
    order_type = request.args.get("orderType")

    # Get orders
    # orders = Order.query.all() if not order_rid else Order.query.filter_by(order_rid=order_rid).all()
    orders = db.session.query(Order).join(OrderStatus, Order.order_id == OrderStatus.order_id).filter(OrderStatus.order_current_status >= 9).all()\
        if not order_rid else db.session.query(Order, OrderStatus).join(OrderStatus, Order.order_id == OrderStatus.order_id).filter(Order.order_rid.like(f"%{order_rid}%"), OrderStatus.order_current_status >= 9).all()
    if not orders:
        return jsonify({"msg": "No order found."}), 404

    order_ids = [o.order_id for o in orders]
    customer_ids = [o.customer_id for o in orders]

    # Get customer names
    customers = {
        c.customer_id: c.customer_name
        for c in db.session.query(Customer).filter(Customer.customer_id.in_(customer_ids))
    }

    # Get order shoes
    order_shoes = db.session.query(OrderShoe, Shoe).join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id).filter(OrderShoe.order_id.in_(order_ids)).all()
    shoes_by_order = defaultdict(list)
    order_shoe_ids = []
    for os, shoe in order_shoes:
        shoes_by_order[os.order_id].append((os, shoe))
        order_shoe_ids.append(os.order_shoe_id)

    # Get production info
    production_infos = {
        pi.order_shoe_id: pi.is_material_arrived
        for pi in db.session.query(OrderShoeProductionInfo).filter(OrderShoeProductionInfo.order_shoe_id.in_(order_shoe_ids))
    }

    # Get current statuses
    status_refs = {
        ref.status_id: ref.status_name
        for ref in db.session.query(OrderShoeStatusReference).all()
    }
    status_by_shoe = defaultdict(list)
    for status in db.session.query(OrderShoeStatus).filter(OrderShoeStatus.order_shoe_id.in_(order_shoe_ids)).all():
        status_name = status_refs.get(status.current_status, "")
        status_by_shoe[status.order_shoe_id].append(status_name)

    # Get finished shoe statuses
    finished_statuses = defaultdict(list)
    fss_query = (
        db.session.query(FinishedShoeStorage, OrderShoeType)
        .join(OrderShoeType, FinishedShoeStorage.order_shoe_type_id == OrderShoeType.order_shoe_type_id)
        .filter(OrderShoeType.order_shoe_id.in_(order_shoe_ids))
        .all()
    )
    for fss, ost in fss_query:
        finished_statuses[ost.order_shoe_id].append(fss.finished_status)

    # Construct response
    order_status_info = []
    if order_type == "0":
        for o in orders:
            customer_name = customers.get(o.customer_id, "")
            order_shoe_list = []

            if len(shoes_by_order[o.order_id]) == 1:
                os, shoe = shoes_by_order[o.order_id][0]
                sid = os.order_shoe_id
                is_arrived_string = "已到料" if production_infos.get(sid) else "未到料"

                # Status string
                order_shoe_status_string = " ".join(status_by_shoe.get(sid, []))

                # Outbound status
                f_status_list = finished_statuses.get(sid, [])
                if not f_status_list:
                    outbound_status = "未入库"
                elif any(s in (0, 1) for s in f_status_list):
                    outbound_status = "未完全出库"
                else:
                    outbound_status = "已出库"
                order_shoe_list.append({
                        "orderShoeId": sid,
                        "shoeRId": shoe.shoe_rid,
                        "shoeName": os.customer_product_name,
                        "isMaterialArrived": is_arrived_string,
                        "orderShoeStatus": order_shoe_status_string,
                        "outboundStatus": outbound_status,
                    })
                order_status_info.append({
                    "orderId": o.order_id,
                    "customerName": customer_name,
                    "shoeRId": shoe.shoe_rid,
                    "shoeName": os.customer_product_name,
                    "orderStartDate": o.start_date.strftime("%Y-%m-%d"),
                    "orderRid": o.order_rid,
                    "orderShoes": order_shoe_list,
                })

            else:
                for os, shoe in shoes_by_order[o.order_id]:
                    sid = os.order_shoe_id
                    is_arrived_string = "已到料" if production_infos.get(sid) else "未到料"

                    # Status string
                    order_shoe_status_string = " ".join(status_by_shoe.get(sid, []))

                    # Outbound status
                    f_status_list = finished_statuses.get(sid, [])
                    if not f_status_list:
                        outbound_status = "未入库"
                    elif any(s in (0, 1) for s in f_status_list):
                        outbound_status = "未完全出库"
                    else:
                        outbound_status = "已出库"

                    order_shoe_list.append({
                        "orderShoeId": sid,
                        "shoeRId": shoe.shoe_rid,
                        "shoeName": os.customer_product_name,
                        "isMaterialArrived": is_arrived_string,
                        "orderShoeStatus": order_shoe_status_string,
                        "outboundStatus": outbound_status,
                    })

                order_status_info.append({
                    "orderId": o.order_id,
                    "customerName": customer_name,
                    "orderStartDate": o.start_date.strftime("%Y-%m-%d"),
                    "orderRid": o.order_rid,
                    "orderShoes": order_shoe_list,
                })

        print("time taken for get order status info is", time.time() - time_s)
        return jsonify(order_status_info)

    else:
        # OrderType != 0 — not implemented in original
        print("time taken for get order status info is", time.time() - time_s)
        return jsonify({"msg": "Invalid order type."}), 400






@head_manager_bp.route("/headmanager/getordershoetimeline", methods=["GET"])
def get_order_shoe_timeline():
    time_s = time.time()
    
    order_id = request.args.get("orderId", None)
    order_shoe_id = request.args.get("orderShoeId", None)
    if not order_id and not order_shoe_id:
        return jsonify({"msg": "Missing query parameters."}), 400

    if order_id:
        # Subquery to find the latest handle_time for each combination of fields
        latest_event_subquery = (
            db.session.query(
                Event.operation_id,
                Event.event_order_id,
                Event.event_type,
                func.max(Event.handle_time).label("latest_handle_time")
            )
            .filter(Event.event_order_id == order_id, Event.event_type == 0)
            .group_by(Event.operation_id, Event.event_order_id, Event.event_type)
            .subquery()
        )

        # Main query to fetch the latest records
        event = (
            db.session.query(Event, Operation, Order, OrderStatus, OrderStatusReference, OrderShoeStatusReference)
            .join(Operation, Event.operation_id == Operation.operation_id)
            .join(Order, Event.event_order_id == Order.order_id)
            .join(
                OrderStatusReference,
                Operation.operation_modified_status == OrderStatusReference.order_status_id,
            )
            .join(OrderStatus, OrderStatus.order_id == Order.order_id)
            .join(
                OrderShoeStatusReference,
                Operation.operation_modified_status == OrderShoeStatusReference.status_id,
            )
            .join(
                latest_event_subquery,
                (Event.operation_id == latest_event_subquery.c.operation_id) &
                (Event.event_order_id == latest_event_subquery.c.event_order_id) &
                (Event.event_type == latest_event_subquery.c.event_type) &
                (Event.handle_time == latest_event_subquery.c.latest_handle_time)
            )
            .filter(Operation.operation_modified_value == 2)
            .all()
        )

        event_list = []
        if event:
            for e in event:
                event_list.append(
                    {
                        "operationId": e.Operation.operation_id,
                        "operationName": e.Operation.operation_name,
                        "operationModifiedStatus": (e.OrderStatusReference.order_status_name
                                                    if e.Operation.operation_type == 1
                                                    else e.OrderShoeStatusReference.status_name),
                        "handleTime": e.Event.handle_time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
            return jsonify(event_list)
        else:
            return jsonify({"msg": "No event found."}), 404

    if order_shoe_id:
        # Subquery to find the latest handle_time for each combination of fields
        latest_event_subquery = (
            db.session.query(
                Event.operation_id,
                Event.event_order_shoe_id,
                Event.event_type,
                func.max(Event.handle_time).label("latest_handle_time")
            )
            .filter(Event.event_order_shoe_id == order_shoe_id, Event.event_type == 1)
            .group_by(Event.operation_id, Event.event_order_shoe_id, Event.event_type)
            .subquery()
        )

        # Main query to fetch the latest records
        event = (
            db.session.query(Event, Operation, OrderShoe, OrderShoeStatusReference)
            .join(Operation, Event.operation_id == Operation.operation_id)
            .join(OrderShoe, Event.event_order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                OrderShoeStatusReference, Operation.operation_modified_status == OrderShoeStatusReference.status_id
            )
            .join(
                latest_event_subquery,
                (Event.operation_id == latest_event_subquery.c.operation_id) &
                (Event.event_order_shoe_id == latest_event_subquery.c.event_order_shoe_id) &
                (Event.event_type == latest_event_subquery.c.event_type) &
                (Event.handle_time == latest_event_subquery.c.latest_handle_time)
            )
            .filter(Operation.operation_modified_value == 2)
            .all()
        )

        event_list = []
        time_t = time.time()
        time_taken = time_t - time_s
        print("time taken for order shoe time line is " + str(time_taken))
        if event:
            for e in event:
                event_list.append(
                    {
                        "operationId": e.Operation.operation_id,
                        "operationName": e.Operation.operation_name,
                        "operationModifiedStatus": e.OrderShoeStatusReference.status_name,
                        "handleTime": e.Event.handle_time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
            return jsonify(event_list)
        else:
            return jsonify({"msg": "No event found."}), 404



@head_manager_bp.route("/headmanager/getmaterialpriceinfo", methods=["GET"])
def get_material_price_info():
    """Get the price information of the materials."""
    time_s = time.time()
    # Get query parameters
    material_name = request.args.get("materialName", None)
    material_model = request.args.get("materialModel", None)
    material_specification = request.args.get("materialSpecification", None)
    supplier_name = request.args.get("supplierName", None)

    # Subquery to get the latest inbound record for each material storage
    latest_material_inbound_subquery = (
        db.session.query(
            InboundRecord.material_storage_id.label("material_storage_id"),
            func.max(InboundRecord.inbound_datetime).label("latest_inbound_date"),
        )
        .group_by(InboundRecord.material_storage_id)
        .subquery()
    )

    # Subquery to get the latest inbound record for each size material storage
    latest_size_inbound_subquery = (
        db.session.query(
            InboundRecord.size_material_storage_id.label("size_material_storage_id"),
            func.max(InboundRecord.inbound_datetime).label("latest_inbound_date"),
        )
        .group_by(InboundRecord.size_material_storage_id)
        .subquery()
    )

    # Main query to get material price info with the newest inbound record
    material_storage = (
        db.session.query(MaterialStorage, Material, MaterialType, Supplier, InboundRecord)
        .join(Material, MaterialStorage.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .outerjoin(
            latest_material_inbound_subquery,
            MaterialStorage.material_storage_id
            == latest_material_inbound_subquery.c.material_storage_id,
        )
        .outerjoin(
            InboundRecord,
            (
                InboundRecord.material_storage_id
                == latest_material_inbound_subquery.c.material_storage_id
            )
            & (
                InboundRecord.inbound_datetime
                == latest_material_inbound_subquery.c.latest_inbound_date
            ),
        )
        .all()
    )

    # Main query to get size material price info with the newest inbound record
    size_material_storage = (
        db.session.query(SizeMaterialStorage, Material, MaterialType, Supplier, InboundRecord)
        .join(Material, SizeMaterialStorage.material_id == Material.material_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .outerjoin(
            latest_size_inbound_subquery,
            SizeMaterialStorage.size_material_storage_id
            == latest_size_inbound_subquery.c.size_material_storage_id,
        )
        .outerjoin(
            InboundRecord,
            (
                InboundRecord.size_material_storage_id
                == latest_size_inbound_subquery.c.size_material_storage_id
            )
            & (
                InboundRecord.inbound_datetime
                == latest_size_inbound_subquery.c.latest_inbound_date
            ),
        )
        .all()
    )

    # Process results for material storage
    material_price_info = []
    for ms in material_storage:
        if (
            (not material_name or ms.Material.material_name == material_name)
            and (not material_model or ms.MaterialStorage.material_model == material_model)
            and (
                not material_specification
                or ms.MaterialStorage.material_specification == material_specification
            )
            and (not supplier_name or ms.Supplier.supplier_name == supplier_name)
        ):
            # Handle missing inbound record
            purchase_date = (
                ms.InboundRecord.inbound_datetime.strftime("%Y-%m-%d")
                if ms.InboundRecord and ms.InboundRecord.inbound_datetime
                else "未入库"
            )

            material_price_info.append(
                {
                    "type": "N",
                    "materialType": ms.MaterialType.material_type_name,
                    "materialStorageId": ms.MaterialStorage.material_storage_id,
                    "materialName": ms.Material.material_name,
                    "materialModel": ms.MaterialStorage.material_model,
                    "materialSpecification": ms.MaterialStorage.material_specification,
                    "supplierName": ms.Supplier.supplier_name,
                    "unitPrice": ms.MaterialStorage.unit_price,
                    "color": ms.MaterialStorage.material_storage_color,
                    "purchaseAmount": ms.MaterialStorage.actual_inbound_amount,  # Assuming 'amount' is the quantity field
                    "purchaseDate": purchase_date,  # Set to "未入库" if no inbound record exists,
                    "purchaseCost": round(ms.MaterialStorage.actual_inbound_amount * ms.MaterialStorage.unit_price, 3),
                }
            )

    # Process results for size material storage
    for sms in size_material_storage:
        if (
            (not material_name or sms.Material.material_name == material_name)
            and (not material_model or sms.SizeMaterialStorage.size_material_model == material_model)
            and (
                not material_specification
                or sms.SizeMaterialStorage.material_specification == material_specification
            )
            and (not supplier_name or sms.Supplier.supplier_name == supplier_name)
        ):
            # Handle missing inbound record
            purchase_date = (
                sms.InboundRecord.inbound_datetime.strftime("%Y-%m-%d")
                if sms.InboundRecord and sms.InboundRecord.inbound_datetime
                else "未入库"
            )

            material_price_info.append(
                {
                    "type": "S",
                    "materialType": sms.MaterialType.material_type_name, 
                    "materialStorageId": sms.SizeMaterialStorage.size_material_storage_id,
                    "materialName": sms.Material.material_name,
                    "materialModel": sms.SizeMaterialStorage.size_material_model,
                    "materialSpecification": sms.SizeMaterialStorage.size_material_specification,
                    "supplierName": sms.Supplier.supplier_name,
                    "unitPrice": sms.SizeMaterialStorage.unit_price,
                    "color": sms.SizeMaterialStorage.size_material_color,
                    "purchaseAmount": sms.SizeMaterialStorage.total_actual_inbound_amount,  # Assuming 'amount' is the quantity field
                    "purchaseDate": purchase_date,  # Set to "未入库" if no inbound record exists
                    "purchaseCost": round(sms.SizeMaterialStorage.total_actual_inbound_amount * sms.SizeMaterialStorage.unit_price, 3),
                }
            )
    time_t = time.time()
    time_taken = time_t - time_s
    print("time taken for get_material price info is " + str(time_taken))
    return jsonify(material_price_info)


@head_manager_bp.route("/headmanager/getmaterialinboundcurve", methods=["GET"])
def get_material_inbound_curve():
    """Get the inbound curve of the materials."""
    material_type = request.args.get("materialType", None)
    material_storage_id = request.args.get("materialStorageId", None)
    if not material_type or not material_storage_id:
        return jsonify({"msg": "Missing query parameters."}), 400
    curve_data = []
    if material_type == "N":
        material_storage = (
            db.session.query(MaterialStorage, InboundRecord)
            .join(
                InboundRecord,
                MaterialStorage.material_storage_id
                == InboundRecord.material_storage_id,
            )
            .filter(MaterialStorage.material_storage_id == material_storage_id)
            .all()
        )
        for ms in material_storage:
            curve_data.append(
                {
                    "date": ms.InboundRecord.inbound_datetime.strftime("%Y-%m-%d"),
                    "unitPrice": ms.MaterialStorage.unit_price,
                }
            )
        return jsonify(curve_data)
    elif material_type == "S":
        size_material_storage = (
            db.session.query(SizeMaterialStorage, InboundRecord)
            .join(
                InboundRecord,
                SizeMaterialStorage.size_material_storage_id
                == InboundRecord.size_material_storage_id,
            )
            .filter(SizeMaterialStorage.size_material_storage_id == material_storage_id)
            .all()
        )
        for sms in size_material_storage:
            curve_data.append(
                {
                    "date": sms.InboundRecord.inbound_datetime.strftime("%Y-%m-%d"),
                    "unitPrice": sms.SizeMaterialStorage.unit_price,
                }
            )
        return jsonify(curve_data)
    return jsonify({"msg": "Invalid material type."}), 400
    # Get query parameters


@head_manager_bp.route("/headmanager/financialstatus", methods=["GET"])
def get_financial_status():
    time_s = time.time()
    order_rid = request.args.get("orderRid", None)
    if not order_rid:
        order = Order.query.all()
    else:
        order = Order.query.filter(Order.order_rid.like(f"%{order_rid}%")).all()
    financial_list = []
    for o in order:
        customer_name = db.session.query(Customer).filter(Customer.customer_id == o.customer_id).first().customer_name
        order_shoes = (
            db.session.query(OrderShoe, Shoe)
            .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
            .filter(OrderShoe.order_id == o.order_id)
            .all()
        )
        order_price_input_status = "未填写"
        order_status = (
            db.session.query(OrderStatus)
            .filter(OrderStatus.order_id == o.order_id)
            .first()
            .order_current_status
        )
        if order_status >= 7:
            order_price_input_status = "已填写"
        order_shoe_list = []
        for os in order_shoes:
            order_shoe_material_inbound_status = "未填写"
            order_shoe_cutting_input_status = "未填写"
            order_shoe_sewing_input_status = "未填写"
            order_shoe_molding_input_status = "未填写"
            order_shoe_price_input_status = order_price_input_status
            production_info = (
                db.session.query(OrderShoeProductionInfo)
                .filter(
                    OrderShoeProductionInfo.order_shoe_id == os.OrderShoe.order_shoe_id
                )
                .first()
            )
            is_arrived = (
                production_info.is_material_arrived if production_info else False
            )
            if is_arrived:
                order_shoe_material_inbound_status = "已填写"
            cutting_price_report = (
                db.session.query(UnitPriceReport)
                .filter(
                    UnitPriceReport.order_shoe_id == os.OrderShoe.order_shoe_id,
                    UnitPriceReport.team == "裁断",
                )
                .first()
            )
            if cutting_price_report:
                if cutting_price_report.status == 1:
                    order_shoe_cutting_input_status = "未审核"
                if cutting_price_report.status == 2:
                    order_shoe_cutting_input_status = "已填写"
            sewing_price_report = (
                db.session.query(UnitPriceReport)
                .filter(
                    UnitPriceReport.order_shoe_id == os.OrderShoe.order_shoe_id,
                    UnitPriceReport.team == "针车",
                )
                .first()
            )
            if sewing_price_report:
                if sewing_price_report.status == 1:
                    order_shoe_sewing_input_status = "未审核"
                if sewing_price_report.status == 2:
                    order_shoe_sewing_input_status = "已填写"
            order_shoe_list.append(
                {
                    "shoeRId": os.Shoe.shoe_rid,
                    "shoeName": os.OrderShoe.customer_product_name,
                    "materialInboundStatus": order_shoe_material_inbound_status,
                    "cuttingInputStatus": order_shoe_cutting_input_status,
                    "sewingInputStatus": order_shoe_sewing_input_status,
                    "moldingInputStatus": order_shoe_molding_input_status,
                    "priceInputStatus": order_shoe_price_input_status,
                }
            )
        order_info = {
            "orderId": o.order_id,
            "orderRid": o.order_rid,
            "customerName": customer_name,
            "orderStartDate": o.start_date.strftime("%Y-%m-%d"),
            "orderShoes": order_shoe_list,
        }
        financial_list.append(order_info)
    time_t = time.time()
    print("financial status time taken is " + str(time_t - time_s))
    return jsonify(financial_list)

@head_manager_bp.route("/headmanager/saveProductionOrderPrice", methods=["POST"])
def save_production_order_Price():
    """Confirm the production order."""
    unit_price_form = request.json.get('unitPriceForm')
    currency_type_form = request.json.get('currencyTypeForm')
    for order_shoe_type_id in unit_price_form.keys():
        unit_price = Decimal(unit_price_form[order_shoe_type_id])
        currency_type = currency_type_form[order_shoe_type_id]
        # find order_shoe_type
        order_shoe_type = db.session.query(OrderShoeType).filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id).first()
        order_shoe_type.unit_price = unit_price
        order_shoe_type.currency_type = currency_type
        entities = (db.session.query(OrderShoeBatchInfo)
            .filter(OrderShoeBatchInfo.order_shoe_type_id == order_shoe_type_id)
			.all())
        for entity in entities:
            entity.total_price = unit_price * entity.total_amount
    db.session.commit()

    return jsonify({"msg": "Production order confirmed."})

@head_manager_bp.route("/headmanager/confirmProductionOrder", methods=["POST"])
def confirm_production_order():
    order_id = request.json.get("orderId")
    order = Order.query.filter(Order.order_id == order_id).first()
    if not order:
        return jsonify({"msg": "Order not found."}), 404
    order_rid = order.order_rid
    order_shoe_rid = db.session.query(OrderShoe, Shoe).join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id).filter(OrderShoe.order_id == order_id).first().Shoe.shoe_rid
    order_status = OrderStatus.query.filter(OrderStatus.order_id == order_id).first()
    if order_status.order_current_status == 7:
        processor = EventProcessor()
        event = Event(
            staff_id=1,
            operation_id=14,
            event_order_id=order_id,
            event_type=0,
            handle_time=datetime.now(),
        )
        result = processor.processEvent(event)
        db.session.add(event)
        db.session.commit()
        event = Event(
            staff_id=1,
            operation_id=15,
            event_order_id=order_id,
            event_type=0,
            handle_time=datetime.now(),
        )
        result = processor.processEvent(event)
        db.session.add(event)
        db.session.commit()
        event = Event(
            staff_id=1,
            operation_id=16,
            event_order_id=order_id,
            event_type=0,
            handle_time=datetime.now(),
        )
        result = processor.processEvent(event)
        db.session.add(event)
        db.session.commit()
        event = Event(
            staff_id=1,
            operation_id=17,
            event_order_id=order_id,
            event_type=0,
            handle_time=datetime.now(),
        )
        result = processor.processEvent(event)
        db.session.add(event)
        message = f"订单已下发至投产指令单阶段，订单号：{order_rid}，鞋型号：{order_shoe_rid}"
        users = "YangShuYao"
        send_massage_to_users(message, users)
        db.session.commit()
        return jsonify({"msg": "Production order confirmed."})
    else:
        return jsonify({"msg": "Error Order Status"}), 400


    # Get the total number of shoes in transit
    
@head_manager_bp.route("/headmanager/getallrevertevent", methods=["GET"])
def get_all_revert_event():
    result = []
    revert_events = db.session.query(RevertEvent, Order).join(Order, RevertEvent.order_id == Order.order_id).all()
    for revert_event, order in revert_events:
        result.append(
            {
                "revertEventId": revert_event.revert_event_id,
                "orderRid": order.order_rid,
                "revertEventTime": revert_event.event_time.strftime("%Y-%m-%d %H:%M:%S"),
                "revertEventReason": revert_event.revert_reason,
                "initialingDepartment": revert_event.initialing_department,
                "responsibleDepartment": revert_event.responsible_department,
            }
        )
    return jsonify(result)


@head_manager_bp.route("/headmanager/approvepricereportbyheadmanager", methods=["PATCH"])
def approve_price_report_by_head_manager():
    data = request.get_json()
    order_shoe_id = data["orderShoeId"]
    report_id = data["reportId"]
    flag = True
    _, staff, department = current_user_info()
    report = db.session.query(UnitPriceReport).get(report_id)
    # if it is sewing or pre-sewing report, check if either one is approved
    if report.team == "针车预备" or report.team == "针车":
        query = db.session.query(UnitPriceReport).filter_by(order_shoe_id=order_shoe_id)
        if report.team == "针车预备":
            report2 = query.filter_by(team="针车").first()
        else:
            report2 = query.filter_by(team="针车预备").first()
        if report2.status != PRICE_REPORT_GM_APPROVED:
            flag = False
    # sum up the price
    value = (
        db.session.query(func.sum(UnitPriceReportDetail.price))
        .filter_by(report_id=report_id)
        .group_by(UnitPriceReportDetail.report_id)
        .scalar()
    )
    report.price_sum = value
    report.status = PRICE_REPORT_GM_APPROVED
    report.rejection_reason = None
    if flag:
        processor: EventProcessor = current_app.config["event_processor"]
        if report.team == "裁断":
            operation_arr = [82, 83]
        elif report.team == "针车" or report.team == "针车预备":
            operation_arr = [96, 97]
        elif report.team == "成型":
            operation_arr = [116, 117]
        else:
            return jsonify({"message": "Cannot change current status"}), 403
        try:
            for operation in operation_arr:
                event = Event(
                    staff_id=staff.staff_id,
                    handle_time=datetime.now(),
                    operation_id=operation,
                    event_order_id=data["orderId"],
                    event_order_shoe_id=data["orderShoeId"],
                )
                processor.processEvent(event)
                db.session.add(event)
        except Exception as e:
            print(e)
            return jsonify({"message": "failed"}), 400
    db.session.commit()
    return jsonify({"message": "审批成功"}), 200


@head_manager_bp.route("/headmanager/rejectpricereportbyheadmanager", methods=["PATCH"])
def reject_price_report_by_head_manager():
    data = request.get_json()
    report_id_arr = data["reportIdArr"]

    processor: EventProcessor = current_app.config["event_processor"]
    _, staff, department = current_user_info()
    team = None
    # find order shoe current status
    for report_id in report_id_arr:
        report = db.session.query(UnitPriceReport).get(report_id)
        report.status = PRICE_REPORT_GM_REJECTED
        report.rejection_reason = data["rejectionReason"]
        team = report.team
    
    if team == "裁断":
        operation = 78
        current_status = 22
    elif team == "针车" or team == "预备":
        operation = 92
        current_status = 29
    elif team == "成型":
        operation = 112
        current_status = 39
    else:
        return jsonify({"message": "Cannot change current status"}), 403
    try:
        event = Event(
            staff_id=staff.staff_id,
            handle_time=datetime.now(),
            operation_id=operation,
            event_order_id=data["orderId"],
            event_order_shoe_id=data["orderShoeId"],
        )
        processor.processRejectEvent(event, current_status)
    except Exception as e:
        print(e)
        return jsonify({"message": "failed"}), 400
    db.session.commit()
    return jsonify({"message": "success"})

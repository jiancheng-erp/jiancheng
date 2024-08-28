import traceback
from datetime import datetime, timedelta

from app_config import db
from constants import IN_PRODUCTION_ORDER_NUMBER, PRICE_REPORT_REFERENCE
from event_processor import EventProcessor
from flask import Blueprint, jsonify, request
from models import *
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert

production_manager_bp = Blueprint("production_manager_bp", __name__)


@production_manager_bp.route(
    "/production/productionmanager/gettobescheduledorders", methods=["GET"]
)
def get_to_be_scheduled_orders():
    response = (
        db.session.query(
            Order,
            Customer,
            OrderShoe,
            func.sum(OrderShoeBatchInfo.total_amount),
        )
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoe.order_shoe_id == OrderShoeBatchInfo.order_shoe_id,
        )
        .filter(
            OrderShoeStatus.current_status == 17,
            OrderShoeStatus.current_status_value != 2,
        )
        .group_by(Order.order_id, OrderShoe.order_shoe_id)
        .all()
    )

    result = []
    for row in response:
        order, customer, order_shoe, total_amount = row
        obj = {
            "orderId": order.order_id,
            "orderShoeId": order_shoe.order_shoe_id,
            "customerName": customer.customer_name,
            "startDate": order.start_date,
            "endDate": order.end_date,
            "orderTotalShoes": total_amount,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getinprogressorders", methods=["GET"]
)
def get_in_progress_orders():
    response = (
        db.session.query(
            Order,
            Customer,
            OrderShoeStatus.current_status,
            OrderShoeProductionInfo.cutting_start_date,
            OrderShoeProductionInfo.molding_end_date,
            func.sum(OrderShoeBatchInfo.total_amount),
        )
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeStatus, OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id)
        .join(
            OrderShoeProductionInfo,
            OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(
            OrderShoeBatchInfo,
            OrderShoe.order_shoe_id == OrderShoeBatchInfo.order_shoe_id,
        )
        .filter(
            OrderShoeStatus.current_status >= 18, OrderShoeStatus.current_status < 40
        )
        .group_by(Order.order_id, OrderShoe.order_shoe_id)
        .all()
    )
    result = []
    mapping = {}
    for row in response:
        (
            order,
            customer,
            current_status,
            cutting_start_date,
            molding_end_date,
            amount_per_order_shoe,
        ) = row
        if order.order_id not in mapping:
            value = "已排产" if current_status == 18 else "排产中"
            mapping[order.order_id] = {
                "startDate": cutting_start_date,
                "endDate": molding_end_date,
                "customerName": customer.customer_name,
                "orderTotalShoes": amount_per_order_shoe,
                "deadlineDate": order.end_date,
                "orderStatus": value,
            }
        else:
            mapping[order.order_id]["startDate"] = min(
                mapping[order.order_id]["start_date"], cutting_start_date
            )
            mapping[order.order_id]["endDate"] = max(
                mapping[order.order_id]["start_date"], molding_end_date
            )
            mapping[order.order_id]["orderTotalShoes"] += amount_per_order_shoe
            if current_status != 18:
                mapping[order.order_id]["orderStatus"] = "排产中"
    return result


@production_manager_bp.route(
    "/production/productionmanager/getorderscheduleinfo", methods=["GET"]
)
def get_order_schedule_info():
    order_id = request.args.get("orderId")
    response = (
        db.session.query(
            OrderShoe,
            Shoe,
            func.sum(OrderShoeBatchInfo.total_amount),
            func.sum(OrderShoeBatchInfo.cutting_amount),
            func.sum(OrderShoeBatchInfo.sewing_amount),
            func.sum(OrderShoeBatchInfo.molding_amount),
            OrderShoeProductionInfo,
        )
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoe.order_shoe_id == OrderShoeBatchInfo.order_shoe_id,
        )
        .join(
            OrderShoeProductionInfo,
            OrderShoe.order_shoe_id == OrderShoeProductionInfo.order_shoe_id,
        )
        .filter(Order.order_id == order_id)
        .group_by(OrderShoe.order_shoe_id)
        .all()
    )

    result = []
    for row in response:
        (
            order_shoe,
            shoe,
            total_amount,
            cutting_amount,
            sewing_amount,
            molding_amount,
            production_info,
        ) = row
        obj = {
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "orderShoeTotalAmount": total_amount,
            "cuttingLineNumbers": production_info.cutting_line_numbers,
            "preSewingLineNumbers": production_info.pre_sewing_line_numbers,
            "sewingLineNumbers": production_info.sewing_line_numbers,
            "moldingLineNumbers": production_info.molding_line_numbers,
            "cuttingStartDate": production_info.cutting_start_date,
            "cuttingEndDate": production_info.cutting_end_date,
            "sewingStartDate": production_info.sewing_start_date,
            "sewingEndDate": production_info.sewing_end_date,
            "moldingStartDate": production_info.molding_start_date,
            "moldingEndDate": production_info.molding_end_date,
            "cuttingAmount": cutting_amount,
            "sewing_amount": sewing_amount,
            "molding_amount": molding_amount,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getproductioninfo", methods=["GET"]
)
def get_production_info():
    # 参考scheduleView.vue 441行
    team = request.args.get("team")
    # 成型号
    number = request.args.get("number")
    if team == "cutting":
        status = 23
        line_usage = OrderShoeProductionInfo.cutting_line_numbers
        start_date = OrderShoeProductionInfo.cutting_start_date
        end_date = OrderShoeProductionInfo.cutting_end_date
    elif team == "preSewing":
        status = 29
        line_usage = OrderShoeProductionInfo.pre_sewing_line_numbers
        start_date = OrderShoeProductionInfo.pre_sewing_start_date
        end_date = OrderShoeProductionInfo.pre_sewing_end_date
    elif team == "sewing":
        status = 31
        line_usage = OrderShoeProductionInfo.sewing_line_numbers
        start_date = OrderShoeProductionInfo.sewing_start_date
        end_date = OrderShoeProductionInfo.sewing_end_date
    elif team == "molding":
        status = 39
        line_usage = OrderShoeProductionInfo.molding_line_numbers
        start_date = OrderShoeProductionInfo.molding_start_date
        end_date = OrderShoeProductionInfo.molding_end_date
    else:
        return {"message": "failed"}, 400
    response = (
        db.session.query(
            Order,
            Shoe,
            func.sum(OrderShoeBatchInfo.total_amount),
            line_usage,
            start_date,
            end_date,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            OrderShoeProductionInfo,
            OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .filter(OrderShoeStatus.current_status == status)
        .group_by(Order.order_id, OrderShoe.order_shoe_id)
        .all()
    )

    result = []
    for row in response:
        (
            order,
            shoe,
            total_amount,
            line_usage_info,
            start_date_val,
            end_date_val,
        ) = row
        val = len(line_usage_info.split(","))
        obj = {
            "startDate": start_date_val,
            "endDate": end_date_val,
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "shoeRId": shoe.shoe_rid,
            "number": total_amount,
            "lineUsage": val,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/editproductionschedule", methods=["PATCH"]
)
def edit_production_schedule():
    data = request.get_json()
    entity = OrderShoeProductionInfo.query.filter(
        OrderShoeProductionInfo.order_shoe_id == data["orderShoeId"]
    ).first()
    entity.cutting_line_numbers = data["cuttingInfo"]["line_numbers"]
    entity.is_cutting_outsourced = data["cuttingInfo"]["isOutsourced"]
    entity.start_date = data["cuttingInfo"]["startDate"]
    entity.end_date = data["cuttingInfo"]["endDate"]

    entity.cutting_line_numbers = data["sewingInfo"]["line_numbers"]
    entity.is_cutting_outsourced = data["sewingInfo"]["isOutsourced"]
    entity.start_date = data["sewingInfo"]["startDate"]
    entity.end_date = data["sewingInfo"]["endDate"]

    entity.cutting_line_numbers = data["moldingInfo"]["line_numbers"]
    entity.is_cutting_outsourced = data["moldingInfo"]["isOutsourced"]
    entity.start_date = data["moldingInfo"]["startDate"]
    entity.end_date = data["moldingInfo"]["endDate"]
    db.session.commit()
    return jsonify({"message": "success"})


# TODO
@production_manager_bp.route(
    "/production/productionmanager/submitproductionschedule", methods=["PATCH"]
)
def submit_production_schedule():
    # pass to event processor
    return "hello world"


@production_manager_bp.route(
    "/production/productionmanager/getallproductionlinesinfo", methods=["GET"]
)
def get_all_production_lines_info():
    order_shoe_id = request.args.get()
    return


@production_manager_bp.route(
    "/production/productionmanager/getorderproductiondetail", methods=["GET"]
)
def get_order_production_detail():
    order_id = request.args.get("orderId")
    response = (
        db.session.query(OrderShoe, Shoe, OrderShoeStatus)
        .join(Order, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(Order.order_id == order_id)
        .filter(
            OrderShoeStatus.current_status >= 18, OrderShoeStatus.current_status <= 41
        )
        .all()
    )
    result = {}
    order_shoe_list = []
    # order_shoe_status有两条record
    for row in response:
        order_shoe, shoe, order_shoe_status = row
        order_shoe_list.append(order_shoe.order_shoe_id)
        if order_shoe_status.current_status == 41:
            status = "已完成"
        else:
            status = "生产中"
        obj = {
            "imgUrl": shoe.shoe_image_url,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "status": status,
        }
        result[order_shoe.order_shoe_id] = {"orderShoeInfo": obj, "batchInfo": []}

    # 加鞋型详情，只返回进度
    response = OrderShoeBatchInfo.query.filter(
        OrderShoeBatchInfo.order_shoe_id.in_(order_shoe_list)
    ).all()
    for row in response:
        obj = {
            "name": row.name,
            "batchAmount": row.total_amount,
            "cuttingAmount": row.cutting_amount,
            "preSewingAmount": row.pre_sewing_amount,
            "sewingAmount": row.sewing_amount,
            "moldingAmount": row.molding_amount,
        }
        result[row.order_shoe_id]["batchInfo"].append(row)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getlogisticsoverview", methods=["GET"]
)
def get_logistics_overview():
    response = (
        db.session.query(Order, Customer)
        .join(Customer, Order.customer_id == Customer.customer_id)
        .join(OrderStatus, Order.order_id == OrderStatus.order_id)
        .filter(OrderStatus.order_current_status == IN_PRODUCTION_ORDER_NUMBER)
        .all()
    )
    result = []
    for row in response:
        order, customer = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "endDate": order.end_date,
            "customerName": customer.customer_name,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getorderlogisticsinfo", methods=["GET"]
)
# TODO
def get_order_logistics_info():
    order_id = request.args.get("orderId")
    db.session.query(Order, OrderShoe, MaterialStorage)
    return "hello world"


@production_manager_bp.route(
    "/production/productionmanager/getfinishednodes", methods=["GET"]
)
def get_finished_nodes():
    response = (
        db.session.query(Order, OrderShoe, Shoe, OrderShoeStatusReference)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(
            OrderShoeStatusReference,
            OrderShoeStatusReference.status_id == OrderShoeStatus.current_status,
        )
        .filter(
            OrderShoeStatus.current_status.in_([18, 24, 30, 32, 40, 41])
        )  # TODO create constants for it
        .all()
    )
    result = []
    for row in response:
        order, order_shoe, shoe, reference = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "nodeName": reference.status_name,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getordershoebatchinfo", methods=["GET"]
)
def get_order_shoe_batch_info():
    order_shoe_id = request.args.get("orderShoeId")
    node_name = request.args.get("nodeName")
    response = (
        db.session.query(Color, OrderShoeBatchInfo)
        .join(OrderShoe, OrderShoe.order_shoe_id == OrderShoeBatchInfo.order_shoe_id)
        .join(Color, Color.color_id == OrderShoeBatchInfo.color_id)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .all()
    )
    result = []
    for row in response:
        color, batch_info = row
        amount = 0
        # 分状态
        if node_name == "裁断完成":
            amount = batch_info.cutting_amount
        elif node_name == "针车预备完成":
            amount = batch_info.pre_sewing_amount
        elif node_name == "针车完成":
            amount = batch_info.sewing_amount
        elif node_name == "成型完成" or node_name == "生产完成":
            amount = batch_info.molding_amount
        obj = {
            "color": color.color_name,
            "batchInfoName": batch_info.name,
            "totalAmount": batch_info.total_amount,
            "finishedAmount": amount,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/editordershoestatus", methods=["PATCH"]
)
# TODO
def edit_order_shoe_status():
    # create event, pass to event processor
    order_shoe_id = request.args.get("orderShoeId")
    return "hello world"


@production_manager_bp.route(
    "/production/productionmanager/getorderoutsourceoverview", methods=["GET"]
)
def get_order_outsource_overview():
    response = (
        db.session.query(
            Order,
            OrderShoe,
            Shoe,
            Customer,
            OrderShoeProductionInfo.is_cutting_outsourced,
            OrderShoeProductionInfo.is_sewing_outsourced,
            OrderShoeProductionInfo.is_molding_outsourced,
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(
            OrderShoeProductionInfo,
            OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .filter(OrderStatus.order_current_status == IN_PRODUCTION_ORDER_NUMBER)
        .all()
    )
    result = []
    for row in response:
        (
            order,
            order_shoe,
            customer,
            shoe,
            is_cutting_outsourced,
            is_sewing_outsourced,
            is_molding_outsourced,
        ) = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "customerName": customer.customer_name,
            "orderShoeId": order_shoe.order_shoe_id,
            "ShoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "isCuttingOutsourced": is_cutting_outsourced,
            "isSewingOutsourced": is_sewing_outsourced,
            "isMoldingOutsourced": is_molding_outsourced,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getordershoebatchinfoforoutsource", methods=["GET"]
)
def get_order_shoe_batch_info_for_outsource():
    order_shoe_id = request.args.get("orderShoeId")
    response = (
        db.session.query(OrderShoeBatchInfo, Color)
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(Color, Color.color_id == OrderShoeBatchInfo.color_id)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
    )
    result = []
    for row in response:
        batch_info, color = row
        obj = {
            "color": color.color_name,
            "batch_name": batch_info.name,
            "size35Amount": batch_info.size_35_amount,
            "size36Amount": batch_info.size_36_amount,
            "size37Amount": batch_info.size_37_amount,
            "size38Amount": batch_info.size_38_amount,
            "size39Amount": batch_info.size_39_amount,
            "size40Amount": batch_info.size_40_amount,
            "size41Amount": batch_info.size_41_amount,
            "size42Amount": batch_info.size_42_amount,
            "size43Amount": batch_info.size_43_amount,
            "size44Amount": batch_info.size_44_amount,
            "size45Amount": batch_info.size_45_amount,
            "size46Amount": batch_info.size_46_amount,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getordershoeoutsourceinfo", methods=["GET"]
)
def get_order_shoe_outsource_info():
    order_shoe_id = request.args.get("orderShoeId")
    response = (
        (
            db.session.query(OutsourceInfo, OutsourceFactory)
            .join(OrderShoe, OrderShoe.order_shoe_id == OutsourceInfo.order_shoe_id)
            .join(
                OutsourceFactory,
                OutsourceFactory.factory_id == OutsourceInfo.factory_id,
            )
        )
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .all()
    )
    result = []
    for row in response:
        outsource_info, factory = row
        obj = {
            "outsourceInfoId": outsource_info.outsource_info_id,
            "outsourceType": outsource_info.outsource_type,
            "outsourceFactory": factory.factory_name,
            "outsourceAmount": outsource_info.outsource_amount,
            "outsourceStartDate": outsource_info.start_date,
            "outsourceEndDate": outsource_info.end_date,
            "approvalStatus": outsource_info.approval_status,
            "deadlineDate": outsource_info.deadline_date,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/storeoutsourceforordershoe", methods=["POST"]
)
def store_outsource_for_order_shoe():
    data = request.get_json()
    entity = OutsourceInfo(
        outsource_type=data["type"],
        factory_id=data["factoryId"],
        outsource_start_date=data["outsourceStartDate"],
        outsource_end_date=data["outsourceEndDate"],
        semifinished_required=data["semifinishedRequired"],
        semifinished_estimated_outbound_date=data["semifinishedEstimatedOutboundDate"],
        deadline_date=data["deadlineDate"],
        material_delivery_date=data["materialDeliveryDate"],
        approval_status=False,
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify({"message": "success"})


@production_manager_bp.route(
    "/production/productionmanager/editoutsourceforordershoe", methods=["PATCH"]
)
def edit_outsource_for_order_shoe():
    data = request.get_json()
    entity = OutsourceInfo.query.filter_by(
        outsource_info_id=data["outsourceInfoId"]
    ).first()
    entity.outsource_type = data["type"]
    entity.factory_id = data["factoryId"]
    entity.outsource_start_date = data["outsourceStartDate"]
    entity.outsource_end_date = data["outsourceEndDate"]
    entity.semifinished_required = data["semifinishedRequired"]
    entity.semifinished_estimated_outbound_date = data[
        "semifinishedEstimatedOutboundDate"
    ]
    entity.deadline_date = data["deadlineDate"]
    entity.material_delivery_date = data["materialDeliveryDate"]
    db.session.add(entity)
    db.session.commit()
    return jsonify({"message": "success"})


@production_manager_bp.route(
    "/production/productionmanager/submitoutsourceinfo", methods=["PATCH"]
)
# TODO
def submit_outsource_info():
    data = request.get_json()
    # create event, pass to event processor
    return jsonify({"message": "success"})


@production_manager_bp.route(
    "/production/productionmanager/getalloutsourcefactories", methods=["GET"]
)
def get_all_outsource_factories():
    response = OutsourceFactory.query.all()
    result = []
    for row in response:
        result.append({"factoryId": row.factory_id, "factoryName": row.factory_name})
    return result


@production_manager_bp.route(
    "/production/productionmanager/getoutsourcesemifinishedshipping", methods=["GET"]
)
def get_outsource_semifinished_shipping():
    order_shoe_id = request.args.get("orderShoeId")
    outsource_info_id = request.args.get("outsourceInfoId")
    response = (
        db.session.query(SemifinishedShoeStorage)
        .join(
            SemifinishedShoeStorage,
            SemifinishedShoeStorage.order_shoe_id == OutsourceInfo.order_shoe_id,
        )
        .filter(
            SemifinishedShoeStorage.order_shoe_id == order_shoe_id,
            OutsourceInfo.outsource_info_id == outsource_info_id,
        )
        .all()
    )
    result = []
    for row in response:
        obj = {
            "semifinishedAmount": row.semifinished_amount,
            "semifinishedStatus": row.semifinished_status,
            "semifinishedEstimatedOutboundDate": row.semifinished_estimated_outbound_date,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getoutsourcematerialshipping", methods=["GET"]
)
def get_outsource_material_shipping():
    order_shoe_id = request.args.get("orderShoeId")
    outsource_info_id = request.args.get("outsourceInfoId")
    # 发货数量：material_storage.current_amount
    response = (
        db.session.query(MaterialStorage, Material, Color)
        .join(
            MaterialStorage,
            MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(Material, Material.material_id == MaterialStorage.material_id)
        .join(Color, Color.color_id == Material.color)
        .filter(
            MaterialStorage.order_shoe_id == order_shoe_id,
            OutsourceInfo.outsource_info_id == outsource_info_id,
        )
        .all()
    )
    result = []
    for row in response:
        material_storage, material, color = row
        obj = {
            "materialName": material.material_name,
            "materialColor": color.color_name,
            "materialUnit": material.material_unit,
            "outsourceStatus": material_storage.material_outsource_status,
            "outboundAmount": material_storage.current_amount,
            "outsouceOutboundDate": material_storage.material_outsource_outbound_date,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getallquantityreportsoverview", methods=["GET"]
)
def get_all_quantity_reports_overview():
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    yesterday_date = yesterday.date()
    response = (
        db.session.query(
            Order,
            OrderShoe,
            Shoe,
            QuantityReport,
            func.sum(QuantityReportItem.amount),
        )
        .join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(QuantityReport, QuantityReport.order_shoe_id == OrderShoe.order_shoe_id)
        .join(
            QuantityReportItem, QuantityReportItem.report_id == QuantityReport.report_id
        )
        .filter(
            OrderShoeStatus.current_status.in_([23, 29, 31, 39]),
            QuantityReport.submission_date == yesterday_date,
        )
        .all()
    )
    result = []
    for row in response:
        order, order_shoe, shoe, report, amount = row
        amounts = {"cutting_amount": 0, "sewing_amount": 0, "molding_amount": 0}
        if report.team == ProductionTeam.CUTTING:
            amounts["cutting_amount"] = amount
        elif report.team == ProductionTeam.SEWING:
            amounts["sewing_amount"] = amount
        elif report.team == ProductionTeam.MOLDING:
            amounts["molding_amount"] = amount
        obj = {
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "yesterdayCuttingAmount": amounts["cutting_amount"],
            "yesterdaySewingAmount": amounts["sewing_amount"],
            "yesterdayMoldingAmount": amounts["molding_amount"],
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getsubmittedquantityreports", methods=["GET"]
)
def get_submitted_quantity_reports():
    order_shoe_id = request.args.get("orderShoeId")
    response = (
        db.session.query(OrderShoeProductionInfo, QuantityReport)
        .join(
            OrderShoeProductionInfo,
            OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(QuantityReport, OrderShoe.order_shoe_id == QuantityReport.order_shoe_id)
        .filter(
            OrderShoeProductionInfo,
            OrderShoeProductionInfo.order_shoe_id == order_shoe_id,
        )
        .all()
    )
    result = []
    for row in response:
        production_info, report = row
        if report.team == ProductionTeam.CUTTING:
            start_date = production_info.cutting_start_date
            end_date = production_info.cutting_end_date
        elif report.team == ProductionTeam.PRE_SEWING:
            start_date = production_info.pre_sewing_start_date
            end_date = production_info.pre_sewing_start_date
        elif report.team == ProductionTeam.SEWING:
            start_date = production_info.sewing_start_date
            end_date = production_info.sewing_start_date
        else:
            start_date = production_info.molding_start_date
            end_date = production_info.molding_end_date
        obj = {
            "reportDate": report.creation_date,
            "startDate": start_date,
            "endDate": end_date,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getpricereportapprovaloverview", methods=["GET"]
)
def get_price_report_approval_overview():
    response = (
        db.session.query(Order, OrderShoe, Shoe, OrderShoeStatus)
        .join(
            OrderShoe,
            Order.order_id == OrderShoe.order_id,
        )
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(
            OrderShoeStatus.current_status.in_([22, 29, 39]),
        )
        .all()
    )
    result = []
    for row in response:
        order, order_shoe, shoe, status_obj = row
        if status_obj.current_value == 22:
            team = "裁断"
        elif status_obj.current_value == 29:
            team = "针车"
        else:
            team = "成型"
        obj = {
            "orderId": order.orderId,
            "orderRId": order.orderRId,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "team": team,
        }
        result.append(obj)
    return result


@production_manager_bp.route(
    "/production/productionmanager/getproductionlinetobeapprovedinfo", methods=["GET"]
)
def get_production_line_to_be_approved_info():
    order_shoe_id = request.args.get("orderShoeId")
    team = request.args.get("team")
    response = (
        db.session.query(OrderShoeProductionInfo, UnitPriceReport)
        .join(
            UnitPriceReport,
            OrderShoeProductionInfo.order_shoe_id == UnitPriceReport.order_shoe_id,
        )
        .filter(
            OrderShoeProductionInfo.order_shoe_id == order_shoe_id,
            UnitPriceReport.team == team,
        )
        .first()
    )
    production_info, report = response
    if team == ProductionTeam.CUTTING:
        start_date = production_info.cutting_start_date
        end_date = production_info.cutting_end_date
    elif team == ProductionTeam.PRE_SEWING:
        start_date = production_info.pre_sewing_start_date
        end_date = production_info.pre_sewing_start_date
    elif team == ProductionTeam.SEWING:
        start_date = production_info.sewing_start_date
        end_date = production_info.sewing_start_date
    else:
        start_date = production_info.molding_start_date
        end_date = production_info.molding_end_date
    result = {
        "productionStartDate": start_date,
        "productionEndDate": end_date,
        "reportId": report.report_id,
    }
    return result


@production_manager_bp.route(
    "/production/productionmanager/approvepricereport", methods=["PATCH"]
)
def approve_price_report():
    data = request.get_json()
    report_id_arr = data["reportIdArr"]
    processor = EventProcessor()
    for report_id in report_id_arr:
        report = db.session.query(UnitPriceReport).get(report_id)
        report.status = 2
    event = Event(
        staff_id=1,
        handle_time=datetime.now(),
        operation_id=PRICE_REPORT_REFERENCE[report.team]["operation_id"],
        event_order_id=data["orderId"],
        event_order_shoe_id=data["orderShoeId"],
    )
    result = processor.processEvent(event)
    if not result:
        return jsonify({"message": "failed"}), 400
    db.session.add(event)
    db.session.commit()
    return jsonify({"message": "success"})


@production_manager_bp.route(
    "/production/productionmanager/rejectpricereport", methods=["PATCH"]
)
#TODO
def reject_price_report():
    data = request.get_json()
    report_id_arr = data["reportIdArr"]
    for report_id in report_id_arr:
        report = db.session.query(UnitPriceReport).get(report_id)
        report.status = 0
        report.rejection_reason = data["rejectionReason"]
    db.session.commit()
    return jsonify({"message": "success"})

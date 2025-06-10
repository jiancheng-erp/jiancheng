from datetime import datetime

from api_utility import format_date
from app_config import db
from constants import END_OF_PRODUCTION_NUMBER
from flask import Blueprint, jsonify, request
from models import *
from sqlalchemy import func, literal
from logger import logger
quantity_report_bp = Blueprint("quantity_report_bp", __name__)


def check_report_status(number):
    if number == 0:
        status_name = "未提交"
    elif number == 1:
        status_name = "已提交"
    elif number == 2:
        status_name = "已审批"
    else:
        status_name = "被驳回"
    return status_name


@quantity_report_bp.route("/production/getquantityreporttasks", methods=["GET"])
def get_quantity_report_tasks():
    page = request.args.get("page", type=int)
    page_size = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    teams = request.args.get("teams").split(",")
    queries = []
    for team in teams:
        teamId = -1
        if team == "裁断":
            start_date = OrderShoeProductionInfo.cutting_start_date
            end_date = OrderShoeProductionInfo.cutting_end_date
            amount = OrderShoeType.cutting_amount
            teamId = 0
        elif team == "针车预备":
            start_date = OrderShoeProductionInfo.pre_sewing_start_date
            end_date = OrderShoeProductionInfo.pre_sewing_end_date
            amount = OrderShoeType.pre_sewing_amount
            teamId = 1
        elif team == "针车":
            start_date = OrderShoeProductionInfo.sewing_start_date
            end_date = OrderShoeProductionInfo.sewing_end_date
            amount = OrderShoeType.sewing_amount
            teamId = 1
        elif team == "成型":
            start_date = OrderShoeProductionInfo.molding_start_date
            end_date = OrderShoeProductionInfo.molding_end_date
            amount = OrderShoeType.molding_amount
            teamId = 2
        else:
            return jsonify({"message": "invalid team name"}), 400
        production_amount_table = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.sum(OrderShoeProductionAmount.total_production_amount).label(
                    "total_amount"
                ),
            )
            .join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
            .join(
                OrderShoeProductionAmount,
                OrderShoeProductionAmount.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(OrderShoeProductionAmount.production_team == teamId)
            .group_by(OrderShoe.order_shoe_id)
        ).subquery()
        report_amount_table = (
            db.session.query(
                OrderShoe.order_shoe_id,
                func.sum(amount).label("report_amount"),
            )
            .join(
                OrderShoeType,
                OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .group_by(OrderShoe.order_shoe_id)
        ).subquery()
        query = (
            db.session.query(
                Order,
                OrderShoe,
                Shoe,
                Customer,
                start_date.label("start_date"),
                end_date.label("end_date"),
                literal(team).label("team"),
                report_amount_table.c.report_amount,
                production_amount_table.c.total_amount,
            )
            .join(OrderShoe, OrderShoe.order_id == Order.order_id)
            .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
            .join(Customer, Customer.customer_id == Order.customer_id)
            .join(
                OrderShoeProductionInfo,
                OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                OrderShoeStatus,
                OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .outerjoin(
                report_amount_table,
                report_amount_table.c.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .join(
                production_amount_table,
                production_amount_table.c.order_shoe_id == OrderShoe.order_shoe_id,
            )
            .filter(
                OrderShoeStatus.current_status >= 23,
            )
        )
        queries.append(query)
    union_query = queries[0]
    for i in range(1, len(queries)):
        union_query = union_query.union(queries[i])
    if order_rid and order_rid != "":
        union_query = union_query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        union_query = union_query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    count_result = union_query.distinct().count()
    response = (
        union_query.distinct().limit(page_size).offset((page - 1) * page_size).all()
    )
    result = []
    for row in response:
        (
            order,
            order_shoe,
            shoe,
            customer,
            start_date_res,
            end_date_res,
            team,
            produced_amount,
            total_amount,
        ) = row
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "productionStartDate": format_date(start_date_res),
            "productionEndDate": format_date(end_date_res),
            "customerName": customer.customer_name,
            "team": team,
            "producedAmount": 0 if not produced_amount else produced_amount,
            "totalAmount": total_amount,
        }
        result.append(obj)
    return {"result": result, "totalLength": count_result}


@quantity_report_bp.route("/production/createquantityreport", methods=["POST"])
def create_quantity_report():
    data = request.get_json()
    report = QuantityReport(
        order_shoe_id=data["orderShoeId"],
        creation_date=data["creationDate"],
        status=0,
        team=data["team"],
    )
    db.session.add(report)
    db.session.flush()
    order_shoe_type_response = (
        db.session.query(
            OrderShoeType.order_shoe_type_id
        )
        .join(
            OrderShoe,
            OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .filter(
            OrderShoeType.order_shoe_id == data["orderShoeId"],
        )
        .all()
    )
    production_line_response = (
        db.session.query(
            ProductionLine.production_line_id
        )
        .filter(
            ProductionLine.production_team == data["team"],
        )
        .all()
    )
    result = []
    for row in order_shoe_type_response:
        order_shoe_type_id = row[0]
        for row2 in production_line_response:
            production_line_id = row2[0]
            item = QuantityReportItem(
                quantity_report_id=report.report_id,
                order_shoe_type_id=order_shoe_type_id,
                production_line_id=production_line_id,
            )
            result.append(item)
    db.session.add_all(result)
    db.session.commit()
    return {"message": "success"}


@quantity_report_bp.route("/production/editquantityreportdetail", methods=["PUT"])
def edit_quantity_report_detail():
    data = request.get_json()
    report_id = data["reportId"]
    detail_arr = data["data"]
    report = QuantityReport.query.filter_by(report_id=report_id).first()
    items_list = QuantityReportItem.query.filter_by(quantity_report_id=report_id).all()
    amount_entries = {}
    for item in detail_arr:
        for amount_obj in item["productionLinesAmount"]:
            key = (item["orderShoeTypeId"], amount_obj["productionLineId"])
            amount_entries[key] = amount_obj["reportAmount"]
    total_report_amount = 0
    for row in items_list:
        if (row.order_shoe_type_id, row.production_line_id) in amount_entries:
            row.report_amount = amount_entries[
                (row.order_shoe_type_id, row.production_line_id)
            ]
            total_report_amount += row.report_amount
    report.total_report_amount = total_report_amount
    db.session.commit()
    return jsonify({"message": "success"})


@quantity_report_bp.route("/production/submitquantityreport", methods=["PATCH"])
def submit_quantity_report():
    data = request.get_json()
    report = QuantityReport.query.get(data["reportId"])
    report.status = 1
    report.submission_date = format_date(datetime.now())
    db.session.commit()
    return jsonify({"message": "success"})


@quantity_report_bp.route("/production/deletequantityreport", methods=["DELETE"])
def delete_quantity_report():
    report_id = request.args.get("reportId")
    items = QuantityReportItem.query.filter_by(quantity_report_id=report_id).all()
    for item in items:
        db.session.delete(item)
    row = QuantityReport.query.get(report_id)
    db.session.delete(row)
    db.session.commit()
    return jsonify({"message": "success"})


@quantity_report_bp.route("/production/getallquantityreports", methods=["GET"])
def get_all_quantity_report():
    order_shoe_id = request.args.get("orderShoeId")
    team = request.args.get("team")
    response = QuantityReport.query.filter_by(
        order_shoe_id=order_shoe_id, team=team
    ).all()
    result = []
    for row in response:
        result.append(
            {
                "reportId": row.report_id,
                "creationDate": format_date(row.creation_date),
                "submissionDate": format_date(row.submission_date),
                "status": check_report_status(row.status),
                "rejectionReason": row.rejection_reason,
            }
        )
    return result


@quantity_report_bp.route("/production/getquantityreportdetail", methods=["GET"])
def get_quantity_report_detail():
    report_id = request.args.get("reportId")
    # 0: 裁断，1：针车预备，2：针车，3：成型
    team = request.args.get("team", type=int)
    mapping = {0: 0, 1: 1, 2: 1, 3: 2}
    response = (
        db.session.query(
            OrderShoeType,
            OrderShoeProductionAmount,
            Color,
            QuantityReportItem,
            ProductionLine,
        )
        .join(
            OrderShoeProductionAmount,
            OrderShoeProductionAmount.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .join(ShoeType, ShoeType.shoe_type_id == OrderShoeType.shoe_type_id)
        .join(Color, Color.color_id == ShoeType.color_id)
        .join(
            QuantityReportItem,
            QuantityReportItem.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .join(
            ProductionLine,
            QuantityReportItem.production_line_id == ProductionLine.production_line_id,
        )
        .filter(
            QuantityReportItem.quantity_report_id == report_id,
            OrderShoeProductionAmount.production_team == mapping[team],
        )
        .all()
    )
    result = []
    meta_data_mapping = {}
    for row in response:
        order_shoe_type, production_amount, color, report_item, production_line = row
        if production_amount.total_production_amount > 0:
            produced_amount = 0
            if team == 0:
                produced_amount = order_shoe_type.cutting_amount
            elif team == 1:
                produced_amount = order_shoe_type.pre_sewing_amount
            elif team == 2:
                produced_amount = order_shoe_type.sewing_amount
            elif team == 3:
                produced_amount = order_shoe_type.molding_amount
            if color.color_name not in meta_data_mapping:
                meta_data_mapping[color.color_name] = {
                    "orderShoeTypeId": order_shoe_type.order_shoe_type_id,
                    "colorName": color.color_name,
                    "totalAmount": production_amount.total_production_amount,
                    "producedAmount": produced_amount,
                    "remainingAmount": production_amount.total_production_amount - produced_amount,
                    "productionLinesAmount": [
                        {
                            "reportAmount": report_item.report_amount,
                            "productionLineId": production_line.production_line_id,
                            "productionLineName": production_line.production_line_name,
                        }
                    ],
                }
            else:
                meta_data_mapping[color.color_name]["productionLinesAmount"].append(
                    {
                        "reportAmount": report_item.report_amount,
                        "productionLineId": production_line.production_line_id,
                        "productionLineName": production_line.production_line_name,
                    }
                )
    for _, value in meta_data_mapping.items():
        result.append(value)
    # logger.debug(result)
    return result

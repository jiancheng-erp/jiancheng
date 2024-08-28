from datetime import datetime

from app_config import db
from constants import END_OF_PRODUCTION_NUMBER, QUANTTIY_REPORT_REFERENCE
from flask import Blueprint, jsonify, request
from models import *

quantity_report_bp = Blueprint("quantity_report_bp", __name__)


@quantity_report_bp.route("/production/createquantityreport", methods=["POST"])
def create_quantity_report():
    data = request.get_json()
    report = QuantityReport(
        order_shoe_id=data["orderShoeId"],
        creation_date=data["creationDate"],
        status=0,
        team=data["team"],
    )
    order_shoe_obj = OrderShoeStatus.query.filter_by(
        order_shoe_id=data["orderShoeId"], current_status=QUANTTIY_REPORT_REFERENCE[data["team"]]
    ).first()
    order_shoe_obj.current_status_value = 1
    db.session.add(report)
    db.session.commit()
    return {"reportId": report.report_id}


@quantity_report_bp.route("/production/editquantityreportdetail", methods=["PUT"])
def edit_quantity_report_detail():
    data = request.get_json()
    report_id = data["reportId"]
    detail_arr = data["data"]
    for row in detail_arr:
        item_obj = QuantityReportItem.query.filter_by(
            report_id=report_id, order_shoe_batch_info_id=row["orderShoeBatchInfoId"]
        ).first()
        item_obj.amount = row["amount"]
    db.session.commit()
    return jsonify({"message": "success"})


@quantity_report_bp.route("/production/submitquantityreport", methods=["PATCH"])
def submit_quantity_report():
    data = request.get_json()
    report = QuantityReport.query.get(data["reportId"])
    report.status = 1
    report.submission_date = datetime.now().strftime("%Y-%m-%d")
    db.session.commit()
    return jsonify({"message": "success"})


@quantity_report_bp.route("/production/deletequantityreport", methods=["DELETE"])
def delete_quantity_report():
    report_id = request.args.get("reportId")
    items = QuantityReportItem.query.filter_by(report_id=report_id).all()
    print(report_id)
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
                "creationDate": row.creation_date.strftime("%Y-%m-%d"),
                "status": row.status,
                "rejectionReason": row.rejection_reason,
            }
        )
    return result


@quantity_report_bp.route("/production/createquantityreportdetail", methods=["POST"])
def create_quantity_report_detail():
    data = request.get_json()
    report_id = data["reportId"]
    order_shoe_id = data["orderShoeId"]
    response = OrderShoeBatchInfo.query.filter_by(order_shoe_id=order_shoe_id).all()
    result = []
    for row in response:
        item = QuantityReportItem(
            report_id=report_id, order_shoe_batch_info_id=row.order_shoe_batch_info_id
        )
        result.append(item)
    db.session.add_all(result)
    db.session.commit()
    return {"message": "success"}


@quantity_report_bp.route("/production/getquantityreportdetail", methods=["GET"])
def get_quantity_report_detail():
    report_id = request.args.get("reportId")
    response = (
        db.session.query(OrderShoeBatchInfo, QuantityReportItem)
        .join(
            QuantityReportItem,
            QuantityReportItem.order_shoe_batch_info_id
            == OrderShoeBatchInfo.order_shoe_batch_info_id,
        )
        .filter(QuantityReportItem.report_id == report_id)
        .all()
    )
    result = []
    for row in response:
        batch_info, report_item = row
        result.append(
            {
                "orderShoeBatchInfoId": batch_info.order_shoe_batch_info_id,
                "name": batch_info.name,
                "amount": report_item.amount,
                "totalAmount": batch_info.total_amount,
                "cuttingAmount": batch_info.cutting_amount,
            }
        )
    return result


@quantity_report_bp.route(
    "/production/getallordershoesquantityreports", methods=["GET"]
)
def get_all_order_shoes_quantity_reports():
    order_id = request.args.get("orderId")
    team = request.args.get("team")
    status_val = QUANTTIY_REPORT_REFERENCE[team]
    response = (
        db.session.query(OrderShoe, Shoe)
        .join(Order, OrderShoe.order_id == Order.order_id)
        .join(
            OrderShoeStatus,
            OrderShoe.order_shoe_id == OrderShoeStatus.order_shoe_id,
        )
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(
            Order.order_id == order_id,
            OrderShoeStatus.current_status >= status_val,
            OrderShoeStatus.current_status < END_OF_PRODUCTION_NUMBER
        )
        .all()
    )
    result = {}
    for row in response:
        order_shoe, shoe = row
        result[order_shoe.order_shoe_id] = {"shoeRId": shoe.shoe_rid, "status": "", }
    return result

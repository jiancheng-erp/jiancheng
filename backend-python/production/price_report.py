import traceback
from datetime import datetime

from api_utility import format_date
from app_config import db
from constants import END_OF_PRODUCTION_NUMBER, PRICE_REPORT_REFERENCE
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request, send_file
from models import *
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert
from general_document.procedure_form import generate_excel_file
import os
from file_locations import FILE_STORAGE_PATH

price_report_bp = Blueprint("price_report_bp", __name__)


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


def report_status_to_number(status_name):
    if status_name == "未提交":
        number = 0
    elif status_name == "已提交":
        number = 1
    elif status_name == "已审批":
        number = 2
    else:
        number = 3
    return number


@price_report_bp.route("/production/getnewpricereports", methods=["GET"])
def get_new_price_reports():
    page = request.args.get("page", type=int)
    page_size = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    status_name = request.args.get("statusName")
    team = request.args.get("team")
    if team == "裁断":
        start_date = OrderShoeProductionInfo.cutting_start_date
        end_date = OrderShoeProductionInfo.cutting_end_date
    elif team == "针车":
        pre_start_date = OrderShoeProductionInfo.pre_sewing_start_date
        pre_end_date = OrderShoeProductionInfo.pre_sewing_end_date
        start_date = OrderShoeProductionInfo.sewing_start_date
        end_date = OrderShoeProductionInfo.sewing_end_date
    elif team == "成型":
        start_date = OrderShoeProductionInfo.molding_start_date
        end_date = OrderShoeProductionInfo.molding_end_date
    else:
        return jsonify({"message": "invalid team name"}), 400
    if team == "针车":
        query = db.session.query(
            Order,
            OrderShoe,
            Shoe,
            Customer,
            UnitPriceReport.status,
            UnitPriceReport.rejection_reason,
            pre_start_date,
            pre_end_date,
            start_date,
            end_date,
        )
    else:
        query = db.session.query(
            Order,
            OrderShoe,
            Shoe,
            Customer,
            UnitPriceReport.status,
            UnitPriceReport.rejection_reason,
            start_date,
            end_date,
        )
    query = (
        query.join(OrderShoe, OrderShoe.order_id == Order.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(Customer, Customer.customer_id == Order.customer_id)
        .join(
            OrderShoeProductionInfo,
            OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .join(UnitPriceReport, UnitPriceReport.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(
            OrderShoeStatus.current_status
            >= PRICE_REPORT_REFERENCE[team]["status_number"],
            UnitPriceReport.team == team,
        )
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if status_name and status_name != "":
        query = query.filter(
            UnitPriceReport.status == report_status_to_number(status_name)
        )
    count_result = query.distinct().count()
    response = query.distinct().limit(page_size).offset((page - 1) * page_size).all()
    result = []
    for row in response:
        if team == "针车":
            (
                order,
                order_shoe,
                shoe,
                customer,
                status,
                rejection_reason,
                pre_start_date_res,
                pre_end_date_res,
                start_date_res,
                end_date_res,
            ) = row
        else:
            (
                order,
                order_shoe,
                shoe,
                customer,
                status,
                rejection_reason,
                start_date_res,
                end_date_res,
            ) = row
        status_name = check_report_status(status)
        obj = {
            "orderId": order.order_id,
            "orderRId": order.order_rid,
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "productionStartDate": format_date(start_date_res),
            "productionEndDate": format_date(end_date_res),
            "customerName": customer.customer_name,
            "statusName": status_name,
            "rejectionReason": rejection_reason,
        }
        if team == "针车":
            obj["preSewingProductionStartDate"] = format_date(pre_start_date_res)
            obj["preSewingProductionEndDate"] = format_date(pre_end_date_res)
        result.append(obj)
    return {"result": result, "totalLength": count_result}


@price_report_bp.route("/production/storepricereportdetail", methods=["POST"])
def store_price_report_detail():
    data = request.get_json()
    report_id = data["reportId"]
    new_data = data["newData"]
    row_id_arr = []
    for row in new_data:
        obj = {
            "report_id": report_id,
            "row_id": row["rowId"],
            "procedure_name": row["procedure"],
            "price": row["price"],
            "note": row["note"],
        }
        row_id_arr.append(row["rowId"])
        insert_stmt = insert(UnitPriceReportDetail).values(**obj)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            report_id=insert_stmt.inserted.report_id,
            row_id=insert_stmt.inserted.row_id,
            procedure_name=insert_stmt.inserted.procedure_name,
            price=insert_stmt.inserted.price,
            note=insert_stmt.inserted.note,
        )
        db.session.execute(on_duplicate_key_stmt)

    UnitPriceReportDetail.query.filter(
        UnitPriceReportDetail.report_id == report_id,
        ~UnitPriceReportDetail.row_id.in_(row_id_arr),
    ).delete()

    # get order_shoe status
    response = (
        db.session.query(UnitPriceReport, OrderShoeStatus)
        .join(
            OrderShoeStatus,
            UnitPriceReport.order_shoe_id == OrderShoeStatus.order_shoe_id,
        )
        .filter(UnitPriceReport.report_id == report_id)
        .all()
    )

    for row in response:
        _, status_obj = row
        status_obj.current_status_value = 1

    db.session.commit()
    return jsonify({"message": "success"})


@price_report_bp.route("/production/submitpricereport", methods=["POST"])
def submit_price_report():
    data = request.get_json()
    report_id_arr = data["reportIdArr"]
    processor: EventProcessor = current_app.config["event_processor"]
    for report_id in report_id_arr:
        report = db.session.query(UnitPriceReport).get(report_id)
        report.submission_date = format_date(datetime.now())
        report.status = 1
    try:
        for operation in PRICE_REPORT_REFERENCE[report.team]["operation_id"]:
            event = Event(
                staff_id=1,
                handle_time=datetime.now(),
                operation_id=operation,
                event_order_id=data["orderId"],
                event_order_shoe_id=data["orderShoeId"],
            )
            processor.processEvent(event)
    except Exception as e:
        print(e)
        return jsonify({"message": "failed"}), 400
    db.session.add(event)
    db.session.commit()
    return jsonify({"message": "success"})


@price_report_bp.route("/production/getpricereportdetail", methods=["GET"])
def get_price_report_detail():
    report_id = request.args.get("reportId")
    response = (
        db.session.query(UnitPriceReportDetail)
        .join(
            UnitPriceReport,
            UnitPriceReport.report_id == UnitPriceReportDetail.report_id,
        )
        .filter(UnitPriceReport.report_id == report_id)
        .order_by(UnitPriceReportDetail.row_id)
        .all()
    )
    result = []
    for row in response:
        report_detail = row
        result.append(
            {
                "rowId": report_detail.row_id,
                "procedure": report_detail.procedure_name,
                "price": report_detail.price,
                "note": report_detail.note,
            }
        )
    return result


@price_report_bp.route("/production/getpricereportdetailbyordershoeid", methods=["GET"])
def get_price_report_detail_by_order_shoe_id():
    order_shoe_id = request.args.get("orderShoeId")
    team = request.args.get("team")
    status = request.args.get("status", type=int)
    query = db.session.query(UnitPriceReport).filter(
        UnitPriceReport.order_shoe_id == order_shoe_id, UnitPriceReport.team == team
    )
    if status:
        query = query.filter(UnitPriceReport.status == status)
    report = query.first()
    if not report:
        return jsonify({"message": "Report not found"}), 400
    status_name = check_report_status(report.status)
    meta_data = {
        "reportId": report.report_id,
        "statusName": status_name,
        "rejectionReason": report.rejection_reason,
    }
    response = (
        db.session.query(UnitPriceReportDetail)
        .outerjoin(
            UnitPriceReport,
            UnitPriceReport.report_id == UnitPriceReportDetail.report_id,
        )
        .filter(UnitPriceReportDetail.report_id == report.report_id)
        .order_by(UnitPriceReportDetail.row_id)
        .all()
    )
    result = []
    detail = []
    for row in response:
        report_detail = row
        detail.append(
            {
                "rowId": report_detail.row_id,
                "procedure": report_detail.procedure_name,
                "price": report_detail.price,
                "note": report_detail.note,
            }
        )
    result = {"metaData": meta_data, "detail": detail}
    return result


@price_report_bp.route("/production/getallprocedures", methods=["GET"])
def get_all_procedures():
    teams = request.args.get("teams").split(",")
    procedure_name = request.args.get("procedureName")
    query = ProcedureReference.query.filter(ProcedureReference.team.in_(teams))
    if procedure_name and procedure_name != "":
        query = query.filter(
            ProcedureReference.procedure_name.ilike(f"%{procedure_name}%")
        )
    response = query.all()
    result = []
    for row in response:
        result.append(
            {
                "procedureId": row.procedure_id,
                "procedureName": row.procedure_name,
                "price": row.current_price,
                "team": row.team,
            }
        )
    return result


@price_report_bp.route("/production/addnewprocedure", methods=["POST"])
def add_new_procedures():
    data = request.get_json()
    obj = ProcedureReference(
        procedure_name=data["name"],
        team=data["team"],
        current_price=float(data["price"]),
    )
    db.session.add(obj)
    db.session.commit()
    return jsonify({"message": "添加成功"})


@price_report_bp.route("/production/editprocedure", methods=["PUT"])
def edit_procedure():
    data = request.get_json()
    for row in data:
        entity = db.session.query(ProcedureReference).get(row["procedureId"])
        entity.procedure_name = row["procedureName"]
        entity.team = row["team"]
        entity.current_price = row["price"]
    db.session.commit()
    return jsonify({"message": "编辑成功"})


@price_report_bp.route("/production/deleteprocedure", methods=["DELETE"])
def delete_procedure():
    data = request.get_json()
    entity = db.session.query(ProcedureReference).get(data["procedureId"])
    db.session.delete(entity)
    db.session.commit()
    return jsonify({"message": "删除成功"})


@price_report_bp.route("/production/savetemplate", methods=["PUT"])
def save_template():
    data = request.get_json()
    shoe_id = data["shoeId"]
    team = data["team"]
    report_rows = data["reportRows"]
    # search template
    template = (
        db.session.query(UnitPriceReportTemplate)
        .filter_by(shoe_id=shoe_id, team=team)
        .first()
    )
    if template:
        # delete old rows
        db.session.query(ReportTemplateDetail).filter_by(
            report_template_id=template.template_id
        ).delete()
    else:
        template = UnitPriceReportTemplate(shoe_id=shoe_id, team=team)
        db.session.add(template)
        db.session.flush()
    arr = []
    # insert new rows
    for row in report_rows:
        print(template.template_id)
        entity = ReportTemplateDetail(
            report_template_id=template.template_id,
            row_id=row["rowId"],
            procedure_name=row["procedure"],
            price=row["price"],
        )
        arr.append(entity)
    db.session.add_all(arr)
    db.session.commit()
    return jsonify({"message": "保存成功"})


@price_report_bp.route("/production/loadtemplate", methods=["GET"])
def load_template():
    shoe_id = request.args.get("shoeId")
    team = request.args.get("team")
    response = (
        db.session.query(ReportTemplateDetail)
        .join(
            UnitPriceReportTemplate,
            ReportTemplateDetail.report_template_id
            == UnitPriceReportTemplate.template_id,
        )
        .join(Shoe, Shoe.shoe_id == UnitPriceReportTemplate.shoe_id)
        .filter(Shoe.shoe_id == shoe_id, UnitPriceReportTemplate.team == team)
        .all()
    )
    result = []
    for row in response:
        obj = {
            "rowId": row.row_id,
            "procedure": row.procedure_name,
            "price": row.price,
            "note": row.note,
        }
        result.append(obj)
    print(result)
    return result


@price_report_bp.route("/production/downloadproductionform", methods=["GET"])
def download_production_form():
    order_shoe_id = request.args.get("orderShoeId")
    report_id = request.args.get("reportId")
    meta_response = (
        db.session.query(Shoe.shoe_rid)
        .join(OrderShoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .first()
    )
    response = (
        db.session.query(UnitPriceReportDetail)
        .join(
            UnitPriceReport,
            UnitPriceReportDetail.report_id == UnitPriceReport.report_id,
        )
        .filter(UnitPriceReport.report_id == report_id)
        .all()
    )
    res = {}
    res["shoe_rid"] = meta_response[0]
    res["procedures"] = []
    for row in response:
        obj = {
            "row_id": row.row_id,
            "procedure_name": row.procedure_name,
        }
        res["procedures"].append(obj)
    template_path = os.path.join("./general_document", "流程卡模板.xlsx")
    new_file_path = os.path.join("./general_document", "流程卡.xlsx")
    new_name = f"鞋型{res['shoe_rid']}_产量流程卡.xlsx"
    generate_excel_file(template_path, new_file_path, res)
    return send_file(new_file_path, as_attachment=True, download_name=new_name)

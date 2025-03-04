import traceback
from datetime import datetime, timedelta

from api_utility import format_date, format_line_group, status_converter
from app_config import db
from constants import *
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request
from models import *
from sqlalchemy import func, or_
from sqlalchemy.dialects.mysql import insert

production_scheduling_bp = Blueprint("production_scheduling_bp", __name__)


@production_scheduling_bp.route(
    "/production/productionmanager/getordershoescheduleinfo", methods=["GET"]
)
def get_order_shoe_schedule_info():
    order_shoe_id = request.args.get("orderShoeId")
    response = (
        db.session.query(
            OrderShoeProductionInfo,
        )
        .filter(OrderShoeProductionInfo.order_shoe_id == order_shoe_id)
        .first()
    )
    teams = ["cutting", "pre_sewing", "sewing", "molding"]
    result = []
    for team in teams:
        obj = {
            "lineGroup": format_line_group(getattr(response, f"{team}_line_group")),
            "startDate": format_date(getattr(response, f"{team}_start_date")),
            "endDate": format_date(getattr(response, f"{team}_end_date")),
        }
        if team == "pre_sewing":
            obj["isOutsourced"] = getattr(response, f"is_sewing_outsourced")
        else:
            obj["isOutsourced"] = getattr(response, f"is_cutting_outsourced")
        result.append(obj)
    return result


def is_valid_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except Exception:
        return None


@production_scheduling_bp.route(
    "/production/productionmanager/editproductionschedule", methods=["PATCH"]
)
def edit_production_schedule():
    data = request.get_json()
    entity = OrderShoeProductionInfo.query.filter(
        OrderShoeProductionInfo.order_shoe_id == data["orderShoeId"]
    ).first()
    teams = ["cutting", "pre_sewing", "sewing", "molding"]
    for index, team in enumerate(teams):
        setattr(
            entity, f"{team}_line_group", data["productionInfoList"][index]["lineValue"]
        )
        setattr(
            entity,
            f"is_{team}_outsourced",
            data["productionInfoList"][index]["isOutsourced"],
        )
        if is_valid_date(data["productionInfoList"][index]["startDate"]):
            setattr(
                entity,
                f"{team}_start_date",
                data["productionInfoList"][index]["startDate"],
            )
        if is_valid_date(data["productionInfoList"][index]["endDate"]):
            setattr(
                entity, f"{team}_end_date", data["productionInfoList"][index]["endDate"]
            )

    entity = (
        db.session.query(OrderShoeStatus)
        .filter(
            OrderShoeStatus.current_status == 17,
            OrderShoeStatus.order_shoe_id == data["orderShoeId"],
        )
        .first()
    )
    if entity:
        entity.current_status_value = 1
    db.session.commit()
    return jsonify({"message": "success"})


@production_scheduling_bp.route(
    "/production/productionmanager/savemultipleschedules", methods=["PATCH"]
)
def save_multiple_schedules():
    data = request.get_json()
    order_shoe_id_arr = data["orderShoeIdArr"]
    response = (
        db.session.query(OrderShoeProductionInfo)
        .filter(OrderShoeProductionInfo.order_shoe_id.in_(order_shoe_id_arr))
        .all()
    )
    for entity in response:
        # 裁断
        entity.cutting_start_date = data["scheduleForm"]["cuttingDateRange"][0]
        entity.cutting_end_date = data["scheduleForm"]["cuttingDateRange"][1]

        # 针车预备
        entity.pre_sewing_start_date = data["scheduleForm"]["preSewingDateRange"][0]
        entity.pre_sewing_end_date = data["scheduleForm"]["preSewingDateRange"][1]

        # 针车
        entity.sewing_start_date = data["scheduleForm"]["sewingDateRange"][0]
        entity.sewing_end_date = data["scheduleForm"]["sewingDateRange"][1]

        # 成型
        entity.molding_start_date = data["scheduleForm"]["moldingDateRange"][0]
        entity.molding_end_date = data["scheduleForm"]["moldingDateRange"][1]

    response = (
        db.session.query(OrderShoeStatus)
        .filter(
            OrderShoeStatus.order_shoe_id.in_(order_shoe_id_arr),
            OrderShoeStatus.current_status == 17,
        )
        .all()
    )
    for entity in response:
        entity.current_status_value = 1

    db.session.commit()
    return jsonify({"message": "success"}), 200


def _create_report_item(report_id, team, shoe_id):
    # load unit price report template
    template = (
        db.session.query(ReportTemplateDetail)
        .join(
            UnitPriceReportTemplate,
            ReportTemplateDetail.report_template_id
            == UnitPriceReportTemplate.template_id,
        )
        .filter(
            UnitPriceReportTemplate.shoe_id == shoe_id,
            UnitPriceReportTemplate.team == team,
        )
        .all()
    )
    if template:
        report_item_list = []
        for row in template:
            detail = row
            report_item = UnitPriceReportDetail(
                report_id=report_id,
                row_id=detail.row_id,
                production_section=detail.production_section,
                procedure_name=detail.procedure_name,
                price=detail.price,
                note=detail.note,
            )
            report_item_list.append(report_item)
        db.session.add_all(report_item_list)


@production_scheduling_bp.route(
    "/production/productionmanager/startproduction", methods=["PATCH"]
)
def start_production():
    data = request.get_json()
    order_shoe_id = data["orderShoeId"]
    query = (
        db.session.query(
            func.sum(OrderShoeBatchInfo.total_amount), OrderShoeType.order_shoe_type_id
        )
        .join(
            OrderShoeBatchInfo,
            OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id,
        )
        .filter(OrderShoeType.order_shoe_id == order_shoe_id)
        .group_by(OrderShoeType.order_shoe_type_id)
    )
    for shoe_size in SHOESIZERANGE:
        column = OrderShoeBatchInfo.__table__.columns.get(f"size_{shoe_size}_amount")
        query = query.add_columns(
            func.sum(column).label(f"size_{shoe_size}_amount")
        )
    order_shoe_type_ids = query.all()
    arr = []
    for row in order_shoe_type_ids:
        color_total_amount, id, *size_amount = row
        semi_entity = SemifinishedShoeStorage(
            order_shoe_type_id=id,
            semifinished_status=0,
            semifinished_object=1,
            semifinished_estimated_amount=color_total_amount,
        )
        for i, amount in enumerate(size_amount):
            setattr(semi_entity, f"size_{SHOESIZERANGE[i]}_estimated_amount", amount)
        arr.append(semi_entity)
        finished_entity = FinishedShoeStorage(
            order_shoe_type_id=id,
            finished_status=0,
            finished_estimated_amount=color_total_amount,
        )
        for i, amount in enumerate(size_amount):
            setattr(finished_entity, f"size_{SHOESIZERANGE[i]}_estimated_amount", amount)
        arr.append(finished_entity)
    db.session.add_all(arr)

    production_amount = (
        db.session.query(
            func.sum(OrderShoeProductionAmount.total_production_amount),
            OrderShoeProductionAmount.production_team,
        )
        .join(
            OrderShoeType,
            OrderShoeProductionAmount.order_shoe_type_id
            == OrderShoeType.order_shoe_type_id,
        )
        .join(OrderShoe, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(
            OrderShoe.order_shoe_id == order_shoe_id,
        )
        .group_by(OrderShoe.order_shoe_id, OrderShoeProductionAmount.production_team)
        .all()
    )
    # 0：裁断，1：针车，2：成型
    # 只有针车，裁断+针车 的外包，一定有成型工价obj

    # find shoe id
    shoe_id = (
        db.session.query(OrderShoe.shoe_id)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .first()
    )
    shoe_id = shoe_id[0]
    report_arr = []
    for row in production_amount:
        amount, team = row

        if team == 0 and amount != 0:
            report1 = UnitPriceReport(
                order_shoe_id=order_shoe_id, team="裁断", status=0
            )
            db.session.add(report1)
            db.session.flush()
            _create_report_item(report1.report_id, "裁断", shoe_id)

        elif team == 1 and amount != 0:
            report1 = UnitPriceReport(
                order_shoe_id=order_shoe_id, team="针车预备", status=0
            )
            report2 = UnitPriceReport(
                order_shoe_id=order_shoe_id, team="针车", status=0
            )
            report_arr.append(report1)
            report_arr.append(report2)
            db.session.add(report1)
            db.session.add(report2)
            db.session.flush()
            _create_report_item(report1.report_id, "针车预备", shoe_id)
            _create_report_item(report2.report_id, "针车", shoe_id)
        elif team == 2:
            report1 = UnitPriceReport(
                order_shoe_id=order_shoe_id, team="成型", status=0
            )
            report_arr.append(report1)
            _create_report_item(report1.report_id, "成型", shoe_id)

    db.session.add_all(report_arr)
    # pass to event processor
    processor: EventProcessor = current_app.config["event_processor"]
    try:
        for operation in [72, 73, 74, 75]:
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
    db.session.commit()
    return jsonify({"message": "success"}), 200


@production_scheduling_bp.route(
    "/production/productionmanager/getorderproductiondetail", methods=["GET"]
)
def get_order_production_detail():
    order_id = request.args.get("orderId")
    response = (
        db.session.query(
            OrderShoe,
            Shoe,
            func.group_concat(OrderShoeStatus.current_status).label(
                "current_status_str"
            ),
            func.group_concat(OrderShoeStatus.current_status_value).label(
                "current_status_value_str"
            ),
        )
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(OrderShoe.order_id == order_id)
        .group_by(OrderShoe.order_shoe_id)
        .all()
    )
    result = []
    for row in response:
        order_shoe, shoe, current_status_str, current_status_value_str = row
        current_status_arr = [int(item) for item in current_status_str.split(",")]
        current_status_value_arr = [
            int(item) for item in current_status_value_str.split(",")
        ]

        obj = {
            "orderShoeId": order_shoe.order_shoe_id,
            "shoeRId": shoe.shoe_rid,
            "customerProductName": order_shoe.customer_product_name,
            "totalShoes": 0,
            "detail": [],
            "status": status_converter(current_status_arr, current_status_value_arr),
        }
        detail_response = (
            db.session.query(
                func.sum(OrderShoeBatchInfo.total_amount), OrderShoeType, Color
            )
            .join(
                OrderShoeType,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .join(ShoeType, OrderShoeType.shoe_type_id == ShoeType.shoe_type_id)
            .join(Color, Color.color_id == ShoeType.color_id)
            .filter(OrderShoeType.order_shoe_id == order_shoe.order_shoe_id)
            .group_by(OrderShoeType.order_shoe_type_id, Color.color_id)
            .all()
        )
        for detail_row in detail_response:
            color_total_amount, order_shoe_type, color = detail_row
            obj["totalShoes"] += color_total_amount
            obj["detail"].append(
                {
                    "colorName": color.color_name,
                    "batchAmount": color_total_amount,
                    "cuttingAmount": order_shoe_type.cutting_amount,
                    "preSewingAmount": order_shoe_type.pre_sewing_amount,
                    "sewingAmount": order_shoe_type.sewing_amount,
                    "moldingAmount": order_shoe_type.molding_amount,
                }
            )
        result.append(obj)
    return result


@production_scheduling_bp.route(
    "/production/productionmanager/saveproductionamount", methods=["PATCH"]
)
def save_production_amount():
    data = request.get_json()
    print(data)
    for row in data:
        obj = {}
        # set production_amount_id
        if "productionAmountId" in row:
            obj["order_shoe_production_amount_id"] = row["productionAmountId"]
        obj["total_production_amount"] = 0
        obj["order_shoe_type_id"] = row["orderShoeTypeId"]
        obj["production_team"] = row["productionTeam"]
        for i in range(34, 47):
            obj[f"size_{i}_production_amount"] = 0
            if f"size{i}Amount" in row:
                if not row[f"size{i}Amount"]:
                    row[f"size{i}Amount"] = 0
                obj[f"size_{i}_production_amount"] = int(row[f"size{i}Amount"])
                obj["total_production_amount"] += int(row[f"size{i}Amount"])
        stmt = insert(OrderShoeProductionAmount).values(**obj)
        stmt = stmt.on_duplicate_key_update(**obj)
        db.session.execute(stmt)
    db.session.commit()
    return jsonify({"message": "success"})

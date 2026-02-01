import traceback
from datetime import datetime, timedelta, date

from api_utility import *
from app_config import db
from constants import *
from event_processor import EventProcessor
from flask import Blueprint, current_app, jsonify, request
from models import *
from sqlalchemy import func, or_
from sqlalchemy.dialects.mysql import insert
from logger import logger

production_scheduling_bp = Blueprint("production_scheduling_bp", __name__)


def _get_order_type_by_order_shoe(order_shoe_id):
    result = (
        db.session.query(Order.order_type)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .filter(OrderShoe.order_shoe_id == order_shoe_id)
        .first()
    )
    return result[0] if result else None


@production_scheduling_bp.route(
    "/production/productionmanager/getordershoescheduleinfo", methods=["GET"]
)
def get_order_shoe_schedule_info():
    order_shoe_id = request.args.get("orderShoeId")
    order_type = _get_order_type_by_order_shoe(order_shoe_id)
    if order_type == "F":
        return jsonify({"message": "预报单不可排期"}), 400
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
    order_type = _get_order_type_by_order_shoe(data.get("orderShoeId"))
    if order_type == "F":
        return jsonify({"message": "预报单不可排期"}), 400
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

    for item in data:
        order_type = _get_order_type_by_order_shoe(item.get("orderShoeId"))
        if order_type == "F":
            return jsonify({"message": "预报单不可排期"}), 400

    order_shoe_ids = [item["orderShoeId"] for item in data]

    order_shoes = (
        db.session.query(OrderShoeProductionInfo)
        .filter(OrderShoeProductionInfo.order_shoe_id.in_(order_shoe_ids))
        .all()
    )

    order_shoes_dict = {
        order_shoe.order_shoe_id: order_shoe for order_shoe in order_shoes
    }

    for item in data:
        order_shoe_id = item["orderShoeId"]
        cutting_date_value = item["cuttingDateValue"]
        pre_sewing_date_value = item["preSewingDateValue"]
        sewing_date_value = item["sewingDateValue"]
        molding_date_value = item["moldingDateValue"]

        production_info = order_shoes_dict.get(order_shoe_id)
        production_info.cutting_start_date = cutting_date_value[0]
        production_info.cutting_end_date = cutting_date_value[1]
        production_info.pre_sewing_start_date = pre_sewing_date_value[0]
        production_info.pre_sewing_end_date = pre_sewing_date_value[1]
        production_info.sewing_start_date = sewing_date_value[0]
        production_info.sewing_end_date = sewing_date_value[1]
        production_info.molding_start_date = molding_date_value[0]
        production_info.molding_end_date = molding_date_value[1]

        status_name = scheduling_status_converter(production_info)
        status_int = SCHEDULING_STATUS_TO_INT[status_name]
        production_info.scheduling_status = status_int

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
    for item in data:
        order_id = item["orderId"]
        order_shoe_id = item["orderShoeId"]
        order_type = _get_order_type_by_order_shoe(order_shoe_id)
        if order_type == "F":
            return jsonify({"message": "预报单不可排期"}), 400
        # check if order shoe status is 17
        order_shoe_status = (
            db.session.query(OrderShoeStatus)
            .filter(
                OrderShoeStatus.order_shoe_id == order_shoe_id,
                OrderShoeStatus.current_status == 17,
            )
            .first()
        )
        if not order_shoe_status:
            continue
        query = (
            db.session.query(
                func.sum(OrderShoeBatchInfo.total_amount),
                OrderShoeType.order_shoe_type_id,
            )
            .join(
                OrderShoeBatchInfo,
                OrderShoeBatchInfo.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(OrderShoeType.order_shoe_id == order_shoe_id)
            .group_by(OrderShoeType.order_shoe_type_id)
        )
        for shoe_size in SHOESIZERANGE:
            column = OrderShoeBatchInfo.__table__.columns.get(
                f"size_{shoe_size}_amount"
            )
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
                semifinished_estimated_amount=color_total_amount,
            )
            for i, amount in enumerate(size_amount):
                setattr(
                    semi_entity, f"size_{SHOESIZERANGE[i]}_estimated_amount", amount
                )
            arr.append(semi_entity)
            finished_entity = FinishedShoeStorage(
                order_shoe_type_id=id,
                finished_status=0,
                finished_estimated_amount=color_total_amount,
            )
            for i, amount in enumerate(size_amount):
                setattr(
                    finished_entity, f"size_{SHOESIZERANGE[i]}_estimated_amount", amount
                )
            arr.append(finished_entity)
        db.session.add_all(arr)

        # find order shoe production amount
        # if not found, create new
        order_shoe_production_amount = (
            db.session.query(OrderShoeProductionAmount)
            .join(
                OrderShoeType,
                OrderShoeProductionAmount.order_shoe_type_id
                == OrderShoeType.order_shoe_type_id,
            )
            .filter(OrderShoeType.order_shoe_id == order_shoe_id)
            .all()
        )
        if not order_shoe_production_amount:
            for row in order_shoe_type_ids:
                color_total_amount, id, *size_amount = row
                # create new OrderShoeProductionAmount
                for team in [0, 1, 2]:
                    order_shoe_production_amount = OrderShoeProductionAmount(
                        order_shoe_type_id=id,
                        total_production_amount=color_total_amount,
                        production_team=team,
                    )
                    for i, amount in enumerate(size_amount):
                        setattr(
                            order_shoe_production_amount,
                            f"size_{SHOESIZERANGE[i]}_production_amount",
                            amount,
                        )
                    db.session.add(order_shoe_production_amount)
                    db.session.flush()

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
            .group_by(
                OrderShoe.order_shoe_id, OrderShoeProductionAmount.production_team
            )
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
                report1 = UnitPriceReport(order_shoe_id=order_shoe_id, team="裁断")
                db.session.add(report1)
                db.session.flush()
                _create_report_item(report1.report_id, "裁断", shoe_id)

            elif team == 1 and amount != 0:
                report1 = UnitPriceReport(order_shoe_id=order_shoe_id, team="针车预备")
                report2 = UnitPriceReport(order_shoe_id=order_shoe_id, team="针车")
                report_arr.append(report1)
                report_arr.append(report2)
                db.session.add(report1)
                db.session.add(report2)
                db.session.flush()
                _create_report_item(report1.report_id, "针车预备", shoe_id)
                _create_report_item(report2.report_id, "针车", shoe_id)
            elif team == 2:
                report1 = UnitPriceReport(order_shoe_id=order_shoe_id, team="成型")
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
                    event_order_id=order_id,
                    event_order_shoe_id=order_shoe_id,
                )
                processor.processEvent(event)
        except Exception as e:
            logger.debug(e)
            return jsonify({"message": "下发失败"}), 400
    db.session.commit()
    return jsonify({"message": "下发成功"}), 200


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
    logger.debug(data)
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


@production_scheduling_bp.route(
    "/production/getorderschedulingprogress", methods=["GET"]
)
def get_order_scheduling_progress():
    page = request.args.get("page", type=int)
    number = request.args.get("pageSize", type=int)
    order_rid = request.args.get("orderRId")
    shoe_rid = request.args.get("shoeRId")
    status_node = request.args.get("statusNode")
    start_date_search = request.args.get("orderStartDate")
    end_date_search = request.args.get("orderEndDate")
    query = (
        db.session.query(Order, OrderShoe, Shoe, OrderShoeProductionInfo)
        .join(OrderShoe, Order.order_id == OrderShoe.order_id)
        .join(Shoe, Shoe.shoe_id == OrderShoe.shoe_id)
        .join(
            OrderShoeProductionInfo,
            OrderShoeProductionInfo.order_shoe_id == OrderShoe.order_shoe_id,
        )
        .join(OrderStatus, OrderStatus.order_id == Order.order_id)
        .join(OrderShoeStatus, OrderShoeStatus.order_shoe_id == OrderShoe.order_shoe_id)
        .filter(Order.order_type == "N")
        .filter(OrderStatus.order_current_status >= IN_PRODUCTION_ORDER_NUMBER)
        .filter(OrderShoeStatus.current_status >= 17)
        .order_by(Order.order_rid)
    )
    if order_rid and order_rid != "":
        query = query.filter(Order.order_rid.ilike(f"%{order_rid}%"))
    if shoe_rid and shoe_rid != "":
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid}%"))
    if status_node and status_node != "":
        query = query.filter(
            OrderShoeProductionInfo.scheduling_status
            == SCHEDULING_STATUS_TO_INT[status_node]
        )
    count_result = query.distinct().count()
    response = query.distinct().limit(number).offset((page - 1) * number).all()
    result = []
    for row in response:
        order, order_shoe, shoe, production_info = row
        order_attrs = Order.__table__.columns.keys()
        order_shoes_attrs = OrderShoe.__table__.columns.keys()
        shoe_attrs = Shoe.__table__.columns.keys()
        production_info_attrs = OrderShoeProductionInfo.__table__.columns.keys()
        scheduling_status = scheduling_status_converter(production_info)
        obj = {}
        for attr in order_attrs:
            obj[to_camel(attr)] = getattr(order, attr)
        for attr in order_shoes_attrs:
            obj[to_camel(attr)] = getattr(order_shoe, attr)
        for attr in shoe_attrs:
            obj[to_camel(attr)] = getattr(shoe, attr)
        for attr in production_info_attrs:
            attr_value = getattr(production_info, attr)
            if attr_value and isinstance(attr_value, (datetime, date)):
                obj[to_camel(attr)] = format_date(attr_value)
            else:
                obj[to_camel(attr)] = attr_value
        obj["schedulingStatus"] = scheduling_status
        result.append(obj)
    return jsonify({"result": result, "totalLength": count_result}), 200

from datetime import datetime

from api_utility import format_date, outsource_status_converter
from app_config import db
from constants import END_OF_PRODUCTION_NUMBER
from flask import Blueprint, jsonify, request
from models import *
from sqlalchemy import func, or_, cast, Integer, and_, select, asc, desc
from datetime import date

production_report_bp = Blueprint("production_report_bp", __name__)


@production_report_bp.route("/production/getselfproductionsummary", methods=["GET"])
def get_self_production_summary():
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    if start_date and end_date:
        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = date.fromisoformat(end_date)
    else:
        return jsonify({"message": "请选择一个日期"}), 400

    response = (
        db.session.query(ProductionLine, func.sum(QuantityReportItem.report_amount))
        .join(
            QuantityReportItem,
            QuantityReportItem.production_line_id == ProductionLine.production_line_id,
        )
        .join(
            QuantityReport,
            QuantityReport.report_id == QuantityReportItem.quantity_report_id,
        )
        .filter(
            QuantityReport.creation_date >= start_date_obj,
            QuantityReport.creation_date <= end_date_obj,
            QuantityReport.status == 2,
        )
        .group_by(ProductionLine.production_line_id)
    )
    temp = {
        "裁断": {"totalAmount": 0, "productionLines": []},
        "针车预备": {"totalAmount": 0, "productionLines": []},
        "针车": {"totalAmount": 0, "productionLines": []},
        "成型": {"totalAmount": 0, "productionLines": []},
    }
    for row in response:
        production_line, production_line_amount = row
        temp[production_line.production_team]["totalAmount"] += production_line_amount
        obj = {
            "team": production_line.production_team,
            "productionLineName": production_line.production_line_name,
            "productionLineAmount": production_line_amount,
        }
        temp[production_line.production_team]["productionLines"].append(obj)
    result = []
    for key, value in temp.items():
        obj = {
            "team": key,
            "totalAmount": value["totalAmount"],
            "productionLines": value["productionLines"],
        }
        result.append(obj)
    return result


@production_report_bp.route("/production/getoutsourcesummary", methods=["GET"])
def get_outsource_summary():
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    if start_date and end_date:
        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = date.fromisoformat(end_date)
    else:
        return jsonify({"message": "请选择一个日期"}), 400

    response = (
        db.session.query(OutsourceInfo, OutsourceFactory)
        .join(OutsourceFactory, OutsourceInfo.factory_id == OutsourceFactory.factory_id)
        .filter(
            or_(
                and_(
                    OutsourceInfo.outsource_start_date >= start_date_obj,
                    OutsourceInfo.outsource_end_date <= end_date_obj,
                ),
                and_(
                    OutsourceInfo.outsource_start_date <= end_date_obj,
                    OutsourceInfo.outsource_start_date >= start_date_obj,
                ),
                and_(
                    OutsourceInfo.outsource_end_date >= start_date_obj,
                    OutsourceInfo.outsource_end_date <= end_date_obj,
                ),
                and_(
                    OutsourceInfo.outsource_start_date <= start_date_obj,
                    OutsourceInfo.outsource_end_date >= end_date_obj,
                ),
            ),
            OutsourceInfo.outsource_status.in_([1, 2, 4, 5, 6, 7]),
        )
    )
    result = []
    for row in response:
        outsource_info, factory = row
        obj = {
            "outsourceInfoId": outsource_info.outsource_info_id,
            "outsourceFactory": factory.factory_name,
            "outsourceStatus": outsource_status_converter(outsource_info.outsource_status),
            "outsourceAmount": outsource_info.outsource_amount
        }
        result.append(obj)
    return result

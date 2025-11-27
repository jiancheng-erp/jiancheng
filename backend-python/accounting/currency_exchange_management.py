from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import and_

from models import AccountingCurrencyUnit, AccountingUnitConversionTable
from api_utility import format_datetime
from app_config import db

currency_exchange_bp = Blueprint("currency_exchange_bp", __name__)


def _resolve_base_unit_id(preferred_id: Optional[int] = None) -> Optional[int]:
    if preferred_id:
        return preferred_id

    rmb_unit = db.session.query(AccountingCurrencyUnit).filter(
        AccountingCurrencyUnit.unit_name_cn == "人民币"
    ).first()
    if rmb_unit:
        return rmb_unit.unit_id

    cny_unit = db.session.query(AccountingCurrencyUnit).filter(
        AccountingCurrencyUnit.unit_name_en.ilike("CNY")
    ).first()
    if cny_unit:
        return cny_unit.unit_id

    fallback_unit = db.session.query(AccountingCurrencyUnit).order_by(
        AccountingCurrencyUnit.unit_id
    ).first()
    return fallback_unit.unit_id if fallback_unit else None


@currency_exchange_bp.route("/accounting/currency_units", methods=["GET"])
def get_currency_units():
    units = (
        db.session.query(AccountingCurrencyUnit)
        .order_by(AccountingCurrencyUnit.unit_id)
        .all()
    )
    response_units = [
        {
            "unitId": unit.unit_id,
            "unitNameEn": unit.unit_name_en,
            "unitNameCn": unit.unit_name_cn,
            "createTime": format_datetime(unit.create_time),
            "updateTime": format_datetime(unit.update_time),
        }
        for unit in units
    ]
    return jsonify({"units": response_units}), 200


@currency_exchange_bp.route("/accounting/currency_conversions", methods=["GET"])
def get_currency_conversions():
    base_unit_id = _resolve_base_unit_id(request.args.get("baseUnitId", type=int))
    if not base_unit_id:
        return jsonify({"conversions": [], "baseUnitId": None}), 200

    conversions = (
        db.session.query(AccountingUnitConversionTable)
        .filter(AccountingUnitConversionTable.unit_from == base_unit_id)
        .all()
    )

    unit_map = {
        unit.unit_id: unit
        for unit in db.session.query(AccountingCurrencyUnit).all()
    }

    response_data = []
    for conversion in conversions:
        unit_to = unit_map.get(conversion.unit_to)
        response_data.append(
            {
                "conversionId": conversion.conversion_id,
                "unitFrom": conversion.unit_from,
                "unitTo": conversion.unit_to,
                "rate": float(conversion.rate) if conversion.rate is not None else None,
                "rateDate": format_datetime(conversion.rate_date),
                "rateActive": bool(conversion.rate_active),
                "unitToNameEn": unit_to.unit_name_en if unit_to else "",
                "unitToNameCn": unit_to.unit_name_cn if unit_to else "",
            }
        )

    return jsonify({"conversions": response_data, "baseUnitId": base_unit_id}), 200


@currency_exchange_bp.route("/accounting/currency_conversion", methods=["POST"])
def upsert_currency_conversion():
    data = request.get_json() or {}

    unit_from = _resolve_base_unit_id(data.get("unitFrom"))
    unit_to = data.get("unitTo")
    rate = data.get("rate")
    rate_date_str = data.get("rateDate")
    rate_active = data.get("rateActive", True)

    if unit_from is None:
        return jsonify({"message": "无法确定基础货币单位"}), 400

    if unit_to is None or rate is None:
        return jsonify({"message": "缺少必要的货币单位或汇率信息"}), 400

    try:
        rate_value = float(rate)
    except (TypeError, ValueError):
        return jsonify({"message": "无效的汇率数值"}), 400

    rate_date = None
    if rate_date_str:
        try:
            rate_date = datetime.fromisoformat(rate_date_str)
        except ValueError:
            return jsonify({"message": "无效的汇率日期格式"}), 400

    conversion = (
        db.session.query(AccountingUnitConversionTable)
        .filter(
            and_(
                AccountingUnitConversionTable.unit_from == unit_from,
                AccountingUnitConversionTable.unit_to == unit_to,
            )
        )
        .first()
    )

    if not conversion:
        conversion = AccountingUnitConversionTable(
            unit_from=unit_from,
            unit_to=unit_to,
        )

    conversion.rate = rate_value
    conversion.rate_date = rate_date
    conversion.rate_active = bool(rate_active)

    db.session.add(conversion)
    db.session.commit()

    return (
        jsonify({"message": "汇率已保存", "conversionId": conversion.conversion_id}),
        200,
    )
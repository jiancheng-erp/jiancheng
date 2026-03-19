from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, desc

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


def get_exchange_rate_for_month(
    unit_from: int, unit_to: int, year: int, month: int
) -> Optional[AccountingUnitConversionTable]:
    """
    获取指定月份的汇率，如果该月没有填写则沿用最近的上一个月的汇率。
    返回 AccountingUnitConversionTable 行或 None。
    """
    row = (
        db.session.query(AccountingUnitConversionTable)
        .filter(
            AccountingUnitConversionTable.unit_from == unit_from,
            AccountingUnitConversionTable.unit_to == unit_to,
            AccountingUnitConversionTable.rate_year * 100
            + AccountingUnitConversionTable.rate_month
            <= year * 100 + month,
        )
        .order_by(
            desc(
                AccountingUnitConversionTable.rate_year * 100
                + AccountingUnitConversionTable.rate_month
            )
        )
        .first()
    )
    return row


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
    """
    获取指定月份的汇率列表。
    查询参数: baseUnitId, year, month
    如果某个货币对在该月未填写，则沿用最近的上一个月的汇率（标记 inherited=True）。
    """
    base_unit_id = _resolve_base_unit_id(request.args.get("baseUnitId", type=int))
    if not base_unit_id:
        return jsonify({"conversions": [], "baseUnitId": None}), 200

    now = datetime.now()
    year = request.args.get("year", type=int) or now.year
    month = request.args.get("month", type=int) or now.month

    unit_map = {
        unit.unit_id: unit
        for unit in db.session.query(AccountingCurrencyUnit).all()
    }

    target_units = [u for uid, u in unit_map.items() if uid != base_unit_id]

    response_data = []
    for unit_to_obj in target_units:
        row = get_exchange_rate_for_month(base_unit_id, unit_to_obj.unit_id, year, month)
        inherited = False
        if row and (row.rate_year != year or row.rate_month != month):
            inherited = True

        response_data.append(
            {
                "conversionId": row.conversion_id if row else None,
                "unitFrom": base_unit_id,
                "unitTo": unit_to_obj.unit_id,
                "rate": float(row.rate) if row and row.rate is not None else None,
                "rateYear": row.rate_year if row else None,
                "rateMonth": row.rate_month if row else None,
                "rateActive": bool(row.rate_active) if row else False,
                "inherited": inherited,
                "unitToNameEn": unit_to_obj.unit_name_en,
                "unitToNameCn": unit_to_obj.unit_name_cn,
            }
        )

    return jsonify({"conversions": response_data, "baseUnitId": base_unit_id,
                     "year": year, "month": month}), 200


@currency_exchange_bp.route("/accounting/currency_conversion_history", methods=["GET"])
def get_currency_conversion_history():
    """获取某个货币对的所有历史月度汇率记录。"""
    base_unit_id = _resolve_base_unit_id(request.args.get("baseUnitId", type=int))
    unit_to = request.args.get("unitTo", type=int)
    if not base_unit_id or not unit_to:
        return jsonify({"records": []}), 200

    rows = (
        db.session.query(AccountingUnitConversionTable)
        .filter(
            AccountingUnitConversionTable.unit_from == base_unit_id,
            AccountingUnitConversionTable.unit_to == unit_to,
        )
        .order_by(
            desc(AccountingUnitConversionTable.rate_year),
            desc(AccountingUnitConversionTable.rate_month),
        )
        .all()
    )

    records = [
        {
            "conversionId": r.conversion_id,
            "rate": float(r.rate) if r.rate is not None else None,
            "rateYear": r.rate_year,
            "rateMonth": r.rate_month,
            "rateActive": bool(r.rate_active),
        }
        for r in rows
    ]
    return jsonify({"records": records}), 200


@currency_exchange_bp.route("/accounting/currency_conversion", methods=["POST"])
def upsert_currency_conversion():
    """
    新增或更新某个月份的汇率。
    按 (unit_from, unit_to, rate_year, rate_month) 进行 upsert。
    """
    data = request.get_json() or {}

    unit_from = _resolve_base_unit_id(data.get("unitFrom"))
    unit_to = data.get("unitTo")
    rate = data.get("rate")
    rate_year = data.get("rateYear")
    rate_month = data.get("rateMonth")
    rate_active = data.get("rateActive", True)

    if unit_from is None:
        return jsonify({"message": "无法确定基础货币单位"}), 400

    if unit_to is None or rate is None:
        return jsonify({"message": "缺少必要的货币单位或汇率信息"}), 400

    if not rate_year or not rate_month:
        return jsonify({"message": "缺少年份或月份信息"}), 400

    try:
        rate_value = float(rate)
    except (TypeError, ValueError):
        return jsonify({"message": "无效的汇率数值"}), 400

    conversion = (
        db.session.query(AccountingUnitConversionTable)
        .filter(
            and_(
                AccountingUnitConversionTable.unit_from == unit_from,
                AccountingUnitConversionTable.unit_to == unit_to,
                AccountingUnitConversionTable.rate_year == int(rate_year),
                AccountingUnitConversionTable.rate_month == int(rate_month),
            )
        )
        .first()
    )

    if not conversion:
        conversion = AccountingUnitConversionTable(
            unit_from=unit_from,
            unit_to=unit_to,
            rate_year=int(rate_year),
            rate_month=int(rate_month),
        )

    conversion.rate = rate_value
    conversion.rate_active = bool(rate_active)

    db.session.add(conversion)
    db.session.commit()

    return (
        jsonify({"message": "汇率已保存", "conversionId": conversion.conversion_id}),
        200,
    )


@currency_exchange_bp.route("/accounting/currency_conversion/<int:conversion_id>", methods=["DELETE"])
def delete_currency_conversion(conversion_id: int):
    """删除某条月度汇率记录。"""
    row = db.session.query(AccountingUnitConversionTable).get(conversion_id)
    if not row:
        return jsonify({"message": "记录不存在"}), 404
    db.session.delete(row)
    db.session.commit()
    return jsonify({"message": "已删除"}), 200
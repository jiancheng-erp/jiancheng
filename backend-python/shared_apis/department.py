from flask import Blueprint, jsonify, request

from app_config import db
from models import *

department_bp = Blueprint("department_bp", __name__)

BUSINESS_DEPARTMENT_ID = 10
BUSINESS_MANAGER_CHARACTER = 4
BUSINESS_CLERK_CHARACTER = 21
@department_bp.route("/general/getalldepartments", methods=["GET"])
def get_all_departments():
    departments = Department.query.all()
    result = []
    for department in departments:
        result.append(
            {
                "value": department.department_id,
                "label": department.department_name,
            }
        )
    return jsonify(result)

#业务经理查询接口
@department_bp.route("/general/getbusinessmanagers", methods=["GET"])
def get_business_managers():
    business_managers = (db.session.query(Staff).filter_by(character_id = BUSINESS_MANAGER_CHARACTER).all())
    result = []
    for business_manager in business_managers:
        result.append(
            {
                "staffId":business_manager.staff_id,
                "staffName":business_manager.staff_name
            }
        )
    return jsonify(result), 200

#业务职员查询接口
@department_bp.route("/general/getbusinessclerks", methods=["GET"])
def get_business_clerks():
    business_clerks = (db.session.query(Staff).filter_by(Staff.character_id == BUSINESS_CLERK_CHARACTER).all())
    result = []
    for clerk in business_clerks:
        result.append(
            {
                "staffId":clerk.staff_id,
                "staffName":clerk.staff_name
            }
        )
    return jsonify(result), 200
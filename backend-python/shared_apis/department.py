from flask import Blueprint, jsonify, request

from app_config import db
from models import *

department_bp = Blueprint("department_bp", __name__)

BUSINESS_DEPARTMENT_ID = 10
BUSINESS_MANAGER_CHARACTER = 4
BUSINESS_CLERK_CHARACTER = 21
BUSINESS_ROLE_IDS = [BUSINESS_MANAGER_CHARACTER, BUSINESS_CLERK_CHARACTER]


def get_business_department_ids():
    """业务部门 = 含有业务经理/业务文员角色成员的部门（动态，随人员部门/角色变动）。"""
    rows = (
        db.session.query(Staff.department_id)
        .filter(
            Staff.character_id.in_(BUSINESS_ROLE_IDS),
            Staff.department_id.isnot(None),
        )
        .distinct()
        .all()
    )
    return [row[0] for row in rows]


@department_bp.route("/general/getbusinessdepartments", methods=["GET"])
def get_business_departments():
    business_ids = get_business_department_ids()
    departments = (
        Department.query.filter(Department.department_id.in_(business_ids)).all()
        if business_ids
        else []
    )
    result = [
        {"value": d.department_id, "label": d.department_name} for d in departments
    ]
    return jsonify(result)

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


@department_bp.route("/general/createdepartment", methods=["POST"])
def create_department():
    department_name = (request.json.get("departmentName") or "").strip()
    if not department_name:
        return jsonify({"error": "部门名称不能为空"}), 400
    try:
        existing = Department.query.filter_by(department_name=department_name).first()
        if existing:
            return jsonify({"error": "部门名称已存在"}), 400
        department = Department(department_name=department_name)
        db.session.add(department)
        db.session.commit()
        return jsonify({"message": "Department created successfully", "departmentId": department.department_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@department_bp.route("/general/updatedepartment", methods=["POST"])
def update_department():
    department_id = request.json.get("departmentId")
    department_name = (request.json.get("departmentName") or "").strip()
    if not department_id:
        return jsonify({"error": "departmentId is required"}), 400
    if not department_name:
        return jsonify({"error": "部门名称不能为空"}), 400
    try:
        department = Department.query.filter_by(department_id=department_id).first()
        if not department:
            return jsonify({"error": "部门不存在"}), 404
        existing = Department.query.filter(
            Department.department_name == department_name,
            Department.department_id != department_id,
        ).first()
        if existing:
            return jsonify({"error": "部门名称已存在"}), 400
        department.department_name = department_name
        db.session.commit()
        return jsonify({"message": "Department updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@department_bp.route("/general/deletedepartment", methods=["POST"])
def delete_department():
    department_id = request.json.get("departmentId")
    if not department_id:
        return jsonify({"error": "departmentId is required"}), 400
    try:
        department = Department.query.filter_by(department_id=department_id).first()
        if not department:
            return jsonify({"error": "部门不存在"}), 404
        staff_count = Staff.query.filter_by(department_id=department_id).count()
        if staff_count > 0:
            return jsonify({"error": "该部门下仍有员工，无法删除"}), 400
        db.session.delete(department)
        db.session.commit()
        return jsonify({"message": "Department deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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
from flask import Blueprint, jsonify, request
import os
from app_config import db
from models import *
from file_locations import IMAGE_STORAGE_PATH, FILE_STORAGE_PATH, IMAGE_UPLOAD_PATH
from Crypto.Cipher import AES
import base64
import hashlib

staff_manage_bp = Blueprint("staff_manage_bp", __name__)

@staff_manage_bp.route("/staffmanage/getallstaff", methods=["GET"])
def get_all_staff():
    entities = (
        db.session.query(Staff, Character, Department)
        .join(Character, Staff.character_id == Character.character_id)
        .join(Department, Staff.department_id == Department.department_id)
        .all()
    )
    result = []
    for entity in entities:
        if entity.Staff.staff_status == 0:
            status_name = "在职"
        elif entity.Staff.staff_status == 1:
            status_name = "离职"
        result.append(
            {
                "staffId": entity.Staff.staff_id,
                "staffName": entity.Staff.staff_name,
                "characterName": entity.Character.character_name,
                "characterId": entity.Character.character_id,
                "departmentName": entity.Department.department_name,
                "departmentId": entity.Department.department_id,
                "staffStatus": status_name,
                "wechatId": getattr(entity.Staff, "wechat_id", None),
            }
        )
    return jsonify(result)

@staff_manage_bp.route("/staffmanage/createstaff", methods=["POST"])
def create_staff():
    staff_name = request.json.get("staffName")
    character_id = request.json.get("characterId")
    department_id = request.json.get("departmentId")
    try:
        character = Character.query.filter_by(character_id=character_id).first()
        department = Department.query.filter_by(department_id=department_id).first()
        existing_staff = Staff.query.filter_by(staff_name=staff_name).first()
        if existing_staff:
            return jsonify({"error": "Staff name already exists"}), 400
        staff = Staff(staff_name=staff_name, character_id=character.character_id, department_id=department.department_id)
        db.session.add(staff)
        db.session.commit()
        return jsonify({"message": "Staff created successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@staff_manage_bp.route("/staffmanage/resignstaff", methods=["POST"])
def resign_staff():
    staff_id = request.json.get("staffId")
    try:
        staff = Staff.query.filter_by(staff_id=staff_id).first()
        staff.staff_status = 1
        db.session.commit()
        return jsonify({"message": "Staff resigned successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@staff_manage_bp.route("/staffmanage/getstaffinfo", methods=["POST"])
def get_staff_info():
    staff_id = request.json.get("staffId")
    staff = Staff.query.filter_by(staff_id=staff_id).first()
    character = Character.query.filter_by(character_id=staff.character_id).first()
    department = Department.query.filter_by(department_id=staff.department_id).first()
    if staff.staff_status == 0:
        status_name = "在职"
    elif staff.staff_status == 1:
        status_name = "离职"
    result = {
        "staffId": staff.staff_id,
        "staffName": staff.staff_name,
        "characterName": character.character_name,
        "characterId": character.character_id,
        "departmentName": department.department_name,
        "departmentId": department.department_id,
        "staffStatus": status_name,
        "IdNumber": staff.id_number,
        "phoneNumber": staff.phone_number,
        "birthDate": staff.birth_date,
        "wechatId": staff.wechat_id,
    }
    return jsonify(result)


@staff_manage_bp.route("/staffmanage/updatewechatid", methods=["POST"])
def update_wechat_id():
    staff_id = request.json.get("staffId")
    wechat_id = request.json.get("wechatId")
    if not staff_id:
        return jsonify({"error": "staffId is required"}), 400
    try:
        staff = Staff.query.filter_by(staff_id=staff_id).first()
        if not staff:
            return jsonify({"error": "Staff not found"}), 404
        staff.wechat_id = wechat_id
        db.session.commit()
        return jsonify({"message": "Wechat ID updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import JWTManager, create_access_token, get_jwt, jwt_required, get_jwt_identity, decode_token
from app_config import db
from models import *
from login.login import decrypt_password
import hashlib

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/general/getallcharacters", methods=["GET"])
def get_all_characters():
    characters = Character.query.all()
    result = []
    for character in characters:
        result.append(
            {
                "value": character.character_id,
                "label": character.character_name,
            }
        )
    return jsonify(result)

@user_bp.route("/general/getallstaffs", methods=["GET"])
def get_all_staffs():
    staffs = Staff.query.all()
    result = []
    for staff in staffs:
        result.append(
            {
                "value": staff.staff_id,
                "label": staff.staff_name,
            }
        )
    return jsonify(result)

@user_bp.route("/general/getcurrentstaffandcharacter", methods=["GET"])
def get_current_staff_and_character():
    redis_client = current_app.redis_client
    token = request.headers.get("Authorization")[7:]
    decoded_token = decode_token(token)  # Decode the created token
    jti = decoded_token["jti"]  # Extract the `jti` from the token payload
    for key in redis_client.scan_iter():
        value = redis_client.get(key)
        if value == jti:
            user = db.session.query(User, Staff, Character).join(
                Staff, User.staff_id == Staff.staff_id).join(
                Character, Staff.character_id == Character.character_id
            ).filter(User.user_name == get_jwt_identity()).first()
            result = {
                "staffName": user.Staff.staff_name,
                "characterName": user.Character.character_name,
            }
            return jsonify(result)


    return {"error": "Key not found for given jti"}, 404

@user_bp.route("/user/changepassword", methods=["POST"])
def change_password():
    data = request.get_json()
    old_password = data.get("currentPassword")
    new_password = data.get("newPassword")
    staff_id = data.get("staffId")
    iv = data.get("iv")  # Get the IV from the request
    print(data)
    secret_key = "6f8e6f9178b12c08dce94bcf57b8df22"  # Same key used in the frontend
    decrypt_old_password_result = decrypt_password(old_password, iv, secret_key)
    second_encrypted_password = hashlib.md5(decrypt_old_password_result.encode()).hexdigest()
    decrypt_new_password_result = decrypt_password(new_password, iv, secret_key)
    second_encrypted_new_password = hashlib.md5(decrypt_new_password_result.encode()).hexdigest()

    user = db.session.query(User, Staff, Character).join(
        Staff, User.staff_id == Staff.staff_id).join(
        Character, Staff.character_id == Character.character_id
    ).filter(Staff.staff_id == staff_id).first()
    print(user)

    if user and user.User.user_passwd == second_encrypted_password:
        user.User.user_passwd = second_encrypted_new_password
        db.session.commit()
        return {"success": "Password changed successfully"}, 200
    
    return {"error": "Old password is incorrect"}, 400


@user_bp.route("/user/createuser", methods=["POST"])
def create_user():
    data = request.get_json()
    user_name = data.get("userName")
    user_password = data.get("userPassword")
    staff_id = data.get("staffId")
    iv = data.get("iv")
    print(data)
    secret_key = "6f8e6f9178b12c08dce94bcf57b8df22"
    new_pw = decrypt_password(user_password, iv, secret_key)
    db_pw = hashlib.md5(new_pw.encode()).hexdigest()
    existing = (db.session.query(User).filter(User.user_name == user_name).first())
    if existing:
        return {"error" : "user name exists"}, 400
    else:
        new_entity = User(user_name = user_name, user_password = db_pw, staff_id = staff_id)
        db.session.add(new_entity)
        db.session.commit()
    return{"success":"new user added"}, 200

@user_bp.route("/user/createstaff", methods=["POST"])
def create_staff():
    data = request.get_json()
    staff_name = data.get("staffName")
    character_id = data.get("characterId")
    department_id = data.get("departmentId")
    existing = (db.session.query(Staff).filter(Staff.staff_name == staff_name).first())
    if existing:
        return {"errror":"staff name exists"}, 400
    else:
        new_entity = Staff(staff_name = staff_name, character_id = character_id, department_id = department_id)
        db.session.add(new_entity)
        db.session.commit()
    return {"success":"new staff added"}, 200

@user_bp.route("/user/createcharacter", methods=["POST"])
def create_character():
    data = request.get_json()
    character_name = data.get("characterName")
    existing = (db.session.query(Character).filter(Character.character_name == character_name).first())
    if existing:
        return {"errror":"character name exists"}, 400
    else:
        new_entity = Character(character_name = character_name)
        db.session.add(new_entity)
        db.session.commit()
    return {"success":"new character added"}, 200


@user_bp.route('/user/deleteuser', methods=["POST"])
def delete_user():
    data = request.get_json()
    user_id = data.get("userId")
    existing = (db.session.query(User).filter(User.user_id == user_id).first())
    if not existing:
        return {"error":"user doesnt exist"}, 400
    else:
        db.session.delete(existing)
        db.session.commit()
        return {"success":"user deleted"}, 200
#账号更换用户， 改变staffid
@user_bp.route('/user/modifyaccountstaff', methods=["POST"])
def modify_user_staff():
    data = request.get_json()
    user_id = data.get("userId")
    new_staff_id = data.get("staffId")
    existing = (db.session.query(User).filter(User.user_id == user_id).first())
    if not existing:
        return {"error":"user doesnt exist"}, 400
    else:
        existing.staff_id = new_staff_id
        db.session.commit()
        return {"success":"account holder staff modified"}, 200

#用户角色变更 更改character id
@user_bp.route('/user/modifiystaffcharacter', methods=["POST"])
def modify_staff_character():
    data = request.get_json()
    staff_id = data.get("staffId")
    new_character_id = data.get("characterId")
    new_department_id = data.get("departmentId")
    existing = (db.session.query(Staff).filter(Staff.staff_id == staff_id).first())
    if not existing:
        return {"error":"staff doesnt exist"}, 400
    else:
        existing.character_id = new_character_id
        existing.department_id = new_department_id
        db.sesison.commit()
    return{"success":"staff character modified"}, 200




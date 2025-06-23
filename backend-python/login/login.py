from Crypto.Cipher import AES
import base64
from flask import request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, get_jwt, jwt_required, get_jwt_identity, decode_token
from datetime import timedelta
import hashlib

from models import *
from flask import Blueprint, jsonify, request, current_app
from app_config import db
from logger import logger
login_bp = Blueprint("login_bp", __name__)

def decrypt_password(encrypted_password, iv, secret_key):
    # Decode Base64 encoded password and IV
    encrypted_password_bytes = base64.b64decode(encrypted_password) 
    iv_bytes = base64.b64decode(iv)
    logger.debug(iv_bytes)

    # Create AES cipher in CBC mode with the provided IV
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_CBC, iv=iv_bytes)
    
    # Decrypt the password (ciphertext)
    decrypted_password = cipher.decrypt(encrypted_password_bytes)

    # Unpad the decrypted password (remove PKCS7 padding)
    decrypted_password = decrypted_password[:-decrypted_password[-1]].decode('utf-8')
    
    return decrypted_password

@login_bp.route('/login', methods=['POST'])
def login():
    redis_client = current_app.redis_client
    data = request.json
    username = data.get("username")
    encrypted_password = data.get("password")
    iv = data.get("iv")  # Get the IV from the request
    logger.debug(encrypted_password)
    secret_key = "6f8e6f9178b12c08dce94bcf57b8df22"  # Same key used in the frontend
    decrypt_password_result = decrypt_password(encrypted_password, iv, secret_key)
    second_encrypted_password = hashlib.md5(decrypt_password_result.encode()).hexdigest()
    logger.debug(decrypt_password_result)
    user = db.session.query(User, Staff, Character).join(
        Staff, User.staff_id == Staff.staff_id).join(
        Character, Staff.character_id == Character.character_id
    ).filter(User.user_name == username).first()

    if user and user.User.user_passwd == second_encrypted_password:
        # Check if the user already has an active session
        previous_jti = redis_client.get(username)
        if previous_jti:
            # Revoke the previous session by deleting the old jti from Redis
            redis_client.delete(previous_jti)

        # Generate a new access token
        expires = timedelta(days=1)
        access_token = create_access_token(identity=username, expires_delta=expires)
        decoded_token = decode_token(access_token)  # Decode the created token
        jti = decoded_token["jti"]  # Extract the `jti` from the token payload

        # Store the new `jti` in Redis keyed by the username, valid for 1 day
        redis_client.setex(username, timedelta(days=7), jti)

        # Also store the `jti` keyed by the token's `jti` to handle logout/revocation
        redis_client.setex(jti, timedelta(days=7), "valid")

        return jsonify(access_token=access_token, role=user.Character.character_id, staffid=user.User.staff_id), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

@login_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    redis_client = current_app.redis_client
    # Get the current token's jti from the JWT payload
    jti = get_jwt()["jti"]
    username = get_jwt_identity()

    # Remove both the token-specific jti and the user's active session from Redis
    redis_client.delete(jti)
    redis_client.delete(username)
    
    return jsonify({"msg": "Access token revoked"}), 200
@jwt_required()
def current_user():
    # Retrieve the identity of the current user
    username = get_jwt_identity()
    # Query the database to get user details (assuming you have a User model)
    user = User.query.filter_by(user_name=username).first()
    staff = Staff.query.filter_by(staff_id=user.staff_id).first()
    staff_name = staff.staff_name
    staff_id = staff.staff_id
    role = staff.character_id
    department = Department.query.filter_by(department_id=staff.department_id).first()
    department_name = department.department_name
    if user:
        user_info = {
            "username": user.user_name,
            # "email": user.email,
            "role": role,
            "staffName":staff_name,
            "staffId":staff_id,
            "departmentName":department_name
        }
        return jsonify(user_info), 200
    else:
        return jsonify({"msg": "User not found"}), 404

@jwt_required()
def current_user_info():
    """
    return current character, staff and department object
    """
    username = get_jwt_identity()
    user_info = db.session.query(User, Staff, Character, Department).join(
        Staff, User.staff_id == Staff.staff_id
    ).join(
        Character, Staff.character_id == Character.character_id
    ).join(
        Department, Staff.department_id == Department.department_id
    ).filter(User.user_name == username).first()
    character = user_info.Character
    staff = user_info.Staff
    department = user_info.Department
    return character, staff, department

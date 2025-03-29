from flask import Blueprint, jsonify, request
import os
from app_config import db
from models import *
from file_locations import IMAGE_STORAGE_PATH, FILE_STORAGE_PATH, IMAGE_UPLOAD_PATH

shoe_manage_bp = Blueprint("shoe_manage_bp", __name__)


@shoe_manage_bp.route("/shoemanage/uploadshoeimage", methods=["POST"])
def upload_shoe_image():
    shoe_rid = request.form.get("shoeRid")
    shoe_id = request.form.get('shoeId')
    shoe_color_name = request.form.get("shoeColorName")
    shoe_color_id = request.form.get("shoeColorId")
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 500
    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 500

    folder_path = os.path.join(IMAGE_UPLOAD_PATH, "shoe", shoe_rid, shoe_color_name)
    print("shoe image stored should be in")
    print(folder_path)
    if os.path.exists(folder_path) == False:
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, "shoe_image.jpg")
    file.save(file_path)
    print("shoe_rid is " + str(shoe_rid))
    shoe_type = (
        db.session.query(Shoe, ShoeType, Color)
        .join(ShoeType, Shoe.shoe_id == ShoeType.shoe_id)
        .join(Color, ShoeType.color_id == Color.color_id)
        .filter(Shoe.shoe_rid == shoe_rid)
        .filter(Color.color_id == shoe_color_id)
        .first()
    )
    db_path = os.path.join("shoe", shoe_rid, shoe_color_name, "shoe_image.jpg")
    shoe_type.ShoeType.shoe_image_url = db_path
    db.session.commit()
    return jsonify({"message": "Shoe image uploaded successfully"})


@shoe_manage_bp.route("/shoemanage/addnewshoe", methods=["POST"])
def add_new_shoe():
    shoe_rid = request.json.get("shoeRId")
    shoe_designer = request.json.get("shoeDesigner")
    shoe_color = request.json.get("shoeColor")
    existing_shoe = db.session.query(Shoe).filter(Shoe.shoe_rid == shoe_rid).first()
    try:
        existing_shoe = db.session.query(Shoe).filter(Shoe.shoe_rid == shoe_rid).first()
        if not existing_shoe:
            shoe = Shoe(
                shoe_rid=shoe_rid,
                shoe_designer=shoe_designer,
            )
            db.session.add(shoe)
            db.session.commit()
        else:
            shoe = existing_shoe

        # if shoe_type_exists
        if (
            db.session.query(ShoeType)
            .filter(ShoeType.color_id == shoe_color, ShoeType.shoe_id == shoe.shoe_id)
            .first()
        ):
            return jsonify({"message": "该鞋款已存在"})
        shoe_type = ShoeType(shoe_id=shoe.shoe_id, color_id=shoe_color)
        db.session.add(shoe_type)
        db.session.commit()
        return jsonify({"message": "Shoe added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@shoe_manage_bp.route("/shoemanage/editshoetype", methods=["POST"])
def edit_shoe_type():
    shoe_type_id = request.json.get("shoeTypeId")
    shoe_color = request.json.get("shoeColor")
    entity = (
        db.session.query(ShoeType).filter(ShoeType.shoe_type_id == shoe_type_id).first()
    )
    if entity:
        entity.color_id = shoe_color
        db.session.commit()
    else:
        return jsonify({"error": "entity not found"}), 500
    return jsonify({"message": "Shoe Type updated successfully"}), 200


@shoe_manage_bp.route("/shoemanage/addshoetype", methods=["POST"])
def add_shoe_type():
    color_ids = request.json.get("colorId")
    shoe_id = request.json.get("shoeId")
    existing_color = []
    for color_id in color_ids:
        shoe_type_existing = (
            db.session.query(ShoeType)
            .filter(ShoeType.color_id == color_id, ShoeType.shoe_id == shoe_id)
            .first()
        )
        if shoe_type_existing:
            existing_color.append(db.session.query(Color).filter(Color.color_id == color_id).first().color_name)
        else:
            shoe_type_entity = ShoeType()
            shoe_type_entity.color_id = color_id
            shoe_type_entity.shoe_id = shoe_id
            db.session.add(shoe_type_entity)
    if len(existing_color) == len(color_ids):
        return jsonify({"message": "all color exists already"}), 400
    else:
        db.session.commit()
        existing_color_str = ''.join(existing_color)
        return jsonify({"message": "shoe type added except " + existing_color_str}), 200


@shoe_manage_bp.route("/shoemanage/deleteshoetype", methods=["POST"])
def delete_shoe_type():
    shoe_type_id = request.json.get("shoeTypeId")
    shoe_id = request.json.get("shoeId")
    existing_shoe = (db.session.query(Shoe).filter_by(shoe_id = shoe_id).first())
    existing_shoe_type = (db.session.query(ShoeType).filter(ShoeType.shoe_type_id == shoe_type_id).first())
    if not existing_shoe_type or not existing_shoe:
        return jsonify({"error":"delete shoe type failed, shoetype or shoe not found"}), 400
    else:
        shoe_rid = existing_shoe.shoe_rid
        shoe_color_name = existing_shoe_type
        path_to_img = existing_shoe_type.shoe_image_url
        if path_to_img:
            img_path = os.path.join(IMAGE_UPLOAD_PATH, path_to_img)
            path_to_delete = '/'.join(path_to_img.split('/')[:-1])
            folder_path = os.path.join(IMAGE_UPLOAD_PATH, path_to_delete)
            if os.path.exists(img_path):
                os.remove(img_path)
            if os.path.exists(folder_path):
                os.rmdir(folder_path)
            if os.path.exists(img_path) or os.path.exists(folder_path):
                print("delete dir failed")
                return jsonify({"error": "removing path failed"}), 400
        db.session.delete(existing_shoe_type)
        db.session.commit()
        return jsonify({"success":"entity and local path removed"}), 200
    # if existing_shoe_type:
    #     db.sesison.delete(existing_shoe_type)
    #     return jsonify({"message":"delete shoe type OK"}), 200
    # else:
    #     return


@shoe_manage_bp.route("/shoemanage/addshoe", methods=["POST"])
def add_shoe():
    shoe_rid = request.json.get("shoeRid")
    shoe_desinger = request.json.get("shoeDesigner")
    shoe_department_id = request.json.get("shoeDepartmentId")
    existing_shoe = db.session.query(Shoe).filter(Shoe.shoe_rid == shoe_rid).first()
    if existing_shoe:
        return jsonify({"error": "shoe_rid already exists"}), 200
    else:
        shoe_entity = Shoe()
        shoe_entity.shoe_rid = shoe_rid
        shoe_entity.shoe_designer = shoe_desinger
        shoe_entity.shoe_department_id = shoe_department_id
        db.session.add(shoe_entity)
        db.session.commit()
        return jsonify({"message": "shoe added"}), 200


@shoe_manage_bp.route("/shoemanage/editshoe", methods=["POST"])
def edit_shoe():
    shoe_id = request.json.get("shoeId")
    shoe_rid = request.json.get("shoeRid")
    shoe_designer = request.json.get("shoeDesigner")
    shoe_department_id = request.json.get("shoeDepartmentId")
    existing_shoe = db.session.query(Shoe).filter(Shoe.shoe_id == shoe_id).first()
    if existing_shoe:
        existing_shoe.shoe_rid = shoe_rid
        existing_shoe.shoe_designer = shoe_designer
        existing_shoe.shoe_department_id = shoe_department_id
        db.session.commit()
        return jsonify({"message": "edit shoe OK"}), 200
    else:
        return jsonify({"error": "shoe not found given shoe_id"}), 400

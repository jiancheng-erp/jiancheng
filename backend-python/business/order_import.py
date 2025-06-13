from flask import Blueprint, jsonify, request, send_file
from sqlalchemy.dialects.mysql import insert
import pandas as pd
import datetime
import time
from werkzeug.utils import secure_filename
import os
import json
import shutil
from models import *
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH
from logger import logger
from app_config import db

order_import_bp = Blueprint("order_import_bp", __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"xls", "xlsx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@order_import_bp.route("/orderimport/getuploadorder", methods=["POST"])
def upload_order():
    time_s = time.time()
    # Check if the request has the file part
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    # If the user does not select a file
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_new_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") + filename
        file_path = os.path.join(FILE_STORAGE_PATH, file_new_name)
        file.save(file_path)

        try:
            # Process the file
            df = pd.read_excel(file_path, header=1)
            df.rename(
                columns={
                    "工厂型号": "inheritId",
                    "客户型号": "customerId",
                    "中文颜色": "colorCN",
                    "英文颜色": "colorEN",
                    "配码编号": "sizeId",
                    "对/件": "pairEachBox",
                    "件数": "boxCount",
                    "双数": "pairCount",
                    "货币单位": "currencyType",
                    "单价": "pricePerPair",
                    "总价": "totalPrice",
                },
                inplace=True,
            )

            # Replace NaN values with 0
            df.fillna(0, inplace=True)

            # Transform the dataframe as needed
            data_list = df.to_dict(orient="records")

            # Transform and filter data as per your requirements
            filtered_data = transform_and_filter_data(data_list)
            return_list = [
                item for sublist in filtered_data.values() for item in sublist
            ]

            # Ensure proper encoding of the response
            response = {
                "message": "File processed and data inserted successfully",
                "tempFileName": file_new_name,
                "data": return_list,
            }
            return app.response_class(
                response=json.dumps(response, ensure_ascii=False),
                status=200,
                mimetype="application/json",
            )

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": str(e)}), 500
    time_t = time.time()
    logger.debug("time taken for /getuploadorder is " + str(time_t - time_s))
    return jsonify({"error": "Invalid file type"}), 400


def transform_and_filter_data(data_list):
    from collections import defaultdict

    def generate_key(item):
        return (item["inheritId"], item["customerId"], item["colorCN"], item["colorEN"])

    filtered_data_dict = defaultdict(list)
    for item in data_list:
        key = generate_key(item)
        filtered_data_dict[key].append(item)
    return filtered_data_dict


@order_import_bp.route("/orderimport/confirmimportorder", methods=["POST"])
def confirm_import_order():
    time_s = time.time()
    file_name = request.json.get("fileName")
    order_info = request.json.get("orderInfo")
    if not file_name or not order_info:
        return jsonify({"error": "Invalid request"}), 400
    order_rid = order_info["orderRId"]
    customer_id = order_info["customerId"]
    order_date = order_info["orderStartDate"]
    order_deadline = order_info["orderEndDate"]
    order_status = order_info["status"]
    order_salesman = order_info["salesman"]

    try:
        df = pd.read_excel(os.path.join(FILE_STORAGE_PATH, file_name), header=1)
        df.rename(
            columns={
                "工厂型号": "inheritId",
                "客户型号": "customerId",
                "中文颜色": "colorCN",
                "英文颜色": "colorEN",
                "配码编号": "sizeId",
                "对/件": "pairEachBox",
                "件数": "boxCount",
                "双数": "pairCount",
                "货币单位": "currencyType",
                "单价": "pricePerPair",
                "总价": "totalPrice",
            },
            inplace=True,
        )
        df.fillna(0, inplace=True)

        data_list = df.to_dict(orient="records")
        filtered_data = transform_and_filter_data(data_list)
        exist_order = Order.query.filter_by(order_rid=order_rid).first()
        if exist_order:
            return jsonify({"error": "Order Name already exists"}), 400

        new_order = Order(
            order_rid=order_rid,
            customer_id=customer_id,
            start_date=order_date,
            end_date=order_deadline,
            salesman=order_salesman,
            production_list_upload_status="0",
            amount_list_upload_status="1",
        )
        db.session.add(new_order)
        db.session.flush()
        
        os.mkdir(os.path.join(FILE_STORAGE_PATH, order_rid))
        new_file_name = "生产数量表.xlsx"
        shutil.copy(
            os.path.join(FILE_STORAGE_PATH, file_name),
            os.path.join(FILE_STORAGE_PATH, order_rid, new_file_name),
        )

        new_order_id = Order.query.filter_by(order_rid=order_rid).first().order_id
        new_order_status = OrderStatus(
            order_id=new_order_id,
            order_current_status=order_status,
            order_status_value=1,
        )
        db.session.add(new_order_status)
        db.session.flush()

        for key, items in filtered_data.items():
            order_shoe_rid = key[0]
            customer_shoe_id = key[1]
            color_chinese_name = key[2]
            color_english_name = key[3]

            # Ensure the Shoe exists
            shoe_obj = Shoe.query.filter_by(shoe_rid=order_shoe_rid).first()
            if not shoe_obj:
                shoe_obj = Shoe(shoe_rid=order_shoe_rid)
                db.session.add(shoe_obj)
                db.session.flush()

            # Ensure the Color exists (if not, create it)
            color_obj = Color.query.filter_by(
                color_name=color_chinese_name, color_en_name=color_english_name
            ).first()

            if not color_obj:
                # Create the Color if it doesn't exist
                color_obj = Color(
                    color_name=color_chinese_name, color_en_name=color_english_name
                )
                db.session.add(color_obj)
                db.session.flush()

            # Ensure the ShoeType exists
            shoe_type = ShoeType.query.filter_by(
                shoe_id=shoe_obj.shoe_id,
                color_id=color_obj.color_id
            ).first()

            if not shoe_type:
                # Create the ShoeType if it doesn't exist
                shoe_type = ShoeType(
                    shoe_id=shoe_obj.shoe_id,
                    color_id=color_obj.color_id,
                    shoe_image_url=""  # Assuming empty initially, or you can pass an image URL
                )
                db.session.add(shoe_type)
                db.session.flush()

            # Create OrderShoe (if it doesn't exist) and associate multiple OrderShoeTypes
            order_shoe = OrderShoe.query.filter_by(
                order_id=new_order_id, shoe_id=shoe_obj.shoe_id
            ).first()

            if not order_shoe:
                # Create the OrderShoe if it doesn't exist
                order_shoe = OrderShoe(
                    order_id=new_order_id,
                    shoe_id=shoe_obj.shoe_id,
                    customer_product_name=customer_shoe_id,
                    production_order_upload_status="0",
                    process_sheet_upload_status="0",
                    adjust_staff="",
                )
                db.session.add(order_shoe)
                db.session.flush()

                os.mkdir(os.path.join(FILE_STORAGE_PATH, order_rid, order_shoe_rid))

                # Create OrderShoeStatus for the new OrderShoe
                order_shoe_status = OrderShoeStatus(
                    order_shoe_id=order_shoe.order_shoe_id,
                    current_status=0,
                    current_status_value=0,
                )
                db.session.add(order_shoe_status)
                db.session.flush()
                order_shoe_production_info = OrderShoeProductionInfo(
                    is_cutting_outsourced=0,
                    is_sewing_outsourced=0,
                    is_molding_outsourced=0,
                    is_material_arrived=0,
                    order_shoe_id=order_shoe.order_shoe_id,
                )
                db.session.add(order_shoe_production_info)
                db.session.flush()

            # Check if an OrderShoeType already exists for this combination of OrderShoe and ShoeType
            order_shoe_type = OrderShoeType.query.filter_by(
                order_shoe_id=order_shoe.order_shoe_id,
                shoe_type_id=shoe_type.shoe_type_id
            ).first()

            if not order_shoe_type:
                # Create OrderShoeType if it doesn't exist for this combination
                order_shoe_type = OrderShoeType(
                    order_shoe_id=order_shoe.order_shoe_id,
                    shoe_type_id=shoe_type.shoe_type_id,
                )
                db.session.add(order_shoe_type)
                db.session.flush()
                

            # Now, proceed to add order_shoe_batch details linked to the order_shoe_type_id
            arr = []
            order_shoe_type_id = order_shoe_type.order_shoe_type_id  # Use order_shoe_type_id for the batch info

            for item in items:
                order_shoe_batch = OrderShoeBatchInfo(
                    order_shoe_type_id=order_shoe_type_id,  # Use the newly created or found order_shoe_type_id
                    name=item["sizeId"],
                    total_amount=item["pairCount"],
                    cutting_amount=0,
                    sewing_amount=0,
                    pre_sewing_amount=0,
                    molding_amount=0,
                    size_34_amount=0,
                    size_35_amount=item["7/35"],
                    size_36_amount=item["7.5/36"],
                    size_37_amount=item["8/37"],
                    size_38_amount=item["8.5/38"],
                    size_39_amount=item["9/39"],
                    size_40_amount=item["9.5/40"],
                    size_41_amount=item["10/41"],
                    size_42_amount=item["10.5/42"],
                    size_43_amount=item["11/43"],
                    size_44_amount=item["12/44"],
                    size_45_amount=item["13/45"],
                    total_price=item["totalPrice"],
                )
                arr.append(order_shoe_batch)

            db.session.add_all(arr)
        db.session.commit()

        result = jsonify({"message": "Order imported successfully"}), 200

    except Exception as e:
        result = jsonify({"error": str(e)}), 500

    time_t = time.time()
    logger.debug("time taken for /confirmimportorder is " + str(time_t - time_s))
    return result



@order_import_bp.route("/orderimport/submitdoc", methods=["POST"])
def submit_doc():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_type = request.form.get("fileType")
    order_rid = request.form.get("orderRid")
    logger.debug(file_type, order_rid)

    if file_type == "0":
        file_path = os.path.join(FILE_STORAGE_PATH, order_rid, "生产订单.xlsx")
        logger.debug(file_path)
        file.save(file_path)
        order = db.session.query(Order).filter_by(order_rid=order_rid).first()
        # order.production_list_upload_status = "0"
        db.session.commit()
    elif file_type == "1":
        file_path = os.path.join(FILE_STORAGE_PATH, order_rid, "生产数量表.xlsx")
        file.save(file_path)
        order = db.session.query(Order).filter_by(order_rid=order_rid).first()
        order.amount_list_upload_status = "1"
        db.session.commit()
    elif file_type == "2":
        file_path = os.path.join(FILE_STORAGE_PATH, order_rid, "包装资料.xlsx")
        file.save(file_path)
        order = db.session.query(Order).filter_by(order_rid=order_rid).first()
        order.production_list_upload_status = "2"
        db.session.commit()
    return jsonify({"message": "File submitted successfully"}), 200


@order_import_bp.route("/orderimport/downloadorderdoc", methods=["GET"])
def download_order_doc():
    file_type = request.args.get("filetype")
    order_rid = request.args.get("orderrid")

    if not file_type or not order_rid:
        return jsonify({"error": "Invalid request"}), 400

    # Define the file path based on file_type
    if file_type == "0":
        file_path = os.path.join(FILE_STORAGE_PATH, order_rid, "生产订单.xlsx")
        new_filename = (
            f"{order_rid}_生产订单.xlsx"  # New filename to send to the client
        )
    elif file_type == "1":
        file_path = os.path.join(FILE_STORAGE_PATH, order_rid, "生产数量表.xlsx")
        new_filename = (
            f"{order_rid}_生产数量表.xlsx"  # New filename to send to the client
        )
    elif file_type == "2":
        file_path = os.path.join(FILE_STORAGE_PATH, order_rid, "包装资料.xlsx")
        new_filename = (
            f"{order_rid}_包装资料.xlsx"  # New filename to send to the client
        )
    else:
        return jsonify({"error": "Invalid file type"}), 400

    # Check if the file exists
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        # Send the file for download with a new filename
        return send_file(file_path, as_attachment=True, download_name=new_filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

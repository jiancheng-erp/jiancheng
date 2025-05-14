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
from api_utility import format_date
from decimal import Decimal

from app_config import db

from flask import current_app
from event_processor import EventProcessor
from wechat_api.send_message_api import send_massage_to_users


order_create_bp = Blueprint("order_create_bp", __name__)

NEW_ORDER_STATUS = 6
NEW_ORDER_STEP_OP = 12
NEW_ORDER_NEXT_STEP_OP = 13
NEW_ORDER_SHOE_OP = 2

department_name = "业务部"
# Allowed file extensions
ALLOWED_EXTENSIONS = {"xls", "xlsx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@order_create_bp.route("/ordercreate/createneworder", methods=["POST"])
def create_new_order():
	time_s = time.time()
	order_info = request.json.get("orderInfo")
	if not order_info:
		return jsonify({'error': 'invalid request'}),400
	order_rid = order_info["orderRId"]
	order_cid = order_info["orderCid"]
	batch_info_type_id = order_info["batchInfoTypeId"]
	customer_id = order_info["customerId"]
	order_start_date = order_info["orderStartDate"]
	order_end_date = order_info["orderEndDate"]
	# 订单对应下发业务经理, 应该为staff_id
	supervisor_id = order_info['supervisorId']
	# new order status should be fixed
	order_status = NEW_ORDER_STATUS
	order_salesman_id = order_info["salesmanId"]
	order_shoe_type_list = order_info["orderShoeTypes"]
	customer_shoe_names = order_info["customerShoeName"]
	rid_exist_order = Order.query.filter_by(order_rid = order_rid).first()
	if rid_exist_order:
		print("order rid exists, must be unique")
		return jsonify({'message':'订单号或客户订单号已经存在 单号不可重复'}), 400

	new_order = Order(
    	order_rid = order_rid,
    	order_cid = order_cid,
		batch_info_type_id = batch_info_type_id,
    	customer_id = customer_id,
    	start_date = order_start_date,
    	end_date = order_end_date,
    	salesman_id = order_salesman_id,
    	production_list_upload_status="0",
    	amount_list_upload_status="0",
		supervisor_id = supervisor_id
    	)

	db.session.add(new_order)
	db.session.flush()
	### os mkdir 
	# os.mkdir(os.path.join(FILE_STORAGE_PATH, order_rid))

	new_order_id = Order.query.filter_by(order_rid = order_rid).first().order_id
	new_order_status = OrderStatus(
		order_id = new_order_id,
		order_current_status = order_status,
		order_status_value = 0,)
	db.session.add(new_order_status)
	db.session.flush()

	shoe_type_id_to_shoe_type = {shoe_type['shoeTypeId']:shoe_type for shoe_type in order_shoe_type_list}
	shoe_type_ids = shoe_type_id_to_shoe_type.keys()
	shoe_id_to_rid = {}
	shoe_type_id_to_shoe_id = {}
	for shoe_type_id in shoe_type_ids:
		db_shoe_entity = ShoeType.query.filter_by(shoe_type_id = shoe_type_id).first()
		shoe_type_id_to_shoe_id[shoe_type_id] = db_shoe_entity.shoe_id
		shoe_id_to_rid[db_shoe_entity.shoe_id] = shoe_type_id_to_shoe_type[shoe_type_id]["shoeRid"] 

	shoe_id_to_order_shoe_id = {}

	### for every shoe
	for shoe_id in shoe_id_to_rid.keys():
		existing_order_shoe = OrderShoe.query.filter_by(
			order_id = new_order_id, shoe_id = shoe_id
		).first()
		if not existing_order_shoe:
			customer_product_name = customer_shoe_names[shoe_id_to_rid[shoe_id]]
			new_order_shoe_entity = OrderShoe(
				order_id = new_order_id,
				shoe_id = shoe_id,
				customer_product_name = customer_product_name,
				production_order_upload_status = "0",
				process_sheet_upload_status = "0",
				adjust_staff = "",
				business_material_remark = "",
				business_technical_remark = "")
			db.session.add(new_order_shoe_entity)
			db.session.flush()

			# os.mkdir(os.path.join(FILE_STORAGE_PATH, order_rid, shoe_id_to_rid[shoe_id]))

			new_order_shoe_status_entity = OrderShoeStatus(
				order_shoe_id = new_order_shoe_entity.order_shoe_id,
				current_status = 0,
				current_status_value = 0,)
			db.session.add(new_order_shoe_status_entity)
			db.session.flush()

			new_order_shoe_production_info_entity = OrderShoeProductionInfo(
				is_cutting_outsourced = 0,
				is_sewing_outsourced = 0,
				is_molding_outsourced = 0,
				is_material_arrived = 0,
				order_shoe_id = new_order_shoe_entity.order_shoe_id)
			
			db.session.add(new_order_shoe_production_info_entity)
			db.session.flush()
			shoe_id_to_order_shoe_id[shoe_id] = new_order_shoe_entity.order_shoe_id

	### for every shoe_type
	for shoe_type_id in shoe_type_ids:
		## create ordershoetype
		shoe_type = shoe_type_id_to_shoe_type[shoe_type_id]
		shoe_id = shoe_type_id_to_shoe_id[shoe_type_id]
		order_shoe_id = shoe_id_to_order_shoe_id[shoe_id]
		quantity_mapping = shoe_type["quantityMapping"]
		batch_info = shoe_type["orderShoeTypeBatchInfo"]
		#业务部改动 客户颜色
		customer_color_name = shoe_type["customerColorName"]
		existing_entity = OrderShoeType.query.filter_by(
			order_shoe_id = order_shoe_id,
			shoe_type_id = shoe_type_id).first()
		if not existing_entity:
			new_entity = OrderShoeType(
				order_shoe_id = order_shoe_id,
				shoe_type_id = shoe_type_id,
				customer_color_name = customer_color_name)
			db.session.add(new_entity)
			db.session.flush()
		else:
			new_entity = existing_entity
		batch_info_entity_array = []
		for batch in batch_info:
			quantity_per_ratio = float(quantity_mapping[str(batch['packagingInfoId'])])
			new_entity = OrderShoeBatchInfo(
				order_shoe_type_id = new_entity.order_shoe_type_id,
				name = batch['packagingInfoName'],
				size_34_amount = int(batch['size34Ratio']*quantity_per_ratio),
				size_35_amount = int(batch['size35Ratio']*quantity_per_ratio),
				size_36_amount = int(batch['size36Ratio']*quantity_per_ratio),
				size_37_amount = int(batch['size37Ratio']*quantity_per_ratio),
				size_38_amount = int(batch['size38Ratio']*quantity_per_ratio),
				size_39_amount = int(batch['size39Ratio']*quantity_per_ratio),
				size_40_amount = int(batch['size40Ratio']*quantity_per_ratio),
				size_41_amount = int(batch['size41Ratio']*quantity_per_ratio),
				size_42_amount = int(batch['size42Ratio']*quantity_per_ratio),
				size_43_amount = int(batch['size43Ratio']*quantity_per_ratio),
				size_44_amount = int(batch['size44Ratio']*quantity_per_ratio),
				size_45_amount = int(batch['size45Ratio']*quantity_per_ratio),
				size_46_amount = int(batch['size46Ratio']*quantity_per_ratio),
				total_price = 0,
				total_amount = int(batch['totalQuantityRatio']*quantity_per_ratio),
				packaging_info_id = batch['packagingInfoId'],
				packaging_info_quantity = quantity_per_ratio)
			batch_info_entity_array.append(new_entity)
		db.session.add_all(batch_info_entity_array)
	print("order added to DB")
	db.session.commit()
	os.mkdir(os.path.join(FILE_STORAGE_PATH, order_rid))
	os.mkdir(os.path.join(FILE_STORAGE_PATH, order_rid, shoe_id_to_rid[shoe_id]))

	result = jsonify({"message": "Order imported successfully", "newOrderId":new_order_id}), 200
	# except Exception as e:
	# 	result = jsonify({"message": str(e)}, 500)
	time_t = time.time()
	print("time taken is " + str(time_t - time_s))
	return result


@order_create_bp.route("/ordercreate/updateprice", methods=["POST"])
def order_price_update():
	time_s = time.time()
	unit_price_form = request.json.get('unitPriceForm')
	currency_type_form = request.json.get('currencyTypeForm')
	
	for order_shoe_type_id in unit_price_form.keys():
		unit_price = float(unit_price_form[order_shoe_type_id])
		currency_type = str(currency_type_form[order_shoe_type_id])
		entity = (db.session.query(OrderShoeType)
			  .filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id)
			  .first())
		entity.unit_price = unit_price
		entity.currency_type = currency_type
	db.session.commit()
	# find all orderShoeTypes belong to this order
	# db.session.query(OrderShoeType)
	# .filter(OrderShoeType.order_shoe_type_id == )
	# sync_order_shoe_status(list(set(unit_price_form.keys()).union(set(currency_type_form.keys()))))
	time_t = time.time()
	print("time taken is update price is" + str(time_t - time_s))
	return jsonify({'msg':"ok"}), 200

@order_create_bp.route("/ordercreate/proceedevent", methods=["POST"])
def order_event_proceed():
	print("PROCEED")
	order_id = request.json.get('orderId')
	staff_id = request.json.get('staffId')
	price_all_filled = True
	print(order_id, staff_id)
	order_shoe_type_entities = (db.session.query(Order,OrderShoe,OrderShoeType)
							 .filter_by(order_id = order_id)
							 .join(OrderShoe,Order.order_id == OrderShoe.order_id)
							 .join(OrderShoeType,OrderShoe.order_shoe_id == OrderShoeType.order_shoe_id )
							 .all())
	for _, _, order_shoe_type_entity in order_shoe_type_entities:
		if order_shoe_type_entity.unit_price == 0 or order_shoe_type_entity.currency_type == None:
			price_all_filled = False
	order_entity = db.session.query(Order).filter_by(order_id = order_id).first()
	if order_entity != None and int(order_entity.production_list_upload_status) == 2 and price_all_filled:
		cur_time = format_date(datetime.datetime.now())
		new_event = Event(staff_id = staff_id, handle_time = cur_time, operation_id = NEW_ORDER_STEP_OP, event_order_id = order_id)
		processor: EventProcessor = current_app.config["event_processor"]
		processor.processEvent(new_event)
		db.session.add(new_event)
		db.session.commit()
		return jsonify({'msg':"OK"}), 200	

	else:
		return jsonify({"error":"order_shoe_type_id not found"}), 201

@order_create_bp.route("/ordercreate/sendprevious", methods=['POST'])
def order_send_previous():
	order_id = request.json.get("orderId")
	staff_id = request.json.get("staffId")
	staff_entity = (db.session.query(Staff).filter_by(staff_id = staff_id).first())
	if staff_entity:
		staff_name = staff_entity.staff_name
	else:
		return jsonify({"msg":"operator not found"}), 404
	entity = (db.session.query(Order,OrderStatus)
		   .filter_by(order_id = order_id)
		   .join(OrderStatus, Order.order_id == OrderStatus.order_id)
		   .first())
	if entity:
		_, status_entity = entity
		if status_entity.order_current_status == 6:
			status_entity.order_status_value = 0
			cur_time = format_date(datetime.datetime.now())
			revert_event = RevertEvent(revert_reason="业务部退回", responsible_department=department_name,
								initialing_department=department_name + staff_name, event_time = cur_time, order_id = order_id)
			db.session.add(revert_event)
			db.session.commit()
			return jsonify({"msg":"revert order"}), 200
		else:
			return jsonify({"error":"wrong status value for order"}), 400
	else:
		return jsonify({"error":"order not found"}), 404

@order_create_bp.route("/ordercreate/sendnext", methods=['POST'])
def order_next_step():
	order_id = request.json.get("orderId")
	staff_id = request.json.get("staffId")
	entity = (db.session.query(Order)
			.filter(Order.order_id == order_id)
			.first())
	order_rid = entity.order_rid
	order_shoe_rid = (db.session.query(OrderShoe, Shoe)
        .join(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
		.filter(OrderShoe.order_id == order_id)
		.first()).Shoe.shoe_rid
	if entity:
		cur_time = format_date(datetime.datetime.now())
		new_event = Event(staff_id = staff_id, handle_time = cur_time, operation_id = NEW_ORDER_NEXT_STEP_OP, event_order_id = order_id)
		processor: EventProcessor = current_app.config["event_processor"]
		processor.processEvent(new_event)
	message = f"订单已发出至总经理审核，订单号：{order_rid}，鞋型号：{order_shoe_rid}"
	users = "070d09bbc28c2cec22535b7ec5d1316b"
	send_massage_to_users(message, users)
	db.session.commit()
	return "Event Processed In Order Create API CALL", 200

@order_create_bp.route("/ordercreate/updateremark", methods=['POST'])
def order_remark_update():
	remark_form = request.json.get('orderShoeRemarkForm')
	order_shoe_id = remark_form['orderShoeId']
	business_technical_remark = remark_form['technicalRemark']
	business_material_remark = remark_form['materialRemark']
	order_shoe_entity = (db.session.query(OrderShoe)
		.filter(OrderShoe.order_shoe_id == order_shoe_id)
		.first())
	order_shoe_entity.business_material_remark = business_material_remark
	order_shoe_entity.business_technical_remark = business_technical_remark
	db.session.commit()
	return jsonify({'msg':"ok"}), 200

@order_create_bp.route("/ordercreate/updateordercid", methods=['POST'])
def order_cid_update():
	order_id = request.json.get('orderId')
	order_cid = request.json.get('orderCid')
	order_entity = (db.session.query(Order)
	.filter(Order.order_id == order_id)
	.first())
	if order_entity:
		order_entity.order_cid = order_cid
	else:
		return jsonify({"error":"order not found"}), 400
	db.session.commit()
	return jsonify({"msg":"ok"}), 200

@order_create_bp.route("/ordercreate/updateorderrid", methods=['POST'])
def order_rid_update():
	order_id = request.json.get('orderId')
	order_new_rid = request.json.get('orderNewRid')
	order_entity = (db.session.query(Order)
	.filter(Order.order_id == order_id)
	.first())
	if order_entity:
		order_entity.order_rid = order_new_rid
		db.session.commit()
		return jsonify({'msg':"update OK"}), 200
	else:
		return jsonify({'error': "order not found"}), 404

@order_create_bp.route("/ordercreate/updateordershoecustomername", methods=['POST'])
def order_shoe_customer_name_update():
	order_shoe_id = request.json.get("orderShoeId")
	order_shoe_customer_name = request.json.get("shoeCid")
	order_shoe_entity = (db.session.query(OrderShoe)
					  .filter(OrderShoe.order_shoe_id == order_shoe_id)
					  .first())
	if order_shoe_entity:
		order_shoe_entity.customer_product_name = order_shoe_customer_name
	else:
		return jsonify({"error":"order shoe not found"}), 500
	db.session.commit()
	return jsonify({"msg":"OK"}), 200


@order_create_bp.route("/ordercreate/updatecustomercolorname", methods=['POST'])
def order_shoe_type_customer_color_update():
	type_id_to_cus_color = request.json.get('orderShoeTypeCustomerColorForm')
	order_shoe_type_ids = type_id_to_cus_color.keys()
	for order_shoe_type_id in order_shoe_type_ids:
		entity = (db.session.query(OrderShoeType).filter(OrderShoeType.order_shoe_type_id == order_shoe_type_id).first())
		if entity:
			entity.customer_color_name = type_id_to_cus_color[order_shoe_type_id]
		else:
			return jsonify({"error":"order_shoe_type_id not found"}), 404
	db.session.commit()
	return jsonify({"msg":"customer color updated"}), 200
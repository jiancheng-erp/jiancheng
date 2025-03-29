from flask import Blueprint, jsonify, request

from app_config import db
from models import *
from api_utility import to_camel, to_snake
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError


customer_bp = Blueprint("customer_bp", __name__)

@customer_bp.route("/customer/getallcustomers", methods=["GET"])
def get_all_customers():
    customers = Customer.query.all()
    result = []
    for customer in customers:
        result.append(
            {
                "value": customer.customer_id,
                "label": customer.customer_name,
            }
        )
    return jsonify(result)

@customer_bp.route("/customer/getcustomerdetails", methods=["GET"])
def get_customer_details():
    customers = Customer.query.all()
    result = []
    for customer in customers:
        result.append(
            {
                "customerId": customer.customer_id,
                "customerName": customer.customer_name,
                "customerBrand": customer.customer_brand,
            }
        )
    return jsonify(result)

@customer_bp.route("/customer/getcustomerbatchinfo", methods=["GET"])
def get_customer_batch_info():
    result = []
    batch_info_type_attrs = BatchInfoType.__table__.columns.keys()
    batch_info_type_attrs.remove("batch_info_type_usage")
    batch_info_attrs = PackagingInfo.__table__.columns.keys()
    customer_id = request.args.get("customerid")
    entities = (db.session.query(PackagingInfo)
                    .filter(PackagingInfo.customer_id == customer_id)
                    )
    
    info_types = (db.session.query(BatchInfoType).filter_by(batch_info_type_usage = 0).all())
    for db_info_type in info_types:
        info_type_response = {}
        for attr in batch_info_type_attrs:
            if getattr(db_info_type, attr) != None:
                info_type_response[to_camel(attr)] = getattr(db_info_type, attr) 
        batch_info_list = []
        cur_entities = entities.filter(PackagingInfo.batch_info_type_id == db_info_type.batch_info_type_id).all()
        for batch_info in cur_entities:
            batch_info_response = {}
            for attr in batch_info_attrs:
                batch_info_response[to_camel(attr)] = getattr(batch_info, attr)
            batch_info_list.append(batch_info_response)
        info_type_response["batchInfoList"] = batch_info_list
        result.append(info_type_response)
    
    return jsonify(result), 200
@customer_bp.route("/customer/addcustomer", methods=["POST"])
def add_customer():
    customer_name = request.json.get("customerName")
    customer_brand = request.json.get("customerBrand")
    existing = (db.session.query(Customer).filter(and_(Customer.customer_name == customer_name ,Customer.customer_brand == customer_brand)).first())
    print(existing)
    if existing:
        return jsonify({"message":"客户及商标信息已存在"}), 400
    try:
        customer = Customer(
            customer_name=customer_name,
            customer_brand=customer_brand,
        )
        db.session.add(customer)
        db.session.commit()
        return jsonify({"message": "Customer added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@customer_bp.route("/customer/addcustomerbatchinfo", methods=["POST"])
def add_customer_batch_info():
    
    customer_id = request.json.get("customerId")
    print(request.json)
    packaging_info_name = request.json.get("packagingInfoName")
    packaging_info_locale = request.json.get("packagingInfoLocale")
    batch_info_type_id = request.json.get("batchInfoTypeId")
    size_34_ratio = request.json.get("size34Ratio")
    size_35_ratio = request.json.get("size35Ratio")
    size_36_ratio = request.json.get("size36Ratio")
    size_37_ratio = request.json.get("size37Ratio")
    size_38_ratio = request.json.get("size38Ratio")
    size_39_ratio = request.json.get("size39Ratio")
    size_40_ratio = request.json.get("size40Ratio")
    size_41_ratio = request.json.get("size41Ratio")
    size_42_ratio = request.json.get("size42Ratio")
    size_43_ratio = request.json.get("size43Ratio")
    size_44_ratio = request.json.get("size44Ratio")
    size_45_ratio = request.json.get("size45Ratio")
    size_46_ratio = request.json.get("size46Ratio")
    total_quantity_ratio = sum([int(single_ratio) if single_ratio != '' else 0 for single_ratio in [size_34_ratio,size_35_ratio
                ,size_36_ratio,size_37_ratio,size_38_ratio,size_39_ratio,
                size_40_ratio,size_41_ratio,size_42_ratio,size_43_ratio,
                size_44_ratio,size_45_ratio,size_46_ratio]])
    try:
        packaging_info_entity = PackagingInfo(
            customer_id=customer_id,
            packaging_info_name = packaging_info_name,
            packaging_info_locale = packaging_info_locale,
            batch_info_type_id = batch_info_type_id,
            size_34_ratio = size_34_ratio,
            size_35_ratio = size_35_ratio,
            size_36_ratio = size_36_ratio,
            size_37_ratio = size_37_ratio,
            size_38_ratio = size_38_ratio,
            size_39_ratio = size_39_ratio,
            size_40_ratio = size_40_ratio,
            size_41_ratio = size_41_ratio,
            size_42_ratio = size_42_ratio,
            size_43_ratio = size_43_ratio,
            size_44_ratio = size_44_ratio,
            size_45_ratio = size_45_ratio,
            size_46_ratio = size_46_ratio,
            total_quantity_ratio = total_quantity_ratio
        )
        db.session.add(packaging_info_entity)
        db.session.commit()
        return jsonify({"message": "Customer BatchInfo added successfully"})
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

@customer_bp.route("/customer/editbatchinfo", methods=["POST"])
def edit_packaging_info():
    packaging_info_id = request.json.get("packagingInfoId")
    packaging_info_name = request.json.get("packagingInfoName")
    packaging_info_locale = request.json.get("packagingInfoLocale")
    size_34_ratio = request.json.get("size34Ratio")
    size_35_ratio = request.json.get("size35Ratio")
    size_36_ratio = request.json.get("size36Ratio")
    size_37_ratio = request.json.get("size37Ratio")
    size_38_ratio = request.json.get("size38Ratio")
    size_39_ratio = request.json.get("size39Ratio")
    size_40_ratio = request.json.get("size40Ratio")
    size_41_ratio = request.json.get("size41Ratio")
    size_42_ratio = request.json.get("size42Ratio")
    size_43_ratio = request.json.get("size43Ratio")
    size_44_ratio = request.json.get("size44Ratio")
    size_45_ratio = request.json.get("size45Ratio")
    size_46_ratio = request.json.get("size46Ratio")
    total_quantity_ratio = sum([int(single_ratio) for single_ratio in [size_34_ratio,size_35_ratio
                ,size_36_ratio,size_37_ratio,size_38_ratio,size_39_ratio,
                size_40_ratio,size_41_ratio,size_42_ratio,size_43_ratio,
                size_44_ratio,size_45_ratio,size_46_ratio]])
    try:
        entity = PackagingInfo.query.filter_by(packaging_info_id=packaging_info_id).first()
        entity.packaging_info_name = packaging_info_name
        entity.packaging_info_locale = packaging_info_locale
        entity.size_34_ratio = size_34_ratio
        entity.size_35_ratio = size_35_ratio
        entity.size_36_ratio = size_36_ratio
        entity.size_37_ratio = size_37_ratio
        entity.size_38_ratio = size_38_ratio
        entity.size_39_ratio = size_39_ratio
        entity.size_40_ratio = size_40_ratio
        entity.size_41_ratio = size_41_ratio
        entity.size_42_ratio = size_42_ratio
        entity.size_43_ratio = size_43_ratio
        entity.size_44_ratio = size_44_ratio
        entity.size_45_ratio = size_45_ratio
        entity.size_46_ratio = size_46_ratio
        entity.total_quantity_ratio = total_quantity_ratio
        db.session.commit()
        return jsonify({"message": "Customer BatchInfo Updated Successfully"})
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

@customer_bp.route("/customer/editcustomer", methods=["POST"])
def edit_customer():
    customer_id = request.json.get("customerId")
    customer_name = request.json.get("customerName")
    customer_brand = request.json.get("customerBrand")
    try:
        customer = Customer.query.filter_by(customer_id=customer_id).first()
        customer.customer_name = customer_name
        customer.customer_brand = customer_brand
        db.session.commit()
        return jsonify({"message": "Customer updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def delete_customer_all_batch(customer_id):
    try:
        db.session.execute(db.delete(PackagingInfo).filter_by(customer_id=customer_id))
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error:{e}")
        raise SystemError("Delete Failed")
    finally:
        db.session.close()
    return 1
        
@customer_bp.route("/customer/deletecustomer", methods=["DELETE"])
def delete_customer():
    try:
        print(request)
        customer_id = request.args.get("customerId")
        customer_entity = (db.session.query(Customer).filter(
            Customer.customer_id == customer_id
        ).first())
        if not customer_entity:
            return jsonify({"status":"error", "message":"entity doesnt exist"})
        if delete_customer_all_batch(customer_id) == 1:
            db.session.delete(customer_entity)
            db.session.commit()
        return jsonify({'status':'success'})

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error:{e}")
        return jsonify({"status":"error", "message" :str(e)}), 500
    finally:
        db.session.close()
@customer_bp.route("/customer/deletebatchinfo", methods = ["DELETE"])
def delete_customer_batch():
    try:
        print(request)
        customer_id = request.args.get("customerId")
        packaging_info_id = request.args.get("packagingInfoId")
        batch_info_entity = db.session.query(PackagingInfo).filter(
            PackagingInfo.customer_id == customer_id,
            PackagingInfo.packaging_info_id == packaging_info_id).first()
        if not batch_info_entity:
            return jsonify({"status":"error", "message":"packaging info doesnt exist"})

        db.session.delete(batch_info_entity)
        db.session.commit()
        return jsonify({'status':'success'})

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error:{e}")
        return jsonify({"status":"error", "message" :str(e)}), 500
    finally:
        db.session.close()
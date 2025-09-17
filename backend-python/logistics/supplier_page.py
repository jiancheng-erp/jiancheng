from flask import Blueprint, jsonify, request
from sqlalchemy import delete

from app_config import db
from models import *

from logger import logger

supplier_page_bp = Blueprint("supplier_page_bp", __name__)


@supplier_page_bp.route("/logistics/allsuppliers", methods=["GET"])
def get_all_suppliers():
    suppliers = Supplier.query.all()
    result = []
    for supplier in suppliers:
        supplier_type = supplier.supplier_type
        if supplier_type == "N":
            supplier_type = "普通供货商"
        elif supplier_type == "W":
            supplier_type = "外加工供货商"
        result.append(
            {
                "supplierId": supplier.supplier_id,
                "supplierName": supplier.supplier_name,
                "supplierType": supplier.supplier_type,
                "supplierField": supplier_type,
            }
        )
    return jsonify(result)


@supplier_page_bp.route("/logistics/createsupplier", methods=["POST"])
def create_supplier():
    supplier_name = request.json.get("supplierName")
    supplier_type = request.json.get("supplierType")
    if supplier_name is None or supplier_name == "":
        return jsonify({"message": "供应商名称不能为空"}), 400
    # search whether the supplier exists
    supplier = Supplier.query.filter_by(supplier_name=supplier_name).first()
    if supplier:
        return jsonify({"message": "供应商已存在"}), 400
    supplier = Supplier(supplier_name=supplier_name, supplier_type=supplier_type)
    db.session.add(supplier)
    db.session.commit()
    return jsonify({"message": "success"})


@supplier_page_bp.route("/logistics/editsupplier", methods=["PUT"])
def edit_supplier():
    logger.debug(f"/logistics/editsupplier data: {request.json}")
    supplier_id = request.json.get("supplierId")
    supplier_name = request.json.get("supplierName")
    supplier_type = request.json.get("supplierType")
    if supplier_name is None or supplier_name == "":
        return jsonify({"message": "供应商名称不能为空"}), 400

    # check whether the supplier exists
    existed_supplier = (
        db.session.query(Supplier)
        .filter(Supplier.supplier_name == supplier_name)
        .first()
    )
    if existed_supplier and existed_supplier.supplier_id != supplier_id:
        return jsonify({"message": "该供应商名称已存在"}), 400

    supplier = db.session.query(Supplier).filter_by(supplier_id=supplier_id).first()
    if not supplier:
        return jsonify({"message": "供应商不存在"}), 404
    supplier.supplier_name = supplier_name
    supplier.supplier_type = supplier_type
    db.session.commit()
    return jsonify({"message": "success"})


@supplier_page_bp.route("/logistics/deleteSupplier", methods=["DELETE"])
def delete_supplier():
    supplier_id = request.json.get("supplierId")
    if supplier_id is None or supplier_id < 1:
        return jsonify({"message": "无效供应商id"}), 400

    # check whether the supplier referenced
    material = db.session.query(Material).filter(Material.material_supplier == supplier_id).first()
    if material:
        return jsonify({"message": "该供应商已被物料引用，无法删除"}), 400
    
    stmt = delete(Supplier).where(Supplier.supplier_id == supplier_id)
    db.session.execute(stmt)
    db.session.commit()
    return jsonify({"message": "success"})
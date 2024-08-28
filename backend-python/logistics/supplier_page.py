from flask import Blueprint, jsonify, request

from app_config import app, db
from models import *

supplier_page_bp = Blueprint("supplier_page_bp", __name__)

@supplier_page_bp.route("/logistics/allsuppliers", methods=["GET"])
def get_all_suppliers():
    suppliers = Supplier.query.all()
    result = []
    for supplier in suppliers:
        supplier_type = supplier.supplier_type
        if supplier_type == "N":
            supplier_type = "普通供货商"
        result.append(
            {
                "supplierId": supplier.supplier_id,
                "supplierName": supplier.supplier_name,
                "supplierField": supplier_type,
            }
        )
    return jsonify(result)

@supplier_page_bp.route("/logistics/createsupplier", methods=["POST"])
def create_supplier():
    supplier_name = request.json.get("supplierName")
    supplier_type = request.json.get("supplierField")
    supplier = Supplier(supplier_name=supplier_name, supplier_type=supplier_type)
    db.session.add(supplier)
    db.session.commit()
    return jsonify({"message": "success"})

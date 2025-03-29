from flask import Blueprint, jsonify, request
from datetime import datetime
from app_config import db
from models import *

warehouse_page_bp = Blueprint("warehouse_page_bp", __name__)

@warehouse_page_bp.route("/logistics/allwarehouses", methods=["GET"])
def get_all_warehouses():
    warehouses = MaterialWarehouse.query.all()
    result = []
    for warehouse in warehouses:
        result.append(
            {
                "warehouseId": warehouse.material_warehouse_id,
                "warehouseName": warehouse.material_warehouse_name,
                "addDate": warehouse.material_warehouse_creation_date.isoformat(),
            }
        )
    return jsonify(result)

@warehouse_page_bp.route("/logistics/addwarehouse", methods=["POST"])
def create_warehouse():
    warehouse_name = request.json.get("warehouseName")
    create_time = datetime.now().strftime("%Y-%m-%d")
    warehouse = MaterialWarehouse(material_warehouse_name=warehouse_name, material_warehouse_creation_date=create_time)
    db.session.add(warehouse)
    db.session.commit()
    return jsonify({"message": "success"})
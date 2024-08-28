from flask import Blueprint, jsonify, request

from app_config import app, db
from models import *

material_page_bp = Blueprint("material_page_bp", __name__)


@material_page_bp.route("/logistics/allmaterialtypes", methods=["GET"])
def get_all_materials():
    material_name = request.args.get("materialname", None)
    material_warehouse = request.args.get("warehousename", None)
    factory_name = request.args.get("factoryname", None)
    material_type = request.args.get("materialtype", None)
    
    # Start building the query
    query = (
        db.session.query(Material, MaterialWarehouse, Supplier)
        .join(
            MaterialWarehouse,
            Material.warehouse_id == MaterialWarehouse.material_warehouse_id,
        )
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
    )
    
    # Apply filters directly to the query
    if material_name:
        query = query.filter(Material.material_name.like(f"%{material_name}%"))
    if material_warehouse:
        query = query.filter(MaterialWarehouse.material_warehouse_name.like(f"%{material_warehouse}%"))
    if factory_name:
        query = query.filter(Supplier.supplier_name.like(f"%{factory_name}%"))
    if material_type:
        query = query.filter(Material.material_type.like(f"%{material_type}%"))
    
    materials = query.all()

    # Prepare the result
    result = []
    for material in materials:
        result.append(
            {
                "materialId": material.Material.material_id,
                "materialName": material.Material.material_name,
                "materialType": material.Material.material_type,
                "unit": material.Material.material_unit,
                "warehouseName": material.MaterialWarehouse.material_warehouse_name,
                "factoryName": material.Supplier.supplier_name,
                "addDate": material.Material.material_creation_date.isoformat(),
            }
        )
    
    # Prepare the final response
    fin_result = {
        "amount": len(result),
        "materials": result,
    }
    
    return jsonify(fin_result)

@material_page_bp.route("/logistics/allwarehousenames", methods=["GET"])
def get_all_warehouse_names():
    warehouses = db.session.query(MaterialWarehouse).all()
    result = []
    for warehouse in warehouses:
        result.append({
            "value": warehouse.material_warehouse_name,
            "label": warehouse.material_warehouse_name
        })
    return jsonify(result)

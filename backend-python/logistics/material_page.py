from flask import Blueprint, jsonify, request
from datetime import datetime
from app_config import db
from models import *
from sqlalchemy import text
from logger import logger
material_page_bp = Blueprint("material_page_bp", __name__)


from sqlalchemy.orm import joinedload


@material_page_bp.route("/logistics/allmaterial", methods=["GET"])
def get_all_materials():
    material_name = request.args.get("materialname", None)
    material_warehouse = request.args.get("warehousename", None)
    factory_name = request.args.get("factoryname", None)
    material_type = request.args.get("materialtype", None)
    logger.debug(material_name, material_warehouse, factory_name, material_type)

    # Start building the query with joinedload to reduce query count
    query = (
        db.session.query(Material, MaterialWarehouse, Supplier, MaterialType)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(
            MaterialWarehouse,
            MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id,
        )
    )

    # Apply filters directly to the query
    if material_name:
        query = query.filter(Material.material_name.like(f"%{material_name}%"))
    if material_warehouse:
        query = query.filter(
            MaterialWarehouse.material_warehouse_name.like(f"%{material_warehouse}%")
        )
    if factory_name:
        query = query.filter(Supplier.supplier_name.like(f"%{factory_name}%"))
    if material_type:
        query = query.filter(MaterialType.material_type_name.like(f"%{material_type}%"))

    # Fetch all materials in a single query
    materials = query.all()

    # Preload ProductionInstructionItem data to avoid per-item queries
    material_ids = [material.Material.material_id for material in materials]
    instruction_items = (
        db.session.query(
            ProductionInstructionItem.material_id,
            ProductionInstructionItem.material_model,
        )
        .filter(ProductionInstructionItem.material_id.in_(material_ids))
        .distinct()
        .all()
    )

    # Create a mapping of material_id to models
    material_models_map = {}
    for item in instruction_items:
        if item.material_id not in material_models_map:
            material_models_map[item.material_id] = []
        material_models_map[item.material_id].append(item.material_model)

    # Consolidate results
    consolidated_results = {}
    for material in materials:
        key = (
            material.Material.material_name,
            material.MaterialType.material_type_name,
        )
        supplier_name = material.Supplier.supplier_name
        material_id = material.Material.material_id
        material_models = material_models_map.get(material_id, [])

        if key not in consolidated_results:
            consolidated_results[key] = {
                "materialName": material.Material.material_name,
                "materialType": material.MaterialType.material_type_name,
                "unit": material.Material.material_unit,
                "warehouseName": material.MaterialWarehouse.material_warehouse_name,
                "addDate": material.Material.material_creation_date.isoformat() if material.Material.material_creation_date else "",
                "factoryInfo": [],  # Initialize as empty list
            }

        # Add supplier and model info separately for each model
        for model in material_models:
            consolidated_results[key]["factoryInfo"].append(
                {
                    "supplierName": supplier_name,
                    "materialModel": model,
                }
            )
        # If no models, still add supplier entry with null model
        if not material_models:
            consolidated_results[key]["factoryInfo"].append(
                {
                    "supplierName": supplier_name,
                    "materialModel": None,
                }
            )

    # Prepare the final response
    result = list(consolidated_results.values())
    fin_result = {
        "amount": len(result),
        "materials": result,
    }

    return jsonify(fin_result)


@material_page_bp.route("/logistics/getwarehousebymaterialtypeid", methods=["GET"])
def get_warehouse_by_material_type_id():
    material_type_id = request.args.get("materialTypeId", None)
    warehouse = (
        db.session.query(MaterialWarehouse)
        .join(
            MaterialType,
            MaterialWarehouse.material_warehouse_id == MaterialType.warehouse_id,
        )
        .filter(MaterialType.material_type_id == material_type_id)
        .first()
    )
    if not warehouse:
        return jsonify({"message": "Warehouse not found"}), 404
    result = {
        "warehouseId": warehouse.material_warehouse_id,
        "warehouseName": warehouse.material_warehouse_name,
    }
    return jsonify(result)


@material_page_bp.route("/logistics/allwarehousenames", methods=["GET"])
def get_all_warehouse_names():
    warehouses = db.session.query(MaterialWarehouse).all()
    result = []
    for warehouse in warehouses:
        result.append(
            {
                "value": warehouse.material_warehouse_name,
                "label": warehouse.material_warehouse_name,
            }
        )
    return jsonify(result)


@material_page_bp.route("/logistics/allmaterialtypes", methods=["GET"])
def get_all_material_types():
    # Query only necessary fields and apply distinct on material_type_name
    material_types = (
        db.session.query(
            MaterialType.material_type_name,
            Material.material_category,
            MaterialWarehouse.material_warehouse_name,
        )
        .join(
            MaterialWarehouse,
            MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id,
        )
        .outerjoin(Material, Material.material_type_id == MaterialType.material_type_id)
        .distinct(MaterialType.material_type_name)
        .order_by(MaterialType.material_type_name)
        .all()
    )

    # Format results as a list of dictionaries
    result = [
        {
            "materialType": material_type_name,
            "materialCategory": material_category,
            "warehouseName": warehouse_name,
        }
        for material_type_name, material_category, warehouse_name in material_types
    ]

    return jsonify(result)


@material_page_bp.route("/logistics/addmaterialtype", methods=["POST"])
def create_material_type():
    material_type = request.json.get("materialType", None)
    warehouse_name = request.json.get("warehouseName", None)
    # Get the warehouse based on the warehouse name
    warehouse = (
        db.session.query(MaterialWarehouse)
        .filter(MaterialWarehouse.material_warehouse_name == warehouse_name)
        .first()
    )
    if not warehouse:
        return jsonify({"message": "Warehouse does not exist"}), 403

    # Check if the material type already exists in the warehouse
    existing_material_type = (
        db.session.query(MaterialType)
        .filter(
            MaterialType.material_type_name == material_type,
            MaterialType.warehouse_id == warehouse.material_warehouse_id,
        )
        .first()
    )

    # If the material type already exists, return an error message
    if existing_material_type:
        return (
            jsonify({"message": "Material type already exists in the warehouse"}),
            403,
        )

    # Create the material type
    material_type = MaterialType(
        material_type_name=material_type,
        warehouse_id=warehouse.material_warehouse_id,
    )
    db.session.add(material_type)
    db.session.commit()

    return jsonify({"message": "success"})


@material_page_bp.route("/logistics/checkmaterial", methods=["POST"])
def check_material():
    material_name = request.json.get("materialname", None)
    factory_name = request.json.get("factoryname", None)
    logger.debug(material_name, factory_name)
    # Check if the material already exists
    existing_material = (
        db.session.query(Material)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(
            Material.material_name == material_name,
            Supplier.supplier_name == factory_name,
        )
        .first()
    )

    # If the material already exists, return an error message
    if existing_material:
        return (
            jsonify({"message": "same"}),
            200,
        )
    similiar_material = (
        db.session.query(Material, Supplier)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .filter(
            Material.material_name.like(f"%{material_name}%"),
            Supplier.supplier_name == factory_name,
        )
        .all()
    )
    if similiar_material:
        similiar_material_list = [
            {
                "materialName": material.Material.material_name,
                "factoryName": material.Supplier.supplier_name,
            }
            for material in similiar_material
        ]
        return (
            jsonify({"message": "similar", "similarMaterials": similiar_material_list}),
            200,
        )

    return jsonify({"message": "none"}), 200


@material_page_bp.route("/logistics/allfactorynames", methods=["GET"])
def get_all_factory_names():
    factories = db.session.query(Supplier).all()
    result = []
    for factory in factories:
        result.append(
            {
                "value": factory.supplier_name,
                "label": factory.supplier_name,
            }
        )
    return jsonify(result)


@material_page_bp.route("/logistics/addmaterial", methods=["POST"])
def create_material():
    material_list = request.json.get("materials", None)
    logger.debug(material_list)
    for material in material_list:
        material_category = material.get("materialCategory", None)
        material_name = material.get("materialName", None)
        material_type = material.get("materialType", None)
        unit = material.get("unit", None)
        factory_name = material.get("factoryName", None)
        logger.debug(material_name, material_type, unit, factory_name)
        material_type_record = (
            db.session.query(MaterialType)
            .filter(MaterialType.material_type_name == material_type)
            .first()
        )
        # Get the factory based on the factory name
        factory = (
            db.session.query(Supplier)
            .filter(Supplier.supplier_name == factory_name)
            .first()
        )
        if not factory:
            return jsonify({"message": "Factory does not exist"}), 403

        # Check if the material already exists
        existing_material = (
            db.session.query(Material, Supplier)
            .join(Supplier, Material.material_supplier == Supplier.supplier_id)
            .filter(
                Material.material_name == material_name,
                Supplier.supplier_name == factory_name,
            )
            .first()
        )

        # If the material already exists, return an error message
        if existing_material:
            return jsonify({"message": "Material already exists"}), 403

        # Create the material
        material = Material(
            material_name=material_name,
            material_type_id=material_type_record.material_type_id,
            material_unit=unit,
            material_supplier=factory.supplier_id,
            material_creation_date=datetime.now().strftime("%Y-%m-%d"),
            material_category=material_category,
        )
        db.session.add(material)
        db.session.commit()
    return jsonify({"message": "success"}), 200


@material_page_bp.route("/logistics/allmaterialstorage", methods=["GET"])
def get_all_material_storage():
    material_type = request.args.get("materialtype", None)
    material_name = request.args.get("materialname", None)
    material_spec = request.args.get("materialspec", None)
    warehouse_name = request.args.get("warehousename", None)
    factory_name = request.args.get("factoryname", None)
    order_id = request.args.get("orderid", None)
    order_shoe_id = request.args.get("ordershoeid", None)
    logger.debug(
        material_type,
        material_name,
        material_spec,
        warehouse_name,
        factory_name,
        order_id,
        order_shoe_id,
    )

    query = (
        db.session.query(
            MaterialType.material_type_name,
            Material.material_name,
            MaterialStorage.material_id.label("material_id"),
            MaterialStorage.material_specification.label("specification"),
            MaterialWarehouse.material_warehouse_name,
            Material.material_unit,
            MaterialStorage.current_amount.label("material_storage_amount"),
            MaterialStorage.unit_price,
            Supplier.supplier_name,
            Shoe.shoe_rid,
            Order.order_rid,
        )
        .join(Material, MaterialType.material_type_id == Material.material_type_id)
        .join(MaterialStorage, Material.material_id == MaterialStorage.material_id)
        .join(
            MaterialWarehouse,
            MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id,
        )
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
        .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
        .outerjoin(Order, OrderShoe.order_id == Order.order_id)
    )

    # Applying the filters
    if material_type:
        query = query.filter(MaterialType.material_type_name.like(f"%{material_type}%"))
    if material_name:
        query = query.filter(Material.material_name.like(f"%{material_name}%"))
    if material_spec:
        query = query.filter(text("specification LIKE :spec")).params(
            spec=f"%{material_spec}%"
        )
    if warehouse_name:
        query = query.filter(
            MaterialWarehouse.material_warehouse_name.like(f"%{warehouse_name}%")
        )
    if factory_name:
        query = query.filter(Supplier.supplier_name.like(f"%{factory_name}%"))
    if order_id:
        query = query.filter(Order.order_rid.like(f"%{order_id}%"))
    if order_shoe_id:
        query = query.filter(Shoe.shoe_rid.like(f"%{order_shoe_id}%"))

    material_storages = query.all()

    result = []
    for material_storage in material_storages:
        result.append(
            {
                "materialId": material_storage.material_id,
                "materialType": material_storage.material_type_name,
                "materialName": material_storage.material_name,
                "materialSpecification": material_storage.specification,
                "warehouseName": material_storage.material_warehouse_name,
                "unit": material_storage.material_unit,
                "amountRemain": round(material_storage.material_storage_amount, 3),
                "valueRemain": round(
                    material_storage.material_storage_amount
                    * material_storage.unit_price,
                    3,
                ),
                "unitPrice": round(material_storage.unit_price, 3),
                "factoryName": material_storage.supplier_name,
                "inheritId": material_storage.shoe_rid,
                "OrderId": material_storage.order_rid,
            }
        )
    fin_result = {
        "amount": len(result),
        "materials": result,
    }

    return jsonify(result)


@material_page_bp.route("/logistics/editmaterialtype", methods=["PATCH"])
def edit_material_type():
    material_old_name = request.json.get("materialoldname", None)
    material_name = request.json.get("materialname", None)
    material_unit = request.json.get("unit", None)
    material_id = (
        db.session.query(Material)
        .filter(Material.material_name == material_old_name)
        .first()
        .material_id
    )

    # Modify the material
    material = (
        db.session.query(Material).filter(Material.material_id == material_id).first()
    )
    material.material_name = material_name
    material.material_unit = material_unit
    db.session.commit()

    return jsonify({"message": "success"}), 200

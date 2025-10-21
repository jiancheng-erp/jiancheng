import sys
import os
from datetime import datetime
from unittest.mock import patch
import pytest
from flask.testing import FlaskClient
from flask import Response, Flask
import json
from flask_jwt_extended import create_access_token


# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app_config import db, create_app
from blueprints import register_blueprints
from models import *
from event_processor import EventProcessor
from constants import (
    WAREHOUSE_CLERK_ROLE,
    WAREHOUSE_CLERK_STAFF_ID,
    WAREHOUSE_CLERK_TEST,
)


# --- Flask App Fixture ---
@pytest.fixture
def test_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "mysql+pymysql://jiancheng_mgt:123456Ab@localhost:3306/jiancheng_local_test",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SECRET_KEY": "EC63AF9BA57B9F20",
            "JWT_SECRET_KEY": "EC63AF9BA57B9F20",
            # 👇 ensure tests use header-based JWT with the expected scheme
            "JWT_TOKEN_LOCATION": ["headers"],
            "JWT_HEADER_NAME": "Authorization",
            "JWT_HEADER_TYPE": "Bearer",
            # optionally keep tokens fresh longer during tests
            # "JWT_ACCESS_TOKEN_EXPIRES": timedelta(hours=1)
            "REDIS_HOST": "localhost",
            "REDIS_PORT": 6379,
            "REDIS_DB": 0,
            "session_lifetime_days": 7,
        }
    )
    # Ensure JWTManager exists and override blocklist callback in tests
    jwt = app.extensions["flask-jwt-extended"]

    @jwt.token_in_blocklist_loader
    def never_revoked(_, __):
        return False

    app.config["event_processor"] = EventProcessor()
    register_blueprints(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    # Provide a test client for making API requests.
    return test_app.test_client()


def create_environment(db):
    character = Character(
        character_id=WAREHOUSE_CLERK_ROLE,
        character_name="仓库文员",
    )
    staff = Staff(
        staff_id=WAREHOUSE_CLERK_STAFF_ID,
        staff_name="仓库文员",
        character_id=WAREHOUSE_CLERK_ROLE,
        department_id=6,
    )
    user = User(
        user_id=WAREHOUSE_CLERK_TEST,
        user_name="zongcangceshi",
        user_passwd="testpassword",
        staff_id=WAREHOUSE_CLERK_STAFF_ID,
    )
    department = Department(
        department_id=6,
        department_name="仓库部",
    )
    db.session.add(character)
    db.session.add(staff)
    db.session.add(user)
    db.session.add(department)
    db.session.flush()


def return_header_with_token():
    token = create_access_token(identity="zongcangceshi")
    return {"Authorization": f"Bearer {token}"}


def test_get_material_inbound_records(client: FlaskClient):
    # Insert dependency data into the temporary database.
    datetime_obj = datetime.strptime("2023-10-01 12:00:00", "%Y-%m-%d %H:%M:%S")
    inbound_record = InboundRecord(
        inbound_record_id=1,
        inbound_rid="12345",
        inbound_batch_id=1,
        supplier_id=1,
        warehouse_id=1,
        inbound_datetime=datetime_obj,
        inbound_type=0,
        pay_method="应付账款",
        staff_id=WAREHOUSE_CLERK_STAFF_ID,
    )
    supplier = Supplier(
        supplier_id=1,
        supplier_name="Supplier A",
    )
    warehouse = MaterialWarehouse(
        material_warehouse_id=1,
        material_warehouse_name="Warehouse A",
    )
    db.session.add(inbound_record)
    db.session.add(supplier)
    db.session.add(warehouse)
    create_environment(db)
    db.session.commit()
    # Use the test client to hit your Flask endpoint.
    query_string = {
        "page": 1,
        "pageSize": 10,
    }
    response = client.get(
        "/warehouse/getmaterialinboundrecords",
        query_string=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 200
    assert response.get_json()["result"][0]["inboundRecordId"] == 1


# 用户选择订单材料
def test_inbound_material_user_select_order_material(client: FlaskClient):
    """
    测试用户选择订单非底材材料
    """

    order = Order(
        order_id=1,
        order_rid="K25-001",
        start_date="2023-10-01",
        end_date="2023-10-31",
        salesman_id=1,
        batch_info_type_id=1,
    )

    order_shoe = OrderShoe(
        order_shoe_id=1,
        shoe_id=1,
        customer_product_name="Product A",
        order_id=1,
    )

    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="嘉泰皮革",
    )

    material = Material(
        material_id=1,
        material_name="PU里",
        material_type_id=2,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=2,
        material_type_name="里料",
        warehouse_id=1,
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1, material_warehouse_name="里料仓"
    )

    purchaese_order_item = PurchaseOrderItem(
        purchase_order_item_id=1,
        bom_item_id=1,
        purchase_divide_order_id=1,
        material_id=1,
        material_model="测试型号",
        material_specification="测试规格",
        color="黑",
        inbound_unit="米",
    )

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(purchaese_order_item)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": "嘉泰皮革",
        "remark": "123",
        "items": [
            {
                "actualInboundAmount": "0.00000",
                "actualInboundUnit": "米",
                "currentAmount": "0.00000",
                "estimatedInboundAmount": "20.00000",
                "inboundModel": "测试型号",
                "inboundSpecification": "测试规格",
                "materialCategory": 0,
                "materialColor": "黑",
                "materialModel": "测试型号",
                "materialName": "PU里",
                "materialSpecification": "测试规格",
                "orderId": 1,
                "orderRId": "K25-001",
                "shoeRId": "0E19533",
                "inboundQuantity": 20,
                "disableEdit": True,
                "unitPrice": 12.5,
                "itemTotalPrice": "250.000",
                "purchaseOrderItemId": 1,
            },
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }
    response = client.post(
        "/warehouse/inboundmaterial",
        json=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 200

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()

    assert storage.purchase_order_item_id == 1
    assert storage.pending_inbound == 20.0
    assert storage.spu_material_id == 1

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 250.0
    assert record.supplier_id == 1
    assert record.warehouse_id == 1
    assert record.inbound_type == 0
    assert record.pay_method == "应付账款"

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].spu_material_id == 1
    assert record_detail[0].material_storage_id == 1
    assert record_detail[0].unit_price == 12.5
    assert record_detail[0].inbound_amount == 20.0
    assert record_detail[0].item_total_price == 250.0
    assert record_detail[0].spu_material_id == 1

    # created new spu record
    spu_material = db.session.query(SPUMaterial).filter_by(spu_material_id=1).first()
    assert spu_material.spu_material_id == 1
    assert spu_material.material_model == "测试型号"
    assert spu_material.material_specification == "测试规格"
    assert spu_material.color == "黑"


def test_inbound_material_user_select_order_size_material(client: FlaskClient):
    """
    测试用户选择订单底材材料
    """

    order = Order(
        order_id=1,
        order_rid="K25-001",
        start_date="2023-10-01",
        end_date="2023-10-31",
        salesman_id=1,
        batch_info_type_id=1,
    )

    order_shoe = OrderShoe(
        order_shoe_id=1,
        shoe_id=1,
        customer_product_name="Product A",
        order_id=1,
    )

    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="日禾底材",
    )

    material = Material(
        material_id=1,
        material_name="大底",
        material_type_id=2,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=2,
        material_type_name="底材",
        warehouse_id=1,
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1, material_warehouse_name="底材仓"
    )

    # insert dependency data into the temporary database
    purchase_order_item = PurchaseOrderItem(
        purchase_order_item_id=1,
        bom_item_id=1,
        purchase_divide_order_id=1,
        material_id=1,
        material_model="9166",
        material_specification="棕/后跟喷棕",
        color="",
        purchase_amount=600,
    )
    setattr(purchase_order_item, f"size_35_purchase_amount", 50)
    setattr(purchase_order_item, f"size_36_purchase_amount", 100)
    setattr(purchase_order_item, f"size_37_purchase_amount", 150)
    setattr(purchase_order_item, f"size_38_purchase_amount", 150)
    setattr(purchase_order_item, f"size_39_purchase_amount", 100)
    setattr(purchase_order_item, f"size_40_purchase_amount", 50)

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(purchase_order_item)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(order)
    db.session.add(order_shoe)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": "日禾底材",
        "remark": "123",
        "items": [
            {
                "materialCategory": 1,
                "materialColor": "",
                "materialModel": "9166",
                "materialName": "大底",
                "materialSpecification": "棕/后跟喷棕",
                "materialStorageId": 1,
                "orderId": 1,
                "orderRId": "K25-001",
                "shoeRId": "3E29515",
                "supplierName": "日禾底材",
                "unitPrice": "12.500",
                "inboundModel": "9166",
                "inboundSpecification": "棕/后跟喷棕",
                "amount0": 0,
                "amount1": 50,
                "amount2": 100,
                "amount3": 150,
                "amount4": 150,
                "amount5": 100,
                "amount6": 50,
                "amount7": 0,
                "inboundQuantity": 600,
                "itemTotalPrice": "7500",
                "purchaseOrderItemId": 1,
                "shoeSizeColumns": ["35", "36", "37", "38", "39", "40", "41", "42"],
            }
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }
    response = client.post(
        "/warehouse/inboundmaterial",
        json=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 200

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()

    assert storage.purchase_order_item_id == 1
    assert storage.spu_material_id == 1
    assert storage.pending_inbound == 600

    size_details = (
        db.session.query(MaterialStorageSizeDetail)
        .filter_by(material_storage_id=1)
        .order_by(MaterialStorageSizeDetail.order_number)
        .all()
    )

    assert size_details[0].pending_inbound == 0
    assert size_details[1].pending_inbound == 50.0
    assert size_details[2].pending_inbound == 100.0
    assert size_details[3].pending_inbound == 150.0
    assert size_details[4].pending_inbound == 150.0
    assert size_details[5].pending_inbound == 100.0
    assert size_details[6].pending_inbound == 50.0
    assert size_details[7].pending_inbound == 0

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 7500
    assert record.supplier_id == 1
    assert record.warehouse_id == 1
    assert record.inbound_type == 0
    assert record.pay_method == "应付账款"

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].spu_material_id == 1
    assert record_detail[0].material_storage_id == 1
    assert record_detail[0].unit_price == 12.5
    assert record_detail[0].inbound_amount == 600
    assert record_detail[0].item_total_price == 7500.0

    assert record_detail[0].size_35_inbound_amount == 50.0
    assert record_detail[0].size_36_inbound_amount == 100.0
    assert record_detail[0].size_37_inbound_amount == 150.0
    assert record_detail[0].size_38_inbound_amount == 150.0
    assert record_detail[0].size_39_inbound_amount == 100.0
    assert record_detail[0].size_40_inbound_amount == 50.0

    # created new spu record
    spu_material = db.session.query(SPUMaterial).filter_by(spu_material_id=1).first()
    assert spu_material.spu_material_id == 1
    assert spu_material.material_model == "9166"
    assert spu_material.material_specification == "棕/后跟喷棕"
    assert spu_material.color == ""


def test_inbound_material_user_enter_material(client: FlaskClient):
    """
    测试用户手输非底材材料
    """

    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="一嘉胶水",
    )

    material = Material(
        material_id=1,
        material_name="胶水",
        material_type_id=2,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=2,
        material_type_name="化工",
        warehouse_id=1,
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1, material_warehouse_name="化工仓"
    )

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": "一嘉胶水",
        "remark": "123",
        "items": [
            {
                "materialCategory": 0,
                "materialColor": "",
                "materialName": "胶水",
                "supplierName": "一嘉胶水",
                "unitPrice": 12.500,
                "inboundModel": "测试1",
                "inboundSpecification": "测试2",
                "inboundQuantity": 600,
                "itemTotalPrice": 7500,
            }
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }

    response: Response = client.post(
        "/warehouse/inboundmaterial",
        json=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 200

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()

    assert storage.spu_material_id == 1
    assert storage.order_id == None
    assert storage.purchase_order_item_id == None
    assert storage.pending_inbound == 600

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 7500
    assert record.supplier_id == 1
    assert record.warehouse_id == 1
    assert record.inbound_type == 0
    assert record.pay_method == "应付账款"

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].spu_material_id == 1
    assert record_detail[0].material_storage_id == 1
    assert record_detail[0].unit_price == 12.5
    assert record_detail[0].inbound_amount == 600
    assert record_detail[0].item_total_price == 7500.0

    # created spu record
    spu_material = db.session.query(SPUMaterial).filter_by(spu_material_id=1).first()
    assert spu_material.material_id == 1
    assert spu_material.material_model == "测试1"
    assert spu_material.material_specification == "测试2"
    assert spu_material.color == ""


# 用户手输订单材料
def test_inbound_material_user_enter_order_size_material(client: FlaskClient):
    """
    测试用户手输订单底材材料
    """

    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="日禾底材",
    )

    material = Material(
        material_id=1,
        material_name="大底",
        material_type_id=2,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=2,
        material_type_name="底材",
        warehouse_id=1,
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1, material_warehouse_name="底材仓"
    )

    order = Order(
        order_id=1,
        order_rid="W25-006",
        start_date="2023-10-01",
        end_date="2023-10-31",
        salesman_id=1,
        batch_info_type_id=1,
    )

    order_shoe = OrderShoe(
        order_shoe_id=1,
        shoe_id=1,
        customer_product_name="Product A",
        order_id=1,
    )

    batch_info_type = BatchInfoType(
        batch_info_type_id=1,
        batch_info_type_name="EU女",
        batch_info_type_usage=1,
        size_34_name="35",
        size_35_name="36",
        size_36_name="37",
        size_37_name="38",
        size_38_name="39",
        size_39_name="40",
        size_40_name="41",
        size_41_name="42",
    )

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(batch_info_type)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": "日禾底材",
        "remark": "123",
        "items": [
            {
                "materialCategory": 1,
                "materialColor": "",
                "materialModel": "9166",
                "materialName": "大底",
                "materialSpecification": "棕/后跟喷棕",
                "orderId": 1,
                "orderRId": "W25-006",
                "shoeRId": "3E29515",
                "supplierName": "日禾底材",
                "unitPrice": "12.500",
                "inboundModel": "9166",
                "inboundSpecification": "棕/后跟喷棕",
                "amount0": 0,
                "amount1": 50,
                "amount2": 100,
                "amount3": 150,
                "amount4": 150,
                "amount5": 100,
                "amount6": 50,
                "amount7": 0,
                "inboundQuantity": 600,
                "itemTotalPrice": "7500",
            }
        ],
        "batchInfoTypeId": 1,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }

    response: Response = client.post(
        "/warehouse/inboundmaterial",
        json=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 200

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()

    assert storage.spu_material_id == 1

    size_details = (
        db.session.query(MaterialStorageSizeDetail)
        .filter_by(material_storage_id=1)
        .order_by(MaterialStorageSizeDetail.order_number)
        .all()
    )
    amounts = [0, 50, 100, 150, 150, 100, 50, 0]
    for i in range(len(amounts)):
        assert size_details[i].pending_inbound == amounts[i]

    assert storage.shoe_size_columns == ["35", "36", "37", "38", "39", "40", "41", "42"]

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 7500
    assert record.supplier_id == 1
    assert record.warehouse_id == 1
    assert record.inbound_type == 0
    assert record.pay_method == "应付账款"

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].spu_material_id == 1
    assert record_detail[0].material_storage_id == 1
    assert record_detail[0].unit_price == 12.5
    assert record_detail[0].inbound_amount == 600
    assert record_detail[0].item_total_price == 7500.0

    assert record_detail[0].size_35_inbound_amount == 50.0
    assert record_detail[0].size_36_inbound_amount == 100.0
    assert record_detail[0].size_37_inbound_amount == 150.0
    assert record_detail[0].size_38_inbound_amount == 150.0
    assert record_detail[0].size_39_inbound_amount == 100.0
    assert record_detail[0].size_40_inbound_amount == 50.0

    # created spu record
    spu_material = db.session.query(SPUMaterial).filter_by(spu_material_id=1).first()
    assert spu_material.material_id == 1
    assert spu_material.material_model == "9166"
    assert spu_material.material_specification == "棕/后跟喷棕"
    assert spu_material.color == ""


def test_inbound_size_material_no_shoe_size_column(client: FlaskClient):
    """
    测试用户手输订单底材材料时没选码段
    """

    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="日禾底材",
    )

    material = Material(
        material_id=1,
        material_name="大底",
        material_type_id=2,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=2,
        material_type_name="底材",
        warehouse_id=1,
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1, material_warehouse_name="底材仓"
    )

    order = Order(
        order_id=1,
        order_rid="W25-006",
        start_date="2023-10-01",
        end_date="2023-10-31",
        salesman_id=1,
        batch_info_type_id=1,
    )

    order_shoe = OrderShoe(
        order_shoe_id=1,
        shoe_id=1,
        customer_product_name="Product A",
        order_id=1,
    )

    batch_info_type = BatchInfoType(
        batch_info_type_id=1,
        batch_info_type_name="EU女",
        batch_info_type_usage=1,
        size_34_name="35",
        size_35_name="36",
        size_36_name="37",
        size_37_name="38",
        size_38_name="39",
        size_39_name="40",
        size_40_name="41",
        size_41_name="42",
    )

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(batch_info_type)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": "日禾底材",
        "warehouseId": 1,
        "remark": "123",
        "items": [
            {
                "materialCategory": 1,
                "materialColor": "",
                "materialModel": "9166",
                "materialName": "大底",
                "materialSpecification": "棕/后跟喷棕",
                "orderId": 1,
                "orderRId": "W25-006",
                "shoeRId": "3E29515",
                "supplierName": "日禾底材",
                "unitPrice": "12.500",
                "inboundModel": "9166",
                "inboundSpecification": "棕/后跟喷棕",
                "amount0": 0,
                "amount1": 50,
                "amount2": 100,
                "amount3": 150,
                "amount4": 150,
                "amount5": 100,
                "amount6": 50,
                "amount7": 0,
                "inboundQuantity": 600,
                "itemTotalPrice": "7500",
                "shoeSizeColumns": [],
            }
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }

    response: Response = client.post(
        "/warehouse/inboundmaterial",
        json=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 400
    assert json.loads(response.data)["message"] == "无效尺码ID"


def test_inbound_material_user_enter_order_material_to_existed_storage(
    client: FlaskClient,
):
    """
    测试用户手输订单材料到已有库存记录
    """

    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="深源皮革",
    )

    material = Material(
        material_id=1,
        material_name="布里",
        material_type_id=2,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=2,
        material_type_name="面料",
        warehouse_id=1,
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1, material_warehouse_name="面料仓"
    )

    order = Order(
        order_id=1,
        order_rid="W25-006",
        start_date="2023-10-01",
        end_date="2023-10-31",
        salesman_id=1,
        batch_info_type_id=1,
    )

    order_shoe = OrderShoe(
        order_shoe_id=1,
        shoe_id=1,
        customer_product_name="Product A",
        order_id=1,
    )

    spu_material = SPUMaterial(
        spu_material_id=1,
        material_id=1,
        material_model="ModelA",
        material_specification="SpecA",
        color="ColorA",
    )

    storage = MaterialStorage(
        material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        spu_material_id=1,
        actual_inbound_unit="米",
        pending_inbound=50,
        inbound_amount=40,
        current_amount=40,
        shoe_size_columns=[],
    )

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(spu_material)
    db.session.add(storage)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": "深源皮革",
        "remark": "123",
        "items": [
            {
                "materialCategory": 0,
                "materialName": "布里",
                "orderRId": "W25-006",
                "shoeRId": "3E29515",
                "unitPrice": 2,
                "inboundModel": "ModelA",
                "inboundSpecification": "SpecA",
                "materialColor": "ColorA",
                "inboundQuantity": 50,
                "itemTotalPrice": 100,
                "actualInboundUnit": "米",
            }
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }

    response: Response = client.post(
        "/warehouse/inboundmaterial",
        json=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 200

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    assert storage.spu_material_id == 1
    assert storage.pending_inbound == 100

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 100
    assert record.supplier_id == 1
    assert record.warehouse_id == 1
    assert record.inbound_type == 0
    assert record.pay_method == "应付账款"

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].spu_material_id == 1
    assert record_detail[0].material_storage_id == 1
    assert record_detail[0].unit_price == 2
    assert record_detail[0].inbound_amount == 50
    assert record_detail[0].item_total_price == 100


def test_inbound_material_manually_multiple_times(client: FlaskClient):
    """
    测试手输多个订单材料入库
    """
    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="深源皮革",
    )

    material = Material(
        material_id=1,
        material_name="布里",
        material_type_id=2,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=2,
        material_type_name="面料",
        warehouse_id=1,
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1, material_warehouse_name="面料仓"
    )

    order = Order(
        order_id=1,
        order_rid="W25-006",
        start_date="2023-10-01",
        end_date="2023-10-31",
        salesman_id=1,
        batch_info_type_id=1,
    )

    order_shoe = OrderShoe(
        order_shoe_id=1,
        shoe_id=1,
        customer_product_name="Product A",
        order_id=1,
    )

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(order)
    db.session.add(order_shoe)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    # test for sanitization
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": " 深 源 皮 革 ",
        "remark": "123",
        "items": [
            {
                "materialCategory": 0,
                "materialName": " 布 里 ",
                "orderRId": "W25-006",
                "shoeRId": "3E29515",
                "unitPrice": 2.5,
                "inboundModel": " Model A ",
                "inboundSpecification": " Spec A ",
                "materialColor": " Color A ",
                "inboundQuantity": 50,
                "itemTotalPrice": 125.0,
                "actualInboundUnit": "米",
            },
            {
                "materialCategory": 0,
                "materialName": "布里",
                "orderRId": "W25-006",
                "shoeRId": "3E29515",
                "unitPrice": 2,
                "inboundModel": "ModelB",
                "inboundSpecification": "SpecB",
                "materialColor": "ColorB",
                "inboundQuantity": 20,
                "itemTotalPrice": 40.0,
                "actualInboundUnit": "米",
            },
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }

    response: Response = client.post(
        "/warehouse/inboundmaterial",
        json=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 200

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()

    assert storage.spu_material_id == 1
    assert storage.pending_inbound == 50

    storage2 = (
        db.session.query(MaterialStorage).filter_by(material_storage_id=2).first()
    )
    assert storage2.spu_material_id == 2
    assert storage2.pending_inbound == 20

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 165.0
    assert record.supplier_id == 1
    assert record.warehouse_id == 1
    assert record.inbound_type == 0
    assert record.pay_method == "应付账款"

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    expected_details = [
        {
            "inbound_record_id": 1,
            "unit_price": Decimal(2.5),
            "inbound_amount": 50,
            "item_total_price": Decimal(125.0),
        },
        {
            "inbound_record_id": 1,
            "unit_price": Decimal(2),
            "inbound_amount": 20,
            "item_total_price": Decimal(40.0),
        },
    ]

    for i, detail in enumerate(record_detail):
        assert detail.inbound_record_id == expected_details[i]["inbound_record_id"]
        print(detail.unit_price, expected_details[i]["unit_price"])
        assert detail.unit_price == expected_details[i]["unit_price"]
        assert detail.inbound_amount == expected_details[i]["inbound_amount"]
        assert detail.item_total_price == expected_details[i]["item_total_price"]

    # created spu record
    expected_spu_materials = [
        {
            "spu_material_id": 1,
            "material_model": "ModelA",
            "material_specification": "SpecA",
            "color": "ColorA",
        },
        {
            "spu_material_id": 2,
            "material_model": "ModelB",
            "material_specification": "SpecB",
            "color": "ColorB",
        },
    ]
    spu_materials = db.session.query(SPUMaterial).all()
    for i, spu_material in enumerate(spu_materials):
        assert (
            spu_material.spu_material_id == expected_spu_materials[i]["spu_material_id"]
        )
        assert (
            spu_material.material_model == expected_spu_materials[i]["material_model"]
        )
        assert (
            spu_material.material_specification
            == expected_spu_materials[i]["material_specification"]
        )
        assert spu_material.color == expected_spu_materials[i]["color"]


def test_inbound_material_with_no_shoe_size_columns(client: FlaskClient):
    """
    测试输订单非底材材料时没选码段
    期望：size details为空
    """

    order1 = Order(
        order_id=1,
        order_rid="K25-880",
        start_date="2023-10-01",
        end_date="2023-10-31",
        salesman_id=1,
        batch_info_type_id=1,
    )

    order_shoe1 = OrderShoe(
        order_shoe_id=1,
        shoe_id=1,
        customer_product_name="Product A",
        order_id=1,
    )

    order2 = Order(
        order_id=2,
        order_rid="K25-882",
        start_date="2023-10-01",
        end_date="2023-10-31",
        salesman_id=1,
        batch_info_type_id=1,
    )

    order_shoe2 = OrderShoe(
        order_shoe_id=2,
        shoe_id=2,
        customer_product_name="Product B",
        order_id=2,
    )

    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="保利鞋材",
    )

    material = Material(
        material_id=1,
        material_name="布里",
        material_type_id=2,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=2,
        material_type_name="里料",
        warehouse_id=1,
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1, material_warehouse_name="里料仓"
    )

    db.session.add(order1)
    db.session.add(order_shoe1)
    db.session.add(order2)
    db.session.add(order_shoe2)
    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundRecordId": 6164,
        "inboundType": 0,
        "supplierName": "保利鞋材",
        "remark": "10.21",
        "items": [
            {
                "actualInboundUnit": "米",
                "amount0": 0,
                "amount1": 0,
                "amount10": 0,
                "amount11": 0,
                "amount12": 0,
                "amount2": 0,
                "amount3": 0,
                "amount4": 0,
                "amount5": 0,
                "amount6": 0,
                "amount7": 0,
                "amount8": 0,
                "amount9": 0,
                "inboundModel": "四方格子布119#",
                "inboundQuantity": "14",
                "inboundRecordDetailId": 1,
                "inboundSpecification": "",
                "itemTotalPrice": "128.8",
                "materialCategory": 0,
                "materialColor": "",
                "materialModel": "四方格子布119#",
                "materialName": "布里",
                "materialSpecification": "",
                "materialStorageId": 1,
                "materialTypeId": 2,
                "materialUnit": "米",
                "orderRId": "K25-880",
                "remark": "0133",
                "shoeRId": "D210725",
                "shoeSizeColumns": [],
                "supplierName": "保利鞋材",
                "unitPrice": "9.2",
                "id": "row_45",
            },
            {
                "actualInboundUnit": "米",
                "amount0": 0,
                "amount1": 0,
                "amount10": 0,
                "amount11": 0,
                "amount12": 0,
                "amount2": 0,
                "amount3": 0,
                "amount4": 0,
                "amount5": 0,
                "amount6": 0,
                "amount7": 0,
                "amount8": 0,
                "amount9": 0,
                "inboundModel": "四方格子布119#",
                "inboundQuantity": "16",
                "inboundRecordDetailId": 2,
                "inboundSpecification": "",
                "itemTotalPrice": "147.2",
                "materialCategory": 0,
                "materialColor": "",
                "materialModel": "四方格子布119#",
                "materialName": "布里",
                "materialSpecification": "",
                "materialStorageId": 2,
                "materialTypeId": 2,
                "materialUnit": "米",
                "orderRId": "K25-882",
                "remark": "None",
                "shoeRId": "D8H2011",
                "shoeSizeColumns": [],
                "supplierName": "保利鞋材",
                "unitPrice": "9.2",
                "id": "row_46",
            },
        ],
        "payMethod": "现金",
        "materialTypeId": 2,
    }

    response: Response = client.post(
        "/warehouse/inboundmaterial",
        json=query_string,
        headers=return_header_with_token(),
    )
    assert response.status_code == 200

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()

    assert storage.spu_material_id == 1
    assert storage.pending_inbound == 14

    storage2 = (
        db.session.query(MaterialStorage).filter_by(material_storage_id=2).first()
    )
    assert storage2.spu_material_id == 1
    assert storage2.pending_inbound == 16

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 276
    assert record.supplier_id == 1
    assert record.warehouse_id == 1
    assert record.inbound_type == 0
    assert record.pay_method == "现金"

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    expected_details = [
        {
            "inbound_record_id": 1,
            "unit_price": Decimal('9.2'),
            "inbound_amount": 14,
            "item_total_price": Decimal('128.8'),
        },
        {
            "inbound_record_id": 1,
            "unit_price": Decimal('9.2'),
            "inbound_amount": 16,
            "item_total_price": Decimal('147.2'),
        },
    ]

    for i, detail in enumerate(record_detail):
        assert detail.inbound_record_id == expected_details[i]["inbound_record_id"]
        assert detail.unit_price == expected_details[i]["unit_price"]
        assert detail.inbound_amount == expected_details[i]["inbound_amount"]
        assert detail.item_total_price == expected_details[i]["item_total_price"]


    # 因为是里料，所以不会创建size detail记录
    size_details = (
        db.session.query(MaterialStorageSizeDetail)
        .filter(MaterialStorageSizeDetail.material_storage_id.in_([1,2]))
        .all()
    )

    assert len(size_details) == 0

import sys
import os
from datetime import datetime
from unittest.mock import patch
import pytest
from flask.testing import FlaskClient


# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app_config import db
from test_app_config import create_app
from blueprints import register_blueprints
from models import *
from event_processor import EventProcessor
from constants import SHOESIZERANGE


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
        }
    )
    app.config["event_processor"] = EventProcessor()
    register_blueprints(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    # Provide a test client for making API requests.
    return test_app.test_client()


@pytest.fixture
def sample_data(test_app):
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
    db.session.commit()
    return inbound_record


def test_get_material_inbound_records(client: FlaskClient, sample_data):
    # Use the test client to hit your Flask endpoint.
    query_string = {
        "page": 1,
        "pageSize": 10,
    }
    response = client.get(
        "/warehouse/getmaterialinboundrecords", query_string=query_string
    )
    assert response.status_code == 200
    # Additional assertions can check that the dependency data (sample_data) is being used properly.
    assert (
        response.get_json()["result"][0]["inboundRecordId"]
        == sample_data.inbound_record_id
    )


# 用户选择订单材料
def test_inbound_material_user_select_order_material(client: FlaskClient):
    """
    测试用户选择订单非底材材料
    """

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

    # insert dependency data into the temporary database
    material_storage = MaterialStorage(
        material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        material_id=1,
        actual_inbound_material_id=1,
        material_model="Model A",
        material_specification="Spec A",
        material_storage_color="Color A",
        inbound_model="Model A",
        inbound_specification="Spec A",
        actual_inbound_unit="米",
        estimated_inbound_amount=100,
    )
    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_storage)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": "嘉泰皮革",
        "warehouseId": 1,
        "remark": "123",
        "items": [
            {
                "actualInboundAmount": "0.00000",
                "actualInboundUnit": "米",
                "currentAmount": "0.00000",
                "estimatedInboundAmount": "20.00000",
                "inboundModel": "1501-1",
                "inboundSpecification": "",
                "materialCategory": 0,
                "materialColor": "黑",
                "materialModel": "1501-1",
                "materialName": "PU里",
                "materialSpecification": "",
                "materialStorageId": 1,
                "orderId": 64,
                "orderRId": "K25-008",
                "shoeRId": "0E19533",
                "inboundQuantity": 20,
                "disableEdit": True,
                "unitPrice": 12.5,
                "itemTotalPrice": "250.000",
            },
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }
    response = client.post("/warehouse/inboundmaterial", json=query_string)
    assert response.status_code == 200
    assert response.get_json()["inboundRId"] == "IR20250406165945T0"

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()

    assert storage.actual_inbound_amount == 20.0

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 250.0

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].unit_price == 12.5
    assert record_detail[0].inbound_amount == 20.0
    assert record_detail[0].item_total_price == 250.0


# 用户选择订单材料
def test_inbound_material_user_select_order_size_material(client: FlaskClient):
    """
    测试用户选择订单底材材料
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

    # insert dependency data into the temporary database
    size_material_storage = SizeMaterialStorage(
        size_material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        material_id=1,
        size_material_model="Model A",
        size_material_specification="Spec A",
        size_material_color="Color A",
        total_estimated_inbound_amount=600,
    )
    setattr(size_material_storage, f"size_35_estimated_inbound_amount", 50)
    setattr(size_material_storage, f"size_36_estimated_inbound_amount", 100)
    setattr(size_material_storage, f"size_37_estimated_inbound_amount", 150)
    setattr(size_material_storage, f"size_38_estimated_inbound_amount", 150)
    setattr(size_material_storage, f"size_39_estimated_inbound_amount", 100)
    setattr(size_material_storage, f"size_40_estimated_inbound_amount", 50)

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(size_material_storage)
    db.session.add(material_type)
    db.session.add(warehouse)
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
                "materialStorageId": 1,
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
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }
    response = client.post("/warehouse/inboundmaterial", json=query_string)
    assert response.status_code == 200
    assert response.get_json()["inboundRId"] == "IR20250406165945T0"

    storage = (
        db.session.query(SizeMaterialStorage)
        .filter_by(size_material_storage_id=1)
        .first()
    )

    assert storage.total_actual_inbound_amount == 600
    assert storage.total_current_amount == 600

    assert storage.size_35_actual_inbound_amount == 50.0
    assert storage.size_36_actual_inbound_amount == 100.0
    assert storage.size_37_actual_inbound_amount == 150.0
    assert storage.size_38_actual_inbound_amount == 150.0
    assert storage.size_39_actual_inbound_amount == 100.0
    assert storage.size_40_actual_inbound_amount == 50.0

    assert storage.size_35_current_amount == 50.0
    assert storage.size_36_current_amount == 100.0
    assert storage.size_37_current_amount == 150.0
    assert storage.size_38_current_amount == 150.0
    assert storage.size_39_current_amount == 100.0
    assert storage.size_40_current_amount == 50.0

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 7500

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].unit_price == 12.5
    assert record_detail[0].inbound_amount == 600
    assert record_detail[0].item_total_price == 7500.0

    assert record_detail[0].size_35_inbound_amount == 50.0
    assert record_detail[0].size_36_inbound_amount == 100.0
    assert record_detail[0].size_37_inbound_amount == 150.0
    assert record_detail[0].size_38_inbound_amount == 150.0
    assert record_detail[0].size_39_inbound_amount == 100.0
    assert record_detail[0].size_40_inbound_amount == 50.0


# 用户手输订单材料
def test_inbound_material_user_enter_order_material(client: FlaskClient):
    """
    测试用户手输订单非底材材料
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
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundType": 0,
        "currentDateTime": "2025-04-06 16:59:45",
        "supplierName": "深源皮革",
        "warehouseId": 1,
        "remark": "123",
        "items": [
            {
                "materialCategory": 0,
                "materialColor": "",
                "materialModel": "3701",
                "materialName": "布里",
                "materialSpecification": "测试123",
                "orderId": 1,
                "orderRId": "W25-006",
                "shoeRId": "3E29515",
                "supplierName": "日禾底材",
                "unitPrice": "12.500",
                "inboundModel": "3701",
                "inboundSpecification": "测试123",
                "inboundQuantity": 600,
                "itemTotalPrice": "7500",
            }
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }
    from flask import Response
    response: Response = client.post("/warehouse/inboundmaterial", json=query_string)
    assert response.status_code == 200
    assert response.get_json()["inboundRId"] == "IR20250406165945T0"

    storage = (
        db.session.query(MaterialStorage)
        .filter_by(material_storage_id=1)
        .first()
    )

    assert storage.material_model == "3701"
    assert storage.material_specification == "测试123"
    assert storage.actual_inbound_amount == 600
    assert storage.current_amount == 600

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 7500

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].unit_price == 12.5
    assert record_detail[0].inbound_amount == 600
    assert record_detail[0].item_total_price == 7500.0


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

    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(order)
    db.session.add(order_shoe)
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
            }
        ],
        "batchInfoTypeId": None,
        "payMethod": "应付账款",
        "materialTypeId": 2,
    }
    from flask import Response
    response: Response = client.post("/warehouse/inboundmaterial", json=query_string)
    assert response.status_code == 200
    assert response.get_json()["inboundRId"] == "IR20250406165945T0"

    storage = (
        db.session.query(SizeMaterialStorage)
        .filter_by(size_material_storage_id=1)
        .first()
    )

    assert storage.size_material_model == "9166"
    assert storage.size_material_specification == "棕/后跟喷棕"
    assert storage.total_actual_inbound_amount == 600
    assert storage.total_current_amount == 600

    assert storage.size_35_actual_inbound_amount == 50.0
    assert storage.size_36_actual_inbound_amount == 100.0
    assert storage.size_37_actual_inbound_amount == 150.0
    assert storage.size_38_actual_inbound_amount == 150.0
    assert storage.size_39_actual_inbound_amount == 100.0
    assert storage.size_40_actual_inbound_amount == 50.0

    assert storage.size_35_current_amount == 50.0
    assert storage.size_36_current_amount == 100.0
    assert storage.size_37_current_amount == 150.0
    assert storage.size_38_current_amount == 150.0
    assert storage.size_39_current_amount == 100.0
    assert storage.size_40_current_amount == 50.0

    record = db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()

    assert record.total_price == 7500

    record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=1).all()
    )

    assert record_detail[0].inbound_record_id == 1
    assert record_detail[0].unit_price == 12.5
    assert record_detail[0].inbound_amount == 600
    assert record_detail[0].item_total_price == 7500.0

    assert record_detail[0].size_35_inbound_amount == 50.0
    assert record_detail[0].size_36_inbound_amount == 100.0
    assert record_detail[0].size_37_inbound_amount == 150.0
    assert record_detail[0].size_38_inbound_amount == 150.0
    assert record_detail[0].size_39_inbound_amount == 100.0
    assert record_detail[0].size_40_inbound_amount == 50.0


def test_update_inbound_record(client: FlaskClient):
    """
    测试更新入库单
    """

    order = Order(
        order_id=1,
        order_rid="K25-031",
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
        is_sized_material=1,
        remark="remark",
    )

    inbound_record_detail = InboundRecordDetail(
        id=1,
        inbound_record_id=1,
        unit_price=12.5,
        inbound_amount=10.0,
        item_total_price=125.0,
        size_36_inbound_amount=1,
        size_37_inbound_amount=2,
        size_38_inbound_amount=3,
        size_39_inbound_amount=4,
        size_material_storage_id=1,
    )

    supplier = Supplier(
        supplier_id=1,
        supplier_name="大富豪底材",
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1,
        material_warehouse_name="Warehouse A",
    )

    material = Material(
        material_id=1,
        material_name="大底",
        material_type_id=1,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=1,
        material_type_name="底材",
        warehouse_id=1,
    )

    material_storage = SizeMaterialStorage(
        size_material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        material_id=1,
        size_material_model="58216",
        size_material_specification="黑色/黑色沿条车灰线/后跟印灰",
        size_material_color="",
        total_estimated_inbound_amount=600,
        total_actual_inbound_amount=10,
        total_current_amount=10,
        size_36_actual_inbound_amount=1,
        size_37_actual_inbound_amount=2,
        size_38_actual_inbound_amount=3,
        size_39_actual_inbound_amount=4,
        size_36_current_amount=1,
        size_37_current_amount=2,
        size_38_current_amount=3,
        size_39_current_amount=4,
    )
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail)
    db.session.add(supplier)
    db.session.add(warehouse)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(material_storage)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundRecordId": 1,
        "supplierName": "大富豪底材",
        "inboundType": 0,
        "remark": "2025/3/4",
        "payMethod": "应付账款",
        "isSizedMaterial": 1,
        "items": [
            {
                "actualInboundUnit": "双",
                "amount0": 0,
                "amount1": 0,
                "amount2": 79,
                "amount3": 125,
                "amount4": 150,
                "amount5": 50,
                "amount6": 0,
                "amount7": 0,
                "amount8": 0,
                "amount9": 0,
                "amount10": 0,
                "amount11": 0,
                "amount12": 0,
                "colorName": "",
                "compositeUnitCost": 0,
                "inboundQuantity": 404,
                "inboundRecordDetailId": 1,
                "itemTotalPrice": 4848,
                "materialModel": "58216",
                "materialName": "大底",
                "materialSpecification": "黑色/黑色沿条车灰线/后跟印灰",
                "materialStorageId": 1,
                "materialUnit": "双",
                "orderRId": "K25-031",
                "remark": "010",
                "shoeSizeColumns": ["35", "36", "37", "38", "39", "40", "41", "42"],
                "supplierName": "大富豪底材",
                "unitPrice": 12,
                "toDelete": 0,
            },
        ],
    }
    response = client.patch("/warehouse/updateinboundrecord", json=query_string)
    assert response.status_code == 200
    updated_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()
    )

    updated_record_detail = (
        db.session.query(InboundRecordDetail)
        .filter_by(inbound_record_id=1)
        .first()
    )
    assert updated_record.remark == "2025/3/4"
    assert updated_record_detail.unit_price == 12.0
    assert updated_record_detail.inbound_amount == 404.0
    assert updated_record_detail.item_total_price == 4848.0

    assert updated_record_detail.size_36_inbound_amount == 79
    assert updated_record_detail.size_37_inbound_amount == 125
    assert updated_record_detail.size_38_inbound_amount == 150
    assert updated_record_detail.size_39_inbound_amount == 50

    assert updated_record_detail.remark == "010"

    updated_storage = (
        db.session.query(SizeMaterialStorage)
        .filter_by(size_material_storage_id=1)
        .first()
    )

    assert updated_storage.total_actual_inbound_amount == 404.0
    assert updated_storage.total_current_amount == 404.0
    assert updated_storage.size_36_actual_inbound_amount == 79.0
    assert updated_storage.size_37_actual_inbound_amount == 125.0
    assert updated_storage.size_38_actual_inbound_amount == 150.0
    assert updated_storage.size_39_actual_inbound_amount == 50.0

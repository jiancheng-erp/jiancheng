import sys
import os
from datetime import datetime
from unittest.mock import patch
import pytest
from flask.testing import FlaskClient
from flask import Response
import json
from flask_jwt_extended import create_access_token


# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app_config import db, create_app
from blueprints import register_blueprints
from models import *
from event_processor import EventProcessor
from constants import SHOESIZERANGE
from constants import WAREHOUSE_CLERK_ROLE, WAREHOUSE_CLERK_STAFF_ID, WAREHOUSE_CLERK_TEST


# --- Flask App Fixture ---
@pytest.fixture
def test_app():
    app = create_app({
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
        "session_lifetime_days": 7
    })
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

@pytest.fixture
def client(test_app):
    # Provide a test client for making API requests.
    return test_app.test_client()


def test_update_outbound_record_model_specification_color(client: FlaskClient):
    """
    测试更新退货单的数量和单价
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
        is_sized_material=0,
        remark="remark",
        approval_status=0,
        staff_id=WAREHOUSE_CLERK_STAFF_ID,
    )

    inbound_record_detail = InboundRecordDetail(
        id=1,
        inbound_record_id=1,
        unit_price=12.5,
        inbound_amount=10.0,
        item_total_price=125.0,
        material_storage_id=1,
        order_id=1,
    )

    outbound_record = OutboundRecord(
        outbound_rid="12345",
        outbound_batch_id=1,
        supplier_id=1,
        outbound_datetime=datetime_obj,
        outbound_type=4,
        is_sized_material=0,
        remark="remark",
        approval_status=0,
        staff_id=WAREHOUSE_CLERK_STAFF_ID,
    )

    outbound_record_detail = OutboundRecordDetail(
        outbound_record_id=1,
        unit_price=12.5,
        outbound_amount=10.0,
        item_total_price=125.0,
        material_storage_id=1,
        order_id=1,
    )

    supplier = Supplier(
        supplier_id=1,
        supplier_name="深源皮革",
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1,
        material_warehouse_name="Warehouse A",
    )

    material = Material(
        material_id=1,
        material_name="PU面",
        material_type_id=1,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=1,
        material_type_name="面料",
        warehouse_id=1,
    )

    spu_material = SPUMaterial(
        spu_material_id=1,
        material_id=1,
        material_model="测试型号",
        material_specification="测试规格",
        color="测试颜色",
    )

    material_storage = MaterialStorage(
        material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        spu_material_id=1,
        actual_inbound_unit="米",
        pending_outbound=10,
        inbound_amount=20,
        current_amount=20,
    )
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail)
    db.session.add(outbound_record)
    db.session.add(outbound_record_detail)
    db.session.add(supplier)
    db.session.add(warehouse)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(spu_material)
    db.session.add(material_storage)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "outboundRecordId": 1,
        "supplierName": "深源皮革",
        "outboundType": 4,
        "remark": "2025/3/4",
        "isSizedMaterial": 0,
        "materialTypeId": 1,
        "items": [
            {
                "materialStorageId": 1,
                "actualInboundUnit": "米",
                "colorName": "Color A",
                "outboundQuantity": 20,
                "outboundRecordDetailId": 1,
                "itemTotalPrice": 240,
                "materialName": "PU面",
                "materialModel": "新型号",
                "materialSpecification": "新规格",
                "inboundModel": "新型号",
                "inboundSpecification": "新规格",
                "materialCategory": 0,
                "materialColor": "新颜色",
                "materialStorageId": 1,
                "materialUnit": "米",
                "orderRId": "K25-031",
                "remark": "010",
                "unitPrice": 12,
            },
        ],
    }
    response = client.put("/warehouse/updateoutboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200
    updated_record = (
        db.session.query(OutboundRecord).filter_by(outbound_record_id=2).first()
    )

    updated_record_detail = (
        db.session.query(OutboundRecordDetail).filter_by(outbound_record_id=2).first()
    )
    assert updated_record.remark == "2025/3/4"
    assert updated_record_detail.unit_price == 12.0
    assert updated_record_detail.outbound_amount == 20
    assert updated_record_detail.item_total_price == 240
    assert updated_record_detail.material_storage_id == 1
    assert updated_record_detail.remark == "010"

    updated_storage = (
        db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    )

    assert updated_storage.order_id == 1
    assert updated_storage.order_shoe_id == 1
    assert updated_storage.spu_material_id == 1
    assert updated_storage.pending_outbound == 20
    assert updated_storage.inbound_amount == 20
    assert updated_storage.current_amount == 20


def test_update_outbound_record_change_unit_price_and_amount(client: FlaskClient):
    """
    测试更新底材退货单的金额和数量
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
        approval_status=1,
        staff_id=WAREHOUSE_CLERK_STAFF_ID,
    )

    inbound_record_detail = InboundRecordDetail(
        id=1,
        inbound_record_id=1,
        unit_price=10,
        inbound_amount=80.0,
        item_total_price=800.0,
        size_34_inbound_amount=10,
        size_35_inbound_amount=10,
        size_36_inbound_amount=10,
        size_37_inbound_amount=10,
        size_38_inbound_amount=10,
        size_39_inbound_amount=10,
        size_40_inbound_amount=10,
        size_41_inbound_amount=10,
        material_storage_id=1,
    )

    outbound_record = OutboundRecord(
        outbound_record_id=1,
        outbound_rid="12345",
        outbound_batch_id=1,
        supplier_id=1,
        outbound_datetime=datetime_obj,
        outbound_type=4,
        is_sized_material=1,
        remark="remark",
        approval_status=0,
        staff_id=WAREHOUSE_CLERK_STAFF_ID,
    )

    outbound_record_detail = OutboundRecordDetail(
        outbound_record_id=1,
        unit_price=10,
        outbound_amount=40.0,
        item_total_price=400.0,
        size_34_outbound_amount=5,
        size_35_outbound_amount=5,
        size_36_outbound_amount=5,
        size_37_outbound_amount=5,
        size_38_outbound_amount=5,
        size_39_outbound_amount=5,
        size_40_outbound_amount=5,
        size_41_outbound_amount=5,
        material_storage_id=1,
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

    spu_material = SPUMaterial(
        spu_material_id=1,
        material_id=1,
        material_model="58216",
        material_specification="黑色/黑色沿条车灰线/后跟印灰",
        color="",
    )
    shoe_size_columns = ["35", "36", "37", "38", "39", "40", "41", "42"]
    material_storage = MaterialStorage(
        material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        spu_material_id=1,
        actual_inbound_unit="双",
        pending_outbound=40,
        inbound_amount=80,
        current_amount=80,
        shoe_size_columns=shoe_size_columns,
    )
    size_details = []
    for i in range(len(shoe_size_columns)):
        storage_size_detail = MaterialStorageSizeDetail(
            material_storage_id=1,
            size_value=shoe_size_columns[i],
            order_number=i,
            pending_outbound=5,
            inbound_amount=10,
            current_amount=10,
        )
        size_details.append(storage_size_detail)
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail)
    db.session.add(outbound_record)
    db.session.add(outbound_record_detail)
    db.session.add(supplier)
    db.session.add(warehouse)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(material_storage)
    db.session.add(spu_material)
    db.session.add_all(size_details)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "outboundRecordId": 1,
        "supplierName": "大富豪底材",
        "outboundType": 4,
        "remark": "2025/3/4",
        "isSizedMaterial": 1,
        "materialTypeId": 1,
        "items": [
            {
                "materialStorageId": 1,
                "actualInboundUnit": "双",
                "amount0": 8,
                "amount1": 8,
                "amount2": 8,
                "amount3": 8,
                "amount4": 8,
                "amount5": 8,
                "amount6": 8,
                "amount7": 8,
                "colorName": "",
                "compositeUnitCost": 0,
                "outboundQuantity": 64,
                "outboundRecordDetailId": 1,
                "itemTotalPrice": 768,
                "materialCategory": 1,
                "materialModel": "58216",
                "materialName": "大底",
                "materialSpecification": "黑色/黑色沿条车灰线/后跟印灰",
                "inboundModel": "58216",
                "inboundSpecification": "黑色/黑色沿条车灰线/后跟印灰",
                "materialColor": "",
                "materialUnit": "双",
                "orderRId": "K25-031",
                "remark": "010",
                "shoeSizeColumns": ["35", "36", "37", "38", "39", "40", "41", "42"],
                "supplierName": "大富豪底材",
                "unitPrice": 12,
            },
        ],
    }
    response = client.put("/warehouse/updateoutboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200
    updated_record = (
        db.session.query(OutboundRecord).filter_by(outbound_record_id=2).first()
    )

    updated_record_detail = (
        db.session.query(OutboundRecordDetail).filter_by(outbound_record_id=2).first()
    )
    assert updated_record.remark == "2025/3/4"
    assert updated_record_detail.unit_price == 12.0
    assert updated_record_detail.outbound_amount == 64
    assert updated_record_detail.item_total_price == 768

    expected_amounts = [8, 8, 8, 8, 8, 8, 8, 8]
    for i in range(len(expected_amounts)):
        size_amount = getattr(updated_record_detail, f"size_{34 + i}_outbound_amount")
        assert size_amount == expected_amounts[i]

    assert updated_record_detail.remark == "010"

    updated_storage = (
        db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    )

    assert updated_storage.pending_outbound == 64

    size_details = db.session.query(MaterialStorageSizeDetail).filter(
        MaterialStorageSizeDetail.material_storage_id == 1
    ).order_by(MaterialStorageSizeDetail.order_number).all()

    for i in range(len(shoe_size_columns)):
        assert size_details[i].size_value == shoe_size_columns[i]
        assert size_details[i].pending_outbound == 8
        assert size_details[i].inbound_amount == 10
        assert size_details[i].current_amount == 10

    assert updated_storage.shoe_size_columns == [
        "35",
        "36",
        "37",
        "38",
        "39",
        "40",
        "41",
        "42",
    ]

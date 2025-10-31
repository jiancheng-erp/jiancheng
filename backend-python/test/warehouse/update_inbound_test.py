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


def test_update_inbound_record_model_specification_color(client: FlaskClient):
    """
    测试更新入库单的材料型号/规格/颜色，创建新库存
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
        approval_status=2,
        staff_id=WAREHOUSE_CLERK_STAFF_ID,
        reject_reason='测试驳回',
    )

    inbound_record_detail = InboundRecordDetail(
        id=1,
        inbound_record_id=1,
        unit_price=12.5,
        inbound_amount=10.0,
        item_total_price=125.0,
        material_storage_id=1,
        order_id=1,
        spu_material_id=1,
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
        pending_inbound=20,
        inbound_amount=20,
        current_amount=20,
    )
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail)
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
        "inboundRecordId": 1,
        "supplierName": "深源皮革",
        "inboundType": 0,
        "remark": "2025/3/4",
        "payMethod": "应付账款",
        "isSizedMaterial": 0,
        "materialTypeId": 1,
        "warehouseId": 1,
        "items": [
            {
                "actualInboundUnit": "米",
                "colorName": "Color A",
                "inboundQuantity": 404,
                "inboundRecordDetailId": 1,
                "itemTotalPrice": 4848,
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
    response = client.put("/warehouse/updateinboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200

    old_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()
    )
    assert old_record.display == 0
    assert old_record.approval_status == 2
    assert old_record.reject_reason == '测试驳回'


    updated_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=2).first()
    )

    assert updated_record.inbound_datetime == datetime_obj
    assert updated_record.inbound_rid == "IR20231001120000T0"

    updated_record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=2).first()
    )
    assert updated_record.remark == "2025/3/4"
    assert updated_record_detail.unit_price == 12.0
    assert updated_record_detail.inbound_amount == 404.0
    assert updated_record_detail.item_total_price == 4848.0
    assert updated_record_detail.material_storage_id == 2
    assert updated_record_detail.remark == "010"

    old_storage = (
        db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    )

    # 修改未审核入库数量
    assert old_storage.pending_inbound == 10

    updated_storage = (
        db.session.query(MaterialStorage).filter_by(material_storage_id=2).first()
    )

    assert updated_storage.order_id == 1
    assert updated_storage.order_shoe_id == 1
    assert updated_storage.spu_material_id == 2
    assert updated_storage.pending_inbound == 404
    assert updated_storage.inbound_amount == 0
    assert updated_storage.current_amount == 0

    new_spu_material = (
        db.session.query(SPUMaterial).filter_by(spu_material_id=2).first()
    )
    assert new_spu_material.material_id == 1
    assert new_spu_material.material_model == "新型号"
    assert new_spu_material.material_specification == "新规格"
    assert new_spu_material.color == "新颜色"


def test_update_inbound_record_material_type(client: FlaskClient):
    """
    测试更新入库单的材料类型和供应商，涉及创建新库存和更新仓库
    例：开发部仓转到面料仓
    """
    # Insert dependency data into the temporary database.
    datetime_obj = datetime.strptime("2023-10-01 12:00:00", "%Y-%m-%d %H:%M:%S")
    inbound_record = InboundRecord(
        inbound_record_id=1,
        inbound_rid="IR20231001120000T0",
        inbound_batch_id=1,
        supplier_id=1,
        warehouse_id=1,
        inbound_datetime=datetime_obj,
        inbound_type=0,
        pay_method="应付账款",
        is_sized_material=0,
        remark="remark",
        approval_status=2,
        reject_reason='测试驳回',
    )

    inbound_record_detail = InboundRecordDetail(
        id=1,
        inbound_record_id=1,
        unit_price=12.5,
        inbound_amount=10.0,
        item_total_price=125.0,
        material_storage_id=1,
        spu_material_id=1,
    )

    supplier = Supplier(
        supplier_id=1,
        supplier_name="深源皮革",
    )

    supplier2 = Supplier(
        supplier_id=2,
        supplier_name="测试供应商",
    )

    warehouse = MaterialWarehouse(
        material_warehouse_id=1,
        material_warehouse_name="开发部仓",
    )

    warehouse2 = MaterialWarehouse(
        material_warehouse_id=2,
        material_warehouse_name="面料仓",
    )

    material = Material(
        material_id=1,
        material_name="开发样品",
        material_type_id=1,
        material_supplier=1,
    )

    material_type = MaterialType(
        material_type_id=1,
        material_type_name="开发样品",
        warehouse_id=1,
    )

    material2 = Material(
        material_id=2,
        material_name="PU面",
        material_type_id=2,
        material_supplier=1,
    )

    material_type2 = MaterialType(
        material_type_id=2,
        material_type_name="面料",
        warehouse_id=2,
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
        spu_material_id=1,
        pending_inbound=10,
        inbound_amount=10,
        current_amount=10,
        actual_inbound_unit="米",
    )
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail)
    db.session.add(supplier)
    db.session.add(warehouse)
    db.session.add(material)
    db.session.add(material_type)
    db.session.add(warehouse2)
    db.session.add(material2)
    db.session.add(material_type2)
    db.session.add(material_storage)
    db.session.add(supplier2)
    db.session.add(spu_material)
    create_environment(db)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundRecordId": 1,
        "supplierName": "测试供应商",
        "inboundType": 0,
        "remark": "2025-05-14",
        "payMethod": "应付账款",
        "isSizedMaterial": 0,
        "materialTypeId": 2,
        "warehouseId": 2,
        "items": [
            {
                "actualInboundUnit": "米",
                "colorName": "Color A",
                "inboundQuantity": 100,
                "inboundRecordDetailId": 1,
                "itemTotalPrice": 1200,
                "materialName": "PU面",
                "inboundModel": "面料型号",
                "inboundSpecification": "面料规格",
                "materialCategory": 0,
                "materialColor": "面料颜色",
                "materialStorageId": 1,
                "materialUnit": "米",
                "remark": "新备注",
                "unitPrice": 12,
            },
        ],
    }
    response = client.put("/warehouse/updateinboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200

    old_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()
    )

    assert old_record.display == 0
    assert old_record.approval_status == 2
    assert old_record.reject_reason == '测试驳回'

    updated_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=2).first()
    )
    assert updated_record.inbound_record_id == 2
    assert updated_record.remark == "2025-05-14"
    assert updated_record.warehouse_id == 2
    assert updated_record.supplier_id == 2
    assert updated_record.inbound_datetime == datetime_obj
    assert updated_record.inbound_rid == "IR20231001120000T0"

    updated_record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=2).all()
    )

    assert updated_record_detail[0].unit_price == 12.0
    assert updated_record_detail[0].inbound_amount == 100.0
    assert updated_record_detail[0].item_total_price == 1200.0
    assert updated_record_detail[0].material_storage_id == 2
    assert updated_record_detail[0].remark == "新备注"

    old_storage = (
        db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    )
    assert old_storage.pending_inbound == 0

    new_storage = (
        db.session.query(MaterialStorage).filter_by(material_storage_id=2).first()
    )

    assert new_storage.spu_material_id == 2
    assert new_storage.pending_inbound == 100

    new_spu_material = (
        db.session.query(SPUMaterial).filter_by(spu_material_id=2).first()
    )
    assert new_spu_material.material_id == 3  # 新材料ID
    assert new_spu_material.material_model == "面料型号"
    assert new_spu_material.material_specification == "面料规格"
    assert new_spu_material.color == "面料颜色"

    new_material = db.session.query(Material).filter_by(material_id=3).first()
    assert new_material.material_name == "PU面"
    assert new_material.material_type_id == 2
    assert new_material.material_supplier == 2


def test_update_inbound_record_change_unit_price_and_amount(client: FlaskClient):
    """
    测试更新入库单的金额和单价，不涉及创建新库存
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
        approval_status=2,
        reject_reason='测试驳回',
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
        material_storage_id=1,
        spu_material_id=1,
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
        pending_inbound=40,
        inbound_amount=15,
        current_amount=15,
        shoe_size_columns=shoe_size_columns,
    )
    size_details = []
    for i in range(len(shoe_size_columns)):
        storage_size_detail = MaterialStorageSizeDetail(
            material_storage_id=1,
            size_value=shoe_size_columns[i],
            order_number=i,
            pending_inbound=5
        )
        size_details.append(storage_size_detail)
    db.session.add(order)
    db.session.add(order_shoe)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail)
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
        "inboundRecordId": 1,
        "supplierName": "大富豪底材",
        "inboundType": 0,
        "remark": "2025/3/4",
        "payMethod": "应付账款",
        "isSizedMaterial": 1,
        "warehouseId": 1,
        "materialTypeId": 1,
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
                "colorName": "",
                "compositeUnitCost": 0,
                "inboundQuantity": 404,
                "inboundRecordDetailId": 1,
                "itemTotalPrice": 4848,
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
    response = client.put("/warehouse/updateinboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200

    old_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()
    )
    assert old_record.display == 0
    assert old_record.approval_status == 2
    assert old_record.reject_reason == '测试驳回'

    updated_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=2).first()
    )

    assert updated_record.inbound_datetime == datetime_obj
    assert updated_record.inbound_rid == "IR20231001120000T0"

    updated_record_detail = (
        db.session.query(InboundRecordDetail).filter_by(inbound_record_id=2).first()
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
        db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    )

    # 40(pending_inbound) - 10(old record detail) + 404(new record detail) = 434
    assert updated_storage.pending_inbound == 434

    size_details = db.session.query(MaterialStorageSizeDetail).filter(
        MaterialStorageSizeDetail.material_storage_id == updated_storage.material_storage_id
    ).order_by(MaterialStorageSizeDetail.order_number).all()

    assert size_details[0].pending_inbound == 5
    assert size_details[1].pending_inbound == 5
    assert size_details[2].pending_inbound == 83 # 5 - 1 + 79
    assert size_details[3].pending_inbound == 128 # 5 - 2 + 125
    assert size_details[4].pending_inbound == 152 # 5 - 3 + 150
    assert size_details[5].pending_inbound == 51  # 5 - 4 + 50
    assert size_details[6].pending_inbound == 5
    assert size_details[7].pending_inbound == 5



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

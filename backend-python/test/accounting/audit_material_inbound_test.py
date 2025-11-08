import sys
import os
from datetime import datetime
from unittest.mock import patch
import pytest
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token


# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app_config import db, create_app
from blueprints import register_blueprints
from models import *
from event_processor import EventProcessor
from constants import SHOESIZERANGE
from logger import logger


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


@pytest.fixture
def client(test_app):
    # Provide a test client for making API requests.
    return test_app.test_client()


def return_header_with_token():
    token = create_access_token(identity="caiwushenhe")
    return {"Authorization": f"Bearer {token}"}


def test_audit_material_inbound(client: FlaskClient):
    """
    测试用户审批订单
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

    spu_material = SPUMaterial(
        spu_material_id=1,
        material_id=1,
        material_model="测试型号",
        material_specification="测试规格",
        color="测试颜色",
    )

    # insert dependency data into the temporary database
    material_storage = MaterialStorage(
        material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        actual_inbound_unit="米",
        spu_material_id=1,
        pending_inbound=40.0,
    )

    inbound_record = InboundRecord(
        inbound_record_id=1,
        inbound_type=0,
        inbound_rid="IR20250406165945T0",
        supplier_id=1,
        warehouse_id=1,
        inbound_datetime=datetime.strptime("2025-04-06 16:59:45", "%Y-%m-%d %H:%M:%S"),
        total_price=650.0,
        approval_status=0,
        is_sized_material=0,
        pay_method="应付账款",
    )

    inbound_record_detail1 = InboundRecordDetail(
        id=1,
        inbound_record_id=1,
        material_storage_id=1,
        spu_material_id=2,
        inbound_amount=20.0,
        unit_price=12.5,
        item_total_price=250.0,
    )

    inbound_record_detail2 = InboundRecordDetail(
        id=2,
        inbound_record_id=1,
        material_storage_id=1,
        spu_material_id=1,
        inbound_amount=20.0,
        unit_price=20,
        item_total_price=400.0,
    )
    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_storage)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail1)
    db.session.add(inbound_record_detail2)
    db.session.add(spu_material)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundRecordId": 1,
    }
    response = client.patch("/accounting/approveinboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200

    inbound_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()
    )
    assert inbound_record.approval_status == 1
    assert inbound_record.approval_datetime is not None

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    assert storage.average_price == 16.25
    assert storage.pending_inbound == 0.0
    assert storage.inbound_amount == 40.0
    assert storage.current_amount == 40.0

    accounting_payee_payer = (
        db.session.query(AccountingPayeePayer).filter_by(payee_name="嘉泰皮革").first()
    )
    assert accounting_payee_payer is not None
    new_payable_account_entity = (
        db.session.query(AccountingPayableAccount)
        .filter_by(account_owner_id=accounting_payee_payer.payee_id)
        .first()
    )
    assert new_payable_account_entity.account_payable_balance == 650.0
    new_transaction_entity = (
        db.session.query(AccountingForeignAccountEvent)
        .filter_by(inbound_record_id=1)
        .first()
    )
    assert new_transaction_entity.transaction_amount == 650.0


def test_audit_size_material_inbound(client: FlaskClient):
    """
    测试用户审批底材订单
    例子：一个大底订单，一次入库36双，单价12.5，总价450元， 另一次入库36双，单价20元，总价720元。
    结果：storage的平均价应为16.25元，总入库数量72双，待入库数量0，当前库存72双。
    应付账户增加1170元。
    """

    # insert supplier
    supplier = Supplier(
        supplier_id=1,
        supplier_name="测试厂家",
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

    spu_material = SPUMaterial(
        spu_material_id=1,
        material_id=1,
        material_model="测试型号",
        material_specification="测试规格",
        color="测试颜色",
    )

    shoe_size_columns = ["35", "36", "37", "38", "39", "40", "41", "42"]

    # insert dependency data into the temporary database
    material_storage = MaterialStorage(
        material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        actual_inbound_unit="米",
        spu_material_id=1,
        pending_inbound=72,
        shoe_size_columns=shoe_size_columns
    )

    inbound_record = InboundRecord(
        inbound_record_id=1,
        inbound_type=0,
        inbound_rid="IR20250406165945T0",
        supplier_id=1,
        warehouse_id=1,
        inbound_datetime=datetime.strptime("2025-04-06 16:59:45", "%Y-%m-%d %H:%M:%S"),
        total_price=1170,
        approval_status=0,
        is_sized_material=1,
        pay_method="应付账款",
    )

    inbound_record_detail1 = InboundRecordDetail(
        id=1,
        inbound_record_id=1,
        material_storage_id=1,
        spu_material_id=2,
        inbound_amount=36,
        unit_price=12.5,
        item_total_price=450,
        size_34_inbound_amount=1,
        size_35_inbound_amount=2,
        size_36_inbound_amount=3,
        size_37_inbound_amount=4,
        size_38_inbound_amount=5,
        size_39_inbound_amount=6,
        size_40_inbound_amount=7,
        size_41_inbound_amount=8,
    )

    inbound_record_detail2 = InboundRecordDetail(
        id=2,
        inbound_record_id=1,
        material_storage_id=1,
        spu_material_id=1,
        inbound_amount=36,
        unit_price=20,
        item_total_price=720,
        size_34_inbound_amount=1,
        size_35_inbound_amount=2,
        size_36_inbound_amount=3,
        size_37_inbound_amount=4,
        size_38_inbound_amount=5,
        size_39_inbound_amount=6,
        size_40_inbound_amount=7,
        size_41_inbound_amount=8,
    )
    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_storage)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail1)
    db.session.add(inbound_record_detail2)
    db.session.add(spu_material)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "inboundRecordId": 1,
    }
    response = client.patch("/accounting/approveinboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200

    inbound_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()
    )
    assert inbound_record.approval_status == 1
    assert inbound_record.approval_datetime is not None

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    assert storage.average_price == 16.25
    assert storage.pending_inbound == 0.0
    assert storage.inbound_amount == 72
    assert storage.current_amount == 72

    size_details = (
        db.session.query(MaterialStorageSizeDetail)
        .filter_by(material_storage_id=1)
        .order_by(MaterialStorageSizeDetail.order_number)
        .all()
    )
    expected_sizes = [2, 4, 6, 8, 10, 12, 14, 16]
    for sd, expected in zip(size_details, expected_sizes):
        assert sd.pending_inbound == 0
        assert sd.inbound_amount == expected
        assert sd.current_amount == expected

    accounting_payee_payer = (
        db.session.query(AccountingPayeePayer).filter_by(payee_name="测试厂家").first()
    )
    assert accounting_payee_payer is not None
    new_payable_account_entity = (
        db.session.query(AccountingPayableAccount)
        .filter_by(account_owner_id=accounting_payee_payer.payee_id)
        .first()
    )
    assert new_payable_account_entity.account_payable_balance == 1170
    new_transaction_entity = (
        db.session.query(AccountingForeignAccountEvent)
        .filter_by(inbound_record_id=1)
        .first()
    )
    assert new_transaction_entity.transaction_amount == 1170

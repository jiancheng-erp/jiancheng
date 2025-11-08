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


def test_audit_material_outbound(client: FlaskClient):
    """
    测试用户审批材料退回订单
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
        pending_outbound=20.0,
        inbound_amount=100.0,
        current_amount=100.0,
    )

    inbound_record = InboundRecord(
        inbound_record_id=1,
        inbound_type=0,
        inbound_rid="IR20250406165945T0",
        supplier_id=1,
        warehouse_id=1,
        inbound_datetime=datetime.strptime("2025-04-06 16:59:45", "%Y-%m-%d %H:%M:%S"),
        total_price=1000,
        approval_status=1,
        is_sized_material=0,
        pay_method="应付账款",
    )

    inbound_record_detail1 = InboundRecordDetail(
        inbound_record_id=1,
        material_storage_id=1,
        spu_material_id=1,
        inbound_amount=100,
        unit_price=10,
        item_total_price=1000,
    )

    outbound_record = OutboundRecord(
        outbound_record_id=1,
        outbound_type=4,
        outbound_rid="OR20250406165945T4",
        supplier_id=1,
        outbound_datetime=datetime.strptime("2025-04-06 16:59:45", "%Y-%m-%d %H:%M:%S"),
        total_price=650.0,
        approval_status=0,
        is_sized_material=0,
    )

    outbound_record_detail1 = OutboundRecordDetail(
        outbound_record_id=1,
        material_storage_id=1,
        spu_material_id=2,
        outbound_amount=20.0,
        unit_price=12.5,
        item_total_price=250.0,
    )


    payee_payer = AccountingPayeePayer(
        payee_id=1,
        payee_name="嘉泰皮革",
        entity_type=0,
    )

    payable_account = AccountingPayableAccount(
        account_id=1,
        account_owner_id=1,
        account_payable_balance=1000.0,
        account_unit_id=1,
    )
    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_storage)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail1)
    db.session.add(outbound_record)
    db.session.add(outbound_record_detail1)
    db.session.add(spu_material)
    db.session.add(payee_payer)
    db.session.add(payable_account)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "outboundRecordId": 1,
    }
    response = client.patch("/accounting/approveoutboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200

    outbound_record = (
        db.session.query(OutboundRecord).filter_by(outbound_record_id=1).first()
    )
    assert outbound_record.approval_status == 1
    assert outbound_record.approval_datetime is not None

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    assert storage.average_price == 9.375
    assert storage.pending_outbound == 0.0
    assert storage.inbound_amount == 100
    assert storage.outbound_amount == 20
    assert storage.current_amount == 80.0

    accounting_payee_payer = (
        db.session.query(AccountingPayeePayer).filter_by(payee_name="嘉泰皮革").first()
    )
    assert accounting_payee_payer is not None
    new_payable_account_entity = (
        db.session.query(AccountingPayableAccount)
        .filter_by(account_owner_id=accounting_payee_payer.payee_id)
        .first()
    )
    assert new_payable_account_entity.account_payable_balance == 350.0
    new_transaction_entity = (
        db.session.query(AccountingForeignAccountEvent)
        .filter_by(outbound_record_id=1)
        .first()
    )
    assert new_transaction_entity.transaction_amount == -650.0


def test_audit_size_material_outbound(client: FlaskClient):
    """
    测试用户审批底材退货订单
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

    shoe_size_columns = ["35", "36", "37", "38", "39", "40", "41", "42", "43", "44"]

    # insert dependency data into the temporary database
    material_storage = MaterialStorage(
        material_storage_id=1,
        order_id=1,
        order_shoe_id=1,
        actual_inbound_unit="米",
        spu_material_id=1,
        pending_outbound=50,
        inbound_amount=100,
        current_amount=100,
        shoe_size_columns=shoe_size_columns
    )

    for i in range(len(shoe_size_columns)):
        size = shoe_size_columns[i]
        size_detail = MaterialStorageSizeDetail(
            material_storage_id=1,
            order_number=i,
            size_value=size,
            pending_outbound=5,
            inbound_amount=10,
            current_amount=10,
        )
        db.session.add(size_detail)

    inbound_record = InboundRecord(
        inbound_record_id=1,
        inbound_type=0,
        inbound_rid="IR20250406165945T0",
        supplier_id=1,
        warehouse_id=1,
        inbound_datetime=datetime.strptime("2025-04-06 16:59:45", "%Y-%m-%d %H:%M:%S"),
        total_price=1000,
        approval_status=1,
        is_sized_material=0,
        pay_method="应付账款",
    )

    inbound_record_detail1 = InboundRecordDetail(
        inbound_record_id=1,
        material_storage_id=1,
        spu_material_id=1,
        inbound_amount=100,
        unit_price=10,
        item_total_price=1000,
        size_34_inbound_amount=10,
        size_35_inbound_amount=10,
        size_36_inbound_amount=10,
        size_37_inbound_amount=10,
        size_38_inbound_amount=10,
        size_39_inbound_amount=10,
        size_40_inbound_amount=10,
        size_41_inbound_amount=10,
        size_42_inbound_amount=10,
        size_43_inbound_amount=10,
    )

    outbound_record = OutboundRecord(
        outbound_record_id=1,
        outbound_type=4,
        outbound_rid="OR20250406165945T4",
        supplier_id=1,
        outbound_datetime=datetime.strptime("2025-04-06 16:59:45", "%Y-%m-%d %H:%M:%S"),
        total_price=500,
        approval_status=0,
        is_sized_material=1,
    )

    outbound_record_detail1 = OutboundRecordDetail(
        outbound_record_id=1,
        material_storage_id=1,
        spu_material_id=2,
        outbound_amount=50.0,
        unit_price=10,
        item_total_price=500.0,
        size_34_outbound_amount=5,
        size_35_outbound_amount=5,
        size_36_outbound_amount=5,
        size_37_outbound_amount=5,
        size_38_outbound_amount=5,
        size_39_outbound_amount=5,
        size_40_outbound_amount=5,
        size_41_outbound_amount=5,
        size_42_outbound_amount=5,
        size_43_outbound_amount=5,
    )
    payee_payer = AccountingPayeePayer(
        payee_id=1,
        payee_name="测试厂家",
        entity_type=0,
    )

    payable_account = AccountingPayableAccount(
        account_id=1,
        account_owner_id=1,
        account_payable_balance=1000.0,
        account_unit_id=1,
    )
    db.session.add(supplier)
    db.session.add(material)
    db.session.add(material_storage)
    db.session.add(material_type)
    db.session.add(warehouse)
    db.session.add(inbound_record)
    db.session.add(inbound_record_detail1)
    db.session.add(outbound_record)
    db.session.add(outbound_record_detail1)
    db.session.add(payee_payer)
    db.session.add(payable_account)
    db.session.add(spu_material)
    db.session.commit()

    # Use the test client to hit your Flask endpoint.
    query_string = {
        "outboundRecordId": 1,
    }
    response = client.patch("/accounting/approveoutboundrecord", json=query_string, headers=return_header_with_token())
    assert response.status_code == 200

    outbound_record = (
        db.session.query(OutboundRecord).filter_by(outbound_record_id=1).first()
    )
    assert outbound_record.approval_status == 1
    assert outbound_record.approval_datetime is not None

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    assert storage.average_price == 10
    assert storage.pending_outbound == 0.0
    assert storage.inbound_amount == 100
    assert storage.outbound_amount == 50
    assert storage.current_amount == 50

    size_details = (
        db.session.query(MaterialStorageSizeDetail)
        .filter_by(material_storage_id=1)
        .order_by(MaterialStorageSizeDetail.order_number)
        .all()
    )
    inbound_expected_sizes = [10] * 10
    expected_sizes = [5] * 10
    for sd, expected in zip(size_details, expected_sizes):
        assert sd.pending_outbound == 0
        assert sd.inbound_amount == inbound_expected_sizes[sd.order_number]
        assert sd.outbound_amount == expected
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
    assert new_payable_account_entity.account_payable_balance == 500
    new_transaction_entity = (
        db.session.query(AccountingForeignAccountEvent)
        .filter_by(outbound_record_id=1)
        .first()
    )
    assert new_transaction_entity.transaction_amount == -500

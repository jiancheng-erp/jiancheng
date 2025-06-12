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
from logger import logger


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
    response = client.patch("/accounting/approveinboundrecord", json=query_string)
    assert response.status_code == 200

    inbound_record = (
        db.session.query(InboundRecord).filter_by(inbound_record_id=1).first()
    )
    assert inbound_record.approval_status == 1

    storage = db.session.query(MaterialStorage).filter_by(material_storage_id=1).first()
    assert storage.average_price == 16.25

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

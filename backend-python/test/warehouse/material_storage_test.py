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
# --- Flask App Fixture ---
@pytest.fixture
def test_app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "mysql+pymysql://jiancheng_mgt:123456Ab@localhost:3306/jiancheng_local_test",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "EC63AF9BA57B9F20",
        "JWT_SECRET_KEY": "EC63AF9BA57B9F20"
    })
    app.config['event_processor'] = EventProcessor()
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


def test_flask_api_function(client: FlaskClient, sample_data):
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
    assert response.get_json()["result"][0]["inboundRecordId"] == sample_data.inbound_record_id

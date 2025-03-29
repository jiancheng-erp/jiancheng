import sys
import os

# Add the parent directory (two levels up) to the system path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from test_app_config import create_app
from app_config import db
from models import *
from flask.testing import FlaskClient
from datetime import datetime
import requests
from blueprints import register_blueprints


@pytest.fixture
def test_app():
    # Configure the app for testing with an in-memory SQLite database.
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "secret_key": "EC63AF9BA57B9F20",  # Provide a test secret key
            "JWT_SECRET_KEY": "EC63AF9BA57B9F20",  # Provide a test JWT secret key if needed
        }
    )
    register_blueprints(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Create tables
        yield app
        db.session.remove()
        db.drop_all()  # Clean up after tests


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

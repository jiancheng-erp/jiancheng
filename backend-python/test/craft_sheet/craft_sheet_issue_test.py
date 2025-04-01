from math import prod
import sys
import os
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

# --- Flask Client Fixture ---
@pytest.fixture
def client(test_app):
    return test_app.test_client()

import pytest
from flask.testing import FlaskClient
from datetime import datetime
from unittest.mock import patch
from models import *

@pytest.fixture
def craft_issue_data(test_app):
    with test_app.app_context():
        customer = Customer(customer_id=1, customer_name="客户")
        shoe = Shoe(shoe_id=1, shoe_rid="SHOE123")
        order = Order(
            order_id=1,
            order_rid="ORD123",
            order_cid="CID123",
            start_date=datetime.today(),
            end_date=datetime.today(),
            customer_id=1,
            salesman_id=1,
            batch_info_type_id=1,
            supervisor_id=1,
            order_size_table='{"客人码": ["7.5", "8.0", "8.5"]}'
        )
        order_shoe = OrderShoe(order_shoe_id=1, order_id=1, shoe_id=1, process_sheet_upload_status="1",customer_product_name="测试鞋")
        order_shoe_type = OrderShoeType(order_shoe_type_id=1, order_shoe_id=1, shoe_type_id=1)
        craft_sheet = CraftSheet(craft_sheet_id=1, order_shoe_id=1, craft_sheet_status="1", craft_sheet_rid="CS123")
        production_item = ProductionInstructionItem(
            production_instruction_item_id=1,
            production_instruction_id=1,
            material_id=1,
            department_id=1,
            order_shoe_type_id=1,
            material_type="M",
            is_pre_purchase=True,
            material_second_type="",
        )
        craft_item = CraftSheetItem(
            craft_sheet_item_id=1,
            craft_sheet_id=1,
            production_instruction_item_id=1,
            material_type="S",
            material_id=1,
            material_model="ModelA",
            material_specification="SpecA",
            color="Black",
            remark="",
            department_id=1,
            order_shoe_type_id=1,
            material_second_type="主料",
            craft_name="缝合"
        )
        order_shoe_status = OrderShoeStatus(
            order_shoe_status_id=1,
            order_shoe_id=1,
            current_status=9,
            current_status_value=0,

        )
        operaton1 = Operation(
            operation_id=56,
            operation_name="测试操作",
            operation_type=2,
            operation_modified_status=9,
            operation_modified_value=1,
        )
        operaton2 = Operation(
            operation_id=57,
            operation_name="测试操作2",
            operation_type=2,
            operation_modified_status=9,
            operation_modified_value=2,
        )
        operaton3 = Operation(
            operation_id=58,
            operation_name="测试操作",
            operation_type=2,
            operation_modified_status=10,
            operation_modified_value=1,
        )
        operaton4 = Operation(
            operation_id=59,
            operation_name="测试操作2",
            operation_type=2,
            operation_modified_status=10,
            operation_modified_value=2,
        )
        db.session.add_all([
            customer, shoe, order, order_shoe, order_shoe_type,
            craft_sheet, production_item, craft_item, operaton1,
            operaton2, operaton3, operaton4, order_shoe_status
        ])
        db.session.commit()

@pytest.mark.usefixtures("craft_issue_data")
def test_issue_production_order_success(client: FlaskClient):
    with patch("technical.process_sheet_upload.randomIdGenerater", return_value="ABCDEF"):
        response = client.post("/craftsheet/issue", json={
            "orderShoeIds": ["SHOE123"],
            "orderId": "ORD123"
        })
        print(response.json)

        assert response.status_code == 200
        assert response.json["message"] == "Production order issued successfully"

        # You can also assert that the second BOM was created and status was updated
        second_bom = Bom.query.filter_by(bom_type=1).first()
        assert second_bom is not None
        assert second_bom.bom_rid.endswith("S")

        craft_sheet = CraftSheet.query.first()
        assert craft_sheet.craft_sheet_status == "2"

        updated_order_shoe = OrderShoe.query.first()
        assert updated_order_shoe.process_sheet_upload_status == "2"

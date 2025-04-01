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

# --- Flask Client Fixture ---
@pytest.fixture
def client(test_app):
    return test_app.test_client()

# --- Sample Data Fixture ---
@pytest.fixture
def sample_data(test_app):
    with test_app.app_context():
        customer = Customer(customer_id=1, customer_name="测试客户")
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
        shoe = Shoe(shoe_id=1, shoe_rid="SHOE123")
        order_shoe = OrderShoe(order_shoe_id=1, order_id=1, shoe_id=1, customer_product_name="测试鞋")
        total_bom = TotalBom(total_bom_id=1, order_shoe_id=1, total_bom_rid="TB123")
        bom = Bom(bom_id=1, bom_rid="BOM123", bom_type=0, order_shoe_type_id=1, bom_status="1", total_bom_id=1)
        purchase_order = PurchaseOrder(
            purchase_order_id=1,
            bom_id=1,
            purchase_order_rid="PO12345",
            purchase_order_type="N",
            purchase_order_issue_date=datetime.today(),
            order_id=1,
            order_shoe_id=1,
            purchase_order_status="1"
        )
        material_type = MaterialType(material_type_id=1, material_type_name="布料", warehouse_id=1)
        supplier = Supplier(supplier_id=1, supplier_name="供应商A")
        material = Material(
            material_id=1,
            material_name="测试物料",
            material_type_id=1,
            material_unit="m",
            material_supplier=1
        )
        production_item = ProductionInstructionItem(
            production_instruction_item_id=1,
            production_instruction_id=1,
            material_id=1,
            department_id=1,
            material_type="M",
            order_shoe_type_id=1,
            material_second_type="主料",
            is_pre_purchase=True,
        )
        bom_item = BomItem(
            bom_item_id=1,
            material_id=1,
            department_id=1,
            bom_item_add_type="M",
            unit_usage=1.0,
            total_usage=1.0,
            bom_id=1,
            production_instruction_item_id=1
        )
        divide_order = PurchaseDivideOrder(
            purchase_divide_order_id=1,
            purchase_order_id=1,
            purchase_divide_order_rid="DIV123",
            purchase_divide_order_type="N"
        )
        purchase_item = PurchaseOrderItem(
            purchase_order_item_id=1,
            bom_item_id=1,
            purchase_divide_order_id=1,
            purchase_amount=10,
            approval_amount=10,
            inbound_material_id=1,
            inbound_unit="m",
            material_id=1,
            size_type="E"
        )
        batch_info = BatchInfoType(
            batch_info_type_id=1,
            batch_info_type_name="默认",
            batch_info_type_usage=0,
            size_34_name="7.5",
            size_35_name="8.0",
            size_36_name="8.5"
        )
        order_shoe_status = OrderShoeStatus(
            order_shoe_status_id=1,
            order_shoe_id=1,
            current_status=6,
            current_status_value=0,

        )
        operaton1 = Operation(
            operation_id=50,
            operation_name="测试操作",
            operation_type=2,
            operation_modified_status=6,
            operation_modified_value=1,
        )
        operaton2 = Operation(
            operation_id=51,
            operation_name="测试操作2",
            operation_type=2,
            operation_modified_status=6,
            operation_modified_value=2,
        )
        db.session.add_all([
            customer, order, shoe, order_shoe, total_bom, bom,
            purchase_order, material_type, supplier, material,
            production_item, bom_item, divide_order, purchase_item, batch_info, order_shoe_status, operaton1, operaton2
        ])
        db.session.commit()

# --- Actual Test ---
@pytest.mark.usefixtures("sample_data")
def test_submit_purchase_divide_orders(client: FlaskClient):
    purchase_order_id = "PO12345"

    with patch("logistics.first_purchase.FILE_STORAGE_PATH", "/tmp/test_storage"), \
     patch("logistics.first_purchase.os.makedirs"), \
     patch("logistics.first_purchase.os.path.exists", return_value=False), \
     patch("logistics.first_purchase.os.mkdir"), \
     patch("logistics.first_purchase.zipfile.ZipFile"), \
     patch("logistics.first_purchase.generate_material_statistics_file"), \
     patch("logistics.first_purchase.generate_excel_file"), \
     patch("logistics.first_purchase.get_order_batch_type_helper", return_value=[]), \
     patch("logistics.first_purchase.randomIdGenerater", return_value="ABCDEF"):

         response = client.post(
            "/firstpurchase/submitpurchasedivideorders",
            json={"purchaseOrderId": purchase_order_id},
        )
         print(response.json)

         assert response.status_code == 200
         assert response.json["status"] == "success"

         updated_po = PurchaseOrder.query.filter_by(purchase_order_rid=purchase_order_id).first()
         assert updated_po.purchase_order_status == "2"

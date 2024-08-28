from app_config import app
from production.price_report import price_report_bp
from shared_apis.order import order_bp
from production.quantity_report import quantity_report_bp
from logistics.logistics_home_page import logistics_home_page_bp
from logistics.supplier_page import supplier_page_bp
from logistics.warehouse_page import warehouse_page_bp
from logistics.material_page import material_page_bp
from production.production_manager import production_manager_bp
from warehouse.warehouse_manager import warehouse_manager_bp


def register_blueprints():
    app.register_blueprint(price_report_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(quantity_report_bp)
    app.register_blueprint(logistics_home_page_bp)
    app.register_blueprint(supplier_page_bp)
    app.register_blueprint(warehouse_page_bp)
    app.register_blueprint(material_page_bp)
    app.register_blueprint(production_manager_bp)
    app.register_blueprint(warehouse_manager_bp)

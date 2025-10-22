from production.price_report import price_report_bp
from shared_apis.order import order_bp
from production.quantity_report import quantity_report_bp
from logistics.logistics_home_page import logistics_home_page_bp
from logistics.supplier_page import supplier_page_bp
from logistics.warehouse_page import warehouse_page_bp
from logistics.material_page import material_page_bp
from production.production_manager import production_manager_bp
from logistics.assets_purchase_page import assets_purchase_page_bp
from shared_apis.color import color_bp
from logistics.first_bom import first_bom_bp
from shared_apis.department import department_bp
from usage_calculation.usage_calculation import usage_calculation_bp
from business.order_import import order_import_bp
from business.order_create import order_create_bp
#from business.order_export import order_export_bp
from shared_apis.batch_info_type import batch_type_bp
from shared_apis.customer import customer_bp
from shared_apis.shoe import shoe_bp
from technical.second_bom import second_bom_bp
from development.shoe_manage import shoe_manage_bp
from development.dev_producion_order import dev_producion_order_bp
from warehouse.material_storage import material_storage_bp
from warehouse.semifinished_storage import semifinished_storage_bp
from warehouse.finished_storage import finished_storage_bp
from warehouse.make_inventory import make_inventory_bp
from shared_apis.message import message_bp
from login.login import login_bp
from human_resources.user_manage import user_manage_bp
from human_resources.staff_manage import staff_manage_bp
from shared_apis.user import user_bp
from logistics.first_purchase import first_purchase_bp
from logistics.second_purchase import second_purchase_bp
from technical.process_sheet_upload import process_sheet_upload_bp
from shared_apis.outsource_factory import outsource_factory_bp
from production.scheduling import production_scheduling_bp
from production.outsource import outsource_bp
from production.production_status_nodes import production_status_nodes_bp
from head_manager.head_manager_api import head_manager_bp
from technical.process_sheet_review import process_sheet_review
from production.production_lines import production_lines_bp
from production.production_report import production_report_bp
from logistics.multiissue_purchase_order import multiissue_purchase_order_bp
from accounting.accounts_management import accounts_management_bp
from accounting.payable_management import payable_management_bp
from logistics.package_api import package_api_bp
from logistics.last_api import last_api_bp
from logistics.cut_model_api import cut_model_api_bp
from shared_apis.revert_order import revert_order_api
from development.dev_revert_api import dev_revert_api
from usage_calculation.usage_revert_api import usage_revert_api
from technical.craft_sheet_revert_api import craft_sheet_revert_api
from accounting.audit_material_inbound import audit_material_inbound_bp
from accounting.accounting_warehouse import accounting_warehouse_bp
from accounting.accounting_term_management import accounting_term_management_bp
from accounting.audit_material_outbound import audit_material_outbound_bp
from development.dev_performance import dev_performance_bp
from accounting.accounting_recievable import accounting_recievable_bp
from technical.missing_material_purchase import missing_material_purchase_bp
from head_manager.customer_analysis import customer_analysis_bp
from flask import Flask
def register_blueprints(app: Flask):
    app.register_blueprint(price_report_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(quantity_report_bp)
    app.register_blueprint(logistics_home_page_bp)
    app.register_blueprint(supplier_page_bp)
    app.register_blueprint(warehouse_page_bp)
    app.register_blueprint(material_page_bp)
    app.register_blueprint(production_manager_bp)
    app.register_blueprint(assets_purchase_page_bp)
    app.register_blueprint(color_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(first_bom_bp)
    app.register_blueprint(second_bom_bp)
    app.register_blueprint(usage_calculation_bp)
    app.register_blueprint(order_import_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(shoe_bp)
    app.register_blueprint(shoe_manage_bp)
    app.register_blueprint(dev_producion_order_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(user_manage_bp)
    app.register_blueprint(staff_manage_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(first_purchase_bp)
    app.register_blueprint(second_purchase_bp)
    app.register_blueprint(material_storage_bp)
    app.register_blueprint(semifinished_storage_bp)
    app.register_blueprint(finished_storage_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(outsource_factory_bp)
    app.register_blueprint(process_sheet_upload_bp)
    app.register_blueprint(order_create_bp)
    app.register_blueprint(production_scheduling_bp)
    app.register_blueprint(outsource_bp)
    app.register_blueprint(production_status_nodes_bp)
    app.register_blueprint(batch_type_bp)
    app.register_blueprint(head_manager_bp)
    app.register_blueprint(process_sheet_review)
    #app.register_blueprint(order_export_bp)
    app.register_blueprint(production_lines_bp)
    app.register_blueprint(production_report_bp)
    app.register_blueprint(multiissue_purchase_order_bp)
    app.register_blueprint(accounts_management_bp)
    app.register_blueprint(payable_management_bp)
    app.register_blueprint(package_api_bp)
    app.register_blueprint(last_api_bp)
    app.register_blueprint(cut_model_api_bp)
    app.register_blueprint(revert_order_api)
    app.register_blueprint(dev_revert_api)
    app.register_blueprint(usage_revert_api)
    app.register_blueprint(craft_sheet_revert_api)
    app.register_blueprint(audit_material_inbound_bp)
    app.register_blueprint(accounting_warehouse_bp)
    app.register_blueprint(accounting_term_management_bp)
    app.register_blueprint(audit_material_outbound_bp)
    app.register_blueprint(dev_performance_bp)
    app.register_blueprint(accounting_recievable_bp)
    app.register_blueprint(make_inventory_bp)
    app.register_blueprint(missing_material_purchase_bp)
    app.register_blueprint(customer_analysis_bp)

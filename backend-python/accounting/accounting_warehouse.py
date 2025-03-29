from flask import Blueprint, jsonify, request
from models import *
from api_utility import to_camel, to_snake, db_obj_to_res, format_datetime, accounting_audit_status_converter


from app_config import app, db


accounting_warehouse_bp = Blueprint("accounting_warehouse_bp", __name__)


INBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES = ["inbound_rid", "inbound_datetime","approval_status"]
SUPPLIER_SELECTABLE_TABLE_ATTRNAMES = ["supplier_name"]
INBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES = ["unit_price", "inbound_amount","item_total_price","composite_unit_cost"]
MATERIAL_STORAGE_SELECTABLE_TABLE_ATTRNAMES = ["material_model", "craft_name", "material_storage_color","material_specification"]
MATERIAL_SELECTABLE_TABLE_ATTRNAMES = ["material_name","material_unit"]
SELECTABLE_ATTRNAMES = [INBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES,SUPPLIER_SELECTABLE_TABLE_ATTRNAMES
                        ,INBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES,MATERIAL_STORAGE_SELECTABLE_TABLE_ATTRNAMES,
                        MATERIAL_SELECTABLE_TABLE_ATTRNAMES]
name_en_cn_mapping = {
    "inbound_rid":"入库单据号",
    "inbound_datetime":"入库时间",
    "supplier_name":"供应商",
    "material_name":"材料名称",
    "material_model":"材料型号",
    "material_specification":"材料规格",
    "material_storage_color":"材料颜色",
    "unit_price":"单价",
    "material_unit":"单位",
    "inbound_amount":"入库数量",
    "item_total_price":"总价",
    "composite_unit_cost":"复合工艺单价",
    "craft_name":"工艺名称",
    "approval_status":"审批状态",
    }
type_to_attr_mapping = {
    'InboundRecord':INBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES,
    'InboundRecordDetail':INBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES,
    'Supplier':SUPPLIER_SELECTABLE_TABLE_ATTRNAMES,
    'MaterialStorage':MATERIAL_STORAGE_SELECTABLE_TABLE_ATTRNAMES,
    'Material':MATERIAL_SELECTABLE_TABLE_ATTRNAMES
}
@accounting_warehouse_bp.route("/accounting/get_warehouse_info", methods=["GET"])
def get_warehouse_info():
    entities = db.session.query(MaterialWarehouse).all()
    res_data = []
    for entity in entities:
        res_data.append(db_obj_to_res(entity, MaterialWarehouse, len('material_')))
    return jsonify({"warehouseInfo":res_data}), 200

def wrapper_helper():
    ### inboundrecord inbound_rid, inbound_date_time, supplier
    ### inboundrecorddetail unit_price, item_total_price, inbound_amount
    ### materialstorage material_storage_color, material_model, craft_name,
    # materialStorage.material_specification
    # material.material_name, material_unit
    #  
    return
@accounting_warehouse_bp.route("/accounting/get_warehouse_inbound_record", methods=["GET"])
def get_warehouse_inbound_record():
    page_num = request.args.get('pageNumber',type=int)
    page_size = request.args.get('pageSize', type=int)
    selected_warehouse = request.args.get('selectedWarehouse')
    query = (db.session.query(InboundRecord,InboundRecordDetail,MaterialStorage, Material, Supplier)
                .filter(InboundRecord.warehouse_id==selected_warehouse)
                .join(Supplier, InboundRecord.supplier_id == Supplier.supplier_id)
                .join(InboundRecordDetail, InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id)
                .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
                .join(Material, MaterialStorage.material_id == Material.material_id))
                
    print(page_num, page_size,selected_warehouse)
    total_count = query.distinct().count()
    response_entities = query.distinct().limit(page_size).offset((page_num - 1) * page_size).all()
    inbound_records = []
    print(total_count)
    for inbound_record, inbound_record_detail, material_storage, material, supplier in response_entities:
        res = db_obj_to_res(inbound_record, InboundRecord,attr_name_list=type_to_attr_mapping["InboundRecord"])
        res = db_obj_to_res(inbound_record_detail, InboundRecordDetail,attr_name_list=type_to_attr_mapping['InboundRecordDetail'],initial_res=res)
        res = db_obj_to_res(material_storage, MaterialStorage,attr_name_list=type_to_attr_mapping['MaterialStorage'],initial_res=res)
        res = db_obj_to_res(material, Material,attr_name_list=type_to_attr_mapping['Material'],initial_res=res)
        res = db_obj_to_res(supplier, Supplier,attr_name_list=type_to_attr_mapping['Supplier'],initial_res=res)
        res[to_camel('inbound_datetime')] = format_datetime(inbound_record.inbound_datetime)
        res[to_camel('approval_status')] = accounting_audit_status_converter(inbound_record.approval_status)
        inbound_records.append(res)
    return jsonify({"inboundRecords":inbound_records, "total":total_count}), 200

@accounting_warehouse_bp.route("/accounting/get_display_columns", methods=["GET"])
def get_display_columns():
    res_data = []
    res_id = 0
    for attr_name in name_en_cn_mapping.keys():
        res_data.append({"attrName":to_camel(attr_name),
                         "labelName":name_en_cn_mapping[attr_name],
                         "id":res_id})
        res_id += 1
    return jsonify({"selectableColumns":res_data}), 200
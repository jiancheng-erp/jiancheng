from flask import Blueprint, jsonify, request, send_file
from accounting import accounting
from models import *
from api_utility import to_camel, to_snake, db_obj_to_res,format_date, format_datetime,format_outbound_type, accounting_audit_status_converter
from sqlalchemy import func, and_
from general_document.accounting_inbound_excel import generate_accounting_inbound_excel
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
import time
from datetime import datetime, timedelta

from app_config import db


accounting_warehouse_bp = Blueprint("accounting_warehouse_bp", __name__)

OUTBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES = ["outbound_rid", "outbound_datetime", "outbound_type", "outbound_department","picker"]
OUTBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES = ["outbound_amount",]
OUTBOUND_MATERIAL_STORAGE_SELECTABLE_TABLE_ATTRNAMES = ["material_model", "craft_name", "material_storage_color","material_specification", "unit_price"]
OUTBOUND_MATERIAL_SELECTABLE_TABLE_ATTRNAMES = ["material_name", "material_unit"]

INBOUND_RECORD_SUBQUERY_SUMMARY_COLUMNS = ["unit_price", "total_amount"]
INBOUND_SUMMARY_MATERIAL_COLUMNS = ["material_name","material_unit"]


INBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES = ["inbound_rid", "inbound_datetime","approval_status"]
INBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES = ["unit_price", "inbound_amount","item_total_price","composite_unit_cost"]
MATERIAL_STORAGE_SELECTABLE_TABLE_ATTRNAMES = ["material_model", "craft_name", "material_storage_color","material_specification"]
MATERIAL_SELECTABLE_TABLE_ATTRNAMES = ["material_name","material_unit"]


SUPPLIER_SELECTABLE_TABLE_ATTRNAMES = ["supplier_name"]

SELECTABLE_ATTRNAMES = [INBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES,SUPPLIER_SELECTABLE_TABLE_ATTRNAMES
                        ,INBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES,MATERIAL_STORAGE_SELECTABLE_TABLE_ATTRNAMES,
                        MATERIAL_SELECTABLE_TABLE_ATTRNAMES]
name_en_cn_mapping_inbound = {
    "inbound_rid":"入库单据号",
    "inbound_datetime":"入库时间",
    "supplier_name":"供应商",
    "material_name":"材料名称",
    "material_model":"材料型号",
    "material_specification":"材料规格",
    "material_storage_color":"材料颜色",
    "unit_price":"采购单价",
    "material_unit":"单位",
    "inbound_amount":"入库数量",
    "item_total_price":"总价",
    "approval_status":"审批状态",
    }
name_mapping_inbound_summary = {
    "supplier_name":"供应商",
    "material_name":"材料名称",
    "material_model":"材料型号",
    "material_color":"材料颜色",
    "material_specification":"材料规格",
    "unit_price":"采购单价",
    "material_unit":"单位",
    "total_amount":"总入库数量",
    "total_price":"总价",
    "spu_Rid":"SPU"
    # "craft_name":"工艺名称",
    # "approval_status":"审批状态",
}
name_en_cn_mapping_outbound = {
    "outbound_rid":"出库单据号",
    "outbound_datetime":"出库时间",
    "outbound_type":"出库类型",
    "outbound_department":"接收部门",
    "picker":"接收人",
    "supplier_name":"供应商",
    "material_name":"材料名称",
    "material_model":"材料型号",
    "material_specification":"材料规格",
    "material_storage_color":"材料颜色",
    "unit_price":"库存单价",
    "material_unit":"单位",
    "outbound_amount":"出库数量",
    "item_total_price":"总价",
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
@accounting_warehouse_bp.route("/accounting/get_warehouse_outbound_record", methods=["GET"])
def get_warehouse_outbound_record():
    page_num = request.args.get('pageNumber',type=int)
    page_size = request.args.get('pageSize', type=int)
    warehouse_filter = request.args.get('selectedWarehouse')
    supplier_name_filter = request.args.get('supplierNameFilter', type=str)
    date_range_filter_start = request.args.get('dateRangeFilterStart', type=str)
    date_range_filter_end = request.args.get('dateRangeFilterEnd', type=str)
    material_model_filter = request.args.get('materialModelFilter', type=str)
    outbound_type_filter = request.args.get('outboudnTypeFilter', type=str)
    query = (db.session.query(OutboundRecord, OutboundRecordDetail, MaterialStorage, Material, Supplier, MaterialType, MaterialWarehouse)
             .join(OutboundRecordDetail, OutboundRecord.outbound_record_id == OutboundRecordDetail.outbound_record_id)
             .join(MaterialStorage, OutboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
             .join(Material, MaterialStorage.material_id == Material.material_id)
             .join(Supplier, Material.material_supplier == Supplier.supplier_id)
             .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
             .join(MaterialWarehouse, MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id))
    if outbound_type_filter:
        query = query.filter(OutboundRecord.outbound_type == outbound_type_filter)
    if warehouse_filter:
        query = query.filter(MaterialWarehouse.warehouse_id == warehouse_filter)
    if supplier_name_filter:
        query = query.filter(Supplier.supplier_name.ilike(f"%{supplier_name_filter}%"))
    if date_range_filter_start:
        query = query.filter(OutboundRecord.outbound_datetime >= date_range_filter_start)
    if date_range_filter_end:
        query = query.filter(OutboundRecord.outbound_datetime <= date_range_filter_end)
    if material_model_filter:
        query = query.filter(MaterialStorage.material_model.ilike(f"%{material_model_filter}%"))
    total_count = query.distinct().count()
    response_entities = query.distinct().limit(page_size).offset((page_num - 1) * page_size).all()
    outbound_records = []
    for outbound_record, outbound_record_detail, material_storage, material, supplier, material_type, material_warehouse in response_entities:
        res = db_obj_to_res(outbound_record, OutboundRecord, attr_name_list=OUTBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES)
        res = db_obj_to_res(outbound_record_detail, OutboundRecordDetail, attr_name_list=OUTBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        res = db_obj_to_res(material_storage, MaterialStorage, attr_name_list=OUTBOUND_MATERIAL_STORAGE_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        res = db_obj_to_res(material, Material, attr_name_list=MATERIAL_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        res = db_obj_to_res(supplier, Supplier,attr_name_list=SUPPLIER_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        res[to_camel('outbound_datetime')] = format_datetime(outbound_record.outbound_datetime)
        res[to_camel('outbound_type')] = format_outbound_type(outbound_record.outbound_type)
        outbound_records.append(res)
    return jsonify({'outboundRecords':outbound_records, "total":total_count}), 200
    
@accounting_warehouse_bp.route("/accounting/get_warehouse_inbound_record", methods=["GET"])
def get_warehouse_inbound_record():
    page_num = request.args.get('pageNumber',type=int)
    page_size = request.args.get('pageSize', type=int)
    warehouse_filter = request.args.get('selectedWarehouse')
    supplier_name_filter = request.args.get('supplierNameFilter', type=str)
    date_range_filter_start = request.args.get('dateRangeFilterStart', type=str)
    date_range_filter_end = request.args.get('dateRangeFilterEnd', type=str)
    material_model_filter = request.args.get('materialModelFilter', type=str)
    # approval_status_filter = request.args.get('approvalStatusFilter', type=str)
    # print(approval_status_filter)
    query = (db.session.query(InboundRecord,InboundRecordDetail,MaterialStorage, Material, Supplier)
                .join(Supplier, InboundRecord.supplier_id == Supplier.supplier_id)
                .join(InboundRecordDetail, InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id)
                .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
                .join(Material, MaterialStorage.material_id == Material.material_id))
    print(date_range_filter_end)
    if warehouse_filter:
        query = query.filter(InboundRecord.warehouse_id == warehouse_filter)
    if supplier_name_filter:
        query = query.filter(Supplier.supplier_name.ilike(f"%{supplier_name_filter}%"))
    if date_range_filter_start:
        query = query.filter(InboundRecord.inbound_datetime >= date_range_filter_start)
    if date_range_filter_end:
        ### next day
        input_date_time = datetime.strptime(date_range_filter_end, '%Y-%m-%d')
        next_day_delta = timedelta(days=1)
        query_compare_date = format_date((input_date_time + next_day_delta))
        query = query.filter(InboundRecord.inbound_datetime <= query_compare_date)
    if material_model_filter:
        query = query.filter(MaterialStorage.material_model.ilike(f"%{material_model_filter}%"))
    # if approval_status_filter != []:
    #     query = query.filter(InboundRecord.approval_status.in_(approval_status_filter))
    total_count = query.distinct().count()
    response_entities = query.distinct().limit(page_size).offset((page_num - 1) * page_size).all()
    inbound_records = []
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

@accounting_warehouse_bp.route("/accounting/get_warehouse_inbound_summery", methods=["GET"])
def get_warehouse_inbound_summery():
    page_num = request.args.get('pageNumber',type=int)
    page_size = request.args.get('pageSize', type=int)
    warehouse_filter = request.args.get('selectedWarehouse')
    supplier_name_filter = request.args.get('supplierNameFilter', type=str)
    date_range_filter_start = request.args.get('dateRangeFilterStart', type=str)
    date_range_filter_end = request.args.get('dateRangeFilterEnd', type=str)
    material_model_filter = request.args.get('materialModelFilter', type=str)
    # approval_status_filter = request.args.get('approvalStatusFilter', type=str)

    inbound_records = (db.session.query(InboundRecord.inbound_record_id))
    if warehouse_filter:
        inbound_records = inbound_records.filter(InboundRecord.warehouse_id == warehouse_filter)
    if date_range_filter_start:
        inbound_records = inbound_records.filter(InboundRecord.inbound_datetime >= date_range_filter_start)
    if date_range_filter_end:
        inbound_records = inbound_records.filter(InboundRecord.inbound_datetime <= date_range_filter_end)
    inbound_records_result = [r.inbound_record_id for r in inbound_records.all()]
    # query = (db.session.query(SPUMaterial.material_id, SPUMaterial.material_model, InboundRecordDetail.unit_price, func.sum(InboundRecordDetail.inbound_amount))
    #          .filter(InboundRecordDetail.inbound_record_id.in_(inbound_records_result))
    #          .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
    #          .join(Material, MaterialStorage.material_id == Material.material_id)
    #          .join(SPUMaterial, SPUMaterial.material_id == Material.material_id)
    #                  .group_by(SPUMaterial.material_id ,SPUMaterial.material_model, InboundRecordDetail.unit_price)
    #                  )
    query = (db.session.query(SPUMaterial, InboundRecordDetail.unit_price, func.sum(InboundRecordDetail.inbound_amount))
             .filter(InboundRecordDetail.inbound_record_id.in_(inbound_records_result))
             .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
             .join(Material, MaterialStorage.material_id == Material.material_id)
             .join(SPUMaterial,and_(Material.material_id == SPUMaterial.material_id, MaterialStorage.material_model == SPUMaterial.material_model,
                    MaterialStorage.material_specification == SPUMaterial.material_specification,
                     MaterialStorage.material_storage_color == SPUMaterial.color))
                     .group_by(SPUMaterial.spu_material_id, InboundRecordDetail.unit_price)
                    )

    time_period_subquery = query.subquery()
    
    response_query = (db.session.query(time_period_subquery, Material, Supplier)
                      .join(Material, time_period_subquery.c.material_id == Material.material_id)
                      .join(Supplier, Material.material_supplier == Supplier.supplier_id)
                      
                      )
    # inbound_record_summery_subquery = query.subquery()
    # response_query = (db.session.query(inbound_record_summery_subquery, MaterialStorage, Material, Supplier)
    #                   .join(MaterialStorage, inbound_record_summery_subquery.c.material_storage_id == MaterialStorage.material_storage_id)
    #                   .join(Material, MaterialStorage.material_id == Material.material_id)
    #                   .join(Supplier, Supplier.supplier_id == Material.material_supplier))
    # print(response_query.all())
    if supplier_name_filter:
        response_query  = response_query.filter(Supplier.supplier_name.ilike(f"%{supplier_name_filter}%"))
    if material_model_filter:
        response_query = response_query.filter(time_period_subquery.c.material_model.ilike(f"%{material_model_filter}%"))
    total_count = response_query.distinct().count()
    response_entities = response_query.distinct().limit(page_size).offset((page_num - 1) * page_size).all()
    inbound_summary = []
    print(response_entities[0])
    for spu_id,m_id,m_model,m_specification, color, spu_rid, unit_price, inbound_amount_sum, material, supplier in response_entities:
        res = db_obj_to_res(material, Material,attr_name_list=INBOUND_SUMMARY_MATERIAL_COLUMNS)
        res['supplierName'] = supplier.supplier_name
        res['unitPrice'] = unit_price
        res['totalAmount'] = inbound_amount_sum
        res['totalPrice'] = unit_price * inbound_amount_sum
        res['materialModel'] = m_model
        res['materialSpecification'] = m_specification
        res['materialColor'] = color
        res['spuRid'] = spu_rid
        inbound_summary.append(res)
    return jsonify({"inboundSummary":inbound_summary, "total":total_count}), 200




@accounting_warehouse_bp.route("/accounting/get_inbound_display_columns", methods=["GET"])
def get_inbound_display_columns():
    res_data = []
    res_id = 0
    for attr_name in name_en_cn_mapping_inbound.keys():
        res_data.append({"attrName":to_camel(attr_name),
                         "labelName":name_en_cn_mapping_inbound[attr_name],
                         "id":res_id})
        res_id += 1
    return jsonify({"selectableColumns":res_data}), 200
@accounting_warehouse_bp.route("/accounting/get_inbound_summary_display_columns", methods=["GET"])
def get_inbound_summary_columns():
    res_data = []
    res_id = 0
    for attr_name in name_mapping_inbound_summary.keys():
        res_data.append({"attrName":to_camel(attr_name),
                         "labelName":name_mapping_inbound_summary[attr_name],
                         "id":res_id})
        res_id += 1
    return jsonify({"selectableColumns":res_data}), 200
@accounting_warehouse_bp.route("/accounting/get_outbound_display_columns", methods=["GET"])
def get_outbound_display_columns():
    res_data = []
    res_id = 0
    for attr_name in name_en_cn_mapping_outbound.keys():
        res_data.append({"attrName":to_camel(attr_name),
                         "labelName":name_en_cn_mapping_outbound[attr_name],
                         "id":res_id})
        res_id += 1
    return jsonify({"selectableColumns":res_data}), 200

@accounting_warehouse_bp.route("/accounting/createinboundexcelanddownload", methods=["GET"])
def create_excel_and_download():
    warehouse_filter = request.args.get('selectedWarehouse')
    supplier_name_filter = request.args.get('supplierNameFilter', type=str)
    date_range_filter_start = request.args.get('dateRangeFilterStart', type=str)
    date_range_filter_end = request.args.get('dateRangeFilterEnd', type=str)
    material_model_filter = request.args.get('materialModelFilter', type=str)
    # approval_status_filter = request.args.get('approvalStatusFilter', type=str)
    # print(approval_status_filter)
    query = (db.session.query(InboundRecord,InboundRecordDetail,MaterialStorage, Material, Supplier)
                .join(Supplier, InboundRecord.supplier_id == Supplier.supplier_id)
                .join(InboundRecordDetail, InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id)
                .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
                .join(Material, MaterialStorage.material_id == Material.material_id))
    
    if warehouse_filter:
        query = query.filter(InboundRecord.warehouse_id == warehouse_filter)
    if supplier_name_filter:
        query = query.filter(Supplier.supplier_name.ilike(f"%{supplier_name_filter}%"))
    if date_range_filter_start:
        query = query.filter(InboundRecord.inbound_datetime >= date_range_filter_start)
    if date_range_filter_end:
        query = query.filter(InboundRecord.inbound_datetime <= date_range_filter_end)
    if material_model_filter:
        query = query.filter(MaterialStorage.material_model.ilike(f"%{material_model_filter}%"))
    # if approval_status_filter != []:
    #     query = query.filter(InboundRecord.approval_status.in_(approval_status_filter))
    total_count = query.distinct().count()
    response_entities = query.distinct().all()
    inbound_records = []
    for inbound_record, inbound_record_detail, material_storage, material, supplier in response_entities:
        res = db_obj_to_res(inbound_record, InboundRecord,attr_name_list=type_to_attr_mapping["InboundRecord"])
        res = db_obj_to_res(inbound_record_detail, InboundRecordDetail,attr_name_list=type_to_attr_mapping['InboundRecordDetail'],initial_res=res)
        res = db_obj_to_res(material_storage, MaterialStorage,attr_name_list=type_to_attr_mapping['MaterialStorage'],initial_res=res)
        res = db_obj_to_res(material, Material,attr_name_list=type_to_attr_mapping['Material'],initial_res=res)
        res = db_obj_to_res(supplier, Supplier,attr_name_list=type_to_attr_mapping['Supplier'],initial_res=res)
        res[to_camel('inbound_datetime')] = format_datetime(inbound_record.inbound_datetime)
        res[to_camel('approval_status')] = accounting_audit_status_converter(inbound_record.approval_status)
        inbound_records.append(res)
    # Generate the Excel file using the inbound_summary data
    template_path = FILE_STORAGE_PATH + "/财务入库总单模板.xlsx"
    timestamp = str(time.time())
    new_file_name = f"财务入库单总单输出_{timestamp}.xlsx"
    save_path = FILE_STORAGE_PATH + "/财务部文件/入库总单/" + new_file_name
    time_range_string = date_range_filter_start + "至" + date_range_filter_end if date_range_filter_start and date_range_filter_end else "全部"
    generate_accounting_inbound_excel(template_path, save_path, warehouse_filter, supplier_name_filter, material_model_filter,time_range_string ,inbound_records)
    return send_file(save_path, as_attachment=True, download_name=new_file_name)
    
    
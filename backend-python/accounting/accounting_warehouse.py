from flask import Blueprint, jsonify, request, send_file
from accounting import accounting
from models import *
from api_utility import to_camel, to_snake, db_obj_to_res,format_date, format_datetime,format_outbound_type, accounting_audit_status_converter
from api_utility import normalize_decimal
from sqlalchemy import func, and_, or_
from general_document.accounting_inbound_excel import generate_accounting_inbound_excel
from general_document.accounting_summary_excel import generate_accounting_summary_excel
from general_document.accounting_warehouse_excel import generate_accounting_warehouse_excel
from file_locations import FILE_STORAGE_PATH, IMAGE_STORAGE_PATH, IMAGE_UPLOAD_PATH
import time
from datetime import datetime, timedelta
from logger import logger
from app_config import db
import os
from constants import INBOUND_RECORD_TYPE_OPTIONS


accounting_warehouse_bp = Blueprint("accounting_warehouse_bp", __name__)

# outbound attrnames
OUTBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES = ["outbound_rid", "outbound_datetime", "outbound_type", "outbound_department","picker", "approval_status"]
OUTBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES = ["outbound_amount",]
OUTBOUND_MATERIAL_SELECTABLE_TABLE_ATTRNAMES = ["material_name", "material_unit"]

# inbound attrnames
INBOUND_RECORD_SUBQUERY_SUMMARY_COLUMNS = ["unit_price", "total_amount"]
INBOUND_SUMMARY_MATERIAL_COLUMNS = ["material_name","material_unit"]

INBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES = ["inbound_rid", "inbound_datetime","approval_status"]
INBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES = ["unit_price", "inbound_amount","item_total_price","composite_unit_cost","remark"]

# inventory attrnames
INVENTORY_MATERIAL_STORAGE_ATTRNAMES = ["material_storage_id", "pending_inbound", "pending_outbound", "inbound_amount", "outbound_amount", "current_amount", "unit_price", "material_outsource_status", "material_outsource_date",
                                        "material_estimated_arrival_date", "actual_inbound_unit", "average_price", "material_storage_status"]

MATERIAL_SELECTABLE_TABLE_ATTRNAMES = ["material_name"]

SPU_MATERIAL_TABLE_ATTRNAMES = ['material_model','material_specification','color','spu_rid']
SUPPLIER_SELECTABLE_TABLE_ATTRNAMES = ["supplier_name"]
SELECTABLE_ATTRNAMES = [INBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES,SUPPLIER_SELECTABLE_TABLE_ATTRNAMES
                        ,INBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES,
                        MATERIAL_SELECTABLE_TABLE_ATTRNAMES]

name_mapping_inventory = {
    "material_warehouse":"仓库",
    "supplier_name":"供应商",
    "material_type":"材料类型",
    "material_name":"材料名称",
    "material_model":"材料型号",
    "material_specification":"材料规格",
    "color":"材料颜色",
    "order_rid":"订单号",
    "customer_product_name":"客户鞋型号",
    "shoe_rid":"工厂鞋型号",
    "material_warehouse":"仓库",
    "pending_inbound":"未审核入库数",
    "pending_outbound":"未审核出库数",
    "inbound_amount":"已审核入库数",
    "outbound_amount":"已审核出库数",
    "current_amount":"库存数",
    "unit_price":"最新采购单价",
    "actual_inbound_unit":"入库单位",
    "average_price":"库存均价",
    "item_total_price":"总价",
}

name_en_cn_mapping_inbound = {
    "inbound_rid":"入库单据号",
    "inbound_datetime":"入库时间",
    "material_warehouse":"仓库",
    "supplier_name":"供应商",
    "material_name":"材料名称",
    "material_model":"材料型号",
    "color":"材料颜色",
    "material_specification":"材料规格",
    "order_rid":"订单号",
    "unit_price":"采购单价",
    "actual_inbound_unit":"单位",
    "inbound_amount":"入库数量",
    "item_total_price":"总价",
    "approval_status":"审批状态",
    "spu_rid":"SPU",
    "remark":"备注",
    }
col_width_mapping = {
    "inbound_rid":"160px",
    "inbound_datetime":"155px",
    "material_warehouse":"100px",
    "supplier_name":"115px",
    "material_name":"140px",
    "material_model":"165px",
    "color":"85px",
    "material_specification":"170px",
    "order_rid":"95px",
    "unit_price":"85px",
    "actual_inbound_unit":"60px",
    "inbound_amount":"90px",
    "item_total_price":"80px",
    "approval_status":"85px",
    "spu_rid":"180px",
    "remark":"85px"

}

name_mapping_inbound_summary = {
    "material_warehouse":"仓库",
    "supplier_name":"供应商",
    "material_name":"材料名称",
    "material_model":"材料型号",
    "material_color":"材料颜色",
    "material_specification":"材料规格",
    "order_rid":"订单号",   
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
    "color":"材料颜色",
    "unit_price":"库存单价",
    "actual_inbound_unit":"单位",
    "outbound_amount":"出库数量",
    "item_total_price":"总价",
    "approval_status":"审批状态",
}
type_to_attr_mapping = {
    'InboundRecord':INBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES,
    'InboundRecordDetail':INBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES,
    'Supplier':SUPPLIER_SELECTABLE_TABLE_ATTRNAMES,
    'SPUMaterial':SPU_MATERIAL_TABLE_ATTRNAMES,
    'Material':MATERIAL_SELECTABLE_TABLE_ATTRNAMES
}
@accounting_warehouse_bp.route("/accounting/get_warehouse_info", methods=["GET"])
def get_warehouse_info():
    entities = db.session.query(MaterialWarehouse).all()
    res_data = []
    for entity in entities:
        res_data.append(db_obj_to_res(entity, MaterialWarehouse, len('material_')))
    return jsonify({"warehouseInfo":res_data}), 200


@accounting_warehouse_bp.route("/accounting/get_warehouse_outbound_record", methods=["GET"])
def get_warehouse_outbound_record():
    page_num = request.args.get('pageNumber',type=int)
    page_size = request.args.get('pageSize', type=int)
    warehouse_filter = request.args.get('selectedWarehouse')
    supplier_name_filter = request.args.get('supplierNameFilter', type=str)
    date_range_filter_start = request.args.get('dateRangeFilterStart', type=str)
    date_range_filter_end = request.args.get('dateRangeFilterEnd', type=str)
    material_name_filter = request.args.get('materialNameFilter', type=str)
    material_model_filter = request.args.get('materialModelFilter', type=str)
    material_specification_filter = request.args.get('materialSpecificationFilter', type=str)
    material_color_filter = request.args.get('materialColorFilter', type=str)
    outbound_type_filter = request.args.getlist('outboundTypeFilter[]')
    outbound_rid_filter = request.args.get('outboundRIdFilter', type=str)
    audit_status_filter = request.args.getlist('auditStatusFilter[]')
    query = (
        db.session.query(OutboundRecord, OutboundRecordDetail, Material, Supplier, MaterialType, MaterialWarehouse, SPUMaterial, MaterialStorage)
        .join(OutboundRecordDetail, OutboundRecord.outbound_record_id == OutboundRecordDetail.outbound_record_id)
        .join(MaterialStorage, OutboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
        .join(SPUMaterial, MaterialStorage.spu_material_id == SPUMaterial.spu_material_id)
        .join(Material, SPUMaterial.material_id == Material.material_id)
        .join(Supplier, Material.material_supplier == Supplier.supplier_id)
        .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
        .join(MaterialWarehouse, MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id)
        .filter(OutboundRecord.display == 1)
        .order_by(OutboundRecord.outbound_datetime.desc())
    )
    if outbound_type_filter != []:
        query = query.filter(OutboundRecord.outbound_type.in_(outbound_type_filter))
    if warehouse_filter:
        query = query.filter(MaterialWarehouse.material_warehouse_id == warehouse_filter)
    if supplier_name_filter:
        query = query.filter(Supplier.supplier_name.ilike(f"%{supplier_name_filter}%"))
    if material_name_filter:
        query = query.filter(Material.material_name.ilike(f"%{material_name_filter}%"))
    if material_model_filter:
        query = query.filter(SPUMaterial.material_model.ilike(f"%{material_model_filter}%"))
    if material_specification_filter:
        query = query.filter(SPUMaterial.material_specification.ilike(f"%{material_specification_filter}%"))
    if material_color_filter:
        query = query.filter(SPUMaterial.color.ilike(f"%{material_color_filter}%"))
    if date_range_filter_start:
        query = query.filter(OutboundRecord.outbound_datetime >= date_range_filter_start)
    if date_range_filter_end:
        ### next day
        input_date_time = datetime.strptime(date_range_filter_end, '%Y-%m-%d')
        next_day_delta = timedelta(days=1)
        query_compare_date = format_date((input_date_time + next_day_delta))
        query = query.filter(OutboundRecord.outbound_datetime <= query_compare_date)
    if outbound_rid_filter:
        query = query.filter(OutboundRecord.outbound_rid.ilike(f"%{outbound_rid_filter}%"))
    if audit_status_filter != []:
        query = query.filter(OutboundRecord.approval_status.in_(audit_status_filter))
    
    total_count = query.distinct().count()
    response_entities = query.distinct().limit(page_size).offset((page_num - 1) * page_size).all()
    outbound_records = []
    department_mapping = {entity.department_id:entity.department_name for entity in db.session.query(Department).all()}
    for outbound_record, outbound_record_detail, material, supplier, material_type, material_warehouse, spu, material_storage in response_entities:
        res = db_obj_to_res(outbound_record, OutboundRecord, attr_name_list=OUTBOUND_RECORD_SELECTABLE_TABLE_ATTRNAMES)
        res = db_obj_to_res(outbound_record_detail, OutboundRecordDetail, attr_name_list=OUTBOUND_RECORD_DETAIL_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        res = db_obj_to_res(spu, SPUMaterial, attr_name_list=SPU_MATERIAL_TABLE_ATTRNAMES, initial_res=res)
        res = db_obj_to_res(material, Material, attr_name_list=MATERIAL_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        res = db_obj_to_res(supplier, Supplier,attr_name_list=SUPPLIER_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        res = db_obj_to_res(material_storage, MaterialStorage, attr_name_list=INVENTORY_MATERIAL_STORAGE_ATTRNAMES,initial_res=res)
        res[to_camel('unit_price')] = outbound_record_detail.unit_price
        res[to_camel('outbound_datetime')] = format_datetime(outbound_record.outbound_datetime)
        res[to_camel('outbound_type')] = format_outbound_type(outbound_record.outbound_type)
        res[to_camel('outbound_department')] = department_mapping[outbound_record.outbound_department] if outbound_record.outbound_department else ''
        res[to_camel('item_total_price')] = outbound_record_detail.item_total_price
        res[to_camel('approval_status')] = accounting_audit_status_converter(outbound_record.approval_status)
        outbound_records.append(res)
    return jsonify({'outboundRecords':outbound_records, "total":total_count}), 200

def _get_warehouse_inventory_query(data: dict, all_records=False):
    page_num = data.get('pageNumber',type=int)
    page_size = data.get('pageSize', type=int)
    warehouse_filter = data.get('selectedWarehouse')
    supplier_name_filter = data.get('supplierNameFilter', type=str)
    material_model_filter = data.get('materialModelFilter', type=str)
    material_name_filter = data.get('materialNameFilter', type=str)
    material_specification_filter = data.get('materialSpecificationFilter', type=str)
    material_color_filter = data.get('materialColorFilter', type=str)

    order_rid_filter = data.get('orderRidFilter', type=str)
    order_shoe_customer_name_filter = data.get('customerProductNameFilter', type=str)
    shoe_rid_filter = data.get('shoeRidFilter', type=str)
    not_zero_flag_filter = data.get('includeZeroFilter', type=str)
    query = (db.session.query(MaterialStorage, Order, OrderShoe, Shoe, SPUMaterial, Material, Supplier, MaterialType, MaterialWarehouse)
             .outerjoin(Order,MaterialStorage.order_id == Order.order_id)
             .outerjoin(OrderShoe, MaterialStorage.order_shoe_id == OrderShoe.order_shoe_id)
             .outerjoin(Shoe, OrderShoe.shoe_id == Shoe.shoe_id)
             .join(SPUMaterial, MaterialStorage.spu_material_id == SPUMaterial.spu_material_id)
             .join(Material, SPUMaterial.material_id == Material.material_id)
             .join(Supplier, Material.material_supplier == Supplier.supplier_id)
             .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
             .join(MaterialWarehouse, MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id))
    # 过滤早期没有入库记录的库存
    query = query.filter(
        or_(
            MaterialStorage.pending_inbound != 0,
            MaterialStorage.pending_outbound != 0,
            MaterialStorage.inbound_amount != 0,
            MaterialStorage.outbound_amount != 0,
            MaterialStorage.current_amount != 0,
        )
    )
    
    if warehouse_filter:
        query = query.filter(MaterialWarehouse.material_warehouse_id == warehouse_filter)
    if supplier_name_filter:
        query = query.filter(Supplier.supplier_name.ilike(f"%{supplier_name_filter}%"))
    if material_model_filter:
        query = query.filter(SPUMaterial.material_model.ilike(f"%{material_model_filter}%"))
    if material_name_filter:
        query = query.filter(Material.material_name.ilike(f"%{material_name_filter}%"))
    if material_model_filter:
        query = query.filter(SPUMaterial.material_model.ilike(f"%{material_model_filter}%"))
    if material_specification_filter:
        query = query.filter(SPUMaterial.material_specification.ilike(f"%{material_specification_filter}%"))
    if material_color_filter:
        query = query.filter(SPUMaterial.color.ilike(f"%{material_color_filter}%"))
    if order_rid_filter:
        query = query.filter(Order.order_rid.ilike(f"%{order_rid_filter}%"))
    if order_shoe_customer_name_filter:
        query = query.filter(OrderShoe.customer_product_name.ilike(f"%{order_shoe_customer_name_filter}"))
    if shoe_rid_filter:
        query = query.filter(Shoe.shoe_rid.ilike(f"%{shoe_rid_filter}"))
    
    if not_zero_flag_filter == 'true':
        query = query.filter(or_(MaterialStorage.pending_inbound > 0, MaterialStorage.current_amount > 0))

    query = query.order_by(MaterialStorage.material_storage_id.asc())
    total_count = query.distinct().count()
    if all_records:
        response_entities = query.all()
    else:
        response_entities = query.distinct().limit(page_size).offset((page_num - 1) * page_size).all()
    current_inventory = []
    for material_storage, order, order_shoe, shoe, spu_material, material, supplier, material_type, material_warehouse in response_entities:
        res = db_obj_to_res(material_storage, MaterialStorage, attr_name_list=INVENTORY_MATERIAL_STORAGE_ATTRNAMES)
        res = db_obj_to_res(spu_material, SPUMaterial, attr_name_list=SPU_MATERIAL_TABLE_ATTRNAMES, initial_res=res)
        res = db_obj_to_res(material, Material, attr_name_list=MATERIAL_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        res = db_obj_to_res(supplier, Supplier,attr_name_list=SUPPLIER_SELECTABLE_TABLE_ATTRNAMES,initial_res=res)
        average_price = material_storage.average_price if material_storage.average_price else 0
        res[to_camel('order_rid')] = order.order_rid if order else None
        res[to_camel('customer_product_name')] = order_shoe.customer_product_name if order_shoe else None
        res[to_camel('shoe_rid')] = shoe.shoe_rid if shoe else None
        res[to_camel('material_type')] = material_type.material_type_name
        res[to_camel('material_warehouse')] = material_warehouse.material_warehouse_name
        res[to_camel('item_total_price')] = round(material_storage.current_amount * average_price, 4)
        current_inventory.append(res)
    return current_inventory, total_count


def _get_warehouse_inbound_record_query(data: dict):
    page_num = data.get('pageNumber',type=int)
    page_size = data.get('pageSize', type=int)
    warehouse_filter = data.get('selectedWarehouse')
    supplier_name_filter = data.get('supplierNameFilter', type=str)
    date_range_filter_start = data.get('dateRangeFilterStart', type=str)
    date_range_filter_end = data.get('dateRangeFilterEnd', type=str)
    inbound_rid_filter = data.get('inboundRIdFilter', type=str)
    material_name_filter = data.get('materialNameFilter', type=str)
    material_model_filter = data.get('materialModelFilter', type=str)
    material_specification_filter = data.get('materialSpecificationFilter', type=str)
    material_color_filter = data.get('materialColorFilter', type=str)
    order_rid_filter = data.get('orderRidFilter', type=str)
    status_filter = [int(status) for status in data.getlist('statusFilter[]')]
    inbound_type_filter = [int(inbound_type) for inbound_type in data.getlist('inboundTypeFilter[]')]

    # ------- 1) 把公共 FROM/JOIN/WHERE 封装成一个“轻”查询（只到 IRD 为止）-------
    query = (
        db.session.query(InboundRecordDetail.id)
        .join(InboundRecord, InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id)
        .join(Supplier, InboundRecord.supplier_id == Supplier.supplier_id)
        .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
        .join(SPUMaterial, MaterialStorage.spu_material_id == SPUMaterial.spu_material_id)
        .join(Material, SPUMaterial.material_id == Material.material_id)
        .outerjoin(Order, InboundRecordDetail.order_id == Order.order_id)
        .filter(InboundRecord.display == 1)
    )
    if inbound_rid_filter:
        query = query.filter(InboundRecord.inbound_rid.ilike(f"%{inbound_rid_filter}%"))
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
    if material_name_filter:
        query = query.filter(Material.material_name.ilike(f"%{material_name_filter}%"))
    if material_model_filter:
        query = query.filter(SPUMaterial.material_model.ilike(f"%{material_model_filter}%"))
    if material_specification_filter:
        query = query.filter(SPUMaterial.material_specification.ilike(f"%{material_specification_filter}%"))
    if material_color_filter:
        query = query.filter(SPUMaterial.color.ilike(f"%{material_color_filter}%"))
    if order_rid_filter:
        query = query.filter(Order.order_rid.ilike(f"%{order_rid_filter}%"))
    if status_filter != []:
        query = query.filter(InboundRecord.approval_status.in_(status_filter))
    if inbound_type_filter != []:
        query = query.filter(InboundRecord.inbound_type.in_(inbound_type_filter))

    # ------- 2) 计数：只数去重的 IRD.id -------
    id_subq = (
        query.with_entities(InboundRecordDetail.id) # 只投影 id
            .distinct()
            .subquery()
    )
    total_count = db.session.query(func.count()).select_from(id_subq).scalar()
    # ------- 3) 分页：先取当前页的 id 列表 -------
    page_ids = (
        query
        .with_entities(InboundRecordDetail.id) # 只拿 id，轻量
        .order_by(InboundRecord.inbound_datetime.desc(), InboundRecordDetail.id.desc())
        .limit(page_size)
        .offset((page_num - 1) * page_size)
        .all()
    )
    page_ids = [x[0] for x in page_ids]
    if not page_ids:
        response_entities = []
    else:
        # ------- 4) 再用 id 列表拉全量需要的列（避免对大元组 distinct）-------
        query = (
            db.session.query(
                InboundRecord, InboundRecordDetail, Material, Supplier, SPUMaterial, Order.order_rid, MaterialStorage
            )
            .join(Supplier, InboundRecord.supplier_id == Supplier.supplier_id)
            .join(InboundRecordDetail, InboundRecord.inbound_record_id == InboundRecordDetail.inbound_record_id)
            .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
            .join(SPUMaterial, MaterialStorage.spu_material_id == SPUMaterial.spu_material_id)
            .join(Material, SPUMaterial.material_id == Material.material_id)
            .outerjoin(Order, InboundRecordDetail.order_id == Order.order_id)  # 仅在确实需要时保留外连接
            .filter(InboundRecordDetail.id.in_(page_ids))
            .order_by(InboundRecord.inbound_datetime.desc(), InboundRecordDetail.id.desc())
            # 这里通常不再需要 distinct()，因为已收敛到本页的 id 集合
        )
        response_entities = query.all()
    warehouse_id_mapping = {entity.material_warehouse_id: entity.material_warehouse_name for entity in db.session.query(MaterialWarehouse).all()}
    inbound_records = []
    for inbound_record, inbound_record_detail,material, supplier, spu, order_rid, material_storage in response_entities:
        res = db_obj_to_res(inbound_record, InboundRecord,attr_name_list=type_to_attr_mapping["InboundRecord"])
        res = db_obj_to_res(inbound_record_detail, InboundRecordDetail,attr_name_list=type_to_attr_mapping['InboundRecordDetail'],initial_res=res)
        res = db_obj_to_res(supplier, Supplier,attr_name_list=type_to_attr_mapping['Supplier'],initial_res=res)
        res = db_obj_to_res(spu, SPUMaterial, attr_name_list = type_to_attr_mapping['SPUMaterial'], initial_res=res)
        res = db_obj_to_res(material, Material, attr_name_list=type_to_attr_mapping['Material'], initial_res = res)
        res[to_camel('inbound_datetime')] = format_datetime(inbound_record.inbound_datetime)
        res[to_camel('approval_status')] = accounting_audit_status_converter(inbound_record.approval_status)
        res[to_camel('material_warehouse')] = warehouse_id_mapping[inbound_record.warehouse_id] if inbound_record.warehouse_id in warehouse_id_mapping.keys() else ''
        res[to_camel('order_rid')] = order_rid
        res[to_camel('actual_inbound_unit')] = material_storage.actual_inbound_unit
        res[to_camel('unit_price')] = normalize_decimal(res[to_camel('unit_price')])
        res[to_camel('inbound_amount')] = normalize_decimal(res[to_camel('inbound_amount')])
        res[to_camel('item_total_price')] = normalize_decimal(res[to_camel('item_total_price')])
        inbound_records.append(res)
    return inbound_records, total_count

def _get_warehouse_inbound_summary_query(data: dict):
    page_num = data.get('pageNumber',type=int)
    page_size = data.get('pageSize', type=int)
    warehouse_filter = data.get('selectedWarehouse')
    supplier_name_filter = data.get('supplierNameFilter', type=str)
    date_range_filter_start = data.get('dateRangeFilterStart', type=str)
    date_range_filter_end = data.get('dateRangeFilterEnd', type=str)
    material_name_filter = data.get('materialNameFilter', type=str)
    material_model_filter = data.get('materialModelFilter', type=str)
    material_specification_filter = data.get('materialSpecificationFilter', type=str)
    material_color_filter = data.get('materialColorFilter', type=str)
    order_rid_filter = data.get('orderRidFilter', type=str)
    order_by_filter = data.get('orderByFilter', type=str)
    inbound_type_filter = [int(inbound_type) for inbound_type in data.getlist('inboundTypeFilter[]')]
    # approval_status_filter = data.get('approvalStatusFilter', type=str)

    inbound_records = (db.session.query(InboundRecord.inbound_record_id).filter(InboundRecord.display == 1))
    if warehouse_filter:
        inbound_records = inbound_records.filter(InboundRecord.warehouse_id == warehouse_filter)
    if date_range_filter_start:
        inbound_records = inbound_records.filter(InboundRecord.inbound_datetime >= date_range_filter_start)
    if date_range_filter_end:
        ### next day
        input_date_time = datetime.strptime(date_range_filter_end, '%Y-%m-%d')
        next_day_delta = timedelta(days=1)
        query_compare_date = format_date((input_date_time + next_day_delta))
        inbound_records = inbound_records.filter(InboundRecord.inbound_datetime <= query_compare_date)
    if inbound_type_filter != []:
        inbound_records = inbound_records.filter(InboundRecord.inbound_type.in_(inbound_type_filter))

    inbound_records_result = [r.inbound_record_id for r in inbound_records.all()]
    query = (
        db.session.query(
            SPUMaterial.spu_material_id,
            SPUMaterial.material_id,
            SPUMaterial.material_model, 
            SPUMaterial.material_specification,
            SPUMaterial.color,
            SPUMaterial.spu_rid,
            InboundRecordDetail.unit_price, 
            Order.order_rid, 
            func.sum(InboundRecordDetail.inbound_amount).label("inbound_amount_sum"), 
            func.max(InboundRecordDetail.inbound_record_id).label("inbound_record_id")
        )
        .filter(InboundRecordDetail.inbound_record_id.in_(inbound_records_result))
        .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
        .join(SPUMaterial,MaterialStorage.spu_material_id == SPUMaterial.spu_material_id)
        .outerjoin(Order, InboundRecordDetail.order_id == Order.order_id)
        .group_by(SPUMaterial.spu_material_id, InboundRecordDetail.unit_price, Order.order_rid)
    )
    time_period_subquery = query.subquery()
    response_query = (db.session.query(time_period_subquery, Material, MaterialWarehouse.material_warehouse_name, Supplier)
                      .join(Material, time_period_subquery.c.material_id == Material.material_id)
                      .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
                      .join(MaterialWarehouse, MaterialType.warehouse_id == MaterialWarehouse.material_warehouse_id)
                      .join(InboundRecord, InboundRecord.inbound_record_id == time_period_subquery.c.inbound_record_id)
                      .join(Supplier, InboundRecord.supplier_id == Supplier.supplier_id)
                      )
    if supplier_name_filter:
        response_query  = response_query.filter(Supplier.supplier_name.ilike(f"%{supplier_name_filter}%"))
    if material_name_filter:
        response_query = response_query.filter(Material.material_name.ilike(f"%{material_name_filter}%"))
    if material_model_filter:
        response_query = response_query.filter(time_period_subquery.c.material_model.ilike(f"%{material_model_filter}%"))
    if material_specification_filter:
        response_query = response_query.filter(time_period_subquery.c.material_specification.ilike(f"%{material_specification_filter}%"))
    if material_color_filter:
        response_query = response_query.filter(time_period_subquery.c.color.ilike(f"%{material_color_filter}%"))
    if order_rid_filter:
        response_query = response_query.filter(time_period_subquery.c.order_rid.ilike(f"%{order_rid_filter}%"))
    total_count = response_query.distinct().count()
    response_entities = response_query.distinct().limit(page_size).offset((page_num - 1) * page_size).all()
    inbound_summary = []
    for spu_id, m_id, m_model,m_specification, color, spu_rid, unit_price, order_rid, inbound_amount_sum, inbound_record_id, material, warehouse_name, supplier in response_entities:
        res = db_obj_to_res(material, Material,attr_name_list=INBOUND_SUMMARY_MATERIAL_COLUMNS)
        res['supplierName'] = supplier.supplier_name
        res['unitPrice'] = normalize_decimal(unit_price)
        res['totalAmount'] = normalize_decimal(inbound_amount_sum)
        res['totalPrice'] = normalize_decimal(unit_price * inbound_amount_sum)
        res['materialModel'] = m_model
        res['materialSpecification'] = m_specification
        res['materialColor'] = color
        res['spuRid'] = spu_rid
        res['materialWarehouse'] = warehouse_name
        res['orderRid'] = order_rid
        inbound_summary.append(res)
    return inbound_summary, total_count

    
@accounting_warehouse_bp.route("/accounting/get_warehouse_inventory", methods=["GET"])
def get_warehouse_inventory():
    current_inventory, total_count = _get_warehouse_inventory_query(request.args)
    return jsonify({'currentInventory':current_inventory, "total":total_count}), 200


@accounting_warehouse_bp.route("/accounting/get_warehouse_inbound_record", methods=["GET"])
def get_warehouse_inbound_record():
    inbound_records, total_count = _get_warehouse_inbound_record_query(request.args)
    return jsonify({"inboundRecords":inbound_records, "total":total_count}), 200

@accounting_warehouse_bp.route("/accounting/get_warehouse_inbound_summary", methods=["GET"])
def get_warehouse_inbound_summary():
    inbound_summary, total_count = _get_warehouse_inbound_summary_query(request.args)
    return jsonify({"inboundSummary":inbound_summary, "total":total_count}), 200


@accounting_warehouse_bp.route("/accounting/get_inventory_display_columns", methods=["GET"])
def get_inventory_display_columns():
    res_data = []
    res_id = 0
    for attr in name_mapping_inventory.keys():
        res_data.append({"attrName":to_camel(attr),
                         "labelName":name_mapping_inventory[attr],
                         "id":res_id,})
        res_id += 1
    return jsonify({"selectableColumns":res_data}), 200
@accounting_warehouse_bp.route("/accounting/get_inbound_display_columns", methods=["GET"])
def get_inbound_display_columns():
    res_data = []
    res_id = 0
    for attr_name in name_en_cn_mapping_inbound.keys():
        res_data.append({"attrName":to_camel(attr_name),
                         "labelName":name_en_cn_mapping_inbound[attr_name],
                         "id":res_id,
                         "width":col_width_mapping[attr_name]
                         })
        res_id += 1
    return jsonify({"selectableColumns":res_data}), 200
@accounting_warehouse_bp.route("/accounting/get_inbound_summary_display_columns", methods=["GET"])
def get_inbound_summary_columns():
    res_data = []
    res_id = 0
    for attr_name in name_mapping_inbound_summary.keys():
        res_data.append({"attrName":to_camel(attr_name),
                         "labelName":name_mapping_inbound_summary[attr_name],
                         "id":res_id,
                         "width":"170px" if attr_name == "spu_Rid" else "120px"})
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
    inbound_records, total_count = _get_warehouse_inbound_record_query(request.args)
    # Generate the Excel file using the inbound_summary data
    template_path = FILE_STORAGE_PATH + "/财务入库总单模板.xlsx"
    timestamp = str(time.time())
    new_file_name = f"财务入库单总单输出_{timestamp}.xlsx"
    save_path = FILE_STORAGE_PATH + "/财务部文件/入库总单/" + new_file_name
    time_range_string = date_range_filter_start + "至" + date_range_filter_end if date_range_filter_start and date_range_filter_end else "全部"
    generate_accounting_inbound_excel(template_path, save_path, warehouse_filter, supplier_name_filter, material_model_filter,time_range_string ,inbound_records)
    return send_file(save_path, as_attachment=True, download_name=new_file_name)
    
@accounting_warehouse_bp.route("/accounting/createinboundsummaryexcelanddownload", methods=["GET"])
def create_inbound_summary_excel_and_download():
    warehouse_filter = request.args.get('selectedWarehouse')
    supplier_name_filter = request.args.get('supplierNameFilter', type=str)
    date_range_filter_start = request.args.get('dateRangeFilterStart', type=str)
    date_range_filter_end = request.args.get('dateRangeFilterEnd', type=str)
    material_model_filter = request.args.get('materialModelFilter', type=str)
    inbound_summary, total_count = _get_warehouse_inbound_summary_query(request.args)

    template_path = FILE_STORAGE_PATH + "/财务入库汇总单模板.xlsx"
    timestamp = str(time.time())
    new_file_name = f"财务入库单汇总输出_{timestamp}.xlsx"
    save_path = FILE_STORAGE_PATH + "/财务部文件/入库汇总单/" + new_file_name
    time_range_string = date_range_filter_start + "至" + date_range_filter_end if date_range_filter_start and date_range_filter_end else "全部"
    generate_accounting_summary_excel(template_path, save_path, warehouse_filter, supplier_name_filter, material_model_filter,time_range_string ,inbound_summary)
    return send_file(save_path, as_attachment=True, download_name=new_file_name)

@accounting_warehouse_bp.route("/accounting/createinventoryexcelanddownload", methods=["GET"])
def create_inventory_excel_and_download():
    warehouse_filter = request.args.get('selectedWarehouse')
    warehouse_name = None
    if warehouse_filter:
        warehouse_name = (
            db.session.query(MaterialWarehouse.material_warehouse_name)
            .filter(MaterialWarehouse.material_warehouse_id == warehouse_filter)
            .scalar()
        )
    supplier_name_filter = request.args.get('supplierNameFilter', type=str)
    material_model_filter = request.args.get('materialModelFilter', type=str)
    current_inventory, total_count = _get_warehouse_inventory_query(request.args, all_records=True)
    template_path = os.path.join(FILE_STORAGE_PATH, "财务库存汇总单模板.xlsx")
    timestamp = str(time.time())
    new_file_name = f"财务库存单汇总输出_{timestamp}.xlsx"
    target_folder = os.path.join(FILE_STORAGE_PATH, "财务部文件", "库存总单")
    os.makedirs(target_folder, exist_ok=True)
    save_path = os.path.join(target_folder, new_file_name)
    time_range_string = "全部"
    generate_accounting_warehouse_excel(template_path, save_path, warehouse_name, supplier_name_filter, material_model_filter,time_range_string ,current_inventory)
    return send_file(save_path, as_attachment=True, download_name=new_file_name)

@accounting_warehouse_bp.route("/accounting/getinboundrecordtype", methods=["GET"])
def get_inbound_record_type():
    return jsonify({"result":INBOUND_RECORD_TYPE_OPTIONS}), 200


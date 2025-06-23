# from models import *

# from event_processor import *
import random
import string
from decimal import Decimal
from datetime import datetime


# ### check if a shoe exists in DB
# def check_shoe_exists(shoe_rid):
#     existance = (
#         db.session.query(Shoe.shoe_rid).filter(Shoe.shoe_rid == shoe_rid).first()
#     )
#     result = existance != None
#     return result


# ### check if customer exists in DB by ID
# def check_customerId_exists(customer_id):
#     existance = (
#         db.session.query(Customer.customer_id)
#         .filter(Customer.customer_id == customer_id)
#         .first()
#     )
#     result = existance != None
#     return result


# ### get customer ID by name
# def get_customerId(customer_name):
#     query_entity = (
#         db.session.query(Customer.customer_name, Customer.customer_id)
#         .filter(Customer.customer_name == customer_name)
#         .first()
#     )
#     result = query_entity.customer_id
#     return result


# ### check if customer exists in DB by Name
# def check_customerName_exists(customer_name):
#     existance = (
#         db.session.query(Customer.customer_name)
#         .filter(Customer.customer_name == customer_name)
#         .first()
#     )
#     result = existance != None
#     return result


# def check_orderRid_exists(order_rid):
#     existance = (
#         db.session.query(Order.order_rid).filter(Order.order_rid == order_rid).first()
#     )
#     result = existance != None
#     return result


# ### create and insert new shoe entity
# def dbcreateShoe(shoe_rid, img_url):
#     db_entity = Shoe(shoe_rid=shoe_rid, shoe_image_url=img_url)
#     db.session.add(db_entity)
#     db.session.commit()
#     return True


# ###
# def dbcreateCustomer(customer_Name):
#     db_entity = Customer(customer_name=customer_Name)
#     db.session.add(db_entity)
#     db.session.commit()
#     return True


# def dbcreateOrder(order_Rid, order_createTime, order_Customer):
#     db_entity = Order(
#         order_rid=order_Rid,
#         order_createtime=order_createTime,
#         order_customer=order_Customer,
#     )
#     db.session.add(db_entity)
#     db.session.commit()
#     return True


# def processEvent(event):
#     return


def randomIdGenerater(digit):
    random_str = "".join(random.choices(string.digits, k=digit))
    return random_str


def format_date(date_obj):
    if not date_obj:
        return ""
    return date_obj.strftime("%Y-%m-%d")


def format_datetime(datetime_obj):
    if not datetime_obj:
        return ""
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")


def format_line_group(line_group_obj):
    if not line_group_obj:
        return []
    return line_group_obj.split(",")


def format_outbound_type(outbound_type):
    format_val = int(outbound_type)
    mapping = {0: "自产", 1: "废料", 2: "外包", 3: "复合", 4: "退回"}
    if format_val in [0, 1, 2, 3, 4]:
        return mapping[int(outbound_type)]


def status_converter(current_status_arr, current_status_value_arr):
    status = "未排期"
    if (
        17 in current_status_arr
        and current_status_value_arr[current_status_arr.index(17)] == 1
    ):
        status = "已保存排期"
    elif 17 in current_status_arr:
        status = "未排期"
    elif 18 in current_status_arr:
        status = "生产前确认"
    elif 23 in current_status_arr:
        status = "生产中"
    elif 42 in current_status_arr:
        status = "生产结束"
    return status


def estimate_status_converter(production_info):
    interval1 = [production_info.cutting_start_date, production_info.cutting_end_date]
    interval2 = [production_info.pre_sewing_start_date, production_info.pre_sewing_end_date]
    interval3 = [production_info.sewing_start_date, production_info.sewing_end_date]
    interval4 = [production_info.molding_start_date, production_info.molding_end_date]

    interval1 = [d if d is not None else datetime.max.date() for d in interval1]
    interval2 = [d if d is not None else datetime.max.date() for d in interval2]
    interval3 = [d if d is not None else datetime.max.date() for d in interval3]
    interval4 = [d if d is not None else datetime.max.date() for d in interval4]
    
    today = datetime.now().date()
    result = "未排期"
    if today < interval1[0]:
        result = "裁断未开始"
    elif interval1[0] <= today <= interval1[1]:
        result = "裁断进行中"
    elif interval1[1] < today < interval2[0]:
        result = "预备未开始"
    elif interval2[0] <= today <= interval2[1]:
        result = "预备进行中"
    elif interval2[1] < today < interval3[0]:
        result = "针车未开始"
    elif interval3[0] <= today <= interval3[1]:
        result = "针车进行中"
    elif interval3[1] < today < interval4[0]:
        result = "成型未开始"
    elif interval4[0] <= today <= interval4[1]:
        result = "成型进行中"
    elif interval4[1] < today:
        result = "生产已结束"
    return result

def scheduling_status_converter(production_info):
    cutting = [production_info.cutting_start_date, production_info.cutting_end_date]
    pre_sewing = [production_info.pre_sewing_start_date, production_info.pre_sewing_end_date]
    sewing = [production_info.sewing_start_date, production_info.sewing_end_date]
    molding = [production_info.molding_start_date, production_info.molding_end_date]

    if cutting == [None, None]:
        status = '裁断未排期'
    elif pre_sewing == [None, None]:
        status = '预备未排期'
    elif sewing == [None, None]:
        status = '针车未排期'
    elif molding == [None, None]:
        status = '成型未排期'
    else:
        status = '已排期'
    return status


def outsource_status_converter(status_val):
    if status_val == 0:
        status = "未提交"
    elif status_val == 1:
        status = "已提交"
    elif status_val == 2:
        status = "已审批"
    elif status_val == 3:
        status = "被驳回"
    elif status_val == 4:
        status = "材料出库"
    elif status_val == 5:
        status = "外包生产中"
    elif status_val == 6:
        status = "成品入库"
    else:
        status = "外包结束"
    return status


def outsource_status_strtoint(status_str):
    if status_str == "未提交":
        status = 0
    elif status_str == "已提交":
        status = 1
    elif status_str == "已审批":
        status = 2
    elif status_str == "被驳回":
        status = 3
    elif status_str == "材料出库":
        status = 4
    elif status_str == "外包生产中":
        status = 5
    elif status_str == "成品入库":
        status = 6
    else:
        status = 7
    return status


def accounting_audit_status_converter(status_val):
    result = ""
    if status_val == 0:
        result = "待审核"
    elif status_val == 1:
        result = "已审核"
    elif status_val == 2:
        result = "已驳回"
    return result


def to_snake(request_attr_name):
    return "".join(
        ["_" + c.lower() if c.isupper() else c for c in request_attr_name]
    ).lstrip("_")


def to_camel(db_attr_name):
    split_list = db_attr_name.split("_")
    result = "".join(
        [split_list[0]] + [db_attr.capitalize() for db_attr in split_list[1:]]
    )
    return result


def db_obj_to_res(
    db_entity, db_model, attr_name_offset=0, attr_name_list=[], initial_res=None
):
    if initial_res:
        res = initial_res
    else:
        res = {}
    if attr_name_list == []:
        attr_name_list = db_model.__table__.columns.keys()
    else:
        if not set(db_model.__table__.columns.keys()).issuperset(set(attr_name_list)):
            for attr in attr_name_list:
                if attr not in db_model.__table__.columns.keys():
                    print(attr)
            # print(db_model)
            # print("ERROR attr name wrong")
            return res
    if attr_name_offset == 0:
        for attr in attr_name_list:
            res[to_camel(attr)] = getattr(db_entity, attr)
    else:
        for attr in attr_name_list:
            res[to_camel(attr[attr_name_offset:])] = getattr(db_entity, attr)

    return res

def normalize_decimal(value):
    d = Decimal(value).normalize()
    # Convert to string without scientific notation
    return format(d, 'f').rstrip('0').rstrip('.') if '.' in format(d, 'f') else format(d, 'f')
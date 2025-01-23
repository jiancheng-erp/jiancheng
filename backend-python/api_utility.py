from models import *

from event_processor import *
import random
import string


### check if a shoe exists in DB
def check_shoe_exists(shoe_rid):
    existance = (
        db.session.query(Shoe.shoe_rid).filter(Shoe.shoe_rid == shoe_rid).first()
    )
    result = existance != None
    return result


### check if customer exists in DB by ID
def check_customerId_exists(customer_id):
    existance = (
        db.session.query(Customer.customer_id)
        .filter(Customer.customer_id == customer_id)
        .first()
    )
    result = existance != None
    return result


### get customer ID by name
def get_customerId(customer_name):
    query_entity = (
        db.session.query(Customer.customer_name, Customer.customer_id)
        .filter(Customer.customer_name == customer_name)
        .first()
    )
    result = query_entity.customer_id
    return result


### check if customer exists in DB by Name
def check_customerName_exists(customer_name):
    existance = (
        db.session.query(Customer.customer_name)
        .filter(Customer.customer_name == customer_name)
        .first()
    )
    result = existance != None
    return result


def check_orderRid_exists(order_rid):
    existance = (
        db.session.query(Order.order_rid).filter(Order.order_rid == order_rid).first()
    )
    result = existance != None
    return result


### create and insert new shoe entity
def dbcreateShoe(shoe_rid, img_url):
    db_entity = Shoe(shoe_rid=shoe_rid, shoe_image_url=img_url)
    db.session.add(db_entity)
    db.session.commit()
    return True


###
def dbcreateCustomer(customer_Name):
    db_entity = Customer(customer_name=customer_Name)
    db.session.add(db_entity)
    db.session.commit()
    return True


def dbcreateOrder(order_Rid, order_createTime, order_Customer):
    db_entity = Order(
        order_rid=order_Rid,
        order_createtime=order_createTime,
        order_customer=order_Customer,
    )
    db.session.add(db_entity)
    db.session.commit()
    return True


def processEvent(event):
    return


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


def status_converter(current_status_arr, current_status_value_arr):
    status = "未排期"
    if 17 in current_status_arr and current_status_value_arr[current_status_arr.index(17)] == 1:
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


def to_snake(request_attr_name):
    return ''.join(['_'+c.lower() if c.isupper() else c for c in request_attr_name]).lstrip('_')

def to_camel(db_attr_name):
    split_list = db_attr_name.split("_")
    result = "".join(
        [split_list[0]] + [db_attr.capitalize() for db_attr in split_list[1:]]
    )
    return result

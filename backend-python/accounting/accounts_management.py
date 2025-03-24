from flask import Blueprint, jsonify, request
from models import *
from api_utility import to_camel, to_snake

import time
from app_config import app, db
from sqlalchemy import func
from constants import PAYABLE_EVENT_TO_TEXT, PAYABLE_EVENT_INBOUND,PAYABLE_EVENT_COMPOSITE_INBOUND,PAYABLE_EVENT_MISC_INBOUND,ACCOUNT_TYPE_CASH,ACCOUNT_TYPE_PAYABLE,ACCOUNT_TYPE_RECIEVABLE
 

accounts_management_bp = Blueprint("accounts_management", __name__)

# attribute name as follows
# first/second/third + Grade + databse column names in camel
# ex. firstGradeAccountName, firstGradeAccountId, secondGradeAccountBalance, thirdGradeAccountBelongsSg
# fg, sg tg = firstGrade, secondGrade, thirdGrade
# curd on differnt grades of accounts

first_grade_attr_list = FirstGradeAccount.__table__.columns.keys()
second_grade_attr_list = SecondGradeAccount.__table__.columns.keys()
third_grade_attr_list = ThirdGradeAccount.__table__.columns.keys()
third_grade_record_attr_list = AccountingThirdGradeRecord.__table__.columns.keys()
first_grade_prefix = "first_grade_"
second_grade_prefix = "second_grade_"
third_grade_prefix = "third_grade_"


## ADD accounts
@accounts_management_bp.route("/accountsmanagement/firstgrade/addaccount", methods=["POST"])
def add_first_grade_account():
    account_name = request.json.get("firstGradeAccountName")
    print("account name is " + str(account_name))
    if not account_name:
        return jsonify({"msg":"account name cannot be empty"}), 400
    existing_entity = db.session.query(FirstGradeAccount).filter_by(account_name = account_name).first()
    if existing_entity:
        return jsonify({"msg":"first grade account name duplicates"}), 400
    else:
        db_entity = FirstGradeAccount()
        db_entity.account_name = account_name
        db.session.add(db_entity)
        db.session.commit()
        return jsonify({"msg":"entity added to db"}), 200
    

## second grade accounts belongs to first grade account
@accounts_management_bp.route("/accountsmanagement/secondgrade/addaccount", methods=["POST"])
def add_second_grade_account():
    print(request.json)
    account_name = request.json.get("secondGradeAccountName")
    account_belongs_to = request.json.get("firstGradeAccountBelonged")
    if not account_name:
        return jsonify({"msg":"account name cannot be empty"}), 400
    if not account_belongs_to:
        return jsonify({"msg":"secondary account must be associated with a first grade account"}), 400
    existing_entity = db.session.query(SecondGradeAccount).filter_by(account_name = account_name).all()
    existing_parent = db.session.query(FirstGradeAccount).filter_by(account_id = account_belongs_to).first()
    if not existing_parent:
        return jsonify({"msg":"associated first grade account doesnt exist"}), 400
    else:
        if existing_entity:
            for entity in existing_entity:
                if entity.account_belongs_fg == existing_parent.account_id:
                    return jsonify({"msg":"associated account with this name already exists"}), 400
        new_entity = SecondGradeAccount()
        new_entity.account_name =  account_name
        new_entity.account_belongs_fg = account_belongs_to
        db.session.add(new_entity)
        db.session.commit()
        return jsonify({"msg":"new account added to db"}), 200

## third grade accounts belongs to second grade
@accounts_management_bp.route("/accountsmanagement/thirdgrade/addaccount", methods=["POST"])
def add_third_grade_account():
    # new account name
    account_name = request.json.get("thirdGradeAccountName")
    # account id of the second grade account it belongs to
    account_belongs_to = request.json.get("secondGradeAccountBelonged")
    account_type = request.json.get("thirdGradeAccountType")
    if not account_name:
        return jsonify({"msg":"account name cannot be empty"}), 400
    if not account_belongs_to:
        return jsonify({"msg":"third grade account must be associated with a second grade account"}), 400
    existing_entity = db.session.query(ThirdGradeAccount).filter_by(account_name = account_name).all()
    existing_parent = db.session.query(SecondGradeAccount).filter_by(account_id = account_belongs_to).first()
    if not existing_parent:
        return jsonify({"msg":"associated second grade account doesnt exist"}), 400
    else:
        if existing_entity:
            for entity in existing_entity:
                if entity.account_belongs_sg == existing_parent.account_id:
                    return jsonify({"msg":"associated account with this name already exists"}), 400
        new_entity = ThirdGradeAccount()
        new_entity.account_name =  account_name
        new_entity.account_belongs_sg = account_belongs_to
        new_entity.account_type = account_type
        db.session.add(new_entity)
        db.session.commit()
        return jsonify({"msg":"new account added to db"}), 200

@accounts_management_bp.route("/accountsmanagement/thirdgrade/boundpayableaccount", methods=["POST"])
def bound_payable_event():
    third_grade_account_id = request.json.get("boundThirdGradeAccountId")
    payable_event_type_enum = request.json.get("boundPayableEventTypeEnum")
    # verify if account is payable account
    print("account id is " + str(third_grade_account_id))
    print("event enum is " + payable_event_type_enum)
    account_entity = db.session.query(ThirdGradeAccount).filter_by(account_id = third_grade_account_id).first()
    if account_entity.account_type == ACCOUNT_TYPE_PAYABLE:
        if payable_event_type_enum in PAYABLE_EVENT_TO_TEXT.keys():
            account_entity.account_bound_event = payable_event_type_enum
            db.session.commit()
        else:
            result = {"msg":"not a payable event"}
            return jsonify(result), 401
    else:
        result = {"msg":"not a payable account"}
        return jsonify(result), 401
    return jsonify({"msg":"bound complete"}), 200



## GET accounts
@accounts_management_bp.route("/accountsmanagement/firstgrade/getaccounts", methods=["GET"])
def get_first_grade_account():
    db_entities = db.session.query(FirstGradeAccount).all()
    response_accounts_list = []
    for entity in db_entities:
        response_entity = {}
        for attr_name in first_grade_attr_list:
            response_entity[to_camel(first_grade_prefix + attr_name)] = getattr(entity, attr_name, None)
        response_accounts_list.append(response_entity)
    
    return jsonify({"firstGradeAccountList":response_accounts_list}), 200

@accounts_management_bp.route("/accountsmanagement/secondgrade/getaccounts", methods=["GET"])
def get_second_grade_account():
    db_entities = db.session.query(SecondGradeAccount).all()
    response_accounts_list = []
    for entity in db_entities:
        response_entity = {}
        for attr_name in second_grade_attr_list:
            response_entity[to_camel(second_grade_prefix + attr_name)] = getattr(entity, attr_name, None)
        response_accounts_list.append(response_entity)
    return jsonify({"secondGradeAccountList":response_accounts_list}), 200


@accounts_management_bp.route("/accountsmanagement/thirdgrade/getaccounts", methods=["GET"])
def get_third_grade_account():
    db_entities = db.session.query(ThirdGradeAccount).all()
    response_accounts_list = []
    for entity in db_entities:
        response_entity = {}
        for attr_name in third_grade_attr_list:
            response_entity[to_camel(third_grade_prefix + attr_name)] = getattr(entity, attr_name, None)
        response_accounts_list.append(response_entity)
    return jsonify({"thirdGradeAccountList":response_accounts_list}), 200

# @accounts_management_bp.route("/accountsmanagement/thirdgrade/getboundable", methods=["GET"])
# def get_boundable_third_grade_account():
#     db_entities = db.session.query(ThirdGrade)
#     return

@accounts_management_bp.route("/accountsmanagement/thirdgrade/getboundinfo", methods=["GET"])
def get_bound_info_accounts():
    # 0 recievable 1 payable
    result = dict()
    result['payableBoundInfo'] = []
    result['recievableBoundInfo'] = []
    print(result.keys())
    payable_entities = db.session.query(ThirdGradeAccount).filter_by(account_type = 1).all()
    recievable_entities = db.session.query(ThirdGradeAccount).filter_by(account_type = 0).all()
    for entity in payable_entities:
        entity_res = dict()
        entity_res['accountName'] = entity.account_name
        entity_res['accountType'] = entity.account_type
        if entity.account_bound_event and entity.account_bound_event in PAYABLE_EVENT_TO_TEXT.keys():
            entity_res['accountBoundEvent'] = PAYABLE_EVENT_TO_TEXT[entity.account_bound_event]
        else:
            entity_res['accountBoundEvent'] = "尚未绑定应付事件"
        result['payableBoundInfo'].append(entity_res)

    for entity in recievable_entities:
        entity_res = dict()
        entity_res['accountName'] = entity.account_name
        entity_res['accountType'] = entity.account_type
        entity_res['accountBoundEvent'] = entity.account_bound_event
        result['recievableBoundInfo'].append(entity_res)
    
    return jsonify(result), 200

@accounts_management_bp.route("/accountsmanagement/getallaccounts", methods=["GET"])
def get_all_accounts():
    
    response_list = []
    fg_accounts = db.session.query(FirstGradeAccount).all()
    sg_accounts = db.session.query(SecondGradeAccount).all()
    tg_accounts = db.session.query(ThirdGradeAccount).all()
    sec_acc_to_res = {}

    for sec_acc in sg_accounts:
        sec_response_entity = {}
        for attr_name in second_grade_attr_list:
            sec_response_entity[to_camel(second_grade_prefix + attr_name)] = getattr(sec_acc, attr_name, None)
        sec_response_entity['associatedThirdGradeAccount'] = []
        sec_acc_to_res[sec_acc.account_id] = sec_response_entity
    for thr_acc in tg_accounts:
        thr_response_entity = {}
        for attr_name in third_grade_attr_list:
            thr_response_entity[to_camel(third_grade_prefix + attr_name)] = getattr(thr_acc, attr_name, None)
        thr_belongs_to = thr_acc.account_belongs_sg
        if thr_belongs_to != None:
            sec_acc_to_res[thr_belongs_to]["associatedThirdGradeAccount"].append(thr_response_entity)

    fir_acc_to_res = {}
    for fir_acc in fg_accounts:
        response_entity = {}
        for attr_name in first_grade_attr_list:
            response_entity[to_camel(first_grade_prefix + attr_name)] = getattr(fir_acc, attr_name, None) 
        response_entity["associatedSecondGradeAccount"] = []
        fir_acc_to_res[fir_acc.account_id] = response_entity
    
    for sec_entity in sec_acc_to_res.values():
        sec_belongs_to = sec_entity["secondGradeAccountBelongsFg"]
        if sec_belongs_to != None:
            fir_acc_to_res[sec_belongs_to]["associatedSecondGradeAccount"].append(sec_entity)
    print(fir_acc_to_res)
    return jsonify({"firstGradeAccountsMapping": fir_acc_to_res}), 200
## Update accounts

@accounts_management_bp.route("/accountsmanagement/firstgrade/updateaccountname", methods=["POST"])
def update_first_grade_account_name():
    account_id = request.args.get("accountId")
    old_account_name = request.args.get("accountNameOld")
    new_account_name = request.args.get("accountNameNew")
    old_existing = db.session.query(FirstGradeAccount).filter_by(account_name = old_account_name).first() or db.sesison.query(FirstGradeAccount).filter_by(account_id = account_id).first()
    new_existing = db.session.query(FirstGradeAccount).filter_by(account_name = new_account_name).first()
    if not old_existing:
        return jsonify({"msg":"account with name or id not found"})
    if new_existing:
        return jsonify({"msg":"account with name already exists"})
    old_existing.account_name = new_account_name
    db.session.commit()
    return jsonify({"msg":"account name changed"}), 200


@accounts_management_bp.route("/accountsmanagement/secondgrade/updateaccountname", methods=["POST"])
def update_second_grade_account_name():
    account_id = request.args.get("accountId")
    old_account_name = request.args.get("accountNameOld")
    new_account_name = request.args.get("accountNameNew")
    old_existing = db.session.query(SecondGradeAccount).filter_by(account_name = old_account_name).first() or db.sesison.query(SecondGradeAccount).filter_by(account_id = account_id).first()
    new_existing = db.session.query(SecondGradeAccount).filter_by(account_name = new_account_name).first()
    if not old_existing:
        return jsonify({"msg":"account with name or id not found"})
    if new_existing:
        return jsonify({"msg":"account with name already exists"})
    old_existing.account_name = new_account_name
    db.session.commit()
    return jsonify({"msg":"account name changed"}), 200


@accounts_management_bp.route("/accountsmanagement/thirdgrade/updateaccountname", methods=["POST"])
def update_third_grade_account_name():
    account_id = request.args.get("accountId")
    old_account_name = request.args.get("accountNameOld")
    new_account_name = request.args.get("accountNameNew")
    old_existing = db.session.query(ThirdGradeAccount).filter_by(account_name = old_account_name).first() or db.sesison.query(ThirdGradeAccount).filter_by(account_id = account_id).first()
    new_existing = db.session.query(ThirdGradeAccount).filter_by(account_name = new_account_name).first()
    if not old_existing:
        return jsonify({"msg":"account with name or id not found"})
    if new_existing:
        return jsonify({"msg":"account with name already exists"})
    old_existing.account_name = new_account_name
    db.session.commit()
    return jsonify({"msg":"account name changed"}), 200


@accounts_management_bp.route("/accountsmanagement/thirdgrade/addrecord", methods=["POST"])
def add_third_grade_account_record():
    # account_id = request.args.get("recordAccountId")
    # record_name = request.args.get("recordName")
    # record_object_id = request.args.get("recordObjectId")
    # record_type = request.args.get("recordType")
    # record_amount = request.args.get("recordAmount")
    # record_creation_date = request.args.get("recordCreationDate")
    # record_processed_date = request.args.get("recordProcessedDate")
    # record_amount_unit_id = request.args.get("recordAmountUnitId")
    # record_amount_unit_conversion_id = request.args.get("recordAmountUnitConversionId")
    # record_is_processed = request.args.get("recordIsProcessed")
    new_entity = AccountingThirdGradeRecord()
    for attr_name in third_grade_record_attr_list:
        setattr(new_entity, attr_name, getattr(request.json, attr_name))
    db.session.add(new_entity)
    db.session.commit()


### sums up all the secondary and third layer accounts balance belonging to this account
def compute_balance(account_grade, account_id):
    return

def add_record(account_grade, account_id, record_name, flow_direction, amount, unit_id):
    return


@accounts_management_bp.route("/accountsmanagement/performancetesting",methods=["GET"])
def performance_testing():
    customers = db.session.query(Customer).all()
    for customer in customers:
        new_recievable_entity = AccountingPayeePayer()
        new_recievable_entity.payee_name = customer.customer_name + "号客人" + "商标" + customer.customer_brand
        new_recievable_entity.entity_type = '1'
        db.session.add(new_recievable_entity)
        db.session.flush()
        new_recievable_account = AccountingRecievableAccount()
        new_recievable_account.account_owner_id = new_recievable_entity.payee_id
        new_recievable_account.account_recievable_balance = 0.00
        new_recievable_account.account_unit_id = 1
        db.session.add(new_recievable_account)
    db.session.commit()
    return jsonify({'res':200})


# only deletes when no second/third account associated with the account
@accounts_management_bp.route("/accountsmanagement/firstgrade/deleteaccount", methods=["DELETE"])
def delete_first_grade_account():
    return



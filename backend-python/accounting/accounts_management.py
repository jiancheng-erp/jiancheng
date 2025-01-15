from flask import Blueprint, jsonify, request
from models import *
from api_utility import to_camel, to_snake


from app_config import app, db

accounts_management_bp = Blueprint("accounts_management", __name__)

# attribute name as follows
# first/second/third + Grade + databse column names in camel
# ex. firstGradeAccountName, firstGradeAccountId, secondGradeAccountBalance, thirdGradeAccountBelongsSg
# fg, sg tg = firstGrade, secondGrade, thirdGrade
# curd on differnt grades of accounts

first_grade_attr_list = FirstGradeAccounts.__table__.columns.keys()
second_grade_attr_list = SecondGradeAccounts.__table__.columns.keys()
third_grade_attr_list = ThirdGradeAccounts.__table__.columns.keys()
first_grade_prefix = "first_grade_"
second_grade_prefix = "second_grade_"
third_grade_prefix = "third_grade_"

## ADD accounts
@accounts_management_bp.route("/accountsmanagement/firstgrade/addaccount", methods=["POST"])
def add_first_grade_account():
    account_name = request.json.get("first_grade_account_name")
    if not account_name:
        return jsonify({"msg":"account name cannot be empty"}), 400
    existing_entity = db.session.query(FirstGradeAccounts).filter_by(account_name = account_name).first()
    if existing_entity:
        return jsonify({"msg":"first grade account name duplicates"}), 400
    else:
        db_entity = FirstGradeAccounts()
        db_entity.account_name = account_name
        db.session.add(db_entity)
        db.session.commit()
        return jsonify({"msg":"entity added to db"}), 200
    

## second grade accounts belongs to first grade account
@accounts_management_bp.route("/accountsmanagement/secondgrade/addaccount", methods=["POST"])
def add_second_grade_account():
    account_name = request.json.get("second_grade_account_name")
    account_belongs_to = request.json.get("account_belongs_fg")
    if not account_name:
        return jsonify({"msg":"account name cannot be empty"}), 400
    if not account_belongs_to:
        return jsonify({"msg":"secondary account must be associated with a first grade account"}), 400
    existing_entity = db.session.query(SecondGradeAccounts).filter_by(account_name = account_name).all()
    existing_parent = db.session.query(FirstGradeAccounts).filter_by(account_id = account_belongs_to).first()
    if not existing_parent:
        return jsonify({"msg":"associated first grade account doesnt exist"}), 400
    else:
        if existing_entity:
            for entity in existing_entity:
                if entity.account_belongs_fg == existing_parent.account_id:
                    return jsonify({"msg":"associated account with this name already exists"}), 400
        new_entity = SecondGradeAccounts()
        new_entity.account_name =  account_name
        new_entity.account_belongs_fg = account_belongs_to
        db.session.add(new_entity)
        db.session.commit()
        return jsonify({"msg":"new account added to db"}), 200

## third grade accounts belongs to second grade
@accounts_management_bp.route("/accountsmanagement/thirdgrade/addaccount", methods=["POST"])
def add_third_grade_account():
    # new account name
    account_name = request.json.get("third_grade_account_name")
    # account id of the second grade account it belongs to
    account_belongs_to = request.json.get("account_belongs_sg")
    if not account_name:
        return jsonify({"msg":"account name cannot be empty"}), 400
    if not account_belongs_to:
        return jsonify({"msg":"third grade account must be associated with a first grade account"}), 400
    existing_entity = db.session.query(ThirdGradeAccounts).filter_by(account_name = account_name).all()
    existing_parent = db.session.query(SecondGradeAccounts).filter_by(account_id = account_belongs_to).first()
    if not existing_parent:
        return jsonify({"msg":"associated second grade account doesnt exist"}), 400
    else:
        if existing_entity:
            for entity in existing_entity:
                if entity.account_belongs_sg == existing_parent.account_id:
                    return jsonify({"msg":"associated account with this name already exists"}), 400
        new_entity = ThirdGradeAccounts()
        new_entity.account_name =  account_name
        new_entity.account_belongs_sg = account_belongs_to
        db.session.add(new_entity)
        db.session.commit()
        return jsonify({"msg":"new account added to db"}), 200


## GET accounts
@accounts_management_bp.route("/accountsmanagement/firstgrade/getaccounts", methods=["GET"])
def get_first_grade_account():
    db_entities = db.session.query(FirstGradeAccounts).all()
    response_accounts_list = []
    for entity in db_entities:
        response_entity = {}
        for attr_name in first_grade_attr_list:
            response_entity[to_camel(first_grade_prefix + attr_name)] = getattr(entity, attr_name, None)
        response_accounts_list.append(response_entity)
    
    return jsonify({"firstGradeAccountList":response_accounts_list}), 200

@accounts_management_bp.route("/accountsmanagement/secondgrade/getaccounts", methods=["GET"])
def get_second_grade_account():
    db_entities = db.session.query(SecondGradeAccounts).all()
    response_accounts_list = []
    for entity in db_entities:
        response_entity = {}
        for attr_name in second_grade_attr_list:
            response_entity[to_camel(second_grade_prefix + attr_name)] = getattr(entity, attr_name, None)
        response_accounts_list.append(response_entity)
    return jsonify({"secondGradeAccountList":response_accounts_list}), 200


@accounts_management_bp.route("/accountsmanagement/thirdgrade/getaccounts", methods=["GET"])
def get_third_grade_account():
    db_entities = db.session.query(ThirdGradeAccounts).all()
    response_accounts_list = []
    for entity in db_entities:
        response_entity = {}
        for attr_name in third_grade_attr_list:
            response_entity[to_camel(third_grade_prefix + attr_name)] = getattr(entity, attr_name, None)
        response_accounts_list.append(response_entity)
    return jsonify({"thirdGradeAccountList":response_accounts_list}), 200



@accounts_management_bp.route("/accountsmanagement/getallaccounts", methods=["GET"])
def get_all_accounts():
    response_list = []
    fg_accounts = db.session.query(FirstGradeAccounts).all()
    sg_accounts = db.session.query(SecondGradeAccounts).all()
    sec_acc_entities = []
    for sec_acc in sg_accounts:
        sec_response_entity = {}
        for attr_name in second_grade_attr_list:
            sec_response_entity[to_camel(second_grade_prefix + attr_name)] = getattr(sec_acc, attr_name, None)
        response_associated_accounts = []
        associated_tg_accounts = db.session.query(ThirdGradeAccounts).filter_by(account_belongs_sg = sec_acc.account_id).all()
        print(associated_tg_accounts)
        for third_acc in associated_tg_accounts:
            third_response_entity = {}
            for attr_name in third_grade_attr_list:
                third_response_entity[to_camel(third_grade_prefix + attr_name)] = getattr(third_acc, attr_name, None)
            response_associated_accounts.append(third_response_entity)
        
        sec_response_entity["associatedThirdGradeAccounts"] = response_associated_accounts
        sec_acc_entities.append(sec_response_entity)
    
    fir_acc_to_res = {}
    for fir_acc in fg_accounts:
        response_entity = {}
        for attr_name in first_grade_attr_list:
            response_entity[to_camel(first_grade_prefix + attr_name)] = getattr(fir_acc, attr_name, None)
        response_entity["associatedSecondGradeAccounts"] = []
        fir_acc_to_res[fir_acc.account_id] = response_entity
    
    for sec_entity in sec_acc_entities:
        sec_belongs_to = sec_entity["secondGradeAccountBelongsFg"]
        if sec_belongs_to != None:
            fir_acc_to_res[sec_belongs_to]["associatedSecondGradeAccounts"].append(sec_entity)
    
    return jsonify({"firstGradeAccountsMapping": fir_acc_to_res}), 200
## Update accounts

@accounts_management_bp.route("/accountsmanagement/firstgrade/updateaccountname", methods=["POST"])
def update_first_grade_account_name():
    account_id = request.args.get("accountId")
    old_account_name = request.args.get("accountNameOld")
    new_account_name = request.args.get("accountNameNew")
    old_existing = db.session.query(FirstGradeAccounts).filter_by(account_name = old_account_name).first() or db.sesison.query(FirstGradeAccounts).filter_by(account_id = account_id).first()
    new_existing = db.session.query(FirstGradeAccounts).filter_by(account_name = new_account_name).first()
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
    old_existing = db.session.query(SecondGradeAccounts).filter_by(account_name = old_account_name).first() or db.sesison.query(SecondGradeAccounts).filter_by(account_id = account_id).first()
    new_existing = db.session.query(SecondGradeAccounts).filter_by(account_name = new_account_name).first()
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
    old_existing = db.session.query(ThirdGradeAccounts).filter_by(account_name = old_account_name).first() or db.sesison.query(ThirdGradeAccounts).filter_by(account_id = account_id).first()
    new_existing = db.session.query(ThirdGradeAccounts).filter_by(account_name = new_account_name).first()
    if not old_existing:
        return jsonify({"msg":"account with name or id not found"})
    if new_existing:
        return jsonify({"msg":"account with name already exists"})
    old_existing.account_name = new_account_name
    db.session.commit()
    return jsonify({"msg":"account name changed"}), 200

### sums up all the secondary and third layer accounts balance belonging to this account
def compute_balance(account_grade, account_id):
    return


@accounts_management_bp.route("/accountsmanagement/performancetesting",methods=["GET"])
def performance_testing():
    return 

# only deletes when no second/third account associated with the account
@accounts_management_bp.route("/accountsmanagement/firstgrade/deleteaccount", methods=["DELETE"])
def delete_first_grade_account():
    return



from flask import Blueprint, jsonify, request
from decimal import Decimal
from models import *
from api_utility import to_camel, to_snake, format_datetime
from constants import DEFAULT_PAYABLE_TRANSACTION_ACCOUNT_GRADE, DEFAULT_TRANSACTION_UNIT
import time
from app_config import db
from sqlalchemy import func

payable_management_bp = Blueprint("payable_management", __name__)
ACCOUNT_ATTR_LIST = AccountingPayableAccount.__table__.columns.keys()
PAYEE_ATTR_LIST = AccountingPayeePayer.__table__.columns.keys()
TRANSACTION_ATTR_LIST = AccountingForeignAccountEvent.__table__.columns.keys()

PAYABLE_INCREASE = 1
RECIEVABLE_INCREASE = 0

@payable_management_bp.route('/payable_management/get_payable_accounts', methods=["GET"])
def get_payable_accounts():

    return
@payable_management_bp.route('/payable_management/edit_account/', methods=["POST"])
def edit_account():

    return
@payable_management_bp.route('/payable_management/add_account', methods=['POST'])
def add_account():

    return
@payable_management_bp.route('/payable_management/remove_account', methods=['POST'])
def delete_account():

    return
@payable_management_bp.route('/payable_management/add_transactions', methods=['POST'])
def add_transactions():
    pending_transactions = request.json.get('data')
    new_transaction_entity_list = []
    for transaction in pending_transactions:
        from_account_id = transaction['fromAccountName']
        to_account_id = transaction['toAccountName']
        transaction_amount = transaction['transactionAmount']
        transaction_date = transaction['transactionDate']
        new_transaction_entity = AccountingPayableTransaction()
        new_transaction_entity.from_account_grade = DEFAULT_PAYABLE_TRANSACTION_ACCOUNT_GRADE
        new_transaction_entity.from_account_id = from_account_id
        new_transaction_entity.to_account_id = to_account_id
        new_transaction_entity.transaction_amount = transaction_amount
        new_transaction_entity.transaction_unit = DEFAULT_TRANSACTION_UNIT
        new_transaction_entity.transaction_date = transaction_date
        new_transaction_entity_list.append(new_transaction_entity)
        payable_entity = db.session.query(AccountingPayableAccount).filter_by(account_id = to_account_id).first()
        payable_entity.account_payable_balance = payable_entity.account_payable_balance - Decimal(transaction_amount)
    print(new_transaction_entity_list)
    for transaction in new_transaction_entity_list:
        db.session.add(transaction)
    # db.session.add_all(new_transaction_entity_list)
    db.session.commit()    
    return {"msg":"all transactions added"}, 200
@payable_management_bp.route('/payable_management/get_payable_info', methods=['GET'])
def get_payable_info():
    payable_object_accounts = (db.session.query(AccountingPayableAccount, AccountingPayeePayer)
                               .join(AccountingPayeePayer, AccountingPayableAccount.account_owner_id == AccountingPayeePayer.payee_id)
                               .all())
    payable_transactions_entities = (db.session.query(AccountingForeignAccountEvent,InboundRecord,InboundRecordDetail
                                                      ,MaterialStorage, Material, MaterialType
                                                      ).filter_by(transaction_type = PAYABLE_INCREASE)
                                     .join(InboundRecord, InboundRecord.inbound_record_id == AccountingForeignAccountEvent.inbound_record_id)
                                     .join(InboundRecordDetail, InboundRecordDetail.inbound_record_id == InboundRecord.inbound_record_id)
                                     .join(MaterialStorage, InboundRecordDetail.material_storage_id == MaterialStorage.material_storage_id)
                                     .join(Material, MaterialStorage.actual_inbound_material_id == Material.material_id)
                                     .join(MaterialType, Material.material_type_id == MaterialType.material_type_id)
                                     .all())
    print(payable_transactions_entities)
    account_owner_id_to_account_res = {}
    for account, payee in payable_object_accounts:
        account_res_data = {}
        for attr in ACCOUNT_ATTR_LIST:
            account_res_data[to_camel(attr)] = getattr(account, attr)
        for attr in PAYEE_ATTR_LIST:
            account_res_data[to_camel(attr.replace("payee", "account_owner"))] = getattr(payee, attr)
        transaction_details = []
        account_res_data["transactionDetails"] = transaction_details
        print(account_res_data)
        account_owner_id_to_account_res[account.account_owner_id] = account_res_data
    for transaction , inbound_record, inbound_record_detail, material_storage, material, material_type in payable_transactions_entities:
        cur_transaction_res = {}
        cur_transaction_res["inboundTime"] = format_datetime(inbound_record.inbound_datetime)
        cur_transaction_res["transactionAmount"] = round(inbound_record_detail.inbound_amount*inbound_record_detail.unit_price,3)
        cur_transaction_res["materialType"] = material_type.material_type_name
        cur_transaction_res["materialName"] = material.material_name
        cur_transaction_res["materialModel"] = material_storage.material_model
        cur_transaction_res["materialSpecifiction"] = material_storage.material_specification
        cur_transaction_res["materialUnit"] = material_storage.actual_inbound_unit
        cur_transaction_res["materialAmount"] = float(inbound_record_detail.inbound_amount)
        cur_transaction_res["materialUnitPrice"] = float(inbound_record_detail.unit_price)
        # print(inbound_record_detail.inbound_amount, inbound_record_detail.unit_price)
        # print(material_storage.material_specification, material.material_name, material_type.material_type_name)
        account_owner_id = transaction.payable_payee_account_id
        account_owner_id_to_account_res[account_owner_id]['transactionDetails'].append(cur_transaction_res)
    res_data = list(account_owner_id_to_account_res.values())
    return jsonify({"payableInfo":res_data}), 200

@payable_management_bp.route('/payable_management/get_payable_info_new', methods=['GET'])
def get_payable_info_new():
    payable_object_accounts = (db.session.query(AccountingPayableAccount, AccountingPayeePayer)
                               .join(AccountingPayeePayer, AccountingPayableAccount.account_owner_id == AccountingPayeePayer.payee_id)
                               .all())
    payable_transactions_entities = (db.session.query(AccountingForeignAccountEvent,InboundRecord).filter_by(transaction_type = PAYABLE_INCREASE)
                                     .join(InboundRecord, InboundRecord.inbound_record_id == AccountingForeignAccountEvent.inbound_record_id)
                                     ).all()
    payable_payment_transactions = (db.session.query(AccountingPayableTransaction)).all()
    payable_sum_by_account_id = (db.session.query(AccountingForeignAccountEvent.payable_payee_account_id, func.sum(AccountingForeignAccountEvent.transaction_amount))
                             .filter_by(transaction_type = 1)
                             .group_by(AccountingForeignAccountEvent.payable_payee_account_id).all())
    paid_sum_by_account_id = (db.session.query(AccountingPayableTransaction.to_account_id, func.sum(AccountingPayableTransaction.transaction_amount))
                              .group_by(AccountingPayableTransaction.to_account_id).all())
    account_owner_id_to_account_res = {}
    for account, payee in payable_object_accounts:
        account_res_data = {}
        for attr in ACCOUNT_ATTR_LIST:
            account_res_data[to_camel(attr)] = getattr(account, attr)
        for attr in PAYEE_ATTR_LIST:
            account_res_data[to_camel(attr.replace("payee", "account_owner"))] = getattr(payee, attr)
        transaction_details = []
        account_res_data["transactionDetails"] = transaction_details
        account_owner_id_to_account_res[account.account_owner_id] = account_res_data
    for event ,inbound_record in payable_transactions_entities:
            transaction_res = {}
            transaction_res['transactionAmount'] = event.transaction_amount
            account_owner_id = event.payable_payee_account_id
            transaction_res['transactionDate'] = format_datetime(inbound_record.inbound_datetime)
            transaction_res['transactionType'] = '应付增加'
            account_owner_id_to_account_res[account_owner_id]['transactionDetails'].append(transaction_res)
    for payment_transaction in payable_payment_transactions:
        transaction_res = {}
        transaction_res['transactionAmount'] = payment_transaction.transaction_amount
        transaction_res['transactionDate'] = format_datetime(payment_transaction.transaction_date)
        transaction_res['transactionType'] = "应付付款"
        transaction_res['transactionFromAccount'] = payment_transaction.from_account_id
        account_owner_id = payment_transaction.to_account_id
        account_owner_id_to_account_res[account_owner_id]['transactionDetails'].append(transaction_res)
    
    for account_id ,payable_sum in payable_sum_by_account_id:
        account_owner_id_to_account_res[account_id]['accountTotalPayable'] = payable_sum
    for account_id, paid_sum in paid_sum_by_account_id:
        account_owner_id_to_account_res[account_id]['accountTotalPaid'] = paid_sum
    res_data = list(account_owner_id_to_account_res.values())
    return jsonify({"payableInfo":res_data}), 200
@payable_management_bp.route('/payable_management/get_transaction_history', methods=['GET'])
def get_transaction_history():
    return

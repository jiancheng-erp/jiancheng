from flask import Blueprint, jsonify, request
from models import *
from api_utility import to_camel, to_snake, format_datetime

import time
from app_config import app, db
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
@payable_management_bp.route('/payable_management/add_transaction', methods=['POST'])
def add_transaction():

    return
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

@payable_management_bp.route('/payable_management/get_transaction_history', methods=['GET'])
def get_transaction_history():
    return

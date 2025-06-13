DEFAULT_MATERIAL_PAYABLE_ACCOUNT_ID = 1
DEFAULT_SALES_COLLECTABLE_ACCOUNT_ID = 2
DEFAULT_HUMAN_RESOURCES_PAYABLE_ACCOUNT_ID = 3
from models import *
from app_config import db
from sqlalchemy import func
from constants import ACCOUNTING_PAYEE_NOT_FOUND, ACCOUNTING_PAYABLE_ACCOUNT_NOT_FOUND, ACCOUNTING_PAYEE_EXISTING
from constants import PAYABLE_EVENT_TO_TEXT, PAYABLE_EVENT_INBOUND,PAYABLE_EVENT_COMPOSITE_INBOUND,PAYABLE_EVENT_MISC_INBOUND,ACCOUNT_TYPE_CASH,ACCOUNT_TYPE_PAYABLE,ACCOUNT_TYPE_RECIEVABLE
from logger import logger
# def add_material_paybable(supplier, amount, unit):

#     supplier_name = supplier.name
#     db.session.query()
def add_payable_entity(name, address='', bank_info='', contact_info=''):
    # 添加应收账户收款人以及账号 初始账号数字为0
    existing_entity = db.session.query(AccountingPayeePayer).filter_by(payee_name = name).first()
    if existing_entity:
        logger.debug("entity already exist")
        return ACCOUNTING_PAYEE_EXISTING
    entity_type = 0
    payable_entity_name = name
    new_payable_entity = AccountingPayeePayer()
    new_payable_entity.payee_name = payable_entity_name
    new_payable_entity.payee_address = address
    new_payable_entity.payee_bank_info = bank_info
    new_payable_entity.payee_contact_info = contact_info
    new_payable_entity.entity_type = entity_type
    db.session.add(new_payable_entity)
    db.session.flush()
    new_payable_account_entity = AccountingPayableAccount()
    new_payable_account_entity.account_payable_balance = 0.00
    # unit 1 CNY default 
    new_payable_account_entity.account_unit_id = 1
    new_payable_account_entity.account_owner_id = new_payable_entity.payee_id
    db.session.add(new_payable_account_entity)
    logger.debug("new accounting entity and its account added successfully")
    return 0

def material_inbound_accounting_event(supplier_name, amount, inbound_record_id, unit=1,has_conversion=0,conversion_id=0):
    # 只处理材料入库 应收账目 工具入库使用 default_inbound_accounting_event()
    # supplier name 对应 accountingpayeepayer 表 payee name
    payee_entity = db.session.query(AccountingPayeePayer).filter_by(payee_name=supplier_name).first()
    if not payee_entity:
        logger.debug("supplier doenst existing in accounting table, check accounting_payee_payer")
        return ACCOUNTING_PAYEE_NOT_FOUND
    else:
        #应付款增加 材料费用
        transaction_type = 1
        new_transaction_entity = AccountingForeignAccountEvent()
        new_transaction_entity.transaction_type = transaction_type
        payable_account_entity = db.session.query(AccountingPayableAccount).filter_by(account_owner_id = payee_entity.payee_id).first()
        if not payable_account_entity:
            logger.debug("entity payable account not found in accounting payable account table")
            return ACCOUNTING_PAYABLE_ACCOUNT_NOT_FOUND
        # TODO type check 
        tg_accounts_update = db.session.query(ThirdGradeAccount).filter_by(account_bound_event = PAYABLE_EVENT_INBOUND).all()
        new_transaction_entity.payable_payee_account_id = payable_account_entity.account_id
        new_transaction_entity.transaction_amount = amount
        new_transaction_entity.transaction_amount_unit = unit
        new_transaction_entity.transaction_has_conversion = has_conversion
        new_transaction_entity.transaction_conversion_id = conversion_id
        new_transaction_entity.inbound_record_id = inbound_record_id
        db.session.add(new_transaction_entity)
        current_balance = payable_account_entity.account_payable_balance 
        payable_account_entity.account_payable_balance = current_balance + amount
        if tg_accounts_update:
            for account in tg_accounts_update:
                tg_account_balance = account.account_balance
                account.account_balance = tg_account_balance + amount
        return 0
    
def material_outbound_accounting_event(supplier_name, amount, outbound_record_id, unit=1, has_conversion=0, conversion_id=0):
    payee_entity = db.session.query(AccountingPayeePayer).filter_by(payee_name=supplier_name).first()
    if not payee_entity:
        logger.debug("supplier doenst existing in accounting table, check accounting_payee_payer")
        return ACCOUNTING_PAYEE_NOT_FOUND
    else:
        #应付款增加 材料费用
        new_transaction_entity = AccountingForeignAccountEvent(
            transaction_type = 1,
            payable_payee_account_id = None,
            transaction_amount = -amount, # 负数表示应付减少
            transaction_amount_unit = unit,
            transaction_has_conversion = has_conversion,
            transaction_conversion_id = conversion_id,
            outbound_record_id = outbound_record_id
        )
        payable_account_entity = db.session.query(AccountingPayableAccount).filter_by(account_owner_id = payee_entity.payee_id).first()
        if not payable_account_entity:
            logger.debug("entity payable account not found in accounting payable account table")
            return ACCOUNTING_PAYABLE_ACCOUNT_NOT_FOUND
        tg_accounts_update = db.session.query(ThirdGradeAccount).filter_by(account_bound_event = PAYABLE_EVENT_INBOUND).all()
        new_transaction_entity.payable_payee_account_id = payable_account_entity.account_id
        db.session.add(new_transaction_entity)
        current_balance = payable_account_entity.account_payable_balance 
        payable_account_entity.account_payable_balance = current_balance - amount
        if tg_accounts_update:
            for account in tg_accounts_update:
                tg_account_balance = account.account_balance
                account.account_balance = tg_account_balance - amount
        return 0

# def add_sales_collectable():
#     return
def add_composition_payable():
    #TODO
    #复合入库
    return

def default_inbound_accounting_event():
    #生产工具入库
    #TODO
    return
def set_up_customer_accounts():
    # TODO for now the balances are 0 by default
    # balances = db.session.query(Customer,func.max(OrderShoeBatchInfo.total_price)).join(Order, Customer.customer_id == Order.customer_id
    #                                 ).join(OrderShoe, Order.order_id == OrderShoe.order_id
    #                                        ).join(OrderShoeType, OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id
    #                                               ).join(OrderShoeBatchInfo,OrderShoeType.order_shoe_type_id == OrderShoeBatchInfo.order_shoe_type_id
    #                                                      ).group_by(Customer.customer_id).all()
    # logger.debug(balances)
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

def compute_balance():
    # TODO 查看当前各客户应收销售额 ERIC
    #客户 鞋款 以及各鞋款总数
    order_count = db.session.query(Customer,OrderShoeType.order_shoe_type_id, func.sum(OrderShoeBatchInfo.total_amount)).join(Order,Order.customer_id == Customer.customer_id
                                                                ).join(OrderShoe, Order.order_id == OrderShoe.order_id
                                                                    ).join(OrderShoeType,OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id
                                                                    ).join(OrderShoeBatchInfo, OrderShoeBatchInfo.order_shoe_type_id == OrderShoeType.order_shoe_type_id
                                                                    ).group_by(OrderShoeType.order_shoe_type_id, Customer.customer_id).all()
    for i in order_count:
        logger.debug(i)
    #客户 鞋款 以及各鞋款单价 和单位
    order_price = db.session.query(Customer,OrderShoeType.unit_price, OrderShoeType.currency_type,OrderShoeType.order_shoe_type_id).join(Order,Order.customer_id == Customer.customer_id
                                                                ).join(OrderShoe, Order.order_id == OrderShoe.order_id
                                                                    ).join(OrderShoeType,OrderShoeType.order_shoe_id == OrderShoe.order_shoe_id
                                                                           ).group_by(OrderShoeType.order_shoe_type_id, Customer.customer_id).all()
    for j in order_price:
        logger.debug(j)
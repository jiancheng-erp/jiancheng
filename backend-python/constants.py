PRODUCTION_LINE_REFERENCE = [0, 1, 2]

PRICE_REPORT_REFERENCE = {
    "裁断": {
        "status_number": 20,
        "operation_id": [78, 79],
    },
    "针车预备": {
        "status_number": 27,
        "operation_id": [92, 93],
    },
    "针车": {
        "status_number": 27,
        "operation_id": [92, 93],
    },
    "成型": {
        "status_number": 37,
        "operation_id": [112, 113],
    },
}

SHOESIZERANGE = [i for i in range(34, 47)]

IN_PRODUCTION_ORDER_NUMBER = 9
END_OF_ORDER_NUMBER = 18
END_OF_PRODUCTION_NUMBER = 42


ORDER_SHOE_STATUS_REFERENCE = {
    "生产开始": 18,
    "裁断开始": 23,
    "针车预备开始": 30,
    "针车开始": 32,
    "成型开始": 40,
    "裁断结束": 24,
    "针车预备结束": 31,
    "针车结束": 33,
    "成型结束": 41,
    "生产结束": 42,
}

DEFAULT_SUPPLIER = "询价"

ACCOUNTING_PAYEE_NOT_FOUND = 1
ACCOUNTING_PAYABLE_ACCOUNT_NOT_FOUND = 2
ACCOUNTING_PAYEE_EXISTING = 3


PAYABLE_EVENT_TO_TEXT = {"I":"材料采购入库产生应付", "C":"委外加工入库产生应付"
                         ,"M":"其他类型入库产生应付"}
PAYABLE_EVENT_INBOUND = "I"
PAYABLE_EVENT_COMPOSITE_INBOUND = "C"
PAYABLE_EVENT_MISC_INBOUND = "M"
ACCOUNT_TYPE_RECIEVABLE = '0'
ACCOUNT_TYPE_PAYABLE = '1'
ACCOUNT_TYPE_CASH = '2'
MATERIAL_PURCHASE_PAYABLE_ID = 14
DEFAULT_TRANSACTION_UNIT = 1
DEFAULT_PAYABLE_TRANSACTION_ACCOUNT_GRADE = '3'


OUTBOUND_TYPE_MAPPING = {
    0: "生产出库",
    1: "废料处理",
    2: "外包出库",
    3: "复合出库",
    4: "材料退回",
}
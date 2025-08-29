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


PAYABLE_EVENT_TO_TEXT = {
    "I": "材料采购入库产生应付",
    "C": "委外加工入库产生应付",
    "M": "其他类型入库产生应付",
}
PAYABLE_EVENT_INBOUND = "I"
PAYABLE_EVENT_COMPOSITE_INBOUND = "C"
PAYABLE_EVENT_MISC_INBOUND = "M"
ACCOUNT_TYPE_RECIEVABLE = "0"
ACCOUNT_TYPE_PAYABLE = "1"
ACCOUNT_TYPE_CASH = "2"
MATERIAL_PURCHASE_PAYABLE_ID = 14
DEFAULT_TRANSACTION_UNIT = 1

DEFAULT_PAYABLE_TRANSACTION_ACCOUNT_GRADE = "3"


OUTBOUND_TYPE_MAPPING = {
    0: "生产出库",
    1: "废料处理",
    2: "外包出库",
    3: "复合出库",
    4: "材料退回",
}

BOM_STATUS = {
    "1": "材料已保存",
    "2": "材料已提交",
    "3": "等待用量填写",
    "4": "用量填写已保存",
    "5": "用量填写已提交",
    "6": "用量填写已下发",
}

BOM_STATUS_TO_INT = {
    "材料已保存": "1",
    "材料已提交": "2",
    "等待用量填写": "3",
    "用量填写已保存": "4",
    "用量填写已提交": "5",
    "用量填写已下发": "6",
}


PO_STATUS = {
    "0": "未填写",
    "1": "已保存",
    "2": "已提交",
}

PO_STATUS_TO_INT = {
    "未填写": "0",
    "已保存": "1",
    "已提交": "2",
}
PRICE_REPORT_NOT_SUBMITTED = "未提交"
PRICE_REPORT_PM_PENDING = "生产副总审核中"
PRICE_REPORT_PM_REJECTED = "生产副总驳回"
PRICE_REPORT_GM_PENDING = "总经理审核中"
PRICE_REPORT_GM_REJECTED = "总经理驳回"
PRICE_REPORT_GM_APPROVED = "已审批"

GENERAL_MANAGER_ROLE = 2
PRODUCTION_MANAGER_ROLE = 3
WAREHOUSE_CLERK_ROLE = 23
ACCOUNTING_AUDIT_ROLE = 24


SCHEDULING_STATUS_TO_INT = {
    "裁断未排期": 0,
    "预备未排期": 1,
    "针车未排期": 2,
    "成型未排期": 3,
    "已排期": 4,
}

FINISHED_STORAGE_STATUS_ENUM = {
    "ALL": -1,
    "PRODUCT_INBOUND_NOT_FINISHED": 0,
    "PRODUCT_INBOUND_FINISHED": 1,
    "PRODUCT_OUTBOUND_FINISHED": 2,
}
FINISHED_STORAGE_STATUS = {
    -1: "全部",
    0: "未完成入库",
    1: "已完成入库",
    2: "已完成出库"
}
PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM = {
    "ALL": -1,
    "PRODUCT_OUTBOUND_AUDIT_NOT_INIT": 0,
    "PRODUCT_OUTBOUND_AUDIT_ONGOING": 1,
    "PRODUCT_OUTBOUND_AUDIT_APPROVED": 2,
}
PRODUCT_OUTBOUND_AUDIT_STATUS = {
    -1: "全部",
    0: "未下发审核",
    1: "总经理审核中",
    2: "已批准",
}

ORDER_FINISH_SYMBOL = 16
BUSINESS_DEPARTMENT = 10
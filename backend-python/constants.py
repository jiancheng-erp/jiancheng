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

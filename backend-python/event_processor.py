from helperclass import *
from models import *
from app_config import db
from logger import logger
from sqlalchemy import or_, and_
from collections import deque
from copy import deepcopy


ORDERSTATUSNAMELIST = [
    "订单创建",
    "打样单创建",
    "打样单初步确认",
    "打样单分配",
    "打样单修改",
    "打样单最终确认",
    "生产订单创建",
    "生产订单总经理确认",
    "生产副总确认",
    "生产流程",
    "生产结束确认",
    "业务部确认",
    "业务部创建发货通知",
    "发货通知下发",
    "总经理确认",
    "成品仓发货",
    "发货量上传",
    "全部发货确认",
    "订单完成",
]

ORDERSHOESTATUSNAMELIST = [
    "投产指令单创建",
    "投产指令单下发",
    "一次BOM填写",
    "一次BOM下发",
    "面料单位用量计算",
    "面料单位用量下发",
    "一次采购订单创建",
    "总仓采购订单创建",
    "一次采购入库",
    "技术部调版分配",
    "技术部调版下发",
    "二次BOM填写",
    "二次BOM下发",
    "二次采购订单创建",
    "二次采购订单下发",
    "二次采购入库",
    "材料到齐通知",
    "生产排期，分配",
    "生产开始",
    "裁断材料出库",
    "裁断，批皮工价填报",
    "生产副总审核",
    "总经理审核",
    "生产中",
    "裁断结束",
    "半成品中转入库",
    "半成品中转针车材料出库",
    "针车及预备工序填报",
    "生产副总审核",
    "总经理审核",
    "针车预备开始",
    "针车预备结束",
    "针车开始",
    "针车结束",
    "鞋包中转仓入库",
    "鞋包中转仓出库",
    "成型材料出库",
    "成型工价填报",
    "生产副总审核",
    "总经理审核",
    "成型开始",
    "成型结束",
    "生产结束",
]

ORDERSHOESTATUSGRAPH = {
    0: {"outgoing": [1], "incoming": []},
    1: {"outgoing": [2, 9, 17], "incoming": [0]},
    2: {"outgoing": [3], "incoming": [1]},
    3: {"outgoing": [4], "incoming": [2]},
    4: {"outgoing": [5], "incoming": [3]},
    5: {"outgoing": [6, 7], "incoming": [4]},
    6: {"outgoing": [8], "incoming": [5]},
    7: {"outgoing": [15], "incoming": [5]},
    8: {"outgoing": [16], "incoming": [6]},
    9: {"outgoing": [10], "incoming": [1]},
    10: {"outgoing": [11], "incoming": [9]},
    11: {"outgoing": [12], "incoming": [10]},
    12: {"outgoing": [13], "incoming": [11]},
    13: {"outgoing": [14], "incoming": [12]},
    14: {"outgoing": [15], "incoming": [13]},
    15: {"outgoing": [16], "incoming": [7]},
    16: {"outgoing": [42], "incoming": [8, 15]},
    17: {"outgoing": [18], "incoming": [1]},
    18: {"outgoing": [20, 23, 27, 37], "incoming": [17]},
    19: {"outgoing": [], "incoming": []},
    20: {"outgoing": [21], "incoming": [18]},
    21: {"outgoing": [22], "incoming": [20]},
    22: {"outgoing": [], "incoming": [21]},
    23: {"outgoing": [42], "incoming": [18]},
    24: {"outgoing": [], "incoming": []},
    25: {"outgoing": [], "incoming": []},
    26: {"outgoing": [], "incoming": []},
    27: {"outgoing": [28], "incoming": [18]},
    28: {"outgoing": [29], "incoming": [27]},
    29: {"outgoing": [], "incoming": [28]},
    30: {"outgoing": [], "incoming": []},
    31: {"outgoing": [], "incoming": []},
    32: {"outgoing": [], "incoming": []},
    33: {"outgoing": [], "incoming": []},
    34: {"outgoing": [], "incoming": []},
    35: {"outgoing": [], "incoming": []},
    36: {"outgoing": [], "incoming": []},
    37: {"outgoing": [38], "incoming": [18]},
    38: {"outgoing": [39], "incoming": [37]},
    39: {"outgoing": [], "incoming": [38]},
    40: {"outgoing": [], "incoming": []},
    41: {"outgoing": [], "incoming": []},
    42: {"outgoing": [], "incoming": [23]},
}


class OrderStatusVal:
    def __init__(self, status_id, status_name):
        self.status_id = status_id
        self.status_name = status_name

    def getId(self):
        return self.status_id

    def getName(self):
        return self.status_name

    def __repr__(self):
        return str([self.status_id, self.status_name])


class OrderShoeStatusVal:
    def __init__(self, status_id, status_name):
        self.status_id = status_id
        self.status_name = status_name

    def getId(self):
        return self.status_id

    def getName(self):
        return self.status_name

    def __repr__(self):
        return f"{self.status_id} {self.status_name}"


class Procedure:
    def __init__(self, name, procedurePath, mapping):
        self.name = name
        self.procedurepath = procedurePath
        self.mappipng = mapping
        self.current_node = []

    def getPath(self):
        return self.procedurepath

    def getName(self):
        return self.name


class EventProcessor:
    def __init__(self):
        ### Paths
        self.orderStatusPath = LinkedList()
        self.orderShoeLogisticPath = Graph()
        self.orderShoeProductionPath = Graph()
        ### NameList
        self.ORDERSTATUSNAMELIST = ORDERSTATUSNAMELIST
        self.ORDERSHOESTATUSNAMELIST = ORDERSHOESTATUSNAMELIST
        ### idToNode dict
        self.orderStatusidToNode = dict()
        self.orderShoeStatusidToNode = dict()
        ### Procedures
        self.orderShoeLogisticProcedures = None
        self.orderShoeProductionProcedures = None
        self.orderProcedures = None
        self._constructProcedures()

    def _constructProcedures(self):

        ### orderStatusPath
        head = self.orderStatusPath.getHead()
        prev = None
        for i in range(len(self.ORDERSTATUSNAMELIST)):
            cur_status = OrderStatusVal(i, self.ORDERSTATUSNAMELIST[i])
            node_insert = LinkedListNode(val=cur_status)
            self.orderStatusidToNode[i] = node_insert
            if i == 0:
                self.orderStatusPath.setHead(node_insert)
                prev = node_insert
            else:
                prev.setNext(node_insert)
                node_insert.setPrev(prev)
                prev = node_insert
        ### OrderStatusProcedures
        self.orderProcedures = Procedure(
            "OrderProcedure", self.orderStatusPath, self.orderStatusidToNode
        )

        ### orderShoeStatusPath
        for node_id, value in ORDERSHOESTATUSGRAPH.items():
            status_name = ORDERSHOESTATUSNAMELIST[node_id]
            node = GraphNode(val=OrderShoeStatusVal(node_id, status_name))
            self.orderShoeStatusidToNode[node_id] = node

        for node_id, value in ORDERSHOESTATUSGRAPH.items():
            node = self.orderShoeStatusidToNode[node_id]
            for prev_node_id in value["incoming"]:
                node.insertPrev(self.orderShoeStatusidToNode[prev_node_id])
            for next_node_id in value["outgoing"]:
                node.insertNext(self.orderShoeStatusidToNode[next_node_id])

        ### disconnect LogisticProcedure and Production Procedure
        # li = self.orderShoeStatusidToNode[2].getPrev()[0].getNext()
        # li.remove(self.orderShoeStatusidToNode[2])
        # self.orderShoeStatusidToNode[2].getPrev().remove(
        #     self.orderShoeStatusidToNode[1]
        # )
        # self.orderShoeStatusidToNode[10].getNext().remove(
        #     self.orderShoeStatusidToNode[11]
        # )
        # self.orderShoeStatusidToNode[11].getPrev().remove(
        #     self.orderShoeStatusidToNode[10]
        # )
        # self.orderShoeProductionProcedures = Procedure(
        #     "OrderShoeProcedure",
        #     self.orderShoeProductionPath,
        #     self.orderShoeStatusidToNode,
        # )

        # ### TODO LogisticPath
        # head = self.orderShoeLogisticPath.getSource()
        # prev = None

    def testPaths(self):
        for i in range(len(ORDERSHOESTATUSNAMELIST)):
            node = self.orderShoeStatusidToNode[i]
            logger.debug("prev has " + str(node.getPrev()))
            logger.debug("cur node is " + str(node))
            logger.debug("next has " + str(node.getNext()))
            logger.debug("================================")

    def isMerge(self, node_id):
        node_prevs = self.orderShoeStatusidToNode[node_id].getPrev()
        result = len(node_prevs) > 1
        return result

    def dbQueryOperation(self, operation_id):
        operation_entity = (
            db.session.query(Operation)
            .filter(Operation.operation_id == operation_id)
            .first()
        )
        return operation_entity

    def dbQueryOrderShoeStatus(self, order_shoe_id):
        queryResult = (
            db.session.query(OrderShoeStatus)
            .filter(OrderShoeStatus.order_shoe_id == order_shoe_id)
            .all()
        )
        resultStatus = [entity.current_status for entity in queryResult]
        resultValue = [entity.current_status_value for entity in queryResult]
        return resultStatus, resultValue

    def dbQueryOrderTypeByOrderShoe(self, order_shoe_id):
        result = (
            db.session.query(Order.order_type)
            .join(OrderShoe, Order.order_id == OrderShoe.order_id)
            .filter(OrderShoe.order_shoe_id == order_shoe_id)
            .first()
        )
        return result[0] if result else None

    def dbQueryOrderStatus(self, orderId):
        queryResult = (
            db.session.query(OrderStatus)
            .filter(OrderStatus.order_id == orderId)
            .first()
        )
        return queryResult.order_current_status, queryResult.order_status_value

    def validateEvent(self, event):
        ### TODO
        return event.operation_id <= 123 and event.operation_id >= 0

    def operationSubjectExists(self, event, operation, current_status=None):
        ### check if order/ordershoe id with specified status exists
        """
        when current status isn't None, checks if an entity with specified current
        status exists, otherwise checks with id.
        """
        if operation.operation_type == 1:
            query_db = OrderStatus
            attr_name = "order_id"
            attr_query_subject = event.event_order_id
        else:
            query_db = OrderShoeStatus
            attr_name = "order_shoe_id"
            attr_query_subject = event.event_order_shoe_id

        if current_status:
            entity = (
                db.session.query(query_db)
                .filter(
                    getattr(query_db, attr_name) == attr_query_subject,
                    getattr(query_db, "current_status") == current_status,
                )
                .first()
            )
        else:
            entity = (
                db.session.query(query_db)
                .filter(getattr(query_db, attr_name) == attr_query_subject)
                .first()
            )
        result = entity != None
        return result

    def processOrderShoeEvent(self, event, operation):
        orderShoeId = event.event_order_shoe_id
        curStat, curVal = self.dbQueryOrderShoeStatus(orderShoeId)
        modifiedStatus = operation.operation_modified_status
        modifiedValue = operation.operation_modified_value
        order_type = self.dbQueryOrderTypeByOrderShoe(orderShoeId)
        logger.debug("current order_shoe_id is " + str(orderShoeId))
        logger.debug("current status is " + str(curStat) + " with value " + str(curVal))
        logger.debug(
            "modifying into "
            + str(modifiedStatus)
            + " with value "
            + str(modifiedValue)
        )
        result = False
        # check operation validility
        if modifiedStatus in curStat and (
            modifiedValue - curVal[curStat.index(modifiedStatus)] == 1
        ):
            logger.debug("operation is valid")
            if modifiedValue == 1:
                result = self.dbSetOrderShoeStatus(event, operation)
            else:
                # modifying existing status
                nextStatus = self.getNextShoeStatus(
                    curStat, curVal, operation, event.event_order_shoe_id
                )
                logger.debug("the next status is " + str(nextStatus))
                if order_type == "F" and any(status_id > 17 for status_id in nextStatus):
                    logger.debug("forecast order cannot move into production statuses")
                    return False
                result = self.dbSetOrderShoeStatus(
                    event, operation, next_status=nextStatus
                )
            ### TODO INSERT EVENT INTO DB
        else:
            logger.debug(
                "Modifying an non exist status or existing status with a wrong value"
            )
        return result

    # def processOutsourceEvent(self, order_shoe_id, outsource_type):
    #     """
    #     outsource_type:
    #         0: 针车，只有在裁断结束时能调用
    #         1: 裁断+针车，只有在生产排期时能调用
    #     """
    #     if outsource_type == 0:
    #         status_obj = (
    #             db.session.query(OrderShoeStatus)
    #             .filter_by(order_shoe_id=order_shoe_id, current_status=24)
    #             .first()
    #         )
    #     elif outsource_type == 1:
    #         status_obj = (
    #             db.session.query(OrderShoeStatus)
    #             .filter_by(order_shoe_id=order_shoe_id, current_status=17)
    #             .first()
    #         )
    #     status_obj.current_status = 33
    #     status_obj.current_status_value = 0

    def processEvent(self, event):
        if self.validateEvent(event):
            operation = self.dbQueryOperation(event.operation_id)
            if self.operationSubjectExists(event, operation):
                operationType = operation.operation_type
                if operationType == 1:
                    result = self.processOrderEvent(event, operation)
                # operation type is 2
                else:
                    result = self.processOrderShoeEvent(event, operation)
            else:
                raise Exception("OrderID or OrderShoeId doesnt Exist")
        else:
            raise Exception("Event Not valid, Operation ID out of Bound")
        return result

    def processRejectEvent(self, event, current_status):
        logger.debug(f"processing reject event for order_shoe_id {event.event_order_shoe_id}")
        logger.debug(f"current status is {current_status}")
        logger.debug(f"needs to perform operation id {event.operation_id}")
        if self.validateEvent(event):
            operation = self.dbQueryOperation(event.operation_id)
            if operation.operation_type == 2:
                if self.operationSubjectExists(
                    event, operation, current_status=current_status
                ):
                    result = self.setOrderShoeRejectStatus(
                        event, operation, current_status
                    )
                else:
                    result = False
                    logger.debug("OrderShoeStatus with current_status Doesnt exist in DB")
            else:
                result = False
                logger.debug("cannot reject order status, use processEvent to set next status")
        else:
            result = False
            logger.debug("bad operation id, should be between 123 and 0")
        return result

    def setOrderShoeRejectStatus(self, event, operation, current_status):
        entity = (
            db.session.query(OrderShoeStatus)
            .filter(
                OrderShoeStatus.current_status == current_status,
                OrderShoeStatus.order_shoe_id == event.event_order_shoe_id,
            )
            .first()
        )
        entity.current_status = operation.operation_modified_status
        entity.current_status_value = operation.operation_modified_value
        db.session.flush()
        return True

    def dbSetOrderShoeStatus(self, event, operation, next_status=None):
        ### if setting next status
        if next_status:
            if len(next_status) == 1:
                prevStatus = [
                    prev.getVal().getId()
                    for prev in self.orderShoeStatusidToNode[next_status[0]].getPrev()
                ]
                if self.isMerge(next_status[0]):
                    logger.debug("Merged node")
                    logger.debug("the next status is" + str(prevStatus))
                    entities = (
                        db.session.query(OrderShoeStatus)
                        .filter(
                            OrderShoeStatus.order_shoe_id == event.event_order_shoe_id,
                            OrderShoeStatus.current_status.in_(prevStatus),
                        )
                        .all()
                    )
                    logger.debug(entities)
                    for entity in entities:
                        db.session.delete(entity)
                    newEntity = (
                        db.session.query(OrderShoeStatus)
                        .filter_by(
                            order_shoe_id=event.event_order_shoe_id,
                            current_status=next_status[0],
                        )
                        .first()
                    )
                    logger.debug(newEntity)
                    if not newEntity:
                        newEntity = OrderShoeStatus(
                            order_shoe_id=event.event_order_shoe_id,
                            current_status=next_status[0],
                            current_status_value=0,
                        )
                        logger.debug(newEntity)
                        db.session.add(newEntity)
                else:
                    entity = (
                        db.session.query(OrderShoeStatus)
                        .filter(
                            OrderShoeStatus.order_shoe_id == event.event_order_shoe_id,
                            OrderShoeStatus.current_status
                            == operation.operation_modified_status,
                        )
                        .first()
                    )
                    entity.current_status = next_status[0]
                    entity.current_status_value = 0
            else:
                prevStatus = operation.operation_modified_status
                logger.debug(prevStatus)
                logger.debug(next_status)
                if prevStatus in next_status:
                    next_status.remove(prevStatus)
                    newEntity = OrderShoeStatus(
                        order_shoe_id=event.event_order_shoe_id,
                        current_status=next_status[0],
                        current_status_value=0,
                    )
                    db.session.add(newEntity)
                    prevEntity = (
                        db.session.query(OrderShoeStatus)
                        .filter(
                            OrderShoeStatus.order_shoe_id == event.event_order_shoe_id,
                            OrderShoeStatus.current_status == prevStatus,
                        )
                        .first()
                    )
                    prevEntity.current_status_value = operation.operation_modified_value
                else:
                    entity = (
                        db.session.query(OrderShoeStatus)
                        .filter(
                            OrderShoeStatus.order_shoe_id == event.event_order_shoe_id,
                            OrderShoeStatus.current_status == prevStatus,
                        )
                        .first()
                    )
                    db.session.delete(entity)
                    for newStatus in next_status:
                        newEntity = OrderShoeStatus(
                            order_shoe_id=event.event_order_shoe_id,
                            current_status=newStatus,
                            current_status_value=0,
                        )
                        db.session.add(newEntity)
        ### or only setting value
        else:
            logger.debug("no next value")
            entity = (
                db.session.query(OrderShoeStatus)
                .filter(
                    OrderShoeStatus.order_shoe_id == event.event_order_shoe_id,
                    OrderShoeStatus.current_status
                    == operation.operation_modified_status,
                )
                .first()
            )
            entity.current_status_value = operation.operation_modified_value
        db.session.flush()
        return True

    def getNextShoeStatus(self, currentStatus, currentValue, operation, order_shoe_id):
        modified_status = operation.operation_modified_status
        cur_node = self.orderShoeStatusidToNode[modified_status]
        logger.debug(cur_node.getNext())
        result = []
        if len(cur_node.getNext()) > 1:
            next_ids = [next_node.getVal().getId() for next_node in cur_node.getNext()]
            for next_id in next_ids:
                if self.isMerge(next_id):
                    prev_ids = [
                        prev.getVal().getId()
                        for prev in self.orderShoeStatusidToNode[next_id].getPrev()
                    ]
                    prev_ids.remove(modified_status)
                    entity = (
                        db.session.query(OrderShoeStatus).filter(
                            OrderShoeStatus.order_shoe_id == order_shoe_id,
                            OrderShoeStatus.current_status == prev_ids[0],
                        )
                    ).first()
                    logger.debug(entity)
                    if entity and entity.current_status_value == 2:
                        result.append(next_id)
                    else:
                        result.append(modified_status)
                    # else:
                    #     logger.debug(5)
                    #     ### do nothing
                else:
                    result.append(next_id)
        elif len(cur_node.getNext()) == 1:
            ### only one next
            ### if it's merge
            next_id = cur_node.getNext()[0].getVal().getId()
            if self.isMerge(next_id):
                prev_ids = [
                    prev.getVal().getId()
                    for prev in self.orderShoeStatusidToNode[next_id].getPrev()
                ]
                prev_ids.remove(modified_status)
                logger.debug("previous ids: " + str(prev_ids))
                entities = (
                    db.session.query(OrderShoeStatus).filter(
                        OrderShoeStatus.order_shoe_id == order_shoe_id,
                        OrderShoeStatus.current_status.in_(prev_ids),
                    )
                ).all()
                # if all previous nodes are presented, processor can progress to next
                if len(entities) == len(prev_ids):
                    flag = all(entity.current_status_value == 2 for entity in entities)
                    if flag:
                        result.append(next_id)
            else:
                result.append(next_id)
        logger.debug(result)
        return result

        if len(currentStatus) == 1:
            cur_stat = currentStatus[0]
            next_status = self.orderShoeStatusidToNode[cur_stat].getNext()
            result = next_status
        elif len(currentStatus) == 2 and len(currentValue) == 2:
            stat_1 = currentStatus[0]
            stat_2 = currentStatus[1]
            nextStatus1 = self.orderShoeStatusidToNode[stat_1].getNext()
            nextStatus2 = self.orderShoeStatusidToNode[stat_2].getNext()
            modifiedStatus = operation.operation_modified_status
            ### the other status is 2
            if 2 in currentValue:
                ## see if the next node is to merge
                if nextStatus1 == nextStatus2:
                    result = nextStatus1
                ### if not merge yet go to next node
                else:
                    result = self.orderShoeStatusidToNode[modifiedStatus].getNext()
            else:
                if self.orderShoeStatusidToNode[modifiedStatus].getNext()[0].isMerge():
                    result = None
                else:
                    result = self.orderShoeStatusidToNode[modifiedStatus].getNext()
        if result:
            idResult = [res.getVal().getId() for res in result]
        else:
            idResult = None
        return idResult

    ## test

    def processOrderEvent(self, event, operation):
        orderId = event.event_order_id
        modifiedValue = operation.operation_modified_value
        modifiedStatus = operation.operation_modified_status
        orderStatus, statusVal = self.dbQueryOrderStatus(orderId)
        ### check operation valid
        if orderStatus == modifiedStatus and (modifiedValue - statusVal == 1):
            if modifiedValue == 2:
                ### set status to next
                curStat = modifiedStatus
                nextStatus = self.getNextOrderStatus(curStat)
                if nextStatus:
                    logger.debug("next status is " + str(nextStatus))
                    result = self.dbSetOrderStatus(
                        event, operation, next_status=nextStatus
                    )
                else:
                    logger.debug("Order Completed, Event not executed")
                    result = False
            else:
                ### set status to operation value
                result = self.dbSetOrderStatus(event, operation)

            ### TODO INSERT EVENT INTO DB
            # self.dbInsertEvent(event)
        else:
            logger.debug("Order status doesnt match operation status, Event Invalid")
            result = False
        return result

    def dbSetOrderStatus(self, event, operation, next_status=None):
        entity = (
            db.session.query(OrderStatus)
            .filter(OrderStatus.order_id == event.event_order_id)
            .first()
        )
        entity.order_current_status = operation.operation_modified_status
        entity.order_status_value = operation.operation_modified_value
        if next_status:
            entity.order_current_status = next_status
            entity.order_status_value = 0
        db.session.flush()
        return True

    def getNextOrderStatus(self, currentstatus):
        return self.orderStatusidToNode[currentstatus].getNext().getVal().getId()

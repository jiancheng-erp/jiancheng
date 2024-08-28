from helperclass import *
from models import *
from app_config import db


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
    "面料单位用量计算",
    "面料单位用量下发",
    "一次BOM填写",
    "一次BOM下发",
    "一次采购订单创建",
    "一次采购订单下发",
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
    "财务部审核",
    "生产副总审核",
    "裁断开始",
    "裁断结束",
    "半成品中转入库",
    "半成品中转针车材料出库",
    "针车及预备工序填报",
    "财务部审核",
    "生产副总审核",
    "针车预备开始",
    "针车预备结束",
    "针车开始",
    "针车结束",
    "鞋包中转仓入库",
    "鞋包中转仓出库",
    "成型材料出库",
    "成型工价填报",
    "财务部审核",
    "生产副总审核",
    "成型开始",
    "成型结束",
    "生产结束",
]


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
        return str(self.status_id) + " " + self.status_name


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
        head = self.orderShoeProductionPath.getSource()
        prev = None
        for i in range(len(self.ORDERSHOESTATUSNAMELIST)):
            statusName = ORDERSHOESTATUSNAMELIST[i]
            node = GraphNode(val=OrderShoeStatusVal(i, statusName))
            self.orderShoeStatusidToNode[i] = node
            prevs = []
            if i == 0:
                self.orderShoeProductionPath.setSource(node)
            elif i == 9:
                prevs.append(self.orderShoeStatusidToNode[3])
            elif i == 16:
                prevs = [prev, self.orderShoeStatusidToNode[8]]
            elif i == 17:
                prevs.append(self.orderShoeStatusidToNode[1])
            elif i == 18:
                prevs = [prev, self.orderShoeStatusidToNode[10]]
            elif i == 20:
                prevs = [self.orderShoeStatusidToNode[18]]
            elif i == 23:
                prevs = [prev, self.orderShoeStatusidToNode[19]]
            elif i == 27:
                prevs = [self.orderShoeStatusidToNode[24]]
            elif i == 30:
                prevs = [prev, self.orderShoeStatusidToNode[26]]
            elif i == 37:
                prevs.append(self.orderShoeStatusidToNode[33])
            elif i == 40:
                prevs = [prev, self.orderShoeStatusidToNode[36]]
            else:
                prevs = [prev]
            for prev_node in prevs:
                prev_node.insertNext(node)
                node.insertPrev(prev_node)
            prev = node

        ### disconnect LogisticProcedure and Production Procedure
        li = self.orderShoeStatusidToNode[4].getPrev()[0].getNext()
        li.remove(self.orderShoeStatusidToNode[4])
        self.orderShoeStatusidToNode[10].getNext().remove(
            self.orderShoeStatusidToNode[11]
        )
        self.orderShoeStatusidToNode[11].getPrev().remove(
            self.orderShoeStatusidToNode[10]
        )
        self.orderShoeProductionProcedures = Procedure(
            "OrderShoeProcedure",
            self.orderShoeProductionPath,
            self.orderShoeStatusidToNode,
        )

        ### TODO LogisticPath
        head = self.orderShoeLogisticPath.getSource()
        prev = None

    def testPaths(self):
        for i in range(len(ORDERSHOESTATUSNAMELIST)):
            node = self.orderShoeStatusidToNode[i]
            print("prev has " + str(node.getPrev()))
            print("cur node is " + str(node))
            print("next has " + str(node.getNext()))

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

    def dbQueryOrderStatus(self, orderId):
        queryResult = (
            db.session.query(OrderStatus)
            .filter(OrderStatus.order_id == orderId)
            .first()
        )
        return queryResult.order_currentstatus, queryResult.order_status_value

    def validateEvent(self, event):
        ### TODO
        return event.operation_id < 122 and event.operation_id >= 0 

    def operationSubjectExists(self, event, operation, current_status = None):
        ### check if order/ordershoe id with specified status exists
        if operation.operation_type == 1:
            query_db = OrderStatus
            attr_name = "order_id"
            attr_query_subject = event.event_order_id
        else:
            query_db = OrderShoeStatus
            attr_name = "order_shoe_id"
            attr_query_subject = event.event.event_order_shoe_id
        
        if current_status:
            entity = (
                db.session.query(query_db)
                .filter(getattr(query_db, attr_name) == attr_query_subject,
                        getattr(query_db, "current_status") == current_status)
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

    def processOrderEvent(self, event, operation):
        orderId = event.event_order_id
        modifiedValue = operation.operation_modified_value
        modifiedStatus = operation.operation_modified_status
        orderStatus, statusVal = self.dbQueryOrderStatus(orderId)
        ### check operation valid
        if orderStatus == modifiedStatus and (modifiedValue - statusVal == 1):
            if modifiedValue == 2:
                ### set status to next ,
                curStat = modifiedStatus
                nextStatus = self.getNextOrderStatus(curStat)
                if nextStatus:
                    print("next status is " + str(nextStatus))
                    result = self.dbSetOrderStatus(
                        event, operation, next_status=nextStatus
                    )
                else:
                    print("Order Completed, Event not executed")
                    result = False
            else:
                ### set status to operation value
                result = self.dbSetOrderStatus(event, operation)

            ### TODO INSERT EVENT INTO DB
            # self.dbInsertEvent(event)
        else:
            print("Order status doesnt match operation status, Event Invalid")
            result = False
        return result

    def processOrderShoeEvent(self, event, operation):
        orderShoeId = event.event_order_shoe_id
        curStat, curVal = self.dbQueryOrderShoeStatus(orderShoeId)
        modifiedStatus = operation.operation_modified_status
        modifiedValue = operation.operation_modified_value
        print("current order_shoe_id is " + str(orderShoeId))
        print("current status is " + str(curStat) + " with value " + str(curVal))
        print(
            "modifying into "
            + str(modifiedStatus)
            + " with value "
            + str(modifiedValue)
        )
        ### check operation validility
        if modifiedStatus in curStat and (
            modifiedValue - curVal[curStat.index(modifiedStatus)] == 1
        ):
            print("operation is valid")
            if modifiedValue == 1:
                result = self.dbSetOrderShoeStatus(event, operation)
            else:
                # modifying existing status
                nextStatus = self.getNextShoeStatus(curStat, curVal, operation)
                result = self.dbSetOrderShoeStatus(
                    event, operation, next_status=nextStatus
                )

            ### TODO INSERT EVENT INTO DB
        else:
            print("Modifying an non exist status or existing status with a wrong value")
            result = False
        return result

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
                print("OrderID or OrderShoeId doesnt Exist")
                result = False
        else:
            print("Event Not valid, Operation ID out of Bound")
            result = False
        return result
    
    def processRejectEvent(self, event, current_status):
        if self.validateEvent(event):
            operation = self.dbQueryOperation(event.operation_id)
            if operation.operation_type == 2:
                if self.operationSubjectExists(event, operation, current_status = current_status):
                    result = self.setOrderShoeRejectStatus(event, operation, current_status)
                else:
                    result = False
                    print("OrderShoeStatus with current_status Doesnt exist in DB")
            else:
                result = False
                print("cannot reject order status, use processEvent to set next status")
        else:
            result = False
            print("bad operation id, should be between 121 and 0")
        return result

    def setOrderShoeRejectStatus(event, operation, current_status):
        entity = (db.session.query(OrderShoeStatus)
                  .filter(OrderShoeStatus.current_status == current_status,
                  OrderShoeStatus.order_shoe_status_id == event.event_order_shoe_id)
                  .first()
                  )
        entity.current_status = operation.operation_modified_status
        entity.current_status_value = operation.operation_modified_value
        db.session.commit()
        return True


    def dbSetOrderStatus(self, event, operation, next_status=None):
        entity = (
            db.session.query(OrderStatus)
            .filter(OrderStatus.order_status_id == event.event_order_id)
            .first()
        )
        entity.order_current_status = operation.operation_modified_status
        entity.order_status_value = operation.operation_modified_value
        if next_status:
            entity.order_current_status = next_status
            entity.order_status_value = 0
        db.session.commit()
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
                    entities = (
                        db.session.query(OrderShoeStatus)
                        .filter(
                            OrderShoeStatus.order_shoe_id == event.event_order_shoe_id
                        )
                        .all()
                    )
                    for entity in entities:
                        db.session.delete(entity)
                    newEntity = OrderShoeStatus(
                        order_shoe_id=event.event_order_shoe_id,
                        current_status=next_status[0],
                        current_status_value=0,
                    )
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
            print("no next value")
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
        db.session.commit()
        return True

    def getNextOrderStatus(self, currentstatus):
        return self.orderStatusidToNode[currentstatus].getNext().getVal().getId()

    def getNextShoeStatus(self, currentStatus, currentValue, operation):
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

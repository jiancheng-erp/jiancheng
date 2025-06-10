from logger import logger
class LinkedListNode:
    def __init__(self, val=None):
        self.prev = None
        self.next = None
        self.val = val

    def setNext(self, next):
        self.next = next

    def setPrev(self, prev):
        self.prev = prev

    def getNext(self):
        return self.next

    def getPrev(self):
        return self.prev

    def getVal(self):
        return self.val


class LinkedList:

    def __init__(self, head=None) -> None:
        self.head = head

    def getHead(self):
        return self.head

    def setHead(self, head_node):
        self.head = head_node


class GraphNode:
    def __init__(self, val=None):
        self.val = val
        self.prev = []
        self.next = []

    def getVal(self):
        return self.val

    def insertNext(self, NodeToInsert):
        self.next.append(NodeToInsert)

    def insertPrev(self, NodeToInsert):
        self.prev.append(NodeToInsert)

    def getNext(self):
        return self.next

    def getPrev(self):
        return self.prev

    def __repr__(self):
        return str(self.val)

    def isMerge(self):
        return len(self.prev) > 1


class Graph:
    def __init__(self, s=None) -> None:
        self.source = s

    def getSource(self):
        return self.source

    def setSource(self, s):
        self.source = s

    def __repr__(self):
        cur = self.source
        result = []
        result.append(cur.getVal())
        logger.debug(cur.getVal())
        while cur.getNext() != []:
            for i in cur.getNext():
                logger.debug(i.getVal())
                result.append(i.getVal())
                cur = i
        return str(result)

    def printAll(self):
        cur = self.source
        logger.debug(self.BFSR(cur))

    def BFSR(self, cur):
        if cur.getNext() == []:
            return [str(cur)]
        else:
            result = []
            result.append(str(cur))
            for i in cur.getNext():
                result += self.BFSR(i)
            return result

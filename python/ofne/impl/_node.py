import uuid
from ..core import param
from .. import exceptions


class _OFnNodeImpl(object):
    def __init__(self, op, node):
        super(_OFnNodeImpl, self).__init__()
        self.__id = uuid.uuid4()
        self.__op = op
        self.__node = node
        self.__inputs = [None] * self.__op.needs()
        self.__params = param.OFnParams(self.__op.params())
        self.__outputs = set()
        self.__user_data = {}

    def __hash__(self):
        return self.__id.int

    def id(self):
        return self.__id.__str__()

    def __eq__(self, other):
        return isinstance(other, _OFnNodeImpl) and other.__hash__() == self.__hash__()

    def __neq__(self, other):
        return not self.__eq__(other)

    def node(self):
        return self.__node

    def type(self):
        return self.__op.type()

    def paramNames(self):
        return self.__params.keys()

    def getParam(self, name):
        return self.__params.getParam(name)

    def getParamValue(self, name, default=None, raw=False):
        return self.__params.get(name, default=default, raw=raw)

    def setParamValue(self, name, value):
        self.__params.set(name, value)

    def needs(self):
        return self.__op.needs()

    def packetable(self):
        return self.__op.packetable()

    def inputs(self):
        return self.__inputs[:]

    def outputs(self):
        return list(self.__outputs)

    def _connectOutput(self, nodeImpl):
        if nodeImpl in self.__outputs:
            return False

        if not self.__op.packetable():
            return False

        self.__outputs.add(nodeImpl)

        return True

    def _disconnectOutput(self, nodeImpl):
        if not nodeImpl in self.__outputs:
            return False

        self.__outputs.remove(nodeImpl)

        return True

    def __makeCycle(self, srcNodeImpl):
        srcid = srcNodeImpl.id()

        curs = list(self.__outputs)
        while (curs):
            nexts = []
            for cur in curs:
                if cur.id() == srcid:
                    return True

                nexts.extend(cur.outputs())

            curs = nexts

        return False

    def connectInput(self, index, nodeImpl):
        if index >= self.__op.needs():
            raise exceptions.OFnIndexError(index, self.__op.needs())

        if not nodeImpl.packetable():
            return False

        if self.__makeCycle(nodeImpl):
            return False

        _org = None
        if self.__inputs[index] is not None:
            _org = self.__inputs[index]

        self.__inputs[index] = nodeImpl
        self.__inputs[index]._connectOutput(self)

        if _org is not None and _org not in self.__inputs:
            _org._disconnectOutput(self)

        return True

    def disconnectInput(self, index):
        if index >= self.__op.needs():
            raise exceptions.OFnIndexError(index, self.__op.needs())

        if self.__inputs[index] is None:
            return False

        _org = self.__inputs[index]
        self.__inputs[index] = None

        if _org is not None and _org not in self.__inputs:
            _org._disconnectOutput(self)

        return True

    def disconnectAllInputs(self):
        for i in range(self.__op.needs()):
            self.disconnectInput(i)

        return True

    def operate(self, packetArray):
        return self.__op.operate(self.__params.copy(), packetArray)

    def userDataKeys(self):
        return sorted(self.__user_data.keys())

    def getUserData(self, key, default=None):
        return self.__user_data.get(key, default)

    def setUserData(self, key, value):
        self.__user_data[key] = value

    def removeUserData(self, key):
        if key in self.__user_data:
            self.__user_data.pop(key)
            return True

        return False

    def clearUserData(self):
        self.__user_data = {}

from .. import exceptions
from ..impl import _node
from . import abst


class OFnNode(abst._NodeBase):
    def __init__(self, scene, op, name=None):
        super(OFnNode, self).__init__()
        self.__scene = scene
        self.__impl = _node._OFnNodeImpl(op, self)
        self.__name = None
        self.__bypassed = False
        self.rename(name or self.type())

    def id(self):
        return self.__hash__()

    def __hash__(self):
        return self.__impl.__hash__()

    def __eq__(self, other):
        return isinstance(other, OFnNode) and other.__impl == self.__impl

    def __neq__(self, other):
        return not self.__eq__(other)

    def type(self):
        return self.__impl.type()

    def name(self):
        return self.__name

    def rename(self, newName):
        self.__name = self.__scene.getUniqueName(newName)

        return self.__name

    def paramNames(self):
        return self.__impl.paramNames()

    def getParam(self, name):
        return self.__impl.getParam(name)

    def getParamValue(self, name, default=None, raw=False):
        return self.__impl.getParamValue(name, default=default, raw=raw)

    def setParamValue(self, name, value):
        self.__impl.setParamValue(name, value)

    def needs(self):
        return self.__impl.needs()

    def packetable(self):
        return self.__impl.packetable()

    def inputs(self):
        inpts = []
        for i in self.__impl.inputs():
            if i is not None:
                i = i.node()
            inpts.append(i)

        return inpts

    def outputs(self):
        oupts = []
        for o in self.__impl.outputs():
            if o is not None:
                o = o.node()
            oupts.append(o)

        return oupts

    def connect(self, src, index=0):
        return self.__impl.connectInput(index, src.__impl)

    def disconnect(self, index=0):
        return self.__impl.disconnectInput(index)

    def disconnectAll(self):
        return self.__impl.disconnectAllInputs()

    def operate(self, packetArray):
        return self.__impl.operate(packetArray)

    def userDataKeys(self):
        return self.__impl.userDataKeys()

    def getUserData(self, key, default=None):
        return self.__impl.getUserData(key, default=default)

    def setUserData(self, key, value):
        self.__impl.setUserData(key, value)

    def removeUserData(self, key):
        return self.__impl.removeUserData(key)

    def clearUserData(self):
        self.__impl.clearUserData()

    def getByPassed(self):
        return self.__bypassed

    def setByPassed(self, b):
        self.__bypassed = b

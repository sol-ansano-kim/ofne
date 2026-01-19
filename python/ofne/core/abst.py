from ..exceptions import OFnNotImplementedError


class _NodeBase(object):
    def __init__(self):
        super(_NodeBase, self).__init__()

    def __hash__(self):
        raise OFnNotImplementedError(self, "__hash__")

    def __eq__(self, other):
        raise OFnNotImplementedError(self, "__eq__")

    def __neq__(self, other):
        raise OFnNotImplementedError(self, "__neq__")

    def id(self):
        raise OFnNotImplementedError(self, "id")

    def type(self):
        raise OFnNotImplementedError(self, "type")

    def name(self):
        raise OFnNotImplementedError(self, "name")

    def rename(self, newName):
        raise OFnNotImplementedError(self, "rename")

    def paramNames(self):
        raise OFnNotImplementedError(self, "paramNames")

    def getParam(self, name):
        raise OFnNotImplementedError(self, "getParam")

    def getParamValue(self, name, default=None):
        raise OFnNotImplementedError(self, "getParamValue")

    def setParamValue(self, name, value):
        raise OFnNotImplementedError(self, "setParamValue")

    def needs(self):
        raise OFnNotImplementedError(self, "needs")

    def packetable(self):
        raise OFnNotImplementedError(self, "packetable")

    def inputs(self):
        raise OFnNotImplementedError(self, "inputs")

    def outputs(self):
        raise OFnNotImplementedError(self, "outputs")

    def connect(self, src, index=0):
        raise OFnNotImplementedError(self, "connect")

    def disconnect(self, index=0):
        raise OFnNotImplementedError(self, "disconnect")

    def disconnectAll(self):
        raise OFnNotImplementedError(self, "disconnectAll")

    def operate(self, packetArray):
        raise OFnNotImplementedError(self, "operate")

    def userDataKeys(self):
        raise OFnNotImplementedError(self, "userDataKeys")

    def getUserData(self, key, default=None):
        raise OFnNotImplementedError(self, "getUserData")

    def setUserData(self, key, value):
        raise OFnNotImplementedError(self, "setUserData")

    def removeUserData(self, key):
        raise OFnNotImplementedError(self, "removeUserData")

    def clearUserData(self):
        raise OFnNotImplementedError(self, "clearUserDatasetUserData")


class _SceneBase(object):
    def __init__(self):
        super(_SceneBase, self).__init__()

    def createNode(self, type, name=None):
        raise OFnNotImplementedError(self, "createNode")

    def deleteNode(self, node):
        raise OFnNotImplementedError(self, "deleteNode")

    def nodes(self):
        raise OFnNotImplementedError(self, "nodes")

    def getUniqueName(self, name):
        raise OFnNotImplementedError(self, "getUniqueName")

    def load(self, data):
        raise OFnNotImplementedError(self, "load")

    def read(self, filepath):
        raise OFnNotImplementedError(self, "read")

    def write(self, filepath):
        raise OFnNotImplementedError(self, "write")

    def toDict(self, nodeBounding=None):
        raise OFnNotImplementedError(self, "toDict")

    def clear(self):
        raise OFnNotImplementedError(self, "clear")


class _OpBase(object):
    def __init__(self):
        super(_OpBase, self).__init__()

    @classmethod
    def type(cls):
        raise OFnNotImplementedError(cls, "type")

    def needs(self):
        raise OFnNotImplementedError(self, "needs")

    def params(self):
        raise OFnNotImplementedError(self, "params")

    def packetable(self):
        raise OFnNotImplementedError(self, "packetable")

    def operate(self, params, packetArray):
        raise OFnNotImplementedError(self, "operate")


class _OpManagerBase(object):
    def __init__(self):
        super(_OpManagerBase, self).__init__()

    def reloadPlugins(self):
        raise OFnNotImplementedError(self, "reloadPlugins")

    def listOps(self):
        raise OFnNotImplementedError(self, "listOps")

    def getOp(self, opName):
        raise OFnNotImplementedError(self, "getOp")

    def registerOp(self, op):
        raise OFnNotImplementedError(self, "registerOp")

    def deregisterOp(self, op):
        raise OFnNotImplementedError(self, "deregisterOp")


class _PacketBase(object):
    def __init__(self):
        super(_PacketBase, self).__init__()

    def copy(self):
        raise OFnNotImplementedError(self, "copy")

    def metadata(self):
        raise OFnNotImplementedError(self, "metadata")

    def data(self):
        raise OFnNotImplementedError(self, "data")


class _PacketArrayBase(object):
    def __init__(self):
        super(_PacketArrayBase, self).__init__()

    def count(self):
        raise OFnNotImplementedError(self, "count")

    def packet(self, index):
        raise OFnNotImplementedError(self, "packet")


class _ParamBase(object):
    def __init__(self):
        super(_ParamBase, self).__init__()

    def default(self):
        raise OFnNotImplementedError(self, "default")

    def get(self):
        raise OFnNotImplementedError(self, "get")

    def set(self, value):
        raise OFnNotImplementedError(self, "set")

    def type(self):
        raise OFnNotImplementedError(self, "type")

    def isValid(self, value):
        raise OFnNotImplementedError(self, "isValid")

    def copy(self):
        raise OFnNotImplementedError(self, "copy")

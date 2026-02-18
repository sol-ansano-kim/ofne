from . import abst
from . import node
from . import opManager
from ..impl import _scene


class OFnScene(abst._SceneBase):
    def __init__(self):
        super(OFnScene, self).__init__()
        self.__impl = _scene._OFnSceneImpl(node.OFnNode, opManager.manager)

    def createNode(self, type, name=None):
        return self.__impl.createNode(type, name=name)

    def deleteNode(self, node):
        return self.__impl.deleteNode(node)

    def nodes(self):
        return self.__impl.nodes()

    def getUniqueName(self, name):
        return self.__impl.getUniqueName(name)

    def load(self, data):
        return self.__impl.load(data)

    def read(self, filepath):
        return self.__impl.read(filepath)

    def write(self, filepath):
        return self.__impl.write(filepath)

    def toDict(self, nodeBounding=None):
        return self.__impl.toDict(nodeBounding=nodeBounding)

    def clear(self):
        return self.__impl.clear()

    def misc(self):
        return self.__impl.misc()

    def setMisc(self, misc):
        self.__impl.setMisc(misc)

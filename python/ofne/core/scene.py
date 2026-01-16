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
        return self.__impl.getUniqueName()

    def read(self, filepath):
        pass

    def write(self, filepath):
        self.__impl.write(filepath)

    def clear(self):
        return self.__impl.clear()

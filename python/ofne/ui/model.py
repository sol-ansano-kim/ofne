import os
from ..core import node
from PySide6 import QtCore


class OFnUIScene(QtCore.QObject):
    nodeCreated = QtCore.Signal(node.OFnNode)
    nodeDeleted = QtCore.Signal(str)
    nodeConnected = QtCore.Signal(tuple)
    nodeDisconnected = QtCore.Signal(tuple)

    def __init__(self, scene):
        super(OFnUIScene, self).__init__()
        self.__scene = scene
        self.__connections = set()

    def saveTo(self, filepath):
        self.__scene.write(filepath)

    def createNode(self, op_type):
        nn = self.__scene.createNode(op_type)
        if nn:
            self.nodeCreated.emit(nn)

    def deleteNode(self, node):
        hashes = []
        nh = node.id()
        for i, inn in enumerate(node.inputs()):
            if inn is None:
                continue

            exh = (inn.id(), nh, i)
            hashes.append(exh)

        for opn in node.outputs():
            for i, opin in enumerate(opn.inputs()):
                if opin == node:
                    exh = (nh, opn.id(), i)
                    hashes.append(exh)

        if self.__scene.deleteNode(node):
            for exh in hashes:
                self.__connections.remove(exh)
                self.nodeDisconnected.emit(exh)

            self.nodeDeleted.emit(str(nh))

    def connect(self, src, dst, index):
        exh = None
        inputs = dst.inputs()
        if inputs[index] is not None:
            exh = (inputs[index].id(), dst.id(), index)

        res = dst.connect(src, index=index)
        if res:
            neh = (src.id(), dst.id(), index)
            self.__connections.add(neh)

            if exh:
                self.__connections.remove(exh)
                self.nodeDisconnected.emit(exh)

            self.nodeConnected.emit(neh)

        return res

    def disconnect(self, dst, index):
        exh = None
        inputs = dst.inputs()

        if inputs[index] is None:
            return False

        if not dst.disconnect(index):
            return False

        exh = (inputs[index].id(), dst.id(), index)
        self.__connections.remove(exh)
        self.nodeDisconnected.emit(exh)

        return True

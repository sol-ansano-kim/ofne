import os
from ..core import node
from ..core import scene
from PySide6 import QtCore


class OFnUIScene(QtCore.QObject):
    nodeCreated = QtCore.Signal(node.OFnNode)
    nodeDeleted = QtCore.Signal(str)
    nodeConnected = QtCore.Signal(tuple)
    nodeDisconnected = QtCore.Signal(tuple)

    def __init__(self):
        super(OFnUIScene, self).__init__()
        self.__filepath = None
        self.__scene = scene.OFnScene()
        self.__connections = set()

    def read(self, filepath):
        res = self.__scene.read(filepath)

        if res:
            for n in self.__scene.nodes():
                self.nodeCreated.emit(n)

            for n in self.__scene.nodes():
                for index, inp in enumerate(n.inputs()):
                    if inp is None:
                        continue

                    h = (inp.id(), n.id(), index)
                    self.__connections.add(h)
                    self.nodeConnected.emit(h)

            self.__filepath = os.path.normpath(filepath)

        return res

    def filepath(self):
        return self.__filepath

    def save(self):
        return self.__scene.write(self.__filepath)

    def saveTo(self, filepath):
        if self.__scene.write(filepath):
            self.__filepath = os.path.normpath(filepath)
            return True

        return False

    def createNode(self, opType):
        nn = self.__scene.createNode(opType)
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

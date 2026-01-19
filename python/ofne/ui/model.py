import os
from ..core import node
from ..core import scene
from PySide6 import QtCore
from PySide6 import QtGui


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
            self.__emitAllContents()
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

    def copyToClipboard(self, nodeBounding):
        if self.__scene:
            d = self.__scene.toDict(nodeBounding=nodeBounding)
            QtGui.QGuiApplication.clipboard().setText(d.__repr__())

    def loadFromClipboard(self, center=None):
        txt = QtGui.QGuiApplication.clipboard().text()
        d = {}
        try:
            d = eval(txt)
        except:
            return

        if not isinstance(d, dict) or "nodes" not in d or "connections" not in d:
            return

        if center:
            l = None
            r = None
            t = None
            b = None

            for n in d["nodes"]:
                ud = n.get("userData")
                if "ui:pos" in ud:
                    x, y = ud["ui:pos"]
                    if l is None:
                        l = x
                    else:
                        l = min(l, x)
                    if r is None:
                        r = x
                    else:
                        r = max(r, x)
                    if t is None:
                        t = y
                    else:
                        t = min(t, y)
                    if b is None:
                        b = y
                    else:
                        b = max(b, y)

            print(l, r, t, b)
            if l is not None and r is not None and t is not None and b is not None:
                cx = (l + r) * 0.5
                cy = (t + b) * 0.5

                for n in d["nodes"]:
                    ud = n.get("userData")
                    if "ui:pos" in ud:
                        x, y = ud["ui:pos"]
                        ud["ui:pos"] = (x - cx + center.x(), y - cy + center.y())

        if self.__scene.load(d):
            self.__emitAllContents()

    def __emitAllContents(self):
        for n in self.__scene.nodes():
            self.nodeCreated.emit(n)

        for n in self.__scene.nodes():
            for index, inp in enumerate(n.inputs()):
                if inp is None:
                    continue

                h = (inp.id(), n.id(), index)
                self.__connections.add(h)
                self.nodeConnected.emit(h)

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

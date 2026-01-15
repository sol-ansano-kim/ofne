from PySide6 import QtCore


class OFnUIScene(QtCore.QObject):
    connected = QtCore.Signal(tuple)
    disconnected = QtCore.Signal(tuple)

    def __init__(self, scene):
        super(OFnUIScene, self).__init__()
        self.__scene = scene
        self.__connections = set()

    def toDict(self):
        return self.__scene.toDict()

    def createNode(self, op_type):
        return self.__scene.createNode(op_type)

    def deleteNode(self, node):
        hashes = []
        nh = node.__hash__()
        for i, inn in enumerate(node.inputs()):
            if inn is None:
                continue

            exh = (inn.__hash__(), nh, i)
            hashes.append(exh)

        for opn in node.outputs():
            for i, opin in enumerate(opn.inputs()):
                if opin == node:
                    exh = (nh, opn.__hash__(), i)
                    hashes.append(exh)

        if self.__scene.deleteNode(node):
            for exh in hashes:
                self.__connections.remove(exh)
                self.disconnected.emit(exh)

            return True

        return False

    def connect(self, src, dst, index):
        exh = None
        inputs = dst.inputs()
        if inputs[index] is not None:
            exh = (inputs[index].__hash__(), dst.__hash__(), index)

        res = dst.connect(src, index=index)
        if res:
            neh = (src.__hash__(), dst.__hash__(), index)
            self.__connections.add(neh)

            if exh:
                self.__connections.remove(exh)
                self.disconnected.emit(exh)

            self.connected.emit(neh)

        return res

    def disconnect(self, dst, index):
        exh = None
        inputs = dst.inputs()

        if inputs[index] is None:
            return False

        if not dst.disconnect(index):
            return False

        exh = (inputs[index].__hash__(), dst.__hash__(), index)
        self.__connections.remove(exh)
        self.disconnected.emit(exh)

        return True

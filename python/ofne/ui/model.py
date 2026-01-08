from PySide6 import QtCore


class OFnUIScene(QtCore.QObject):
    connected = QtCore.Signal(tuple)
    disconnected = QtCore.Signal(tuple)

    def __init__(self, scene):
        super(OFnUIScene, self).__init__()
        self.__scene = scene
        self.__nodes = {}
        self.__connections = set()

    def createNode(self, op_type):
        new_node = self.__scene.createNode(op_type)
        if new_node:
            self.__nodes[new_node.__hash__()] = new_node

        return new_node

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

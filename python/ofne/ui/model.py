import os
import uuid
import numpy as np
from ..core import abst
from ..core import param
from ..core import node
from ..core import resource
from ..core.scene import OFnScene
from ..graph.scene import OFnGraphScene
from PySide6 import QtCore
from PySide6 import QtGui


class OFnUINote(abst._NodeBase):
    def __init__(self):
        super(OFnUINote, self).__init__()
        self.__id = uuid.uuid4()
        self.__x = 0
        self.__y = 0
        self.__w = 100
        self.__h = 100
        self.__params = param.OFnParams(
            [
                param.OFnParamCode("note", default="")
            ]
        )

    def toDict(self):
        return {
            "id": self.id(),
            "pos": (self.__x, self.__y),
            "size": (self.__w, self.__h),
            "note": self.getParamValue("note")
        }

    def __hash__(self):
        return self.__id.int

    def id(self):
        return self.__id.__str__()

    def __eq__(self, other):
        return isinstance(other, OFnUINote) and other.id() == self.__id

    def __neq__(self, other):
        return not self.__eq__(other)

    def pos(self):
        return (self.__x, self.__y)

    def setPos(self, x, y):
        self.__x = x
        self.__y = y

    def size(self):
        return (self.__w, self.__h)

    def setSize(self, w, h):
        self.__w = w
        self.__h = h

    def paramNames(self):
        return self.__params.keys()

    def getParam(self, name):
        return self.__params.getParam(name)

    def getParamValue(self, name, default=None, raw=False):
        return self.__params.get(name, default=default, raw=raw)

    def setParamValue(self, name, value):
        self.__params.set(name, value)


class OFnUIScene(QtCore.QObject):
    nodeCreated = QtCore.Signal(node.OFnNode)
    nodeDeleted = QtCore.Signal(str)
    noteCreated = QtCore.Signal(OFnUINote)
    noteDeleted = QtCore.Signal(str)
    nodeConnected = QtCore.Signal(tuple)
    nodeDisconnected = QtCore.Signal(tuple)
    evaluationFinished = QtCore.Signal()

    def __init__(self):
        super(OFnUIScene, self).__init__()
        os.environ["OFSN"] = ""
        self.__filepath = None
        self.__scene = OFnScene()
        self.__scene_graph = OFnGraphScene(self.__scene)
        self.__notes = {}
        self.__connections = set()

    def read(self, filepath):
        res = self.__scene.read(filepath)

        if res:
            self.__emitAllContents()
            self.__filepath = os.path.normpath(filepath)
            os.environ["OFSN"] = os.path.normpath(os.path.dirname(os.path.abspath(self.__filepath)))

            for nd in self.__scene.misc().get("notes", []):
                self.createNote(nd)

        return res

    def filepath(self):
        return self.__filepath

    def save(self):
        return self.__scene.write(self.__filepath)

    def saveTo(self, filepath):
        notes = []
        misc = {"notes": notes}
        for n in self.__notes.values():
            notes.append(n.toDict())

        self.__scene.setMisc(misc)
        if self.__scene.write(filepath):
            self.__filepath = os.path.normpath(filepath)
            os.environ["OFSN"] = os.path.normpath(os.path.dirname(os.path.abspath(self.__filepath)))

            return True

        return False

    def copyToClipboard(self, nodeBounding, noteBounding):
        if self.__scene:
            if nodeBounding:
                d = self.__scene.toDict(nodeBounding=nodeBounding)
            else:
                d = {"nodes": [], "connections": []}

            new_notes = []
            for note in noteBounding:
                new_notes.append(note.toDict())
            d["misc"] = {"notes": new_notes}

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

            def _updateRect(x, y):
                nonlocal l
                nonlocal r
                nonlocal t
                nonlocal b

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

            for n in d["nodes"]:
                ud = n.get("userData")
                if "ui:pos" in ud:
                    _updateRect(*ud["ui:pos"])

            for n in d.get("misc", {}).get("notes", []):
                _updateRect(*n["pos"])

            if l is not None and r is not None and t is not None and b is not None:
                cx = (l + r) * 0.5
                cy = (t + b) * 0.5

                for n in d["nodes"]:
                    ud = n.get("userData")
                    if "ui:pos" in ud:
                        x, y = ud["ui:pos"]
                        ud["ui:pos"] = (x - cx + center.x(), y - cy + center.y())

                for n in d.get("misc", {}).get("notes", []):
                    x, y = n["pos"]
                    n["pos"] = (x - cx + center.x(), y - cy + center.y())

        if self.__scene.load(d):
            self.__emitAllContents()

        for n in d.get("misc", {}).get("notes", []):
            self.createNote(n)

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

    def createNode(self, opType, paramDict=None, userData=None):
        nn = self.__scene.createNode(opType)
        if nn:
            params = set(nn.paramNames())
            for k, v in (paramDict or {}).items():
                if k in params:
                    nn.setParamValue(k, v)

            for k, v in (userData or {}).items():
                nn.setUserData(k, v)

            self.nodeCreated.emit(nn)

    def createNote(self, data):
        nt = OFnUINote()
        pos = data.get("pos")
        if pos:
            nt.setPos(*pos)

        size = data.get("size")
        if size:
            nt.setSize(*size)

        note = data.get("note")
        if note:
            nt.setParamValue("note", note)

        self.__notes[nt.id()] = nt
        self.noteCreated.emit(nt)

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

            self.nodeDeleted.emit(nh)

    def deleteNote(self, note):
        if note.id() in self.__notes:
            self.__notes.pop(note.id())
            self.noteDeleted.emit(note.id())

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

    def evaluate(self):
        target_nodes = [x for x in self.__scene.nodes() if not x.packetable()]
        if target_nodes:
            self.__scene_graph.evaluate(target_nodes)
            self.evaluationFinished.emit()

    def failedNodes(self):
        return self.__scene_graph.failedNodes()

    def errorMessage(self, node):
        return self.__scene_graph.errorMessage(node)


class OFnUIViewResource(object):
    def __init__(self):
        super(OFnUIViewResource, self).__init__()
        self.__empty_image = QtGui.QImage(640, 640, QtGui.QImage.Format_RGBA32FPx4)
        self.__empty_arr = np.zeros((640, 640, 4), dtype=np.float32)
        self.__empty_arr[..., 3] = 1.0
        self.__empty_image.fill(QtGui.QColor(0, 0, 0))
        self.__latest_stamp = None
        self.__image = self.__empty_image
        self.__arr = self.__empty_arr

    def isDirty(self):
        stamp = resource.OFnViewResource().stamp()
        if stamp == self.__latest_stamp:
            return False

        self.__latest_stamp = stamp
        self.__readResource()

        return True

    def image(self):
        return self.__image

    def getPixelValues(self, x, y):
        colors = []

        shape = self.__arr.shape
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2):
                yy = y + dy
                xx = x + dx

                if yy < 0 or yy >= shape[0] or xx < 0 or xx >= shape[1]:
                    colors.append((0, 0, 0, 1))
                else:
                    colors.append(tuple([float(x) for x in self.__arr[yy, xx]]))

        return colors

    def __readResource(self):
        packet = resource.OFnViewResource().packet()
        arr = packet.data()

        if len(arr.shape) == 3:
            h, w, c = arr.shape

            rgba = None
            if c == 4:
                rgba = arr

            elif c == 3:
                alpha = np.ones((h, w, 1), dtype=arr.dtype)
                rgba = np.concatenate([arr, alpha], axis=-1)

            elif c == 2:
                rgba = np.concatenate([arr[..., 0:1], arr[..., 1:2], np.zeros((h, w, 1), dtype=arr.dtype), np.ones((h, w, 1), dtype=arr.dtype)], axis=-1)

            elif c == 1:
                rgba  = np.concatenate([np.repeat(arr, 3, axis=-1), np.ones((h, w, 1), dtype=arr.dtype)], axis=-1)

            elif c > 4:
                rgba = arr[..., :4]

            if rgba is not None:
                self.__image = QtGui.QImage(rgba.data, w, h, rgba.strides[0], QtGui.QImage.Format.Format_RGBA32FPx4)
                self.__arr = rgba
            else:
                self.__image = self.__empty_image
                self.__arr = self.__empty_arr
        else:
            self.__image = self.__empty_image
            self.__arr = self.__empty_arr

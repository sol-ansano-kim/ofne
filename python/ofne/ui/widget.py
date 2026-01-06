from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

from ..core.opManager import manager as op_manager
from ..core.scene import OFnScene


NODE_DEFAULT_WIDTH = 100
NODE_DEFAULT_HEGIHT = 30


class OFnUIOpSelector(QtWidgets.QLineEdit):
    OpSelected = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(OFnUIOpSelector, self).__init__(parent=parent)
        self.editingFinished.connect(self.__editingFinished)
        self.hide()
        self.blockSignals(True)

    def keyPressEvent(self, evnt):
        if evnt.key() == QtCore.Qt.Key_Escape:
            self.blockSignals(True)
            self.setText("")
            self.hide()

        super(OFnUIOpSelector, self).keyPressEvent(evnt)

    def __updateCompleter(self):
        comp = QtWidgets.QCompleter(op_manager.listOps())
        comp.popup().setStyleSheet("QListView { font-size : 13px; border: 1px solid #8B8B8B; color: #EDEDED; background-color: #222222; }")
        comp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        comp.setFilterMode(QtCore.Qt.MatchContains)
        comp.setModelSorting(QtWidgets.QCompleter.CaseInsensitivelySortedModel)
        self.setCompleter(comp)

    def show(self, pos):
        self.setText("")
        self.blockSignals(False)
        self.move(pos)
        self.setFocus(QtCore.Qt.PopupFocusReason)
        self.__updateCompleter()
        super(OFnUIOpSelector, self).show()

    def __editingFinished(self):
        self.OpSelected.emit(self.text())
        self.blockSignals(True)
        self.hide()


class OFnUINodeBody(QtWidgets.QGraphicsPathItem):
    def __init__(self, needs, out, parent=None):
        super(OFnUINodeBody, self).__init__(parent=parent)
        self.__normal_brush = QtGui.QBrush(QtGui.QColor(51, 49, 58), QtCore.Qt.SolidPattern)
        self.__selected_brush = QtGui.QBrush(QtGui.QColor(81, 83, 102), QtCore.Qt.SolidPattern)
        self.__normal_pen = QtGui.QPen(QtCore.Qt.gray)
        self.__selected_pen = QtGui.QPen(QtCore.Qt.white)
        rect_height = NODE_DEFAULT_HEGIHT * max(needs, 1)
        path = QtGui.QPainterPath()
        path.addRoundedRect(0, 0, NODE_DEFAULT_WIDTH, rect_height, 5, 5)
        self.setPath(path)

    def paint(self, painter, option, widget):
        brush = self.__normal_brush
        pen = self.__normal_pen
        if self.isSelected():
            brush = self.__selected_brush
            pen = self.__selected_pen

        self.setBrush(brush)
        self.setPen(pen)

        super(OFnUINodeBody, self).paint(painter, option, widget)


class OFnUINodeLabel(QtWidgets.QGraphicsSimpleTextItem):
    def __init__(self, name, parent=None):
        super(OFnUINodeLabel, self).__init__(parent=parent)
        self.setLabel(name)
        self.__normal_pen = QtGui.QPen(QtCore.Qt.gray)
        self.__selected_pen = QtGui.QPen(QtCore.Qt.white)

    def setLabel(self, name):
        frect = QtGui.QFontMetrics(self.font()).boundingRect(name)
        self.setPos((NODE_DEFAULT_WIDTH - frect.width()) * 0.5, 0)
        self.setText(name)

    def paint(self, painter, option, widget):
        self.setPen(self.__selected_pen if self.isSelected() else self.__normal_pen)
        super(OFnUINodeLabel, self).paint(painter, option, widget)


class OFnUIPort(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, parent=None):
        super(OFnUIPort, self).__init__(parent=parent)
        self.__normal_brush = QtGui.QBrush(QtGui.QColor(102, 208, 153), QtCore.Qt.SolidPattern)
        self.setRect(0, 0, NODE_DEFAULT_HEGIHT * 0.55, NODE_DEFAULT_HEGIHT * 0.5)
        self.setBrush(self.__normal_brush)
        self.setPen(QtCore.Qt.NoPen)


class OFnUINodeItem(QtWidgets.QGraphicsItemGroup):
    def __init__(self, node, parent=None):
        super(OFnUINodeItem, self).__init__(parent=parent)
        self.__node = node

        self.setFlags(QtWidgets.QGraphicsRectItem.ItemIsMovable | QtWidgets.QGraphicsRectItem.ItemIsSelectable | QtWidgets.QGraphicsRectItem.ItemIsFocusable)

        # label
        self.__label = OFnUINodeLabel(node.name(), parent=self)
        self.addToGroup(self.__label)

        body_start = self.__label.boundingRect().height() + 6

        # port
        for i in range(self.__node.needs()):
            port = OFnUIPort(parent=self)
            prect = port.rect()
            port.setPos(prect.width() * -0.5, body_start + (NODE_DEFAULT_HEGIHT * (i + 0.5)) - (prect.height() * 0.5))

        if self.__node.packetable():
            port = OFnUIPort(parent=self)
            prect = port.rect()
            port.setPos(NODE_DEFAULT_WIDTH + prect.width() * -0.5, body_start + (NODE_DEFAULT_HEGIHT * (0.5)) - (prect.height() * 0.5))

        # body
        rect_height = NODE_DEFAULT_HEGIHT * max(node.needs(), 1)
        self.__body = OFnUINodeBody(self.__node.needs(), self.__node.packetable(), parent=self)
        self.__body.setPos(0, body_start)
        self.addToGroup(self.__body)

    def paint(self, painter, option, widget):
        pass

    def node(self):
        return self.__node

    def mouseReleaseEvent(self, event):
        super(OFnUINodeItem, self).mouseReleaseEvent(event)


class OFnUINodeGraph(QtWidgets.QGraphicsView):
    def __init__(self, scene=None, parent=None):
        super(OFnUINodeGraph, self).__init__(parent=parent)
        self.__scene = scene if isinstance(scene, OFnScene) else OFnScene()

        self.__graphic_scene = QtWidgets.QGraphicsScene()
        self.setScene(self.__graphic_scene)

        self.__op_selector = OFnUIOpSelector(parent=self)
        self.__op_selector.OpSelected.connect(self.__onOpCreateRequested)

    def __onOpCreateRequested(self, name):
        n = self.__scene.createNode(name)
        if n is not None:
            item = OFnUINodeItem(n)
            self.__graphic_scene.addItem(item)
            pos = self.mapToScene(self.mapFromGlobal(QtGui.QCursor.pos()))
            item.setPos(
                pos.x() - item.boundingRect().width() * 0.5,
                pos.y() - item.boundingRect().height() * 0.5,
            )

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            self.__op_selector.show(self.mapFromGlobal(QtGui.QCursor.pos()))

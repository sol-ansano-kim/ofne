import enum
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

from ..core.opManager import manager as op_manager
from ..core.scene import OFnScene
from ..core.node import OFnNode


NODE_DEFAULT_WIDTH = 100
NODE_DEFAULT_HEGIHT = 30


class PortDirection(enum.Enum):
    Input = 0
    Output = 1


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
        self.__normal_pen.setWidth(2)
        self.__selected_pen.setWidth(4)
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


class OFnUIPort(QtCore.QObject, QtWidgets.QGraphicsEllipseItem):
    portClicked = QtCore.Signal(QtWidgets.QGraphicsItem, PortDirection, int)

    def __init__(self, direction, index, parent=None):
        QtCore.QObject.__init__(self)
        QtWidgets.QGraphicsEllipseItem.__init__(self, parent=parent)
        self.__index = index
        self.__direction = direction
        self.__hover = False
        self.__normal_brush = QtGui.QBrush(QtGui.QColor(50, 208, 103), QtCore.Qt.SolidPattern)
        self.__hover_brush = QtGui.QBrush(QtGui.QColor(102, 228, 153), QtCore.Qt.SolidPattern)
        self.__hover_pen = QtGui.QPen(QtCore.Qt.white)
        self.__hover_pen.setWidth(2)
        self.__parent = parent
        self.setRect(0, 0, NODE_DEFAULT_HEGIHT * 0.5, NODE_DEFAULT_HEGIHT * 0.5)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setBrush(self.__normal_brush)
        self.setPen(QtCore.Qt.NoPen)
        self.setAcceptHoverEvents(True)

    def centerPos(self):
        return self.__parent.mapToScene(self.pos() + self.boundingRect().center())

    def index(self):
        return self.__index

    def direction(self):
        return self.__direction

    def hoverEnterEvent(self, event):
        self.__hover = True
        self.setScale(1.2)

    def hoverLeaveEvent(self, event):
        self.__hover = False
        self.setScale(1)

    def paint(self, painter, option, widget):
        brush = self.__normal_brush
        pen = QtCore.Qt.NoPen
        if self.isSelected() or self.__hover:
            brush = self.__hover_brush
            pen = self.__hover_pen

        self.setBrush(brush)
        self.setPen(pen)

        super(OFnUIPort, self).paint(painter, option, widget)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.portClicked.emit(self, self.__direction, self.__index)


class OFnUINodeItem(QtCore.QObject, QtWidgets.QGraphicsItemGroup):
    portClicked = QtCore.Signal(OFnNode, QtWidgets.QGraphicsItem, PortDirection, int)

    def __init__(self, node, parent=None):
        QtCore.QObject.__init__(self)
        QtWidgets.QGraphicsItemGroup.__init__(self, parent=parent)
        self.setHandlesChildEvents(False)
        self.__node = node

        self.setFlags(QtWidgets.QGraphicsRectItem.ItemIsMovable | QtWidgets.QGraphicsRectItem.ItemIsSelectable)

        # label
        self.__label = OFnUINodeLabel(node.name(), parent=self)
        self.addToGroup(self.__label)

        body_start = self.__label.boundingRect().height() + 6

        # body
        rect_height = NODE_DEFAULT_HEGIHT * max(node.needs(), 1)
        self.__body = OFnUINodeBody(self.__node.needs(), self.__node.packetable(), parent=self)
        self.__body.setPos(0, body_start)
        self.addToGroup(self.__body)

        # port
        for i in range(self.__node.needs()):
            port = OFnUIPort(PortDirection.Input, i, parent=self)
            prect = port.rect()
            port.setPos(prect.width() * -0.5, body_start + (NODE_DEFAULT_HEGIHT * (i + 0.5)) - (prect.height() * 0.5))
            self.addToGroup(port)
            port.portClicked.connect(self.__onPortClicked)

        if self.__node.packetable():
            port = OFnUIPort(PortDirection.Output, 0, parent=self)
            prect = port.rect()
            port.setPos(NODE_DEFAULT_WIDTH + prect.width() * -0.5, body_start + (NODE_DEFAULT_HEGIHT * (0.5)) - (prect.height() * 0.5))
            self.addToGroup(port)
            port.portClicked.connect(self.__onPortClicked)

    def __onPortClicked(self, item, direction, index):
        self.portClicked.emit(self.__node, item, direction, index)

    def paint(self, painter, option, widget):
        # cancel focus drawing
        pass

    def node(self):
        return self.__node


class OFnUIConnector(QtWidgets.QGraphicsPathItem):
    def __init__(self, start_item, direction, parent=None):
        super(OFnUIConnector, self).__init__(parent=parent)
        self.__start_item = start_item
        self.__normal_pen = QtGui.QPen(QtCore.Qt.white)
        self.__normal_pen.setWidth(2)
        self.setPen(self.__normal_pen)

    def updatePos(self, pos):
        path = QtGui.QPainterPath()
        st_pos = self.mapFromScene(self.__start_item.centerPos())
        path.moveTo(st_pos)
        path.cubicTo(st_pos, st_pos, pos)
        self.setPath(path)


class OFnUINodeGraph(QtWidgets.QGraphicsView):
    def __init__(self, scene=None, parent=None):
        super(OFnUINodeGraph, self).__init__(parent=parent)
        self.setMouseTracking(True)

        pal = self.palette()
        pal.setColor(QtGui.QPalette.Window, QtGui.QColor(25, 25, 25))
        pal.setColor(QtGui.QPalette.Text, QtGui.QColor(220, 220, 220))
        self.setPalette(pal)

        self.__connector = None

        self.__scene = scene if isinstance(scene, OFnScene) else OFnScene()

        self.__graphic_scene = QtWidgets.QGraphicsScene()
        self.setScene(self.__graphic_scene)

        self.__op_selector = OFnUIOpSelector(parent=self)
        self.__op_selector.OpSelected.connect(self.__onOpCreateRequested)

    def __showConnector(self, node, item, direction, index):
        if self.__connector is None:
            self.__connector = OFnUIConnector(item, direction)
            self.__graphic_scene.addItem(self.__connector)

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

            item.portClicked.connect(self.__showConnector)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            self.__op_selector.show(self.mapFromGlobal(QtGui.QCursor.pos()))

    def mousePressEvent(self, event):
        if self.__connector:
            self.__graphic_scene.removeItem(self.__connector)
            self.__connector = None

        super(OFnUINodeGraph, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.__connector:
            self.__connector.updatePos(self.mapToScene(self.mapFromGlobal(QtGui.QCursor.pos())))

        super(OFnUINodeGraph, self).mouseMoveEvent(event)
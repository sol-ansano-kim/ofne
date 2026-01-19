import enum
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

from ..core.opManager import manager as op_manager
from . import model


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
        self.__normal_brush = QtGui.QBrush(QtCore.Qt.gray)
        self.__selected_brush = QtGui.QBrush(QtCore.Qt.white)
        self.setPen(QtCore.Qt.NoPen)

    def setLabel(self, name):
        frect = QtGui.QFontMetrics(self.font()).boundingRect(name)
        self.setPos((NODE_DEFAULT_WIDTH - frect.width()) * 0.5, 0)
        self.setText(name)

    def paint(self, painter, option, widget):
        self.setBrush(self.__selected_brush if self.isSelected() else self.__normal_brush)
        super(OFnUINodeLabel, self).paint(painter, option, widget)


class OFnUIPort(QtCore.QObject, QtWidgets.QGraphicsEllipseItem):
    portClicked = QtCore.Signal(QtWidgets.QGraphicsItem)

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

    def node(self):
        if isinstance(self.__parent, OFnUINodeItem):
            return self.__parent.node()

        return None

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
            self.portClicked.emit(self)


class OFnUINodeItem(QtCore.QObject, QtWidgets.QGraphicsItemGroup):
    portClicked = QtCore.Signal(QtWidgets.QGraphicsItem)

    def __init__(self, node, parent=None):
        QtCore.QObject.__init__(self)
        QtWidgets.QGraphicsItemGroup.__init__(self, parent=parent)
        self.setHandlesChildEvents(False)
        self.__node = node
        self.__inputs = []
        self.__output = None

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
            port.portClicked.connect(self.portClicked.emit)
            self.__inputs.append(port)

        if self.__node.packetable():
            port = OFnUIPort(PortDirection.Output, 0, parent=self)
            prect = port.rect()
            port.setPos(NODE_DEFAULT_WIDTH + prect.width() * -0.5, body_start + (NODE_DEFAULT_HEGIHT * (0.5)) - (prect.height() * 0.5))
            self.addToGroup(port)
            port.portClicked.connect(self.portClicked.emit)
            self.__output = port

    def input(self, index):
        return self.__inputs[index]

    def output(self):
        return self.__output

    def paint(self, painter, option, widget):
        # cancel focus drawing
        pass

    def node(self):
        return self.__node


class OFnUIConnection(QtWidgets.QGraphicsPathItem):
    def __init__(self, src, dst, parent=None):
        super(OFnUIConnection, self).__init__(parent=parent)
        self.setFlags(QtWidgets.QGraphicsRectItem.ItemIsSelectable)
        self.__src = src
        self.__dst = dst

        self.__normal_pen = QtGui.QPen(QtGui.Qt.gray)
        self.__normal_pen.setWidth(2)
        self.__selected_pen = QtGui.QPen(QtGui.Qt.white)
        self.__selected_pen.setWidth(2)

    def updatePos(self):
        st_pos = self.mapFromScene(self.__src.centerPos()) + QtCore.QPoint(self.__src.boundingRect().width() * 0.5, 0)
        ed_pos = self.mapFromScene(self.__dst.centerPos()) - QtCore.QPoint(self.__src.boundingRect().width() * 0.5, 0)
        c1 = QtCore.QPoint(st_pos.x() + 50, st_pos.y())
        c2 = QtCore.QPoint(ed_pos.x() - 50, ed_pos.y())
        path = QtGui.QPainterPath()
        path.moveTo(st_pos)
        path.cubicTo(c1, c2, ed_pos)
        self.setPath(path)

    def paint(self, painter, option, widget):
        self.updatePos()

        painter.save()
        painter.setPen(self.__selected_pen if self.isSelected() else self.__normal_pen)
        painter.drawPath(self.path())
        painter.restore()

class OFnUIConnector(QtWidgets.QGraphicsPathItem):
    def __init__(self, item, direction, parent=None):
        super(OFnUIConnector, self).__init__(parent=parent)
        self.__direction = direction
        self.__item = item
        pen = QtGui.QPen(QtGui.Qt.white)
        pen.setStyle(QtCore.Qt.DashLine)
        pen.setWidth(2)
        self.setPen(pen)

    def item(self):
        return self.__item

    def setEndPos(self, pos):
        factor = -1 if self.__direction == PortDirection.Input else 1
        path = QtGui.QPainterPath()
        st_pos = self.mapFromScene(self.__item.centerPos()) + (QtCore.QPoint(self.__item.boundingRect().width() * 0.5, 0) * factor)
        path.moveTo(st_pos)
        c1 = QtCore.QPoint(st_pos.x() + 50 * factor, st_pos.y())
        c2 = QtCore.QPoint(pos.x() + 50 * -factor, pos.y())
        path.cubicTo(c1, c2, pos)

        self.setPath(path)


class OFnUINodeGraph(QtWidgets.QGraphicsView):
    sceneFilepathChanged = QtCore.Signal(str)

    def __init__(self, scene=None, parent=None):
        super(OFnUINodeGraph, self).__init__(parent=parent)
        self.__nodes = {}
        self.__connections = {}
        self.__connector = None
        self.__move_scene = False
        self.__old_scene_pos = None
        self.__scene = None
        self.__graphic_scene = None

        self.__op_selector = OFnUIOpSelector(parent=self)
        self.__op_selector.OpSelected.connect(self.__onOpCreateRequested)

        pal = self.palette()
        pal.setColor(QtGui.QPalette.Window, QtGui.QColor(25, 25, 25))
        pal.setColor(QtGui.QPalette.Text, QtGui.QColor(220, 220, 220))
        self.setPalette(pal)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)

        self.newScene()

    def newScene(self):
        self.__acceptScene(model.OFnUIScene())

    def open(self, filepath):
        self.newScene()

        if self.__scene.read(filepath):
            self.fit()
            self.sceneFilepathChanged.emit(self.__scene.filepath())

    def __acceptScene(self, scene):
        self.__nodes = {}
        self.__connections = {}

        old_scene = self.__scene
        self.__scene = scene
        self.__scene.nodeCreated.connect(self.__onNodeCreated)
        self.__scene.nodeDeleted.connect(self.__onDeleteNode)
        self.__scene.nodeConnected.connect(self.__onConnected)
        self.__scene.nodeDisconnected.connect(self.__onDisconnected)

        old_gscene = self.__graphic_scene
        self.__graphic_scene = QtWidgets.QGraphicsScene()
        self.setScene(self.__graphic_scene)
        self.__graphic_scene.setSceneRect(0, 0, 10000, 10000)
        self.verticalScrollBar().setValue(5000)
        self.horizontalScrollBar().setValue(5000)

        if old_scene is not None:
            old_scene.nodeCreated.disconnect(self.__onNodeCreated)
            old_scene.nodeDeleted.disconnect(self.__onDeleteNode)
            old_scene.nodeConnected.disconnect(self.__onConnected)
            old_scene.nodeDisconnected.disconnect(self.__onDisconnected)

            del old_scene

        if old_gscene is not None:
            del old_gscene

    def saveSceneAs(self, filepath):
        for node in self.__nodes.values():
            pos = node.pos()
            node.node().setUserData("ui:pos", (pos.x(), pos.y()))

        if self.__scene.saveTo(filepath):
            self.sceneFilepathChanged.emit(self.__scene.filepath())

    def save(self):
        return self.saveSceneAs(self.__scene.filepath())

    def __onConnected(self, hash):
        if hash in self.__connections:
            return

        srch, dsth, index = hash
        src = self.__nodes[srch].output()
        dst = self.__nodes[dsth].input(index)
        con = OFnUIConnection(src, dst)
        con.updatePos()
        self.__graphic_scene.addItem(con)
        self.__connections[hash] = con

    def __onDisconnected(self, hash):
        con = self.__connections.pop(hash, None)
        if con:
            self.__graphic_scene.removeItem(con)

    def __showConnector(self, item):
        if self.__connector is None:
            self.__connector = OFnUIConnector(item, item.direction())
            self.__graphic_scene.addItem(self.__connector)

    def __onDeleteNode(self, strid):
        itm = self.__nodes.pop(int(strid))
        if itm is None:
            return

        self.__graphic_scene.removeItem(itm)

    def __onOpCreateRequested(self, name):
        self.__scene.createNode(name)

    def __onNodeCreated(self, node):
        if node.id() in self.__nodes:
            return

        if node is not None:
            item = OFnUINodeItem(node)
            self.__nodes[node.id()] = item
            self.__graphic_scene.addItem(item)
            px, py = node.getUserData("ui:pos", (None, None))
            if px is None or py is None:
                pos = self.mapToScene(self.mapFromGlobal(QtGui.QCursor.pos()))
                px = pos.x() - item.boundingRect().width() * 0.5
                py = pos.y() - item.boundingRect().height() * 0.5

            item.setPos(px, py)

            item.portClicked.connect(self.__showConnector)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            self.__op_selector.show(self.mapFromGlobal(QtGui.QCursor.pos()))
        elif event.key() == QtCore.Qt.Key_F:
            self.fit()
        elif event.key() == QtCore.Qt.Key_Delete:
            self.__deleteSelectedItems()
        elif event.modifiers() == QtCore.Qt.ControlModifier:
            if event.key() == QtCore.Qt.Key_C:
                self.__copyToClipboard()
            elif event.key() == QtCore.Qt.Key_V:
                self.__loadFromClipboard()

    def __copyToClipboard(self):
        selected_nodes = []
        for node_item in self.__nodes.values():
            if node_item.isSelected():
                selected_nodes.append(node_item.node())

        if selected_nodes:
            self.__scene.copyToClipboard(selected_nodes)

    def __loadFromClipboard(self):
        self.__scene.loadFromClipboard()

    def __deleteSelectedItems(self):
        rmv_cons = []
        for h, con_item in self.__connections.items():
            if con_item.isSelected():
                rmv_cons.append((self.__nodes[h[1]].node(), h[2]))
        for rc in rmv_cons:
            self.__scene.disconnect(*rc)

        rmv_nodes = []
        for h, node_item in self.__nodes.items():
            if node_item.isSelected():
                rmv_nodes.append(node_item)

        for rn in rmv_nodes:
            rnh = rn.node().id()
            self.__scene.deleteNode(rn.node())

    def fit(self):
        rect = QtCore.QRect()
        selected = self.__graphic_scene.selectedItems()
        if len(selected) == 0:
            rect = self.__graphic_scene.itemsBoundingRect()
        else:
            for sel in selected:
                to_scene = sel.mapToScene(sel.boundingRect())
                if isinstance(to_scene, (QtGui.QPolygonF, QtGui.QPolygon)):
                    to_scene = to_scene.boundingRect()

                if isinstance(to_scene, QtCore.QRectF):
                    to_scene = to_scene.toRect()

                rect = rect.united(to_scene)

        self.fitInView(rect, QtCore.Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        delta = 0
        if event.source() == QtCore.Qt.MouseEventSynthesizedBySystem:
            delta = event.pixelDelta().y()
        else:
            delta = event.angleDelta().y()

        if delta == 0:
            return

        if delta > 0:
            self.scale(1.05, 1.05)
        else:
            self.scale(0.95, 0.95)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton or event.modifiers() == QtCore.Qt.AltModifier:
            QtGui.QGuiApplication.setOverrideCursor(QtCore.Qt.OpenHandCursor)
            self.__move_scene = True
            self.__old_scene_pos = event.pos()
            return

        if self.__connector:
            self.__graphic_scene.removeItem(self.__connector)

            item_at = self.itemAt(self.mapFromGlobal(QtGui.QCursor.pos()))
            if isinstance(item_at, OFnUIPort):
                start_item = self.__connector.item()
                if start_item.node() != item_at.node() and start_item.direction() != item_at.direction():
                    if start_item.direction() == PortDirection.Input:
                        src = item_at
                        dst = start_item
                    else:
                        src = start_item
                        dst = item_at

                    self.__scene.connect(src.node(), dst.node(), dst.index())

            self.__connector = None
            return

        super(OFnUINodeGraph, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.__move_scene:
            cur_pos = event.pos()

            if self.__old_scene_pos:
                d = self.__old_scene_pos - cur_pos
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() + d.y())
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + d.x())

            self.__old_scene_pos = cur_pos
            return

        if self.__connector:
            self.__connector.setEndPos(self.mapToScene(self.mapFromGlobal(QtGui.QCursor.pos())))

        super(OFnUINodeGraph, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        QtGui.QGuiApplication.restoreOverrideCursor()
        self.__move_scene = False
        self.__old_scene_pos = None

        super(OFnUINodeGraph, self).mouseReleaseEvent(event)

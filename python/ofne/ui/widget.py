from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

from ..core.opManager import manager as op_manager
from ..core.scene import OFnScene


NODE_SIZE_UNIT = 100


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


class OFnUINodeRect(QtWidgets.QGraphicsRectItem):
    def __init__(self, parent=None):
        super(OFnUINodeRect, self).__init__(parent=parent)
        self.setFlags(QtWidgets.QGraphicsRectItem.ItemIsMovable | QtWidgets.QGraphicsRectItem.ItemIsSelectable | QtWidgets.QGraphicsRectItem.ItemIsFocusable)
        # self.setBrush(QtGui.QBrush(QtCore.Qt.yellow, QtCore.Qt.SolidPattern))

    def paint(self, painter, option, widget):
        if self.isSelected():
            self.setBrush(QtGui.QBrush(QtCore.Qt.red, QtCore.Qt.SolidPattern))
        else:
            self.setBrush(QtGui.QBrush(QtCore.Qt.yellow, QtCore.Qt.SolidPattern))

        super(OFnUINodeRect, self).paint(painter, option, widget)


class OFnUINodeItem(QtWidgets.QGraphicsItemGroup):
    def __init__(self, node, parent=None):
        super(OFnUINodeItem, self).__init__(parent=parent)
        self.__node = node
        height = NODE_SIZE_UNIT * max(node.needs(), 1)

        self.setFlags(QtWidgets.QGraphicsRectItem.ItemIsMovable | QtWidgets.QGraphicsRectItem.ItemIsSelectable | QtWidgets.QGraphicsRectItem.ItemIsFocusable)
        self.__rect = OFnUINodeRect(parent=self)
        self.__rect.setRect(
            0,
            0,
            NODE_SIZE_UNIT,
            height
        )
        self.addToGroup(self.__rect)

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
            item.setPos(self.mapToScene(self.mapFromGlobal(QtGui.QCursor.pos())))

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab:
            self.__op_selector.show(self.mapFromGlobal(QtGui.QCursor.pos()))

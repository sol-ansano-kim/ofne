from PySide6 import QtWidgets
from PySide6 import QtCore

from .. import exceptions
from ..core import param
from ..core.abst import _NodeBase
from . import model


class _TypedLineEditor(QtWidgets.QLineEdit):
    paramChanged = QtCore.Signal()

    def __init__(self, node, paramName, parent=None):
        super(_TypedLineEditor, self).__init__(parent=parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__node = node
        self.__param = node.getParam(paramName)
        self.__param_name = paramName
        self.__refresh()
        self.editingFinished.connect(self.__textChanged)

    def setParam(self, v):
        if self.__param.isValid(v):
            self.__node.setParamValue(self.__param_name, v)
            self.__refresh()
            self.paramChanged.emit()

    def __refresh(self):
        self.setText(str(self.__node.getParamValue(self.__param_name, raw=True)))

    def _typed(self, v):
        raise exceptions.OFnNotImplementedError(self, "_typed")

    def __textChanged(self):
        text = self.text()

        if not text:
            self.__node.setParamValue(self.__param_name, self.__param.default())
            self.paramChanged.emit()
        else:
            try:
                v = self._typed(text)
                if self.__param.isValid(v):
                    self.__node.setParamValue(self.__param_name, v)
                    self.paramChanged.emit()
            except:
                pass

        self.__refresh()


class OFnUICodeParam(QtWidgets.QPlainTextEdit):
    paramChanged = QtCore.Signal()

    def __init__(self, node, paramName, parent=None):
        super(OFnUICodeParam, self).__init__(parent=parent)
        self.__node = node
        self.__param_name = paramName
        self.setPlainText(node.getParamValue(paramName))

    def focusOutEvent(self, event):
        self.__node.setParamValue(self.__param_name, self.toPlainText())
        self.paramChanged.emit()
        super(OFnUICodeParam, self).focusOutEvent(event)


class OFnUIIntParam(_TypedLineEditor):
    def __init__(self, node, paramName, parent=None):
        super(OFnUIIntParam, self).__init__(node, paramName, parent=parent)

    def _typed(self, v):
        return int(v)


class OFnUIFloatParam(_TypedLineEditor):
    def __init__(self, node, paramName, parent=None):
        super(OFnUIFloatParam, self).__init__(node, paramName, parent=parent)

    def _typed(self, v):
        return float(v)


class OFnUIStrParam(_TypedLineEditor):
    def __init__(self, node, paramName, parent=None):
        super(OFnUIStrParam, self).__init__(node, paramName, parent=parent)

    def _typed(self, v):
        return str(v)


class OFnUIStrCombo(QtWidgets.QComboBox):
    paramChanged = QtCore.Signal()

    def __init__(self, node, paramName, parent=None):
        super(OFnUIStrCombo, self).__init__(parent=parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__emit_when_leave = False
        self.__enter = False
        self.__node = node
        self.__param = self.__node.getParam(paramName)
        self.__param_name = paramName
        vls = self.__param.valueList()
        pv = self.__node.getParamValue(self.__param_name, raw=True)
        if not self.__param.enforceValueList() and pv not in vls:
            vls.insert(0, pv)
        self.addItems(vls)

        if self.__param.enforceValueList():
            self.setCurrentIndex(self.findText(self.__node.getParamValue(self.__param_name, raw=True)))
        else:
            self.__emit_when_leave = True
            self.setEditable(True)
            self.setCurrentText(self.__node.getParamValue(self.__param_name, raw=True))

        self.currentIndexChanged.connect(self.__changed)

    def enterEvent(self, event):
        self.__enter = True

    def leaveEvent(self, event):
        if self.__enter and self.__emit_when_leave:
            self.__changed()

        self.__enter = False

    def __changed(self, *args):
        if self.__node.getParamValue(self.__param_name, raw=True) != self.currentText():
            self.__node.setParamValue(self.__param_name, self.currentText())
            self.paramChanged.emit()

    def setParam(self, v):
        # don't have to test self.__param.enforceValueList(), isValid will returns False
        if self.__param.isValid(v) and v != self.__node.getParamValue(self.__param_name, raw=True):
            index = self.findText(v, QtCore.Qt.MatchExactly)
            if index < 0:
                self.insertItem(0, v)
                index = 0

            self.setCurrentIndex(index)


class OFnUIPathInput(QtWidgets.QWidget):
    paramChanged = QtCore.Signal()

    def __init__(self, node, paramName, parent=None):
        super(OFnUIPathInput, self).__init__(parent=parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        self.__param = node.getParam(paramName)
        button = QtWidgets.QPushButton(parent=self)
        button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon))

        if self.__param.valueList():
            self.__param_widget = OFnUIStrCombo(node, paramName, parent=self)
        else:
            self.__param_widget = OFnUIStrParam(node, paramName, parent=self)

        layout.addWidget(self.__param_widget)
        layout.addWidget(button)

        self.__param_widget.paramChanged.connect(self.paramChanged.emit)
        button.clicked.connect(self.__pathDialog)

    def __pathDialog(self):
        if self.__param.pathType() == param.OFnParamPath.TypeFile:
            res = QtWidgets.QFileDialog.getOpenFileName(self, "Open File")[0]
        else:
            res = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory")

        if res:
            self.__param_widget.setParam(res)


class OFnUIBoolParam(QtWidgets.QCheckBox):
    paramChanged = QtCore.Signal()

    def __init__(self, node, paramName, parent=None):
        super(OFnUIBoolParam, self).__init__(parent=parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__node = node
        self.__param = self.__node.getParam(paramName)
        self.__param_name = paramName
        self.setChecked(self.__node.getParamValue(self.__param_name, raw=True))
        self.stateChanged.connect(self.__stateChanged)

    def __stateChanged(self, state):
        self.__node.setParamValue(self.__param_name, self.isChecked())
        self.paramChanged.emit()


class OFnUIParams(QtWidgets.QScrollArea):
    paramChanged = QtCore.Signal()
    updateRequest = QtCore.Signal(_NodeBase)
    nodeRenamed = QtCore.Signal(_NodeBase)

    def __init__(self, parent=None):
        super(OFnUIParams, self).__init__(parent=parent)
        self.__node = None

        main_layout = QtWidgets.QVBoxLayout(self)
        type_layout = QtWidgets.QHBoxLayout()
        name_layout = QtWidgets.QHBoxLayout()
        self.__param_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(type_layout)
        main_layout.addLayout(name_layout)
        main_layout.addLayout(self.__param_layout)
        main_layout.addStretch(1)

        self.__type_label = QtWidgets.QLabel(parent=self)
        self.__type_label.setText("--------------------")
        type_layout.addWidget(self.__type_label)

        self.__name_label = QtWidgets.QLabel("name", parent=self)
        self.__name_line = QtWidgets.QLineEdit("", parent=self)
        self.__name_line.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__name_line.editingFinished.connect(self.__onNameChanged)
        self.__name_label.setVisible(False)
        self.__name_line.setVisible(False)
        self.__name_line.setText("")
        name_layout.addWidget(self.__name_label)
        name_layout.addStretch(1)
        name_layout.addWidget(self.__name_line)

    def setNode(self, node):
        self.__node = node
        self.clearLayout()
        self.__buildParams()

    def __buildParams(self):
        if self.__node:
            is_a_note = isinstance(self.__node, model.OFnUINote)
            if is_a_note:
                self.__type_label.setVisible(False)
                self.__name_label.setVisible(False)
                self.__name_line.setVisible(False)
            else:
                self.__type_label.setText(self.__node.type())
                # TODO : hmm...
                name_editable = self.__node.type() != "Viewer"
                self.__name_label.setVisible(name_editable)
                self.__name_line.setVisible(name_editable)
                self.__name_line.setText(self.__node.name())

            for pn in self.__node.paramNames():
                p = self.__node.getParam(pn)
                pw = None
                if p.type() == param.ParamTypeBool:
                    pw = OFnUIBoolParam(self.__node, pn, parent=self)
                elif p.type() == param.ParamTypeInt:
                    pw = OFnUIIntParam(self.__node, pn, parent=self)
                elif p.type() == param.ParamTypeFloat:
                    pw = OFnUIFloatParam(self.__node, pn, parent=self)
                elif p.type() == param.ParamTypePath:
                    pw = OFnUIPathInput(self.__node, pn, parent=self)
                elif p.type() == param.ParamTypeStr:
                    if p.valueList():
                        pw = OFnUIStrCombo(self.__node, pn, parent=self)
                    else:
                        pw = OFnUIStrParam(self.__node, pn, parent=self)
                elif p.type() == param.ParamTypeCode:
                    pw = OFnUICodeParam(self.__node, pn, parent=self)

                layout = QtWidgets.QHBoxLayout()
                label = QtWidgets.QLabel(pn, parent=self)
                layout.addWidget(label)
                layout.addStretch(1)
                if pw:
                    layout.addWidget(pw)
                    if not is_a_note:
                        pw.paramChanged.connect(self.paramChanged.emit)
                    else:
                        pw.paramChanged.connect(self.__requestUpdate)

                self.__param_layout.addLayout(layout)

            self.__param_layout.addStretch(1)
        else:
            self.__type_label.setText("--------------------")
            self.__name_label.setVisible(False)
            self.__name_line.setVisible(False)
            self.__name_line.setText("")

    def __requestUpdate(self):
        self.updateRequest.emit(self.__node)

    def clearLayout(self):
        curs = [self.__param_layout]

        while (curs):
            cur = curs.pop(0)

            while (cur.count()):
                item = cur.takeAt(0)
                if not item:
                    continue

                l = item.layout()
                w = item.widget()
                if l:
                    curs.append(l)
                if w:
                    cur.removeWidget(w)
                    w.setParent(None)

    def __onNameChanged(self):
        if not self.__node:
            return

        txt = self.__name_line.text()
        if self.__node.name() == txt:
            return

        if not txt:
            self.__name_line.setText(self.__node.name())
        else:
            new_name = self.__node.rename(txt)
            self.__name_line.setText(new_name)
            self.nodeRenamed.emit(self.__node)

from PySide6 import QtWidgets
from PySide6 import QtCore

from .. import exceptions
from ..core import param
from ..core.node import OFnNode


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

    def __refresh(self):
        self.setText(str(self.__node.getParamValue(self.__param_name)))

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
        self.__node = node
        self.__param = self.__node.getParam(paramName)
        self.__param_name = paramName
        vls = self.__param.valueList()
        pv = self.__node.getParamValue(self.__param_name)
        if not self.__param.enforceValueList() and pv not in vls:
            vls.insert(0, pv)
        self.addItems(vls)

        if self.__param.enforceValueList():
            self.setCurrentIndex(self.findText(self.__node.getParamValue(self.__param_name)))
        else:
            self.setEditable(True)
            self.setCurrentText(self.__node.getParamValue(self.__param_name))

        self.currentIndexChanged.connect(self.__changed)

    def __changed(self, *args):
        if self.__node.getParamValue(self.__param_name) != self.currentText():
            self.__node.setParamValue(self.__param_name, self.currentText())
            self.paramChanged.emit()


class OFnUIBoolParam(QtWidgets.QCheckBox):
    paramChanged = QtCore.Signal()

    def __init__(self, node, paramName, parent=None):
        super(OFnUIBoolParam, self).__init__(parent=parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__node = node
        self.__param = self.__node.getParam(paramName)
        self.__param_name = paramName
        self.setChecked(self.__node.getParamValue(self.__param_name))
        self.stateChanged.connect(self.__stateChanged)

    def __stateChanged(self, state):
        self.__node.setParamValue(self.__param_name, self.isChecked())
        self.paramChanged.emit()


class OFnUIParams(QtWidgets.QFrame):
    paramChanged = QtCore.Signal()
    nodeRenamed = QtCore.Signal(OFnNode)

    def __init__(self, parent=None):
        super(OFnUIParams, self).__init__(parent=parent)
        self.setFrameStyle(QtWidgets.QFrame.Raised | QtWidgets.QFrame.StyledPanel)
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
                elif p.type() == param.ParamTypeStr:
                    if p.valueList():
                        pw = OFnUIStrCombo(self.__node, pn, parent=self)
                    else:
                        pw = OFnUIStrParam(self.__node, pn, parent=self)

                layout = QtWidgets.QHBoxLayout()
                label = QtWidgets.QLabel(pn, parent=self)
                layout.addWidget(label)
                layout.addStretch(1)
                if pw:
                    layout.addWidget(pw)
                    pw.paramChanged.connect(self.paramChanged.emit)

                self.__param_layout.addLayout(layout)

            self.__param_layout.addStretch(1)
        else:
            self.__type_label.setText("--------------------")
            self.__name_label.setVisible(False)
            self.__name_line.setVisible(False)
            self.__name_line.setText("")

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

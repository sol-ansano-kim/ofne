from PySide6 import QtWidgets
from PySide6 import QtCore

from .. import exceptions
from ..core import param


class _TypedLineEditor(QtWidgets.QLineEdit):
    paramChanged = QtCore.Signal()

    def __init__(self, node, paramName, parent=None):
        super(_TypedLineEditor, self).__init__(parent=parent)
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
        self.__node = node
        self.__param = self.__node.getParam(paramName)
        self.__param_name = paramName
        self.addItems(self.__param.valueList())

        if self.__param.enforceValueList():
            self.setCurrentIndex(self.findText(self.__node.getParamValue(self.__param_name)))
        else:
            self.setEditable(True)
            self.setCurrentText(self.__node.getParamValue(self.__param_name))

        self.currentIndexChanged.connect(self.__changed)

    def __changed(self, *args):
        self.__node.setParamValue(self.__param_name, self.currentText())
        self.paramChanged.emit()


class OFnUIBoolParam(QtWidgets.QCheckBox):
    paramChanged = QtCore.Signal()

    def __init__(self, node, paramName, parent=None):
        super(OFnUIBoolParam, self).__init__(parent=parent)
        self.__node = node
        self.__param = self.__node.getParam(paramName)
        self.__param_name = paramName
        self.setChecked(self.__node.getParamValue(self.__param_name))
        self.stateChanged.connect(self.__stateChanged)

    def __stateChanged(self, state):
        self.__node.setParamValue(self.__param_name, self.isChecked())
        self.paramChanged.emit()


class OFnUIParams(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super(OFnUIParams, self).__init__(parent=parent)
        self.setFrameStyle(QtWidgets.QFrame.Raised | QtWidgets.QFrame.StyledPanel)
        self.__node = None
        self.__param_layout = QtWidgets.QVBoxLayout(self)

    def setNode(self, node):
        self.__node = node
        self.clearLayout()
        self.__buildParams()

    def __buildParams(self):
        if self.__node:
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

                self.__param_layout.addLayout(layout)

            self.__param_layout.addStretch(1)

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

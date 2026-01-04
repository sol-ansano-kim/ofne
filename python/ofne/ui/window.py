from PySide6 import QtWidgets
from . import widget


class OFnUIMain(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(OFnUIMain, self).__init__(parent=parent)
        central = QtWidgets.QWidget(self)
        central_layout = QtWidgets.QVBoxLayout(central)
        self.setCentralWidget(central)
        # splitter = QtWidgets.QSplitter()
        graph = widget.OFnUINodeGraph(parent=self)
        central_layout.addWidget(graph)
        self.resize(800, 600)

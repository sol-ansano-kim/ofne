from PySide6 import QtWidgets
from . import widget


class OFnUIMain(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(OFnUIMain, self).__init__(parent=parent)
        central = QtWidgets.QWidget(self)
        central_layout = QtWidgets.QVBoxLayout(central)
        self.setCentralWidget(central)
        # splitter = QtWidgets.QSplitter()
        self.__graph = widget.OFnUINodeGraph(parent=self)
        central_layout.addWidget(self.__graph)

        file_menu = self.menuBar().addMenu("File")
        new_action = file_menu.addAction("New")
        save_action = file_menu.addAction("Save")
        load_action = file_menu.addAction("Load")

        new_action.triggered.connect(self.__new)
        save_action.triggered.connect(self.__save)
        load_action.triggered.connect(self.__load)

        self.resize(800, 600)

    def __new(self):
        self.__graph.newScene()

    def __save(self):
        pass

    def __load(self):
        pass
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
        open_action = file_menu.addAction("Open")
        save_as_action = file_menu.addAction("SaveAs")

        new_action.triggered.connect(self.__new)
        save_as_action.triggered.connect(self.__saveAs)
        open_action.triggered.connect(self.__open)

        self.resize(800, 600)

    def __new(self):
        self.__graph.newScene()

    def __saveAs(self):
        res = QtWidgets.QFileDialog.getSaveFileName(self, "Save", "", "Ofne Scene (*.ofsn)")[0]
        if res:
            self.__graph.saveSceneAs(res)

    def __open(self):
        res = QtWidgets.QFileDialog.getOpenFileName(self, "Open", "", "Ofne Scene (*.ofsn)")
        print(res)

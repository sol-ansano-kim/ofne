from PySide6 import QtWidgets
from . import graph


class OFnUIMain(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(OFnUIMain, self).__init__(parent=parent)
        central = QtWidgets.QWidget(self)
        central_layout = QtWidgets.QVBoxLayout(central)
        self.setCentralWidget(central)
        # splitter = QtWidgets.QSplitter()
        self.__graph = graph.OFnUINodeGraph(parent=self)
        central_layout.addWidget(self.__graph)

        file_menu = self.menuBar().addMenu("File")
        new_action = file_menu.addAction("New")
        open_action = file_menu.addAction("Open")
        self.__save_action = file_menu.addAction("Save")
        save_as_action = file_menu.addAction("SaveAs")
        self.__save_action.setEnabled(False)

        new_action.triggered.connect(self.__new)
        self.__save_action.triggered.connect(self.__save)
        save_as_action.triggered.connect(self.__saveAs)
        open_action.triggered.connect(self.__open)
        self.__graph.sceneFilepathChanged.connect(self.__setTitle)

        self.resize(800, 600)
        self.__setTitle(None)

    def __setTitle(self, filepath):
        title = "OFNE"

        if filepath:
            title += f" : {filepath}"
            self.__save_action.setEnabled(True)
        else:
            self.__save_action.setEnabled(False)

        self.setWindowTitle(title)

    def __new(self):
        self.__graph.newScene()
        self.__save_action.setEnabled(False)

    def __save(self):
        self.__graph.save()

    def __saveAs(self):
        res = QtWidgets.QFileDialog.getSaveFileName(self, "Save", "", "Ofne Scene (*.ofsn)")[0]
        if res:
            self.__graph.saveSceneAs(res)

    def __open(self):
        res = QtWidgets.QFileDialog.getOpenFileName(self, "Open", "", "Ofne Scene (*.ofsn)")[0]
        if res:
            self.__graph.open(res)

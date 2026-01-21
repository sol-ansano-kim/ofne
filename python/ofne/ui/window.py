from PySide6 import QtWidgets
from PySide6 import QtCore
from . import graph
from . import params
from . import viewport


class OFnUIMain(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(OFnUIMain, self).__init__(parent=parent)
        central = QtWidgets.QWidget(self)
        central_layout = QtWidgets.QVBoxLayout(central)
        self.setCentralWidget(central)

        self.__vert_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.__bottom_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        central_layout.addWidget(self.__vert_splitter)

        self.__viewport = viewport.OFnUIViewport(parent=self)
        self.__vert_splitter.addWidget(self.__viewport)
        self.__vert_splitter.addWidget(self.__bottom_splitter)
        self.__vert_splitter.setStretchFactor(0, 1)
        self.__vert_splitter.setStretchFactor(1, 0)

        self.__graph = graph.OFnUINodeGraph(parent=self)
        self.__params = params.OFnUIParams(parent=self)
        self.__bottom_splitter.addWidget(self.__graph)
        self.__bottom_splitter.addWidget(self.__params)
        self.__bottom_splitter.setStretchFactor(0, 1)
        self.__bottom_splitter.setStretchFactor(1, 0)

        # menu
        file_menu = self.menuBar().addMenu("File")
        new_action = file_menu.addAction("New")
        open_action = file_menu.addAction("Open")
        self.__save_action = file_menu.addAction("Save")
        save_as_action = file_menu.addAction("SaveAs")
        self.__save_action.setEnabled(False)

        # signal
        new_action.triggered.connect(self.__new)
        self.__save_action.triggered.connect(self.__save)
        save_as_action.triggered.connect(self.__saveAs)
        open_action.triggered.connect(self.__open)
        self.__graph.sceneFilepathChanged.connect(self.__setTitle)
        self.__graph.nodeSelected.connect(self.__onNodeSelected)
        self.__params.nodeRenamed.connect(self.__onNodeRenamed)
        self.__params.paramChanged.connect(self.__graph.evaluate)

        # setup
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

    def __onNodeSelected(self, node):
        self.__params.setNode(node)

    def __onNodeRenamed(self, node):
        self.__graph.updateNodeName(node)

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

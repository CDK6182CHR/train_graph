"""
2019.06.26新增，数据库管理器，可独立运行。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .trainWidget import TrainWidget
from .currentWidget import CurrentWidget
from .circuitWidget import CircuitWidget,CircuitDialog
from .pyETRCExceptions import *
from .graph import Graph

class TrainDatabase(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super(TrainDatabase, self).__init__(parent)
        self.setWindowTitle('车次数据库管理器')
        self.currentWidget = ...  # type:CurrentWidget
        self.trainWidget = ...  # type:TrainWidget
        self.trainDockWidget = ...  # type:QtWidgets.QDockWidget
        self.currentDockWidget = ...  # type:QtWidgets.QDockWidget
        self.graph = Graph()  # type:Graph
        self._initUI()

    def _initUI(self):
        """
        2019.06.26，非正式的。
        """
        trainDock = QtWidgets.QDockWidget()
        widget = TrainWidget(self.graph)
        trainDock.setWidget(widget)
        self.trainDockWidget = trainDock
        self.trainWidget = widget
        self.addDockWidget(Qt.LeftDockWidgetArea,trainDock)

        currentDock = QtWidgets.QDockWidget()
        s = QtWidgets.QScrollArea()
        widget = CurrentWidget(self.graph)
        s.setWidget(widget)
        s.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        s.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        s.setWidgetResizable(True)
        currentDock.setWidget(s)
        self.currentWidget = widget
        self.currentDockWidget = currentDock
        self.addDockWidget(Qt.RightDockWidgetArea,currentDock)
        self.trainWidget.current_train_changed.connect(self.currentWidget.setData)

        self._initMenubar()

    def _initMenubar(self):
        menubar = QtWidgets.QMenuBar(self)
        menu = menubar.addMenu('文件(&F)')

        action = QtWidgets.QAction('打开',self)
        action.setShortcut('ctrl+O')
        menu.addAction(action)
        action.triggered.connect(self._open)

        menubar.addMenu(menu)
        self.setMenuBar(menubar)

    def setData(self):
        """
        打开时调用。
        """
        self.trainWidget.setData()
        self.currentWidget.setData()


    # slots
    def _open(self):
        # flag = QtWidgets.QMessageBox.question(self, self.title, "是否保存对运行图的修改？",
        #                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
        #                                       QtWidgets.QMessageBox.Cancel)
        # if flag == QtWidgets.QMessageBox.Yes:
        #     self._saveGraph()
        # elif flag == QtWidgets.QMessageBox.No:
        #     pass
        # else:
        #     return

        filename,ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
        filter='pyETRC运行图文件(*.pyetgr;*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')
        if not ok:
            return

        self.graph.clearAll()
        try:
            self.graph.loadGraph(filename)
        except:
            self._derr("文件错误！请检查")
        else:
            pass
        self.setData()

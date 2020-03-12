"""
数据库管理主窗口。主要部分由tabWidget实现。

工作区信息文件*.pnconf  json编码，保存当前引用的文件名和打开的切片状态。
系统不持有工作区文件名的状态信息。这就是说，只提供加载和保存。
格式：
dct = {
            "trainFile":self.trainFile,
            "lineFile":self.lineFile,
            "slices":[],  # List[List]  所有切片经由表
        }
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from ..data import *
from ..linedb.lineLibWidget import LineLibWidget
from .trainManager import TrainManager
from .sliceManager import SliceManager
from ..MainGraphWindow import MainGraphWindow
from ..importTrainDialog import ImportTrainDialog
import json


class MainNetWindow(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super(MainNetWindow, self).__init__(parent)
        self.name = "pyETRC路网管理模块"
        # self.version = "V0.1.0"
        self.title = ""
        # self.release = "R0"
        # self.date = "20200202"
        self.graphdb = Graph()

        self.centerWidget = QtWidgets.QTabWidget()
        self.trainManager = TrainManager(self.graphdb)
        self.lineManager = LineLibWidget(fromPyetrc=False)
        self.sliceManager = SliceManager(self.graphdb,self.lineManager.lineLib)

        self.lineFile = self.lineManager.filename
        self.trainFile = ""

        self._initUI()

    def _initUI(self):
        self._updateTitle()
        self.centerWidget.addTab(self.lineManager,'基线管理')
        self.centerWidget.addTab(self.trainManager,'车次管理')
        self.centerWidget.addTab(self.sliceManager,'切片管理')

        self.sliceManager.SliceGraphAdded.connect(self._add_slice_graph)
        self.sliceManager.SliceDeleted.connect(self._del_slice_graph)
        self.sliceManager.ShowSlice.connect(self._show_slice_graph)
        self.sliceManager.OutputSlice.connect(self._output_slice_graph)

        self.setCentralWidget(self.centerWidget)
        self._initMenubar()

    def _initMenubar(self):
        menubar:QtWidgets.QMenuBar = self.menuBar()

        # 工作区
        m = menubar.addMenu('工作区')
        self._addMenuAction(m,'读取工作区配置',self._loadConf)
        self._addMenuAction(m,'保存当前工作区',self._saveConf)
        self._addMenuAction(m,'保存所有数据库变更',self._saveAll)

        # 基线
        m:QtWidgets.QMenu = menubar.addMenu('基线')
        # self._addMenuAction(m,'新建基线文件',self._newLineFile)
        self._addMenuAction(m,'打开基线文件',self._openLineFile)
        self._addMenuAction(m,'保存基线文件',self._saveLineFile)
        # self._addMenuAction(m,'基线文件另存为...',self._saveLineFileAs)

        # 车次
        m=menubar.addMenu('车次')
        self._addMenuAction(m,'新建车次数据库文件',self._newTrainFile)
        self._addMenuAction(m,'打开车次数据库文件',self._openTrainFile)
        self._addMenuAction(m,'保存车次数据库文件',self._saveTrainFile)
        self._addMenuAction(m,'车次数据库另存为...',self._saveTrainFileAs)
        m.addSeparator()
        self._addMenuAction(m,'导入车次',self._importTrain)

        # 切片
        m = menubar.addMenu('切片')
        self._addMenuAction(m,'直接读取有向图数据',self._readDigraphFile)
        self._addMenuAction(m,'刷新线路网络模型',self._loadLibToGraph)

    def _addMenuAction(self,menu:QtWidgets.QMenu,name:str,slot,shortcut:str=None):
        action = QtWidgets.QAction(name,self)
        action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)

    def _newLineFile(self):
        """
        新建容易导致逻辑复杂化，暂时不允许新建。
        """
        pass

    def _openLineFile(self):
        self.lineManager.change_filename()

    def _saveLineFile(self):
        self.lineManager.save_lib()

    def _saveLineFileAs(self):
        """
        暂不实现另存为
        """
        pass

    def _newTrainFile(self):
        QM = QtWidgets.QMessageBox
        btn = QtWidgets.QMessageBox.question(self, self.title,
                                             f'是否保存到车次文件{self.trainFile}？',
                                             QM.Yes | QM.No | QM.Cancel, QM.Yes
                                             )
        if btn == QM.Yes:
            # 保存
            self._saveTrainFile()
        elif btn == QM.Cancel or btn == QM.NoButton:
            return
        self.graphdb.clearAll()
        self.trainManager.setData()
        self._updateTitle()

    def _openTrainFile(self):
        QM = QtWidgets.QMessageBox
        btn = QtWidgets.QMessageBox.question(self,self.title,
                                             f'是否保存到车次文件{self.trainFile}？',
                                             QM.Yes|QM.No|QM.Cancel,QM.Yes
                                             )
        if btn == QM.Yes:
            # 保存
            self._saveTrainFile()
        elif btn==QM.Cancel or btn == QM.NoButton:
            return
        filename,ok = QtWidgets.QFileDialog.getOpenFileName(self,'打开基线文件',
                    filter = 'pyETRC车次数据库文件(*.pyetdb)\n'
                             'pyETRC列车运行图文件(*.pyetgr;*.json)\n'
                             'ETRC列车运行图文件(*.trc)\n'
                             '所有文件(*.*,*)'
                    )
        if not ok:
            return
        self.trainManager.openFile(filename)
        self._updateTitle()

    def _saveTrainFile(self):
        if not self.trainFile:
            self._saveTrainFileAs()
        else:
            self.graphdb.save(self.trainFile)

    def _saveTrainFileAs(self):
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self, '基线文件另存为',
                                                             filter='pyETRC车次数据库文件(*.pyetdb)\n'
                                                                    'pyETRC列车运行图文件(*.pyetgr;*.json)\n'
                                                                    'ETRC列车运行图文件(*.trc)\n'
                                                                    '所有文件(*.*;*)'
                                                             )
        if not ok:
            return
        self.graphdb.filename = filename
        self.graphdb.save(filename)
        self._updateTitle()

    def _updateTitle(self):
        self.lineFile = self.lineManager.filename
        self.trainFile = self.graphdb.filename
        self.title = f"{self.name}  {self.lineFile}  {self.trainFile}"
        self.setWindowTitle(self.title)

    def _readDigraphFile(self):
        filename,ok = QtWidgets.QFileDialog.getOpenFileName(self,'读取图模型',
                        filter='NetworkX有向图模型(*.gml)\n所有文件(*)'
                                                            )
        if not ok:
            return
        self.sliceManager.loadDigraph(filename)

    def _loadLibToGraph(self):
        self.sliceManager.net.reset()
        self.sliceManager.net.loadLineLib(self.sliceManager.lineLib)

    def _importTrain(self):
        dialog = ImportTrainDialog(self.graphdb)
        dialog.checkAll.setChecked(False)
        dialog.checkAll.setEnabled(False)
        dialog.importTrainOk.connect(self.trainManager.setData)
        dialog.exec_()

    def _loadConf(self):
        QM = QtWidgets.QMessageBox
        b = QM.question(self,self.title,f'在加载新的工作区前，是否保存到线路数据库文件{self.lineFile}和'
                                        f'车次数据库文件{self.trainFile}？',
                        QM.Yes | QM.No | QM.Cancel)
        if b == QM.Yes:
            self._saveAll()
        elif b == QM.Cancel or b == QM.NoButton:
            return
        filename, ok = QtWidgets.QFileDialog.getOpenFileName(self, '保存工作区配置',
                                                             filter='pyETRC网络模块工作区配置文件(*.pnconf)\n'
                                                                    'JSON文件(*.json)\n'
                                                                    '"所有文件(*)')
        if not ok:
            return
        with open(filename,'r',encoding='utf-8',errors='ignore') as fp:
            try:
                dct = json.load(fp)
                self._loadConfig(dct)
            except Exception as e:
                QM.warning(self,'错误','文件无效:\n'+repr(e))

    def _loadConfig(self,dct:dict):
        self.trainManager.openFile(dct["trainFile"])
        self.lineManager.loadFile(dct["lineFile"])
        self.sliceManager.clearAllSlices()
        for via in dct['slices']:
            self.sliceManager.addNewSlice(via)
        self._updateTitle()

    def _saveConf(self):
        filename,ok = QtWidgets.QFileDialog.getSaveFileName(self,'保存工作区配置',
                    filter='pyETRC网络模块工作区配置文件(*.pnconf)\n'
                           'JSON文件(*.json)\n'
                           '"所有文件(*)')
        if not ok:
            return
        dct = {
            "trainFile":self.trainFile,
            "lineFile":self.lineFile,
            "slices":[],  # List[List]  所有切片经由表
        }
        lw = self.sliceManager.sliceListWidget
        for row in range(lw.count()):
            dct["slices"].append(lw.item(row).data(Qt.UserRole))
        with open(filename,'w',encoding='utf-8',errors='ignore') as fp:
            json.dump(dct,fp,ensure_ascii=False)

    def _saveAll(self):
        self._saveLineFile()
        self._saveTrainFile()

    @staticmethod
    def tabIndexMap(id):
        return id + 3

    # slots
    def _add_slice_graph(self,graph:Graph, name:str):
        """

        """
        w = MainGraphWindow(graph=graph)
        self.centerWidget.addTab(w,name)

    def _del_slice_graph(self,index:int):
        id = self.tabIndexMap(index)
        self.centerWidget.removeTab(id)

    def _show_slice_graph(self,index:int):
        id = self.tabIndexMap(index)
        self.centerWidget.setCurrentIndex(id)

    def _output_slice_graph(self,index:int):
        id = self.tabIndexMap(index)
        w:MainGraphWindow = self.centerWidget.widget(id)
        w._saveGraphAs()

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, self.title, note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

    def closeEvent(self, event:QtGui.QCloseEvent):
        QM = QtWidgets.QMessageBox
        b = QM.question(self, self.title, f'在退出前，是否保存到线路数据库'
                                          f'文件{self.lineFile}和'
                                          f'车次数据库文件{self.trainFile}？',
                        QM.Yes|QM.No|QM.Cancel
                        )
        if b == QM.Yes:
            self._saveAll()
        elif b == QM.Cancel or b == QM.NoButton:
            event.ignore()
            return
        event.accept()

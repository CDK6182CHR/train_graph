from .data import *
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .trainDiffDialog import TrainDiffDialog
from typing import List,Dict,Tuple,Union

class GraphDiffDialog(QtWidgets.QDialog):
    def __init__(self,graph:Graph,parent=None):
        super(GraphDiffDialog, self).__init__(parent)
        self.graph = graph
        self.anGraph = None
        self.graphDiffData = None  # type: List
        self.initUI()

    def initUI(self):
        self.setWindowTitle('运行图比较')
        self.resize(800,700)
        vlayout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        filenameEdit = QtWidgets.QLineEdit()
        filenameEdit.setFocusPolicy(Qt.NoFocus)
        self.filenameEdit = filenameEdit
        hlayout.addWidget(filenameEdit)
        btnOpen = QtWidgets.QPushButton('打开文件')
        btnOpen.clicked.connect(self._open_file)
        hlayout.addWidget(btnOpen)
        vlayout.addLayout(hlayout)

        checkLocalOnly = QtWidgets.QCheckBox('仅对比经过本线的车次')
        self.checkLocalOnly = checkLocalOnly
        vlayout.addWidget(checkLocalOnly)
        checkLocalOnly.toggled.connect(self.setData)

        label = QtWidgets.QLabel('双击，或通过右键菜单查看车次时刻对比。\n如果选择“仅对比经过本线的车次”，则这里的逻辑相当于使用“导入车次”前对比两张运行图。\n请注意如果运行图规模比较大，打开文件后将会耗费较多时间。')
        label.setWordWrap(True)
        vlayout.addWidget(label)

        tw = QtWidgets.QTableWidget()
        self.tableWidget = tw
        tw.setColumnCount(6)
        tw.setHorizontalHeaderLabels(('车次','始发1','终到1','修改数','始发2','终到2'))
        header:QtWidgets.QHeaderView = tw.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(tw.sortByColumn)
        for i,s in enumerate((130,100,100,90,100,100)):
            tw.setColumnWidth(i,s)
        tw.setEditTriggers(tw.NoEditTriggers)
        vlayout.addWidget(tw)

        action = QtWidgets.QAction('时刻对比', self.tableWidget)
        self.tableWidget.addAction(action)
        self.tableWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        action.triggered.connect(self._train_diff)
        tw.itemDoubleClicked.connect(self._train_diff)

        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(self.close)
        vlayout.addWidget(btnClose)

        self.setLayout(vlayout)

    def readData(self):
        """
        读取数据。在diffWith里面调用callBack，来设置进度条。
        """
        if self.anGraph is None:
            return
        process = QtWidgets.QProgressDialog(self)
        process.setValue(0)
        process.setMaximum(self.graph.trainCount()+self.anGraph.trainCount())
        process.setWindowTitle('请稍后')
        process.setLabelText('数据处理中……\n较大的运行图可能需要数秒才能完成读取。\n此过程的耗时主要取决于两运行图重叠车次的数量。')
        process.setCancelButtonText('取消')

        def callBack(dv:int):
            """
            在diffWith中回调。如果取消，在这里抛出异常。
            """
            process.setValue(process.value()+dv)
            QtCore.QCoreApplication.processEvents()
            if process.wasCanceled():
                raise KeyboardInterrupt('取消Graph::diffWith()过程')

        try:
            data = self.graph.diffWith(self.anGraph, self.checkLocalOnly.isChecked(),callBack)
        except KeyboardInterrupt:
            return
        finally:
            process.close()
        self.graphDiffData = data

    def setData(self):
        """

        """
        if self.anGraph is None:
            return
        self.readData()
        tw = self.tableWidget
        TWI = QtWidgets.QTableWidgetItem
        data = self.graphDiffData
        if data is None:
            return
        tw.setRowCount(len(data))
        for row,tple in enumerate(data):
            tp,trainDiffData,trainDiffCount,train1,train2 = tple
            train = train1 if train1 is not None else train2
            tw.setItem(row,0,TWI(train.fullCheci()))
            tw.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])
            if train1 is not None:
                tw.setItem(row,1,TWI(train1.sfz))
                tw.setItem(row,2,TWI(train1.zdz))
            if train2 is not None:
                tw.setItem(row,4,TWI(train2.sfz))
                tw.setItem(row,5,TWI(train2.zdz))
            item = TWI()
            tw.setItem(row,3,item)
            if tp == Graph.TrainDiffType.NewAdded:
                item.setText('新增')
                self._setItemColor(row,0,Qt.blue)
                self._setItemColor(row,4,Qt.blue)
                self._setItemColor(row,5,Qt.blue)
            elif tp == Graph.TrainDiffType.Deleted:
                item.setText('删除')
                self._setItemColor(row, 0, Qt.darkGray)
                self._setItemColor(row, 1, Qt.darkGray)
                self._setItemColor(row, 2, Qt.darkGray)
            else:
                item.setData(Qt.DisplayRole,trainDiffCount)
                if trainDiffCount != 0:
                    for col in (0,1,2,4,5):
                        self._setItemColor(row,col,Qt.red)

    def _setItemColor(self,row:int,col:int,color:QtGui.QColor):
        item = self.tableWidget.item(row,col)
        if isinstance(item,QtWidgets.QTableWidgetItem):
            item.setForeground(color)

    # slots
    def _open_file(self):
        filename,ok = QtWidgets.QFileDialog.getOpenFileName(
            self,'选择运行图',filter='pyETRC运行图文件(*.pyetgr;*.json)\npyETRC车次数据库文件(*.pyetdb;*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)'
        )
        if not ok:
            return

        anGraph = Graph()
        self.filenameEdit.setText(filename)
        try:
            anGraph.loadGraph(filename)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','运行图文件错误\n'+repr(e))
            return
        self.anGraph = anGraph
        self.setData()

    def _train_diff(self):
        row = self.tableWidget.currentRow()
        succ = True
        if not 0<=row<self.tableWidget.rowCount():
            succ = False
        else:
            tp,trainDiffData,_,train1,train2 = self.graphDiffData[row]
            if train1 is None or train2 is None:
                succ=False
        if not succ:
            QtWidgets.QMessageBox.warning(self,'提示','请选择非新增或删除的车次来对比！')
            return
        dialog = TrainDiffDialog(train1,train2,self.graph,trainDiffData)
        dialog.exec_()

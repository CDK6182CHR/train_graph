"""
车次编辑功能的封装类
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from graph import Graph
from train import Train

class TrainWidget(QtWidgets.QWidget):
    search_train = QtCore.pyqtSignal(str)
    current_train_changed = QtCore.pyqtSignal(Train)
    train_double_clicked = QtCore.pyqtSignal(Train)
    trainShowChanged = QtCore.pyqtSignal(Train,bool)
    addNewTrain = QtCore.pyqtSignal()
    showStatus = QtCore.pyqtSignal(str)
    def __init__(self,graph,main=None,parent=None):
        super().__init__(parent)
        self.graph = graph
        self.main = main

    def initWidget(self):
        vlayout = QtWidgets.QVBoxLayout()
        tableWidget = QtWidgets.QTableWidget()

        hlayout = QtWidgets.QHBoxLayout()
        lineEdit = QtWidgets.QLineEdit()
        lineEdit.setFixedHeight(30)
        lineEdit.editingFinished.connect(lambda: self.search_train.emit(lineEdit.text()))
        btnSearch = QtWidgets.QPushButton("搜索车次")
        btnSearch.clicked.connect(lambda: self.search_train.emit(lineEdit.text()))
        hlayout.addWidget(lineEdit)
        hlayout.addWidget(btnSearch)
        vlayout.addLayout(hlayout)

        tableWidget.setRowCount(self.graph.trainCount())
        tableWidget.setColumnCount(6)
        tableWidget.setHorizontalHeaderLabels(["车次", "始发", "终到", "类型", "显示", "本线里程"])
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        tableWidget.setSelectionBehavior(tableWidget.SelectRows)
        tableWidget.currentCellChanged.connect(self._current_row_changed)

        tableWidget.setColumnWidth(0, 90)
        tableWidget.setColumnWidth(1, 80)
        tableWidget.setColumnWidth(2, 80)
        tableWidget.setColumnWidth(3, 80)
        tableWidget.setColumnWidth(4, 40)
        tableWidget.setColumnWidth(5, 80)

        tableWidget.setViewportMargins(0, 0, 0, 0)
        tableWidget.doubleClicked.connect(self._train_table_doubleClicked)

        self.trainTable = tableWidget

        now_line = 0
        for train in self.graph.trains():
            tableWidget.setRowHeight(now_line, 30)

            item = QtWidgets.QTableWidgetItem(train.fullCheci())
            item.setData(-1, train)
            tableWidget.setItem(now_line, 0, item)

            item = QtWidgets.QTableWidgetItem(train.sfz)
            tableWidget.setItem(now_line, 1, item)

            item = QtWidgets.QTableWidgetItem(train.zdz)
            tableWidget.setItem(now_line, 2, item)

            item = QtWidgets.QTableWidgetItem(train.type)
            tableWidget.setItem(now_line, 3, item)

            item = QtWidgets.QTableWidgetItem('%.2f' % train.localMile(self.graph))
            item.setData(0, train.localMile(self.graph))
            tableWidget.setItem(now_line, 5, item)

            # 修改直接生效
            check = QtWidgets.QCheckBox()
            check.setChecked(train.isShow())
            check.setMinimumSize(1, 1)
            check.setStyleSheet("QCheckBox{margin:3px}")
            # check.toggled.connect(lambda x:self._train_show_changed(now_line,tableWidget,x))
            check.train = train
            check.toggled.connect(self._train_show_changed)
            tableWidget.setCellWidget(now_line, 4, check)

            now_line += 1

        vlayout.addWidget(tableWidget)

        btnEdit = QtWidgets.QPushButton("编辑")
        btnEdit.setMinimumWidth(80)
        btnAdd = QtWidgets.QPushButton("添加")
        btnAdd.setMinimumWidth(80)
        btnDel = QtWidgets.QPushButton("删除")
        btnDel.setMinimumWidth(80)

        btnEdit.clicked.connect(lambda: self._train_table_doubleClicked(self.trainTable.currentRow()))
        btnAdd.clicked.connect(lambda:self.addNewTrain.emit())
        btnDel.clicked.connect(self._del_train)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnEdit)
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        vlayout.addLayout(hlayout)

        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        self.setLayout(vlayout)

    def trainByRow(self,row):
        item = self.trainTable.item(row, 0)
        if item is None:
            return

        train: Train = item.data(-1)
        return train

    def setCurrentTrain(self,train):
        for i in range(self.trainTable.rowCount()):
            if train is self.trainTable.item(i, 0).data(-1):
                self.trainTable.setCurrentCell(i, 0)
                self.trainTable.cellWidget(i,4).setChecked(train.isShow())

    #slots
    def _current_row_changed(self,row):
        """
        trainTable行变化，解析出列车信息，然后emit信号给main窗口。对应在main的855行
        """
        train = self.trainByRow(row)
        if train is None:
            return
        self.current_train_changed.emit(train)

    def _train_table_doubleClicked(self,row):
        """
        双击表中的行触发。计算出列车对象，然后返回
        """
        train = self.trainByRow(row)
        if train is None:
            return
        self.train_double_clicked.emit(train)

    def _train_show_changed(self):
        """
        """
        sender = self.sender()
        train = sender.train
        train.setIsShow(sender.isChecked())
        self.trainShowChanged.emit(train,sender.isChecked())

    def _del_train(self):
        tableWidget = self.trainTable
        rows = []
        # tableWidget.currentCellChanged.disconnect(self._current_train_changed)
        # 用Nuitka编译后此行代码导致程序崩溃，故删除这条语句。
        for index in tableWidget.selectedIndexes():
            row = index.row()
            if row not in rows:
                rows.append(row)

        rows.reverse()

        if self.main:
            progressDialog = QtWidgets.QProgressDialog(self.main)
            progressDialog.setWindowTitle('正在删除')
            progressDialog.setRange(0, len(rows))
            progressDialog.setCancelButtonText('取消')

        count = len(rows)

        for i, row in enumerate(rows):
            train = tableWidget.item(row, 0).data(-1)
            self.graph.delTrain(train)
            tableWidget.removeRow(row)
            if self.main:
                self.main.GraphWidget.delTrainLine(train)
                progressDialog.setLabelText(f'正在删除车次({i+1}/{len(rows)}): {train.fullCheci()} ')
                progressDialog.setValue(i + 1)
                QtCore.QCoreApplication.processEvents()
                if progressDialog.wasCanceled():
                    count = i + 1
                    break

        if count:
            self.showStatus.emit(f"成功删除{count}个车次")


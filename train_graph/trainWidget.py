"""
车次编辑功能的封装类
2019.07.09将trainMapToRow数据结构改为：Train->QTableWidgetItem，指向的是每行第0个Item，即车次一格。
2019.10.21重构：肃清cellWidget。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .data.graph import Graph,Line
from .data.train import Train
from .trainFilter import TrainFilter

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
        self.trainMapToRow=dict()  # dict<train,item>
        self.filter = TrainFilter(self.graph,self)
        self.initWidget()

    def initWidget(self):
        vlayout = QtWidgets.QVBoxLayout()
        tableWidget = QtWidgets.QTableWidget()

        hlayout = QtWidgets.QHBoxLayout()
        lineEdit = QtWidgets.QLineEdit()
        lineEdit.setFixedHeight(30)
        lineEdit.editingFinished.connect(lambda: self.search_train.emit(lineEdit.text()))
        btnSearch = QtWidgets.QPushButton("搜索")
        btnSearch.setMinimumWidth(80)
        btnSearch.clicked.connect(lambda: self.search_train.emit(lineEdit.text()))
        hlayout.addWidget(lineEdit)
        hlayout.addWidget(btnSearch)
        btnFilter = QtWidgets.QPushButton('筛选')
        btnFilter.setMinimumWidth(80)
        btnFilter.clicked.connect(self.filter.setFilter)
        hlayout.addWidget(btnFilter)
        vlayout.addLayout(hlayout)

        tableWidget.setRowCount(0)
        tableWidget.setColumnCount(7)
        tableWidget.setHorizontalHeaderLabels(["车次", "始发", "终到", "类型", "显示", "本线里程",'本线旅速'])
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        tableWidget.setSelectionBehavior(tableWidget.SelectRows)
        tableWidget.currentCellChanged.connect(self._current_row_changed)

        tableWidget.setColumnWidth(0, 90)
        tableWidget.setColumnWidth(1, 80)
        tableWidget.setColumnWidth(2, 80)
        tableWidget.setColumnWidth(3, 80)
        tableWidget.setColumnWidth(4, 40)
        tableWidget.setColumnWidth(5, 90)
        tableWidget.setColumnWidth(6, 90)

        tableWidget.setViewportMargins(0, 0, 0, 0)
        tableWidget.doubleClicked.connect(lambda idx:self._train_table_doubleClicked(idx.row()))

        self.trainTable = tableWidget

        self.setData()
        tableWidget.itemChanged.connect(self._item_changed)

        vlayout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnUp = QtWidgets.QPushButton('上移')
        btnUp.setMinimumWidth(80)
        btnDown = QtWidgets.QPushButton('下移')
        btnDown.setMinimumWidth(80)
        hlayout.addWidget(btnUp)
        hlayout.addWidget(btnDown)
        btnSaveOrder = QtWidgets.QPushButton('保存顺序')
        btnSaveOrder.setMinimumWidth(80)
        hlayout.addWidget(btnSaveOrder)
        vlayout.addLayout(hlayout)
        btnUp.clicked.connect(self._move_up)
        btnDown.clicked.connect(self._move_down)
        btnSaveOrder.clicked.connect(self._save_order)

        btnEdit = QtWidgets.QPushButton("编辑")
        btnEdit.setMinimumWidth(80)
        btnChange = QtWidgets.QPushButton("批量调整")
        btnChange.setMinimumWidth(80)
        btnAdd = QtWidgets.QPushButton("添加")
        btnAdd.setMinimumWidth(80)
        btnDel = QtWidgets.QPushButton("删除")
        btnDel.setMinimumWidth(80)
        self.btnDel = btnDel  # 用于从profile处操纵删除。

        btnEdit.clicked.connect(lambda: self._train_table_doubleClicked(self.trainTable.currentRow()))
        btnAdd.clicked.connect(self.addNewTrain.emit)
        btnChange.clicked.connect(self._batch_change_ui)
        btnDel.clicked.connect(self._del_train)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnEdit)
        hlayout.addWidget(btnChange)
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        vlayout.addLayout(hlayout)

        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        self.setLayout(vlayout)

        self.filter.FilterChanged.connect(self.setData) # 不能放在init中，否则报错

    def setData(self):
        """
        根据自带的graph数据对象重新设置表格信息。
        原则上只有系统初始化时才可以调用initWidget。
        """
        self.trainMapToRow.clear()
        self.trainTable.setRowCount(0)
        for train in self.graph.trains():
            if self.filter.check(train):
                self.addTrain(train)

    def addTrain(self,train:Train):
        """
        添加新车次到末尾。由初始化函数和标尺排图、添加车次调用。
        """
        tableWidget = self.trainTable

        now_line = tableWidget.rowCount()
        tableWidget.insertRow(now_line)
        tableWidget.setRowHeight(now_line, self.graph.UIConfigData()['table_row_height'])

        item = QtWidgets.QTableWidgetItem(train.fullCheci())
        item.setData(-1, train)
        tableWidget.setItem(now_line, 0, item)
        self.trainMapToRow[train] = item

        item = QtWidgets.QTableWidgetItem(train.sfz)
        tableWidget.setItem(now_line, 1, item)

        item = QtWidgets.QTableWidgetItem(train.zdz)
        tableWidget.setItem(now_line, 2, item)

        item = QtWidgets.QTableWidgetItem(train.type)
        tableWidget.setItem(now_line, 3, item)

        mile = train.localMile(self.graph,fullAsDefault=False)
        item = QtWidgets.QTableWidgetItem()
        item.setData(Qt.DisplayRole, mile)
        tableWidget.setItem(now_line, 5, item)

        # train: Train
        spd = train.localSpeed(self.graph,fullAsDefault=False)
        item = QtWidgets.QTableWidgetItem()
        item.setData(Qt.DisplayRole, spd)
        tableWidget.setItem(now_line, 6, item)

        # 修改直接生效
        # check = QtWidgets.QCheckBox()
        # check.setChecked(train.isShow())
        # check.setMinimumSize(1, 1)
        # check.setStyleSheet("QCheckBox{margin:3px}")
        # # check.toggled.connect(lambda x:self._train_show_changed(now_line,tableWidget,x))
        # check.train = train
        # check.toggled.connect(self._train_show_changed)
        # tableWidget.setCellWidget(now_line, 4, check)
        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Line.bool2CheckState(train.isShow()))
        tableWidget.setItem(now_line,4,item)


    def delTrain(self,train:Train):
        """
        2019.07.11新增，从main中移动出来。利用映射表信息快速删除行，并更新映射表。
        不保证要删除的车次在表中存在（因车次筛选器）
        """
        try:
            item = self.trainMapToRow[train]
        except KeyError:
            return
        else:
            self.trainTable.removeRow(item.row())
            del self.trainMapToRow[train]

    def updateShow(self):
        """
        在已知其他不变的情况下，只更新显示项目，以提高效率。
        """
        tableWidget = self.trainTable
        col = 4  # “显示”所在的列
        for row in range(tableWidget.rowCount()):
            train = self.trainByRow(row)
            if train is None:
                continue
            tableWidget.item(row,col).setCheckState(Line.bool2CheckState(train.isShow()))

    def updateRowByNum(self,row:int):
        """
        已知列车对象不变，更新一行的数据。
        """
        # ["车次", "始发", "终到", "类型", "显示", "本线里程",'跨越站数']
        item:QtWidgets.QTableWidgetItem
        train = self.trainByRow(row)
        tableWidget = self.trainTable
        item = tableWidget.item(row,0)
        item.setText(train.fullCheci())

        tableWidget.item(row,1).setText(train.sfz)
        tableWidget.item(row,2).setText(train.zdz)
        tableWidget.item(row,3).setText(train.trainType())
        tableWidget.item(row,4).setCheckState(Line.bool2CheckState(train.isShow()))
        mile = train.localMile(self.graph,fullAsDefault=False)
        tableWidget.item(row,5).setData(Qt.DisplayRole,mile)
        tableWidget.item(row,5).setText(f"{mile:.1f}")
        speed=train.localSpeed(self.graph,fullAsDefault=False)
        tableWidget.item(row,6).setData(Qt.DisplayRole,speed)
        tableWidget.item(row,6).setText(f"{speed:.2f}" if speed!=-1 else 'NA')

    def updateRowByTrain(self,train:Train):
        item:QtWidgets.QTableWidgetItem = self.trainMapToRow[train]
        self.updateRowByNum(item.row())

    def updateAllTrains(self):
        """
        已知不增加减少列车，更新所有行的数据。
        """
        for row in range(self.trainTable.rowCount()):
            self.updateRowByNum(row)

    def addTrainsFromBottom(self,count:int):
        """
        将车次表末尾的count个添加到表格中，已知其他车次信息不变。
        called when: 从运行图添加车次。
        """
        if count==0:
            return
        for train in self.graph._trains[-count:]:
            self.addTrain(train)

    def trainByRow(self,row:int)->Train:
        item = self.trainTable.item(row, 0)
        if item is None:
            return None

        train: Train = item.data(-1)
        return train

    def setCurrentTrain(self,train):
        """
        2019.07.07改用映射表，删除线性算法。
        """
        try:
            item = self.trainMapToRow[train]
        except KeyError:
            # 这不是异常。当车次筛选器有效时，不是所有车次都能在表上找到。
            print("TrainWidget::setCurrentTrain: train not found!",train)
            return
        self.trainTable.setCurrentCell(item.row(),0)
        self.trainTable.item(item.row(),4).setCheckState(Line.bool2CheckState(train.isShow()))


    # slots
    def _current_row_changed(self,row):
        """
        trainTable行变化，解析出列车信息，然后emit信号给main窗口。对应在main的855行
        """
        train = self.trainByRow(row)
        if train is None:
            print("trainWidget::_current_row_changed: train is None.",row)
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

    def _item_changed(self,item:QtWidgets.QTableWidgetItem):
        """
        2019.10.21添加
        """
        if item is None or item.column() != 4:
            return
        train = self.trainTable.item(item.row(),0).data(-1)
        if train is None:
            return
        on=bool(item.checkState())
        train.setIsShow(on)
        self.trainShowChanged.emit(train,on)

    def _train_show_changed(self):
        """
        2019.10.21撤销定义
        """
        print("Warning: TrainWidget::train_show_changed: 取消定义的函数。")
        sender = self.sender()
        train = sender.train
        train.setIsShow(sender.isChecked())
        self.trainShowChanged.emit(train,sender.isChecked())

    def _batch_change_ui(self):
        """
        2019.02.27新增。批量修改【被选中车次】的运行线宽度、颜色。
        """
        tableWidget = self.trainTable
        rows = []
        for idx in tableWidget.selectedIndexes():
            row = idx.row()
            if row not in rows:
                rows.append(row)
        self.batchRows = rows

        if not self.qustion(f"请在上表中选择车次来批量调整线宽、颜色，"
                            f"可用本停靠面板顶上的“筛选”来选择具有指定特征的车次。"
                            f"当前选择的车次个数为*{len(rows)}*，是否继续？"):
            return

        dialog = QtWidgets.QDialog(self)
        self.batchDialog = dialog
        dialog.setWindowTitle('批量调整车次')
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        # 颜色
        hlayout = QtWidgets.QHBoxLayout()
        btnColor = QtWidgets.QPushButton('系统默认')
        self.btnColor = btnColor
        btnColor.clicked.connect(self._select_color)
        btnDefaultColor = QtWidgets.QPushButton('使用默认')
        btnDefaultColor.clicked.connect(self._default_color)
        self.btnDefaultColor = btnDefaultColor
        btnDefaultColor.setEnabled(False)
        hlayout.addWidget(btnColor)
        hlayout.addWidget(btnDefaultColor)
        flayout.addRow('运行线颜色',hlayout)

        # 运行线宽度
        spinWidth = QtWidgets.QDoubleSpinBox()
        spinWidth.setDecimals(2)
        spinWidth.setSingleStep(0.5)
        self.spinWidth = spinWidth
        spinWidth.setMaximumWidth(100)
        flayout.addRow('运行线宽度',spinWidth)

        vlayout.addLayout(flayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        btnOk.clicked.connect(self._batch_change_ok)
        btnCancel.clicked.connect(dialog.close)

        vlayout.addLayout(hlayout)
        dialog.setLayout(vlayout)
        dialog.exec_()

    def _select_color(self):
        color:QtGui.QColor = QtWidgets.QColorDialog.getColor()
        color_str = "#%02X%02X%02X" % (color.red(), color.green(), color.blue())
        self.btnColor.setStyleSheet(f"color:rgb({color.red()},{color.green()},{color.blue()})")
        self.btnColor.setText(color_str)
        self.btnDefaultColor.setEnabled(True)

    def _default_color(self):
        self.btnColor.setStyleSheet("default")
        self.btnColor.setText('系统默认')
        self.btnDefaultColor.setEnabled(False)

    def _batch_change_ok(self):
        for row in self.batchRows:
            train = self.trainByRow(row)
            color_str = self.btnColor.text()
            if color_str == '系统默认':
                color_str = ''
            train.setUI(color=color_str,width=self.spinWidth.value())
            train.updateUI()
        self.batchDialog.close()
        self.showStatus.emit(f'批量修改完成，共修改{len(self.batchRows)}个车次')

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

        if self.main:
            self.main.updating=True
        for i, row in enumerate(rows):
            train = tableWidget.item(row, 0).data(-1)
            self.graph.delTrain(train)
            tableWidget.removeRow(row)
            del self.trainMapToRow[train]
            if self.main:
                self.main.GraphWidget.delTrainLine(train)
                progressDialog.setLabelText(f'正在删除车次({i+1}/{len(rows)}): {train.fullCheci()} ')
                progressDialog.setValue(i + 1)
                if i % 10 == 0:
                    QtCore.QCoreApplication.processEvents()
                if progressDialog.wasCanceled():
                    count = i + 1
                    break
        if self.main:
            self.main.updating=False

        if count:
            self.showStatus.emit(f"成功删除{count}个车次")

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def qustion(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '车次编辑', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

    def _swapRow(self,x,y):
        """
        交换表中的两行x和y。
        precondition: x,y的行有效。
        postcondition: 交换后的item对象仍然不变。
        """
        ncols = self.trainTable.columnCount()
        for c in range(ncols):
            item0 = self.trainTable.takeItem(x,c)
            item1 = self.trainTable.takeItem(y,c)
            self.trainTable.setItem(x,c,item1)
            self.trainTable.setItem(y,c,item0)

    def _move_up(self):
        """
        只处理当前的一个。逐个item的交换。
        """
        row = self.trainTable.currentRow()
        if row <= 0:
            return
        self._swapRow(row,row-1)
        self.trainTable.setCurrentCell(row-1,0)

    def _move_down(self):
        row = self.trainTable.currentRow()
        if row >= self.trainTable.rowCount()-1:
            return
        self._swapRow(row,row+1)
        self.trainTable.setCurrentCell(row+1,0)

    def _save_order(self):
        """
        没有显示的车次，全都放到后面去。记得调整映射表
        """
        origin = self.graph._trains[:]
        newList = []
        for row in range(self.trainTable.rowCount()):
            train = self.trainTable.item(row,0).data(-1)
            origin.remove(train)
            newList.append(train)
        self.graph._trains.clear()
        self.graph._trains = newList + origin  # 剩下的是没有显示的
        self.showStatus.emit('保存车次顺序成功')


"""
2.0.2起新增，更正列车时刻表中错误（主要是点单转换过程中错误）的窗口。
调整的逻辑是:
对于上移下移、交换到发，调整数据的同时微调单元格窗口，目的是保留当前的选择；
其他的每一次调整都将其直接作用在self.train上，然后暴力刷新窗口。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
import sys
from .data.graph import Graph,Train

class CorrectionWidget(QtWidgets.QDialog):
    correctionOK = QtCore.pyqtSignal(Train)
    def __init__(self,train:Train,graph:Graph,parent=None):
        super(CorrectionWidget, self).__init__(parent)
        self.originTrain=train
        self.graph = graph
        self.train=Train(self.graph)
        self.train.coverData(self.originTrain)
        self.initUI()
        self.setData()

    def initUI(self):
        self.setWindowTitle(f'时刻表重排*{self.train.fullCheci()}')
        self.resize(700,800)
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('本功能提供时刻表排序中常见问题的手动更正功能。请先选择要操作的行，然后选择相应的操作。\n'
                                 '说明：上移（下移）功能将所有选中的行从当前位置向上（向下）移动一行；置顶、置底功能保持当前选中的行的顺序不变，而将它们移动到时刻表最前或者最后；反排功能将当前选中的第一行和最后一行之间的所有行顺序反排。')
        label.setWordWrap(True)
        vlayout.addWidget(label)

        hlayout = QtWidgets.QHBoxLayout()
        btnUp=QtWidgets.QPushButton('上移')
        btnDown=QtWidgets.QPushButton("下移")
        btnTop=QtWidgets.QPushButton('置顶')
        btnBottom=QtWidgets.QPushButton('置底')
        hlayout.addWidget(btnUp)
        hlayout.addWidget(btnDown)
        hlayout.addWidget(btnTop)
        hlayout.addWidget(btnBottom)
        vlayout.addLayout(hlayout)

        btnUp.clicked.connect(self._up)
        btnDown.clicked.connect(self._down)
        btnTop.clicked.connect(self._top)
        btnBottom.clicked.connect(self._bottom)

        hlayout = QtWidgets.QHBoxLayout()

        btnExchange = QtWidgets.QPushButton('交换到发')
        btnReverse = QtWidgets.QPushButton('区间反排')
        hlayout.addWidget(btnExchange)
        hlayout.addWidget(btnReverse)

        btnExchange.clicked.connect(self._exchange)
        btnReverse.clicked.connect(self._reverse)
        vlayout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnSelectAll = QtWidgets.QPushButton('全选')
        btnSelectNone = QtWidgets.QPushButton('全不选')
        btnSelectFlip = QtWidgets.QPushButton('反选')
        hlayout.addWidget(btnSelectAll)
        hlayout.addWidget(btnSelectNone)
        hlayout.addWidget(btnSelectFlip)
        vlayout.addLayout(hlayout)

        btnSelectAll.clicked.connect(self._select_all)
        btnSelectNone.clicked.connect(self._select_none)
        btnSelectFlip.clicked.connect(self._select_flip)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(7)
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        tableWidget.setHorizontalHeaderLabels(['选择','站名','到点','开点','停时','区间','备注'])
        for i,s in enumerate((40,100,100,100,80,80,80)):
            tableWidget.setColumnWidth(i,s)
        self.tableWidget = tableWidget
        vlayout.addWidget(tableWidget)

        btnOk = QtWidgets.QPushButton('确定')
        btnRestore = QtWidgets.QPushButton('还原')
        btnCancel = QtWidgets.QPushButton('取消')
        btnOk.clicked.connect(self._ok)
        btnRestore.clicked.connect(self._restore)
        btnCancel.clicked.connect(self.close)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnRestore)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)

        self.setLayout(vlayout)

    def setData(self):
        """
        无条件地将表中数据全部换为当前self.train中的数据。
        """
        self.tableWidget.setRowCount(self.train.stationCount())
        for row,st_dict in enumerate(self.train.stationDicts()):
            self.setTableRow(st_dict,row)

    def setTableRow(self,st_dict,row):
        """
        将ddsj,cfsj以Qt::UserRole形式备注在相应单元格内。
        若停时大于12小时，认为异常，将其标红。
        """
        name, ddsj, cfsj, note = st_dict['zhanming'],st_dict['ddsj'],st_dict['cfsj'],st_dict.get('note','')
        tableWidget = self.tableWidget
        tableWidget.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Qt.Unchecked)
        tableWidget.setItem(row,0,item)

        item = QtWidgets.QTableWidgetItem(name)
        tableWidget.setItem(row,1,item)
        item.setData(Qt.UserRole,st_dict)

        item = QtWidgets.QTableWidgetItem(ddsj.strftime('%H:%M:%S'))
        item.setData(Qt.UserRole,ddsj)
        tableWidget.setItem(row,2,item)

        item = QtWidgets.QTableWidgetItem(cfsj.strftime('%H:%M:%S'))
        item.setData(Qt.UserRole,cfsj)
        tableWidget.setItem(row,3,item)

        dt = self.train.dt(ddsj,cfsj)
        dt_str = self.train.sec2str(dt)
        item = QtWidgets.QTableWidgetItem(dt_str)
        tableWidget.setItem(row,4,item)
        if dt > 3600*12:
            color = QtGui.QColor(Qt.red)
            color.setAlpha(150)
            item.setBackground(QtGui.QBrush(color))

        if row == 0:
            dt_inter_str = '-'
            dt_inter = 0
        else:
            cfsj_last = tableWidget.item(row-1,3).data(Qt.UserRole)
            dt_inter = self.train.dt(cfsj_last,ddsj)
            dt_inter_str = self.train.sec2str(dt_inter)
        item = QtWidgets.QTableWidgetItem(dt_inter_str)
        if dt_inter > 2*3600:
            color = QtGui.QColor(Qt.red)
            color.setAlpha(150)
            item.setBackground(QtGui.QBrush(color))
        tableWidget.setItem(row,5,item)
        tableWidget.setItem(row,6,QtWidgets.QTableWidgetItem(note))

    def updateIntervalTime(self,row:int):
        """
        已知指定行存在，更新它的区间时分。
        """
        if not 0<=row<self.tableWidget.rowCount():
            return
        tableWidget = self.tableWidget
        ddsj = tableWidget.item(row,2).data(Qt.UserRole)
        if row == 0:
            dt_inter_str = '-'
            dt_inter = 0
        else:
            cfsj_last = tableWidget.item(row-1,3).data(Qt.UserRole)
            dt_inter = self.train.dt(cfsj_last,ddsj)
            dt_inter_str = self.train.sec2str(dt_inter)
        item = tableWidget.item(row,5)
        item.setText(dt_inter_str)
        if dt_inter > 2*3600:
            color = QtGui.QColor(Qt.red)
            color.setAlpha(150)
            item.setBackground(QtGui.QBrush(color))
        else:
            item.setBackground(Qt.transparent)


    # slots
    def _up(self):
        tableWidget = self.tableWidget
        for row in range(self.tableWidget.rowCount()):
            if tableWidget.item(row,0).checkState() != Qt.Checked:
                continue
            if row == 0:
                # 直接忽略移动第一行的请求
                continue
            self.train.timetable.insert(row-1,self.train.timetable.pop(row))
            dct = tableWidget.item(row,1).data(Qt.UserRole)
            tableWidget.removeRow(row)
            tableWidget.insertRow(row-1)
            self.setTableRow(dct,row-1)
            tableWidget.item(row-1,0).setCheckState(Qt.Checked)
            self.updateIntervalTime(row)
            self.updateIntervalTime(row+1)

    def _down(self):
        tableWidget = self.tableWidget
        for row in range(self.tableWidget.rowCount()-1,-1,-1):
            if tableWidget.item(row, 0).checkState() != Qt.Checked:
                continue
            if row == tableWidget.rowCount()-1:
                continue
            self.train.timetable.insert(row + 1, self.train.timetable.pop(row))
            dct = tableWidget.item(row, 1).data(Qt.UserRole)
            tableWidget.removeRow(row)
            tableWidget.insertRow(row + 1)
            self.setTableRow(dct, row + 1)
            tableWidget.item(row + 1, 0).setCheckState(Qt.Checked)
            self.updateIntervalTime(row)
            self.updateIntervalTime(row+2)

    def _top(self):
        n=0  # 插入位置
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row,0).checkState() == Qt.Checked:
                self.train.timetable.insert(n,self.train.timetable.pop(row))
                n+=1
        self.setData()

    def _bottom(self):
        n = self.tableWidget.rowCount()-1
        for row in range(self.tableWidget.rowCount()-1,-1,-1):
            if self.tableWidget.item(row,0).checkState() == Qt.Checked:
                self.train.timetable.insert(n,self.train.timetable.pop(row))
                n-=1
            self.updateIntervalTime(n)
            self.updateIntervalTime(row)
        self.setData()

    def _exchange(self):
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row,0).checkState()==Qt.Checked:
                dct = self.train.timetable[row]
                dct['ddsj'],dct['cfsj'] = dct['cfsj'],dct['ddsj']
                self.setTableRow(dct,row)
                self.tableWidget.item(row,0).setCheckState(Qt.Checked)
                self.updateIntervalTime(row)
                self.updateIntervalTime(row+1)

    def _reverse(self):
        low,high=self.tableWidget.rowCount()-1,0
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row,0).checkState()==Qt.Checked:
                if row < low:
                    low=row
                if row > high:
                    high=row
        if low >= high:
            QtWidgets.QMessageBox.warning(self,'错误','无效的选择。请选择多行，本系统将把选择的第一行至'
                                                    '最后一行（均包含）之间的站表排序。')
            return
        print(low,high)
        self.train.timetable = self.train.timetable[:low]\
                               +self.train.timetable[high:low-1:-1]+self.train.timetable[high+1:]
        self.setData()

    def _select_all(self):
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.item(row,0).setCheckState(Qt.Checked)

    def _select_none(self):
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.item(row,0).setCheckState(Qt.Unchecked)

    def _select_flip(self):
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row,0)
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)

    def _restore(self):
        self.train.coverData(self.originTrain)
        self.setData()

    def _ok(self):
        self.originTrain.coverData(self.train)
        self.correctionOK.emit(self.originTrain)
        self.close()



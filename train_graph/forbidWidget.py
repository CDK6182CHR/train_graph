"""
天窗编辑的窗口，可仿照标尺编辑。
"""
from .forbid import Forbid
from PyQt5 import QtWidgets,QtCore
from PyQt5.QtCore import Qt
from datetime import datetime
from .line import Line

class ForbidWidget(QtWidgets.QWidget):
    okClicked = QtCore.pyqtSignal()
    showForbidChanged = QtCore.pyqtSignal(bool,bool)
    currentShowedChanged = QtCore.pyqtSignal(bool) #当前显示的天窗变化发射
    def __init__(self,data:Forbid,parent=None):
        super().__init__(parent)
        self.setWindowTitle('天窗编辑')
        self.data = data
        self.line = data.line()  # type:Line
        self.updating = False
        self.initUI()

    def initUI(self):
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        checkDifferent = QtWidgets.QCheckBox()
        checkDifferent.setChecked(self.data.different())
        self.checkDifferent = checkDifferent
        flayout.addRow('上下行分设',checkDifferent)
        checkDifferent.toggled.connect(self._different_changed)

        checkDown = QtWidgets.QCheckBox('下行')
        checkUp = QtWidgets.QCheckBox("上行")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(checkDown)
        hlayout.addWidget(checkUp)
        checkUp.setChecked(self.data.upShow())
        checkDown.setChecked(self.data.downShow())
        flayout.addRow('显示天窗',hlayout)
        self.checkUpShow = checkUp
        self.checkDownShow = checkDown

        checkDown.toggled.connect(lambda checked: self._show_changed(checked, True))
        checkUp.toggled.connect(lambda checked: self._show_changed(checked, False))

        vlayout.addLayout(flayout)

        label = QtWidgets.QLabel("按Alt+C将本行数据复制到下一行，\n"
                                 "按Alt+Shift+C将本行数据复制到同方向所有行。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        actionCp1 = QtWidgets.QAction('复制数据到下一行(Alt+C)',tableWidget)
        actionCp1.setShortcut('Alt+C')
        tableWidget.addAction(actionCp1)
        actionCp1.triggered.connect(self._copy_1)

        actionCpAll = QtWidgets.QAction('复制数据到本方向所有行(Alt+Shift+C)',tableWidget)
        actionCpAll.setShortcut('Alt+Shift+C')
        tableWidget.addAction(actionCpAll)
        actionCpAll.triggered.connect(self._copy_all)

        self.tableWidget = tableWidget
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        self.tableWidget = tableWidget
        tableWidget.setColumnCount(4)
        for i, s in enumerate((120, 100, 100, 60)):
            tableWidget.setColumnWidth(i, s)
        tableWidget.setHorizontalHeaderLabels(('区间', '开始时间', '结束时间', '时长'))
        self._setTableWidget()
        vlayout.addWidget(self.tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("还原")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)
        btnOk.clicked.connect(self._ok_clicked)
        btnCancel.clicked.connect(self._cancel_clicked)

        self.setLayout(vlayout)

    def setData(self):
        self.updating=True
        self.checkDifferent.setChecked(self.data.different())
        self.checkDownShow.setChecked(self.data.downShow())
        self.checkUpShow.setChecked(self.data.upShow())
        self._setTableWidget()  # 此处效率问题较明显
        self.updating=False

    def _setTableWidget(self):
        tableWidget = self.tableWidget
        tableWidget.setRowCount(2*self.line.stationCount())

        line = self.data.line()
        station_dicts = line.stations
        blocker = "->" if self.data.different() else "<->"

        row = 0
        former_dict = None
        for i, st_dict in enumerate(station_dicts):
            if st_dict["direction"] & line.DownVia:
                if former_dict is not None:
                    self._addTableRow(former_dict["zhanming"], st_dict["zhanming"],
                                      self.data.getInfo(former_dict["zhanming"], st_dict["zhanming"]), blocker,row)
                    row+=1
                former_dict = st_dict

        former_dict = None
        if self.data.different():
            # 上下行不一致，增加上行部分
            for st_dict in reversed(station_dicts):
                if st_dict["direction"] & line.UpVia:
                    if former_dict is not None:
                        self._addTableRow(former_dict["zhanming"], st_dict["zhanming"],
                                          self.data.getInfo(former_dict["zhanming"], st_dict["zhanming"]), blocker,row)
                        row+=1
                    former_dict = st_dict
        tableWidget.setRowCount(row)

    def _addTableRow(self,fazhan,daozhan,node,blocker,row):
        tableWidget:QtWidgets.QTableWidget = self.tableWidget
        tableWidget.setRowHeight(row,30)  # cannot infer to graph

        item = QtWidgets.QTableWidgetItem(f'{fazhan}{blocker}{daozhan}')
        item.setData(-1,[fazhan,daozhan])
        tableWidget.setItem(row,0,item)

        spinBegin = QtWidgets.QTimeEdit()
        spinBegin.setDisplayFormat('hh:mm')
        spinBegin.setMinimumSize(1,1)
        spinEnd = QtWidgets.QTimeEdit()
        spinEnd.setDisplayFormat('hh:mm')
        spinEnd.setMinimumSize(1,1)

        if node is not None:
            begin:datetime = node["begin"]
            beginQ = QtCore.QTime(begin.hour,begin.minute,begin.second)
            end = node["end"]
            endQ = QtCore.QTime(end.hour,end.minute,end.second)
            spinBegin.setTime(beginQ)
            spinEnd.setTime(endQ)
            dt = (end-begin).seconds
            if dt < 0:
                dt += 3600*24
        else:
            dt = 0

        spinBegin.timeChanged.connect(lambda: self._time_changed(tableWidget, row))
        spinEnd.timeChanged.connect(lambda: self._time_changed(tableWidget, row))

        tableWidget.setCellWidget(row,1,spinBegin)
        tableWidget.setCellWidget(row,2,spinEnd)

        item = QtWidgets.QTableWidgetItem('%2d:%02d'%(int(dt/3600),int((dt%3600)/60)))
        tableWidget.setItem(row,3,item)

    def _different_changed(self,checked:bool):
        if self.updating:
            return
        if checked is False:
            flag = self.question("删除所有上行区间数据，用下行区间天窗数据代表双向（单线）数据。"
                                      "是否继续？")
            if not flag:
                self.sender().setChecked(True)
                return
        self.data.setDifferent(checked,del_up=True)
        self.setData()

    def _show_changed(self,checked:bool,down:bool):
        self.data.setShow(checked,down)
        self.showForbidChanged.emit(checked,down)

    def _time_changed(self,tableWidget:QtWidgets.QTableWidget,row:int):
        self.tableWidget.setCurrentCell(row,self.tableWidget.currentColumn())
        spinBegin = tableWidget.cellWidget(row,1)
        spinEnd = tableWidget.cellWidget(row,2)
        beginQ:QtCore.QTime = spinBegin.time()
        endQ = spinEnd.time()

        begin = datetime(1900,1,1,beginQ.hour(),beginQ.minute())
        end = datetime(1900,1,1,endQ.hour(),endQ.minute())
        dt = (end-begin).seconds
        if dt<0:
            dt+=24*3600
        dt /= 60

        tableWidget.item(row,3).setText('%2d:%02d'%(int(dt/60),dt%60))

    def _copy_1(self):
        tableWidget:QtWidgets.QTableWidget = self.tableWidget
        row = tableWidget.currentRow()
        if row == tableWidget.rowCount()-1:
            return
        beginQ = tableWidget.cellWidget(row,1).time()
        endQ = tableWidget.cellWidget(row,2).time()
        row += 1
        tableWidget.setCurrentCell(row,0)
        tableWidget.cellWidget(row,1).setTime(beginQ)
        tableWidget.cellWidget(row,2).setTime(endQ)

    def _copy_all(self):
        tableWidget: QtWidgets.QTableWidget = self.tableWidget
        row = tableWidget.currentRow()
        if row == tableWidget.rowCount() - 1 or row == -1:
            return

        if not self.data.different():
            #上下行不分设，从当前行复制到所有行
            while row < tableWidget.rowCount():
                self._copy_1()
                row += 1
        else:
            #上下行分设，考虑区间上下行问题
            gap = tableWidget.item(row,0).data(-1)
            down = self.line.isDownGap(*gap)
            while row < tableWidget.rowCount()-1:
                row += 1
                row_down = self.line.isDownGap(*tableWidget.item(row,0).data(-1))
                if down != row_down:
                    break
                self._copy_1()

    def _ok_clicked(self):
        tableWidget = self.tableWidget
        self.data.clear()
        for row in range(tableWidget.rowCount()):
            gap = tableWidget.item(row,0).data(-1)
            beginQ = tableWidget.cellWidget(row,1).time()
            endQ = tableWidget.cellWidget(row,2).time()
            begin = datetime(1900, 1, 1, beginQ.hour(), beginQ.minute())
            end = datetime(1900, 1, 1, endQ.hour(), endQ.minute())
            self.data.addForbid(gap[0],gap[1],begin,end)
        if self.data.downShow():
            self.currentShowedChanged.emit(True)
        if self.data.upShow():
            self.currentShowedChanged.emit(False)

    def _cancel_clicked(self):
        if not self.question('将本线标尺信息恢复为保存的信息，当前未保存的改动将会丢失。是否继续？'):
            return
        self.setData()

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '天窗编辑', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default




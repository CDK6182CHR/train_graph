"""
天窗编辑的窗口，可仿照标尺编辑。
"""
from .data.forbid import Forbid
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from datetime import datetime
from .data.line import Line
from .utility import PECellWidget,PECelledTable,PEControlledTable,CellWidgetFactory


class ForbidTabWidget(QtWidgets.QTabWidget):
    """
    2020.01.23新增，由mainWindow直接调用的天窗编辑窗口，聚合两类天窗。
    转发下层的信号，添加forbid对象。接受Line对象（注意：不可接受Graph，因LineDB中的调用）
    信号处理只需要关注mainWindow。
    """
    # okClicked = QtCore.pyqtSignal(Forbid)
    showForbidChanged = QtCore.pyqtSignal(Forbid, bool, bool)
    currentShowedChanged = QtCore.pyqtSignal(Forbid, bool)  # 当前显示的天窗变化发射

    def __init__(self, line: Line, parent=None):
        super(ForbidTabWidget, self).__init__(parent)
        self.setWindowTitle("天窗编辑")
        self.line = line  # type:Line
        self.widget1 = ...  # type: ForbidWidget
        self.widget2 = ...  # type: ForbidWidget
        self.initUI()

    def initUI(self):
        self.widget1 = ForbidWidget(self.line.forbid, self)
        self.widget2 = ForbidWidget(self.line.forbid2, self)
        # 转发信号
        for w in (self.widget1, self.widget2):
            w.currentShowedChanged.connect(self.currentShowedChanged.emit)
            w.showForbidChanged.connect(self.showForbidChanged.emit)
        self.addTab(self.widget1, "综合维修")
        self.addTab(self.widget2, "综合施工")

    def setData(self):
        self.widget1.setData()
        self.widget2.setData()


class ForbidWidget(QtWidgets.QWidget):
    okClicked = QtCore.pyqtSignal()
    showForbidChanged = QtCore.pyqtSignal(Forbid, bool, bool)
    currentShowedChanged = QtCore.pyqtSignal(Forbid, bool)  # 当前显示的天窗变化发射

    def __init__(self, data: Forbid, parent=None):
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
        flayout.addRow('上下行分设', checkDifferent)
        checkDifferent.toggled.connect(self._different_changed)

        checkDown = QtWidgets.QCheckBox('下行')
        checkUp = QtWidgets.QCheckBox("上行")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(checkDown)
        hlayout.addWidget(checkUp)
        checkUp.setChecked(self.data.upShow())
        checkDown.setChecked(self.data.downShow())
        flayout.addRow('显示天窗', hlayout)
        self.checkUpShow = checkUp
        self.checkDownShow = checkDown

        checkDown.toggled.connect(lambda checked: self._show_changed(checked, True))
        checkUp.toggled.connect(lambda checked: self._show_changed(checked, False))

        spinDefault = QtWidgets.QSpinBox()
        spinDefault.setSingleStep(10)
        spinDefault.setRange(0,1000)
        spinDefault.setValue(120)
        self.spinDefault = spinDefault
        spinDefault.setToolTip("用于从天窗开始时间计算结束时间（Alt+E），或者从结束时间计算开始时间。（Alt+R）")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinDefault)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        flayout.addRow("默认时长",hlayout)

        vlayout.addLayout(flayout)

        # label = QtWidgets.QLabel("按Alt+C将本行数据复制到下一行，\n"
        #                          "按Alt+Shift+C将本行数据复制到同方向所有行。")
        # label.setWordWrap(True)
        # vlayout.addWidget(label)

        tableWidget = PECelledTable()
        actionCp1 = QtWidgets.QAction('复制数据到下一行(Alt+C)', tableWidget)
        tableWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        actionCp1.setShortcut('Alt+C')
        tableWidget.addAction(actionCp1)
        actionCp1.triggered.connect(self._copy_1)

        actionCpAll = QtWidgets.QAction('复制数据到本方向所有行(Alt+Shift+C)', tableWidget)
        actionCpAll.setShortcut('Alt+Shift+C')
        tableWidget.addAction(actionCpAll)
        actionCpAll.triggered.connect(self._copy_all)

        action = QtWidgets.QAction("计算结束时间(Alt+E)",tableWidget)
        action.setShortcut('Alt+E')
        tableWidget.addAction(action)
        action.triggered.connect(self._calculate_forward)

        action = QtWidgets.QAction("计算开始时间(Alt+R)",tableWidget)
        action.setShortcut("Alt+R")
        tableWidget.addAction(action)
        action.triggered.connect(self._calculate_reverse)

        action = QtWidgets.QAction("计算所有结束时间(Alt+Shift+E)", tableWidget)
        action.setShortcut('Alt+Shift+E')
        tableWidget.addAction(action)
        action.triggered.connect(self._calculate_forward_all)

        action = QtWidgets.QAction("计算开始时间(Alt+Shift+R)", tableWidget)
        action.setShortcut("Alt+Shift+R")
        tableWidget.addAction(action)
        action.triggered.connect(self._calculate_reverse_all)

        self.tableWidget = tableWidget
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        tableWidget.setColumnCount(4)
        for i, s in enumerate((120, 80, 80, 60)):
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
        self.updating = True
        self.checkDifferent.setChecked(self.data.different())
        self.checkDownShow.setChecked(self.data.downShow())
        self.checkUpShow.setChecked(self.data.upShow())
        self._setTableWidget()  # 此处效率问题较明显
        self.updating = False

    def _setTableWidget(self):
        tableWidget = self.tableWidget
        tableWidget.setRowCount(2 * self.line.stationCount())

        line = self.data.line()
        station_dicts = line.stations
        blocker = "->" if self.data.different() else "<->"

        row = 0
        former_dict = None
        for i, st_dict in enumerate(station_dicts):
            if st_dict["direction"] & line.DownVia:
                if former_dict is not None:
                    self._addTableRow(former_dict["zhanming"], st_dict["zhanming"],
                                      self.data.getInfo(former_dict["zhanming"], st_dict["zhanming"]), blocker, row)
                    row += 1
                former_dict = st_dict

        former_dict = None
        if self.data.different():
            # 上下行不一致，增加上行部分
            for st_dict in reversed(station_dicts):
                if st_dict["direction"] & line.UpVia:
                    if former_dict is not None:
                        self._addTableRow(former_dict["zhanming"], st_dict["zhanming"],
                                          self.data.getInfo(former_dict["zhanming"], st_dict["zhanming"]), blocker, row)
                        row += 1
                    former_dict = st_dict
        tableWidget.setRowCount(row)

    def _addTableRow(self, fazhan, daozhan, node, blocker, row):
        tableWidget: PECelledTable = self.tableWidget
        tableWidget.setRowHeight(row, 30)  # cannot infer to graph

        item = QtWidgets.QTableWidgetItem(f'{fazhan}{blocker}{daozhan}')
        item.setData(-1, [fazhan, daozhan])
        tableWidget.setItem(row, 0, item)

        spinBegin:QtWidgets.QTimeEdit = CellWidgetFactory.new(QtWidgets.QTimeEdit)
        spinBegin.setDisplayFormat('hh:mm')
        spinBegin.setMinimumSize(1, 1)
        spinEnd:QtWidgets.QTimeEdit = CellWidgetFactory.new(QtWidgets.QTimeEdit)
        spinEnd.setDisplayFormat('hh:mm')
        spinEnd.setMinimumSize(1, 1)

        if node is not None:
            begin: datetime = node["begin"]
            beginQ = QtCore.QTime(begin.hour, begin.minute, begin.second)
            end = node["end"]
            endQ = QtCore.QTime(end.hour, end.minute, end.second)
            spinBegin.setTime(beginQ)
            spinEnd.setTime(endQ)
            dt = (end - begin).seconds
            if dt < 0:
                dt += 3600 * 24
        else:
            dt = 0

        spinBegin.timeChanged.connect(lambda: self._time_changed(tableWidget, row))
        spinEnd.timeChanged.connect(lambda: self._time_changed(tableWidget, row))

        tableWidget.setCellWidget(row, 1, spinBegin)
        tableWidget.setCellWidget(row, 2, spinEnd)

        item = QtWidgets.QTableWidgetItem('%2d:%02d' % (int(dt / 3600), int((dt % 3600) / 60)))
        tableWidget.setItem(row, 3, item)

    def _different_changed(self, checked: bool):
        if self.updating:
            return
        if checked is False:
            flag = self.question("删除所有上行区间数据，用下行区间天窗数据代表双向（单线）数据。"
                                 "是否继续？")
            if not flag:
                self.sender().setChecked(True)
                return
        self.data.setDifferent(checked, del_up=True)
        self.setData()

    def _show_changed(self, checked: bool, down: bool):
        self.data.setShow(checked, down)
        self.showForbidChanged.emit(self.data, checked, down)

    def _time_changed(self, tableWidget: QtWidgets.QTableWidget, row: int):
        self.tableWidget.setCurrentCell(row, self.tableWidget.currentColumn())
        spinBegin = tableWidget.cellWidget(row, 1)
        spinEnd = tableWidget.cellWidget(row, 2)
        beginQ: QtCore.QTime = spinBegin.time()
        endQ = spinEnd.time()

        begin = datetime(1900, 1, 1, beginQ.hour(), beginQ.minute())
        end = datetime(1900, 1, 1, endQ.hour(), endQ.minute())
        dt = (end - begin).seconds
        if dt < 0:
            dt += 24 * 3600
        dt /= 60

        tableWidget.item(row, 3).setText('%2d:%02d' % (int(dt / 60), dt % 60))

    def _copy_1(self):
        tableWidget: QtWidgets.QTableWidget = self.tableWidget
        row = tableWidget.currentRow()
        if not 0 <= row < tableWidget.rowCount() - 1:
            return
        beginQ:QtWidgets.QSpinBox = tableWidget.cellWidget(row, 1).time()
        endQ = tableWidget.cellWidget(row, 2).time()
        row += 1
        tableWidget.setCurrentCell(row, 0)
        tableWidget.cellWidget(row, 1).setTime(beginQ)
        tableWidget.cellWidget(row, 2).setTime(endQ)

    def _copy_all(self):
        tableWidget: QtWidgets.QTableWidget = self.tableWidget
        row = tableWidget.currentRow()
        if row == tableWidget.rowCount() - 1 or row == -1:
            return

        if not self.data.different():
            # 上下行不分设，从当前行复制到所有行
            while row < tableWidget.rowCount():
                self._copy_1()
                row += 1
        else:
            # 上下行分设，考虑区间上下行问题
            gap = tableWidget.item(row, 0).data(-1)
            down = self.line.isDownGap(*gap)
            while row < tableWidget.rowCount() - 1:
                row += 1
                row_down = self.line.isDownGap(*tableWidget.item(row, 0).data(-1))
                if down != row_down:
                    break
                self._copy_1()

    def _calculate_forward(self):
        """
        正向计算天窗时长，即结束时间。Alt+E
        """
        row = self.tableWidget.currentRow()
        if 0<=row<self.tableWidget.rowCount():
            self._calculateForward(row)

    def _calculateForward(self,row):
        """
        保证row有效。
        """
        length = self.spinDefault.value()
        start:QtCore.QTime = self.tableWidget.cellWidget(row,1).time()
        h = start.hour()
        m = start.minute() + length
        h = (h+m//60)%24
        m %= 60
        self.tableWidget.cellWidget(row,2).setTime(QtCore.QTime(h,m))

    def _calculate_reverse(self):
        """
        反向计算，由结束时间和默认时长计算开始时间。Alt+R
        """
        row = self.tableWidget.currentRow()
        if 0 <= row < self.tableWidget.rowCount():
            self._calculateReverse(row)

    def _calculateReverse(self,row):
        """
        保证row有效。
        """
        length = self.spinDefault.value()
        end: QtCore.QTime = self.tableWidget.cellWidget(row, 2).time()
        h = end.hour()
        m = end.minute() - length
        h = (h + m // 60) % 24
        m %= 60
        self.tableWidget.cellWidget(row, 1).setTime(QtCore.QTime(h, m))

    def _calculate_forward_all(self):
        if not self.question("此操作根据设置的默认时间和各行的开始时间，自动设置[所有区间]的天窗结束时间，将覆盖此前手工设定的天窗结束时间。是否继续？"):
            return
        for row in range(self.tableWidget.rowCount()):
            self._calculateForward(row)

    def _calculate_reverse_all(self):
        if not self.question("此操作根据设置的默认时间和各行的结束时间，自动设置[所有区间]的天窗开始时间，将覆盖此前手工设定的天窗开始时间。是否继续？"):
            return
        for row in range(self.tableWidget.rowCount()):
            self._calculateReverse(row)

    def _ok_clicked(self):
        tableWidget = self.tableWidget
        self.data.clear()
        for row in range(tableWidget.rowCount()):
            gap = tableWidget.item(row, 0).data(-1)
            beginQ = tableWidget.cellWidget(row, 1).time()
            endQ = tableWidget.cellWidget(row, 2).time()
            begin = datetime(1900, 1, 1, beginQ.hour(), beginQ.minute())
            end = datetime(1900, 1, 1, endQ.hour(), endQ.minute())
            self.data.addForbid(gap[0], gap[1], begin, end)
        if self.data.downShow():
            self.currentShowedChanged.emit(self.data, True)
        if self.data.upShow():
            self.currentShowedChanged.emit(self.data, False)

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

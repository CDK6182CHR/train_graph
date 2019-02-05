"""
抽离线路编辑部分的模块。
2018.12.14修改：不再依赖于main模块。
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
import sys
from line import Line

class LineWidget(QtWidgets.QWidget):
    showStatus = QtCore.pyqtSignal(str)
    lineChangedApplied = QtCore.pyqtSignal()
    def __init__(self,line:Line):
        super().__init__()
        self.line = line

    def initWidget(self):
        """
        add arribute to lineWidget:
        btnOk,btnReturn,tableWidget,nameEdit,line
        """
        line = self.line

        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        label = QtWidgets.QLabel("线路名称")
        lineEdit = QtWidgets.QLineEdit(line.name)
        self.nameEdit = lineEdit
        flayout.addRow(label, lineEdit)

        tableWidget = QtWidgets.QTableWidget()

        tableWidget.setEditTriggers(tableWidget.CurrentChanged)
        self.tableWidget = tableWidget

        tableWidget.setColumnCount(5)
        tableWidget.setHorizontalHeaderLabels(["站名", "里程", "等级", "显示", "单向站"])

        tableWidget.setColumnWidth(0, 100)
        tableWidget.setColumnWidth(1, 80)
        tableWidget.setColumnWidth(2, 60)
        tableWidget.setColumnWidth(3, 40)
        tableWidget.setColumnWidth(4, 80)

        tableWidget.setRowCount(line.stationCount())

        self._setLineTable()

        vlayout.addLayout(flayout)
        vlayout.addWidget(tableWidget)

        btnAdd = QtWidgets.QPushButton("添加(前)")
        btnAdd.setMinimumWidth(80)
        btnAddL = QtWidgets.QPushButton("添加(后)")
        btnAddL.setMinimumWidth(80)
        btnDel = QtWidgets.QPushButton("删除站")
        btnDel.setMinimumWidth(50)
        btnAdd.clicked.connect(lambda: self._add_station(tableWidget))
        btnAddL.clicked.connect(lambda: self._add_station(tableWidget, True))
        btnDel.clicked.connect(lambda: self._del_station(tableWidget))

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnAddL)
        hlayout.addWidget(btnDel)

        btnOk = QtWidgets.QPushButton("确定")
        btnOk.setMaximumWidth(50)
        btnReturn = QtWidgets.QPushButton("还原")
        btnReturn.setMaximumWidth(50)

        btnReturn.clicked.connect(lambda: self._discard_line_info_change(tableWidget,line))
        btnOk.clicked.connect(self._apply_line_info_change)

        self.btnReturn = btnReturn
        self.btnOk = btnOk

        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnReturn)
        vlayout.addLayout(hlayout)

        self.setLayout(vlayout)

    def setData(self):
        """
        更新所有数据，不重新创建对象。
        """
        self.nameEdit.setText(self.line.name)
        self._setLineTable()

    def updateData(self):
        """
        逐行检查表数据，如果没有变化就不修改了。
        """
        self.nameEdit.setText(self.line.name)
        self.tableWidget.setRowCount(self.line.stationCount())
        for row in range(self.tableWidget.rowCount()):
            dct = self.line.stationDictByIndex(row)
            item = self.tableWidget.item(row,0)
            if item is not None:
                self._updateTableRow(dct,row)
            else:
                self._setLineTable(row+1)
                break

    def _updateTableRow(self,dct,row:int):
        """
        已知当前行的item, cellWidget存在
        """
        self.tableWidget.item(row,0).setText(dct["zhanming"])
        self.tableWidget.cellWidget(row, 1).setValue(dct["licheng"])
        self.tableWidget.cellWidget(row, 2).setValue(dct["dengji"])
        self.tableWidget.cellWidget(row, 3).setChecked(dct.get('show', True))
        self.tableWidget.cellWidget(row, 4).setCurrentIndex(dct.get('direction', 0x3))

    def _setLineTable(self,start_index=0):
        tableWidget = self.tableWidget
        line = self.line

        now_line = start_index
        for stationDict in line.stationDicts(start_index):

            item = QtWidgets.QTableWidgetItem(stationDict["zhanming"])
            tableWidget.setItem(now_line, 0, item)

            spin1 = QtWidgets.QDoubleSpinBox()
            spin1.setRange(-9999.0, 9999.0)
            spin1.setValue(stationDict["licheng"])
            spin1.setDecimals(1)
            tableWidget.setCellWidget(now_line, 1, spin1)
            spin1.setMinimumSize(10, 10)

            spin2 = QtWidgets.QSpinBox()
            spin2.setValue(stationDict["dengji"])
            spin2.setRange(0, 20)
            tableWidget.setCellWidget(now_line, 2, spin2)
            spin2.setMinimumSize(10, 10)

            check = QtWidgets.QCheckBox()
            check.setMinimumSize(1,1)
            check.setMinimumHeight(10)
            try:
                stationDict["show"]
            except KeyError:
                stationDict["show"] = True
            check.setChecked(stationDict["show"])
            check.setStyleSheet("QCheckBox{margin:3px}")
            tableWidget.setCellWidget(now_line, 3, check)

            combo = QtWidgets.QComboBox()
            combo.setMinimumSize(1,1)
            combo.addItems(["不通过", "下行", "上行", "上下行"])
            try:
                stationDict["direction"]
            except KeyError:
                stationDict["direction"] = 0x3
            combo.setCurrentIndex(stationDict["direction"])
            combo.setStyleSheet("QComboBox{margin:3px}")
            tableWidget.setCellWidget(now_line, 4, combo)

            tableWidget.setRowHeight(now_line, 30)
            now_line += 1


    #slots
    def _add_station(self, tableWidget: QtWidgets.QTableWidget, later: bool = False):
        num = tableWidget.currentIndex().row()
        if later:
            num += 1

        tableWidget.insertRow(num)

        spin1 = QtWidgets.QDoubleSpinBox()
        spin1.setRange(-9999.0, 9999.0)
        spin1.setDecimals(1)
        tableWidget.setCellWidget(num, 1, spin1)

        spin2 = QtWidgets.QSpinBox()
        spin2.setRange(0, 20)
        tableWidget.setCellWidget(num, 2, spin2)
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)

        check = QtWidgets.QCheckBox()
        check.setChecked(True)
        check.setStyleSheet("QCheckBox{margin:3px}")
        tableWidget.setCellWidget(num, 3, check)

        combo = QtWidgets.QComboBox()
        combo.addItems(["不通过", "下行", "上行", "上下行"])
        combo.setCurrentIndex(3)
        combo.setStyleSheet("QComboBox{margin:3px}")
        tableWidget.setCellWidget(num, 4, combo)

        tableWidget.setRowHeight(num, 30)

    def _del_station(self, tableWidget: QtWidgets.QTableWidget):
        tableWidget.removeRow(tableWidget.currentIndex().row())

    def _discard_line_info_change(self, tableWidget,line):
        if not self.qustion("是否恢复线路信息？当前所有修改都将丢失。"):
            return
        self._setLineTable()

    def _apply_line_info_change(self):
        """
        线路信息确定
        """
        line = self.line
        tableWidget = self.tableWidget
        nameEdit = self.nameEdit
        name = nameEdit.text()
        line.setLineName(name)

        # 应用修改
        self.showStatus.emit("正在更新线路数据")

        adjust_miles = False
        new_line = Line(name)

        for i in range(tableWidget.rowCount()):
            zhanming = tableWidget.item(i, 0).text()
            licheng = tableWidget.cellWidget(i, 1).value()
            dengji = tableWidget.cellWidget(i, 2).value()
            show = True if tableWidget.cellWidget(i, 3).isChecked() else False
            direction = tableWidget.cellWidget(i, 4).currentIndex()

            if i == 0 and licheng != 0.0:
                if self.qustion("本线起始里程不为0，是否调整所有车站里程以使起始站里程归零？", False):
                    adjust_miles = True

            if (i == 0 or i == tableWidget.rowCount() - 1) and direction != 0x3:
                self._derr("首末站必须设为双向通过。已自动修改。")
                direction = Line.DownVia | Line.UpVia

            if new_line.stationExisted(zhanming):
                # 禁止站名重复
                self._derr("本线已存在站名：{}，请重新设置站名！\n在第{}行。".format(zhanming, i + 1))
                return

            info = {
                "zhanming": zhanming,
                "licheng": licheng,
                "dengji": dengji,
                "show": show,
                "direction": direction,
            }
            new_line.addStationDict(info)

        if adjust_miles:
            new_line.adjustLichengTo0()

        line.copyData(new_line)
        self.updateData()

        # 2018.12.14将确认信息后的操作移动回主窗口
        self.lineChangedApplied.emit()

        self.showStatus.emit("线路信息更新完毕")

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def qustion(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '列车运行图系统', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

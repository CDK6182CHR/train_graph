"""
抽离线路编辑部分的模块。
2018.12.14修改：不再依赖于main模块。
2.0.2开始新增办客、办货的选项，默认情况都是True。第一次读取时使用setdefault。
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .data.line import Line

class LineWidget(QtWidgets.QWidget):
    showStatus = QtCore.pyqtSignal(str)
    lineChangedApplied = QtCore.pyqtSignal()
    LineApplied = QtCore.pyqtSignal(Line)
    lineNameChanged = QtCore.pyqtSignal(Line,str,str)  # new,old 2019.10.08新增
    def __init__(self,line:Line):
        super().__init__()
        self.line = line
        self.toSave = False  # 2019.10.07新增

    def setLine(self,line:Line):
        """
        2019.10.07新增。
        重新设置line数据，并更新界面。
        """
        self.line=line
        self.setData()


    def initWidget(self):
        """
        add attributes to lineWidget:
        btnOk,btnReturn,tableWidget,nameEdit,line
        """
        line = self.line

        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        label = QtWidgets.QLabel("线路名称")
        lineEdit = QtWidgets.QLineEdit(line.name)
        lineEdit.textChanged.connect(self.changed)
        self.nameEdit = lineEdit
        flayout.addRow(label, lineEdit)

        tableWidget = QtWidgets.QTableWidget()

        tableWidget.setEditTriggers(tableWidget.CurrentChanged)
        self.tableWidget = tableWidget

        tableWidget.setColumnCount(7)
        tableWidget.setHorizontalHeaderLabels(["站名", "里程", "等级", "显示", "单向站","办客","办货"])
        tableWidget.itemChanged.connect(self.changed)

        tableWidget.setColumnWidth(0, 100)
        tableWidget.setColumnWidth(1, 100)
        tableWidget.setColumnWidth(2, 40)
        tableWidget.setColumnWidth(3, 40)
        tableWidget.setColumnWidth(4, 80)
        tableWidget.setColumnWidth(5, 50)
        tableWidget.setColumnWidth(6, 50)

        tableWidget.setRowCount(line.stationCount())

        self._setLineTable()

        vlayout.addLayout(flayout)
        vlayout.addWidget(tableWidget)

        btnAdd = QtWidgets.QPushButton("前插站")
        btnAdd.setMinimumWidth(50)
        btnAddL = QtWidgets.QPushButton("后插站")
        btnAddL.setMinimumWidth(50)
        btnDel = QtWidgets.QPushButton("删除站")
        btnDel.setMinimumWidth(50)
        btnAdd.clicked.connect(lambda: self._add_station(tableWidget))
        btnAddL.clicked.connect(lambda: self._add_station(tableWidget, True))
        btnDel.clicked.connect(lambda: self._del_station(tableWidget))

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnAddL)
        hlayout.addWidget(btnDel)
        vlayout.addLayout(hlayout)

        hlayout=QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnOk.setMinimumWidth(50)
        btnReturn = QtWidgets.QPushButton("还原")
        btnReturn.setMinimumWidth(50)
        btnNotes = QtWidgets.QPushButton("注释")
        btnNotes.setMinimumWidth(50)

        btnReturn.clicked.connect(lambda: self._discard_line_info_change(tableWidget,line))
        btnOk.clicked.connect(self.apply_line_info_change)
        btnNotes.clicked.connect(self._edit_notes)

        self.btnReturn = btnReturn
        self.btnOk = btnOk

        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnReturn)
        hlayout.addWidget(btnNotes)
        vlayout.addLayout(hlayout)

        self.setLayout(vlayout)

    def setData(self):
        """
        更新所有数据，不重新创建对象。
        """
        self.nameEdit.setText(self.line.name)
        self.tableWidget.setRowCount(self.line.stationCount())
        self._setLineTable()
        self.toSave=False

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

    def changed(self):
        self.toSave=True

    def _updateTableRow(self,dct,row:int):
        """
        已知当前行的item, cellWidget存在
        """
        self.tableWidget.item(row,0).setText(dct["zhanming"])
        self.tableWidget.cellWidget(row, 1).setValue(dct["licheng"])
        self.tableWidget.cellWidget(row, 2).setValue(dct["dengji"])
        self.tableWidget.cellWidget(row, 3).setChecked(dct.get('show', True))
        self.tableWidget.cellWidget(row, 4).setCurrentIndex(dct.get('direction', 0x3))
        self.tableWidget.item(row,5).setCheckState(Qt.Checked if dct.setdefault("passenger",True)
                                                   else Qt.Unchecked)
        self.tableWidget.item(row,6).setCheckState(Qt.Checked if dct.setdefault("freight", True)
                                                    else Qt.Unchecked)

    def _setLineTable(self,start_index=0):
        tableWidget = self.tableWidget
        line = self.line

        now_line = start_index
        for stationDict in line.stationDicts(start_index):

            item = QtWidgets.QTableWidgetItem(stationDict["zhanming"])
            tableWidget.setItem(now_line, 0, item)

            spin1 = QtWidgets.QDoubleSpinBox()
            spin1.setRange(-9999.000, 9999.000)
            spin1.setDecimals(3)
            spin1.setValue(stationDict["licheng"])
            tableWidget.setCellWidget(now_line, 1, spin1)
            spin1.setMinimumSize(10, 10)
            spin1.valueChanged.connect(self.changed)

            spin2 = QtWidgets.QSpinBox()
            spin2.setValue(stationDict["dengji"])
            spin2.setRange(0, 20)
            tableWidget.setCellWidget(now_line, 2, spin2)
            spin2.setMinimumSize(10, 10)
            spin2.valueChanged.connect(self.changed)

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
            check.toggled.connect(self.changed)

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
            combo.currentTextChanged.connect(self.changed)

            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(Line.bool2CheckState(stationDict.setdefault("passenger",True)))
            tableWidget.setItem(now_line,5,item)

            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(Line.bool2CheckState(stationDict.setdefault("freight", True)))
            tableWidget.setItem(now_line, 6, item)

            tableWidget.setRowHeight(now_line, 30)  # cannot infer to graph
            now_line += 1


    #slots
    def _add_station(self, tableWidget: QtWidgets.QTableWidget, later: bool = False):
        num = tableWidget.currentIndex().row()
        if later:
            num += 1

        tableWidget.insertRow(num)
        tableWidget.setItem(num,0,QtWidgets.QTableWidgetItem(''))

        spin1 = QtWidgets.QDoubleSpinBox()
        spin1.setRange(-9999.0, 9999.0)
        spin1.setDecimals(3)
        tableWidget.setCellWidget(num, 1, spin1)
        spin1.valueChanged.connect(self.changed)

        spin2 = QtWidgets.QSpinBox()
        spin2.setRange(0, 20)
        tableWidget.setCellWidget(num, 2, spin2)
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)
        spin2.valueChanged.connect(self.changed)

        check = QtWidgets.QCheckBox()
        check.setChecked(True)
        check.setStyleSheet("QCheckBox{margin:3px}")
        tableWidget.setCellWidget(num, 3, check)
        check.toggled.connect(self.changed)

        combo = QtWidgets.QComboBox()
        combo.addItems(["不通过", "下行", "上行", "上下行"])
        combo.setCurrentIndex(3)
        combo.setStyleSheet("QComboBox{margin:3px}")
        tableWidget.setCellWidget(num, 4, combo)
        combo.currentIndexChanged.connect(self.changed)

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Line.bool2CheckState(True))
        tableWidget.setItem(num, 5, item)

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(True)
        tableWidget.setItem(num, 6, item)

        tableWidget.setRowHeight(num, 30)  # cannot infer to graph

    def _del_station(self, tableWidget: QtWidgets.QTableWidget):
        tableWidget.removeRow(tableWidget.currentIndex().row())

    def _discard_line_info_change(self, tableWidget,line):
        if not self.qustion("是否恢复线路信息？当前所有修改都将丢失。"):
            return
        self._setLineTable()
        self.toSave=False

    def _edit_notes(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('线路数据注释')
        self.noteDialog = dialog

        label = QtWidgets.QLabel('此处可编辑线路的注释信息。如果当前线路被加入数据库，则这些信息也会加入。'
                                 '在本页面点击确定直接生效。')
        label.setWordWrap(True)

        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        authorEdit = QtWidgets.QLineEdit()
        authorEdit.setText(self.line.getNotes()['author'])
        self.authorEdit = authorEdit
        flayout.addRow('贡献者',authorEdit)

        versionEdit = QtWidgets.QLineEdit()
        versionEdit.setText(self.line.getNotes()['version'])
        self.versionEdit = versionEdit
        flayout.addRow('版本',versionEdit)

        vlayout.addLayout(flayout)
        vlayout.addWidget(QtWidgets.QLabel('其他说明'))

        noteEdit = QtWidgets.QTextEdit()
        self.noteEdit = noteEdit
        vlayout.addWidget(noteEdit)
        noteEdit.setText(self.line.getNotes()['note'])

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton('确定')
        hlayout.addWidget(btnOk)
        btnOk.clicked.connect(self._edit_note_ok)

        btnCancel = QtWidgets.QPushButton('取消')
        hlayout.addWidget(btnCancel)
        btnCancel.clicked.connect(dialog.close)
        vlayout.addLayout(hlayout)
        dialog.setLayout(vlayout)
        dialog.exec_()

    def _edit_note_ok(self):
        self.line.getNotes()['author']=self.authorEdit.text()
        self.line.getNotes()['version']=self.versionEdit.text()
        self.line.getNotes()['note']=self.noteEdit.toPlainText()
        self.noteDialog.close()

    def apply_line_info_change(self):
        """
        线路信息确定
        """
        line = self.line
        tableWidget = self.tableWidget
        nameEdit = self.nameEdit
        name = nameEdit.text()
        oldName = line.name
        line.setLineName(name)
        if name != oldName:
            self.lineNameChanged.emit(self.line,name,oldName)

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
                "passenger":bool(tableWidget.item(i,5).checkState()),
                "freight":bool(tableWidget.item(i,6).checkState())
            }
            new_line.addStationDict(info)

        if adjust_miles:
            new_line.adjustLichengTo0()

        line.copyData(new_line)
        self.updateData()

        # 2018.12.14将确认信息后的操作移动回主窗口
        self.lineChangedApplied.emit()
        self.LineApplied.emit(self.line)

        self.showStatus.emit("线路信息更新完毕")
        self.toSave=False

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

"""
抽离线路编辑部分的模块。
2018.12.14修改：不再依赖于main模块。
2.0.2开始新增办客、办货的选项，默认情况都是True。第一次读取时使用setdefault。
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .data.line import Line,LineStation
from .utility import PECelledTable,PECellWidget,CellWidgetFactory,PEControlledTable


class LineTable(PEControlledTable):
    def __init__(self,parent=None):
        super(LineTable, self).__init__(meta=PECelledTable,parent=parent)

    def insertRow(self, row):
        super(LineTable, self).insertRow(row)
        self.setItem(row, 0, QtWidgets.QTableWidgetItem(''))

        spin1 = CellWidgetFactory.new(QtWidgets.QDoubleSpinBox)
        spin1.setRange(-9999.0, 9999.0)
        spin1.setDecimals(3)
        self.setCellWidget(row, 1, spin1)
        # spin1.valueChanged.connect(self.changed)

        item = QtWidgets.QTableWidgetItem()
        # item.setData()
        self.setItem(row, 2, item)

        spin2 = CellWidgetFactory.new(QtWidgets.QSpinBox)
        spin2.setRange(0, 20)
        self.setCellWidget(row, 3, spin2)
        # spin2.valueChanged.connect(self.changed)

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Qt.Checked)
        self.setItem(row, 4, item)

        combo = CellWidgetFactory.new(QtWidgets.QComboBox)  # type:QtWidgets.QComboBox
        combo.addItems(["不通过", "下行", "上行", "上下行"])
        combo.setCurrentIndex(3)
        combo.setStyleSheet("QComboBox{margin:3px}")
        self.setCellWidget(row, 5, combo)
        # combo.currentIndexChanged.connect(self.changed)

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Line.bool2CheckState(True))
        self.setItem(row, 6, item)

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Line.bool2CheckState(True))
        self.setItem(row, 7, item)

    def exchangeRow(self,row1:int,row2:int):
        super(LineTable, self).exchangeRow(row1,row2)
        # 只需要重写交换cellWidget部分
        # value()方法
        for c in (1,3):
            v = self._tw.cellWidget(row1,c).value()
            self._tw.cellWidget(row1,c).setValue(self._tw.cellWidget(row2,c).value())
            self._tw.cellWidget(row2,c).setValue(v)
        # currentIndex()方法
        for c in (5,):
            i = self._tw.cellWidget(row1,c).currentIndex()
            self._tw.cellWidget(row1,c).setCurrentIndex(self._tw.cellWidget(row2,c).currentIndex())
            self._tw.cellWidget(row2,c).setCurrentIndex(i)


class LineWidget(QtWidgets.QWidget):
    showStatus = QtCore.pyqtSignal(str)
    lineChangedApplied = QtCore.pyqtSignal()
    LineApplied = QtCore.pyqtSignal(Line)
    lineNameChanged = QtCore.pyqtSignal(Line,str,str)  # new,old 2019.10.08新增
    def __init__(self,line:Line,parent=None):
        super(LineWidget, self).__init__(parent)
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

        tableWidget = LineTable()

        tableWidget.setEditTriggers(tableWidget.CurrentChanged)
        self.tableWidget = tableWidget

        tableWidget.setColumnCount(8)
        tableWidget.setHorizontalHeaderLabels(["站名", "里程", "对里程", "等级", "显示", "单向站","办客","办货"])
        tableWidget.itemChanged.connect(self.changed)

        for i,s in enumerate((100,100,80,40,40,80,50,50)):
            tableWidget.setColumnWidth(i,s)

        tableWidget.setRowCount(line.stationCount())

        self._setLineTable()

        vlayout.addLayout(flayout)
        vlayout.addWidget(tableWidget)

        # btnAdd = QtWidgets.QPushButton("前插站")
        # btnAdd.setMinimumWidth(50)
        # btnAddL = QtWidgets.QPushButton("后插站")
        # btnAddL.setMinimumWidth(50)
        # btnDel = QtWidgets.QPushButton("删除站")
        # btnDel.setMinimumWidth(50)
        # btnAdd.clicked.connect(lambda: self._add_station(tableWidget))
        # btnAddL.clicked.connect(lambda: self._add_station(tableWidget, True))
        # btnDel.clicked.connect(lambda: self._del_station(tableWidget))
        #
        # hlayout = QtWidgets.QHBoxLayout()
        # hlayout.addWidget(btnAdd)
        # hlayout.addWidget(btnAddL)
        # hlayout.addWidget(btnDel)
        # vlayout.addLayout(hlayout)

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

        action = QtWidgets.QAction("复制[里程]到[对里程] (Alt+Z)",self.tableWidget)
        action.triggered.connect(self._copy_counter)
        action.setShortcut('alt+Z')
        self.tableWidget.addAction(action)
        self.tableWidget.setContextMenuPolicy(Qt.ActionsContextMenu)

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
        if not isinstance(dct,LineStation):
            dct=LineStation(dct)
        self.tableWidget.item(row,0).setText(dct["zhanming"])
        self.tableWidget.cellWidget(row, 1).setValue(dct["licheng"])
        self.tableWidget.item(row,2).setText(dct.counterStr())
        self.tableWidget.cellWidget(row, 3).setValue(dct["dengji"])
        self.tableWidget.item(row,4).setCheckState(Line.bool2CheckState(dct.get('show',True)))
        self.tableWidget.cellWidget(row, 5).setCurrentIndex(dct.get('direction', 0x3))
        self.tableWidget.item(row,6).setCheckState(Qt.Checked if dct.setdefault("passenger",True)
                                                   else Qt.Unchecked)
        self.tableWidget.item(row,7).setCheckState(Qt.Checked if dct.setdefault("freight", True)
                                                    else Qt.Unchecked)

    def _setLineTable(self,start_index=0):
        tableWidget = self.tableWidget
        line = self.line

        now_line = start_index
        for stationDict in line.stationDicts(start_index):
            if not isinstance(stationDict,LineStation):
                stationDict=LineStation(stationDict)

            item = QtWidgets.QTableWidgetItem(stationDict["zhanming"])
            tableWidget.setItem(now_line, 0, item)

            spin1 = CellWidgetFactory.new(QtWidgets.QDoubleSpinBox)
            spin1.setRange(-9999.000, 9999.000)
            spin1.setDecimals(3)
            spin1.setValue(stationDict["licheng"])
            tableWidget.setCellWidget(now_line, 1, spin1)
            spin1.setMinimumSize(10, 10)
            spin1.valueChanged.connect(self.changed)

            tableWidget.setItem(now_line,2,QtWidgets.QTableWidgetItem(stationDict.counterStr()))

            spin2 = CellWidgetFactory.new(QtWidgets.QSpinBox)
            spin2.setValue(stationDict["dengji"])
            spin2.setRange(0, 20)
            tableWidget.setCellWidget(now_line, 3, spin2)
            spin2.setMinimumSize(10, 10)
            spin2.valueChanged.connect(self.changed)

            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(Line.bool2CheckState(stationDict.setdefault("show",True)))
            tableWidget.setItem(now_line,4,item)

            combo:QtWidgets.QComboBox = CellWidgetFactory.new(QtWidgets.QComboBox)
            combo.setMinimumSize(1,1)
            combo.addItems(["不通过", "下行", "上行", "上下行"])
            try:
                stationDict["direction"]
            except KeyError:
                stationDict["direction"] = 0x3
            combo.setCurrentIndex(stationDict["direction"])
            combo.setStyleSheet("QComboBox{margin:3px}")
            tableWidget.setCellWidget(now_line, 5, combo)
            combo.currentTextChanged.connect(self.changed)

            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(Line.bool2CheckState(stationDict.setdefault("passenger",True)))
            tableWidget.setItem(now_line,6,item)

            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(Line.bool2CheckState(stationDict.setdefault("freight", True)))
            tableWidget.setItem(now_line, 7, item)

            tableWidget.setRowHeight(now_line, 30)  # cannot infer to graph
            now_line += 1

    # slots
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
            dengji = tableWidget.cellWidget(i, 3).value()
            show = bool(tableWidget.item(i,4).checkState())
            direction = tableWidget.cellWidget(i, 5).currentIndex()
            try:
                counter = float(tableWidget.item(i,2).text())
            except:
                counter = None

            if i == 0 and (licheng != 0.0 or (counter is not None and counter != 0.0)):
                if self.qustion("本线起始里程（或起始对里程）不为0，是否调整所有车站里程（或对里程）以使起始站里程（或对里程）归零？", False):
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
                "passenger":bool(tableWidget.item(i,6).checkState()),
                "freight":bool(tableWidget.item(i,7).checkState()),
                "counter":counter,
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

    def _copy_counter(self):
        """
        Alt+Z。
        2020.01.23新增，将当前行里程复制到对里程。
        """
        row = self.tableWidget.currentRow()
        if not 0<=row<self.tableWidget.rowCount():
            return
        tw = self.tableWidget
        tw.item(row,2).setText(f"{tw.cellWidget(row,1).value():.3f}")

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



"""
独立出来的标尺编辑窗口类。架空主程序中相关部分。
2018.12.14修改，将main设为可选，保证可以从数据库独立调用。
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .ruler import Ruler
from .line import Line

class RulerWidget(QtWidgets.QTabWidget):
    okClicked = QtCore.pyqtSignal()
    showStatus = QtCore.pyqtSignal(str)
    def __init__(self,line:Line,main=None):
        super().__init__()
        self.line = line
        self.main = main
        self.updating = False
        self.initUI()

    def initUI(self):
        """
        初始化数据。
        """
        self.updating=True
        self.clear()
        line = self.line
        for ruler in line.rulers:
            self._addRulerTab(ruler)
        new_ruler = Ruler(line=line)
        self._addRulerTab(new_ruler)
        self.updating=False

    def setData(self):
        """
        2019.07.19新增。
        标尺数量可能变化，更新内容。由刷新操作调用。
        """
        self.updating=True
        cnt = len(self.line.rulers)
        while self.count() > cnt+1:
            self.removeTab(self.count()-1)
        # 先更新既有的widget
        for i,ruler in enumerate(self.line.rulers):
            if i < self.count():
                widget = self.widget(i)
                widget.ruler=ruler
                self._updateRulerTabWidget(widget)
                self.setTabText(i,ruler.name())
            else:
                self._addRulerTab(ruler)
        if self.count() != len(self.line.rulers)+1:
            # 差最后一个“新建”，补上。
            self._addRulerTab(Ruler(line=self.line,name='新建'))
        else:
            widget = self.widget(self.count()-1)
            widget.ruler = Ruler(name='新建',line=self.line)
            self.setTabText(self.count()-1,'新建')
            self._updateRulerTabWidget(widget)
        self.updating=False

    def updateRulerTabs(self):
        """
        已知标尺不增减，只有内部变化，更新所有标尺的标签页。
        """
        for i in range(self.count()):
            widget = self.widget(i)
            self._updateRulerTabWidget(widget)

    def _addRulerTab(self,ruler):
        widget = QtWidgets.QWidget(self)
        widget.ruler = ruler

        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        nameEdit = QtWidgets.QLineEdit()
        nameEdit.setText(ruler.name())
        flayout.addRow("标尺名称", nameEdit)
        widget.nameEdit = nameEdit

        check = QtWidgets.QCheckBox()
        check.setChecked(ruler.different())
        flayout.addRow("上下行分设", check)
        check.toggled.connect(lambda x: self._ruler_different_changed(ruler, x, tableWidget))
        widget.check = check

        vlayout.addLayout(flayout)

        # 2018.12.14修改：抽离main，将触发的函数弄到外面去
        if self.main is not None:
            # 若当前编辑的是运行图的标尺而不是数据库中的
            btnRead = QtWidgets.QPushButton("从车次读取")
            btnRead.clicked.connect(lambda: self._ruler_from_train(widget))
            btnSet = QtWidgets.QPushButton("设为排图标尺")
            btnSet.clicked.connect(lambda: self._apply_ruler_change(widget))  # 先提交标尺信息
            btnSet.clicked.connect(lambda: self.main.changeOrdinateRuler(ruler))  # 直接触发修改函数
            btnMerge = QtWidgets.QPushButton("合并标尺")
            btnMerge.clicked.connect(lambda:self._merge_ruler(widget))
            hlayout = QtWidgets.QHBoxLayout()
            hlayout.addWidget(btnRead)
            hlayout.addWidget(btnMerge)
            hlayout.addWidget(btnSet)

            vlayout.addLayout(hlayout)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        widget.tableWidget = tableWidget

        self._setRulerTable(tableWidget, widget.ruler)

        vlayout.addWidget(tableWidget)

        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("还原")
        btnDel = QtWidgets.QPushButton("删除")

        btnOk.clicked.connect(lambda: self._apply_ruler_change(widget))
        btnCancel.clicked.connect(lambda: self._discard_ruler_change(widget))
        btnDel.clicked.connect(lambda: self._del_ruler(ruler))

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        hlayout.addWidget(btnDel)
        vlayout.addLayout(hlayout)

        widget.setLayout(vlayout)

        tabname = ruler.name()
        if not tabname:
            tabname = "新建"

        self.addTab(widget, tabname)

    def _setRulerTable(self, tableWidget: QtWidgets.QTableWidget, ruler: Ruler):
        """
        设置ruler的table。
        """
        tableWidget.setRowCount(self.line.stationCount()*2)  # 先给一个明显超过需要的值

        tableWidget.verticalHeader().setVisible(False)
        tableWidget.setColumnCount(7)
        tableWidget.setHorizontalHeaderLabels(["区间", "分", "秒", "起", "停","距离", "旅速"])
        tableWidget.setColumnWidth(0, 150)
        tableWidget.setColumnWidth(1, 40)
        tableWidget.setColumnWidth(2, 50)
        tableWidget.setColumnWidth(3, 50)
        tableWidget.setColumnWidth(4, 50)
        tableWidget.setColumnWidth(5, 70)
        tableWidget.setColumnWidth(6, 70)

        # 方便起见，直接调用line对象
        line = ruler.line()
        station_dicts = line.stations
        blocker = "->" if ruler.different() else "<->"

        row = 0  # 下一次要添加的行号
        former_dict = None
        for i, st_dict in enumerate(station_dicts):
            if not ruler.isDownPassed(st_dict["zhanming"]):
                if former_dict is not None:
                    mile = abs(st_dict["licheng"] - former_dict["licheng"])
                    self._addRulerRow(former_dict["zhanming"], st_dict["zhanming"], blocker
                                      , ruler.getInfo(former_dict["zhanming"], st_dict["zhanming"]),
                                      tableWidget, mile,row)
                    row+=1
                former_dict = st_dict
        print("初始化上行")
        former_dict = None
        if ruler.different():
            # 上下行不一致，增加上行部分
            for st_dict in reversed(station_dicts):
                if not ruler.isUpPassed(st_dict["zhanming"]):
                    if former_dict is not None:
                        mile = abs(st_dict["licheng"] - former_dict["licheng"])
                        self._addRulerRow(former_dict["zhanming"], st_dict["zhanming"], blocker
                                          , ruler.getInfo(former_dict["zhanming"], st_dict["zhanming"]),
                                          tableWidget, mile, row)
                        row += 1
                    former_dict = st_dict
        tableWidget.setRowCount(row)

    def _addRulerRow(self, fazhan, daozhan, blocker
                     , node: dict, tableWidget: QtWidgets.QTableWidget,
                     mile,now_line):
        print("RulerWidget::addRulerRow",fazhan,blocker,daozhan)
        tableWidget.setRowHeight(now_line, self.main.graph.UIConfigData()['table_row_height']
            if self.main is not None else 30)

        interval = fazhan + blocker + daozhan
        item = QtWidgets.QTableWidgetItem(interval)
        item.setData(-1, [fazhan, daozhan])
        tableWidget.setItem(now_line, 0, item)

        minute = 0
        second = 0
        if node is not None:
            minute = int(node["interval"] / 60)
            second = node["interval"] % 60

        spinMin = QtWidgets.QSpinBox()
        spinMin.setRange(0, 300)
        spinMin.setValue(minute)
        spinMin.setMinimumSize(1,1)

        spinSec = QtWidgets.QSpinBox()
        spinSec.setRange(0, 60)
        spinSec.setSingleStep(10)
        spinSec.setValue(second)
        spinSec.setMinimumSize(1,1)

        spinMin.valueChanged.connect(lambda: self._ruler_interval_changed(
            now_line, tableWidget, mile
        ))
        spinSec.valueChanged.connect(lambda: self._ruler_interval_changed(
            now_line, tableWidget, mile
        ))

        tableWidget.setCellWidget(now_line, 1, spinMin)
        tableWidget.setCellWidget(now_line, 2, spinSec)

        spinStart = QtWidgets.QSpinBox()
        spinStart.setRange(0, 300)
        spinStart.setSingleStep(10)
        spinStop = QtWidgets.QSpinBox()
        spinStop.setRange(0, 300)
        spinStop.setSingleStep(10)
        spinStart.setMinimumSize(1,1)
        spinStop.setMinimumSize(1,1)

        start = 0
        stop = 0

        if node is not None:
            start = node["start"]
            stop = node["stop"]

        spinStart.setValue(start)
        spinStop.setValue(stop)

        tableWidget.setCellWidget(now_line, 3, spinStart)
        tableWidget.setCellWidget(now_line, 4, spinStop)

        try:
            speed = 1000 * mile / (minute * 60 + second) * 3.6
        except ZeroDivisionError:
            speed = 0

        tableWidget.setItem(now_line,5,QtWidgets.QTableWidgetItem(f"{mile:.1f}"))

        item = QtWidgets.QTableWidgetItem("%.2f" % speed)
        tableWidget.setItem(now_line, 6, item)

    def _updateRulerTabWidget(self,widget):
        ruler:Ruler = widget.ruler
        widget.check.setChecked(ruler.different())
        widget.nameEdit.setText(ruler.name())
        self._updateRulerTable(widget.tableWidget,ruler)

    def _updateRulerTable(self,tableWidget:QtWidgets.QTableWidget,ruler:Ruler):
        """
        逐行更新数据。尽量减少变动。
        """
        blocker = "->" if ruler.different() else "<->"

        former_dict = None
        nrows_previous = tableWidget.rowCount()
        tableWidget.setRowCount(self.line.stationCount()*2)
        row_cnt = 0
        for i, st_dict in enumerate(self.line.stationDicts()):
            if not ruler.isDownPassed(st_dict["zhanming"]):
                if former_dict is not None:
                    if row_cnt >= nrows_previous:
                        # 原来没有的行，直接插入
                        mile = abs(st_dict["licheng"] - former_dict["licheng"])
                        self._addRulerRow(former_dict["zhanming"], st_dict["zhanming"], blocker
                                          , ruler.getInfo(former_dict["zhanming"], st_dict["zhanming"]),
                                          tableWidget, mile,row_cnt)
                        row_cnt+=1
                    else:
                        # 原来有的行，更新
                        mile = abs(st_dict["licheng"] - former_dict["licheng"])
                        self._updateTableRowData(tableWidget,row_cnt,
                                                 ruler.getInfo(former_dict["zhanming"], st_dict["zhanming"]),
                                                 mile,blocker,former_dict["zhanming"], st_dict["zhanming"]
                                                 )
                        row_cnt += 1
                former_dict = st_dict

        if not ruler.different():
            tableWidget.setRowCount(row_cnt)
            return
        former_dict = None
        for i, st_dict in enumerate(self.line.reversedStationDicts()):
            if not ruler.isUpPassed(st_dict["zhanming"]):
                if former_dict is not None:
                    if row_cnt >= nrows_previous:
                        # 原来没有的行，直接插入
                        mile = abs(st_dict["licheng"] - former_dict["licheng"])
                        self._addRulerRow(former_dict["zhanming"], st_dict["zhanming"], blocker
                                          , ruler.getInfo(former_dict["zhanming"], st_dict["zhanming"]),
                                          tableWidget, mile,row_cnt)
                        row_cnt+=1
                    else:
                        # 原来有的行，更新
                        mile = abs(st_dict["licheng"] - former_dict["licheng"])
                        self._updateTableRowData(tableWidget,row_cnt,
                                                 ruler.getInfo(former_dict["zhanming"], st_dict["zhanming"]),
                                                 mile,blocker,former_dict["zhanming"], st_dict["zhanming"]
                                                 )
                        row_cnt += 1
                former_dict = st_dict
        tableWidget.setRowCount(row_cnt)

    @staticmethod
    def _tableRowInterval(tableWidget:QtWidgets.QTableWidget,row:int):
        """
        返回某一行对应的区间。
        """
        try:
            return tableWidget.item(row,0).data(-1)
        except:
            return None

    @staticmethod
    def _updateTableRowData(tableWidget:QtWidgets.QTableWidget,row:int,info,mile,blocker,start,end):
        """
        已知这一行存在且各数据有效，使用info中的数据更新这一行的数据。
        """
        if info is None:
            info = {}
        item:QtWidgets.QTableWidgetItem = tableWidget.item(row,0)
        item.setText(f"{start}{blocker}{end}")
        item.setData(-1,[start,end])

        int_sec = info.get("interval",0)
        tableWidget.cellWidget(row,1).setValue(int(int_sec/60))
        tableWidget.cellWidget(row,2).setValue(int_sec%60)
        tableWidget.cellWidget(row,3).setValue(info.get("start",0))
        tableWidget.cellWidget(row,4).setValue(info.get("stop",0))
        tableWidget.item(row,5).setText(f"{mile:.1f}")


    #slots
    def _ruler_different_changed(self, ruler: Ruler, checked: bool, tableWidget):
        if self.updating:
            return
        if checked == False:
            if self.line.isSplited():
                self._derr("本线存在上下行分设站，不能设置上下行一致的标尺！")
                self.sender().setChecked(True)
                return

            flag = self.qustion("所有上行数据都将丢失，使用下行数据代表双向数据。是否继续？")
            if flag == False:
                self.sender().setChecked(True)
                return
            ruler.setDifferent(False, change=True)
        else:
            ruler.setDifferent(True, change=True)

        self._setRulerTable(tableWidget, ruler)

    def _apply_ruler_change(self, widget: QtWidgets.QWidget):
        name = widget.nameEdit.text()
        if not name:
            self._derr("标尺名称不能为空！")
            return
        ruler = widget.ruler
        line = ruler._line
        if line.rulerNameExisted(name, ruler):
            self._derr(f"标尺名称 {name} 已存在，请重新输入名称！")
            return

        ruler.setName(name)

        tableWidget: QtWidgets.QTableWidget = widget.tableWidget

        for row in range(tableWidget.rowCount()):
            fazhan = tableWidget.item(row, 0).data(-1)[0]
            daozhan = tableWidget.item(row, 0).data(-1)[1]
            interval = tableWidget.cellWidget(row, 1).value() * 60 + \
                       tableWidget.cellWidget(row, 2).value()
            if not interval:
                #这一行标红
                color = QtGui.QColor(Qt.red)
                color.setAlpha(150)
                for col in range(tableWidget.columnCount()):
                    try:
                        tableWidget.item(row,col).setBackground(QtGui.QBrush(color))
                    except:
                        pass
            else:
                for col in range(tableWidget.columnCount()):
                    try:
                        tableWidget.item(row,col).setBackground(QtGui.QBrush(Qt.transparent))
                    except:
                        pass

            start = tableWidget.cellWidget(row, 3).value()
            stop = tableWidget.cellWidget(row, 4).value()
            ruler.addStation_info(fazhan, daozhan, interval, start, stop, del_existed=True)

        self.setTabText(self.currentIndex(), ruler.name())

        if line.isNewRuler(ruler):
            line.addRuler(ruler)
            new_ruler = Ruler(line=line)
            self._addRulerTab(new_ruler)

        if self.main is not None:
            self.main.configWidget.setOrdinateCombo()

    def _discard_ruler_change(self, widget: QtWidgets.QWidget):
        flag = self.qustion("将此标尺数据恢复到保存的数据，所有未保存的修改都将丢失！是否继续？")
        if not flag:
            return

        ruler = widget.ruler
        widget.nameEdit.setText(ruler.name())
        #第一重parent是stackedWidget，第二重才是tabWidget
        self.updateRulerTabs()

    def _del_ruler(self, ruler: Ruler):
        new = False
        line:Line = ruler.line()
        if line.isNewRuler(ruler):
            new = True

        if not self.qustion("是否确认删除当前标尺？"):
            return

        if self.main is not None and ruler is self.main.graph.ordinateRuler():
            #若是排图标尺，取消排图标尺
            self.main.changeOrdinateRuler(None)

        self.removeTab(self.currentIndex())
        line.delRuler(ruler)

        if new:
            # 如果是新建标尺，则再新建一个tab
            new_ruler = Ruler(line=line)
            self._addRulerTab(new_ruler)

    def _merge_ruler(self,widget:QtWidgets.QWidget):
        """
        合并标尺。选择另一标尺，将其中所有内容复制过来。
        """
        ruler = widget.ruler
        cover = self.qustion('将本线另一标尺的数据合并到本标尺中，如何处理公共区间的数据？'
                             '选择是以覆盖，选择否以忽略。')
        dialog = QtWidgets.QDialog(self)
        dialog.cover = cover
        dialog.setWindowTitle('标尺合并')
        vlayout = QtWidgets.QVBoxLayout()
        listWidget = QtWidgets.QListWidget()
        dialog.listWidget = listWidget
        for r in self.line.rulers:
            if r is not ruler:
                listWidget.addItem(r.name())
        vlayout.addWidget(listWidget)

        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)

        btnOk.clicked.connect(lambda:self._merge_ruler_ok(widget,dialog))
        btnCancel.clicked.connect(dialog.close)
        listWidget.itemDoubleClicked.connect(lambda:self._merge_ruler_ok(widget,dialog))

        dialog.setLayout(vlayout)
        dialog.exec_()

    def _merge_ruler_ok(self,widget,dialog):
        ruler = widget.ruler
        cover:bool = dialog.cover
        listWidget:QtWidgets.QListWidget = dialog.listWidget
        item = listWidget.currentItem()
        if item is None:
            QtWidgets.QMessageBox.warning(self,'错误','请选择要合并的标尺名称！')
            return
        ruler.mergeRuler(self.line.rulerByName(item.text()),cover)
        self._setRulerTable(widget.tableWidget,ruler)
        dialog.close()

    # 允许直接使用main
    def _ruler_from_train(self, widget: QtWidgets.QWidget):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("从车次读取标尺")
        flayout = QtWidgets.QFormLayout()
        label = QtWidgets.QLabel("请选择要读入的车次，设置默认的起停附加时分。"
                                 "\n建议选择通过本线所有车站的车次。"
                                 "\n起停附加单位均为秒。")
        label.setWordWrap(True)
        flayout.addRow(label)

        label1 = QtWidgets.QLabel("选择车次")
        combo = QtWidgets.QComboBox()
        combo.setEditable(True)

        for train in self.main.graph.trains():
            combo.addItem(train.fullCheci())

        if self.main.GraphWidget.selectedTrain is not None:
            combo.setCurrentText(self.main.GraphWidget.selectedTrain.fullCheci())

        flayout.addRow(label1, combo)

        label2 = QtWidgets.QLabel("起步附加")
        spinStart = QtWidgets.QSpinBox()
        spinStart.setRange(0, 300)
        spinStart.setValue(120)
        spinStart.setSingleStep(10)
        flayout.addRow(label2, spinStart)

        label3 = QtWidgets.QLabel("停车附加")
        spinStop = QtWidgets.QSpinBox()
        spinStop.setRange(0, 300)
        spinStop.setValue(120)
        spinStop.setSingleStep(10)
        flayout.addRow(label3, spinStop)

        btnOk = QtWidgets.QPushButton("确定(&Y)")
        btnOk.clicked.connect(lambda: self._ruler_from_train_ok(dialog, widget))
        btnCancel = QtWidgets.QPushButton("取消(&C)")
        btnCancel.clicked.connect(dialog.close)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        dialog.combo = combo
        dialog.spinStart = spinStart
        dialog.spinStop = spinStop

        flayout.addRow(hlayout)

        dialog.setLayout(flayout)
        dialog.exec_()

    # 允许使用main
    def _ruler_from_train_ok(self, dialog, widget):
        train = self.main.graph.trainFromCheci(dialog.combo.currentText())
        if train is None:
            self.main._derr("错误：无此车次!")
            return

        flag = self.main.qustion("车次覆盖区间的数据将丢失。是否继续？")
        if not flag:
            return

        ruler: Ruler = widget.ruler

        ruler.rulerFromTrain(train, dialog.spinStop.value(), dialog.spinStart.value())
        tableWidget = widget.tableWidget
        self._setRulerTable(tableWidget, ruler)
        dialog.close()

    def _ruler_interval_changed(self, now_line: int, tableWidget: QtWidgets.QTableWidget,
                                mile: float):
        if self.updating:
            return
        # 重新计算均速
        spinMin = tableWidget.cellWidget(now_line, 1)
        spinSec = tableWidget.cellWidget(now_line, 2)

        seconds = spinMin.value() * 60 + spinSec.value()

        try:
            speed = 1000 * mile / (seconds) * 3.6
        except ZeroDivisionError:
            speed = 0.0
            color = QtGui.QColor(Qt.red)
            color.setAlpha(150)
            tableWidget.item(now_line, 0).setBackground(QtGui.QBrush(color))
        else:
            tableWidget.item(now_line, 0).setBackground(QtGui.QBrush(Qt.transparent))

        tableWidget.item(now_line, 6).setText("%.2f" % speed)

        if not seconds:
            # 这一行标红
            color = QtGui.QColor(Qt.red)
            color.setAlpha(150)
            for col in range(tableWidget.columnCount()):
                try:
                    tableWidget.item(now_line, col).setBackground(QtGui.QBrush(color))
                except:
                    pass
        else:
            for col in range(tableWidget.columnCount()):
                try:
                    tableWidget.item(now_line, col).setBackground(QtGui.QBrush(Qt.transparent))
                except:
                    pass

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def qustion(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '标尺编辑', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default
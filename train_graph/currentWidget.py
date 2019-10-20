"""
当前车次信息窗口类。2019.06.30修改：将与Main的连接全部改为signal
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .ruler import Ruler
from .line import Line
from .graph import Graph
from .circuit import Circuit
from .train import Train
from datetime import datetime,timedelta
from Timetable_new.checi3 import Checi
from Timetable_new.utility import judge_type,strToTime

class CurrentWidget(QtWidgets.QWidget):
    checkCurrentTrainRuler=QtCore.pyqtSignal(Train)
    showCurrentTrainEvents = QtCore.pyqtSignal()
    correctCurrentTrainTable = QtCore.pyqtSignal(Train)
    showStatus = QtCore.pyqtSignal(str)
    currentTrainApplied = QtCore.pyqtSignal(Train)
    currentTrainDeleted = QtCore.pyqtSignal(Train)
    editCurrentTrainCircuit = QtCore.pyqtSignal(Circuit)
    def __init__(self,graph):
        super().__init__()
        self.graph = graph  # type:Graph
        self.train = None
        self.updating=False
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()

        flayout = QtWidgets.QFormLayout()
        checiLabel = QtWidgets.QLabel("车次")
        checiEdit = QtWidgets.QLineEdit()
        checiEdit.editingFinished.connect(self._auto_updown_checi)
        flayout.addRow(checiLabel, checiEdit)
        self.checiEdit = checiEdit

        hlayout = QtWidgets.QHBoxLayout()
        checiDown = QtWidgets.QLineEdit()
        checiUp = QtWidgets.QLineEdit()
        hlayout.addWidget(checiDown)
        splitter = QtWidgets.QLabel("/")
        splitter.setAlignment(Qt.AlignCenter)
        splitter.setFixedWidth(20)
        hlayout.addWidget(splitter)
        hlayout.addWidget(checiUp)
        # layout.addLayout(hlayout)
        flayout.addRow("下行/上行", hlayout)
        self.checiDown = checiDown
        self.checiUp = checiUp

        sfzEdit = QtWidgets.QLineEdit()
        zdzEdit = QtWidgets.QLineEdit()
        splitter = QtWidgets.QLabel("->")
        splitter.setAlignment(Qt.AlignCenter)
        splitter.setFixedWidth(20)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(sfzEdit)
        hlayout.addWidget(splitter)
        hlayout.addWidget(zdzEdit)
        flayout.addRow("始发终到", hlayout)
        self.sfzEdit = sfzEdit
        self.zdzEdit = zdzEdit

        comboType = QtWidgets.QComboBox()
        comboType.setEditable(True)
        comboType.addItems(self.graph.typeList)
        self.comboType = comboType
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(comboType)
        checkPassenger = QtWidgets.QCheckBox('旅客列车')
        checkPassenger.setTristate(True)
        self.checkPassenger = checkPassenger
        hlayout.addWidget(checkPassenger)
        flayout.addRow('列车种类',hlayout)
        comboType.setToolTip('列车种类留空则由系统自动判定')
        comboType.setCurrentText("")

        btnItems = QtWidgets.QPushButton("设置")
        btnItems.setMaximumWidth(120)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnItems)
        checkAutoItem = QtWidgets.QCheckBox('自动设置')
        self.checkAutoItem = checkAutoItem
        hlayout.addWidget(checkAutoItem)
        btnItems.clicked.connect(self._items_dialog)
        flayout.addRow("运行线管理",hlayout)

        checkShow = QtWidgets.QCheckBox()
        checkShow.setChecked(True)
        checkShow.setText("显示")
        self.checkShow = checkShow
        flayout.addRow("显示运行线", checkShow)

        btnColor = QtWidgets.QPushButton("系统默认")
        btnColor.clicked.connect(self._set_train_color)
        btnColor.setFixedHeight(30)
        btnColor.setMinimumWidth(120)
        btnColor.setMaximumWidth(150)
        self.btnColor = btnColor

        btnDefault = QtWidgets.QPushButton("使用默认")
        btnDefault.setMaximumWidth(150)
        btnDefault.setMinimumWidth(100)
        btnDefault.clicked.connect(self._use_default_color)
        self.btnDefault = btnDefault
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnColor)
        hlayout.addWidget(btnDefault)
        flayout.addRow("运行线颜色", hlayout)
        self.color = ""

        spinWidth = QtWidgets.QDoubleSpinBox()
        spinWidth.setRange(0, 20)
        spinWidth.setSingleStep(0.5)
        spinWidth.setMaximumWidth(100)
        self.spinWidth = spinWidth
        flayout.addRow("运行线宽度", spinWidth)
        spinWidth.setToolTip("设置本次车运行线宽度。使用0代表使用系统默认。")

        hlayout = QtWidgets.QHBoxLayout()
        circuitEdit = QtWidgets.QLineEdit()
        self.circuitEdit = circuitEdit
        circuitEdit.setFocusPolicy(Qt.NoFocus)
        hlayout.addWidget(circuitEdit)

        btnEditCircuit = QtWidgets.QPushButton('编辑')
        self.btnEditCircuit = btnEditCircuit
        btnEditCircuit.setEnabled(False)
        hlayout.addWidget(btnEditCircuit)
        btnEditCircuit.clicked.connect(self._edit_circuit)
        flayout.addRow('车底交路',hlayout)

        layout.addLayout(flayout)

        timeTable = QtWidgets.QTableWidget()
        timeTable.setToolTip("按Alt+D将当前行到达时间复制为出发时间。")
        timeTable.setColumnCount(6)
        timeTable.setHorizontalHeaderLabels(["站名", "到点", "开点", '营业','备注', "停时"])
        timeTable.setColumnWidth(0, 80)
        timeTable.setColumnWidth(1, 100)
        timeTable.setColumnWidth(2, 100)
        timeTable.setColumnWidth(3, 50)
        timeTable.setColumnWidth(4, 100)
        timeTable.setColumnWidth(5, 80)
        timeTable.setEditTriggers(timeTable.CurrentChanged)
        timeTable.itemChanged.connect(self._table_item_changed)
        timeTable.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.timeTable = timeTable
        actionCpy = QtWidgets.QAction('复制到达时间为出发时间(Alt+D)',timeTable)
        actionCpy.setShortcut('Alt+D')
        actionCpy.triggered.connect(lambda: self._copy_time(timeTable))
        timeTable.addAction(actionCpy)

        layout.addWidget(timeTable)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton("添加(前)")
        btnAddL = QtWidgets.QPushButton("添加(后)")
        btnRm = QtWidgets.QPushButton("删除")
        btnLoad = QtWidgets.QPushButton("导入站表")

        btnAdd.clicked.connect(lambda: self._add_timetable_station(timeTable))
        btnAddL.clicked.connect(lambda: self._add_timetable_station(timeTable, True))
        btnRm.clicked.connect(lambda: self._remove_timetable_station(timeTable))
        btnLoad.clicked.connect(lambda: self._load_station_list(timeTable))

        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnAddL)
        hlayout.addWidget(btnRm)
        hlayout.addWidget(btnLoad)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnCheck = QtWidgets.QPushButton("标尺对照")
        btnCheck.clicked.connect(lambda:self.checkCurrentTrainRuler.emit(self.train))
        btnCheck.setMinimumWidth(120)

        btnEvent = QtWidgets.QPushButton("切片输出")
        btnEvent.setToolTip("显示本车次在本线的停站、发车、通过、会车、待避、越行等事件列表。")
        btnEvent.clicked.connect(self.showCurrentTrainEvents.emit)
        btnEvent.setMinimumWidth(120)

        btnCorrection = QtWidgets.QPushButton("顺序重排")
        btnAutoBusiness = QtWidgets.QPushButton('自动营业')
        btnAutoBusiness.clicked.connect(self._auto_business)
        btnCorrection.clicked.connect(lambda:self.correctCurrentTrainTable.emit(self.train))

        btnAutoStartEnd = QtWidgets.QPushButton("自动始发终到(&R)")
        btnAutoStartEnd.clicked.connect(self._auto_start_end)

        hlayout.addWidget(btnCheck)
        hlayout.addWidget(btnEvent)
        hlayout.addWidget(btnCorrection)
        hlayout.addWidget(btnAutoBusiness)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定(&O)")
        btnCancel = QtWidgets.QPushButton("还原")
        btnDel = QtWidgets.QPushButton("删除车次")
        btnOk.setMinimumWidth(100)
        btnCancel.setMinimumWidth(100)
        btnDel.setMinimumWidth(100)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        hlayout.addWidget(btnDel)
        hlayout.addWidget(btnAutoStartEnd)
        layout.addLayout(hlayout)

        btnOk.clicked.connect(self._current_ok)
        btnDel.clicked.connect(self._del_train_from_current)
        btnCancel.clicked.connect(self._restore_current_train)

        self.setLayout(layout)

    def _items_dialog(self):
        """
        显示对话框，用以设置运行图铺画参数。
        """
        if self.train is None:
            return
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('运行线管理')
        self.itemDialog = dialog
        hlayout = QtWidgets.QHBoxLayout()

        listWidget = QtWidgets.QListWidget()
        listWidget.setSelectionMode(listWidget.MultiSelection)
        listWidget.setMaximumWidth(200)
        self.stationList = listWidget
        hlayout.addWidget(listWidget)
        self._set_item_station_list(0)

        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("请在左侧列表中选择任意多个车站，系统将你选择的"
                                 "第一个作为起始站，最后一个作为终止站，自动添加到表格中。"
                                 "请注意你的这些设置只有在“自动设置”没有勾选时才有效。")
        label.setWordWrap(True)
        vlayout.addWidget(label)
        sublayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton("添加")
        btnDel = QtWidgets.QPushButton("删除")
        sublayout.addWidget(btnAdd)
        sublayout.addWidget(btnDel)

        vlayout.addLayout(sublayout)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(5)
        tableWidget.setHorizontalHeaderLabels(('起始站','结束站','下行','起始标签','结束标签'))
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        for i,s in enumerate((120,120,50,90,90)):
            tableWidget.setColumnWidth(i,s)
        self.itemTable = tableWidget

        maxi = 0
        for dct in self.train.itemInfo():
            end = dct["end"]
            end_index = self.train.stationIndexByName(end)
            maxi = max((end_index,maxi))
            self._add_item_table_row(dct['start'],end,end_index,dct['down'],
                                     dct['show_start_label'],dct['show_end_label'])
        self._set_item_station_list(maxi)

        btnAdd.clicked.connect(self._add_item_part)
        btnDel.clicked.connect(self._del_item_part)

        vlayout.addWidget(tableWidget)

        sublayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        sublayout.addWidget(btnOk)
        sublayout.addWidget(btnCancel)
        vlayout.addLayout(sublayout)
        hlayout.addLayout(vlayout)

        btnOk.clicked.connect(self._set_item_ok)
        btnCancel.clicked.connect(dialog.close)

        dialog.setLayout(hlayout)
        dialog.resize(900,700)
        dialog.exec_()

    def _set_item_station_list(self,start=0):
        listWidget = self.stationList
        listWidget.clear()
        for i,st in enumerate(self.train.stationDicts(start)):
            index = i + start
            item = QtWidgets.QListWidgetItem(st['zhanming'])
            item.setData(-1,index)
            listWidget.addItem(item)

    def _add_item_part(self):
        listWidget = self.stationList
        firstIndex,lastIndex = None,None
        firstStation = None
        curStation = None
        for item in listWidget.selectedItems():
            if firstIndex is None:
                firstIndex = item.data(-1)
                firstStation = item.text()
            lastIndex = item.data(-1)
            curStation = item.text()
        if firstStation is None:
            QtWidgets.QMessageBox.warning(self,'错误','请先再左侧选择要添加的站！')
            return
        self._add_item_table_row(firstStation,curStation,lastIndex,True,True,True)

        self._set_item_station_list(lastIndex)

    def _add_item_table_row(self,start,end,lastIndex,down,showstart,showend):
        tableWidget = self.itemTable
        row = tableWidget.rowCount()
        tableWidget.insertRow(row)

        item = QtWidgets.QTableWidgetItem(start)
        tableWidget.setItem(row, 0, item)

        item = QtWidgets.QTableWidgetItem(end)
        tableWidget.setItem(row, 1, item)
        item.setData(-1, lastIndex)

        checkDown = QtWidgets.QCheckBox()
        checkDown.setChecked(down)
        tableWidget.setCellWidget(row, 2, checkDown)

        checkStart = QtWidgets.QCheckBox()
        checkStart.setChecked(showstart)
        tableWidget.setCellWidget(row, 3, checkStart)

        checkEnd = QtWidgets.QCheckBox()
        checkEnd.setChecked(showend)
        tableWidget.setCellWidget(row, 4, checkEnd)

        tableWidget.setRowHeight(row, self.graph.UIConfigData().get("table_row_height", 30))

    def _del_item_part(self):
        tableWidget = self.itemTable
        tableWidget.removeRow(tableWidget.currentRow())
        maxi = 0
        for row in range(tableWidget.rowCount()):
            maxi = max((maxi,tableWidget.item(row,1).data(-1)))
        self._set_item_station_list(maxi)

    def _set_item_ok(self):
        train = self.train
        train.clearItemInfo()
        tableWidget = self.itemTable
        for row in range(tableWidget.rowCount()):
            dct = {
                "start":tableWidget.item(row,0).text(),
                "end":tableWidget.item(row,1).text(),
                "down":tableWidget.cellWidget(row,2).isChecked(),
                "show_start_label":tableWidget.cellWidget(row,3).isChecked(),
                "show_end_label":tableWidget.cellWidget(row,4).isChecked()
            }
            train.addItemInfoDict(dct)
        self.itemDialog.close()


    def setData(self,train:Train=None):
        """
        将current中的信息变为train的信息
        """
        # 2019.03.24取消此逻辑。此逻辑导致“还原”操作无效。
        # if train is self.train:
        #     # 此逻辑不确定
        #     return
        self.updating=True
        print("current::setData",train)
        self.train = train
        if train is None:
            # 2019.01.29修改：取消return，空列车信息按空白处置
            train = self.train = Train(self.graph)

        self.checiEdit.setText(train.fullCheci())
        self.checiDown.setText(train.downCheci())
        self.checiUp.setText(train.upCheci())

        self.sfzEdit.setText(train.sfz)
        self.zdzEdit.setText(train.zdz)

        self.comboType.setCurrentText(train.trainType())
        self.color = train.color()
        if not self.color:
            self.btnColor.setText("系统默认")
            self.btnDefault.setEnabled(False)
            self.btnColor.setStyleSheet('default')
        else:
            color = QtGui.QColor(self.color)
            st = f"color:rgb({color.red()},{color.green()},{color.blue()})"
            self.btnColor.setText(self.color)
            self.btnColor.setStyleSheet(st)
        self.spinWidth.setValue(train.lineWidth())

        self.checkShow.setChecked(train.isShow())
        self.checkAutoItem.setChecked(train.autoItem())
        self.checkPassenger.setCheckState(train.isPassenger())

        if self.train.carriageCircuit() is not None:
            self.circuitEdit.setText(self.train.carriageCircuit().name())
            self.btnEditCircuit.setEnabled(True)
        else:
            self.circuitEdit.setText('')
            self.btnEditCircuit.setEnabled(False)

        timeTable: QtWidgets.QTableWidget = self.timeTable
        timeTable.setRowCount(train.stationCount())

        num = 0
        for st_dict in train.timetable:
            station, ddsj, cfsj = st_dict['zhanming'],st_dict['ddsj'],st_dict['cfsj']
            ddsj: datetime

            timeTable.setRowHeight(num, self.graph.UIConfigData()['table_row_height'])
            itemStation = QtWidgets.QTableWidgetItem(station)
            itemStation.setData(Qt.UserRole,st_dict)
            timeTable.setItem(num, 0, itemStation)

            # 2019.07.13调整，设置时间会触发计算时间，此时要求第3、5列不能是None。
            time_str = train.stopTimeStr(st_dict)
            item: QtWidgets.QTableWidgetItem = QtWidgets.QTableWidgetItem(time_str)
            item.setFlags(Qt.ItemIsEnabled)
            timeTable.setItem(num, 5, item)

            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(Line.bool2CheckState(train.stationBusiness(st_dict)))
            timeTable.setItem(num, 3, item)

            ddsjEdit = timeTable.cellWidget(num,1)
            if ddsjEdit is None:
                ddsjEdit = QtWidgets.QTimeEdit()
                ddsjEdit.setWrapping(True)
                ddsjEdit.setDisplayFormat("hh:mm:ss")
                ddsjEdit.timeChanged.connect(self._time_changed)
                timeTable.setCellWidget(num, 1, ddsjEdit)
            ddsjEdit.row = num
            ddsjQ = QtCore.QTime(ddsj.hour, ddsj.minute, ddsj.second)
            # ddsjEdit.setMinimumSize(1,1)
            ddsjEdit.setTime(ddsjQ)

            cfsjEdit = timeTable.cellWidget(num,2)
            if cfsjEdit is None:
                cfsjEdit = QtWidgets.QTimeEdit()
                cfsjEdit.setDisplayFormat("hh:mm:ss")
                cfsjEdit.setWrapping(True)
                cfsjEdit.timeChanged.connect(self._time_changed)
                timeTable.setCellWidget(num, 2, cfsjEdit)
            cfsjEdit.row = num
            cfsjQ = QtCore.QTime(cfsj.hour, cfsj.minute, cfsj.second)
            cfsjEdit.setTime(cfsjQ)
            # cfsjEdit.setMinimumSize(1,1)

            note=st_dict.setdefault('note','')
            item=QtWidgets.QTableWidgetItem(note)
            timeTable.setItem(num,4,item)

            if train.stationBusiness(st_dict):
                itemStation.setForeground(QtGui.QBrush(Qt.red))
            elif train.stationStopped(st_dict):
                itemStation.setForeground(QtGui.QBrush(Qt.blue))

            num += 1
        self.updating=False

    # Slots
    def _time_changed(self):
        if self.updating:
            return
        row = self.sender().row
        ddsjEdit:QtWidgets.QTimeEdit = self.timeTable.cellWidget(row,1)
        cfsjEdit:QtWidgets.QTimeEdit = self.timeTable.cellWidget(row,2)
        ddsjQ: QtCore.QTime = ddsjEdit.time()
        ddsj = strToTime(ddsjQ.toString("hh:mm:ss"))
        cfsjQ = cfsjEdit.time()
        cfsj = strToTime(cfsjQ.toString("hh:mm:ss"))

        # 设置停靠时间数据
        dt: timedelta = cfsj - ddsj
        seconds = dt.seconds
        if seconds == 0:
            time_str = ""
        else:
            m = int(seconds / 60)
            s = seconds % 60
            time_str = "{}分".format(m)
            if s:
                time_str += str(s) + "秒"
        self.timeTable.item(row,5).setText(time_str)

        if self.timeTable.item(row,3).checkState() == Qt.Checked:
            self.timeTable.item(row,0).setForeground(QtGui.QBrush(Qt.red))
        elif time_str:
            self.timeTable.item(row,0).setForeground(QtGui.QBrush(Qt.blue))
        else:
            self.timeTable.item(row, 0).setForeground(QtGui.QBrush(Qt.black))


    def _auto_updown_checi(self):
        """
        自动设置上下行车次
        """
        try:
            checi = Checi(self.sender().text())
            self.checiDown.setText(checi.down)
            self.checiUp.setText(checi.up)
        except:
            self.checiDown.setText("")
            self.checiUp.setText("")

    def _set_train_color(self):
        color: QtGui.QColor = QtWidgets.QColorDialog.getColor()
        self.color = "#%02X%02X%02X" % (color.red(), color.green(), color.blue())
        btn: QtWidgets.QPushButton = self.btnColor
        btn.setStyleSheet(f"color:rgb({color.red()},{color.green()},{color.blue()})")
        btn.setText(self.color)
        self.btnDefault.setEnabled(True)

    def _use_default_color(self):
        self.color = ""
        btn: QtWidgets.QPushButton = self.btnColor
        btn.setText("系统默认")
        btn.setStyleSheet("default")
        self.btnDefault.setEnabled(False)

    def _table_item_changed(self,item:QtWidgets.QTableWidgetItem):
        if self.updating:
            return
        # print("currentWidget::table_item_changed",item.text(),item.row(),item.column())
        row = item.row()
        if item.column() == 3:
            # 营业列变化
            itemStation = self.timeTable.item(row,0)
            if item.checkState() == Qt.Checked:
                itemStation.setForeground(QtGui.QBrush(Qt.red))
            elif self.timeTable.cellWidget(row,1).time() != self.timeTable.cellWidget(row,2).time():
                itemStation.setForeground(QtGui.QBrush(Qt.blue))
            else:
                itemStation.setForeground(QtGui.QBrush(Qt.black))


    def _copy_time(self, timeTable: QtWidgets.QTableWidget):
        row = timeTable.currentRow()
        time = timeTable.cellWidget(row, 1).time()
        timeTable.cellWidget(row, 2).setTime(time)
        timeTable.item(row, 3).setText("")  # 停时变成0
        self.showStatus.emit(f"{timeTable.item(row,0).text()}站到达时间复制成功")

    def _add_timetable_station(self, timeTable: QtWidgets.QTableWidget, later=False):
        row = timeTable.currentIndex().row()
        if later:
            row += 1
        self._add_timetable_row(row, timeTable)

    def _add_timetable_row(self, row: int, timeTable: QtWidgets.QTableWidget, name: str = "",business=False):
        timeTable.insertRow(row)
        timeTable.setRowHeight(row, self.graph.UIConfigData()['table_row_height'])

        item = QtWidgets.QTableWidgetItem(name)
        timeTable.setItem(row, 0, item)

        ddsjEdit = QtWidgets.QTimeEdit()
        ddsjEdit.setDisplayFormat('hh:mm:ss')
        timeTable.setCellWidget(row, 1, ddsjEdit)
        ddsjEdit.row = row
        ddsjEdit.timeChanged.connect(self._time_changed)

        cfsjEdit = QtWidgets.QTimeEdit()
        cfsjEdit.setDisplayFormat('hh:mm:ss')
        timeTable.setCellWidget(row, 2, cfsjEdit)
        cfsjEdit.row = row
        cfsjEdit.timeChanged.connect(self._time_changed)

        item = QtWidgets.QTableWidgetItem()
        item.setFlags(Qt.ItemIsEnabled)
        timeTable.setItem(row, 5, item)

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Line.bool2CheckState(business))
        timeTable.setItem(row,3,item)

    def _remove_timetable_station(self, timeTable: QtWidgets.QTableWidget):
        timeTable.removeRow(timeTable.currentRow())

    def _load_station_list(self, timeTable):
        """
        导入本线车站表。按上下行
        """
        flag = self.question("删除本车次时刻表信息，从本线车站表导入，是否继续？")
        if not flag:
            return

        down = self.train.firstDown()

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("本线车站导入")
        layout = QtWidgets.QVBoxLayout()

        radioDown = QtWidgets.QRadioButton('下行')
        radioUp = QtWidgets.QRadioButton("上行")
        radioDown.setChecked(True)
        box = QtWidgets.QButtonGroup(self)
        box.addButton(radioDown)
        box.addButton(radioUp)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(radioDown)
        hlayout.addWidget(radioUp)
        layout.addLayout(hlayout)
        radioDown.toggled.connect(self._set_load_station_list)

        listWidget = QtWidgets.QListWidget()

        listWidget.setSelectionMode(listWidget.MultiSelection)
        self.loadList = listWidget

        self._set_load_station_list(down)

        layout.addWidget(listWidget)

        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        btnOk.clicked.connect(lambda: self._load_station_ok(listWidget, timeTable))
        btnCancel.clicked.connect(dialog.close)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        layout.addLayout(hlayout)

        dialog.setLayout(layout)

        dialog.exec_()

    def _set_load_station_list(self,down:bool):
        listWidget = self.loadList
        listWidget.clear()
        dir = Line.DownVia if down else Line.UpVia

        dir_dict = {
            0x0: '不通过',
            0x1: '下行',
            0x2: '上行',
            0x3: '上下行'
        }
        for st in self.graph.stationDicts(reverse=not down):
            try:
                st["direction"]
            except KeyError:
                st["direction"] = 0x3

            text = "%s\t%s" % (st["zhanming"], dir_dict[st["direction"]])
            item = QtWidgets.QListWidgetItem(text)
            item.setData(-1, st["zhanming"])
            listWidget.addItem(item)
            if dir & st["direction"]:
                item.setSelected(True)
            else:
                item.setSelected(False)

    def _load_station_ok(self, listWidget: QtWidgets.QListWidget, timeTable: QtWidgets.QTableWidget):
        timeTable.setRowCount(0)
        for item in listWidget.selectedItems():
            zm = item.data(-1)
            row = timeTable.rowCount()
            # business = self.graph.lineStationBusiness(zm,self.train.isPassenger(detect=True))
            self._add_timetable_row(row, timeTable, zm, False)
        sender: QtWidgets.QPushButton = self.sender()
        sender.parentWidget().close()

    def _current_ok(self):
        self.showStatus.emit("车次信息更新中……")

        if self.train is None:
            self.train = Train(self.graph)
        train: Train = self.train

        fullCheci = self.checiEdit.text()
        downCheci = self.checiDown.text()
        upCheci = self.checiUp.text()

        if self.graph.checiExisted(fullCheci, train):
            self._derr(f"车次{fullCheci}已存在，请重新输入！")
            return

        self.graph.changeTrainCheci(train,fullCheci,downCheci,upCheci)

        sfz = self.sfzEdit.text()
        zdz = self.zdzEdit.text()
        train.setStartEnd(sfz, zdz)

        trainType = self.comboType.currentText()

        if not trainType:
            try:
                trainType = judge_type(fullCheci)
            except:
                trainType = '未知'

        elif trainType not in self.graph.typeList:
            self.graph.typeList.append(trainType)
        train.setType(trainType)

        isShow = self.checkShow.isChecked()
        train.setIsShow(isShow)
        train.setAutoItem(self.checkAutoItem.isChecked())
        train.setIsPassenger(self.checkPassenger.checkState())

        train.setUI(color=self.color, width=self.spinWidth.value())

        timeTable: QtWidgets.QTableWidget = self.timeTable
        train.clearTimetable()

        domain = False
        for row in range(timeTable.rowCount()):
            name = timeTable.item(row, 0).text()
            if not domain and '::' in name:
                domain = True
            ddsjSpin: QtWidgets.QTimeEdit = timeTable.cellWidget(row, 1)
            ddsjQ: QtCore.QTime = ddsjSpin.time()
            ddsj = strToTime(ddsjQ.toString("hh:mm:ss"))

            cfsjSpin = timeTable.cellWidget(row, 2)
            cfsj = strToTime(cfsjSpin.time().toString("hh:mm:ss"))

            try:
                note = timeTable.item(row,4).text()
            except AttributeError:
                # item is None
                note = ''

            train.addStation(name, ddsj, cfsj,business=bool(timeTable.item(row,3).checkState()),note=note)

        # 2019.07.05将setData移动到main中完成。
        # self.setData(train)
        self.currentTrainApplied.emit(train)
        # 2019.06.30将所有与main有关的移到main._current_applied中。

    def _del_train_from_current(self):
        self.currentTrainDeleted.emit(self.train)
        self.setData(None)

    def _restore_current_train(self):
        self.setData(self.train)

    def _auto_business(self):
        self.train.autoBusiness()
        self.setData(self.train)

    def _auto_start_end(self):
        if not self.train.timetable:
            return
        self.train.sfz = self.train.timetable[0]['zhanming']
        self.train.zdz = self.train.timetable[-1]['zhanming']
        self.setData(self.train)

    def _edit_circuit(self):
        circuit = self.train.carriageCircuit()
        if circuit is None:
            return
        if self.main:
            self.editCurrentTrainCircuit.emit(circuit)

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '问题', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default


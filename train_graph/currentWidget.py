"""
当前车次信息窗口类
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .ruler import Ruler
from .line import Line
from .train import Train
from datetime import datetime,timedelta
from Timetable_new.checi3 import Checi
from Timetable_new.utility import judge_type

class CurrentWidget(QtWidgets.QWidget):
    def __init__(self,main):
        super().__init__()
        self.main = main
        self.graph = main.graph
        self.train = None
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
        flayout.addRow("上下行车次", hlayout)
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
        comboType.addItems(self.main.graph.typeList)
        self.comboType = comboType
        flayout.addRow("列车种类", comboType)
        comboType.setCurrentText("")

        checkDown = QtWidgets.QCheckBox()
        checkDown.setChecked(True)
        checkDown.setText("本线下行运行")
        self.checkDown = checkDown
        checkShow = QtWidgets.QCheckBox()
        checkShow.setChecked(True)
        checkShow.setText("显示运行线")
        self.checkShow = checkShow
        hlayout = QtWidgets.QVBoxLayout()  # 名称未修改，注意类型
        hlayout.addWidget(checkDown)
        hlayout.addWidget(checkShow)
        flayout.addRow("铺画", hlayout)

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

        layout.addLayout(flayout)

        timeTable = QtWidgets.QTableWidget()
        timeTable.setToolTip("按Alt+D将当前行到达时间复制为出发时间。")
        timeTable.setColumnCount(5)
        timeTable.setHorizontalHeaderLabels(["站名", "到点", "开点", '备注', "停时"])
        timeTable.setColumnWidth(0, 80)
        timeTable.setColumnWidth(1, 100)
        timeTable.setColumnWidth(2, 100)
        timeTable.setColumnWidth(3, 100)
        timeTable.setColumnWidth(4, 80)
        timeTable.setEditTriggers(timeTable.CurrentChanged)
        self.timeTable = timeTable
        actionCpy = QtWidgets.QAction(timeTable)
        actionCpy.setShortcut('Alt+D')
        actionCpy.triggered.connect(lambda: self._copy_time(timeTable))
        timeTable.addAction(actionCpy)
        # item:QtWidgets.QTableWidgetItem
        # item.setFlags(Qt.NoItemFlags)

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
        btnCheck.clicked.connect(lambda: self.main._check_ruler(self.train))

        btnEvent = QtWidgets.QPushButton("切片输出")
        btnEvent.setToolTip("显示本车次在本线的停站、发车、通过、会车、待避、越行等事件列表。")
        btnEvent.clicked.connect(self.main._train_event_out)
        btnCheck.setMinimumWidth(120)
        btnEvent.setMinimumWidth(120)
        hlayout.addWidget(btnCheck)
        hlayout.addWidget(btnEvent)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnOk.setShortcut('Ctrl+Shift+I')
        btnCancel = QtWidgets.QPushButton("还原")
        btnDel = QtWidgets.QPushButton("删除车次")
        btnOk.setMinimumWidth(100)
        btnCancel.setMinimumWidth(100)
        btnDel.setMinimumWidth(100)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        hlayout.addWidget(btnDel)
        layout.addLayout(hlayout)

        btnOk.clicked.connect(self._current_ok)
        btnDel.clicked.connect(self._del_train_from_current)
        btnCancel.clicked.connect(self._restore_current_train)

        self.setLayout(layout)

    def setData(self,train:Train=None):
        """
        将current中的信息变为train的信息
        """
        if train is self.train:
            # 此逻辑不确定
            return
        self.train = train
        if train is None:
            # 2019.01.29修改：取消return，空列车信息按空白处置
            train = self.train = Train()

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
        else:
            color = QtGui.QColor(self.color)
            self.btnColor.setStyleSheet(f"color:rgb({color.red()},{color.green()},{color.blue()})")
            self.btnColor.setStyleSheet(self.color)
        self.spinWidth.setValue(train.lineWidth())

        self.checkDown.setChecked(train.isDown(default=True))
        self.checkShow.setChecked(train.isShow())

        timeTable: QtWidgets.QTableWidget = self.timeTable
        timeTable.setRowCount(0)
        timeTable.setRowCount(train.stationCount())

        num = 0
        for st_dict in train.timetable:
            station, ddsj, cfsj = st_dict['zhanming'],st_dict['ddsj'],st_dict['cfsj']
            ddsj: datetime

            timeTable.setRowHeight(num, self.graph.UIConfigData()['table_row_height'])
            item = QtWidgets.QTableWidgetItem(station)
            timeTable.setItem(num, 0, item)

            ddsjEdit = QtWidgets.QTimeEdit()
            # ddsjQ = QtCore.QTime(ddsj.hour,ddsj.minute,ddsj.second)
            ddsjQ = QtCore.QTime(ddsj.hour, ddsj.minute, ddsj.second)
            ddsjEdit.setDisplayFormat("hh:mm:ss")
            ddsjEdit.setTime(ddsjQ)
            ddsjEdit.setMinimumSize(1,1)
            timeTable.setCellWidget(num, 1, ddsjEdit)

            cfsjEdit = QtWidgets.QTimeEdit()
            cfsjQ = QtCore.QTime(cfsj.hour, cfsj.minute, cfsj.second)
            cfsjEdit.setDisplayFormat("hh:mm:ss")
            cfsjEdit.setTime(cfsjQ)
            cfsjEdit.setMinimumSize(1,1)
            timeTable.setCellWidget(num, 2, cfsjEdit)

            note=st_dict.setdefault('note','')
            item=QtWidgets.QTableWidgetItem(note)
            timeTable.setItem(num,3,item)

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

            add = ''
            if train.isSfz(station):
                add = '始'
            elif train.isZdz(station):
                add = '终'

            if not time_str:
                time_str = add
            elif add != '':
                time_str += f', {add}'

            item: QtWidgets.QTableWidgetItem = QtWidgets.QTableWidgetItem(time_str)
            item.setFlags(Qt.NoItemFlags)
            timeTable.setItem(num, 4, item)

            num += 1


    #Slots
    def _auto_updown_checi(self):
        """
        自动设置上下行车次
        :return:
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
        btn.setStyleSheet(f"background-color:rgb({color.red()},{color.green()},{color.blue()})")
        btn.setText(self.color)
        self.btnDefault.setEnabled(True)

    def _use_default_color(self):
        self.color = ""
        btn: QtWidgets.QPushButton = self.btnColor
        btn.setText("系统默认")
        btn.setStyleSheet("default")
        self.btnDefault.setEnabled(False)

    def _copy_time(self, timeTable: QtWidgets.QTableWidget):
        row = timeTable.currentRow()
        time = timeTable.cellWidget(row, 1).time()
        timeTable.cellWidget(row, 2).setTime(time)
        timeTable.item(row, 3).setText("")  # 停时变成0
        self.main.statusOut(f"{timeTable.item(row,0).text()}站到达时间复制成功")

    def _add_timetable_station(self, timeTable: QtWidgets.QTableWidget, later=False):
        row = timeTable.currentIndex().row()
        if later:
            row += 1
        self._add_timetable_row(row, timeTable)

    def _add_timetable_row(self, row: int, timeTable: QtWidgets.QTableWidget, name: str = ""):
        timeTable.insertRow(row)
        timeTable.setRowHeight(row, self.graph.UIConfigData()['table_row_height'])

        item = QtWidgets.QTableWidgetItem(name)
        timeTable.setItem(row, 0, item)

        ddsjEdit = QtWidgets.QTimeEdit()
        ddsjEdit.setDisplayFormat('hh:mm:ss')
        timeTable.setCellWidget(row, 1, ddsjEdit)

        cfsjEdit = QtWidgets.QTimeEdit()
        cfsjEdit.setDisplayFormat('hh:mm:ss')
        timeTable.setCellWidget(row, 2, cfsjEdit)

        item = QtWidgets.QTableWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        timeTable.setItem(row, 3, item)

    def _remove_timetable_station(self, timeTable: QtWidgets.QTableWidget):
        timeTable.removeRow(timeTable.currentRow())

    def _load_station_list(self, timeTable):
        """
        导入本线车站表。按上下行
        """
        flag = self.main.qustion("删除本车次时刻表信息，从本线车站表导入，是否继续？")
        if not flag:
            return

        down = self.checkDown.isChecked()

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("本线车站导入")
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel(f"本车次当前方向为【{'下行'if down else '上行'}】，已自动选中本方向车站")
        label.setWordWrap(True)
        layout.addWidget(label)

        listWidget = QtWidgets.QListWidget()

        dir = Line.DownVia if down else Line.UpVia

        dir_dict = {
            0x0: '不通过',
            0x1: '下行',
            0x2: '上行',
            0x3: '上下行'
        }

        listWidget.setSelectionMode(listWidget.MultiSelection)

        for st in self.main.graph.stationDicts(reverse=not down):
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

    def _load_station_ok(self, listWidget: QtWidgets.QListWidget, timeTable: QtWidgets.QTableWidget):
        timeTable.setRowCount(0)
        for item in listWidget.selectedItems():
            zm = item.data(-1)
            row = timeTable.rowCount()
            self._add_timetable_row(row, timeTable, zm)
        sender: QtWidgets.QPushButton = self.sender()
        sender.parentWidget().close()

    def _current_ok(self):
        self.main.statusOut("车次信息更新中……")

        if self.train is None:
            self.train = Train()
        train: Train = self.train

        fullCheci = self.checiEdit.text()
        downCheci = self.checiDown.text()
        upCheci = self.checiUp.text()

        if self.main.graph.checiExisted(fullCheci, train):
            self.main._derr(f"车次{fullCheci}已存在，请重新输入！")
            return

        train.setCheci(fullCheci, downCheci, upCheci)

        sfz = self.sfzEdit.text()
        zdz = self.zdzEdit.text()
        train.setStartEnd(sfz, zdz)

        trainType = self.comboType.currentText()

        if not trainType:
            try:
                trainType = judge_type(fullCheci)
            except:
                trainType = '未知'

        elif trainType not in self.main.graph.typeList:
            self.main.graph.typeList.append(trainType)
            self.main._initTypeWidget()
        train.setType(trainType)

        isDown = self.checkDown.isChecked()
        isShow = self.checkShow.isChecked()
        train.setIsDown(isDown)
        train.setIsShow(isShow)
        print("line 442 current widget set is show ok")

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
            ddsj = datetime.strptime(ddsjQ.toString("hh:mm:ss"), "%H:%M:%S")

            cfsjSpin = timeTable.cellWidget(row, 2)
            cfsj = datetime.strptime(cfsjSpin.time().toString("hh:mm:ss"), "%H:%M:%S")

            train.addStation(name, ddsj, cfsj)

        self.setData(train)

        # repaint line
        self.main.GraphWidget.delTrainLine(train)
        self.main.GraphWidget.addTrainLine(train)

        if not self.graph.trainExisted(train):
            self.graph.addTrain(train)
            self.main.trainWidget.addTrain(train)

        else:
            self.main.trainWidget.updateRowByTrain(train)

        if domain:
            self.main._out_domain_info()

        self.main.statusOut("车次信息更新完毕")

    def _del_train_from_current(self):
        tableWidget = self.main.trainTable
        train: Train = self.train
        isOld = self.graph.trainExisted(train)

        self.main.GraphWidget._line_un_selected()

        if isOld:
            # 旧车次，清除表格中的信息
            for row in range(tableWidget.rowCount()):
                if tableWidget.item(row, 0).data(-1) is train:
                    tableWidget.removeRow(row)
                    break

        self.graph.delTrain(train)
        self.main.GraphWidget.delTrainLine(train)
        self.setData()

    def _restore_current_train(self):
        self.setData(self.train)

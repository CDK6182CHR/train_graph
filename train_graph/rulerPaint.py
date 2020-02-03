"""
按标尺排图向导对象封装。
注意：排图进行过程中，重新执行painGraph操作是高危动作，发现崩溃首先查找这里。
2018.11.24重构为QWidget+QStackedWidget实现。
2019.07.04新增注意事项：ChangeTrainIntervalDialog中有对本类listWidget，timeTable等的直接操作，破坏封装性。
"""

from .GraphicWidget import GraphicsWidget
from .data.graph import Graph,Train,Ruler
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from datetime import datetime,timedelta
from .utility import PECelledTable,PECellWidget,CellWidgetFactory

import cgitb
cgitb.enable(format='text')

class rulerPainter(QtWidgets.QWidget):
    trainOK = QtCore.pyqtSignal(Train)
    def __init__(self,graphWindow:GraphicsWidget,parent=None,setCheci=True):
        super(rulerPainter,self).__init__(parent)
        self.setCheci = setCheci  # 如果为False，则任何情况下都不显示设置车次的窗口。
        self.graphWindow = graphWindow
        self.ruler = None
        self.graph = graphWindow.graph
        self.train_new = Train(self.graph,"0001/2","0001","0002")
        self.train_new.autoTrainType()
        self.widget1=QtWidgets.QWidget()
        self.widget2=QtWidgets.QWidget()
        self.stackedWidget = QtWidgets.QStackedWidget(self)

        self.train = self.train_new
        self.combo = None
        self.down = True
        self.start_station = None
        self.interrupted = False
        self.start_from_this = False
        self.end_at_this = False
        self.first_station = None
        self.start_time = datetime(1900,1,1,0,0,0)
        self.isAppend = False
        self.toEnd = True
        # self.train.setIsDown(True)
        self.maxRow = 0
        self._initUI()

    def _initUI(self):
        self._step_1()
        self._step_2()

        self.stackedWidget.addWidget(self.widget1)
        self.stackedWidget.addWidget(self.widget2)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.stackedWidget)
        hlayout = QtWidgets.QHBoxLayout()
        btnCancel = QtWidgets.QPushButton('取消')
        btnFormer = QtWidgets.QPushButton('上一步')
        btnNext = QtWidgets.QPushButton('下一步')
        btnOk = QtWidgets.QPushButton('确定')
        self.btnOk = btnOk
        self.btnNext = btnNext
        self.btnFormer = btnFormer

        btnNext.clicked.connect(self._next_clicked)
        btnCancel.clicked.connect(self._cancel)
        btnFormer.clicked.connect(self._former_clicked)
        btnOk.clicked.connect(self._ok_clicked)

        hlayout.addWidget(btnCancel)
        hlayout.addWidget(btnFormer)
        hlayout.addWidget(btnNext)
        hlayout.addWidget(btnOk)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.widget1.resize(900,900)
        self.widget2.resize(900,900)
        self.resize(900,900)
        self.btnFormer.setEnabled(False)
        self.btnOk.setEnabled(False)

    def paint(self):
        self._step_1()
        if self.interrupted:
            return None
        else:
            return self.train

    def _step_1(self):
        widget = self.widget1
        widget.setWindowIcon(QtGui.QIcon('icon.ico'))
        widget.setWindowTitle("标尺排图向导")
        layout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        combo = QtWidgets.QComboBox()
        for ruler in self.graph.rulers():
            if self.ruler is None:
                self.ruler = ruler
            combo.addItem(ruler.name())
        flayout.addRow("排图标尺",combo)
        self.combo = combo
        combo.currentTextChanged.connect(self._ruler_changed)

        comboAppend = QtWidgets.QComboBox()
        comboAppend.setEditable(True)
        self.comboAppend = combo
        for train in self.graph.trains():
            comboAppend.addItem(train.fullCheci())

        comboAppend.setCurrentText('')
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(comboAppend)
        label = QtWidgets.QLabel("车次无效")
        label.setMaximumWidth(80)
        hlayout.addWidget(label)
        self.appendValidLabel = label
        comboAppend.setToolTip('将当前排图信息追加到车次，覆盖该车次已存在的站点时刻表。请注意，只能向后追加，不能倒推。'
                               '留空或车次非法表示铺画新车次运行图。')
        flayout.addRow("附加到车次(选填)",hlayout)

        group = QtWidgets.QButtonGroup(self)
        radioBegin = QtWidgets.QRadioButton("添加到开头")
        radioEnd = QtWidgets.QRadioButton("追加到末尾")
        group.addButton(radioBegin)
        group.addButton(radioEnd)
        self.radioBegin = radioBegin
        self.radioEnd = radioEnd
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(radioBegin)
        hlayout.addWidget(radioEnd)
        flayout.addRow("附加位置",hlayout)
        radioEnd.setChecked(True)
        self.radioBegin.setEnabled(False)
        self.radioEnd.setEnabled(False)
        radioEnd.toggled.connect(lambda x:self.setToEnd(x))

        hlayout = QtWidgets.QHBoxLayout()
        group = QtWidgets.QButtonGroup(self)
        self.radio1 = QtWidgets.QRadioButton("下行")
        self.radio2 = QtWidgets.QRadioButton("上行")
        group.addButton(self.radio1)
        group.addButton(self.radio2)
        self.radio1.setChecked(True)
        self.radio1.toggled.connect(self._radio_toggled)
        hlayout.addWidget(self.radio1)
        hlayout.addWidget(self.radio2)
        flayout.addRow("本线运行方向",hlayout)

        comboAppend.currentTextChanged.connect(self._append_changed)

        layout.addLayout(flayout)
        layout.addWidget(QtWidgets.QLabel("请选择起始站"))

        listWidget = QtWidgets.QListWidget()
        self.listWidget = listWidget
        layout.addWidget(listWidget)
        listWidget.currentItemChanged.connect(self._start_changed)

        widget.setLayout(layout)
        self._setRulerInfo()

    def setToEnd(self,x:bool):
        self.toEnd = x

    def _append_changed(self,checi:str):
        """
        “追加到车次”选项变更。
        2.0版本修改：不再限制追加排图时只能使用相同行别。
        """
        if not checi:
            self.train = self.train_new
            self.appendValidLabel.setText('车次无效')
        else:
            train:Train = self.graph.trainFromCheci(checi,full_only=True)
            if train:
                # 复制车次
                self.train = train.translation(checi,timedelta(days=0,seconds=0))
                self.appendValidLabel.setText('车次有效')
            else:
                self.train = self.train_new
                self.appendValidLabel.setText('车次无效')

        if self.train is self.train_new:
            self.radio1.setEnabled(True)
            self.radio2.setEnabled(True)
            self.radioBegin.setEnabled(False)
            self.radioEnd.setEnabled(False)
            self.isAppend = False
        else:
            self.radioBegin.setEnabled(True)
            self.radioEnd.setEnabled(True)
            self.train_origin = train
            self.isAppend = True

    def _next_clicked(self):
        self._reset_widget2_info()
        # self.stackedWidget.removeWidget(self.widget2)
        # self.stackedWidget.addWidget(self.widget2)
        self.stackedWidget.setCurrentIndex(1)
        self.btnOk.setEnabled(True)
        self.btnNext.setEnabled(False)
        self.btnFormer.setEnabled(True)

    def _step_2(self):
        widget = self.widget2

        layout = QtWidgets.QVBoxLayout()
        text = f"现在使用*{self.ruler.name()}*标尺从*{self.start_station}*起始，" \
               f"按*{'下行'if self.down else '上行'}*方向排图。双击排图到指定行，按Alt+X进行冲突检查。"
        label = QtWidgets.QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.step2Label = label

        flayout = QtWidgets.QFormLayout()

        timeEdit = QtWidgets.QTimeEdit()
        timeEdit.setDisplayFormat('hh:mm:ss')
        timeEdit.setWrapping(True)
        timeEdit.setLineEdit(QtWidgets.QLineEdit())
        timeEdit.timeChanged.connect(self._start_time_changed)
        timeEdit.setMaximumWidth(200)
        self.startTimeEdit = timeEdit
        flayout.addRow("起始时刻",timeEdit)

        checkStartThis = QtWidgets.QCheckBox()
        flayout.addRow("自本线始发",checkStartThis)
        self.checkStartThis = checkStartThis
        checkStartThis.toggled.connect(self._start_from_this_changed)

        checkEndThis = QtWidgets.QCheckBox()
        flayout.addRow("在本线终到",checkEndThis)
        self.checkEndThis = checkEndThis
        self.checkEndThis.toggled.connect(self._end_at_this_changed)
        layout.addLayout(flayout)

        checkCurrentChanged = QtWidgets.QCheckBox()
        flayout.addRow('即时模式',checkCurrentChanged)
        checkCurrentChanged.setChecked(True)
        self.checkCurrentChanged = checkCurrentChanged

        timeTable = PECelledTable()
        timeTable.setEditTriggers(timeTable.NoEditTriggers)
        timeTable.setColumnCount(8)
        timeTable.setToolTip("按Alt+X检测所在行时刻冲突情况")
        actionText = QtWidgets.QAction('冲突检查(Alt+X)',timeTable)
        actionText.setShortcut('Alt+X')
        actionText.triggered.connect(self._test_collid)
        timeTable.addAction(actionText)
        timeTable.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.timeTable = timeTable
        column_width = {
            0:80,
            1:50,
            2:50,
            3:90,
            4:90,
            5:60,
            6:60,
            7:60,
        }
        for key,value in column_width.items():
            timeTable.setColumnWidth(key,value)
        timeTable.setHorizontalHeaderLabels(['站名','停分','秒','到点','开点','附加','调整','区间'])
        self._setTable()
        timeTable.cellDoubleClicked.connect(self._paint_to_here)

        layout.addWidget(timeTable)

        widget.setLayout(layout)

    def _reset_widget2_info(self):
        label = self.step2Label
        text = f"现在使用*{self.ruler.name()}*标尺从*{self.start_station}*起始，" \
               f"按*{'下行'if self.down else '上行'}*方向排图。双击排图到指定行，按Alt+X进行冲突检查。"
        label.setText(text)
        self._setTable()


    def _setTable(self):
        former = None
        former_time = self.start_time
        started = False
        for station in self.ruler.coveredStations(self.down):
            if station == self.start_station:
                started=True
            if not started:
                continue

            if former is None:
                self._addTableRow(station, self.start_time, None)
                former = station
                continue

            node = self.ruler.getInfo(former, station)
            if node is None:
                break
            ds = node["interval"]
            if node["fazhan"] == self.start_station or node["daozhan"] == self.start_station:
                ds += node["start"]
            dt = timedelta(days=0, seconds=ds)
            self._addTableRow(station, former_time + dt, node)
            former = station
            former_time = former_time + dt

    def _addTableRow(self,name,ddsj,node):
        num = self.timeTable.rowCount()
        timeTable = self.timeTable
        timeTable.insertRow(num)
        timeTable.setRowHeight(num,self.graph.UIConfigData()['table_row_height'])

        item = QtWidgets.QTableWidgetItem(name)
        timeTable.setItem(num,0,item)

        spinMin = CellWidgetFactory.new(QtWidgets.QSpinBox)  # type:QtWidgets.QSpinBox
        spinMin.setRange(0,99999)
        spinMin.setMinimumSize(1,1)
        timeTable.setCellWidget(num,1,spinMin)
        spinMin.valueChanged.connect(lambda :self._stop_changed(num))

        spinSec = CellWidgetFactory.new(QtWidgets.QSpinBox)  # type:QtWidgets.QSpinBox
        timeTable.setCellWidget(num,2,spinSec)
        spinSec.setRange(0,59)
        spinSec.setSingleStep(10)
        spinSec.setWrapping(True)
        spinSec.valueChanged.connect(lambda :self._stop_changed(num))
        spinSec.setMinimumSize(1,1)

        ddsj_str = ddsj.strftime('%H:%M:%S')
        item = QtWidgets.QTableWidgetItem(ddsj_str)
        item.setData(-1,ddsj)
        timeTable.setItem(num,3,item)

        cfsj_str = ddsj_str
        item = QtWidgets.QTableWidgetItem(cfsj_str)
        timeTable.setItem(num,4,item)

        item = QtWidgets.QTableWidgetItem()
        if node is None:
            text = '--'
            item.setData(-1,-1)
        elif self.start_from_this and\
                (node["fazhan"] == self.start_station or node["daozhan"] == self.start_station):
            text='起通'
            item.setData(-1,0x1)
            flag = 0x1
        else:
            text='通通'
            item.setData(-1,0x0)
            flag = 0x0
        item.setText(text)
        timeTable.setItem(num,5,item)

        spinAdjust = CellWidgetFactory.new(QtWidgets.QSpinBox)  # type:QtWidgets.QSpinBox
        spinAdjust.setSingleStep(10)
        spinAdjust.setRange(-1000,1000)
        spinAdjust.setValue(0)
        spinAdjust.row = num
        spinAdjust.valueChanged.connect(lambda:self._adjust_changed(num))

        if node is None:
            ds = 0
            spinAdjust.setEnabled(False)
            ds_str = '--'
        else:
            ds = node["interval"]
            if 0x1&flag:
                ds += node["start"]
            ds_str = "%d:%02d"%(int(ds/60),ds%60)
        timeTable.setCellWidget(num,6,spinAdjust)

        item = QtWidgets.QTableWidgetItem(ds_str)
        item.setData(-1,node)
        timeTable.setItem(num,7,item)

    def _ruler_changed(self,name:str):
        self.ruler = self.graph.line.rulerByName(name)
        self._setRulerInfo()

    def _setRulerInfo(self):
        """
        设置listWidget的数据
        """
        self.listWidget.clear()
        ruler:Ruler = self.ruler
        stations = ruler.coveredStations(self.down)[:]

        for station in stations:
            if self.first_station is None:
                self.first_station = station
            item = QtWidgets.QListWidgetItem(station)
            self.listWidget.addItem(item)

    def _radio_toggled(self,isChecked:bool):
        radio = self.widget1.sender()
        print(radio.text(),isChecked)
        # self.train.setIsDown(isChecked)
        self.down = isChecked
        self._setRulerInfo()

    # slots
    def _cancel(self):
        """
        中途点击取消触发。
        """
        self.interrupted = True

        self.graphWindow.delTrainLine(self.train)

        try:
            self.parentWidget().close()
        except:
            pass

    def _start_changed(self,item1):
        """
        变换起始站。item1是现在选择的
        """
        try:
            item1.text()
        except:
            self.start_station=self.first_station
        else:
            self.start_station=item1.text()
            print("start changed!",item1.text())

    def _start_time_changed(self,time:QtCore.QTime):
        self.start_time = datetime.strptime(time.toString('hh:mm:ss'),'%H:%M:%S')
        self._reCalculate(0)

    def _start_from_this_changed(self,checked:bool):
        self.start_from_this = checked
        self._reCalculate(0)
        if checked:
            self.train.setStartEnd(sfz=self.start_station)

    def _end_at_this_changed(self,checked:bool):
        self.end_at_this = checked

    def _stop_changed(self,row:int):
        """
        车站停时改变触发。
        """
        self._reCalculate(row)
        if self.checkCurrentChanged.isChecked():
            self._paint_to_here(max((row,self.maxRow)))

    def _adjust_changed(self,row:int):
        self._reCalculate(row)
        if self.checkCurrentChanged.isChecked():
            self._paint_to_here(max((row,self.maxRow)))

    def _paint_to_here(self,row:int):
        """
        铺画运行线至本行.
        2.0版本新增逻辑：当现在铺画的运行线的行别与原车次行别在【铺画开始站】左邻域内相同时，
        选择覆盖，否则不覆盖。如果原车次在该点邻域上下行数据为None，则按覆盖处理。
        """
        self.maxRow = row
        if row<1 or row > self.timeTable.rowCount()-1:
            return

        if self.isAppend:
            self.train.coverData(self.train_origin)
            down_origin = self.train_origin.stationDown(self.start_station,self.graph)
            if down_origin == self.down or down_origin is None:
                cover = True
            else:cover = False
        else:
            self.train.clearTimetable()
            cover = False

        self._reCalculate(0)
        if self.start_from_this:
            self.train.setStartEnd(sfz=self.timeTable.item(0, 0).text())

        if self.end_at_this:
            self.train.setStartEnd(zdz=self.timeTable.item(row,0).text())
            self._setEndStation(row)

        if not self.isAppend or (self.isAppend and self.toEnd):
            for i in range(row+1):
                this_cover = cover or (i==0)# 第一行是无条件覆盖的
                name = self.timeTable.item(i,0).text()
                ddsj = datetime.strptime(self.timeTable.item(i,3).text(),'%H:%M:%S')
                cfsj = datetime.strptime(self.timeTable.item(i,4).text(),'%H:%M:%S')
                self.train.addStation(name,ddsj,cfsj,auto_cover=this_cover,to_end=True)

        else:
            for i in reversed(range(row + 1)):
                this_cover = cover or (i==0)
                name = self.timeTable.item(i, 0).text()
                ddsj = datetime.strptime(self.timeTable.item(i, 3).text(), '%H:%M:%S')
                cfsj = datetime.strptime(self.timeTable.item(i, 4).text(), '%H:%M:%S')
                self.train.addStation(name, ddsj, cfsj, auto_cover=this_cover, to_end=False)

        self.graphWindow.delTrainLine(self.train)
        # new = True
        # if self.train.items():
        #     # self.graphWindow.delTrainLine(self.train)
        #     new = False

        self.graphWindow.addTrainLine(self.train)
        # if new:
        #     self.graphWindow.ensureVisible(self.train.getItem())

    def _setEndStation(self,row:int):
        """
        设置row行为终到站。
        """
        if row == 0:
            return
        elif '终' in self.timeTable.item(row,5).text():
            return

        append_flag = self.timeTable.item(row,5).data(-1)
        append_text = self.timeTable.item(row, 5).text()[:1] + '终'
        self.timeTable.item(row,5).setText(append_text)
        if 0x2&append_flag:
            #本来就有停点，不需要另加。
            return
        append_flag += 0x2
        last_time = self._leaveTime(row-1)
        interval = self._cal_interval(self.timeTable.item(row,7).data(-1),append_flag)
        ddsj = last_time+timedelta(days=0,seconds=interval)
        self.timeTable.item(row,3).setData(-1,ddsj)
        self.timeTable.item(row,3).setText(ddsj.strftime('%H:%M:%S'))
        self.timeTable.item(row,4).setText(ddsj.strftime('%H:%M:%S')) #到这里的一定是没有停时的
        self.timeTable.item(row,7).setText("%d:%02d"%(int(interval/60),interval%60))

    def _resetEndStation(self,row:int):
        """
        取消终点站设置
        """
        if '终' not in self.timeTable.item(row,5).text():
            return
        elif row == 0:
            return

        if self._stayTime(row)!=0:
            self.timeTable.item(row,5).setText(self.timeTable.item(row,5).text()[:1]+'停')
            return

        self._reCalculate(row-1)

    def _reCalculate(self,from_row:int=0):
        """
        从from_row开始重新计算以下所有的时刻信息。信息都已经更新完毕。
        """
        timeTable = self.timeTable

        if from_row == 0:
            last_time = self.start_time
        else:
            last_time = self._leaveTime(from_row-1)

        for row in range(from_row,timeTable.rowCount()):
            current_stay = self._stayTime(row)
            if row == 0:
                ddsj = last_time
                cfsj = last_time+current_stay
                append_flag = -1
                append_flag_str = '--'
                interval = 0
                interval_str = '--'
            else:
                #区间行为判断
                adjust_value = timeTable.cellWidget(row,6).value()
                last_stay = self._stayTime(row-1)
                append_flag = 0x0
                append_flag_str = ""
                node:dict = timeTable.item(row,7).data(-1)
                interval = node["interval"]+adjust_value
                if last_stay.seconds != 0:
                    append_flag += 0x1  #起
                    append_flag_str += '起'
                    #node += interval["start"]
                    interval += node["start"]
                elif row==1 and self.start_from_this:
                    append_flag += 0x1  #始发站附加
                    append_flag_str += '始'
                    interval += node["start"]
                else:
                    append_flag_str += '通'

                if current_stay.seconds:
                    append_flag += 0x2  #停
                    append_flag_str += '停'
                    interval += node["stop"]
                else:
                    append_flag_str += '通'
                interval_str = "%d:%02d"%(int(interval/60),interval%60)

                interval_dt = timedelta(days=0,seconds=interval)
                ddsj = last_time+interval_dt
                cfsj = ddsj + current_stay

            timeTable.item(row,3).setData(-1,ddsj)
            timeTable.item(row,3).setText(ddsj.strftime('%H:%M:%S'))
            timeTable.item(row,4).setText(cfsj.strftime('%H:%M:%S'))
            timeTable.item(row,5).setData(-1,append_flag)
            timeTable.item(row,5).setText(append_flag_str)
            timeTable.item(row,7).setText(interval_str)

            last_time = cfsj

    def _stayTime(self,row:int)->timedelta:
        """
        计算row行的停留时间。返回timedelta。
        """
        ds = self.timeTable.cellWidget(row,1).value()*60+self.timeTable.cellWidget(row,2).value()
        return timedelta(days=0,seconds=ds)

    def _arriveTime(self,row:int):
        return self.timeTable.item(row,3).data(-1)

    def _leaveTime(self,row:int):
        return self._arriveTime(row)+self._stayTime(row)

    def _cal_interval(self,node:dict,flag:int):
        """
        计算区间运行时分。
        """
        dt = node["interval"]
        if 0x1&flag:
            dt += node["start"]

        if 0x2&flag:
            dt += node["stop"]

        return dt

    def _former_clicked(self):
        self.btnNext.setEnabled(True)
        self.btnOk.setEnabled(False)
        self.btnFormer.setEnabled(False)
        self.graphWindow.delTrainLine(self.train)
        self.stackedWidget.setCurrentIndex(0)
        self.timeTable.setRowCount(0)

    def _ok_clicked(self):
        if not self.train.timetable:
            QtWidgets.QMessageBox.information(self,'提示','未排图。双击要排图的终点站所在行来排图，然后再次点击确定')
            return
        self.interrupted = False

        if not self.isAppend:
            graph: Graph = self.graphWindow.graph
            if self.setCheci:
                checi,ok = QtWidgets.QInputDialog.getText(self,'车次设置','当前排图列车车次')
                if not ok:
                    return
                while not checi or graph.checiExisted(checi):
                    QtWidgets.QMessageBox.information(self,"提示","无效车次。车次不能为空，且不能与本运行图当前存在的车次重复。请重新设置。")
                    checi,ok = QtWidgets.QInputDialog.getText(self, '车次设置', '当前排图列车车次')
                    if not ok:
                        return
                self.train.setFullCheci(checi)
                self.train.autoTrainType()

            graph.addTrain(self.train)
            if self.train.items():
                self.graphWindow.delTrainLine(self.train)
            self.graphWindow.addTrainLine(self.train)

        else:
            #追加排图模式
            if self.train.items():
                self.graphWindow.delTrainLine(self.train)

            train:Train = self.graph.trainFromCheci(self.train.fullCheci())

            if train.items():
                self.graphWindow.delTrainLine(train)

            train.coverData(self.train)
            self.train = train
            self.graphWindow.addTrainLine(train)

        if self.setCheci:
            QtWidgets.QMessageBox.information(self, '提示', '排图成功。请到“当前车次设置”中继续编辑相关信息。')
        self.trainOK.emit(self.train)
        self.close()
        try:
            self.parentWidget().close()
        except:
            pass

    def _test_collid(self):
        """
        检测当前行的时刻冲突风险
        数据结构：
        dict{
            "time":datetime,
            "down":bool,
            "checi":str,
            "type":str,
        """
        print("test_collid")
        row = self.timeTable.currentRow()
        station_name = self.timeTable.item(row,0).text()
        ddsj = self._arriveTime(row)
        cfsj = self._leaveTime(row)
        ddsj = ddsj.replace(1900,1,1)
        cfsj = cfsj.replace(1900,1,1)

        timeTable_dicts = self.graph.stationTimeTable(station_name)

        dialog = QtWidgets.QDialog(self)
        dialog.resize(400,400)

        dialog.setWindowTitle(f"冲突检查*{station_name}")

        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(f"现在检查{station_name}站 当前排图车次"
                                 f"到达时间前20分钟至"
                                 f"出发时间后1小时的图定列车时刻表。\n")
        addText = f"到达时间：{ddsj.strftime('%H:%M:%S')}\n"
        addText += f"出发时间：{cfsj.strftime('%H:%M:%S')}"
        label.setText(label.text()+addText)
        start_time = ddsj-timedelta(days=0,seconds=1200)
        end_time = cfsj+timedelta(days=0,seconds=3600)
        label.setWordWrap(True)
        layout.addWidget(label)

        #重构数据
        events = []
        for node in timeTable_dicts:
            if node["ddsj"] >= start_time and node["ddsj"] <= end_time:
                reform = {
                    "checi":node["train"].fullCheci(),
                    "down":node["train"].stationDown(station_name,self.graph),
                    "time":node["ddsj"],
                }
                if node["ddsj"] == node["cfsj"]:
                    reform["type"] = '通过'
                else:
                    reform["type"] = '到达'
                reform["time"] = reform["time"].replace(1900, 1, 1)
                events.append(reform)

            if node["cfsj"] >= start_time and node["cfsj"] <= end_time:
                reform = {
                    "checi": node["train"].fullCheci(),
                    "down": node["train"].stationDown(station_name,self.graph),
                    "time": node["cfsj"],
                }
                if node["ddsj"] != node["cfsj"]:
                    reform["type"] = "发车"
                    reform["time"] = reform["time"].replace(1900, 1, 1)
                    events.append(reform)
        print(ddsj,cfsj,events)

        #排序
        for i in range(len(events)-1):
            t = i
            for j in range(i+1,len(events)):
                if events[j]["time"] < events[t]["time"]:
                    t = j
            temp=events[i];events[i]=events[t];events[t]=temp

        textEdit = QtWidgets.QTextBrowser()

        down_text = ""
        up_text = ""
        none_text = ""

        for event in events:
            text = f"{event['time'].strftime('%H:%M:%S')} {event['checi']}次 {event['type']}<br>"
            if abs((event['time']-ddsj).seconds)<600 or abs((event['time']-cfsj).seconds)<600:
                text = f'<span style="color:#ff0000;">{text}</span>'
                pass
            if event["down"] is True:
                down_text += text
            elif event["down"] is False:
                up_text += text
            else:
                none_text += text

        text = f"""\
下行：<br>
{down_text if down_text else '下行无冲突列车'}<br>
        <br>
上行：<br>
{up_text if up_text else '上行无冲突列车'}<br>\
        """
        if none_text:
            text += f"\n\n{'未知方向（通常是未排图列车）：' if none_text else ''}<br>"
        f"{none_text if none_text else ''}<br>"

        textEdit.setHtml(text)
        layout.addWidget(textEdit)

        dialog.setLayout(layout)
        dialog.exec_()


"""
从stationTimetable移植的，车站可视化部分对话框代码。
"""
from .pyETRCExceptions import *
from .data import *
from .stationvisualize import StationGraphWidget
from .utility import PEControlledTable
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt

class StationVisualizeDialog(QtWidgets.QDialog):
    stationVisualizeChanged = QtCore.pyqtSignal(int)  # emit to stationVisualize
    def __init__(self,graph:Graph,station_dicts:list,station_name:str,parent=None):
        super(StationVisualizeDialog, self).__init__(parent)
        self.graph=graph
        self.station_dicts = station_dicts
        self.station_name = station_name
        self.initUI()

    def initUI(self):
        station_dicts = self.station_dicts
        station_name = self.station_name
        self.setWindowTitle(f"车站停车示意图*{station_name}")

        phlayout = QtWidgets.QHBoxLayout()  # parent HBoxLayout
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        group = QtWidgets.QButtonGroup(self)
        radioManual = QtWidgets.QRadioButton("手动铺画")
        self.radioManual = radioManual
        radioDouble = QtWidgets.QRadioButton("双线铺画")
        self.radioDouble = radioDouble
        radioSingle = QtWidgets.QRadioButton("单线铺画")
        self.radioSingle = radioSingle
        cvlayout = QtWidgets.QVBoxLayout()
        cvlayout.addWidget(radioManual)
        group.addButton(radioManual)
        cvlayout.addWidget(radioDouble)
        group.addButton(radioDouble)
        cvlayout.addWidget(radioSingle)
        group.addButton(radioSingle)
        flayout.addRow("铺画模式", cvlayout)
        radioManual.setChecked(True)
        # radioDouble.toggled.connect(visualWidget.setDoubleLine)
        radioManual.toggled.connect(self._manual_mode_changed)

        group = QtWidgets.QButtonGroup(self)
        hlayout = QtWidgets.QHBoxLayout()
        radioMainStay = QtWidgets.QRadioButton("允许")
        radioMainStayNo = QtWidgets.QRadioButton("不允许")
        hlayout.addWidget(radioMainStay)
        hlayout.addWidget(radioMainStayNo)
        self.radioMainStay = radioMainStay
        self.radioMainStayNo = radioMainStayNo
        group.addButton(radioMainStay)
        group.addButton(radioMainStayNo)
        flayout.addRow("正线停车", hlayout)
        radioMainStayNo.setChecked(True)
        # radioMainStay.toggled.connect(visualWidget.setAllowMainStay)
        self.radioMainStay.setEnabled(False)
        self.radioMainStayNo.setEnabled(False)

        spinSame = QtWidgets.QSpinBox()
        spinSame.setValue(0)
        spinSame.setRange(0, 999)
        # spinSame.valueChanged.connect(visualWidget.setSameSplitTime)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinSame)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        self.spinSame = spinSame
        flayout.addRow("同向接车间隔", hlayout)

        spinOpposite = QtWidgets.QSpinBox()
        self.spinOpposite = spinOpposite
        spinOpposite.setValue(0)
        spinOpposite.setRange(0, 999)
        # spinOpposite.valueChanged.connect(visualWidget.setOppositeSplitTime)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinOpposite)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        flayout.addRow("对向接车间隔", hlayout)

        vlayout.addLayout(flayout)
        vlayout.addWidget(QtWidgets.QLabel("股道次序表"))

        tw:QtWidgets.QTableWidget = PEControlledTable()
        tw.setDefaultRowHeight(self.graph.UIConfigData()['table_row_height'])
        tw.setEditTriggers(QtWidgets.QTableWidget.CurrentChanged)
        self.trackTable = tw  # type: QtWidgets.QTableWidget
        vlayout.addWidget(tw)
        tw.setColumnCount(1)
        tw.setHorizontalHeaderLabels(['股道名称'])

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("铺画")
        btnOk.clicked.connect(self._set_ok)
        btnSave = QtWidgets.QPushButton("保存")
        btnSave.clicked.connect(self._save_tracks)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnSave)
        vlayout.addLayout(hlayout)

        phlayout.addLayout(vlayout)

        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("说明：本功能提供股道占用示意图。如果选择“手动模式”，"
                                 "则依据车次时刻表中设置的“股道”安排；否则系统自动安排。"
                                 "系统自动安排的结果仅是一种可能方案，与真实安排方案无关。"
                                 "如果选择“手动模式”，则自动安排的车次一律按照单线且允许正线停车模式。")
        label.setWordWrap(True)
        layout.addWidget(label)

        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setRange(1, 120)
        slider.setMaximumWidth(600)
        # slider.valueChanged.connect(lambda x:print(x))
        slider.setMaximumWidth(800)
        slider.setValue(20)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(QtWidgets.QLabel("水平缩放"))
        hlayout.addStretch(10)
        hlayout.addWidget(QtWidgets.QLabel("大"))
        hlayout.addStretch(2)
        hlayout.addWidget(slider)
        hlayout.addStretch(2)
        hlayout.addWidget(QtWidgets.QLabel("小"))
        hlayout.addStretch(20)

        slider.valueChanged.connect(lambda x: self.stationVisualizeChanged.emit(x))
        layout.addLayout(hlayout)

        widget = StationGraphWidget(station_dicts, self.graph, station_name,
                                    self.graph.line.stationTracks(self.station_name),self)
        layout.addWidget(widget)
        self.visualWidget = widget  # type:StationGraphWidget
        self._updateTable()

        phlayout.addLayout(layout)
        self.setLayout(phlayout)
        self.showManualMessage()

    def _updateTable(self):
        """
        更新股道表
        """
        tw = self.trackTable
        order = self.visualWidget.track_order
        tw.setRowCount(len(order))
        TWI = QtWidgets.QTableWidgetItem
        for i,t in enumerate(order):
            tw.setItem(i,0,TWI(t))
            tw.setRowHeight(i,self.graph.UIConfigData()['table_row_height'])

    # slots
    def _manual_mode_changed(self,manual:bool):
        """
        手动模式变更
        """
        if manual:
            self.radioMainStay.setChecked(True)
            self.radioMainStay.setEnabled(False)
            self.radioMainStayNo.setEnabled(False)
            self.trackTable.setEnabled(True)
        else:
            self.radioMainStay.setEnabled(True)
            self.radioMainStayNo.setEnabled(True)
            self.trackTable.setEnabled(False)

    def _set_ok(self):
        if self.radioManual.isChecked():
            self.visualWidget.setManual(True)
            self.visualWidget.track_order.clear()
            self.visualWidget.single_names.clear()
            self.visualWidget.single_list.clear()
            for r in range(self.trackTable.rowCount()):
                self.visualWidget.single_list.append([])
                name = self.trackTable.item(r,0).text()
                self.visualWidget.track_order.append(name)
                self.visualWidget.single_map[name] = len(self.visualWidget.single_list)-1
                self.visualWidget.single_names.append(name)
        else:
            self.visualWidget.setManual(False)
            if self.radioDouble.isChecked():
                self.visualWidget.setDoubleLine(True)
            else:
                self.visualWidget.setDoubleLine(False)
            if self.radioMainStay.isChecked():
                self.visualWidget.setAllowMainStay(True)
            else:
                self.visualWidget.setAllowMainStay(False)
        self.visualWidget.setSameSplitTime(self.spinSame.value())
        self.visualWidget.setOppositeSplitTime(self.spinOpposite.value())

        self.visualWidget.repaintGraphAdvanced()
        self._updateTable()
        self.showManualMessage()

    def _save_tracks(self):
        if not self.question("将上表中的股道信息保存到线路信息中，并清除原来保存的信息，下次查看股道表时自动读入。\n"
                             "是否确认？"):
            return
        tracks = []
        for row in range(self.trackTable.rowCount()):
            tracks.append(self.trackTable.item(row,0).text())
        self.graph.line.setStationTracks(self.station_name,tracks)

    def showManualMessage(self):
        if self.visualWidget.msg:
            txt = '\n'.join(self.visualWidget.msg)
            QtWidgets.QMessageBox.information(self,'提示',txt)
            self.visualWidget.msg.clear()

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, "问题", note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

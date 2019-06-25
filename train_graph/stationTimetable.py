"""
2019.06.25新增
独立“车站时刻表”（ctrl+E）功能。
只包括指定车站后的部分，不包括最开始选车站的部分。
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from .graph import Graph
from .train import Train
from .circuit import Circuit
from .stationvisualize import StationGraphWidget
from .trainFilter import TrainFilter
import sys


class StationTimetable(QtWidgets.QDialog):
    showStatusInfo = QtCore.pyqtSignal(str)
    stationVisualizeChanged = QtCore.pyqtSignal(int)  # emit to stationVisualize

    def __init__(self, graph: Graph, station: str, parent=None):
        super(StationTimetable, self).__init__(parent)
        self.graph = graph
        self.station = station
        self.filter = TrainFilter(self.graph,self)
        self.filter.FilterChanged.connect(self._setStationTimetable)
        self.initUI()

    def initUI(self):
        timetable_dicts = self.graph.stationTimeTable(self.station)
        self.timetable_dicts = timetable_dicts
        self.resize(600, 600)
        self.setWindowTitle(f"车站时刻表*{self.station}")
        layout = QtWidgets.QVBoxLayout()

        checkStopOnly = QtWidgets.QCheckBox('不显示通过列车')
        layout.addWidget(checkStopOnly)
        self.checkStopOnly = checkStopOnly
        checkStopOnly.toggled.connect(self._station_timetable_stop_only_changed)

        btnFilter = QtWidgets.QPushButton("车次筛选器")
        btnFilter.setMaximumWidth(200)
        btnFilter.clicked.connect(self.filter.setFilter)
        layout.addWidget(btnFilter)

        label = QtWidgets.QLabel(f"*{self.station}*在本线时刻表如下：")
        layout.addWidget(label)

        tableWidget = QtWidgets.QTableWidget()
        self.tableWidget = tableWidget
        tableWidget.setColumnCount(12)
        tableWidget.setHorizontalHeaderLabels(['车次', '站名', '到点', '开点',
                                               '类型', '停站', '方向', '始发', '终到',
                                               '车底','担当','备注',])
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        column_width = (80, 100, 100, 100, 80, 80, 80, 90, 90, 90, 90, 90)
        for i, s in enumerate(column_width):
            tableWidget.setColumnWidth(i, s)

        self._setStationTimetable(False)

        layout.addWidget(tableWidget)
        hlayout = QtWidgets.QHBoxLayout()
        btnOut = QtWidgets.QPushButton("导出")
        btnVisual = QtWidgets.QPushButton("可视化")
        btnClose = QtWidgets.QPushButton("关闭")
        btnClose.clicked.connect(self.close)
        btnOut.clicked.connect(self._station_timetable_out)
        btnVisual.clicked.connect(self._station_visualize)
        hlayout.addWidget(btnOut)
        hlayout.addWidget(btnVisual)
        hlayout.addWidget(btnClose)
        layout.addLayout(hlayout)

        self.setLayout(layout)

    def _station_timetable_stop_only_changed(self, stopOnly: bool):
        self._setStationTimetable(stopOnly)

    def _setStationTimetable(self, stop_only=None):
        if stop_only is None:
            stop_only = self.checkStopOnly.isChecked()
        timetable_dicts = self.timetable_dicts
        tableWidget = self.tableWidget
        station_name = self.station
        tableWidget.setRowCount(0)
        row = -1
        for _, node in enumerate(timetable_dicts):
            train = node["train"]
            if not self.filter.check(train):
                continue
            stop_text = train.stationStopBehaviour(station_name)
            if stop_only and stop_text in ('通过', '不通过'):
                # print(train.fullCheci(),stop_text)
                continue

            row += 1
            tableWidget.insertRow(row)
            tableWidget.setRowHeight(row, self.graph.UIConfigData()['table_row_height'])

            item = QtWidgets.QTableWidgetItem(train.fullCheci())
            tableWidget.setItem(row, 0, item)

            item = QtWidgets.QTableWidgetItem(node["station_name"])
            tableWidget.setItem(row, 1, item)

            item = QtWidgets.QTableWidgetItem(node["ddsj"].strftime('%H:%M:%S'))
            tableWidget.setItem(row, 2, item)

            item = QtWidgets.QTableWidgetItem(node["cfsj"].strftime('%H:%M:%S'))
            tableWidget.setItem(row, 3, item)

            item = QtWidgets.QTableWidgetItem(train.trainType())
            tableWidget.setItem(row, 4, item)

            tableWidget.setItem(row, 5, QtWidgets.QTableWidgetItem(stop_text))

            down = train.stationDown(station_name, self.graph)
            text = '下行' if down is True else ('上行' if down is False else '未知')
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 6, item)

            text = train.sfz
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 7, item)

            text = train.zdz
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 8, item)

            text = node['note']
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 11, item)

            circuit:Circuit = train.carriageCircuit()
            if circuit is not None:
                tableWidget.setItem(row,9,QtWidgets.QTableWidgetItem(circuit.model()))
                tableWidget.setItem(row,10,QtWidgets.QTableWidgetItem(circuit.owner()))
            else:
                tableWidget.setItem(row, 9, QtWidgets.QTableWidgetItem('-'))
                tableWidget.setItem(row, 10, QtWidgets.QTableWidgetItem('-'))

    def _station_visualize(self):
        station_dicts = self.timetable_dicts
        station_name = self.station
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"车站停车示意图*{station_name}")
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("说明：此功能将各个车次在本线到开时间可视化，绘出股道占用时间图。"
                                 "本图只是提供一种可能的情况，并不代表实际情况，如有雷同，纯属巧合；"
                                 "本图默认采用双线股道铺排模式，Ⅰ、Ⅱ为上下行正线，其他为侧线；"
                                 "所有下行车安排在下行股道；且通过车优先安排在正线，停车列车只安排在侧线。")
        label.setWordWrap(True)
        layout.addWidget(label)

        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setRange(1, 120)
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
        btnAdvance = QtWidgets.QPushButton("高级")
        hlayout.addWidget(btnAdvance)

        slider.valueChanged.connect(lambda x: self.stationVisualSizeChanged.emit(x))
        layout.addLayout(hlayout)

        widget = StationGraphWidget(station_dicts, self.graph, station_name, self)
        btnAdvance.clicked.connect(lambda: self._station_visualize_advance(widget))
        layout.addWidget(widget)
        dialog.setLayout(layout)
        dialog.exec_()

    def _station_visualize_advance(self, visualWidget: StationGraphWidget):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('高级')
        flayout = QtWidgets.QFormLayout()

        group = QtWidgets.QButtonGroup()
        radioDouble = QtWidgets.QRadioButton("双线铺画")
        dialog.radioDouble = radioDouble
        radioSingle = QtWidgets.QRadioButton("单线铺画")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(radioDouble)
        group.addButton(radioDouble)
        hlayout.addWidget(radioSingle)
        group.addButton(radioSingle)
        flayout.addRow("铺画模式", hlayout)
        if visualWidget.doubleLine():
            radioDouble.setChecked(True)
        else:
            radioSingle.setChecked(True)
        radioDouble.toggled.connect(visualWidget.setDoubleLine)

        group = QtWidgets.QButtonGroup()
        hlayout = QtWidgets.QHBoxLayout()
        radioMainStay = QtWidgets.QRadioButton("允许")
        radioMainStayNo = QtWidgets.QRadioButton("不允许")
        hlayout.addWidget(radioMainStay)
        hlayout.addWidget(radioMainStayNo)
        dialog.radioMainStay = radioMainStay
        group.addButton(radioMainStay)
        group.addButton(radioMainStayNo)
        flayout.addRow("正线停车", hlayout)
        if visualWidget.allowMainStay():
            radioMainStay.setChecked(True)
        else:
            radioMainStayNo.setChecked(True)
        radioMainStay.toggled.connect(visualWidget.setAllowMainStay)

        spinSame = QtWidgets.QSpinBox()
        spinSame.setValue(visualWidget.sameSplitTime())
        spinSame.setRange(0, 999)
        spinSame.valueChanged.connect(visualWidget.setSameSplitTime)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinSame)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        flayout.addRow("同向接车间隔", hlayout)

        spinOpposite = QtWidgets.QSpinBox()
        spinOpposite.setValue(visualWidget.oppositeSplitTime())
        spinOpposite.setRange(0, 999)
        spinOpposite.valueChanged.connect(visualWidget.setOppositeSplitTime)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinOpposite)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        flayout.addRow("对向接车间隔", hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        flayout.addRow(hlayout)

        btnOk.clicked.connect(visualWidget.rePaintGraphAdvanced)
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(dialog.close)

        dialog.setLayout(flayout)
        dialog.exec_()

    def _station_timetable_out(self):
        tableWidget = self.tableWidget
        self.showStatusInfo.emit("正在准备导出……")
        try:
            import xlwt
        except ImportError:
            self._derr("错误：此功能需要'xlwt'库支持。")
            self.showStatusInfo.emit("就绪")
            return

        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self, '选择文件', filter='*.xls')
        if not ok:
            return

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('车站时刻表')

        for i, s in enumerate(['车次', '站名', '到点', '开点', '类型', '停站', '方向', '始发', '终到',
                               '车底','担当','备注']):
            ws.write(0, i, s)

        for row in range(tableWidget.rowCount()):
            for col in range(12):
                ws.write(row + 1, col, tableWidget.item(row, col).text())
        wb.save(filename)
        self._dout("时刻表导出成功！")
        self.statusOut("就绪")

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

"""
2019.06.25新增
独立“车站时刻表”（ctrl+E）功能。
只包括指定车站后的部分，不包括最开始选车站的部分。
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from .data.graph import Graph,Train,Circuit
from .stationvisualize import StationGraphWidget
from .stationVisualizeDialog import StationVisualizeDialog
from .trainFilter import TrainFilter
import sys


class StationTimetable(QtWidgets.QDialog):
    showStatusInfo = QtCore.pyqtSignal(str)

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
        tableWidget.setColumnCount(13)
        tableWidget.setHorizontalHeaderLabels(['车次', '站名', '到点', '开点',
                                               '类型', '停站', '方向', '始发', '终到','股道',
                                               '车底','担当','备注',])
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        column_width = (80, 100, 100, 100, 80, 80, 80, 90, 90, 90, 90, 90, 90)
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

            tableWidget.setItem(row,9,QtWidgets.QTableWidgetItem(node['track']))

            text = node['note']
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 12, item)

            circuit:Circuit = train.carriageCircuit()
            if circuit is not None:
                tableWidget.setItem(row,10,QtWidgets.QTableWidgetItem(circuit.model()))
                tableWidget.setItem(row,11,QtWidgets.QTableWidgetItem(circuit.owner()))
            else:
                tableWidget.setItem(row, 10, QtWidgets.QTableWidgetItem('-'))
                tableWidget.setItem(row, 11, QtWidgets.QTableWidgetItem('-'))

    def _station_visualize(self):
        dialog = StationVisualizeDialog(self.graph,
                                        self.timetable_dicts,self.station,self)
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

        for i, s in enumerate(['车次', '站名', '到点', '开点', '类型',
                               '停站', '方向', '始发', '终到', '股道',
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

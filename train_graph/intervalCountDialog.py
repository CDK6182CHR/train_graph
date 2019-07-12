"""
2019.05.10从mainGraphWindow中抽离出区间对数表功能的对话框。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
import sys
from .graph import Graph
from .train import Train
from .trainFilter import TrainFilter
from .intervalTrainDialog import IntervalTrainDialog

class IntervaLCountDialog(QtWidgets.QDialog):
    intervalRowDoubleClicked = QtCore.pyqtSignal(str,str)  # 双击打开区间车次表。
    def __init__(self,graph:Graph,parent=None):
        super(IntervaLCountDialog, self).__init__(parent)
        self.graph = graph
        self.initUI()

    def initUI(self):
        self.setWindowTitle('区间对数表')
        self.resize(700, 700)
        layout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        hlayout = QtWidgets.QHBoxLayout()
        radioStart = QtWidgets.QRadioButton('出发站')
        radioEnd = QtWidgets.QRadioButton('到达站')
        group = QtWidgets.QButtonGroup(self)
        group.addButton(radioStart)
        group.addButton(radioEnd)
        radioStart.setChecked(True)
        hlayout.addWidget(radioStart)
        hlayout.addWidget(radioEnd)
        flayout.addRow('查询方式', hlayout)
        self.startView = True

        radioStart.toggled.connect(self._interval_count_method_changed)

        combo = QtWidgets.QComboBox()
        combo.setMaximumWidth(250)
        combo.setEditable(True)
        for st in self.graph.stations():
            combo.addItem(st)
        self.combo = combo
        flayout.addRow('查询车站', combo)
        layout.addLayout(flayout)
        self.station = ''
        combo.currentTextChanged.connect(self._interval_count_station_changed)

        checkPassengerOnly = QtWidgets.QCheckBox('仅显示办客车站')
        checkPassengerOnly.setChecked(True)
        checkFreightOnly = QtWidgets.QCheckBox('仅显示办货车站')
        self.checkPassengerOnly = checkPassengerOnly
        self.checkFreightOnly = checkFreightOnly
        checkPassengerOnly.toggled.connect(self._set_interval_count_table)
        checkFreightOnly.toggled.connect(self._set_interval_count_table)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(checkPassengerOnly)
        hlayout.addWidget(checkFreightOnly)
        flayout.addRow('车站筛选',hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        checkBusinessOnly = QtWidgets.QCheckBox('仅营业车次')
        self.checkBusinessOnly = checkBusinessOnly
        checkBusinessOnly.setChecked(True)
        checkStoppedOnly = QtWidgets.QCheckBox('仅停车车次')
        self.checkStoppedOnly = checkStoppedOnly
        hlayout.addWidget(checkBusinessOnly)
        hlayout.addWidget(checkStoppedOnly)
        flayout.addRow('显示车次',hlayout)
        checkBusinessOnly.toggled.connect(self._set_interval_count_table)
        checkStoppedOnly.toggled.connect(self._set_interval_count_table)

        self.filter = TrainFilter(self.graph, self)
        btnFilt = QtWidgets.QPushButton("筛选")
        btnFilt.setMaximumWidth(120)
        self.filter.FilterChanged.connect(self._set_interval_count_table)
        btnFilt.clicked.connect(self.filter.setFilter)
        flayout.addRow('车次筛选', btnFilt)

        label = QtWidgets.QLabel('双击区间行显示对应区间的车次。')
        layout.addWidget(label)

        tableWidget = QtWidgets.QTableWidget()
        self.tableWidget = tableWidget
        tableWidget.setColumnCount(6)
        tableWidget.itemDoubleClicked.connect(self._double_clicked)
        tableWidget.setHorizontalHeaderLabels(('发站', '到站', '车次数', '始发数', '终到数', '始发终到'))
        widths = (110, 110, 80, 80, 80, 80)
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        for i, s in enumerate(widths):
            tableWidget.setColumnWidth(i, s)
        self._set_interval_count_table()
        layout.addWidget(tableWidget)

        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(self.close)
        layout.addWidget(btnClose)
        self.setLayout(layout)

    def _interval_count_method_changed(self, x):
        self.startView = x
        self._set_interval_count_table()

    def _interval_count_station_changed(self,st):
        self._set_interval_count_table()

    def _station_filter_changed(self):
        """
        筛选是否仅包含办客或办货车站变化。
        """
        self._set_interval_count_table()

    def _set_interval_count_table(self):
        tableWidget: QtWidgets.QTableWidget = self.tableWidget
        startView = self.startView
        self.station = self.combo.currentText()
        station = self.station
        if not station:
            return
        tableWidget.setRowCount(0)
        count_list = self.graph.getIntervalCount_faster(station, startView, self.filter,
                                                 self.checkPassengerOnly.isChecked(),
                                                 self.checkFreightOnly.isChecked(),
                                                 self.checkBusinessOnly.isChecked(),
                                                 self.checkStoppedOnly.isChecked(),
                                                 )
        for i, s in enumerate(count_list):
            tableWidget.insertRow(i)
            tableWidget.setRowHeight(i, self.graph.UIConfigData()['table_row_height'])
            tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(s['from']))
            tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(s['to']))
            tableWidget.setItem(i, 2, QtWidgets.QTableWidgetItem(str(s['count']) if s['count'] else '-'))
            tableWidget.setItem(i, 3, QtWidgets.QTableWidgetItem(str(s['countSfz']) if s['countSfz'] else '-'))
            tableWidget.setItem(i, 4, QtWidgets.QTableWidgetItem(str(s['countZdz']) if s['countZdz'] else '-'))
            tableWidget.setItem(i, 5, QtWidgets.QTableWidgetItem(str(s['countSfZd']) if s['countSfZd'] else '-'))

    def _double_clicked(self,item:QtWidgets.QTableWidgetItem):
        row = item.row()
        start = self.tableWidget.item(row,0).text()
        end = self.tableWidget.item(row,1).text()
        d = IntervalTrainDialog(self.graph,self)
        d.comboStart.setCurrentText(start)
        d.comboEnd.setCurrentText(end)
        d.exec_()

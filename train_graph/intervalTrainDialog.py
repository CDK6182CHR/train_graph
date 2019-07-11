"""
独立出的区间车次表功能。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .train import Train
from .trainFilter import TrainFilter
from .graph import Graph

class IntervalTrainDialog(QtWidgets.QDialog):
    def __init__(self,graph:Graph,parent=None):
        super(IntervalTrainDialog, self).__init__(parent)
        self.graph=graph
        self.initUI()

    def initUI(self):
        self.setWindowTitle('区间车次表')
        self.resize(700, 700)
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        comboStart = QtWidgets.QComboBox()
        comboEnd = QtWidgets.QComboBox()
        self.comboStart = comboStart
        self.comboEnd = comboEnd
        self.start = self.graph.firstStation()
        self.end = self.graph.lastStation()
        for st in self.graph.stations():
            comboStart.addItem(st)
            comboEnd.addItem(st)
        comboStart.setEditable(True)
        comboStart.setCurrentText(self.start)
        comboEnd.setEditable(True)
        comboEnd.setCurrentText(self.end)
        comboStart.currentTextChanged.connect(self._interval_trains_start_changed)
        comboEnd.currentTextChanged.connect(self._interval_trains_end_changed)

        flayout.addRow('发站', comboStart)
        flayout.addRow('到站', comboEnd)

        checkBusinessOnly = QtWidgets.QCheckBox('仅营业车次')
        checkStoppedOnly = QtWidgets.QCheckBox('仅停车车次')
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(checkBusinessOnly)
        hlayout.addWidget(checkStoppedOnly)
        self.checkBusinessOnly = checkBusinessOnly
        self.checkStoppedOnly = checkStoppedOnly
        self.checkBusinessOnly.setChecked(True)
        flayout.addRow('显示条件',hlayout)
        checkBusinessOnly.toggled.connect(self._interval_trains_table)
        checkStoppedOnly.toggled.connect(self._interval_trains_table)

        self.filter = TrainFilter(self.graph, self)
        btnFilt = QtWidgets.QPushButton("筛选")
        btnFilt.setMaximumWidth(120)
        self.filter.FilterChanged.connect(self._interval_trains_table)
        btnFilt.clicked.connect(self.filter.setFilter)
        flayout.addRow('车次筛选', btnFilt)

        vlayout.addLayout(flayout)

        tableWidget = QtWidgets.QTableWidget()
        self.tableWidget = tableWidget

        tableWidget.setColumnCount(10)
        tableWidget.setHorizontalHeaderLabels(('车次', '类型', '发站', '发时', '到站', '到时',
                                               '历时', '旅速', '始发', '终到'))
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        for i, s in enumerate((80, 60, 110, 90, 110, 90, 120, 80, 80, 80)):
            tableWidget.setColumnWidth(i, s)
        self._interval_trains_table()

        vlayout.addWidget(tableWidget)
        btnClose = QtWidgets.QPushButton('关闭')
        vlayout.addWidget(btnClose)
        btnClose.clicked.connect(self.close)
        self.setLayout(vlayout)

    def _interval_trains_start_changed(self,start):
        self.start = start
        self._interval_trains_table()

    def _interval_trains_end_changed(self,end):
        self.end = end
        self._interval_trains_table()

    def _interval_trains_table(self):
        """
        重新设置表内容时调用此处。
        """
        if self.start == self.end or not self.start or not self.end:
            return
        tb: QtWidgets.QTableWidget = self.tableWidget
        IT = QtWidgets.QTableWidgetItem

        # ('车次','类型','发站','发时','到站','到时', '历时','旅速','始发','终到')
        # print(dialog.start,dialog.end)
        info_dicts = self.graph.getIntervalTrains(self.start, self.end, self.filter,
                                                  businessOnly=self.checkBusinessOnly.isChecked(),
                                                  stoppedOnly=self.checkStoppedOnly.isChecked())
        tb.setRowCount(0)

        for i, tr in enumerate(info_dicts):
            train: Train = tr['train']
            tb.insertRow(i)
            tb.setRowHeight(i, self.graph.UIConfigData()['table_row_height'])

            tb.setItem(i, 0, IT(train.fullCheci()))
            tb.setItem(i, 1, IT(train.type))
            start_dict = train.stationDict(self.start)
            tb.setItem(i, 2, IT(start_dict['zhanming']))
            tb.setItem(i, 3, IT(start_dict['cfsj'].strftime('%H:%M:%S')))
            end_dict = train.stationDict(self.end)
            tb.setItem(i, 4, IT(end_dict['zhanming']))
            tb.setItem(i, 5, IT(end_dict['ddsj'].strftime('%H:%M:%S')))
            tm_int = train.gapBetweenStation(self.start, self.end)
            tm_int = int(tm_int)
            tm_str = f"{tm_int//3600:02d}:{tm_int//60%60:02d}:{tm_int%60:02d}"
            try:
                mile = self.graph.gapBetween(self.start, self.end)
                mile_str = f"{mile:.1f}"
            except:
                mile_str = "NA"
            try:
                speed = mile / tm_int * 1000 * 3.6
                speed_str = f"{speed:.2f}"
            except:
                speed = 0
                speed_str = 'NA'
            tb.setItem(i, 6, IT(tm_str))
            item = IT(speed_str)
            if speed:
                item.setData(Qt.DisplayRole, speed)
            tb.setItem(i, 7, item)
            tb.setItem(i, 8, IT(train.sfz))
            tb.setItem(i, 9, IT(train.zdz))


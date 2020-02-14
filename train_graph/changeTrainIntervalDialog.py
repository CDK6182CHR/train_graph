"""
2019.07.04新增，当前车次区间时刻表重排（ctrl+shift+R）。
点击确定后关闭窗口但不析构。当rulerPaint点击确定时，铺画生效。
此模块与mainGraphWindow有牵连。
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from .data.graph import Train, Graph
from .rulerPaint import rulerPainter
from datetime import datetime


class ChangeTrainIntervalDialog(QtWidgets.QDialog):
    trainChangeOk = QtCore.pyqtSignal(Train, Train)  # 第一个是本车，第二个是铺画的车次。

    def __init__(self, train, graph, main):
        super(ChangeTrainIntervalDialog, self).__init__(main)
        self.train = train  # type:Train
        self.graph = graph  # type:Graph
        self.main = main  # type:QtWidgets.QMainWindow
        self.startIndex = 0
        self.endIndex = 0
        self.initUI()

    def initUI(self):
        self.setWindowTitle('区间时刻重排')
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(
            "请在下表中选择要覆盖的区间。所选的第一个站和最后一个站之间将被认为是要覆盖的区间。如果不选择，默认覆盖所有数据。点击确定后，系统将调起“标尺排图向导”功能，将新铺画车次的【所有】时刻覆盖所选区间。请注意，在排图向导中，不要附加到任何车次！")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        flayout = QtWidgets.QFormLayout()
        checiEdit = QtWidgets.QLineEdit(self.train.fullCheci())
        checiEdit.setFocusPolicy(Qt.NoFocus)
        flayout.addRow('当前车次',checiEdit)
        vlayout.addLayout(flayout)

        listWidget = QtWidgets.QListWidget()
        self.listWidget = listWidget
        for st_dict in self.train.stationDicts():
            text = f"{st_dict['zhanming']:10s} "
            if not self.train.stationStopped(st_dict):
                text += '...'
            else:
                text += st_dict['ddsj'].strftime('%H:%M:%S')
            text += '/'+st_dict['cfsj'].strftime('%H:%M:%S')
            listWidget.addItem(text)
        listWidget.setSelectionMode(listWidget.MultiSelection)
        vlayout.addWidget(listWidget)

        btnOk = QtWidgets.QPushButton('确定(&Y)')
        btnCancel = QtWidgets.QPushButton('取消(&C)')

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        btnCancel.clicked.connect(self.close)
        btnOk.clicked.connect(self._ok_clicked)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)

    def _ok_clicked(self):
        minrow, maxrow = self.train.stationCount() - 1, 0
        for item in self.listWidget.selectedItems():
            r = self.listWidget.row(item)
            minrow = min(minrow, r)
            maxrow = max(maxrow, r)
        self.startIndex = minrow
        self.endIndex = maxrow
        self.close()
        start_dict = self.train.timetable[minrow]
        end_dict = self.train.timetable[maxrow]
        start_name = start_dict['zhanming']
        start_stop_sec = Train.dt(start_dict['ddsj'], start_dict['cfsj'])
        end_stop_sec = Train.dt(end_dict['ddsj'], end_dict['cfsj'])

        start_time: datetime = self.train.timetable[minrow]['ddsj']
        start_time_q = QtCore.QTime(start_time.hour, start_time.minute, start_time.second)
        painter = rulerPainter(self.main.GraphWidget, setCheci=False)
        painter.startTimeEdit.setTime(start_time_q)
        self.rulerPainter = painter
        painter.trainOK.connect(self._paint_ok)
        painter.comboAppend.setEnabled(False)
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("标尺排图向导")
        dock.setWidget(painter)
        dock.setFeatures(dock.DockWidgetMovable | dock.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.NoDockWidgetArea)
        self.main.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)
        dock.resize(700, 800)

        # 尝试在向导中寻找起始站
        if self.train.stationDown(start_name):
            painter.radio1.setChecked(True)
        else:
            painter.radio2.setChecked(True)
        find_start = False
        for r in range(painter.listWidget.count()):
            item = painter.listWidget.item(r)
            if item.text() == start_name:
                painter.listWidget.setCurrentRow(r)
                item.setSelected(True)
                find_start = True
        if find_start:
            painter.btnNext.click()

        # 尝试在第二步的表格中寻找起始站和结束站
        tw = painter.timeTable  # type:QtWidgets.QTableWidget
        for r in range(painter.timeTable.rowCount()):
            if tw.item(r, 0).text() == start_name:
                tw.cellWidget(r, 1).setValue(start_stop_sec // 60)
                tw.cellWidget(r, 2).setValue(start_stop_sec % 60)
            if tw.item(r, 0).text() == end_dict['zhanming']:
                tw.cellWidget(r, 1).setValue(end_stop_sec // 60)
                tw.cellWidget(r, 2).setValue(end_stop_sec % 60)
                break

    def _paint_ok(self, anTrain: Train):
        """
        铺画结束。
        """
        print("ChangeTrainIntervalDialog::paint_ok")
        self.train.intervalExchange(self.startIndex, self.endIndex, anTrain, 0, anTrain.stationCount() - 1)
        self.trainChangeOk.emit(self.train, anTrain)
        self.setParent(None)  # 丢弃引用，析构

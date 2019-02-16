"""
展示当前车次某个区间信息的窗口。
sample:
        图定站点数：110
        停站次数：
        运行里程：1196.0
        运行时间：11:26:00
        旅行速度：104.61km/h
        纯运行时间：10:09:00
        总停站时间：1:17:00
        技术速度：117.83km/h
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from .train import Train

class IntervalWidget(QtWidgets.QDialog):
    def __init__(self,graph,parent=None):
        super().__init__(parent)
        self.setParent(parent)
        self.graph=graph
        self.line=graph.line
        self.train=None
        self._initUI()

    def _initUI(self):
        layout=QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.startCombo=QtWidgets.QComboBox()
        self.startCombo.currentTextChanged.connect(self._start_changed)
        layout.addRow('区间起点',self.startCombo)

        self.endCombo=QtWidgets.QComboBox()
        self.endCombo.currentTextChanged.connect(self._end_changed)
        layout.addRow('区间终点',self.endCombo)

        self.stationCountEdit=QtWidgets.QLineEdit()
        #self.stationCountEdit.setEnabled(False)
        layout.addRow('图定站点数',self.stationCountEdit)

        self.stopCountEdit=QtWidgets.QLineEdit()
        #self.stopCountEdit.setEnabled(False)
        layout.addRow('图定停站数',self.stopCountEdit)

        self.mileEdit=QtWidgets.QLineEdit()
        #self.mileEdit.setEnabled(False)
        layout.addRow('区间里程',self.mileEdit)

        self.totalTimeEdit=QtWidgets.QLineEdit()
        #self.totalTimeEdit.setEnabled(False)
        layout.addRow('总运行时间',self.totalTimeEdit)

        self.travelSpeedEdit=QtWidgets.QLineEdit()
        #self.travelSpeedEdit.setEnabled(False)
        self.travelSpeedEdit.setToolTip('旅行速度对应时间为列车区间运行总时间，包括停站和起停附加时间。')
        layout.addRow('旅行速度',self.travelSpeedEdit)

        self.runTimeEdit=QtWidgets.QLineEdit()
        #self.runTimeEdit.setEnabled(False)
        layout.addRow('纯运行时间',self.runTimeEdit)

        self.stopTimeEdit=QtWidgets.QLineEdit()
        #self.stopTimeEdit.setEnabled(False)
        layout.addRow('总停站时间',self.stopTimeEdit)

        self.technicalSpeedEdit=QtWidgets.QLineEdit()
        #self.technicalSpeedEdit.setEnabled(False)
        layout.addRow('技术速度',self.technicalSpeedEdit)
        self.technicalSpeedEdit.setToolTip('技术速度对应时间为列车区间运行总时间减去停站时间。')

        btnClose=QtWidgets.QPushButton("关闭")
        btnClose.clicked.connect(self.close)
        layout.addRow(btnClose)

    def _start_changed(self,name):
        if self.train is None:
            return
        self.startStation = name
        self.endCombo.clear()
        flag=False
        for station,_,_ in self.train.station_infos():
            if flag and self.line.stationInLine(station):
                self.endCombo.addItem(station)
            if station==name:
                flag=True
        self.setData()


    def _end_changed(self,name):
        self.endStation=name
        try:
            self.setData()
        except:
            pass

    def setTrain(self,train:Train):
        self.train=train
        if self.train is not None:
            self.setWindowTitle(f'区间性质*{train.fullCheci()}')
            self.startStation=train.localFirst(self.graph)
            self.endStation=train.localLast(self.graph)
            for station,_,_ in self.train.station_infos():
                if self.line.stationInLine(station) and station != self.train.localLast(self.graph):
                    self.startCombo.addItem(station)
            self.setData()

    def setData(self):
        runTime,stopTime=self.train.intervalRunStayTime(self.graph,self.startStation,self.endStation)
        totalTime=runTime+stopTime
        mile=self.graph.gapBetween(self.startStation,self.endStation)
        stationCount=self.train.intervalCount(self.graph,self.startStation,self.endStation)
        stopCount=self.train.intervalStopCount(self.graph,self.startStation,self.endStation)

        self.mileEdit.setText(f'{mile:.2f} km')
        self.stationCountEdit.setText(str(stationCount))
        self.stopCountEdit.setText(str(stopCount))
        self.runTimeEdit.setText(f"{int(runTime/3600):02d}:{int(runTime%3600/60):02d}:{runTime%60:02d}")
        self.totalTimeEdit.setText(f"{int(totalTime/3600):02d}:{int(totalTime%3600/60):02d}:{totalTime%60:02d}")
        self.stopTimeEdit.setText(f"{int(stopTime/3600):02d}:{int(stopTime%3600/60):02d}:{stopTime%60:02d}")

        try:
            travelSpeed=mile/totalTime*3600
            travelSpeed_str=f"{travelSpeed:.3f} km/h"
        except ZeroDivisionError:
            travelSpeed_str='NA'

        try:
            technicalSpeed=mile/runTime*3600
            technicalSpeed_str=f"{technicalSpeed:.3f} km/h"
        except ZeroDivisionError:
            technicalSpeed_str='NA'

        self.travelSpeedEdit.setText(travelSpeed_str)
        self.technicalSpeedEdit.setText(technicalSpeed_str)

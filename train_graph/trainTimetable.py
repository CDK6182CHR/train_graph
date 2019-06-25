"""
2019.06.25新增。
当前车次时刻表停靠面板，只读的时刻表，设计原则为尽可能简洁明了，直接继承TableWidget。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .train import Train
from .graph import Graph

class TrainTimetable(QtWidgets.QWidget):
    def __init__(self,graph:Graph,parent=None):
        super(TrainTimetable, self).__init__(parent)
        self.graph = graph
        self.train = None
        self.initUI()

    def initUI(self):
        """
        站名，到点，开点，停时，备注。
        """
        self.setWindowTitle('当前车次时刻表')
        tableWidget = QtWidgets.QTableWidget()
        self.tableWidget = tableWidget
        vlayout = QtWidgets.QVBoxLayout()

        flayout = QtWidgets.QFormLayout()
        checiEdit = QtWidgets.QLineEdit()
        checiEdit.setFocusPolicy(Qt.NoFocus)
        flayout.addRow('当前车次',checiEdit)
        self.checiEdit = checiEdit
        vlayout.addLayout(flayout)

        label = QtWidgets.QLabel("下表中红色字体表示该站营业，蓝色表示该站停车但不营业。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        vlayout.addWidget(tableWidget)
        self.setLayout(vlayout)

        tableWidget.setColumnCount(5)
        for i,s in enumerate((100,85,85,90,100)):
            tableWidget.setColumnWidth(i,s)
        tableWidget.setHorizontalHeaderLabels(('站名','到点','开点','停时','备注'))
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

    def setData(self,train:Train=None):
        if train is None:
            train = self.train
        else:
            self.train=train
        tw = self.tableWidget
        tw.setRowCount(0)
        if train is None:
            return
        self.checiEdit.setText(train.fullCheci())
        tw.setRowCount(train.stationCount())
        TWI = QtWidgets.QTableWidgetItem

        for row,st_dict in enumerate(train.stationDicts()):
            zm,ddsj,cfsj = st_dict['zhanming'],st_dict['ddsj'],st_dict['cfsj']
            tw.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])

            item = TWI(zm)
            if train.stationBusiness(st_dict):
                item.setForeground(QtGui.QBrush(Qt.red))
            elif train.stationStopped(st_dict):
                item.setForeground(QtGui.QBrush(Qt.blue))
            tw.setItem(row,0,item)

            tw.setItem(row,1,TWI(ddsj.strftime('%H:%M:%S')))
            tw.setItem(row,2,TWI(cfsj.strftime('%H:%M:%S')))
            tw.setItem(row,3,TWI(train.stopTimeStr(st_dict)))
            tw.setItem(row,4,TWI(st_dict.get('note','')))

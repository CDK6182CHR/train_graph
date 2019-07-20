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
        tableWidget.verticalHeader().hide()
        vlayout = QtWidgets.QVBoxLayout()

        checiEdit = QtWidgets.QLineEdit()
        checiEdit.setFocusPolicy(Qt.NoFocus)
        self.checiEdit = checiEdit
        vlayout.addWidget(checiEdit)

        # label = QtWidgets.QLabel("下表中红色字体表示该站营业，蓝色表示该站停车但不营业。")
        # label.setWordWrap(True)
        # vlayout.addWidget(label)

        vlayout.addWidget(tableWidget)
        self.setLayout(vlayout)

        tableWidget.setColumnCount(3)
        for i,s in enumerate((100,85,100)):
            tableWidget.setColumnWidth(i,s)
        tableWidget.setHorizontalHeaderLabels(('站名','时刻','停时备注'))
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

    def setData(self,train:Train=None):
        if train is None:
            train = Train(self.graph)
            self.train = train
        else:
            self.train=train
        tw = self.tableWidget
        # if train is None:
        #     return
        self.checiEdit.setText(f"{train.fullCheci()}({train.sfz}->{train.zdz})")
        self.checiEdit.setCursorPosition(0)
        tw.setRowCount(train.stationCount()*2)
        TWI = QtWidgets.QTableWidgetItem

        tw.setAlternatingRowColors(True)

        # for row,st_dict in enumerate(train.stationDicts()):
        #     zm,ddsj,cfsj = st_dict['zhanming'],st_dict['ddsj'],st_dict['cfsj']
        #     tw.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])
        #
        #     item0 = TWI(zm)
        #     item1 = TWI(ddsj.strftime('%H:%M:%S'))
        #     item2 = TWI(cfsj.strftime('%H:%M:%S'))
        #     item3 = TWI(train.stopTimeStr(st_dict))
        #     item4 = TWI(st_dict.get('note',''))
        #     items = (item0,item1,item2,item3,item4)
        #     color = Qt.black
        #     if not self.graph.stationInLine(zm):
        #         color = Qt.darkGray
        #     elif train.stationBusiness(st_dict):
        #         color = Qt.red
        #     elif train.stationStopped(st_dict):
        #         color = Qt.blue
        #
        #     for i,item in enumerate(items):
        #         item.setForeground(QtGui.QBrush(color))
        #         tw.setItem(row,i,item)
        for i in range(0,2*train.stationCount(),2):
            tw.setRowHeight(i,self.graph.UIConfigData()['table_row_height']*0.9)
            tw.setRowHeight(i+1,self.graph.UIConfigData()['table_row_height']*0.9)
            tw.setSpan(i,0,2,1)
            st_dict = train.timetable[i//2]
            zm, ddsj, cfsj = st_dict['zhanming'], st_dict['ddsj'], st_dict['cfsj']
            item0 = TWI(zm)
            item0.setTextAlignment(Qt.AlignCenter)
            if ddsj != cfsj:
                item1 = TWI(ddsj.strftime('%H:%M:%S'))
                item2 = TWI(cfsj.strftime('%H:%M:%S'))
            elif train.isSfz(zm):
                item1 = TWI('')
                item2 = TWI(cfsj.strftime('%H:%M:%S'))
            elif train.isZdz(zm):
                item1 = TWI(ddsj.strftime('%H:%M:%S'))
                item2 = TWI('--')
            else:
                item1 = TWI('...')
                item2 = TWI(cfsj.strftime('%H:%M:%S'))
            item1.setTextAlignment(Qt.AlignCenter)

            item2.setTextAlignment(Qt.AlignCenter)
            item3 = TWI(train.stopTimeStr(st_dict))
            item4 = TWI(st_dict.get('note',''))
            # 设置颜色
            if True:
                color = Qt.black
                if not self.graph.stationInLine(zm):
                    color = Qt.darkGray
                elif train.stationBusiness(st_dict):
                    color = Qt.red
                elif train.stationStopped(st_dict):
                    color = Qt.blue
                items = (item0,item1,item2,item3,item4)
                for item in items:
                    item.setForeground(QtGui.QBrush(color))
            tw.setItem(i,0,item0)
            tw.setItem(i,1,item1)
            tw.setItem(i+1,1,item2)
            tw.setItem(i,2,item3)
            tw.setItem(i+1,2,item4)
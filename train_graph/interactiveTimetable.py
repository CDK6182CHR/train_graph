"""
2019.07.05新增，交互式时刻表调整停靠面板（ctrl+shift+Y），调整立即生效，对本线站的时刻调整立即重新铺画。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .graph import Train,Graph
from datetime import datetime

class InteractiveTimetable(QtWidgets.QWidget):
    trainTimetableChanged = QtCore.pyqtSignal(Train,dict)  # 被调整的列车对象和被调整的站。
    def __init__(self,graph,parent=None):
        super(InteractiveTimetable, self).__init__(parent)
        self.graph = graph  # type:Graph
        self.train = None  # type:Train
        self.updating = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('交互式时刻表')
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()
        checiEdit = QtWidgets.QLineEdit()
        self.checiEdit = checiEdit
        checiEdit.setFocusPolicy(Qt.NoFocus)
        flayout.addRow('当前车次',checiEdit)
        vlayout.addLayout(flayout)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.verticalHeader().hide()
        tableWidget.itemDoubleClicked.connect(self._double_clicked)
        self.tableWidget = tableWidget
        tableWidget.setColumnCount(3)
        tableWidget.setHorizontalHeaderLabels(('站名','时刻','停时备注'))
        for i,s in enumerate((100,100,100)):
            tableWidget.setColumnWidth(i,s)
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        vlayout.addWidget(tableWidget)

        self.setLayout(vlayout)

    def setData(self,train:Train=None):
        """
        除去最开始外，self.train都不会是None。所以遇到None直接return。
        编辑栏增加ddsjEdit.row属性，记录所在的（物理）行号。
        """
        self.updating=True
        if train is None:
            train = self.train
        if train is None:
            return
        self.train = train
        self.checiEdit.setText(train.fullCheci())

        tw = self.tableWidget
        tw.setRowCount(train.stationCount()*2)
        TWI = QtWidgets.QTableWidgetItem

        for r in range(0,tw.rowCount(),2):
            st_dict = train.timetable[r//2]
            tw.setSpan(r,0,2,1)

            brush = self.itemBrush(st_dict,train)
            zm = st_dict['zhanming']
            item = TWI(zm)
            item.setTextAlignment(Qt.AlignCenter)
            tw.setItem(r,0,item)
            item.setForeground(brush)

            # 设置time会触发槽函数，所以必须先设置这几个，否则Item就是None。
            item = TWI(train.stopTimeStr(st_dict))
            item.setForeground(brush)
            tw.setItem(r, 2, item)
            item = TWI(st_dict.get('note', ''))
            item.setForeground(brush)
            tw.setItem(r + 1, 2, item)

            ddsjEdit = tw.cellWidget(r,1)
            if ddsjEdit is None:
                ddsjEdit = QtWidgets.QTimeEdit()
                ddsjEdit.setDisplayFormat('hh:mm:ss')
                ddsjEdit.setMaximumHeight(30)
                tw.setCellWidget(r,1,ddsjEdit)
                ddsjEdit.row = r
                ddsjEdit.timeChanged.connect(self._time_changed)
            ddsjEdit.setTime(self.pytime2QTime(st_dict['ddsj']))
            cfsjEdit = tw.cellWidget(r+1,1)
            if cfsjEdit is None:
                cfsjEdit = QtWidgets.QTimeEdit()
                cfsjEdit.setDisplayFormat('hh:mm:ss')
                cfsjEdit.setMinimumHeight(30)
                tw.setCellWidget(r+1,1,cfsjEdit)
                cfsjEdit.row = r+1
                cfsjEdit.timeChanged.connect(self._time_changed)
            cfsjEdit.setTime(self.pytime2QTime(st_dict['cfsj']))
            # tw.setRowHeight(r, self.graph.UIConfigData()['table_row_height'])
            tw.setRowHeight(r,30)
            tw.setRowHeight(r + 1, self.graph.UIConfigData()['table_row_height'])
        self.updating=False

    @staticmethod
    def pytime2QTime(tm:datetime)->QtCore.QTime:
        return QtCore.QTime(tm.hour,tm.minute,tm.second)

    @staticmethod
    def QTime2pytime(qtm:QtCore.QTime)->datetime:
        return datetime(1900,1,1,qtm.hour(),qtm.minute(),qtm.second())


    def itemBrush(self,st_dict:dict,train:Train)->QtGui.QBrush:
        if not self.graph.stationInLine(st_dict['zhanming']):
            return (QtGui.QBrush(Qt.darkGray))
        elif train.stationBusiness(st_dict):
            return(QtGui.QBrush(Qt.red))
        elif train.stationStopped(st_dict):
            return(QtGui.QBrush(Qt.blue))
        return QtGui.QBrush(Qt.black)

    # slots
    def _time_changed(self,tm:QtCore.QTime):
        if self.updating:
            return
        sender:QtWidgets.QTimeEdit = self.sender()
        row = sender.row
        dct = self.train.timetable[row//2]
        if row%2==0:  # 到达时间行
            dct['ddsj'] = self.QTime2pytime(tm)
        else:  # 出发时间
            dct['cfsj'] = self.QTime2pytime(tm)
        # 保证相关的Item存在。
        brush = self.itemBrush(dct,self.train)
        r = row-(row%2)
        tw = self.tableWidget
        tw.item(r,0).setForeground(brush)
        tw.item(r,2).setText(self.train.stopTimeStr(dct))
        tw.item(r,2).setForeground(brush)
        tw.item(r+1,2).setForeground(brush)

        self.trainTimetableChanged.emit(self.train,dct)

    def _double_clicked(self,item:QtWidgets.QTableWidgetItem):
        r = item.row()
        dct = self.train.timetable[r//2]
        if self.train.stationStoppedOrStartEnd(dct):
            dct['business']=not self.train.stationBusiness(dct)
            row=r-(r%2)
            brush = self.itemBrush(dct,self.train)
            self.tableWidget.item(row,0).setForeground(brush)
            self.tableWidget.item(row,2).setForeground(brush)
            self.tableWidget.item(row+1,2).setForeground(brush)

"""
比较两车次时刻表信息。原则上每次启用的时候构造，也就是是一次性的。
原则上应该保证两列车的车次是一样的，但不做检查。
规定颜色：
灰色-删除
蓝色-新增
红色-调整
"""
from .data import *
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from typing import List,Tuple,Dict

class TrainDiffDialog(QtWidgets.QDialog):
    def __init__(self,train1:Train,train2:Train,graph:Graph,diffData=None,parent=None):
        super(TrainDiffDialog, self).__init__(parent)
        self.train1 = train1
        self.train2 = train2
        self.graph = graph
        if diffData is None:
            self.trainDiffData:List[Tuple[Train.StationDiffType,TrainStation,TrainStation]]\
                = train1.globalDiff(train2)
        else:
            self.trainDiffData:List[Tuple[Train.StationDiffType,TrainStation,TrainStation]]\
                = diffData
        self.initUI()
        self.setData()

    def initUI(self):
        self.setWindowTitle(f'列车时刻表对照*{self.train1.fullCheci()}')
        self.resize(800,700)
        vlayout = QtWidgets.QVBoxLayout()
        tw = QtWidgets.QTableWidget()
        tw.setEditTriggers(tw.NoEditTriggers)
        self.tableWidget = tw
        tw.setColumnCount(7)
        tw.setHorizontalHeaderLabels(('站名1','到点1','开点1','说明','站名2','到点2','开点2'))
        for i,s in enumerate((120,100,100,60,120,100,100)):
            tw.setColumnWidth(i,s)
        vlayout.addWidget(tw)
        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(self.close)
        vlayout.addWidget(btnClose)
        self.setLayout(vlayout)

    def setData(self):
        self.tableWidget.setRowCount(len(self.trainDiffData))
        height = self.graph.UIConfigData()['table_row_height']
        tw = self.tableWidget
        TWI = QtWidgets.QTableWidgetItem
        for row,tple in enumerate(self.trainDiffData):
            tp,st1,st2 = tple
            tw.setRowHeight(row,height)
            # 先设置单元格数据
            if st1 is not None:
                tw.setItem(row,0,TWI(st1['zhanming']))
                tw.setItem(row,1,TWI(st1['ddsj'].strftime('%H:%M:%S')))
                tw.setItem(row,2,TWI(st1['cfsj'].strftime('%H:%M:%S')))
            if st2 is not None:
                tw.setItem(row,4,TWI(st2['zhanming']))
                tw.setItem(row,5,TWI(st2['ddsj'].strftime('%H:%M:%S')))
                tw.setItem(row,6,TWI(st2['cfsj'].strftime("%H:%M:%S")))
            if tp == Train.StationDiffType.Unchanged:
                pass
            elif tp == Train.StationDiffType.NewAdded:
                tw.setItem(row, 3, TWI('新增'))
                for i in range(4,7):
                    self._setItemColor(row,i,Qt.blue)
            elif tp == Train.StationDiffType.Deleted:
                tw.setItem(row, 3, TWI('删除'))
                for i in range(3):
                    self._setItemColor(row,i,Qt.darkGray)
            elif tp == Train.StationDiffType.NameChanged:
                tw.setItem(row,3,TWI('改名'))
                self._setItemColor(row, 0, Qt.red)
                self._setItemColor(row, 4, Qt.red)
            else:  # 各种时刻调整
                tw.setItem(row,3,TWI('改点'))
                if tp == Train.StationDiffType.ArriveModified:
                    self._setItemColor(row, 1, Qt.red)
                    self._setItemColor(row, 5, Qt.red)
                elif tp == Train.StationDiffType.DepartModified:
                    self._setItemColor(row, 2, Qt.red)
                    self._setItemColor(row, 6, Qt.red)
                else:  # BothModified
                    self._setItemColor(row, 1, Qt.red)
                    self._setItemColor(row, 2, Qt.red)
                    self._setItemColor(row, 5, Qt.red)
                    self._setItemColor(row, 6, Qt.red)


    def _setItemColor(self,row:int,col:int,color:QtGui.QColor):
        item:QtWidgets.QTableWidgetItem = self.tableWidget.item(row,col)
        if not isinstance(item,QtWidgets.QTableWidgetItem):
            return
        item.setForeground(QtGui.QBrush(color))




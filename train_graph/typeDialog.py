"""
由configWidget调出，列车类型管理界面。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
import sys
from .train import Train
from .graph import Graph

class TypeDialog(QtWidgets.QDialog):
    def __init__(self,graph:Graph,system:bool,parent=None):
        super(TypeDialog, self).__init__(parent)
        self.graph = graph
        self.system = system
        self.UIDict = self.graph.UIConfigData() if not system else self.graph.sysConfigData()
        self.initUI()
        self.setData()

    def initUI(self):
        self.setWindowTitle('类型管理')
        self.resize(400,600)
        vlayout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel('在这里设置本系统默认的车次类型。车次类型是有序的，可以任意重复，'
                                 '上面的优先级高于下面的。本系统由车次推定类型、由类型推定是否为客车'
                                 '皆依据此处。')
        label.setWordWrap(True)
        vlayout.addWidget(label)

        hlayout = QtWidgets.QHBoxLayout()
        btnInsBef=QtWidgets.QPushButton('前插')
        btnInsAft=QtWidgets.QPushButton('后插')
        btnDel = QtWidgets.QPushButton('删除')
        hlayout.addWidget(btnInsBef)
        hlayout.addWidget(btnInsAft)
        hlayout.addWidget(btnDel)
        vlayout.addLayout(hlayout)
        btnInsBef.clicked.connect(self._insert_before)
        btnInsAft.clicked.connect(self._insert_after)
        btnDel.clicked.connect(self._del)

        hlayout = QtWidgets.QHBoxLayout()
        btnMoveUp = QtWidgets.QPushButton('上移')
        btnMoveDown = QtWidgets.QPushButton('下移')
        hlayout.addWidget(btnMoveUp)
        hlayout.addWidget(btnMoveDown)
        vlayout.addLayout(hlayout)
        btnMoveUp.clicked.connect(self._move_up)
        btnMoveDown.clicked.connect(self._move_down)

        tableWidget = QtWidgets.QTableWidget()
        self.tableWidget = tableWidget
        tableWidget.setColumnCount(3)
        for i,s in enumerate((120,120,60)):
            tableWidget.setColumnWidth(i,s)
        tableWidget.setHorizontalHeaderLabels(('名称','正则','客车'))
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)
        vlayout.addWidget(tableWidget)

        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(self.close)
        vlayout.addWidget(btnClose)

        self.setLayout(vlayout)

    def setData(self):
        """
        将所有数据重设
        """
        nrows = len(self.UIDict['type_regex'])
        self.tableWidget.setRowCount(nrows)
        n=0
        for name,reg,passenger in self.UIDict['type_regex']:
            self.setTableRow(n,name,reg,passenger)
            n+=1


    def setTableRow(self,row,name,reg,passenger:bool):
        tableWidget = self.tableWidget
        tableWidget.setRowHeight(row,self.UIDict['table_row_height'])

        tableWidget.setItem(row,0,QtWidgets.QTableWidgetItem(name))
        tableWidget.setItem(row,1,QtWidgets.QTableWidgetItem(reg))
        item = QtWidgets.QTableWidgetItem()
        if passenger:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)
        tableWidget.setItem(row,2,item)

    # slots
    def _insert_before(self):
        row = self.tableWidget.currentRow()
        self.tableWidget.insertRow(row)
        self.tableWidget.setRowHeight(row,self.UIDict['table_row_height'])

    def _insert_after(self):
        row = self.tableWidget.currentRow()
        self.tableWidget.insertRow(row+1)
        self.tableWidget.setRowHeight(row+1,self.UIDict['table_row_height'])

    def _del(self):
        self.tableWidget.removeRow(self.tableWidget.currentRow())

    def _move_up(self):
        row = self.tableWidget.currentRow()
        if row == 0:
            return
        name = self.tableWidget.item(row,0).text()
        reg = self.tableWidget.item(row,1).text()
        pas = (self.tableWidget.item(row,2).checkState()==Qt.Checked)
        self.tableWidget.removeRow(row)
        self.tableWidget.insertRow(row-1)
        self.setTableRow(row-1,name,reg,pas)
        self.tableWidget.setCurrentCell(row-1,self.tableWidget.currentColumn())

    def _move_down(self):
        row = self.tableWidget.currentRow()
        if row == self.tableWidget.rowCount()-1:
            return
        name = self.tableWidget.item(row, 0).text()
        reg = self.tableWidget.item(row, 1).text()
        pas = (self.tableWidget.item(row, 2).checkState() == Qt.Checked)
        self.tableWidget.removeRow(row)
        self.tableWidget.insertRow(row + 1)
        self.setTableRow(row + 1, name, reg, pas)
        self.tableWidget.setCurrentCell(row + 1, self.tableWidget.currentColumn())

    def apply(self):
        """
        应用更改，这个由上级调用
        """
        self.UIDict['type_regex'].clear()
        for row in range(self.tableWidget.rowCount()):
            self.UIDict['type_regex'].append((
                self.tableWidget.item(row,0).text(),
                self.tableWidget.item(row,1).text(),
                (self.tableWidget.item(row,2).checkState()==Qt.Checked)
            ))

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from typing import Type


class PEControlledTable(QtWidgets.QWidget):
    """
    adapter设计模式。
    pyETRC使用的TableWidget的封装，包括增删、上下移动的按钮。
    使用反射把有关的信息转发到QTableWidget中去。
    内置的东西都使用下划线开头。
    注意 暂时不支持cellWidget交换操作。
    """
    RowInserted = QtCore.pyqtSignal(int)
    def __init__(self, meta:[Type[QtWidgets.QTableWidget]]=QtWidgets.QTableWidget, parent=None):
        """
        class PEControlledTable <T extends QTableWidget>
        """
        super(PEControlledTable, self).__init__(parent)
        self._tw = meta(self)
        self._defaultRowHeight = 30
        self._initUI()

    def _initUI(self):
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self._tw)
        hlayout = QtWidgets.QHBoxLayout()
        PB = QtWidgets.QPushButton
        b = PB("前插")
        b.clicked.connect(self.addBefore)
        b.setMinimumWidth(50)
        hlayout.addWidget(b)
        b = PB("后插")
        b.clicked.connect(self.addAfter)
        b.setMinimumWidth(50)
        hlayout.addWidget(b)
        b = PB("删除")
        b.clicked.connect(self.remove)
        b.setMinimumWidth(50)
        hlayout.addWidget(b)
        b = PB("上移")
        b.clicked.connect(self.up)
        b.setMinimumWidth(50)
        hlayout.addWidget(b)
        b = PB("下移")
        b.clicked.connect(self.down)
        b.setMinimumWidth(50)
        hlayout.addWidget(b)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)

    def insertRow(self, row):
        """
        模版方法，指出插入一行的动作。
        """
        self._tw.insertRow(row)
        self._tw.setRowHeight(row, self._defaultRowHeight)
        self.RowInserted.emit(row)

    def setDefaultRowHeight(self, h):
        self._defaultRowHeight = h

    def exchangeRow(self,row1:int,row2:int):
        """
        模版方法，交换两行的数据，由上移、下移函数调用。
        保证两行有效。
        """
        TWI = QtWidgets.QTableWidgetItem
        for c in range(self._tw.columnCount()):
            i = TWI(self._tw.item(row1, c))
            self._tw.setItem(row1, c, TWI(self._tw.item(row2, c)))
            self._tw.setItem(row2, c, i)

    def exchangeCellWidget(self,row1:int,row2:int,col:int,getMethodName:str,setMethodName:str):
        """
        在两行之间交换cellWidget的数据。
        适用于形式：
        \q tableWidget.cellWidget(row1,col).getMethodName()
        \q tableWidget.cellWidget(row1,col).setMethodName(v)
        """
        w1 = self._tw.cellWidget(row1,col)
        w2 = self._tw.cellWidget(row2,col)
        v1 = getattr(w1,getMethodName)()
        v2 = getattr(w2,getMethodName)()
        getattr(w1,setMethodName)(v2)
        getattr(w2,setMethodName)(v1)

    def __getattribute__(self, item):
        try:
            return super(PEControlledTable, self).__getattribute__(item)
        except AttributeError:
            return getattr(self._tw, item)

    # slots
    def addBefore(self):
        row = self._tw.currentRow()
        if row <= 0:
            self.insertRow(0)
        elif row >= self._tw.rowCount():
            self.insertRow(self._tw.rowCount() - 1)
        else:
            self.insertRow(row)

    def addAfter(self):
        row = self._tw.currentRow()
        if row < 0:
            self.insertRow(0)
        elif row >= self._tw.rowCount():
            self.insertRow(self._tw.rowCount())
        else:
            self.insertRow(row + 1)

    def remove(self):
        row = self._tw.currentRow()
        if 0 <= row < self._tw.rowCount():
            self._tw.removeRow(row)

    def up(self):
        row = self._tw.currentRow()
        if row <= 0:
            return

        self.exchangeRow(row-1,row)
        self._tw.setCurrentCell(row - 1, self._tw.currentColumn())

    def down(self):
        row = self._tw.currentRow()
        if row >= self._tw.rowCount() - 1:
            return
        self.exchangeRow(row+1,row)
        self._tw.setCurrentCell(row + 1, self._tw.currentColumn())

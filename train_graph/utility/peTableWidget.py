from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt


class PETableWidget(QtWidgets.QWidget):
    """
    adapter设计模式。
    pyETRC使用的TableWidget的封装，包括增删、上下移动的按钮。
    使用反射把有关的信息转发到QTableWidget中去。
    内置的东西都使用下划线开头。
    """

    def __init__(self, parent=None):
        super(PETableWidget, self).__init__(parent)
        self._tw = QtWidgets.QTableWidget(self)
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

    def insertRow(self, p_int):
        """
        模版方法，指出插入一行的动作。
        """
        self._tw.insertRow(p_int)
        self._tw.setRowHeight(p_int, self._defaultRowHeight)

    def setDefaultRowHeight(self, h):
        self._defaultRowHeight = h

    def __getattribute__(self, item):
        try:
            return super(PETableWidget, self).__getattribute__(item)
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
        TWI = QtWidgets.QTableWidgetItem
        if row <= 0:
            return
        for c in range(self._tw.columnCount()):
            i = TWI(self._tw.item(row - 1, c))
            self._tw.setItem(row - 1, c, TWI(self._tw.item(row, c)))
            self._tw.setItem(row, c, i)
            w = self._tw.cellWidget(row - 1, c)
            self._tw.setCellWidget(row - 1, c, self._tw.cellWidget(row, c))
            self._tw.setCellWidget(row, c, w)
        self._tw.setCurrentCell(row - 1, self._tw.currentColumn())

    def down(self):
        row = self._tw.currentRow()
        TWI = QtWidgets.QTableWidgetItem
        if row >= self._tw.rowCount() - 1:
            return
        for c in range(self._tw.columnCount()):
            i = TWI(self._tw.item(row + 1, c))
            self._tw.setItem(row + 1, c, TWI(self._tw.item(row, c)))
            self._tw.setItem(row, c, i)
            w = self._tw.cellWidget(row + 1, c)
            self._tw.setCellWidget(row + 1, c, self._tw.cellWidget(row, c))
            self._tw.setCellWidget(row, c, w)
        self._tw.setCurrentCell(row + 1, self._tw.currentColumn())

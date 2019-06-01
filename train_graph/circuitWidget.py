"""
交路编辑停靠面板
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .pyETRCExceptions import *
from .circuit import Circuit
from .graph import Graph
from .train import Train
from .circuitDialog import CircuitDialog

class CircuitWidget(QtWidgets.QWidget):
    def __init__(self,graph:Graph,parent=None):
        super(CircuitWidget, self).__init__(parent)
        self.graph=graph
        self.dialog = CircuitDialog(self.graph,self)
        self.initUI()
        self.setData()

    def initUI(self):
        self.setWindowTitle('交路编辑')
        vlayout = QtWidgets.QVBoxLayout()
        tableWidget = QtWidgets.QTableWidget()

        self.tableWidget = tableWidget
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        self.tableWidget.setColumnCount(3)
        tableWidget.setHorizontalHeaderLabels(['交路名','车次列','注释'])

        for i,s in enumerate((120,120,120)):
            tableWidget.setColumnWidth(i,s)

        vlayout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnEdit = QtWidgets.QPushButton('编辑')
        tableWidget.itemDoubleClicked.connect(btnEdit.click)
        btnEdit.clicked.connect(self._edit_clicked)
        hlayout.addWidget(btnEdit)

        btnAdd = QtWidgets.QPushButton('添加')
        btnAdd.clicked.connect(self._add_circuit)
        hlayout.addWidget(btnAdd)

        btnDel = QtWidgets.QPushButton("删除")
        btnDel.clicked.connect(self._del_circuit)
        hlayout.addWidget(btnDel)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)

    def setData(self):
        """
        circuit对象封装在第0列。
        """
        tableWidget = self.tableWidget
        tableWidget.setRowCount(self.graph.circuitCount())
        for row,circuit in enumerate(self.graph.circuits()):
            tableWidget.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])

            item = QtWidgets.QTableWidgetItem(circuit.name())
            item.setData(Qt.UserRole,circuit)
            tableWidget.setItem(row,0,item)

            tableWidget.setItem(row,1,QtWidgets.QTableWidgetItem(circuit.orderStr()))

            tableWidget.setItem(row,2,QtWidgets.QTableWidgetItem(circuit.note()))

    # slots
    def _edit_clicked(self):
        pass

    def _add_circuit(self):
        self.dialog.exec_()

    def _del_circuit(self):
        pass
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
        self.dialog.NewCircuitAdded.connect(self._circuit_added)
        self.dialog.CircuitChangeApplied.connect(self._circuit_changed)
        self.initUI()
        self.setData()

    def initUI(self):
        self.setWindowTitle('交路编辑')
        vlayout = QtWidgets.QVBoxLayout()
        tableWidget = QtWidgets.QTableWidget()

        self.tableWidget = tableWidget
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        self.tableWidget.setColumnCount(4)
        tableWidget.setHorizontalHeaderLabels(['交路名','车次列','注释','高亮'])
        tableWidget.itemChanged.connect(self._table_item_changed)

        for i,s in enumerate((120,120,120,60)):
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

            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(Qt.Unchecked)
            tableWidget.setItem(row,3,item)

    def editCircuit(self,circuit:Circuit):
        """
        从currentWidget调用，直接编辑交路。
        """
        self.dialog.setData(circuit)
        self.dialog.exec_()

    # slots
    def _table_item_changed(self,item:QtWidgets.QTableWidgetItem):
        if item.column() == 3:
            circuit:Circuit = self.tableWidget.item(item.row(),0).data(Qt.UserRole)
            if item.checkState() == Qt.Checked:
                for node in circuit.nodes():
                    if node.train() is not None:
                        node.train().highlightItems()
            else:
                for node in circuit.nodes():
                    if node.train() is not None:
                        node.train().unHighlightItems()

    def _circuit_highlight(self):
        pass

    def _circuit_highlight_cancel(self):
        pass

    def _edit_clicked(self):
        row = self.tableWidget.currentRow()
        item = self.tableWidget.item(row, 0)
        if item is None:
            return
        circuit = item.data(Qt.UserRole)
        if isinstance(circuit,Circuit):
            self.dialog.setData(circuit)
            self.dialog.exec_()

    def _add_circuit(self):
        self.dialog.setData(None)
        self.dialog.exec_()

    def _del_circuit(self):
        row = self.tableWidget.currentRow()
        circuit = self.tableWidget.item(row,0).data(Qt.UserRole)
        if isinstance(circuit,Circuit):
            self.graph.delCircuit(circuit)
            self.tableWidget.removeRow(row)
        else:
            print("CircuitWidget::del_circuit: Unexpceted circuit data")

    def _circuit_changed(self,circuit:Circuit):
        """
        circuitDialog调用。修改既有circuit。
        线性算法。
        """
        tw = self.tableWidget
        for row in range(tw.rowCount()):
            if tw.item(row,0).data(Qt.UserRole) is circuit:
                tw.item(row,0).setText(circuit.name())
                tw.item(row,1).setText(circuit.orderStr())
                tw.item(row,2).setText(circuit.note())
                return
        print("CircuitWidget::circuit_changed not correctly called!")
        self._circuit_added(circuit)


    def _circuit_added(self,circuit:Circuit):
        """
        circuitDialog调用。增加新的circuit，为提高效率而设置。
        """
        print("circuit_added!")
        tw = self.tableWidget
        row = tw.rowCount()
        tw.insertRow(row)
        tw.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])
        item = QtWidgets.QTableWidgetItem(circuit.name())
        item.setData(Qt.UserRole,circuit)
        tw.setItem(row,0,item)
        tw.setItem(row,1,QtWidgets.QTableWidgetItem(circuit.orderStr()))
        tw.setItem(row,2,QtWidgets.QTableWidgetItem(circuit.note()))
        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Qt.Unchecked)
        tw.setItem(row,3,item)
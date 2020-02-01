"""
交路编辑停靠面板
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .pyETRCExceptions import *
from .data.circuit import Circuit
from .data.graph import Graph,Train
from .circuitDialog import CircuitDialog
from .circuitwidgets import *
from .dialogAdapter import DialogAdapter

class CircuitWidget(QtWidgets.QWidget):
    def __init__(self,graph:Graph,parent=None):
        super(CircuitWidget, self).__init__(parent)
        self.graph=graph
        self.dialog = CircuitDialog(self.graph,self)
        self.dialog.NewCircuitAdded.connect(self._circuit_added)
        self.dialog.CircuitChangeApplied.connect(self._circuit_changed)
        self.dialog.setWindowModality(Qt.NonModal)
        self.initUI()
        self.setData()

    def initUI(self):
        self.setWindowTitle('交路编辑')
        vlayout = QtWidgets.QVBoxLayout()
        tableWidget = QtWidgets.QTableWidget()

        self.tableWidget = tableWidget
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        self.tableWidget.setColumnCount(6)
        tableWidget.setHorizontalHeaderLabels(['高亮','交路名','车次列','车底','担当','注释'])
        tableWidget.itemChanged.connect(self._table_item_changed)
        header = tableWidget.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        for i,s in enumerate((40,110,110,100,100,120)):
            tableWidget.setColumnWidth(i,s)

        vlayout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnParse = QtWidgets.QPushButton('批量解析')
        hlayout.addWidget(btnParse)
        btnParse.clicked.connect(self.batch_parse)

        btnIdentify = QtWidgets.QPushButton('批量识别')
        hlayout.addWidget(btnIdentify)
        btnIdentify.clicked.connect(self.identify)
        vlayout.addLayout(hlayout)


        hlayout = QtWidgets.QHBoxLayout()
        btnEdit = QtWidgets.QPushButton('编辑(&E)')
        tableWidget.itemDoubleClicked.connect(btnEdit.click)
        btnEdit.clicked.connect(self._edit_clicked)
        hlayout.addWidget(btnEdit)

        btnAdd = QtWidgets.QPushButton('添加(&N)')
        btnAdd.clicked.connect(self._add_circuit)
        hlayout.addWidget(btnAdd)

        btnDel = QtWidgets.QPushButton("删除(&D)")
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
            tableWidget.setItem(row,1,item)

            tableWidget.setItem(row,2,QtWidgets.QTableWidgetItem(circuit.orderStr()))
            tableWidget.setItem(row,3,QtWidgets.QTableWidgetItem(circuit.model()))
            tableWidget.setItem(row,4,QtWidgets.QTableWidgetItem(circuit.owner()))
            tableWidget.setItem(row,5,QtWidgets.QTableWidgetItem(circuit.note()))

            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(Qt.Unchecked)
            tableWidget.setItem(row,0,item)
            item.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled)

    def editCircuit(self,circuit:Circuit):
        """
        从currentWidget调用，直接编辑交路。
        """
        self.dialog.setData(circuit)
        self.dialog.show()

    def currentCircuit(self)->Circuit:
        """
        返回当前行的Circuit对象，当前行无效则为None。
        """
        item = self.tableWidget.item(self.tableWidget.currentRow(),1)
        if isinstance(item,QtWidgets.QTableWidgetItem):
            return item.data(Qt.UserRole)
        return None

    # slots
    def _table_item_changed(self,item:QtWidgets.QTableWidgetItem):
        if item.column() == 0:
            circuit:Circuit = self.tableWidget.item(item.row(),1).data(Qt.UserRole)
            if item.checkState() == Qt.Checked:
                for node in circuit.nodes():
                    if node.train() is not None:
                        node.train().highlightItems(containLink=True)
            else:
                for node in circuit.nodes():
                    if node.train() is not None:
                        node.train().unHighlightItems(containLink=True)

    def _circuit_highlight(self):
        pass

    def _circuit_highlight_cancel(self):
        pass

    def _edit_clicked(self):
        row = self.tableWidget.currentRow()
        item = self.tableWidget.item(row, 1)
        if item is None:
            return
        circuit = item.data(Qt.UserRole)
        if isinstance(circuit,Circuit):
            self.dialog.setData(circuit)
            self.dialog.show()

    def _add_circuit(self):
        self.dialog.setData(None)
        self.dialog.show()

    def _del_circuit(self):
        row = self.tableWidget.currentRow()
        item = self.tableWidget.item(row,1)
        if isinstance(item,QtWidgets.QTableWidgetItem):
            circuit = item.data(Qt.UserRole)
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
            if tw.item(row,1).data(Qt.UserRole) is circuit:
                tw.item(row,1).setText(circuit.name())
                tw.item(row,2).setText(circuit.orderStr())
                tw.item(row,3).setText(circuit.model())
                tw.item(row,4).setText(circuit.owner())
                tw.item(row,5).setText(circuit.note())
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
        tw.setItem(row,1,item)
        tw.setItem(row,2,QtWidgets.QTableWidgetItem(circuit.orderStr()))
        tw.setItem(row,3,QtWidgets.QTableWidgetItem(circuit.model()))
        tw.setItem(row,4,QtWidgets.QTableWidgetItem(circuit.owner()))
        tw.setItem(row,5,QtWidgets.QTableWidgetItem(circuit.note()))
        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Qt.Unchecked)
        tw.setItem(row,0,item)

    def add_circuit_from_current(self,train):
        self._add_circuit()
        self.dialog.addTrain(train)

    def batch_parse(self):
        dialog = BatchParseCircuit(self.graph,self,self.parent())
        dialog.resize(1400,800)
        dialog.exec_()

    def identify(self):
        if not self.question('此操作将尝试识别交路中所有虚拟车次，将本线实际存在的车次识别成实体车次。是否继续？'):
            return
        full_only = self.question('是否仅识别完整车次？')
        # self._apply()
        totalResults = []
        for circuit in self.graph.circuits():
            results = circuit.identifyTrain(full_only)
            results.insert(0,f'交路{circuit}新的序列为：{circuit.orderStr()}')
            totalResults.extend(results)
        self.setData()
        tb = QtWidgets.QTextBrowser()
        tb.setWindowTitle('识别结果')
        tb.setText('\n'.join(totalResults))
        dialog = DialogAdapter(tb,self)
        dialog.resize(400,400)
        dialog.exec_()

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '批量识别', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default
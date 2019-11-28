"""
具体的一个交路的编辑界面。
由circuitWidget管理其实例，只在程序初始化时构建一个实例，其他时候只setData。模式类似currentWidget，但用对话框形式。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .data.circuit import Circuit,CircuitNode
from .pyETRCExceptions import *
from .data.graph import Graph,Train
from .circuitDiagramWidget import CircuitDiagramWidget
from .circuitwidgets import *
from .dialogAdapter import DialogAdapter

class CircuitDialog(QtWidgets.QDialog):
    CircuitChangeApplied = QtCore.pyqtSignal(Circuit)
    NewCircuitAdded = QtCore.pyqtSignal(Circuit)
    def __init__(self,graph:Graph,parent=None):
        super(CircuitDialog, self).__init__(parent)
        self.graph=graph
        self.toAddTrain=None
        self.circuit=None
        self.isNewCircuit = False  # 状态值，表征当前页面上的数据是否是一个新的Circuit。保证准确。
        self.resize(700,600)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('交路设置')
        vlayout = QtWidgets.QVBoxLayout()

        flayout = QtWidgets.QFormLayout()
        nameEdit = QtWidgets.QLineEdit()
        self.nameEdit = nameEdit
        flayout.addRow('交路名称',nameEdit)
        noteEdit = QtWidgets.QTextEdit()
        noteEdit.setMaximumHeight(100)
        self.noteEdit = noteEdit

        modelEdit = QtWidgets.QLineEdit()
        self.modelEdit = modelEdit
        flayout.addRow('车底型号',modelEdit)

        ownerEdit = QtWidgets.QLineEdit()
        self.ownerEdit = ownerEdit
        flayout.addRow('担当局段',ownerEdit)

        vlayout.addLayout(flayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton('前插')
        btnAddAfter = QtWidgets.QPushButton('后插')
        btnDel = QtWidgets.QPushButton('删除')
        btnUp = QtWidgets.QPushButton('上移')
        btnDown = QtWidgets.QPushButton('下移')
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnAddAfter)
        hlayout.addWidget(btnDel)
        hlayout.addWidget(btnUp)
        hlayout.addWidget(btnDown)

        btnAdd.clicked.connect(self._add_train_before)
        btnAddAfter.clicked.connect(self._add_train_after)
        btnDel.clicked.connect(self._del_train)
        btnUp.clicked.connect(self._move_up)
        btnDown.clicked.connect(self._move_down)

        vlayout.addLayout(hlayout)

        tw = QtWidgets.QTableWidget()
        self.tableWidget = tw
        tw.setColumnCount(7)
        tw.setEditTriggers(tw.NoEditTriggers)
        tw.setHorizontalHeaderLabels(['车次','虚拟','始发站','终到站','交路起点','交路终点','连线'])
        for i,s in enumerate((120,50,100,100,100,100,60)):
            tw.setColumnWidth(i,s)
        vlayout.addWidget(tw)
        vlayout.addWidget(QtWidgets.QLabel('备注或说明'))
        vlayout.addWidget(noteEdit)

        btnOk = QtWidgets.QPushButton("确定(&Y)")
        btnRestore = QtWidgets.QPushButton("还原(&R)")
        btnDiagram = QtWidgets.QPushButton('交路图(&D)')
        btnCancel = QtWidgets.QPushButton("关闭(&C)")
        btnOk.clicked.connect(self._apply)
        btnCancel.clicked.connect(self.close)
        btnRestore.clicked.connect(self._restore)
        btnDiagram.clicked.connect(self._show_diagram)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnRestore)
        hlayout.addWidget(btnDiagram)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)

        self.setLayout(vlayout)

    def setData(self,circuit:Circuit):
        self.circuit=circuit
        if circuit is None:
            circuit=self.circuit=Circuit(self.graph)
            self.isNewCircuit = True
        else:
            self.isNewCircuit = False
        self.tableWidget.setRowCount(circuit.trainCount())
        self.nameEdit.setText(circuit.name())
        self.noteEdit.setText(circuit.note())
        self.ownerEdit.setText(circuit.owner())
        self.modelEdit.setText(circuit.model())
        for row,node in enumerate(circuit.nodes()):
            self.setTableRow(row,node)

    def setTableRow(self,row:int,node:CircuitNode):
        """
        新建一行时，设置基本格式。保证该行存在。
        """
        tw = self.tableWidget
        tw.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])

        item = QtWidgets.QTableWidgetItem(node.checi())
        item.setData(Qt.UserRole,node)
        tw.setItem(row,0,item)

        item = QtWidgets.QTableWidgetItem()
        item.setText('√' if node.isVirtual() else '')
        item.setFlags(item.flags() & (~Qt.ItemIsEditable))
        tw.setItem(row, 1, item)

        item = QtWidgets.QTableWidgetItem()
        if not node.isVirtual():
            item.setText(node.train().sfz)
        else:
            item.setText('-')
        item.setFlags(item.flags()&(~Qt.ItemIsEditable))
        tw.setItem(row,2,item)

        item = QtWidgets.QTableWidgetItem()
        if not node.isVirtual():
            item.setText(node.train().zdz)
        else:
            item.setText('-')
        item.setFlags(item.flags() & (~Qt.ItemIsEditable))
        tw.setItem(row, 3, item)

        item = QtWidgets.QTableWidgetItem()
        item.setText(node.startStation())
        item.setFlags(item.flags() & (~Qt.ItemIsEditable))
        tw.setItem(row, 4, item)

        item = QtWidgets.QTableWidgetItem()
        item.setText(node.endStation())
        item.setFlags(item.flags() & (~Qt.ItemIsEditable))
        tw.setItem(row, 5, item)

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Qt.Checked if node.link else Qt.Unchecked)
        tw.setItem(row,6,item)
        # tw.itemChanged.connect(self._item_changed)

    def addTrainDialog(self,row:int):
        """
        弹出对话框，新增车次。
        """
        addWidget = AddTrainWidget(self.graph,self)
        dialog = DialogAdapter(addWidget,self,closeButton=False)
        self.addDialog = dialog  # 作用仅仅在于关闭

        addWidget.Canceled.connect(lambda:self._add_train_cancel(row))
        addWidget.Applied.connect(lambda node:self._add_train_ok(row,node))

        dialog.exec_()

    def checkTrainAdded(self,train:Train)->bool:
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row,0).data(Qt.UserRole).train() is train:
                return True
        return False

    def _add_train_ok(self,row:int,node:CircuitNode):
        """
        确定信息，关闭对话框，将数据直接加入到表格中。
        precondition: 车次已经符合要求，不做检查。
        """

        self.addDialog.close()
        self.tableWidget.insertRow(row)
        self.tableWidget.setCurrentCell(row,0)
        self.setTableRow(row,node)
        self.toAddTrain = None

    def _add_train_cancel(self,row:int):
        self.tableWidget.removeRow(row)
        self.addDialog.close()

    # slots for self--circuitDialog
    def _add_train_before(self):
        """
        插入行的动作在ok里再进行。
        """
        row = self.tableWidget.currentRow()
        if row < 0:
            return
        self.addTrainDialog(row)

    def _add_train_after(self):
        row = self.tableWidget.currentRow()
        self.addTrainDialog(row+1)

    def _del_train(self):
        self.tableWidget.removeRow(self.tableWidget.currentRow())

    def _move_up(self):
        tw = self.tableWidget
        row = tw.currentRow()
        if row <=0:
            return
        node = tw.item(row,0).data(Qt.UserRole)
        tw.removeRow(row)
        tw.insertRow(row-1)
        self.setTableRow(row-1,node)

    def _move_down(self):
        tw = self.tableWidget
        row = tw.currentRow()
        if row >= tw.rowCount()-1:
            return
        node = tw.item(row, 0).data(Qt.UserRole)
        tw.removeRow(row)
        tw.insertRow(row + 1)
        self.setTableRow(row + 1, node)

    def _restore(self):
        self.setData(self.circuit)

    def _show_diagram(self):
        try:
            dialog = CircuitDiagramWidget(self.graph,self.circuit,self)
        except StartOrEndNotMatchedError as e:
            QtWidgets.QMessageBox.warning(self,'错误','交路不符合绘图要求。'
                                '铺画交路图要求交路中每个车次的始发终到站与时刻表首末站一致。\n'+
                                          str(e))
            return
        dialog.exec_()

    def _apply(self):
        """
        提交更改。原则上信息都可以直接提交，不会有问题。故不作考虑。
        先清除原有信息在车次中的映射再重新建立。检查是否重名、名称是否为空。
        """
        name = self.nameEdit.text()
        if not name:
            QtWidgets.QMessageBox.warning(self,'错误','交路名称不能为空！')
            return
        if self.graph.circuitNameExisted(name,self.circuit):
            QtWidgets.QMessageBox.warning(self,'错误',f'交路名称{name}已存在，不能重复添加！')
            return
        if self.circuit is None:
            self.isNewCircuit = True
            self.circuit = Circuit(self.graph)
        self.circuit.setName(name)
        self.circuit.setNote(self.noteEdit.toPlainText())
        self.circuit.setModel(self.modelEdit.text())
        self.circuit.setOwner(self.ownerEdit.text())

        for node in self.circuit.nodes():
            if not node.isVirtual():
                node.train().setCarriageCircuit(None)
        self.circuit.clear()

        tw = self.tableWidget
        for row in range(tw.rowCount()):
            node = tw.item(row,0).data(Qt.UserRole)
            if not isinstance(node,CircuitNode):
                print("CircuitDialog::Apply: Unexpected node")
                continue
            self.circuit.addNode(node)
            if not node.isVirtual():
                node.train().setCarriageCircuit(self.circuit)
        if self.isNewCircuit:
            self.NewCircuitAdded.emit(self.circuit)
            self.graph.addCircuit(self.circuit)
        else:
            self.CircuitChangeApplied.emit(self.circuit)
        self.close()




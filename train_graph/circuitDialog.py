"""
具体的一个交路的编辑界面。
由circuitWidget管理其实例，只在程序初始化时构建一个实例，其他时候只setData。模式类似currentWidget，但用对话框形式。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .circuit import Circuit,CircuitNode
from .pyETRCExceptions import *
from .graph import Graph
from .train import Train

class CircuitDialog(QtWidgets.QDialog):
    CircuitChangeApplied = QtCore.pyqtSignal(Circuit)
    NewCircuitAdded = QtCore.pyqtSignal(Circuit)
    def __init__(self,graph:Graph,parent=None):
        super(CircuitDialog, self).__init__(parent)
        self.graph=graph
        self.toAddTrain=None
        self.circuit=None
        self.isNewCircuit = False  # 状态值，表征当前页面上的数据是否是一个新的Circuit。保证准确。
        self.resize(600,600)
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
        tw.setColumnCount(6)
        tw.setEditTriggers(tw.NoEditTriggers)
        tw.setHorizontalHeaderLabels(['车次','始发站','终到站','交路起点','交路终点','连线'])
        for i,s in enumerate((120,100,100,100,100,60)):
            tw.setColumnWidth(i,s)
        vlayout.addWidget(tw)
        vlayout.addWidget(QtWidgets.QLabel('备注或说明'))
        vlayout.addWidget(noteEdit)

        btnOk = QtWidgets.QPushButton("确定")
        btnRestore = QtWidgets.QPushButton("还原")
        btnCancel = QtWidgets.QPushButton("关闭")
        btnOk.clicked.connect(self._apply)
        btnCancel.clicked.connect(self.close)
        btnRestore.clicked.connect(self._restore)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnRestore)
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
        item.setText(node.train().sfz)
        item.setFlags(item.flags()&(~Qt.ItemIsEditable))
        tw.setItem(row,1,item)

        item = QtWidgets.QTableWidgetItem()
        item.setText(node.train().zdz)
        item.setFlags(item.flags() & (~Qt.ItemIsEditable))
        tw.setItem(row, 2, item)

        item = QtWidgets.QTableWidgetItem()
        item.setText(node.startStation())
        item.setFlags(item.flags() & (~Qt.ItemIsEditable))
        tw.setItem(row, 3, item)

        item = QtWidgets.QTableWidgetItem()
        item.setText(node.endStation())
        item.setFlags(item.flags() & (~Qt.ItemIsEditable))
        tw.setItem(row, 4, item)

        item = QtWidgets.QTableWidgetItem()
        item.setCheckState(Qt.Checked if node.link else Qt.Unchecked)
        tw.setItem(row,5,item)
        # tw.itemChanged.connect(self._item_changed)

    def addTrainDialog(self,row:int):
        """
        弹出对话框，新增车次。
        """
        dialog = QtWidgets.QDialog(self)
        self.addDialog = dialog
        dialog.setWindowTitle('添加车次')
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        label = QtWidgets.QLabel('请先输入车次，然后在右侧的下拉列表中选择准确的车次。可按Tab键切换。'
                                 '下拉列表中选择的车次才是有效的。')
        label.setWordWrap(True)
        vlayout.addWidget(label)

        comboCheci = QtWidgets.QComboBox()
        self.comboCheci = comboCheci
        checiEdit = QtWidgets.QLineEdit()
        # checiEdit.editingFinished.connect(lambda:self.checiEdit.setFocus())
        checiEdit.editingFinished.connect(self._add_train_checi_line_changed)
        self.checiEdit = checiEdit
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(checiEdit)
        hlayout.addWidget(comboCheci)
        flayout.addRow('车次',hlayout)

        sfzEdit = QtWidgets.QLineEdit()
        self.sfzEdit = sfzEdit
        sfzEdit.setFocusPolicy(Qt.NoFocus)
        flayout.addRow('始发站',sfzEdit)

        self.zdzEdit = QtWidgets.QLineEdit()
        zdzEdit = self.zdzEdit
        zdzEdit.setFocusPolicy(Qt.NoFocus)
        flayout.addRow('终到站',zdzEdit)

        startEdit = QtWidgets.QLineEdit()
        startEdit.setFocusPolicy(Qt.NoFocus)
        self.startEdit = startEdit
        flayout.addRow('交路起点',startEdit)

        endEdit = QtWidgets.QLineEdit()
        endEdit.setFocusPolicy(Qt.NoFocus)
        self.endEdit = endEdit
        flayout.addRow('交路终点',endEdit)

        checkLink = QtWidgets.QCheckBox()
        self.checkLink = checkLink
        checkLink.setChecked(True)
        flayout.addRow('开始处连线',checkLink)

        vlayout.addLayout(flayout)
        label = QtWidgets.QLabel("说明：对交路的第一个车次，“开始处连线”的选项无效，可任意设置。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton('确定')
        btnCancel = QtWidgets.QPushButton('取消')
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        btnCancel.clicked.connect(lambda:self._add_train_cancel(row))
        btnOk.clicked.connect(lambda:self._add_train_ok(row))
        vlayout.addLayout(hlayout)
        dialog.setLayout(vlayout)
        comboCheci.currentTextChanged.connect(self._add_train_checi_changed)

        dialog.exec_()

    # slots for add-dialog
    def _add_train_checi_line_changed(self):
        """
        由lineEdit触发。设置combo中的车次。
        """
        checi = self.checiEdit.text()
        if not checi:
            return
        self.comboCheci.setFocus()
        trains = self.graph.multiSearch(checi)
        self.comboCheci.clear()
        self.comboCheci.addItems(map(lambda x:x.fullCheci(),trains))

    def _add_train_checi_changed(self,checi:str):
        """
        由combo触发。
        """
        train = self.graph.trainFromCheci(checi,full_only=True)
        if train is None:
            self.sfzEdit.setText('')
            self.zdzEdit.setText('')
            self.startEdit.setText('')
            self.endEdit.setText('')
            self.toAddTrain = None
            return
        elif train.carriageCircuit() is not None and train.carriageCircuit() is not self.circuit:
            QtWidgets.QMessageBox.warning(self.addDialog,'警告',f'车次{train.fullCheci()}已有交路信息:{train.carriageCircuit()}。')
            return
        # 检查车次是否在本交路表中已经出现过
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row,0).data(Qt.UserRole).train() is train:
                QtWidgets.QMessageBox.warning(self.addDialog,'错误',f'车次{train.fullCheci()}已在本交路中'
                                                                  f'出现过，不能重复添加！')
                return
        self.sfzEdit.setText(train.sfz)
        self.zdzEdit.setText(train.zdz)
        self.startEdit.setText(train.localFirst(self.graph))
        self.endEdit.setText(train.localLast(self.graph))
        self.toAddTrain = train

    def _add_train_ok(self,row:int):
        """
        确定信息，关闭对话框，将数据直接加入到表格中。
        precondition: 车次已经符合要求，不做检查。
        """
        if self.toAddTrain is None:
            QtWidgets.QMessageBox.warning(self.addDialog,'错误','请先选择有效的车次！')
            return
        node = CircuitNode(self.graph,train=self.toAddTrain,start=self.startEdit.text(),
                           end=self.endEdit.text(),link=self.checkLink.isChecked())
        self.addDialog.close()
        self.tableWidget.insertRow(row)
        self.setTableRow(row,node)

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

    def _apply(self):
        """
        提交更改。原则上信息都可以直接提交，不会有问题。故不作考虑。
        先清除原有信息在车次中的映射再重新建立。检查是否重名、名称是否为空。
        """
        name = self.nameEdit.text()
        if not name:
            QtWidgets.QMessageBox.warning(self,'错误','交路名称不能为空！')
            return
        for circuit in self.graph.circuits():
            if circuit.name() == name and circuit is not self.circuit:
                QtWidgets.QMessageBox.warning(self,'错误',f'交路名称{name}已存在，不能重复添加！')
                return
        if self.circuit is None:
            self.isNewCircuit = True
            self.circuit = Circuit(self.graph)
        self.circuit.setName(name)
        self.circuit.setNote(self.noteEdit.toPlainText())

        for node in self.circuit.nodes():
            node.train().setCarriageCircuit(None)
        self.circuit.clear()

        tw = self.tableWidget
        for row in range(tw.rowCount()):
            node = tw.item(row,0).data(Qt.UserRole)
            if not isinstance(node,CircuitNode):
                print("CircuitDialog::Apply: Unexpected node")
                continue
            self.circuit.addNode(node)
            node.train().setCarriageCircuit(self.circuit)
        if self.isNewCircuit:
            self.NewCircuitAdded.emit(self.circuit)
            self.graph.addCircuit(self.circuit)
        else:
            self.CircuitChangeApplied.emit(self.circuit)
        self.close()




"""
具体的一个交路的编辑界面。
由circuitWidget管理其实例，只在程序初始化时构建一个实例，其他时候只setData。模式类似currentWidget，但用对话框形式。
todo 2019年6月1日 18:59:21
apply时要先清除原有信息在车次中的映射再重新建立。检查是否重名、名称是否为空。
注意特别处理同一个交路中可能的车次重复问题。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .circuit import Circuit,CircuitNode
from .pyETRCExceptions import *
from .graph import Graph
from .train import Train

class CircuitDialog(QtWidgets.QDialog):
    def __init__(self,graph:Graph,parent=None):
        super(CircuitDialog, self).__init__(parent)
        self.graph=graph
        self.toAddTrain=None
        self.circuit=None
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
        self.tableWidget.setRowCount(circuit.trainCount())
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

        comboCheci = QtWidgets.QComboBox()
        comboCheci.addItems(map(lambda x:x.fullCheci(),self.graph.trains()))
        comboCheci.setEditable(True)
        comboCheci.setCurrentText("")
        flayout.addRow('车次',comboCheci)

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
    def _add_train_checi_changed(self,checi:str):
        train = self.graph.trainFromCheci(checi,full_only=True)
        if train is None:
            self.sfzEdit.setText('')
            self.zdzEdit.setText('')
            self.startEdit.setText('')
            self.endEdit.setText('')
            self.toAddTrain = None
        elif train.carriageCircuit() is not None and train.carriageCircuit() is not self.circuit:
            QtWidgets.QMessageBox.warning(self.addDialog,'警告',f'车次{train.fullCheci()}已有交路信息:{train.carriageCircuit()}。')
            return
        else:
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
        pass



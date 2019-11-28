"""
2019.11.28新增
添加实体车次。从CircuitDialog中抽离出来。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from ..data import *

class AddRealTrain(QtWidgets.QWidget):
    Canceled = QtCore.pyqtSignal()
    Applied = QtCore.pyqtSignal(CircuitNode)
    def __init__(self,graph:Graph,circuitDialog,parent=None):
        super(AddRealTrain, self).__init__(parent)
        self.graph=graph
        self.circuitDialog = circuitDialog
        self.initUI()

    def initUI(self):
        self.setWindowTitle('添加实体车次')
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
        flayout.addRow('车次', hlayout)

        sfzEdit = QtWidgets.QLineEdit()
        self.sfzEdit = sfzEdit
        sfzEdit.setFocusPolicy(Qt.NoFocus)
        flayout.addRow('始发站', sfzEdit)

        self.zdzEdit = QtWidgets.QLineEdit()
        zdzEdit = self.zdzEdit
        zdzEdit.setFocusPolicy(Qt.NoFocus)
        flayout.addRow('终到站', zdzEdit)

        startEdit = QtWidgets.QLineEdit()
        startEdit.setFocusPolicy(Qt.NoFocus)
        self.startEdit = startEdit
        flayout.addRow('交路起点', startEdit)

        endEdit = QtWidgets.QLineEdit()
        endEdit.setFocusPolicy(Qt.NoFocus)
        self.endEdit = endEdit
        flayout.addRow('交路终点', endEdit)

        checkLink = QtWidgets.QCheckBox()
        self.checkLink = checkLink
        checkLink.setChecked(True)
        flayout.addRow('开始处连线', checkLink)

        vlayout.addLayout(flayout)
        label = QtWidgets.QLabel("说明：对交路的第一个车次，“开始处连线”的选项无效，可任意设置。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton('确定')
        btnCancel = QtWidgets.QPushButton('取消')
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        btnCancel.clicked.connect(self.Canceled.emit)
        btnOk.clicked.connect(self._ok_clicked)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)
        comboCheci.currentTextChanged.connect(self._add_train_checi_changed)

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
        if self.comboCheci.count() > 1:
            self.comboCheci.showPopup()

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
            QtWidgets.QMessageBox.warning(self,'警告',f'车次{train.fullCheci()}已有交路信息:{train.carriageCircuit()}。')
            return
        # 检查车次是否在本交路表中已经出现过
        if self.circuitDialog.checkTrainAdded(train):
            QtWidgets.QMessageBox.warning(self.addDialog, '错误', f'车次{train.fullCheci()}已在本交路中'
                                                                f'出现过，不能重复添加！')
            return
        self.sfzEdit.setText(train.sfz)
        self.zdzEdit.setText(train.zdz)
        self.startEdit.setText(train.localFirst(self.graph))
        self.endEdit.setText(train.localLast(self.graph))
        self.toAddTrain = train

    def _ok_clicked(self):
        if self.toAddTrain is None:
            QtWidgets.QMessageBox.warning(self,'错误','请先选择有效的车次!')
            return
        node = CircuitNode(self.graph, train=self.toAddTrain, start=self.startEdit.text(),
                           end=self.endEdit.text(), link=self.checkLink.isChecked())
        self.Applied.emit(node)
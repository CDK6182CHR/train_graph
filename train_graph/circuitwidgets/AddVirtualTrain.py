"""
2019.11.28新增。
添加虚拟车次。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from ..data import *

class AddVirtualTrain(QtWidgets.QWidget):
    Canceled = QtCore.pyqtSignal()
    Applied = QtCore.pyqtSignal(CircuitNode)
    def __init__(self,graph:Graph,circuitWidget,parent=None):
        super(AddVirtualTrain, self).__init__(parent)
        self.graph = graph
        self.circuitWidget = circuitWidget
        self.initUI()

    def initUI(self):
        self.setWindowTitle("添加虚拟车次")
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("虚拟车次一般用于不在本线的车次，为了保持交路完整性，将它记录在交路里面。"
                                 "请输入完整车次即可。\n请注意添加虚拟车次不会经过车次重复性检查。")
        label.setWordWrap(True)
        vlayout.addWidget(label)
        flayout = QtWidgets.QFormLayout()
        checiEdit = QtWidgets.QLineEdit()
        self.checiEdit = checiEdit
        flayout.addRow('车次',checiEdit)

        startEdit = QtWidgets.QLineEdit()
        self.startEdit = startEdit
        flayout.addRow('交路起点',startEdit)

        endEdit = QtWidgets.QLineEdit()
        self.endEdit = endEdit
        flayout.addRow('交路终点',endEdit)

        checkLink = QtWidgets.QCheckBox('开始处连线')
        self.checkLink = checkLink
        flayout.addRow('连线',checkLink)
        vlayout.addLayout(flayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton('确定')
        btnOk.clicked.connect(self._ok_clicked)
        hlayout.addWidget(btnOk)
        btnCancel = QtWidgets.QPushButton('取消')
        btnCancel.clicked.connect(self.Canceled.emit)
        hlayout.addWidget(btnCancel)

        vlayout.addLayout(hlayout)

        self.setLayout(vlayout)

    # slots
    def _ok_clicked(self):
        if not self.checiEdit.text():
            QtWidgets.QMessageBox.warning(self,'错误','车次不能为空！')
            return
        node = CircuitNode(self.graph,checi=self.checiEdit.text(),link=self.checkLink.isChecked(),
                           start=self.startEdit.text(),end=self.endEdit.text(),
                           virtual=True)
        self.Applied.emit(node)

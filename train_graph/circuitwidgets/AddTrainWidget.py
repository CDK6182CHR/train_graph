"""
2019.11.28新增
添加车次窗口。
并改为用TabWidget实现。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .AddRealTrain import AddRealTrain
from .AddVirtualTrain import AddVirtualTrain
from ..data import *

class AddTrainWidget(QtWidgets.QTabWidget):
    Applied = QtCore.pyqtSignal(CircuitNode)
    Canceled = QtCore.pyqtSignal()
    def __init__(self,graph:Graph,circuitDialog,parent=None):
        super(AddTrainWidget, self).__init__(parent)
        self.graph=graph
        self.circuitDialog = circuitDialog
        self.realWidget = AddRealTrain(graph,circuitDialog,self)
        self.virtualWidget = AddVirtualTrain(graph,circuitDialog,self)
        self.realWidget.Applied.connect(self.Applied.emit)
        self.realWidget.Canceled.connect(self.Canceled.emit)
        self.virtualWidget.Applied.connect(self.Applied.emit)
        self.virtualWidget.Canceled.connect(self.Canceled.emit)  # 只负责转发消息
        self.initUI()

    def initUI(self):
        self.setWindowTitle('添加车次')
        self.addTab(self.realWidget,'实体')
        self.addTab(self.virtualWidget,'虚拟')
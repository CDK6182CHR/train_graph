"""
比较两车次时刻表信息。
"""
from .data import *
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt

class TrainDiffDialog(QtWidgets.QDialog):
    def __init__(self,train1:Train,train2:Train,graph:Graph,parent=None):
        super(TrainDiffDialog, self).__init__(parent)
        self.train1 = train1
        self.train2 = train2
        self.graph = graph

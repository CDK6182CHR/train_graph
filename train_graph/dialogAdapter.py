"""
接受一个QWidget，将其包装成QDialog的工具类
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt

class DialogAdapter(QtWidgets.QDialog):
    def __init__(self,widget:QtWidgets.QWidget,parent=None,closeButton=True):
        super(DialogAdapter, self).__init__(parent)
        self.widget = widget
        self.setWindowTitle(self.widget.windowTitle())
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self.widget)
        if closeButton:
            btnClose = QtWidgets.QPushButton('关闭')
            btnClose.clicked.connect(self.close)
            vlayout.addWidget(btnClose)
        self.setLayout(vlayout)
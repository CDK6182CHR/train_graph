from .data import *
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt

class GraphDiffDialog(QtWidgets.QDialog):
    def __init__(self,graph:Graph,anGraph:Graph,parent=None):
        super(GraphDiffDialog, self).__init__(parent)
        self.graph = graph
        self.anGraph = anGraph
        self.initUI()

    def initUI(self):
        self.setWindowTitle('运行图比较')
        vlayout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        filenameEdit = QtWidgets.QLineEdit()
        filenameEdit.setFocusPolicy(Qt.NoFocus)
        self.filenameEdit = filenameEdit
        hlayout.addWidget(filenameEdit)
        btnOpen = QtWidgets.QPushButton('打开文件')
        btnOpen.clicked.connect(self._open_file)
        hlayout.addWidget(btnOpen)
        vlayout.addLayout(hlayout)

        checkLocalOnly = QtWidgets.QCheckBox('仅对比经过本线的车次')
        self.checkLocalOnly = checkLocalOnly
        vlayout.addWidget(checkLocalOnly)
        checkLocalOnly.toggled.connect(self.setData)

        tw = QtWidgets.QTableWidget
        self.tableWidget = tw
        tw.setColumnCount(6)
        tw.setHorizontalHeaderLabels(('车次','始发1','终到1','修改数','始发2','终到2'))
        for i,s in enumerate((130,120,120,90,120,120)):
            tw.setColumnWidth(i,s)
        tw.setEditTriggers(tw.NoEditTriggers)
        vlayout.addWidget(tw)

        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(self.close)
        vlayout.addWidget(btnClose)

        self.setLayout(vlayout)

    def setData(self):
        pass

    # slots
    def _open_file(self):
        pass


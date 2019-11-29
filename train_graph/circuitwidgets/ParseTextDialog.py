"""
在单交路内解析车次串。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from ..data import *
from ..dialogAdapter import DialogAdapter


class ParseTextDialog(QtWidgets.QDialog):
    def __init__(self,graph:Graph,circuit:Circuit,circuitDialog,parent=None):
        super(ParseTextDialog, self).__init__(parent)
        self.graph = graph
        self.circuit = circuit
        self.circuitDialog = circuitDialog
        self.results = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle('解析车次列文本')
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(f'此功能允许输入一列车次套跑交路，可指定分隔符，如果缺省则按系统默认分隔符处理。分隔符两侧空白字符将被清除。请输入完整车次。整个车次列只能有一种分隔符，不能混用。系统内置分隔符有：'+','.join(Circuit.Spliters))
        label.setWordWrap(True)
        vlayout.addWidget(label)

        flayout = QtWidgets.QFormLayout()
        editSpliter = QtWidgets.QLineEdit()
        self.editSpliter = editSpliter
        flayout.addRow('分隔符',editSpliter)

        checkFullOnly = QtWidgets.QCheckBox('仅识别完整车次')
        flayout.addRow('仅全车次',checkFullOnly)
        self.checkFullOnly = checkFullOnly

        vlayout.addLayout(flayout)

        vlayout.addWidget(QtWidgets.QLabel('套跑交路：'))
        textEdit = QtWidgets.QTextEdit()
        self.textEdit = textEdit
        vlayout.addWidget(textEdit)

        hlayout = QtWidgets.QHBoxLayout()
        btnApply = QtWidgets.QPushButton('解析')
        btnApply.clicked.connect(self._apply)
        hlayout.addWidget(btnApply)
        btnCencel = QtWidgets.QPushButton('取消')
        btnCencel.clicked.connect(self.close)
        hlayout.addWidget(btnCencel)
        vlayout.addLayout(hlayout)

        vlayout.addWidget(QtWidgets.QLabel('解析结果：'))
        resultBrowser = QtWidgets.QTextEdit()
        self.resultBrowser = resultBrowser
        vlayout.addWidget(resultBrowser)
        self.setLayout(vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnDetail = QtWidgets.QPushButton('详细信息')
        btnDetail.clicked.connect(self._detail)
        hlayout.addWidget(btnDetail)
        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(self.close)
        hlayout.addWidget(btnClose)
        vlayout.addLayout(hlayout)

    # slots
    def _apply(self):
        self.resultBrowser.clear()
        text = self.textEdit.toPlainText()
        spliter = self.editSpliter.text()
        results = self.circuit.parseText(text,spliter,self.checkFullOnly.isChecked())
        self.results = results

        self.resultBrowser.setPlainText(f'解析后交路：{self.circuit.orderStr()}')
        self.circuitDialog.setData(self.circuit)

    def _detail(self):
        tb = QtWidgets.QTextBrowser()
        tb.setWindowTitle('解析详细信息')
        tb.setPlainText('\n'.join(self.results))
        dialog = DialogAdapter(tb,self)
        dialog.resize(500,500)
        dialog.exec_()



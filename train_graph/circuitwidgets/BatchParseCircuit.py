"""
批量解析交路。一行一个
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from ..data import *
from ..dialogAdapter import DialogAdapter


class BatchParseCircuit(QtWidgets.QDialog):
    def __init__(self,graph:Graph,circuitWidget,parent=None):
        super(BatchParseCircuit, self).__init__(parent)
        self.graph = graph
        self.results = []
        self.circuitWidget = circuitWidget
        self.initUI()

    def initUI(self):
        self.setWindowTitle('批量解析')
        hlayout = QtWidgets.QHBoxLayout()
        textEdit = QtWidgets.QTextEdit()
        self.textEdit = textEdit
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('此功能支持批量解析套跑车次字符串。每行一个交路信息，交路的第一个车次将被用于交路名。可手工指定分隔符，或者用系统默认分隔符之一：'+','.join(Circuit.Spliters)+', 但注意只能用一种分隔符，不可以混用。')
        label.setWordWrap(True)
        vlayout.addWidget(label)

        flayout = QtWidgets.QFormLayout()
        spliterEdit = QtWidgets.QLineEdit()
        self.spliterEdit = spliterEdit
        flayout.addRow('分隔符',spliterEdit)
        vlayout.addLayout(flayout)

        check = QtWidgets.QCheckBox('保留纯虚交路')
        flayout.addRow('筛选',check)
        self.checkAllVirtual = check

        check = QtWidgets.QCheckBox('仅识别全车次')
        flayout.addRow('仅全车次',check)
        self.checkFullOnly = check

        vlayout.addWidget(textEdit)

        hlayout.addLayout(vlayout)

        vlayout = QtWidgets.QVBoxLayout()
        btnOk = QtWidgets.QPushButton('解析')
        btnDetail = QtWidgets.QPushButton('信息')
        btnClose = QtWidgets.QPushButton('关闭')
        vlayout.addWidget(btnOk)
        vlayout.addWidget(btnDetail)
        vlayout.addWidget(btnClose)
        hlayout.addLayout(vlayout)
        btnOk.clicked.connect(self._apply)
        btnClose.clicked.connect(self.close)
        btnDetail.clicked.connect(self._detail)

        tw = QtWidgets.QTableWidget()
        self.tableWidget = tw
        tw.setColumnCount(3)
        tw.setHorizontalHeaderLabels(('实','虚','交路'))
        for i,s in enumerate((40,40,400)):
            tw.setColumnWidth(i,s)
        hlayout.addWidget(tw)
        tw.setEditTriggers(tw.NoEditTriggers)
        self.setLayout(hlayout)

    # slots
    def _apply(self):
        spliter = self.spliterEdit.text()
        text = self.textEdit.toPlainText()
        self.results.clear()
        TWI = QtWidgets.QTableWidgetItem

        cache_circuits = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue  # 拒绝空行
            circuit = Circuit(self.graph)
            res = circuit.parseText(line,spliter)

            if self.checkAllVirtual.isChecked() or circuit.realCount():
                # 接受这个交路
                if circuit.trainCount():
                    first = circuit.firstCheci()
                else:
                    first = '空交路'
                name = first
                i = 0
                # 得到一个确保不重复的交路名
                while self.graph.circuitNameExisted(name,self.checkFullOnly.isChecked()):
                    i += 1
                    name = f"{first}-{i}"
                circuit.setName(name)
                self.results.extend(res)
                cache_circuits.append(circuit)
                self.graph.addCircuit(circuit)

        # 修改表格
        tw:QtWidgets.QTableWidget = self.tableWidget
        tw.setRowCount(len(cache_circuits))
        for row,circuit in enumerate(cache_circuits):
            tw.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])

            tw.setItem(row,0,TWI(str(circuit.realCount())))
            tw.setItem(row,1,TWI(str(circuit.virtualCount())))
            item = TWI(circuit.orderStr())
            item.setToolTip(circuit.orderStr())
            tw.setItem(row,2,item)

        self.circuitWidget.setData()

    def _detail(self):
        tb = QtWidgets.QTextBrowser()
        tb.setText('\n'.join(self.results))
        tb.setWindowTitle('解析详情')
        dialog = DialogAdapter(tb,self)
        dialog.resize(500,500)
        dialog.exec_()
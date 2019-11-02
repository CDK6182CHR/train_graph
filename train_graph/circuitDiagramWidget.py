"""
2019.07.07新增
交路图对话框，包含大小调整和算法调整。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .data.graph import Graph,CircuitNode,Circuit
from .pyETRCExceptions import *
from .circuitDiagram import CircuitDiagram

class CircuitDiagramWidget(QtWidgets.QDialog):
    def __init__(self,graph:Graph,circuit:Circuit,parent=None):
        super(CircuitDiagramWidget, self).__init__(parent)
        self.graph = graph
        self.circuit = circuit
        self.diagram = CircuitDiagram(self.graph,self.circuit)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('交路示意图')
        self.resize(1300,870)
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        label = QtWidgets.QLabel("说明：若勾选“扫描整个时刻表”，则系统遍历时刻表中的每一个站，当下一时刻"
                                 "在前一时刻之前时，认为跨日，此情况下要求整个时刻表不能有错。"
                                 "若不勾选，则仅比较最后时刻和最前时刻，当后者在前者之前时认为跨日。"
                                 "此情况下仅在车次跨最多一日时才能正确处理。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        checkTimetable = QtWidgets.QCheckBox('扫描整个时刻表')
        self.checkTimetable = checkTimetable
        checkTimetable.toggled.connect(self.diagram.setMultiDayByTimetable)
        flayout.addRow('跨日算法',checkTimetable)

        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setMaximumWidth(400)
        slider.setRange(100,2000)
        flayout.addRow('水平缩放',slider)
        slider.setValue(self.diagram.sizes["dayWidth"])
        slider.valueChanged.connect(self.diagram.setDayWidth)

        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setMaximumWidth(400)
        slider.setRange(200,800)
        flayout.addRow('垂直缩放',slider)
        slider.setValue(self.diagram.sizes["height"])
        slider.valueChanged.connect(self.diagram.setHeight)

        btnOutPNG = QtWidgets.QPushButton('PNG图片')
        btnOutPDF = QtWidgets.QPushButton('PDF文档')
        btnOutPDF.setMaximumWidth(180)
        btnOutPNG.setMaximumWidth(180)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOutPNG)
        hlayout.addWidget(btnOutPDF)
        flayout.addRow('导出为',hlayout)
        btnOutPDF.clicked.connect(self._out_pdf)
        btnOutPNG.clicked.connect(self._out_png)

        vlayout.addLayout(flayout)
        vlayout.addWidget(self.diagram)

        self.setLayout(vlayout)

    def _out_pdf(self):
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
                                                             caption='导出PDF交路图',
                                                             directory=self.circuit.name(),
                                                             filter="PDF图像(*.pdf)")
        if not filename or not ok:
            return
        if self.diagram.outVector(filename):
            self._dout("导出PDF成功！")
        else:
            self._derr("导出PDF交路图失败，可能由于文件冲突，")

    def _out_png(self):
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
                                                             caption='导出PNG交路图',
                                                             directory=self.circuit.name(),
                                                             filter="可移植网络图形(*.PNG)")
        if not filename or not ok:
            return
        if self.diagram.outPixel(filename):
            self._dout("导出PNG交路图成功！")
        else:
            self._derr("导出PNG交路图失败，可能由于文件冲突。")

    def _derr(self, note: str):
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

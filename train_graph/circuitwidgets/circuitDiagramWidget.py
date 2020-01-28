"""
2019.07.07新增
交路图对话框，包含大小调整和算法调整。
"""
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from ..data.graph import Graph, Circuit
from .circuitDiagram import CircuitDiagram
from ..utility import PEControlledTable

class CircuitDiagramWidget(QtWidgets.QDialog):
    def __init__(self,graph:Graph,circuit:Circuit,parent=None):
        super(CircuitDiagramWidget, self).__init__(parent)
        self.graph = graph
        self.circuit = circuit
        self.diagram = CircuitDiagram(self.graph,self.circuit)
        self.diagram.DiagramRepainted.connect(self._updateTable)
        self.initUI()
        self._updateTable()

    def initUI(self):
        self.setWindowTitle('交路示意图')
        self.resize(1300,870)

        phlayout = QtWidgets.QHBoxLayout()
        vlayout = QtWidgets.QVBoxLayout()
        # 2020.01.27新增显示站表部分

        class T(PEControlledTable):
            def insertRow(self, p_int):
                super(T, self).insertRow(p_int)
                spin = QtWidgets.QSpinBox()
                spin.setRange(0,3000)
                spin.setSingleStep(10)
                self.setCellWidget(p_int,1,spin)
            # 临时方案
            def down(self):
                row = self._tw.currentRow()
                super(T, self).down()
                if 0<=row<self.rowCount()-1:
                    y = self._tw.cellWidget(row,1).value()
                    y1 = self._tw.cellWidget(row+1,1).value()
                    self._tw.cellWidget(row,1).setValue(y1)
                    self._tw.cellWidget(row+1,1).setValue(y)

            def up(self):
                row = self._tw.currentRow()
                super(T, self).up()
                if 0<row<=self.rowCount()-1:
                    y = self._tw.cellWidget(row,1).value()
                    y1 = self._tw.cellWidget(row-1,1).value()
                    self._tw.cellWidget(row,1).setValue(y1)
                    self._tw.cellWidget(row-1,1).setValue(y)

        tw:QtWidgets.QTableWidget = T()
        self.tableWidget = tw
        tw.setColumnCount(2)
        tw.setHorizontalHeaderLabels(['站名','相对位置'])
        tw.setEditTriggers(tw.CurrentChanged)
        for i,s in enumerate((180,80)):
            tw.setColumnWidth(i,s)
        vlayout.addWidget(tw)

        btn = QtWidgets.QPushButton('重新铺画')
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btn)
        btn.clicked.connect(self._repaint)
        btnAuto = QtWidgets.QPushButton('自动铺画')
        hlayout.addWidget(btnAuto)
        btnAuto.clicked.connect(self._auto)
        vlayout.addLayout(hlayout)
        phlayout.addLayout(vlayout)

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

        phlayout.addLayout(vlayout)
        self.setLayout(phlayout)

    def _repaint(self):
        self.diagram.userDefinedYValues.clear()
        for row in range(self.tableWidget.rowCount()):
            name = self.tableWidget.item(row,0).text()
            y = self.tableWidget.cellWidget(row,1).value()
            self.diagram.userDefinedYValues[name] = y
        self.diagram.initUI()

    def _auto(self):
        self.diagram.userDefinedYValues.clear()
        self.diagram.initUI()

    def _updateTable(self):
        """
        2020.01.27新增，更新车站位置表
        """
        tw = self.tableWidget
        ys_dict = self.diagram.stationYValues
        print(ys_dict)
        tw.setRowCount(len(ys_dict))
        TWI = QtWidgets.QTableWidgetItem
        for (row,(name,y)) in enumerate(sorted(ys_dict.items(),key=lambda x:x[1])):
            tw.setItem(row,0,TWI(name))
            spin = QtWidgets.QSpinBox()
            spin.setRange(0,3000)
            spin.setValue(y)
            spin.setSingleStep(10)
            tw.setCellWidget(row,1,spin)
            tw.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])

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

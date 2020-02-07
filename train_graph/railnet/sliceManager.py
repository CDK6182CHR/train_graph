"""
切片运行图管理。
管理、添加所有导出的临时运行图。注意运行图导出时与原来的数据同步。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from ..data import *
from ..linedb.lineLib import LineLib
from .railnet import RailNet
from ..utility import PEControlledTable
from typing import List
from ..lineWidget import LineWidget


class SliceManager(QtWidgets.QWidget):
    SliceGraphAdded = QtCore.pyqtSignal(Graph,str)  # 运行图，标题
    SliceDeleted = QtCore.pyqtSignal(int)  # 序号。对应graph里那个
    OutputSlice = QtCore.pyqtSignal(int)
    ShowSlice = QtCore.pyqtSignal(int)
    def __init__(self,graphdb:Graph,lineLib:LineLib,parent=None):
        super(SliceManager, self).__init__(parent)
        self.graphdb = graphdb
        self.lineLib = lineLib
        self.net = RailNet()
        self.net.reset()
        self.slices = []  # type:List[Graph]
        self.line = Line()
        self.initUI()
        self.net.loadLineLib(self.lineLib)

    def initUI(self):
        hlayout = QtWidgets.QHBoxLayout()
        vlayout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel("下方显示的是所有已打开的运行图切片。可在右侧增加新的运行图切片。请注意对运行图切片的车次时刻表的修改将作用于数据库，但交路不会。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        chlayout = QtWidgets.QHBoxLayout()
        btn = QtWidgets.QPushButton('删除')
        btn.clicked.connect(self._del)
        chlayout.addWidget(btn)

        btn = QtWidgets.QPushButton('显示')
        btn.clicked.connect(self._show)
        chlayout.addWidget(btn)

        btn = QtWidgets.QPushButton('导出')
        btn.clicked.connect(self._out)
        chlayout.addWidget(btn)
        vlayout.addLayout(chlayout)

        lw = QtWidgets.QListWidget()
        self.sliceListWidget = lw

        ac = QtWidgets.QAction('删除',lw)
        ac.triggered.connect(self._del)
        lw.addAction(ac)
        ac = QtWidgets.QAction('显示',lw)
        ac.triggered.connect(self._show)
        lw.addAction(ac)
        ac = QtWidgets.QAction('导出',lw)
        ac.triggered.connect(self._out)
        lw.addAction(ac)
        lw.setContextMenuPolicy(Qt.ActionsContextMenu)
        vlayout.addWidget(lw)

        hlayout.addLayout(vlayout)
        self.setLayout(hlayout)

        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('请在下表编辑要导出线路的经由，按从上行端到下行端的顺序。系统将在列出的每个站间，选取最短路径，连接成新的pyETRC运行图线路数据。列出的站需要是上下行都经过的站。')
        label.setWordWrap(True)
        vlayout.addWidget(label)

        tw = PEControlledTable()  # type:QtWidgets.QTableWidget
        tw.setColumnCount(1)
        tw.setHorizontalHeaderLabels(['站名'])
        tw.setColumnWidth(0,300)
        tw.setEditTriggers(tw.CurrentChanged)
        self.viaTable = tw
        vlayout.addWidget(tw)
        btn = QtWidgets.QPushButton('预览')
        btn.clicked.connect(self._preview)
        vlayout.addWidget(btn)
        hlayout.addLayout(vlayout)

        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("下方是从经由表生成的预览线路信息。点击“确定”或者“生成切片”都将生成新的运行图切片。请注意在此处对线路信息的修改不会影响线路数据库中的信息。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        w = LineWidget(self.line)
        self.lineWidget = w
        w.lineChangedApplied.connect(self._apply)
        w.initWidget()
        vlayout.addWidget(w)

        btn = QtWidgets.QPushButton('生成切片')
        btn.clicked.connect(self._apply)
        vlayout.addWidget(btn)
        hlayout.addLayout(vlayout)

    def setData(self):
        """
        暂时不知道干啥，先把接口留下
        """
        pass

    def clearAllSlices(self):
        """
        删除所有切片。
        暂不考虑效率问题，借用slot实现。
        """
        lw = self.sliceListWidget
        while lw.count():
            lw.takeItem(0)
            self.SliceDeleted.emit(0)

    # slots
    def _del(self):
        id = self.sliceListWidget.currentRow()
        if 0<=id<=self.sliceListWidget.count():
            self.sliceListWidget.takeItem(id)
            self.SliceDeleted.emit(id)

    def _show(self):
        id = self.sliceListWidget.currentRow()
        if 0 <= id <= self.sliceListWidget.count():
            self.ShowSlice.emit(id)

    def _out(self):
        id = self.sliceListWidget.currentRow()
        if 0 <= id <= self.sliceListWidget.count():
            self.OutputSlice.emit(id)

    def _preview(self):
        via = []
        for r in range(self.viaTable.rowCount()):
            it = self.viaTable.item(r,0)
            if isinstance(it,QtWidgets.QTableWidgetItem):
                via.append(it.text())
        try:
            line = self.net.outLine(via,withRuler=False)  # todo 暂时不导出标尺
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','无效经由：\n'+repr(e))
        else:
            self.line = line
            self.lineWidget.setLine(line)
            self.lineWidget.setData()
            self.currentVia = via   # 当前经由表

    def addNewSlice(self,via:List[str]):
        """
        由经由表添加切片。读取时调用。
        """
        try:
            line = self.net.outLine(via,withRuler=False)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','无效经由：\n'+repr(e))
        else:
            self.line = line
            self.lineWidget.setLine(line)
            self.lineWidget.setData()
            self.currentVia = via   # 当前经由表
            self._apply()

    def _apply(self):
        """
        生成新的切片运行图。此时self.line就是线路。
        """
        if not self.line.stations:
            QtWidgets.QMessageBox.warning(self,'错误','请先生成有效的站表！')
            return
        graph = self.graphdb.subGraph(self.line)
        for c in self.graphdb.circuits():
            graph.addCircuit(c)  # 暴力方法：加入所有交路数据

        lw = self.sliceListWidget
        item = QtWidgets.QListWidgetItem()
        name = self.line.name
        if not name:
            name = f"{graph.firstStation()}-{graph.lastStation()}"
        item.setText(name)
        item.setData(Qt.UserRole, self.currentVia)  # data中保存经由表数据。
        lw.addItem(item)
        self.SliceGraphAdded.emit(graph, name)
        n = lw.count()-1
        self.ShowSlice.emit(n)
        if n == 0:
            txt = "此操作将利用数据库的数据生成区段运行图。运行图将用完整的pyETRC" \
                  "列车运行图主程序展示。请注意，在区段运行图中修改已存在列车时刻，" \
                  "将【会】直接更改数据库中内容；但进行其他更改，例如增删车次，" \
                  "调整线路里程标尺，调整交路等，将【不会】作用于原数据库。" \
                  "即使保存、另存也是如此。\n" \
                  "但若[打开]其他运行图文件，则该窗口与数据库没有关系。" \
                  "但不建议这样操作。\n" \
                  "此提示每当添加第一个区段运行图时弹出。"
            QtWidgets.QMessageBox.information(self,'提示',txt)


    def loadDigraph(self, filename:str):
        self.net.reset()
        try:
            self.net.read(filename)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'读取错误','无法解析文件: \n'+repr(e))

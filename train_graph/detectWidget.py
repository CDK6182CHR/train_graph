"""
按标尺自动推定区间通过时刻。
一个含有起停的跨站区间，扣除起停时分后，区间纯运行时分按标尺【比例】划分，同时给出相对误差供参考。
允许选择推定到本线起点或终点，此区间完全按照所选标尺推断。但若始发/终到站在本线，则不向两端推定。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .train import Train
from .graph import Graph
from .ruler import Ruler

class DetectWidget(QtWidgets.QDialog):
    """
    核心widget是stackedWidget
    """
    okClicked=QtCore.pyqtSignal()
    def __init__(self,mainWindow,parent=None):
        super().__init__(parent)
        self.setParent(parent)
        self.setWindowTitle('推定通过站时刻')
        self.mainWindow=mainWindow
        self.graph: Graph = mainWindow.graph

        self.resize(600,700)

        #是否推定到结尾
        self.toStart=False
        self.toEnd=False
        self.ruler=None

        self.stackedWidget=QtWidgets.QStackedWidget(self)
        self.widget1=QtWidgets.QWidget()
        self.widget2=QtWidgets.QWidget()
        self._initWidget1()
        self._initWidget2()
        self.stackedWidget.addWidget(self.widget1)
        self.stackedWidget.addWidget(self.widget2)

        layout=QtWidgets.QVBoxLayout()
        hlayout=QtWidgets.QHBoxLayout()
        self.btnForward=QtWidgets.QPushButton("上一步")
        self.btnNext=QtWidgets.QPushButton("下一步")
        self.btnCancel=QtWidgets.QPushButton("取消")
        self.btnOk=QtWidgets.QPushButton("确定")
        self.btnNext.clicked.connect(self._next_clicked)
        self.btnForward.clicked.connect(self._forward_clicked)
        self.btnOk.clicked.connect(self._ok_clicked)
        self.btnCancel.clicked.connect(self.close)
        hlayout.addWidget(self.btnCancel)
        hlayout.addWidget(self.btnForward)
        hlayout.addWidget(self.btnNext)
        hlayout.addWidget(self.btnOk)
        layout.addWidget(self.stackedWidget)
        layout.addLayout(hlayout)
        self.setLayout(layout)

        self.stackedWidget.setCurrentIndex(0)
        self.btnForward.setEnabled(False)
        self.btnOk.setEnabled(False)

    def _initWidget1(self):
        vlayout=QtWidgets.QVBoxLayout()
        flayout=QtWidgets.QFormLayout()

        label = QtWidgets.QLabel("按标尺推定未给出时刻的车站通过时刻。可选择是否推定到区间起点和终点。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        btnNote=QtWidgets.QPushButton("逻辑说明")
        btnNote.setMaximumWidth(100)
        btnNote.clicked.connect(self._note_clicked)
        vlayout.addWidget(btnNote)

        rulerCombo=QtWidgets.QComboBox()
        for ruler in self.graph.rulers():
            if self.ruler is None:
                self.ruler=ruler
            rulerCombo.addItem(ruler.name())
        rulerCombo.currentTextChanged.connect(self._ruler_changed)
        rulerCombo.setMaximumWidth(150)
        flayout.addRow("标尺选择",rulerCombo)

        checkStart=QtWidgets.QCheckBox()
        checkStart.toggled.connect(self._to_start_changed)
        flayout.addRow("推定到本线起点",checkStart)

        checkEnd=QtWidgets.QCheckBox()
        checkEnd.toggled.connect(self._to_end_changed)
        flayout.addRow("推定到本线终点",checkEnd)
        vlayout.addLayout(flayout)

        label=QtWidgets.QLabel("请在下表中【点击选择】要推定时刻的车次所在行，按住ctrl或shift可多选。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        tableWidget=QtWidgets.QTableWidget()
        self.chooseTable=tableWidget
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        tableWidget.setSelectionBehavior(tableWidget.SelectRows)
        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)
        tableWidget.setColumnCount(5)
        tableWidget.setHorizontalHeaderLabels(['车次','方向','类型','始发','终到'])
        for i,s in enumerate((120,80,60,90,90)):
            tableWidget.setColumnWidth(i,s)
        for train in self.graph.trains():
            self.addChooseTableRow(train)

        vlayout.addWidget(tableWidget)
        self.widget1.setLayout(vlayout)

    def addChooseTableRow(self,train:Train):
        tableWidget=self.chooseTable
        row=tableWidget.rowCount()
        tableWidget.insertRow(row)
        tableWidget.setRowHeight(row,30)

        item=QtWidgets.QTableWidgetItem(train.fullCheci())
        item.setData(-1,train)
        tableWidget.setItem(row,0,item)

        item=QtWidgets.QTableWidgetItem(train.downStr())
        tableWidget.setItem(row,1,item)

        item=QtWidgets.QTableWidgetItem(train.trainType())
        tableWidget.setItem(row,2,item)

        item=QtWidgets.QTableWidgetItem(train.sfz)
        tableWidget.setItem(row,3,item)

        tableWidget.setItem(row,4,QtWidgets.QTableWidgetItem(train.zdz))


    def _initWidget2(self):
        vlayout=QtWidgets.QVBoxLayout()
        label=QtWidgets.QLabel("以下是所选的各个车次关于通过标尺的总体相对误差，选择确定修改，点击上一步返回"
                               "重新选择。行的颜色越深表明误差越大。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        tableWidget=QtWidgets.QTableWidget()

        tableWidget.setColumnCount(6)
        tableWidget.setHorizontalHeaderLabels(('车次','方向','类型','始发','终到','相对误差'))
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        for i,s in enumerate((80,60,60,80,80,90)):
            tableWidget.setColumnWidth(i,s)

        self.confirmTable=tableWidget
        vlayout.addWidget(tableWidget)
        self.widget2.setLayout(vlayout)

    def _getSelectedTrains(self):
        rows = list(set(map(lambda x: x.row(), self.chooseTable.selectedIndexes())))
        rows.sort()
        return list(map(lambda x:self.chooseTable.item(x,0).data(-1),rows))

    def _setConfirmTable(self):
        self.confirmTable.setRowCount(0)
        trains=self._getSelectedTrains()
        for train in trains:
            self._addConfirmTableRow(train)

    def _addConfirmTableRow(self,train):
        row=self.confirmTable.rowCount()
        tableWidget=self.confirmTable
        tableWidget.insertRow(row)
        tableWidget.setRowHeight(row,30)

        item=QtWidgets.QTableWidgetItem(train.fullCheci())
        tableWidget.setItem(row,0,item)

        item = QtWidgets.QTableWidgetItem(train.downStr())
        tableWidget.setItem(row, 1, item)

        item = QtWidgets.QTableWidgetItem(train.trainType())
        tableWidget.setItem(row, 2, item)

        item = QtWidgets.QTableWidgetItem(train.sfz)
        tableWidget.setItem(row, 3, item)

        tableWidget.setItem(row, 4, QtWidgets.QTableWidgetItem(train.zdz))

        train.delNonLocal(self.graph)
        rate=train.relativeError(self.ruler)
        item=QtWidgets.QTableWidgetItem(f'{rate:.3f}')
        tableWidget.setItem(row,5,item)

        color = QtGui.QColor(Qt.yellow)
        color.setAlpha(300*rate)
        for c in range(6):
            item: QtWidgets.QTableWidgetItem = tableWidget.item(row, c)
            item.setBackground(QtGui.QBrush(color))

    #slots
    def _forward_clicked(self):
        self.stackedWidget.setCurrentIndex(0)
        self.btnForward.setEnabled(False)
        self.btnNext.setEnabled(True)
        self.btnOk.setEnabled(False)

    def _next_clicked(self):
        self.stackedWidget.setCurrentIndex(1)
        self.btnNext.setEnabled(False)
        self.btnForward.setEnabled(True)
        self.btnOk.setEnabled(True)
        self._setConfirmTable()

    def _ruler_changed(self,rulerName:str):
        self.ruler=rulerName

    def _to_start_changed(self,status:bool):
        self.toStart=status

    def _to_end_changed(self,status:bool):
        self.toEnd=status

    def _ok_clicked(self):
        for train in self._getSelectedTrains():
            train.detectPassStation(self.graph,self.ruler,self.toStart,self.toEnd)
            print("计算通过站完毕",train.fullCheci())
        self.okClicked.emit()
        self.mainWindow._dout("计算完毕！刷新运行图以显示新运行图。")
        self.close()

    def _note_clicked(self):
        label="此功能按将区间标尺纯运行时分（已经扣去起停附加时分）的比例，将实际纯运行时分" \
              "（扣去起停附加时分）分配到各个子区间上。\n" \
              "若选择“推定到本线起点”，则将本线第一个站点（不分上下行）到列车最靠近该站点的区间内各个站点" \
              "时刻使用标尺计算，“推定到本线终点”同理。" \
              "选择“下一步”后，程序计算出各车次相对时刻与标尺的相对误差，计算规则是各个【已知区间】" \
              "标尺运行时分（考虑起停）和已知运行时分之差值的绝对值之和与该区间【已知运行时分】之比。" \
              "\n各行背景色深浅表示相对误差大小，若相对误差大则不推荐继续推定时刻。"
        QtWidgets.QMessageBox.information(self,'逻辑说明',label)

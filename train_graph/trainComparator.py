"""
两车次比较的对话框
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .train import Train
from .graph import Graph
from .line import Line

class TrainComparator(QtWidgets.QDialog):
    def __init__(self,graph:Graph,parent=None):
        super(TrainComparator, self).__init__(parent)
        self.resize(600,600)
        self.setWindowTitle('车次运行对照')
        self.graph = graph
        self.train1 = None
        self.train2 = None
        self.initWidget()

    def initWidget(self):
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel("本功能对比两车次在本线各区间运行数据，两车次皆不经过的区间将被省略。"
                                 "若车次跨越中间车站，则该区间数据不会显示。两者不同的区间，背景红色是较快的"
                                 "一方，蓝色是较慢的一方。颜色深浅由差异程度决定。")
        label.setWordWrap(True)
        layout.addWidget(label)
        hlayout = QtWidgets.QHBoxLayout()
        combo1 = QtWidgets.QComboBox(self)
        combo2 = QtWidgets.QComboBox(self)
        self.combo1 = combo1
        self.combo2 = combo2
        combo1.addItem('请选择车次')
        combo1.setEditable(True)
        combo2.addItem('请选择车次')
        combo2.setEditable(True)
        for train in self.graph.trains():
            combo1.addItem(train.fullCheci())
            combo2.addItem(train.fullCheci())
        hlayout.addWidget(combo1)
        hlayout.addWidget(QtWidgets.QLabel('—'))
        hlayout.addWidget(combo2)
        layout.addLayout(hlayout)
        combo1.currentTextChanged.connect(self._train1_changed)
        combo2.currentTextChanged.connect(self._train2_changed)

        tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget = tableWidget
        tableWidget.setColumnCount(7)
        tableWidget.setHorizontalHeaderLabels(('区间','历时1','均速1','附加1','历时2','均速2','附加2'))
        for i,s in enumerate((120,80,80,60,80,80,60)):
            tableWidget.setColumnWidth(i,s)
        self.tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        layout.addWidget(tableWidget)

        self.setLayout(layout)

    def setTableWidget(self):
        self.tableWidget.setRowCount(0)
        if self.train1 is None and self.train2 is None:
            return
        self.addDirData(True)
        self.addDirData(False)
        checis = [train.fullCheci() if train is not None else 'null' for train in (self.train1,self.train2)]
        self.setWindowTitle('车次运行对照*{}-{}'.format(*checis))

    def addDirData(self,down:bool):
        previous = None
        for st_dict in self.graph.stationDicts(reverse=not down):
            if previous is None:
                # 第一个和最后一个站肯定是双向通过，不用试
                previous = st_dict
                continue
            if not st_dict.get('direction', Line.BothVia) &(Line.DownVia if down else Line.UpVia):
                continue
            mile = st_dict['licheng'] - previous['licheng']
            if not down:
                mile = -mile
            try:
                sec1 = self.train1.gapBetweenStation(previous['zhanming'], st_dict['zhanming'])
                tm1_str = f"{int(sec1/60)}:{sec1%60:02d}"
            except:
                sec1 = 0
                tm1_str = '-'
            if sec1 > 3600*24-sec1:
                sec1 = 0
                tm1_str = '-'
            if sec1:
                speed1 = 1000 * mile / sec1 * 3.6
                speed1_str = f"{speed1:.2f}"
                self.train1:Train
                append_str1 = self.train1.stationStopBehaviour_single(previous['zhanming'],True)+\
                             self.train1.stationStopBehaviour_single(st_dict['zhanming'],False)
            else:
                speed1 = 0
                speed1_str = '-'
                append_str1 = '-'
            try:
                sec2 = self.train2.gapBetweenStation(previous['zhanming'], st_dict['zhanming'])
                tm2_str = f"{int(sec2/60)}:{sec2%60:02d}"
            except:
                sec2 = 0
                tm2_str = '-'
            if sec2 > 3600*24-sec2:
                sec2 = 0
                tm2_str = '-'
            if sec2:
                speed2 = 1000 * mile / sec2 * 3.6
                speed2_str = f"{speed2:.2f}"
                append_str2 = self.train2.stationStopBehaviour_single(previous['zhanming'],True) + \
                             self.train2.stationStopBehaviour_single(st_dict['zhanming'],False)
            else:
                speed2 = 0
                speed2_str = '-'
                append_str2 = '-'
            if not sec1 and not sec2:
                continue

            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])

            self.tableWidget.setItem(row,0,
                QtWidgets.QTableWidgetItem(f"{previous['zhanming']}->{st_dict['zhanming']}"))

            item1 = QtWidgets.QTableWidgetItem(tm1_str)
            item2 = QtWidgets.QTableWidgetItem(speed1_str)
            item3 = QtWidgets.QTableWidgetItem(append_str1)
            item4 = QtWidgets.QTableWidgetItem(tm2_str)
            item5 = QtWidgets.QTableWidgetItem(speed2_str)
            item6 = QtWidgets.QTableWidgetItem(append_str2)
            if sec1 and sec2 and sec1 != sec2:
                alpha1 = abs(sec1-sec2)/sec1*200+55
                alpha2 = abs(sec1-sec2)/sec2*200+55
                if sec1 < sec2:
                    color1 = QtGui.QColor(Qt.red)
                    color2 = QtGui.QColor(Qt.blue)
                else:
                    color1 = QtGui.QColor(Qt.blue)
                    color2 = QtGui.QColor(Qt.red)
                color1.setAlpha(alpha1)
                color2.setAlpha(alpha2)
                item1.setBackground(QtGui.QBrush(color1))
                item2.setBackground(QtGui.QBrush(color1))
                item3.setBackground(QtGui.QBrush(color1))
                item4.setBackground(QtGui.QBrush(color2))
                item5.setBackground(QtGui.QBrush(color2))
                item6.setBackground(QtGui.QBrush(color2))
            for i,s in enumerate((item1,item2,item3,item4,item5,item6)):
                self.tableWidget.setItem(row,i+1,s)

            previous = st_dict

    # slots
    def _train1_changed(self,checi):
        if checi == '请选择车次':
            self.train1 = None
        else:
            self.train1 = self.graph.trainFromCheci(checi,True)
        self.setTableWidget()

    def _train2_changed(self,checi):
        if checi == '请选择车次':
            self.train2 = None
        else:
            self.train2 = self.graph.trainFromCheci(checi,True)
        self.setTableWidget()
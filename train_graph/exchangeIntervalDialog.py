"""
2019.07.04新增。交换两车次一个区间内的运行时刻。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .data.graph import Train,Graph

class ExchangeIntervalDialog(QtWidgets.QDialog):
    exchangeOk = QtCore.pyqtSignal(Train,Train)
    def __init__(self,train,graph,parent=None):
        super(ExchangeIntervalDialog, self).__init__(parent)
        self.train = train  # type:Train
        self.anTrain = None  # type:Train
        self.graph = graph  # type:Graph
        self.initUI()

    def initUI(self):
        self.setWindowTitle('区间换线')
        self.resize(600,600)
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('请选择一个车次，然后选择要交换时刻的区间。当前车次和另一车次的表中选择的第一个站作为起始站，最后一个站作为终止站。交换的时刻包括起始站和终止站。你可以选择是否包含起始站的到达时刻和终止站的出发时刻。请注意，原则上只有同方向且相交两次的运行线才能换线（并且只能在两个交叉点站之间），但本系统不做限制。')
        label.setWordWrap(True)
        vlayout.addWidget(label)

        hlayout = QtWidgets.QHBoxLayout()
        checkIncludeFirst = QtWidgets.QCheckBox('交换起始站到达时刻')
        self.checkIncludeFirst = checkIncludeFirst
        checkIncludeLast = QtWidgets.QCheckBox('交换终止站出发时刻')
        self.checkIncludeLast = checkIncludeLast
        hlayout.addWidget(checkIncludeFirst)
        hlayout.addWidget(checkIncludeLast)
        vlayout.addLayout(hlayout)

        flayout = QtWidgets.QFormLayout()
        comboCheci = QtWidgets.QComboBox()
        comboCheci.setEditable(True)
        for tr in self.graph.trains():
            comboCheci.addItem(tr.fullCheci())
        comboCheci.setCurrentText('')
        self.comboCheci = comboCheci
        flayout.addRow('另一车次',comboCheci)
        vlayout.addLayout(flayout)

        hlayout = QtWidgets.QHBoxLayout()
        listWidget1 = QtWidgets.QListWidget()
        self.listWidget1 = listWidget1
        listWidget1.setSelectionMode(listWidget1.MultiSelection)
        for st_dict in self.train.stationDicts():
            listWidget1.addItem(self.stationItem(st_dict))
        hlayout.addWidget(listWidget1)

        listWidget2 = QtWidgets.QListWidget()
        listWidget2.setSelectionMode(listWidget2.MultiSelection)
        self.listWidget2 = listWidget2
        hlayout.addWidget(listWidget2)

        vlayout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton('确定(&Y)')
        btnCancel = QtWidgets.QPushButton('取消(&C)')
        btnCancel.clicked.connect(self.close)
        btnOk.clicked.connect(self._ok_clicked)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)

        comboCheci.currentTextChanged.connect(self._checi_changed)
        self.setLayout(vlayout)


    @staticmethod
    def stationItem(st_dict:dict)->QtWidgets.QListWidgetItem:
        text = f"{st_dict['zhanming']:10s} "
        if st_dict['ddsj'] == st_dict['cfsj']:
            text += f".../{st_dict['cfsj'].strftime('%H:%M:%S')}"
        else:
            text += f"{st_dict['ddsj'].strftime('%H:%M:%S')}/{st_dict['cfsj'].strftime('%H:%M:%S')}"
        item = QtWidgets.QListWidgetItem(text)
        return item

    @staticmethod
    def selectionRange(listWidget:QtWidgets.QListWidget)->(int,int):
        """
        返回选择的最小和最大的行号。如果没有，返回None。
        """
        selected_rows = list(map(lambda x:listWidget.row(x),listWidget.selectedItems()))
        try:
            return min(selected_rows),max(selected_rows)
        except ValueError:
            # ValueError: max() arg is an empty sequence
            return None,None

    # slots
    def _checi_changed(self,checi:str):
        anTrain = self.graph.trainFromCheci(checi,full_only=True)
        if anTrain is None:
            return
        self.anTrain = anTrain
        self.listWidget2.clear()
        for st_dict in self.anTrain.stationDicts():
            self.listWidget2.addItem(self.stationItem(st_dict))

    def _ok_clicked(self):
        if self.anTrain is None:
            QtWidgets.QMessageBox.warning(self,'错误','请先选择另一车次！')
            return
        start1,end1 = self.selectionRange(self.listWidget1)
        start2,end2 = self.selectionRange(self.listWidget2)
        if start1 is None or start2 is None:
            QtWidgets.QMessageBox.warning(self, '错误', '请选择要换线的车站区域！')
            return
        self.train.intervalExchange(start1,end1,self.anTrain,start2,end2,
                                    includeStart=self.checkIncludeFirst.isChecked(),
                                    includeEnd=self.checkIncludeLast.isChecked())
        self.exchangeOk.emit(self.train,self.anTrain)
        self.close()
"""
2020.03.13新增
从一组车次中读取标尺数据的向导
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .data import *
from .trainFilter import TrainFilter
from typing import List,Tuple,Dict
from .dialogAdapter import DialogAdapter


class TrainTable(QtWidgets.QTableWidget):
    """
    显示车次的只读列表。
    """
    def __init__(self, graph:Graph, parent=None):
        super(TrainTable, self).__init__(parent)
        self.graph = graph
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['车次','始发','终到','类型','本线里程','本线旅速'])
        for i,s in enumerate((100,100,100,80,100,100)):
            self.setColumnWidth(i,s)
        header: QtWidgets.QHeaderView = self.horizontalHeader()
        # header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.sortByColumn)
        self.setSelectionMode(self.MultiSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.setEditTriggers(self.NoEditTriggers)

    def setTrain(self, row:int, train:Train):
        self.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])
        TWI = QtWidgets.QTableWidgetItem
        it = TWI(train.fullCheci())
        it.setData(Qt.UserRole,train)
        self.setItem(row,0,it)
        self.setItem(row,1,TWI(train.sfz))
        self.setItem(row,2,TWI(train.zdz))
        self.setItem(row,3,TWI(train.trainType()))
        it = TWI()
        it.setData(Qt.DisplayRole, train.localMile(self.graph,fullAsDefault=False))
        self.setItem(row,4,it)
        it = TWI()
        it.setData(Qt.DisplayRole, train.localSpeed(self.graph,fullAsDefault=False))
        self.setItem(row,5,it)

    def addTrain(self, train:Train):
        i = self.rowCount()
        self.insertRow(i)
        self.setTrain(i,train)

    def resetTrains(self,trains:List[Train]):
        self.setRowCount(len(trains))
        for i,train in enumerate(trains):
            self.setTrain(i,train)


class ReadRulerWizard(QtWidgets.QWizard):
    """
    pages:
    0 向导
    1 选择区间
    2 选择车次
    3 配置参数
    4 预览
    """
    rulerFinished = QtCore.pyqtSignal(Ruler, bool)  # 标尺，是否是新标尺
    def __init__(self,graph:Graph,parent=None):
        super(ReadRulerWizard, self).__init__(parent)
        self.setWindowTitle('从车次读取标尺')
        self.graph = graph
        self.initUI()
        self.currentIdChanged.connect(self._id_changed)
        self.resize(900,800)
        self.resultDict = {}
        self.resultData = {}
        self.resultFt = {}
        self.resultUsed = {}
        self.button(self.FinishButton).clicked.connect(self._finish)

    def initUI(self):
        self.setButtonText(self.FinishButton,'完成')
        self.setButtonText(self.NextButton,'下一步')
        self.setButtonText(self.CancelButton,'取消')
        self.initPage0()
        self.initPage1()
        self.initPage2()
        self.initPage3()
        self.initPage4()

    def initPage0(self):
        pg = QtWidgets.QWizardPage()
        pg.setTitle('概览')
        lay = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('欢迎使用标尺自动生成向导\n'
                                 '点击[下一步]开始配置。'
                                 )
        label.setWordWrap(True)
        lay.addWidget(label)

        label = QtWidgets.QLabel('逻辑说明：\n'
                                 '此向导将引导用户选择一组本线的区间，并按照一组选定的车次在该区间的'
                                 '运行时分，计算区间运行时分标准（标尺）。\n'
                                 '按照车次在区间的起停附加情况（通通，起通，通停，'
                                 '起停四种）可将车次分为四类。并按照下列两种算法之一决定每一类的标准数据\n'
                                 '（1）众数模式。找出每一组数据（运行秒数）中出现次数最多的那个'
                                 '作为本类的运行数据。如果有多个出现次数一样的，则取最快的那个。\n'
                                 '（2）均值模式。首先删除每一组数据中的离群数据。如果数据偏离样本均值'
                                 '超过用户指定的秒数或者用户指定的样本标准差倍数，则剔除数据。然后取所有'
                                 '剩余数据的平均值作为本类运行数据。\n\n'
                                 '产生的四类情况的数据实质上就是一个线性方程组。按照方程的数量，'
                                 '分为四种情况：\n'
                                 'a. 4类都有数据，即有四个方程。在众数模式下，如果存在一个数量最少的类，'
                                 '则删除这个方程，求解剩余3个方程构成的线性方程组即得结果。'
                                 '否则选择出现次数最少的（并列）类之一删除，使得计算出来的结果最快。'
                                 '（3.1.3版本开始，众数模式中任何情况下不使用伪逆）\n'
                                 'b. 有3类有数据，即3个方程，刚好对应3个未知数（通通时分、起步附加、'
                                 '停车附加），线性方程组一定有唯一解，求解即可。\n'
                                 'c. 有2类有数据。此时需要用到用户输入的[默认起步附加时分]和[默认停车'
                                 '附加时分]中的一个。如果起、停之中有一个是能确定的，则使用这个能确定'
                                 '的数据；如果起、停是对称的，则优先用[默认起步附加时分]。\n'
                                 'd. 只有1类有数据。此时用户输入的[默认起步附加时分]和'
                                 '[默认停车附加时分]都会使用。')
        label.setWordWrap(True)
        lay.addWidget(label)

        pg.setLayout(lay)
        self.addPage(pg)

    def initPage1(self):
        pg = QtWidgets.QWizardPage()
        pg.setTitle('选择标尺和区间')
        pg.validatePage = self.page1Validator
        lay = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('请选择一个标尺，或者新建一个标尺。\n新读取的标尺数据将放入这个标尺，'
                                 '并无条件覆盖既有数据。')
        label.setWordWrap(True)
        lay.addWidget(label)

        flay = QtWidgets.QFormLayout()
        combo = QtWidgets.QComboBox()
        combo.addItem('（新建标尺）',Ruler(line=self.graph.line))
        for ruler in self.graph.rulers():
            combo.addItem(ruler.name(),ruler)
        flay.addRow('选择标尺',combo)
        combo.currentIndexChanged.connect(self._ruler_changed)
        self.comboRuler = combo

        check = QtWidgets.QCheckBox('上下行分别读取')
        check.setChecked(True)
        if self.graph.lineSplited():
            check.setEnabled(False)
        flay.addRow('选项',check)
        check.toggled.connect(self._diff_changed)
        self.checkDiff = check
        lay.addLayout(flay)

        lb = QtWidgets.QLabel('请在下表中选择要计算的所有区间.')
        lay.addWidget(lb)

        h = QtWidgets.QHBoxLayout()
        btn = QtWidgets.QPushButton('全选')
        btn.clicked.connect(self._l_select_all)
        h.addWidget(btn)
        btn = QtWidgets.QPushButton('全不选')
        btn.clicked.connect(self._l_select_none)
        h.addWidget(btn)
        btn = QtWidgets.QPushButton('全选')
        btn.clicked.connect(self._r_select_all)
        self.btnRAll = btn
        h.addWidget(btn)
        btn = QtWidgets.QPushButton('全不选')
        btn.clicked.connect(self._r_select_none)
        self.btnRNone = btn
        h.addWidget(btn)
        lay.addLayout(h)

        hlay = QtWidgets.QHBoxLayout()
        lwd = QtWidgets.QListWidget()
        lwd.setSelectionMode(lwd.MultiSelection)
        self.downAdjs = self.graph.line.adjIntervals(True)
        self.upAdjs = self.graph.line.adjIntervals(False)
        for fz,dz in self.downAdjs:
            item = QtWidgets.QListWidgetItem(f"{fz}->{dz}")
            item.setData(Qt.UserRole,(fz,dz))
            lwd.addItem(item)
        self.listWidgetDown = lwd
        hlay.addWidget(lwd)

        lwu = QtWidgets.QListWidget()
        lwu.setSelectionMode(lwu.MultiSelection)
        for fz,dz in self.upAdjs:
            item = QtWidgets.QListWidgetItem(f"{fz}->{dz}")
            item.setData(Qt.UserRole,(fz,dz))
            lwu.addItem(item)
        self.listWidgetUp = lwu
        hlay.addWidget(lwu)
        lay.addLayout(hlay)

        pg.setLayout(lay)
        self.addPage(pg)

    def selectedIntervals(self)->List[Tuple[str,str]]:
        """
        返回已选区间。
        """
        lst = []
        for i in range(self.listWidgetDown.count()):
            if self.listWidgetDown.item(i).isSelected():
                lst.append(self.listWidgetDown.item(i).data(Qt.UserRole))
        if self.checkDiff.isChecked():
            for i in range(self.listWidgetUp.count()):
                if self.listWidgetUp.item(i).isSelected():
                    lst.append(self.listWidgetUp.item(i).data(Qt.UserRole))
        return lst

    def initPage2(self):
        pg = QtWidgets.QWizardPage()
        pg.setTitle('选择车次')
        pg.validatePage = self._page2_validator
        pg.setSubTitle('请选择一组用于读取标尺的车次（通过添加到右边表格）\n'
                       '本系统将认为所选车次属于同一标尺。如果不是，计算准确性受到影响。')
        vbox = QtWidgets.QVBoxLayout()
        h = QtWidgets.QHBoxLayout()
        btn = QtWidgets.QPushButton('车次筛选器')
        btn.setToolTip('选择左侧表格中要显示的车次')
        self.trainFilter = TrainFilter(self.graph,self)
        btn.clicked.connect(self.trainFilter.setFilter)
        self.trainFilter.FilterChanged.connect(self._filter_changed)
        h.addWidget(btn)

        btn = QtWidgets.QPushButton('全选显示车次')
        btn.clicked.connect(self._train_select_all)
        h.addWidget(btn)
        btn = QtWidgets.QPushButton('清空选择')
        btn.clicked.connect(self._train_clear)
        h.addWidget(btn)
        vbox.addLayout(h)

        self.remainTrains = list(self.graph.trains())
        self.selectTrains = []

        hbox = QtWidgets.QHBoxLayout()
        tb1 = TrainTable(self.graph)
        tb1.resetTrains(self.remainTrains)
        hbox.addWidget(tb1)
        self.remainTable = tb1

        v = QtWidgets.QVBoxLayout()
        btn = QtWidgets.QPushButton('>')
        btn.clicked.connect(self._add_trains)
        btn.setFixedWidth(30)
        v.addWidget(btn)
        btn = QtWidgets.QPushButton('<')
        btn.clicked.connect(self._remove_trains)
        btn.setFixedWidth(30)
        v.addWidget(btn)
        hbox.addLayout(v)

        tb2 = TrainTable(self.graph)
        self.selectTable = tb2
        hbox.addWidget(tb2)
        vbox.addLayout(hbox)
        pg.setLayout(vbox)
        self.addPage(pg)

    def initPage3(self):
        pg = QtWidgets.QWizardPage()
        pg.setTitle('参数配置')
        pg.setSubTitle('配置计算选项，点击[下一步]显示预览。\n'
                       '说明：\n'
                       '众数模式将选择出现次数最多的区间数据作为标尺数据，'
                       '均值模式将对所有符合条件的数据求平均值作为标尺数据；\n'
                       '默认起步、停车附加时分是当区间没有足够数据时使用的。\n'
                       '当选择均值模式时，可以选择清除偏离样本均值一定秒数或者一定样本标准差倍数的'
                       '数据，以排除极端数据的影响。\n')
        form = QtWidgets.QFormLayout()

        g = QtWidgets.QButtonGroup(self)
        hbox = QtWidgets.QHBoxLayout()
        radioMode = QtWidgets.QRadioButton('众数模式')
        radioMean = QtWidgets.QRadioButton('均值模式')
        self.radioMean = radioMean
        hbox.addWidget(radioMode)
        hbox.addWidget(radioMean)
        g.addButton(radioMode)
        g.addButton(radioMean)
        radioMode.setChecked(True)
        radioMean.toggled.connect(self._mean_toggled)
        form.addRow('算法选择',hbox)

        comboPrec = QtWidgets.QComboBox()
        self.comboPrec = comboPrec
        for i in (1,5,10,15,30,60):
            self.comboPrec.addItem(f"{i}秒",i)
        comboPrec.setMaximumHeight(200)
        form.addRow('数据粒度',comboPrec)

        s = QtWidgets.QSpinBox()
        s.setRange(0,1000)
        s.setSingleStep(10)
        s.setValue(120)
        self.spinStart = s
        h = QtWidgets.QHBoxLayout()
        h.addWidget(s)
        h.addWidget(QtWidgets.QLabel('秒'))
        form.addRow('默认起步附加',h)

        s = QtWidgets.QSpinBox()
        s.setRange(0,1000)
        s.setValue(120)
        s.setSingleStep(10)
        self.spinStop = s
        h = QtWidgets.QHBoxLayout()
        h.addWidget(s)
        h.addWidget(QtWidgets.QLabel('秒'))
        form.addRow('默认停车附加',h)

        v = QtWidgets.QVBoxLayout()
        g = QtWidgets.QButtonGroup(self)
        r = QtWidgets.QRadioButton('不筛选')
        self.radioNoCut = r
        r.setChecked(True)
        v.addWidget(r)
        g.addButton(r)
        r.setEnabled(False)

        h = QtWidgets.QHBoxLayout()
        r = QtWidgets.QRadioButton('截断于')
        self.radioCutSeconds = r
        r.setEnabled(False)
        g.addButton(r)
        h.addWidget(r)
        spinCutSec = QtWidgets.QSpinBox()
        spinCutSec.setValue(30)
        spinCutSec.setSingleStep(10)
        self.spinCutSec = spinCutSec
        spinCutSec.setRange(1,1000)
        spinCutSec.setEnabled(False)
        h.addWidget(spinCutSec)
        h.addWidget(QtWidgets.QLabel('秒'))
        v.addLayout(h)
        r.toggled.connect(self._sec_toggled)

        h = QtWidgets.QHBoxLayout()
        r = QtWidgets.QRadioButton('截断于')
        self.radioCutSigma = r
        r.setEnabled(False)
        h.addWidget(r)
        g.addButton(r)
        spinCutSigma = QtWidgets.QSpinBox()
        self.spinCutSigma  = spinCutSigma
        spinCutSigma.setRange(1,1000)
        spinCutSigma.setEnabled(False)
        h.addWidget(spinCutSigma)
        h.addWidget(QtWidgets.QLabel('倍标准差'))
        v.addLayout(h)
        r.toggled.connect(self._sigma_toggled)

        form.addRow('离群数据筛选', v)

        pg.setLayout(form)
        self.addPage(pg)

    def initPage4(self):
        """
        本函数只是初始化。数据的设置在calculate中。
        """
        pg = QtWidgets.QWizardPage()
        pg.setTitle('预览')
        pg.setSubTitle('计算结果如下表所示。\n'
                       '点击[完成]应用结果，否则结果不会被应用。\n'
                       '双击行显示详细计算数据。\n'
                       '表中的[数据类]是指在[通通]/[起通]/[通停]/[起停]这四种情况中，'
                       '有多少种情况的有效数据；'
                       '[数据总量]是指用于计算的数据总条数；[满足车次]是指用于计算的车次中，'
                       '严格满足标尺的数量。'
                       )
        tw = QtWidgets.QTableWidget()
        tw.setEditTriggers(tw.NoEditTriggers)
        tw.itemDoubleClicked.connect(self._show_detail)
        self.previewTable = tw
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(tw)
        tw.setContextMenuPolicy(Qt.ActionsContextMenu)

        ac = QtWidgets.QAction('显示各车次数据（双击）',tw)
        ac.triggered.connect(self._show_detail)
        tw.addAction(ac)

        ac = QtWidgets.QAction('按类型整理数据',tw)
        ac.triggered.connect(self._order_by_type)
        tw.addAction(ac)

        tw.setColumnCount(7)
        tw.setHorizontalHeaderLabels(['区间','通通','起步','停车','数据类','数据总量', '满足车次'])
        for i,s in enumerate((200,90,80,80,70,90,100)):
            tw.setColumnWidth(i,s)

        pg.setLayout(vbox)
        self.addPage(pg)

    def __fixCount(self,fz,dz)->int:
        node = self.resultDict[(fz,dz)]
        cnt = 0
        for train,(sec,tp) in self.resultData[(fz,dz)].items():
            if sec == self.__stdInterval(tp,*node):
                cnt+=1
        return cnt

    def calculate(self):
        res,data,ft,used = self.graph.rulerFromMultiTrains(
            self.selectedIntervals(), self.selectTrains,
            self.checkDiff.isChecked(),self.radioMean.isChecked(),
            self.spinStart.value(),self.spinStop.value(),
            self.spinCutSigma.value() if self.spinCutSigma.isEnabled() else None,
            self.spinCutSec.value() if self.spinCutSec.isEnabled() else None,
            self.comboPrec.currentData(Qt.UserRole)
        )
        # from pprint import pprint as printf
        # print("ft:")
        # printf(ft)
        self.resultDict = res
        self.resultData = data
        self.resultFt = ft
        self.resultUsed = used

        tw = self.previewTable
        ints = self.selectedIntervals()
        tw.setRowCount(len(ints))
        TWI = QtWidgets.QTableWidgetItem

        # ['区间','通通','起步','停车','数据类','数据总量']
        for i,(fz,dz) in enumerate(ints):
            tw.setRowHeight(i,self.graph.UIConfigData()['table_row_height'])
            it = TWI(f"{fz}{self.blocker()}{dz}")
            it.setData(Qt.UserRole,(fz,dz))
            tw.setItem(i,0,it)
            node = res.get((fz,dz),None)
            if node is None:
                tw.setItem(i,1,TWI('-'))
                tw.setItem(i,2,TWI('-'))
                tw.setItem(i,3,TWI('-'))
                tw.setItem(i,4,TWI('0'))
                tw.setItem(i,5,TWI('0'))
                tw.setItem(i,6,TWI('-'))
            else:
                x,y,z = node
                tw.setItem(i, 1, TWI(Train.sec2strmin(x)))
                tw.setItem(i, 2, TWI(Train.sec2strmin(y)))
                tw.setItem(i, 3, TWI(Train.sec2strmin(z)))
                tw.setItem(i, 4, TWI(str(len(ft[(fz,dz)]))))
                tw.setItem(i, 5, TWI(str(sum(map(lambda x:sum(x.values()),ft[(fz,dz)].values())))))
                tw.setItem(i, 6, TWI(str(self.__fixCount(fz,dz))))

    def blocker(self)->str:
        return '->' if self.checkDiff.isChecked() else '<->'

    # slots
    def _ruler_changed(self,idx:int):
        """
        对既有标尺，其上下行分设情况必须和既有相同。
        """
        ruler = self.comboRuler.currentData(Qt.UserRole)
        if isinstance(ruler,Ruler):
            if idx != 0:
                # 既有标尺
                self.checkDiff.setChecked(ruler.different())
                self.checkDiff.setEnabled(False)
            elif not self.graph.lineSplited():
                self.checkDiff.setEnabled(True)

    def _diff_changed(self,on:bool):
        lwd,lwu = self.listWidgetDown,self.listWidgetUp
        if on:
            lwu.setEnabled(True)
            self.btnRAll.setEnabled(True)
            self.btnRNone.setEnabled(True)
            for i in range(lwd.count()):
                lwd.item(i).setText('->'.join(lwd.item(i).data(Qt.UserRole)))
        else:
            lwu.setEnabled(False)
            self.btnRAll.setEnabled(False)
            self.btnRNone.setEnabled(False)
            for i in range(lwd.count()):
                lwd.item(i).setText('<->'.join(lwd.item(i).data(Qt.UserRole)))

    def _id_changed(self, id:int):
        if id == 4:
            self.calculate()


    def page1Validator(self)->bool:
        if not self.selectedIntervals():
            QtWidgets.QMessageBox.warning(self, '错误', '请至少选择一个区间！')
            return False
        return True

    def _filter_changed(self):
        lst = []
        for train in self.remainTrains:
            if self.trainFilter.check(train):
                lst.append(train)
        self.remainTable.resetTrains(lst)

    def _add_trains(self):
        tw = self.remainTable
        selectedRows = list(set(map(lambda item:item.row(),tw.selectedItems())))
        selectedRows.sort(reverse=True)  # 倒着一个个处理
        for row in selectedRows:
            train = tw.item(row,0).data(Qt.UserRole)
            if isinstance(train,Train):
                self.selectTrains.append(train)
                self.remainTrains.remove(train)
                self.selectTable.addTrain(train)
            tw.removeRow(row)

    def _remove_trains(self):
        tw = self.selectTable
        selectedRows = list(set(map(lambda item: item.row(), tw.selectedItems())))
        selectedRows.sort(reverse=True)  # 倒着一个个处理
        for row in selectedRows:
            train = tw.item(row, 0).data(Qt.UserRole)
            if isinstance(train, Train):
                self.selectTrains.remove(train)
                self.remainTrains.append(train)
                self.remainTable.addTrain(train)
            tw.removeRow(row)

    def _page2_validator(self)->bool:
        if len(self.selectTrains) <= 1:
            QtWidgets.QMessageBox.warning(self,'错误','请选择至少两个车次！\n'
                                            '如果只选择一个车次，此功能效果和“从车次读取标尺”相同。')
            return False
        return True

    def _mean_toggled(self, on:bool):
        if on:
            self.radioCutSeconds.setEnabled(True)
            self.radioCutSigma.setEnabled(True)
            self.radioNoCut.setEnabled(True)
        else:
            self.radioCutSeconds.setEnabled(False)
            self.radioCutSigma.setEnabled(False)
            self.radioNoCut.setEnabled(False)

    def _sec_toggled(self, on:bool):
        if on:
            self.spinCutSec.setEnabled(True)
        else:
            self.spinCutSec.setEnabled(False)

    def _sigma_toggled(self, on:bool):
        if on:
            self.spinCutSigma.setEnabled(True)
        else:
            self.spinCutSigma.setEnabled(False)

    def _finish(self):
        ruler:Ruler = self.comboRuler.currentData(Qt.UserRole)
        new = self.comboRuler.currentIndex() == 0
        if new:
            ruler.setName(self.graph.validRulerName())
        for (fz,dz), (x,y,z) in self.resultDict.items():
            ruler.addStation_info(fz,dz,x,y,z,del_existed=True)
        if new:
            while True:
                name,ok = QtWidgets.QInputDialog.getText(self,
                                                         '标尺名称',
                                                         '请为新读取的标尺命名（或点击[取消]以自动命名）')
                if name and not self.graph.rulerNameExisted(name):
                    ruler.setName(name)
                    break
                elif not ok:
                    break
                else:
                    QtWidgets.QMessageBox.warning(self,'错误','请输入一个不与现有重复且非空的有效标尺名称！')
        if self.resultDict:
            self.rulerFinished.emit(ruler, new)

    def _l_select_all(self):
        lw = self.listWidgetDown
        for i in range(lw.count()):
            lw.item(i).setSelected(True)

    def _l_select_none(self):
        self.listWidgetDown.clearSelection()

    def _r_select_all(self):
        lw = self.listWidgetUp
        for i in range(lw.count()):
            lw.item(i).setSelected(True)

    def _r_select_none(self):
        self.listWidgetUp.clearSelection()

    def _train_select_all(self):
        tw = self.remainTable
        for i in range(tw.rowCount()-1,-1,-1):
            train = tw.item(i,0).data(Qt.UserRole)
            if isinstance(train,Train):
                self.selectTable.addTrain(train)
                self.remainTrains.remove(train)
                self.selectTrains.append(train)
                tw.removeRow(i)

    def _train_clear(self):
        tw = self.selectTable
        for i in range(tw.rowCount() - 1, -1, -1):
            train = tw.item(i, 0).data(Qt.UserRole)
            if isinstance(train, Train):
                self.remainTable.addTrain(train)
            tw.removeRow(i)
        self.remainTrains.extend(self.selectTrains)
        self.selectTrains.clear()

    @staticmethod
    def __type2str(tp:int)->str:
        res = ''
        if tp & Train.AttachStart:
            res+='起'
        if tp & Train.AttachStop:
            res+='停'
        return res

    @staticmethod
    def __type2rich_str(tp:int)->str:
        res = ''
        if tp & Train.AttachStart:
            res += '起'
        else:
            res+='通'
        if tp & Train.AttachStop:
            res += '停'
        else:
            res+='通'
        return res

    @staticmethod
    def __stdInterval(tp:int,interval:int,start:int,stop:int)->int:
        if tp & Train.AttachStart:
            interval+=start
        if tp & Train.AttachStop:
            interval+=stop
        return interval

    def _show_detail(self, item:QtWidgets.QTableWidgetItem=None):
        """
        显示各个车次与计算标尺的比较.
        暂不考虑排序。
        """
        if not isinstance(item,QtWidgets.QTableWidgetItem):
            item = self.previewTable.currentItem()
        i = item.row()
        fz,dz = self.previewTable.item(i,0).data(Qt.UserRole)

        tw = QtWidgets.QTableWidget()
        tw.setWindowTitle(f'计算细节*{fz}{self.blocker()}{dz}')

        tw.setEditTriggers(tw.NoEditTriggers)
        tw.setColumnCount(7)
        tw.setHorizontalHeaderLabels(['车次','附加','标准','实际','差时','绝对值','标记'])
        header:QtWidgets.QHeaderView = tw.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tw.sortByColumn)
        header.setSortIndicatorShown(True)

        for i,s in enumerate((120,60,80,80,80,80,90)):
            tw.setColumnWidth(i,s)

        TWI = QtWidgets.QTableWidgetItem
        tw.setRowCount(len(self.resultData[(fz,dz)]))
        node = self.resultDict[(fz,dz)]
        for row, (train,(sec,tp)) in enumerate(self.resultData[(fz,dz)].items()):
            std = self.__stdInterval(tp,*node)
            tw.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])
            tw.setItem(row,0,TWI(train.fullCheci()))
            tw.setItem(row,1,TWI(self.__type2str(tp)))
            tw.setItem(row,2,TWI(Train.sec2strmin(std)))
            tw.setItem(row,3,TWI(Train.sec2strmin(sec)))
            it = TWI()
            it.setData(Qt.DisplayRole,sec-std)
            tw.setItem(row,4,it)
            it = TWI()
            it.setData(Qt.DisplayRole,abs(sec-std))
            tw.setItem(row,5,it)
            it = TWI()
            if self.radioMean.isChecked():
                # 均值模式，标记截断数据
                if self.resultFt[(fz,dz)][tp].get(sec,None) is None:
                    it.setText('截断')
            else:
                # 众数模式，标记采信数据和类型弃用数据
                if not self.resultUsed[(fz,dz)][tp][2]:
                    it.setText('类型弃用')
                elif sec == self.resultUsed[(fz,dz)][tp][0]:
                    it.setText('采信')
            tw.setItem(row,6,it)
        dialog = DialogAdapter(tw,self)
        dialog.resize(700,600)
        dialog.show()

    def _order_by_type(self):
        row = self.previewTable.currentRow()
        if not 0<=row<self.previewTable.rowCount():
            return
        fz,dz = self.previewTable.item(row,0).data(Qt.UserRole)

        tw = QtWidgets.QTableWidget()
        tw.setEditTriggers(tw.NoEditTriggers)
        header = tw.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tw.sortByColumn)

        tw.setColumnCount(4)
        tw.setHorizontalHeaderLabels(['类型','采信数据','有效数','使用'])
        tw.setRowCount(len(self.resultUsed[(fz,dz)]))
        TWI = QtWidgets.QTableWidgetItem
        for i,s in enumerate((80,100,70,70)):
            tw.setColumnWidth(i,s)

        for i, (tp, (value, cnt, used)) in enumerate(self.resultUsed[(fz,dz)].items()):
            tw.setItem(i,0,TWI(self.__type2rich_str(tp)))
            tw.setItem(i,1,TWI(Train.sec2strmin(value)))
            tw.setItem(i,2,TWI(str(cnt)))
            tw.setItem(i,3,TWI('√' if used else '×'))

        tw.setWindowTitle(f'类型数据{fz}{self.blocker()}{dz}')
        dialog = DialogAdapter(tw,self)
        dialog.resize(400,400)
        dialog.show()
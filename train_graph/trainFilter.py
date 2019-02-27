"""
列车筛选器类，允许根据列车种类，上下行等信息筛选并保存列车信息，同时可根据已经保存的信息决定车次是否属于。
支持功能：类型选择；包含/排除车次（正则）；上下行；只包括显示车次
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .graph import Graph
from .train import Train
from Timetable_new.utility import stationEqual
import re

class TrainFilter(QtCore.QObject):
    DownOnly = 1
    UpOnly = 2
    DownAndUp = 3
    FilterChanged = QtCore.pyqtSignal()
    def __init__(self,graph:Graph,parent):
        super().__init__(parent)
        self.graph = graph
        self.parent = parent
        self.includes = []
        self.includesCache = None
        self.useInclude = False
        self.excludes = []
        self.excludesCache = None
        self.useExclude = False
        self.types = []
        self.typesCache = None
        self.useType = False
        self.showOnly = False
        self.direction = self.DownAndUp
        self.startStations = []
        self.endStations = []
        self.useStart = False
        self.useEnd = False
        self.startCache = [] # 全程不允许创建空对象
        self.endCache = []
        self.reverse = False

    def setFilter(self):
        dialog = QtWidgets.QDialog(self.parent)
        self.dialog = dialog
        dialog.setWindowTitle('车次筛选器')
        layout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        typeCheck = QtWidgets.QCheckBox('列车类型')
        self.typeCheck = typeCheck
        typeCheck.setChecked(self.useType)
        btnType = QtWidgets.QPushButton('设置类型')
        btnType.setMaximumWidth(120)
        flayout.addRow(typeCheck,btnType)
        btnType.clicked.connect(self._select_type)

        includeCheck = QtWidgets.QCheckBox('包含车次')
        self.includeCheck = includeCheck
        includeCheck.setChecked(self.useInclude)
        btnInclude = QtWidgets.QPushButton('设置包含车次')
        btnInclude.setMaximumWidth(120)
        btnInclude.clicked.connect(self._select_include)
        flayout.addRow(includeCheck, btnInclude)

        excludeCheck = QtWidgets.QCheckBox('排除车次')
        self.excludeCheck = excludeCheck
        excludeCheck.setChecked(self.useExclude)
        btnExclude = QtWidgets.QPushButton('设置排除车次')
        btnExclude.clicked.connect(self._select_exclude)
        btnExclude.setMaximumWidth(120)
        flayout.addRow(excludeCheck,btnExclude)

        startCheck = QtWidgets.QCheckBox('在选定站始发')
        self.startCheck = startCheck
        startCheck.setChecked(self.useStart)
        btnStart = QtWidgets.QPushButton('设置始发站')
        btnStart.clicked.connect(lambda:self._select_start_or_end(self.startStations,self.startCache,'始发站'))
        btnStart.setMaximumWidth(120)
        flayout.addRow(startCheck,btnStart)

        endCheck = QtWidgets.QCheckBox('在选定站终到')
        self.endCheck = endCheck
        endCheck.setChecked(self.useEnd)
        btnEnd = QtWidgets.QPushButton('设置终到站')
        btnEnd.clicked.connect(lambda:self._select_start_or_end(self.endStations,self.endCache,'终到站'))
        btnEnd.setMaximumWidth(120)
        flayout.addRow(endCheck,btnEnd)

        radioDown = QtWidgets.QRadioButton('下行')
        radioUp = QtWidgets.QRadioButton('上行')
        radioAll = QtWidgets.QRadioButton("全部")
        self.radioDown = radioDown
        self.radioUp = radioUp
        if self.direction == self.DownOnly:
            radioDown.setChecked(True)
        elif self.direction == self.UpOnly:
            radioUp.setChecked(True)
        else:
            radioAll.setChecked(True)
        group = QtWidgets.QButtonGroup(dialog)
        group.addButton(radioAll)
        group.addButton(radioUp)
        group.addButton(radioDown)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(radioDown)
        hlayout.addWidget(radioUp)
        hlayout.addWidget(radioAll)
        flayout.addRow('方向选择',hlayout)

        checkShowOnly = QtWidgets.QCheckBox()
        checkShowOnly.setChecked(self.showOnly)
        self.checkShowOnly = checkShowOnly
        flayout.addRow('只包括当前显示车次',checkShowOnly)

        checkReverse = QtWidgets.QCheckBox()
        checkReverse.setChecked(self.reverse)
        self.checkReverse = checkReverse
        flayout.addRow('反向选择',checkReverse)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnClear = QtWidgets.QPushButton("清空")
        btnCancel = QtWidgets.QPushButton("取消")
        btnOk.clicked.connect(self._ok_cliecked)
        btnCancel.clicked.connect(dialog.close)
        btnClear.clicked.connect(self.clear)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnClear)
        hlayout.addWidget(btnCancel)

        layout.addLayout(flayout)
        layout.addLayout(hlayout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _select_type(self):
        dialog = QtWidgets.QDialog(self.dialog)
        self.typeDialog = dialog
        dialog.setWindowTitle('列车类型选择')
        layout = QtWidgets.QVBoxLayout()

        if self.typesCache is None:
            self.typesCache = self.types[:]
        typeList = QtWidgets.QListWidget()
        self.typeList = typeList
        self.typeList.setSelectionMode(typeList.MultiSelection)
        for t in self.graph.typeList:
            item = QtWidgets.QListWidgetItem(t)
            typeList.addItem(item)
            if t in self.typesCache:
                item.setSelected(True)
        layout.addWidget(typeList)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(self._select_type_ok)
        layout.addLayout(hlayout)
        dialog.setLayout(layout)

        dialog.exec_()

    def _select_type_ok(self):
        self.typesCache = []
        for item in self.typeList.selectedItems():
            self.typesCache.append(item.text())
        self.typeDialog.close()

    def _select_include(self):
        dialog = QtWidgets.QDialog(self.dialog)
        dialog.setWindowTitle('包含车次')
        self.includeDialog = dialog
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("请在下表中选择或填写要包含的车次，允许使用正则表达式。")
        label.setWordWrap(True)
        layout.addWidget(label)

        includeTable = QtWidgets.QTableWidget()
        self.includeTable = includeTable
        includeTable.setColumnCount(1)
        includeTable.setHorizontalHeaderLabels(('车次',))
        includeTable.setColumnWidth(0,200)
        if self.includesCache is None:
            self.includesCache=self.includes[:]
        for c in self.includesCache:
            self._add_includeTable_row(c)
        layout.addWidget(includeTable)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton('添加')
        btnDel = QtWidgets.QPushButton('删除')
        btnAdd.clicked.connect(self._add_includeTable_row)
        btnDel.clicked.connect(self._del_includeTable_row)
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        btnOk.clicked.connect(self._select_include_ok)
        btnCancel.clicked.connect(dialog.close)
        layout.addLayout(hlayout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _add_includeTable_row(self,checi=''):
        combo = QtWidgets.QComboBox()
        for tr in self.graph.trains():
            combo.addItem(tr.fullCheci())
        combo.setEditable(True)
        if checi:
            combo.setCurrentText(checi)
        else:
            combo.setCurrentText('')
        row = self.includeTable.rowCount()
        self.includeTable.insertRow(row)
        self.includeTable.setCellWidget(row,0,combo)
        self.includeTable.setRowHeight(row, self.graph.UIConfigData()['table_row_height'])

    def _del_includeTable_row(self):
        self.includeTable.removeRow(self.includeTable.currentRow())

    def _select_include_ok(self):
        self.includesCache = []
        for row in range(self.includeTable.rowCount()):
            checi = self.includeTable.cellWidget(row,0).currentText()
            if checi and checi not in self.includesCache:
                self.includesCache.append(checi)
        self.includeDialog.close()

    def _select_exclude(self):
        dialog = QtWidgets.QDialog(self.dialog)
        dialog.setWindowTitle('包含车次')
        self.excludeDialog = dialog
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("请在下表中选择或填写要包含的车次，允许使用正则表达式。")
        label.setWordWrap(True)
        layout.addWidget(label)

        excludeTable = QtWidgets.QTableWidget()
        self.excludeTable = excludeTable
        excludeTable.setColumnCount(1)
        excludeTable.setHorizontalHeaderLabels(('车次',))
        excludeTable.setColumnWidth(0,200)

        if self.excludesCache is None:
            self.excludesCache = self.excludes[:]
        for c in self.excludesCache:
            self._add_excludeTable_row(c)
        layout.addWidget(excludeTable)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton('添加')
        btnDel = QtWidgets.QPushButton('删除')
        btnAdd.clicked.connect(self._add_excludeTable_row)
        btnDel.clicked.connect(self._del_excludeTable_row)
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        btnOk.clicked.connect(self._select_exclude_ok)
        btnCancel.clicked.connect(dialog.close)
        layout.addLayout(hlayout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _add_excludeTable_row(self,checi=''):
        combo = QtWidgets.QComboBox()
        for tr in self.graph.trains():
            combo.addItem(tr.fullCheci())
        combo.setEditable(True)
        if checi:
            combo.setCurrentText(checi)
        else:
            combo.setCurrentText('')
        row = self.excludeTable.rowCount()
        self.excludeTable.insertRow(row)
        self.excludeTable.setCellWidget(row,0,combo)
        self.excludeTable.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])

    def _del_excludeTable_row(self):
        self.excludeTable.removeRow(self.excludeTable.currentRow())

    def _select_exclude_ok(self):
        self.excludesCache = []
        for row in range(self.excludeTable.rowCount()):
            checi = self.excludeTable.cellWidget(row,0).currentText()
            if checi and checi not in self.excludesCache:
                self.excludesCache.append(checi)
        self.excludeDialog.close()

    # 按始发终到站筛选
    def _select_start_or_end(self,data:list,cache:list,title):
        """
        选择始发站和终到站的操作合并到一个函数
        """
        if not cache:
            cache.extend(data)
        dialog = QtWidgets.QDialog(self.dialog)
        dialog.setWindowTitle(title)
        vlayout = QtWidgets.QVBoxLayout()

        btnImport = QtWidgets.QPushButton("导入本线站表")
        vlayout.addWidget(btnImport)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(1)
        tableWidget.setHorizontalHeaderLabels(('站名',))
        tableWidget.setColumnWidth(0,120)
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)
        vlayout.addWidget(tableWidget)

        for name in cache:
            self._add_start_end_row(tableWidget,name)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton('添加')
        btnDel = QtWidgets.QPushButton('删除')
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        btnAdd.clicked.connect(lambda:self._add_start_end_row(tableWidget))
        btnDel.clicked.connect(lambda:self._del_start_end_row(tableWidget))
        vlayout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton('确定')
        btnCancel = QtWidgets.QPushButton('取消')
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)
        btnOk.clicked.connect(lambda:self._start_or_end_ok(tableWidget,dialog,data,cache))
        btnCancel.clicked.connect(dialog.close)

        btnImport.clicked.connect(lambda:self._import_local_stations(tableWidget,dialog))
        dialog.setLayout(vlayout)
        dialog.exec_()

    def _import_local_stations(self,tableWidget:QtWidgets.QTableWidget,pardialog:QtWidgets.QDialog):
        """
        导入站表。pardialog只用来设置parent。
        """
        dialog = QtWidgets.QDialog(pardialog)
        dialog.setWindowTitle('导入本线站表')
        label = QtWidgets.QLabel("请在列表中选择选择需要导入的本线站名，或直接点击下方的全选按钮。")
        label.setWordWrap(True)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(label)

        listWidget = QtWidgets.QListWidget()
        listWidget.setSelectionMode(listWidget.MultiSelection)
        for name in self.graph.stations():
            listWidget.addItem(name)
        vlayout.addWidget(listWidget)
        dialog.setLayout(vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnAll = QtWidgets.QPushButton("全选")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnAll)
        hlayout.addWidget(btnCancel)
        btnOk.clicked.connect(lambda:self._import_ok(dialog,tableWidget,listWidget))
        btnAll.clicked.connect(lambda:self._import_all(dialog,tableWidget))
        btnCancel.clicked.connect(dialog.close)
        vlayout.addLayout(hlayout)
        dialog.exec_()

    def _import_ok(self,dialog,tableWidget:QtWidgets.QTableWidget,listWidget:QtWidgets.QListWidget):
        for item in listWidget.selectedItems():
            self._add_start_end_row(tableWidget,item.text())
        dialog.close()

    def _import_all(self,dialog,tableWidget:QtWidgets.QTableWidget):
        for st in self.graph.stations():
            self._add_start_end_row(tableWidget,st)
        dialog.close()

    def _add_start_end_row(self,tableWidget:QtWidgets.QTableWidget,name=None):
        row = tableWidget.rowCount()
        tableWidget.insertRow(row)
        if name is None:
            name = ''
        tableWidget.setItem(row,0,QtWidgets.QTableWidgetItem(name))
        tableWidget.setRowHeight(row,30)

    def _del_start_end_row(self,tableWidget:QtWidgets.QTableWidget):
        tableWidget.removeRow(tableWidget.currentRow())

    def _start_or_end_ok(self,tableWidget:QtWidgets.QTableWidget,dialog:QtWidgets.QDialog,
                         data:list,cache:list):
        cache.clear()
        for row in range(tableWidget.rowCount()):
            txt = tableWidget.item(row,0).text()
            if txt not in cache:
                cache.append(txt)
        dialog.close()

    def _ok_cliecked(self):
        if self.includesCache is not None:
            self.includes = self.includesCache
            self.includesCache=None
        if self.excludesCache is not None:
            self.excludes = self.excludesCache
            self.excludesCache = None
        if self.typesCache is not None:
            self.types = self.typesCache
            self.typesCache = None
        self.startStations = self.startCache[:]
        self.endStations = self.endCache[:]
        self.startCache.clear()
        self.endCache.clear()

        self.useExclude = self.excludeCheck.isChecked()
        self.useInclude = self.includeCheck.isChecked()
        self.useType = self.typeCheck.isChecked()
        self.useStart = self.startCheck.isChecked()
        self.useEnd = self.endCheck.isChecked()
        self.showOnly = self.checkShowOnly.isChecked()
        self.reverse = self.checkReverse.isChecked()

        if self.radioDown.isChecked():
            self.direction = self.DownOnly
        elif self.radioUp.isChecked():
            self.direction = self.UpOnly
        else:
            self.direction = self.DownAndUp
        self.dialog.close()
        print(self.includes,self.excludes)
        self.FilterChanged.emit()

    def clear(self):
        """
        清除所有筛选条件.
        """
        if not self.question('清除所有筛选条件，即设置所有车次都被选中。是否继续？'):
            return
        self.useType = False
        self.types = []
        self.useInclude = False
        self.includes = []
        self.useExclude = False
        self.excludes = []
        self.direction = self.DownAndUp
        self.showOnly = False
        self.startStations.clear()
        self.startCache.clear()
        self.useStart = False
        self.endStations.clear()
        self.endCache.clear()
        self.useEnd = False
        self.dialog.close()
        self.FilterChanged.emit()

    def checkInclude(self,train:Train):
        if not self.useInclude:
            return False
        for regex in self.includes:
            if re.match(regex,train.fullCheci()):
                return True
            if re.match(regex,train.downCheci()):
                return True
            if re.match(regex,train.upCheci()):
                return True
        return False

    def checkExclude(self,train:Train):
        """
        检查是否被排除。被排除返回True
        """
        if not self.useExclude:
            return False
        for regex in self.excludes:
            if re.match(regex,train.fullCheci()):
                return True
            if re.match(regex,train.downCheci()):
                return True
            if re.match(regex,train.upCheci()):
                return True
        return False

    def checkType(self,train):
        if not self.useType:
            return True
        if train.trainType() in self.types:
            return True
        return False

    def checkDir(self,train):
        if self.direction == self.DownAndUp:
            return True
        elif self.direction == self.DownOnly:
            if train.down:
                return True
            return False
        else: # UpOnly
            if train.down:
                return False
            return True

    def checkShow(self,train):
        if not self.showOnly or train.isShow():
            return True
        return False

    def checkStartEnd(self,train):
        # 返回False，True保留到最后
        if self.useStart:
            for st in self.startStations:
                if stationEqual(train.sfz,st):
                    break
            else:
                return False
        if self.useEnd:
            for st in self.endStations:
                if stationEqual(train.zdz,st):
                    break
            else:
                return False
        return True


    def check(self,train):
        result = (self.checkShow(train) and self.checkDir(train) and self.checkType(train) \
               and (not self.checkExclude(train)) and self.checkStartEnd(train)) \
               or self.checkInclude(train)
        if self.reverse:
            return not result
        return result

    def setGraph(self,graph):
        self.graph = graph

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self.dialog, self.dialog.windowTitle(), note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default
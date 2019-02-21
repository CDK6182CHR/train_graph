"""
列车筛选器类，允许根据列车种类，上下行等信息筛选并保存列车信息，同时可根据已经保存的信息决定车次是否属于。
支持功能：类型选择；包含/排除车次（正则）；上下行；只包括显示车次
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .graph import Graph
from .train import Train
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

        typeList = QtWidgets.QListWidget()
        self.typeList = typeList
        self.typeList.setSelectionMode(typeList.MultiSelection)
        for t in self.graph.typeList:
            item = QtWidgets.QListWidgetItem(t)
            typeList.addItem(item)
            if t in self.types:
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
        for c in self.includes:
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
        for c in self.excludes:
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

        self.useExclude = self.excludeCheck.isChecked()
        self.useInclude = self.includeCheck.isChecked()
        self.useType = self.typeCheck.isChecked()
        self.showOnly = self.checkShowOnly.isChecked()

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
        :param train:
        :return:
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

    def check(self,train):
        return (self.checkShow(train) and self.checkDir(train) and self.checkType(train) \
               and not self.checkExclude(train)) or self.checkInclude(train)

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
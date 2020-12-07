"""
独立出来的标尺编辑窗口类。架空主程序中相关部分。
2018.12.14修改，将main设为可选，保证可以从数据库独立调用。
"""
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from .rulerTabWidget import RulerTabWidget
from .data.line import Line, Ruler


class RulerWidget(QtWidgets.QTabWidget):
    okClicked = QtCore.pyqtSignal()
    showStatus = QtCore.pyqtSignal(str)

    def __init__(self, line: Line, main=None):
        super().__init__()
        self.line = line
        self.main = main
        self.updating = False
        self.initUI()

    def initUI(self):
        """
        初始化数据。
        """
        self.updating = True
        self.clear()
        line = self.line
        for ruler in line.rulers:
            self._addRulerTab(ruler)
        new_ruler = Ruler(line=line)
        self._addRulerTab(new_ruler)
        self.updating = False

    def setData(self):
        """
        2019.07.19新增。
        标尺数量可能变化，更新内容。由刷新操作调用。
        """
        self.updating = True
        cnt = len(self.line.rulers)
        while self.count() > cnt + 1:
            self.removeTab(self.count() - 1)
        # 先更新既有的widget
        for i, ruler in enumerate(self.line.rulers):
            if i < self.count():
                widget = self.widget(i)
                widget.ruler = ruler
                self._updateRulerTabWidget(widget)
                self.setTabText(i, ruler.name())
            else:
                self._addRulerTab(ruler)
        if self.count() != len(self.line.rulers) + 1:
            # 差最后一个“新建”，补上。
            self._addRulerTab(Ruler(line=self.line, name='新建'))
        else:
            widget = self.widget(self.count() - 1)
            widget.ruler = Ruler(name='新建', line=self.line)
            self.setTabText(self.count() - 1, '新建')
            self._updateRulerTabWidget(widget)
        self.updating = False

    def updateRulerTabs(self):
        """
        已知标尺不增减，只有内部变化，更新所有标尺的标签页。
        """
        for i in range(self.count()):
            widget = self.widget(i)
            self._updateRulerTabWidget(widget)

    def _addRulerTab(self, ruler):
        """
        主要逻辑移动到RulerTabWidget.initUI()中去。这里主要是实例化和connect
        """
        widget = RulerTabWidget(ruler, self.main)
        tabname = ruler.name()
        if not tabname:
            tabname = "新建"
        self.addTab(widget, tabname)

        widget.newRulerAdded.connect(self._addRulerTab)
        widget.tabNameChanged.connect(self._current_ruler_name_changed)
        widget.rulerDeleted.connect(self._del_ruler)

    def _updateRulerTabWidget(self, widget: RulerTabWidget):
        """
        转移到新的 updateData()
        """
        widget.updateData()

    @staticmethod
    def _tableRowInterval(tableWidget: QtWidgets.QTableWidget, row: int):
        """
        返回某一行对应的区间。
        """
        try:
            return tableWidget.item(row, 0).data(-1)
        except:
            return None

    # slots

    def _current_ruler_name_changed(self, name: str):
        self.setTabText(self.currentIndex(), name)

    def _del_ruler(self):
        """
        2020.06.08重构：不再通过ruler参数定位，而是直接用当前显示的tab。
        """
        tab = self.currentWidget()
        ruler: Ruler = tab.ruler
        line: Line = ruler.line()
        new = line.isNewRuler(ruler)

        if not self.qustion("是否确认删除当前标尺？"):
            return

        if self.main is not None and ruler is self.main.graph.ordinateRuler():
            # 若是排图标尺，取消排图标尺
            self.main.changeOrdinateRuler(None)

        self.removeTab(self.currentIndex())
        line.delRuler(ruler)

        if new:
            # 如果是新建标尺，则再新建一个tab
            new_ruler = Ruler(line=line)
            self._addRulerTab(new_ruler)

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def qustion(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '标尺编辑', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

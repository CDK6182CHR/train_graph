"""
2019.02.05抽离颜色面板
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .graph import Graph

class ColorWidget(QtWidgets.QWidget):
    def __init__(self,graph:Graph,parent=None):
        super(ColorWidget, self).__init__(parent)
        self.setWindowTitle("颜色编辑")
        self.graph = graph
        self.initWidget()

    def initWidget(self):
        UIDict = self.graph.UIConfigData()

        layout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        gridBtn = QtWidgets.QPushButton(UIDict["grid_color"])
        gridColor = QtGui.QColor(UIDict["grid_color"])
        self.gridColor = gridColor
        self.gridBtn = gridBtn
        gridBtn.setStyleSheet(f"background-color:rgb({gridColor.red()},{gridColor.green()},{gridColor.blue()})")
        gridBtn.setMaximumWidth(150)
        gridBtn.clicked.connect(lambda: self._choose_color(gridColor))
        flayout.addRow("运行线格颜色", gridBtn)

        textBtn = QtWidgets.QPushButton(UIDict["text_color"])
        textColor = QtGui.QColor(UIDict["text_color"])
        self.textColor = textColor
        self.textBtn = textBtn
        textBtn.setStyleSheet(f"background-color:rgb({textColor.red()},{textColor.green()},{textColor.blue()})")
        textBtn.setMaximumWidth(150)
        textBtn.clicked.connect(lambda: self._choose_color(textColor))
        flayout.addRow("文字颜色", textBtn)

        defaultBtn = QtWidgets.QPushButton(UIDict["default_colors"]["default"])
        defaultColor = QtGui.QColor(UIDict["default_colors"]["default"])
        self.defaultColor = defaultColor
        self.defaultBtn = defaultBtn
        defaultBtn.setStyleSheet(
            f"background-color:rgb({defaultColor.red()},{defaultColor.green()},{defaultColor.blue()})")
        defaultBtn.setMaximumWidth(150)
        defaultBtn.clicked.connect(lambda: self._choose_color(defaultColor))
        flayout.addRow("默认运行线颜色", defaultBtn)

        layout.addLayout(flayout)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(2)
        tableWidget.setHorizontalHeaderLabels(["类型", "颜色"])
        tableWidget.setColumnWidth(0, 80)
        tableWidget.setColumnWidth(1, 120)
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)

        tableWidget.cellClicked.connect(self._choose_color_table)
        self.tableWidget = tableWidget

        self._setTable()

        layout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton("添加类型")
        btnAdd.setMinimumWidth(90)
        btnDel = QtWidgets.QPushButton("删除类型")
        btnDel.setMinimumWidth(90)
        btnOk = QtWidgets.QPushButton("确定")
        btnOk.setMinimumWidth(60)
        btnCancel = QtWidgets.QPushButton("还原")
        btnCancel.setMinimumWidth(60)
        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        btnAdd.clicked.connect(self._add_color_row)
        btnDel.clicked.connect(self._del_color_row)
        btnOk.clicked.connect(self._apply_color)
        btnCancel.clicked.connect(self._default_color)

        layout.addLayout(hlayout)
        self.setLayout(layout)

    def _setTable(self):
        """
        代价不大，暂定每次都重新创建所有单元格
        """
        tableWidget = self.tableWidget
        UIDict = self.graph.UIConfigData()
        tableWidget.setRowCount(len(UIDict["default_colors"]) - 1)
        row = 0
        for key, value in UIDict["default_colors"].items():
            if key == "default":
                continue

            tableWidget.setRowHeight(row, 30)
            item = QtWidgets.QTableWidgetItem(key)
            tableWidget.setItem(row, 0, item)

            item = QtWidgets.QTableWidgetItem(value)
            item.setBackground(QtGui.QBrush(QtGui.QColor(value)))
            tableWidget.setItem(row, 1, item)
            item.setFlags(Qt.NoItemFlags)

            row += 1

    def setData(self):
        UIDict = self.graph.UIConfigData()
        self._setButtonColorText(self.gridBtn,UIDict["grid_color"])
        self._setButtonColorText(self.defaultBtn,UIDict["default_colors"]["default"])
        self._setButtonColorText(self.textBtn,UIDict["text_color"])

    @staticmethod
    def _setButtonColorText(btn:QtWidgets.QPushButton,color_str:str):
        btn.setText(color_str)
        color = QtGui.QColor(color_str)
        btn.setStyleSheet(f"background-color:rgb({color.red()},{color.green()},{color.blue()})")

    def _choose_color(self, initColor: QtGui.QColor):
        btn: QtWidgets.QPushButton = self.sender()
        color: QtGui.QColor = QtWidgets.QColorDialog.getColor(initColor, title=btn.text())
        btn.setText("#%02X%02X%02X" % (color.red(), color.green(), color.blue()))
        btn.setStyleSheet(f"background-color:rgb({color.red()},{color.green()},{color.blue()})")
        arribute_dict = {
            '运行线格颜色': self.gridColor,
            '文字颜色': self.textColor,
            '默认运行线颜色': self.defaultColor,
        }
        arribute_dict[btn.text()] = color

    def _choose_color_table(self, row):
        """
        slot。colorDock中的表格双击进入。
        """
        table: QtWidgets.QTableWidget = self.sender()
        initColor = QtGui.QColor(table.item(row, 1).text())
        color = QtWidgets.QColorDialog.getColor(initColor, title=f"默认颜色: {table.item(row,0).text()}")
        table.item(row, 1).setBackground(QtGui.QBrush(color))
        table.item(row, 1).setText("#%02X%02X%02X" % (color.red(), color.green(), color.blue()))

    def _default_color(self):
        flag = self.qustion("将颜色设置恢复为系统默认，当前运行图相关设置的修改将丢失。是否继续？")
        if not flag:
            return

        keys = ("grid_color", "default_colors", "text_color")
        for key in keys:
            self.graph.UIConfigData()[key] = self.graph.sysConfigData()[key]

        self.setData()

    def _add_color_row(self):
        table = self.tableWidget
        row = table.rowCount()
        table.insertRow(table.rowCount())
        table.setRowHeight(row, 30)

        item = QtWidgets.QTableWidgetItem('#FFFFFF')
        item.setFlags(Qt.NoItemFlags)
        table.setItem(row, 1, item)

    def _del_color_row(self):
        table = self.tableWidget
        table.removeRow(table.currentRow())

    RepaintGraph = QtCore.pyqtSignal()
    def _apply_color(self):
        repaint = False
        rawDict = self.graph.UIConfigData()
        UIDict = {}
        if self.gridBtn.text() != rawDict["grid_color"]:
            UIDict["grid_color"] = self.gridBtn.text()
            repaint = True
        if self.textBtn.text() != rawDict["text_color"]:
            UIDict["text_color"] = self.textBtn.text()
            repaint = True
        UIDict["default_colors"] = {}
        UIDict["default_colors"]["default"] = self.defaultBtn.text()

        tableWidget: QtWidgets.QTableWidget = self.tableWidget
        for row in range(tableWidget.rowCount()):
            key = tableWidget.item(row, 0).text()
            value = tableWidget.item(row, 1).text()
            try:
                UIDict["default_colors"][key] = value
            except:
                self._derr(f"类型名称重复：{key}，请重新编辑！")
                return

        self.graph.UIConfigData().update(UIDict)

        if repaint:
            self.RepaintGraph.emit()
        else:
            for train in self.graph.trains():
                train.updateColor()

    def _derr(self, note: str):
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, self.windowTitle(), note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default
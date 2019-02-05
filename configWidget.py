"""
抽离运行图设置面板。组织逻辑暂时保持不变。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from graph import Graph

class ConfigWidget(QtWidgets.QWidget):
    RepaintGraph = QtCore.pyqtSignal()
    SaveSystemConfig = QtCore.pyqtSignal()
    def __init__(self,graph:Graph,parent=None):
        super(ConfigWidget, self).__init__(parent)
        self.setWindowTitle('运行图设置')
        self.graph = graph
        self.initWidget()

    def initWidget(self):
        """
        原main._initConfigWidget。
        """
        vlayout = QtWidgets.QVBoxLayout()
        layout = QtWidgets.QFormLayout()
        vlayout.addLayout(layout)

        label1 = QtWidgets.QLabel("起始时刻")
        spin1 = QtWidgets.QSpinBox()
        spin1.setSingleStep(1)
        spin1.setRange(0, 24)
        spin1.setValue(self.graph.UIConfigData()["start_hour"])
        layout.addRow(label1, spin1)
        self.startTimeSpin = spin1

        label2 = QtWidgets.QLabel("结束时刻")
        spin2 = QtWidgets.QSpinBox()
        spin2.setSingleStep(1)
        spin2.setRange(0, 24)
        spin2.setValue(self.graph.UIConfigData()["end_hour"])
        layout.addRow(label2, spin2)
        self.endTimeSpin = spin2

        label3 = QtWidgets.QLabel("默认客车线宽")
        spin3 = QtWidgets.QDoubleSpinBox()
        spin3.setSingleStep(0.5)
        spin3.setValue(self.graph.UIConfigData()["default_keche_width"])
        layout.addRow(label3, spin3)
        self.kecheWidthSpin=spin3

        label4 = QtWidgets.QLabel("默认货车线宽")
        spin4 = QtWidgets.QDoubleSpinBox()
        spin4.setSingleStep(0.5)
        spin4.setValue(self.graph.UIConfigData()["default_huoche_width"])
        layout.addRow(label4, spin4)
        self.huocheWidthSpin = spin4

        label7 = QtWidgets.QLabel("横轴每像素秒数")
        spin7 = QtWidgets.QDoubleSpinBox()
        spin7.setSingleStep(1)
        spin7.setRange(0, 240)
        spin7.setValue(self.graph.UIConfigData()["seconds_per_pix"])
        layout.addRow(label7, spin7)
        self.seconds_per_pix_spin=spin7

        label8 = QtWidgets.QLabel("纵轴每像素秒数")
        spin8 = QtWidgets.QDoubleSpinBox()
        spin8.setSingleStep(1)
        spin8.setRange(0, 240)
        spin8.setValue(self.graph.UIConfigData()["seconds_per_pix_y"])
        layout.addRow(label8, spin8)
        self.seconds_per_pix_y_spin = spin8

        label9 = QtWidgets.QLabel("纵轴每公里像素")
        spin9 = QtWidgets.QDoubleSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(0, 20)
        spin9.setValue(self.graph.UIConfigData()["pixes_per_km"])
        layout.addRow(label9, spin9)
        self.pixes_per_km_spin = spin9

        label9 = QtWidgets.QLabel("最低粗线等级")
        spin9 = QtWidgets.QSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(0, 20)
        spin9.setValue(self.graph.UIConfigData()["bold_line_level"])
        layout.addRow(label9, spin9)
        self.bold_line_level_spin = spin9

        label9 = QtWidgets.QLabel("每小时纵线数")
        spin9 = QtWidgets.QSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(1, 20)
        spin9.setValue(60 / (self.graph.UIConfigData()["minutes_per_vertical_line"]) - 1)
        layout.addRow(label9, spin9)
        self.vertical_lines_per_hour_spin = spin9

        label10 = QtWidgets.QLabel("纵坐标标尺")
        combo = QtWidgets.QComboBox()
        self.ordinateCombo = combo
        self.setOrdinateCombo()
        self.ordinateCombo = combo#todo
        layout.addRow(label10, combo)

        check = QtWidgets.QCheckBox()
        check.setChecked(self.graph.UIConfigData().setdefault('showFullCheci', False))
        layout.addRow("显示完整车次", check)
        self.showFullCheciCheck = check

        vlayout.addLayout(layout)

        label = QtWidgets.QLabel("运行图说明或备注")
        vlayout.addWidget(label)
        textEdit = QtWidgets.QTextEdit()
        textEdit.setText(self.graph.markdown())
        self.noteEdit = textEdit
        vlayout.addWidget(textEdit)

        btn1 = QtWidgets.QPushButton("确定")
        btn1.clicked.connect(self._applyConfig)#todo
        btn2 = QtWidgets.QPushButton("默认")
        btn2.clicked.connect(self._clearConfig)#todo
        btnlay = QtWidgets.QHBoxLayout()
        btnlay.addWidget(btn1)
        btnlay.addWidget(btn2)

        vlayout.addLayout(btnlay)

        self.setLayout(vlayout)

    def setOrdinateCombo(self):
        combo = self.ordinateCombo
        combo.clear()
        combo.addItem("按里程")
        for ruler in self.graph.rulers():
            combo.addItem(ruler.name())
        ordinate = self.graph.ordinateRuler()
        if ordinate is None:
            combo.setCurrentIndex(0)
        else:
            combo.setCurrentText(ordinate.name())

    def setData(self):
        UIDict = self.graph.UIConfigData()
        self.startTimeSpin.setValue(UIDict["start_hour"])
        self.endTimeSpin.setValue(UIDict["end_hour"])
        self.kecheWidthSpin.setValue(UIDict["default_keche_width"])
        self.huocheWidthSpin.setValue(UIDict["default_huoche_width"])
        self.seconds_per_pix_spin.setValue(UIDict["seconds_per_pix"])
        self.seconds_per_pix_y_spin.setValue(UIDict["seconds_per_pix_y"])
        self.pixes_per_km_spin.setValue(UIDict["pixes_per_km"])
        self.bold_line_level_spin.setValue(UIDict["bold_line_level"])
        self.vertical_lines_per_hour_spin.setValue(60 / (UIDict["minutes_per_vertical_line"]) - 1)
        self.setOrdinateCombo()
        self.showFullCheciCheck.setChecked(UIDict["showFullCheci"])
        self.noteEdit.setPlainText(self.graph.markdown())

    def _applyConfig(self):
        UIDict = self.graph.UIConfigData()

        repaint = False

        if self.startTimeSpin.value() != UIDict["start_hour"]:
            UIDict["start_hour"] = self.startTimeSpin.value()
            repaint = True
        if self.endTimeSpin.value()!=UIDict["end_hour"]:
            UIDict["end_hour"] = self.endTimeSpin.value()
            repaint = True
        UIDict["default_keche_width"] = self.kecheWidthSpin.value()
        UIDict["default_huoche_width"] = self.huocheWidthSpin.value()
        if self.seconds_per_pix_spin.value() != UIDict["seconds_per_pix"]:
            UIDict["seconds_per_pix"] = self.seconds_per_pix_spin.value()
            repaint = True
        if self.seconds_per_pix_y_spin.value() != UIDict["seconds_per_pix_y"]:
            UIDict["seconds_per_pix_y"] = self.seconds_per_pix_y_spin.value()
            repaint = True
        if self.pixes_per_km_spin.value() != UIDict["pixes_per_km"]:
            UIDict["pixes_per_km"] = self.pixes_per_km_spin.value()
            repaint = True
        if self.bold_line_level_spin.value() != UIDict["bold_line_level"]:
            UIDict["bold_line_level"] = self.bold_line_level_spin.value()
            repaint = True
        minutes_per_vertical_line = 60/(self.vertical_lines_per_hour_spin.value()+1)
        if minutes_per_vertical_line != UIDict["minutes_per_vertical_line"]:
            UIDict["minutes_per_vertical_line"] = minutes_per_vertical_line
            repaint = True
        if self.ordinateCombo.currentIndex() == 0:
            ruler = None
        else:
            ruler = self.graph.line.rulerByName(self.ordinateCombo.currentText())
        if ruler is not self.graph.ordinateRuler():
            self.graph.setOrdinateRuler(ruler)
            repaint = True
        if self.showFullCheciCheck.isChecked() != UIDict["showFullCheci"]:
            UIDict["showFullCheci"] = self.showFullCheciCheck.isChecked()
            repaint = True
        self.graph.setMarkdown(self.noteEdit.toPlainText())

        dialog = QtWidgets.QMessageBox()
        btnOk = QtWidgets.QPushButton("保存默认(&D)")
        btnOk.clicked.connect(self.SaveSystemConfig.emit)
        btnCancel = QtWidgets.QPushButton("仅运行图(&G)")
        dialog.addButton(btnOk, dialog.AcceptRole)
        dialog.addButton(btnCancel, dialog.RejectRole)
        dialog.setText("请选择将以上设置保存为系统默认设置，还是仅应用到本运行图？")
        dialog.setWindowTitle(self.windowTitle())
        dialog.exec_()
        if repaint:
            self.RepaintGraph.emit()

    def _clearConfig(self):
        """
        将所有设置恢复为默认设置
        """
        r = QtWidgets.QMessageBox.question(self, "提示",
                                           "确定将所有设置恢复为系统默认？当前运行图的有关设置将丢失。",
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                           QtWidgets.QMessageBox.Yes)

        if r == QtWidgets.QMessageBox.Rejected or r == QtWidgets.QMessageBox.NoButton:
            return

        keys = (
            "seconds_per_pix",
            "seconds_per_pix_y",
            "pixes_per_km",
            "default_keche_width",
            "default_huoche_width",
            "start_hour",
            "end_hour",
            "minutes_per_vertical_line",
            "bold_line_level",
        )

        buff = self.graph.readSystemConfig()
        for key in keys:
            self.graph.UIConfigData()[key] = buff[key]
        self.setData()

"""
抽离运行图设置面板。组织逻辑暂时保持不变。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .data.graph import Graph
from .colorWidget import ColorWidget
from .typeDialog import TypeDialog

class ConfigWidget(QtWidgets.QWidget):
    RepaintGraph = QtCore.pyqtSignal()
    def __init__(self,graph:Graph,system:bool=False,parent=None):
        super(ConfigWidget, self).__init__(parent)
        self.system = system
        self.repaint = False
        self.setWindowTitle('运行图设置' if not system else '系统默认设置')
        self.graph = graph
        self.UIDict = self.graph.UIConfigData() if not self.system else self.graph.sysConfigData()
        self.colorWidget = ColorWidget(self.graph, system, self)
        self.typeDialog = TypeDialog(self.graph,system,self)
        self.initWidget()
        self.colorWidget.RepaintGraph.connect(self.setRepaintTrue)

    def setRepaintTrue(self):
        self.repaint=True

    def initWidget(self):
        """
        原main._initConfigWidget。
        """
        vlayout = QtWidgets.QVBoxLayout()
        layout = QtWidgets.QFormLayout()

        label1 = QtWidgets.QLabel("起始时刻")
        spin1 = QtWidgets.QSpinBox()
        spin1.setSingleStep(1)
        spin1.setRange(0, 24)
        spin1.setValue(self.UIDict["start_hour"])
        layout.addRow(label1, spin1)
        self.startTimeSpin = spin1

        label2 = QtWidgets.QLabel("结束时刻")
        spin2 = QtWidgets.QSpinBox()
        spin2.setSingleStep(1)
        spin2.setRange(0, 24)
        spin2.setValue(self.UIDict["end_hour"])
        layout.addRow(label2, spin2)
        self.endTimeSpin = spin2

        label3 = QtWidgets.QLabel("默认客车线宽")
        spin3 = QtWidgets.QDoubleSpinBox()
        spin3.setSingleStep(0.5)
        spin3.setValue(self.UIDict["default_keche_width"])
        layout.addRow(label3, spin3)
        self.kecheWidthSpin=spin3

        label4 = QtWidgets.QLabel("默认货车线宽")
        spin4 = QtWidgets.QDoubleSpinBox()
        spin4.setSingleStep(0.5)
        spin4.setValue(self.UIDict["default_huoche_width"])
        layout.addRow(label4, spin4)
        self.huocheWidthSpin = spin4

        label7 = QtWidgets.QLabel("横轴每像素秒数")
        spin7 = QtWidgets.QDoubleSpinBox()
        spin7.setSingleStep(1)
        spin7.setRange(0, 240)
        spin7.setValue(self.UIDict["seconds_per_pix"])
        layout.addRow(label7, spin7)
        self.seconds_per_pix_spin=spin7

        label8 = QtWidgets.QLabel("纵轴每像素秒数")
        spin8 = QtWidgets.QDoubleSpinBox()
        spin8.setSingleStep(1)
        spin8.setRange(0, 240)
        spin8.setValue(self.UIDict["seconds_per_pix_y"])
        layout.addRow(label8, spin8)
        self.seconds_per_pix_y_spin = spin8

        label9 = QtWidgets.QLabel("纵轴每公里像素")
        spin9 = QtWidgets.QDoubleSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(0, 20)
        spin9.setValue(self.UIDict["pixes_per_km"])
        layout.addRow(label9, spin9)
        self.pixes_per_km_spin = spin9

        label9 = QtWidgets.QLabel("最低粗线等级")
        spin9 = QtWidgets.QSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(-1, 20)
        spin9.setValue(self.UIDict["bold_line_level"])
        layout.addRow(label9, spin9)
        self.bold_line_level_spin = spin9

        label9 = QtWidgets.QLabel("每小时纵线数")
        spin9 = QtWidgets.QSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(1, 20)
        spin9.setValue(60 / (self.UIDict["minutes_per_vertical_line"]) - 1)
        layout.addRow(label9, spin9)
        self.vertical_lines_per_hour_spin = spin9

        if not self.system:
            label10 = QtWidgets.QLabel("纵坐标标尺")
            combo = QtWidgets.QComboBox()
            self.ordinateCombo = combo
            self.setOrdinateCombo()
            self.ordinateCombo = combo
            layout.addRow(label10, combo)

        spin = QtWidgets.QSpinBox()
        spin.setRange(1,20)
        spin.setValue(self.UIDict.setdefault("valid_width",3))
        text = """\
        本功能解决运行线不容易选中的问题。当设置值大于1时，启用扩大选择范围功能，此时运行图铺画效率会有所降低，运行线周围，运行线宽度的设置值倍数被点击都可以选中运行线。
        """
        spin.setToolTip(text)
        self.validWidthSpin = spin
        layout.addRow("有效选择宽度",spin)

        spin = QtWidgets.QSpinBox()
        spin.setRange(0,100)
        spin.setValue(self.UIDict.setdefault("max_passed_stations",3))
        text = "当区间无数据站点超过设定值时，系统自动分成两条运行线。运行线也可以手工管理。"
        spin.setToolTip(text)
        self.maxPassSpin = spin
        layout.addRow("最大跨越站数",spin)

        combo = QtWidgets.QComboBox()
        combo.addItems(('不显示','仅选中车次显示','全部显示'))
        self.markModeCombo = combo
        combo.setCurrentIndex(self.UIDict.setdefault('show_time_mark',1))
        layout.addRow("图中显示时刻",combo)

        check = QtWidgets.QCheckBox()
        check.setChecked(self.UIDict.setdefault('showFullCheci', False))
        layout.addRow("显示完整车次", check)
        self.showFullCheciCheck = check

        check = QtWidgets.QCheckBox()
        check.setChecked(self.UIDict.setdefault("auto_paint",True))
        layout.addRow("自动铺画",check)
        check.setToolTip("若关闭，当运行图发生变更时不会自动铺画，只有手动选择刷新（F5）或者铺画运行图（shitf+F5）时才会重新铺画运行图。建议当运行图较大时关闭。")
        self.autoPaintCheck = check

        check = QtWidgets.QCheckBox()
        check.setChecked(self.UIDict.setdefault('avoid_cover',True))
        layout.addRow('标签自动偏移',check)
        check.setToolTip('当同一站的始发终到标签发生重叠时，自动调整标签高度。')
        self.avoidCoverCheck = check

        self.initGridDialog()
        btnGrid = QtWidgets.QPushButton("设置")
        btnGrid.setMaximumWidth(120)
        btnGrid.clicked.connect(self.gridDialog.exec_)
        layout.addRow('详细尺寸设置',btnGrid)

        btnColor = QtWidgets.QPushButton("设置")
        btnColor.clicked.connect(self.colorWidget.exec_)
        btnColor.setMaximumWidth(120)
        layout.addRow('默认颜色设置',btnColor)

        btnType = QtWidgets.QPushButton('设置')
        btnType.clicked.connect(self.typeDialog.exec_)
        btnType.setMaximumWidth(120)
        layout.addRow('类型管理',btnType)

        vlayout.addLayout(layout)

        if not self.system:
            label = QtWidgets.QLabel("运行图说明或备注")
            vlayout.addWidget(label)
            textEdit = QtWidgets.QTextEdit()
            textEdit.setText(self.graph.markdown())
            self.noteEdit = textEdit
            vlayout.addWidget(textEdit)

        btn1 = QtWidgets.QPushButton("确定")
        btn1.clicked.connect(self._applyConfig)
        btn2 = QtWidgets.QPushButton("默认")
        btn2.clicked.connect(self._clearConfig)
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
        self.UIDict = self.graph.UIConfigData() if not self.system else self.graph.sysConfigData()
        UIDict = self.UIDict
        self.startTimeSpin.setValue(UIDict["start_hour"])
        self.endTimeSpin.setValue(UIDict["end_hour"])
        self.kecheWidthSpin.setValue(UIDict["default_keche_width"])
        self.huocheWidthSpin.setValue(UIDict["default_huoche_width"])
        self.seconds_per_pix_spin.setValue(UIDict["seconds_per_pix"])
        self.seconds_per_pix_y_spin.setValue(UIDict["seconds_per_pix_y"])
        self.pixes_per_km_spin.setValue(UIDict["pixes_per_km"])
        self.bold_line_level_spin.setValue(UIDict["bold_line_level"])
        self.vertical_lines_per_hour_spin.setValue(60 / (UIDict["minutes_per_vertical_line"]) - 1)
        if not self.system:
            self.setOrdinateCombo()
        self.showFullCheciCheck.setChecked(UIDict["showFullCheci"])
        self.markModeCombo.setCurrentIndex(UIDict["show_time_mark"])
        self.validWidthSpin.setValue(UIDict.setdefault('valid_width',3))
        self.maxPassSpin.setValue(UIDict.setdefault("max_passed_stations",3))
        self.autoPaintCheck.setChecked(UIDict.setdefault('auto_paint',True))
        self.avoidCoverCheck.setChecked(UIDict.setdefault('avoid_cover',True))
        if not self.system:
            self.noteEdit.setPlainText(self.graph.markdown())
        self.setGridDialogData()
        self.colorWidget.setData()
        self.typeDialog.setData()

    def initGridDialog(self):
        """
        self.margins = {
            "left_white": 15,  # 左侧白边，不能有任何占用的区域
            "right_white": 10,
            "left": 325,
            "up": 90,
            "down": 90,
            "right": 170,
            "label_width": 100,
            "mile_label_width": 50,
            "ruler_label_width": 100,
        }
        """
        UIDict = self.UIDict
        self.gridDialog = QtWidgets.QDialog(self)
        self.gridDialog.setWindowTitle('底图设置')
        layout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()
        label = QtWidgets.QLabel("本对话框可设置运行图边距、格线粗细，设置完毕后在“运行图设置”面板点击确定才会生效。")
        label.setWordWrap(True)
        layout.addWidget(label)

        spin = QtWidgets.QDoubleSpinBox(self)
        self.defaultWidthSpin = spin
        spin.setRange(0.1,5)
        spin.setSingleStep(0.5)
        spin.setDecimals(1)
        spin.setValue(UIDict.setdefault("default_grid_width",1))
        flayout.addRow("细格线宽度",spin)

        spin = QtWidgets.QDoubleSpinBox(self)
        self.boldWidthSpin = spin
        spin.setRange(0.1, 5)
        spin.setSingleStep(0.5)
        spin.setDecimals(1)
        spin.setValue(UIDict.setdefault("bold_grid_width", 2.5))
        flayout.addRow("粗格线宽度", spin)

        spin = QtWidgets.QSpinBox(self)
        self.rulerLabelSpin = spin
        spin.setRange(20,200)
        spin.setValue(UIDict['margins']['ruler_label_width'])
        flayout.addRow('排图标尺栏宽度',spin)

        spin = QtWidgets.QSpinBox(self)
        self.mileLabelSpin = spin
        spin.setRange(20,200)
        spin.setValue(UIDict['margins']['mile_label_width'])
        flayout.addRow('延长公里栏宽度',spin)

        spin = QtWidgets.QSpinBox(self)
        self.stationLabelSpin = spin
        spin.setRange(20, 200)
        spin.setValue(UIDict['margins']['label_width'])
        flayout.addRow('站名栏宽度', spin)

        spin = QtWidgets.QSpinBox(self)
        self.topBottomLabelSpin = spin
        spin.setRange(20, 200)
        spin.setValue(UIDict['margins']['up'])
        flayout.addRow('上下边距', spin)

        spin = QtWidgets.QSpinBox(self)
        self.leftRightLabelSpin = spin
        spin.setRange(20, 200)
        spin.setValue(UIDict['margins']['right']-UIDict['margins']['right_white']-UIDict['margins']['label_width'])
        flayout.addRow('左右图边至站名栏距离', spin)

        spin = QtWidgets.QSpinBox(self)
        self.startLabelSpin = spin
        spin.setRange(0,100)
        spin.setValue(UIDict.setdefault('start_label_height',30))
        flayout.addRow('开始标签高度',spin)

        spin = QtWidgets.QSpinBox(self)
        self.endLabelSpin = spin
        spin.setRange(0,100)
        spin.setValue(UIDict.setdefault('end_label_height',18))
        flayout.addRow('结束标签高度',spin)

        spin = QtWidgets.QSpinBox(self)
        self.baseHeightSpin = spin
        spin.setRange(1, 1000)
        spin.setValue(UIDict.setdefault('base_label_height', 15))
        flayout.addRow('基准标签高度', spin)

        spin = QtWidgets.QSpinBox(self)
        self.stepHeightSpin = spin
        spin.setRange(1,1000)
        spin.setValue(UIDict.setdefault('step_label_height', 15))
        flayout.addRow('标签层级高度', spin)

        spin = QtWidgets.QSpinBox(self)
        self.tableRowSpin = spin
        spin.setRange(15,60)
        spin.setValue(UIDict.setdefault('table_row_height',30))
        flayout.addRow('默认表格行高',spin)

        layout.addLayout(flayout)
        self.gridDialog.setLayout(layout)
        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(self.gridDialog.close)
        layout.addWidget(btnClose)

    def setGridDialogData(self):
        """
        """
        UIDict = self.UIDict
        self.defaultWidthSpin.setValue(UIDict.setdefault('default_grid_width',1))
        self.boldWidthSpin.setValue(UIDict.setdefault('bold_grid_width',2))
        self.rulerLabelSpin.setValue(UIDict['margins']['ruler_label_width'])
        self.mileLabelSpin.setValue(UIDict['margins']['mile_label_width'])
        self.stationLabelSpin.setValue(UIDict['margins']['label_width'])
        self.topBottomLabelSpin.setValue(UIDict['margins']['up'])
        self.leftRightLabelSpin.setValue(UIDict['margins']['right']-UIDict['margins']['right_white']-UIDict['margins']['label_width'])
        self.startLabelSpin.setValue(UIDict['start_label_height'])
        self.endLabelSpin.setValue(UIDict['end_label_height'])
        self.tableRowSpin.setValue(UIDict['table_row_height'])
        self.baseHeightSpin.setValue(UIDict['base_label_height'])
        self.stepHeightSpin.setValue(UIDict['step_label_height'])


    def _applyConfig(self):
        UIDict = self.UIDict

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
        if not self.system:
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
        if self.markModeCombo.currentIndex() != UIDict["show_time_mark"]:
            UIDict["show_time_mark"] = self.markModeCombo.currentIndex()
            repaint = True
        UIDict['auto_paint'] = self.autoPaintCheck.isChecked()
        if self.validWidthSpin.value() != UIDict['valid_width']:
            UIDict['valid_width'] = self.validWidthSpin.value()
            repaint = True
        if self.maxPassSpin.value() != UIDict['max_passed_stations']:
            UIDict['max_passed_stations'] = self.maxPassSpin.value()
            repaint = True
        if self.avoidCoverCheck.isChecked() != UIDict['avoid_cover']:
            UIDict['avoid_cover'] = self.avoidCoverCheck.isChecked()
            repaint = True
        repaint = repaint or self._applyGridDialogConfig()
        if not self.system:
            self.graph.setMarkdown(self.noteEdit.toPlainText())
        self.repaint = repaint
        self.colorWidget.apply_color()
        self.typeDialog.apply()

        if self.repaint:
            self.RepaintGraph.emit()

        if self.system:
            self.graph.saveSysConfig()

    def _applyGridDialogConfig(self)->bool:
        """
        应用对话框数据，返回是否要重新铺画
        """
        repaint = False
        UIDict = self.UIDict
        if self.defaultWidthSpin.value() != UIDict['default_grid_width']:
            UIDict['default_grid_width'] = self.defaultWidthSpin.value()
            repaint = True
        if self.boldWidthSpin.value() != UIDict['bold_grid_width']:
            UIDict['bold_grid_width'] = self.boldWidthSpin.value()
            repaint = True
        if self.startLabelSpin.value() != UIDict['start_label_height']:
            UIDict['start_label_height'] = self.startLabelSpin.value()
            repaint = True
        if self.endLabelSpin.value() != UIDict['end_label_height']:
            UIDict['end_label_height'] = self.endLabelSpin.value()
            repaint = True
        if self.baseHeightSpin.value() != UIDict['base_label_height']:
            UIDict['base_label_height'] = self.baseHeightSpin.value()
            repaint = True
        if self.stepHeightSpin.value() != UIDict['step_label_height']:
            UIDict['step_label_height'] = self.stepHeightSpin.value()
            repaint = True
        UIDict['table_row_height'] = self.tableRowSpin.value()
        repaint = repaint or self.graph.setMargin(
            self.rulerLabelSpin.value(),
            self.mileLabelSpin.value(),
            self.stationLabelSpin.value(),
            self.leftRightLabelSpin.value(),
            self.topBottomLabelSpin.value(),
            system=self.system
        )
        return repaint

    def _clearConfig(self):
        """
        将所有设置恢复为默认设置.
        """
        r = QtWidgets.QMessageBox.question(self, "提示",
                                           "确定将所有设置恢复为系统默认？当前运行图的有关设置将丢失。",
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                           QtWidgets.QMessageBox.Yes)

        if r == QtWidgets.QMessageBox.Rejected or r == QtWidgets.QMessageBox.NoButton:
            return

        self.graph.resetGraphConfigFromConfigWidget()
        self.setData()

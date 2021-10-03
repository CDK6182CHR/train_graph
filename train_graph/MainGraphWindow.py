"""
拟使用的正式mainwindow.不用Designer.
copyright (c) mxy 2018
1.4版本config架构修改方案：
1. 系统设置改由数据域的graph模块负责管理，system.json由mainGraphWindow负责管理，GraphicsWidget不再管理。
2. 将Margin集成进入默认的系统设置。
3. 新增默认系统设置停靠面板（sysWidget），负责管理默认系统设置，不再允许通过configWidget修改默认系统设置。
4. 系统配置文件分裂为config.json和system.json。system.json目前仅负责记录last_file, default_file两项参数；config.json接管老版本config.json的其他功能。
5. 新增系统内置的默认系统设置，用于兼容老版本，补全settings.json中所缺数据。当settings.json文件发生错误时，调用本函数初始化，而不是抛出异常。

1.4版本系统初始化修改方案：
1. 初始化打开文件由mainGraphWindow负责管理，GraphicsWidget不再管理。
2. 允许初始化时直接打开文件。

右键菜单参考
https://blog.csdn.net/qq_37233607/article/details/78649151
"""
import sys, time
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt
from .data.graph import Graph,Ruler,Line,Train
from datetime import datetime, timedelta
from .forbidWidget import ForbidTabWidget
from .rulerWidget import RulerWidget
from .currentWidget import CurrentWidget
from .lineWidget import LineWidget
from .trainWidget import TrainWidget
from .trainFilter import TrainFilter
from .configWidget import ConfigWidget
from .typeWidget import TypeWidget
from .trainInfoWidget import TrainInfoWidget
from .pyETRCExceptions import *
from .circuitWidget import CircuitWidget
import json
from .GraphicWidget import GraphicsWidget, TrainEventType
from .rulerPaint import rulerPainter
from .lineDB import LineDB
from .intervalWidget import IntervalWidget
from .intervalCountDialog import IntervaLCountDialog
from .intervalTrainDialog import IntervalTrainDialog
from .detectWidget import DetectWidget
from .changeStationDialog import ChangeStationDialog
from .batchChangeStationDialog import BatchChangeStationDialog
from .trainComparator import TrainComparator
from .correctionWidget import CorrectionWidget
from .stationTimetable import StationTimetable
from .trainTimetable import TrainTimetable
from .interactiveTimetable import InteractiveTimetable
from .helpDialog import HelpDialog
from .changeTrainIntervalDialog import ChangeTrainIntervalDialog
from .exchangeIntervalDialog import ExchangeIntervalDialog
from .importTrainDialog import ImportTrainDialog
from .linedb.lineLibWidget import LineLibWidget
from .dialogAdapter import DialogAdapter
from .graphDiffDialog import GraphDiffDialog
from .readRulerWizard import ReadRulerWizard
from .utility import QRibbonToolBar, PEToolButton, PEDockButton
from .rulerTable import RulerTable
import traceback
from . import resource

import cgitb

cgitb.enable(format='text')

system_file = "system.json"


class MainGraphWindow(QtWidgets.QMainWindow):

    def __init__(self, filename=None, graph=None):
        super().__init__()
        start = time.time()
        self.name = "pyETRC列车运行图系统"
        self.version = "V3.3.3"
        self.title = f"{self.name} {self.version}"  # 一次commit修改一次版本号
        self.date = '20211003'
        self.release = 'R51'  # 发布时再改这个
        self._system = None
        self.updating = True
        self.setWindowTitle(f"{self.title}   正在加载")
        self.setWindowIcon(QtGui.QIcon(':/icon.ico'))
        if not graph:
            self.showMaximized()
        self._readSystemSetting()

        self._selectedTrain = None
        self.graph = graph
        if self.graph is None:
            self.graph = Graph()
            self.graph.setSysVersion(self.version)
            self._initGraph(filename)
        self.GraphWidget = GraphicsWidget(self.graph, self)
        self.GraphWidget.menu.triggered.connect(self._shortcut_action_triggered)

        self.setWindowTitle(f"{self.title}   {self.graph.filename if self.graph.filename else '新运行图'}")

        self.showFilter = TrainFilter(self.graph, self)
        self.showFilter.FilterChanged.connect(self._train_show_filter_ok)

        self.GraphWidget.showNewStatus.connect(self.statusOut)
        self.GraphWidget.focusChanged.connect(self.on_focus_changed)

        self.lineDockWidget = None  # type:QtWidgets.QDockWidget
        self.configDockWidget = None  # type:QtWidgets.QDockWidget
        self.sysDockWidget = None  # type:QtWidgets.QDockWidget
        self.currentDockWidget = None  # type:QtWidgets.QDockWidget
        self.typeDockWidget = None  # type:QtWidgets.QDockWidget
        self.trainDockWidget = None  # type:QtWidgets.QDockWidget
        self.rulerDockWidget = None  # type:QtWidgets.QDockWidget
        self.guideDockWidget = None  # type:QtWidgets.QDockWidget
        self.forbidDockWidget = None  # type:QtWidgets.QDockWidget
        self.circuitDockWidget = None  # type:QtWidgets.QDockWidget
        self.trainInfoDockWidget = None  # type:QtWidgets.QDockWidget
        self.trainTimetableDockWidget = None  # type:QtWidgets.QDockWidget
        self.interactiveTimetableDockWidget = None  # type:QtWidgets.QDockWidget
        self.to_repaint = False

        self.action_widget_dict = {}

        self._initUI()
        self._checkGraph()
        self.rulerPainter = None
        self.GraphWidget.lineDoubleClicked.connect(lambda:self.trainTimetableDockWidget.setVisible(True))
        self.updating=False
        end = time.time()
        print("系统初始化用时：",end-start)

    def _readSystemSetting(self):
        """
        1.4版本新增函数。
        """
        try:
            with open(system_file, encoding='utf-8', errors='ignore') as fp:
                self._system = json.load(fp)
        except:
            self._system = {}
        self._checkSystemSetting()

    def _checkSystemSetting(self):
        """
        1.4版本新增函数。
        """
        system_default = {
            "last_file": '',
            "default_file": 'sample.pyetgr',
            "dock_show": {}
        }
        system_default.update(self._system)
        self._system = system_default

    def _saveSystemSetting(self):
        """
        1.4版本新增函数
        """
        with open(system_file, 'w', encoding='utf-8', errors='ignore') as fp:
            json.dump(self._system, fp, ensure_ascii=False)

    def _initGraph(self, filename=None):
        """
        1.4版本新增函数。按照给定文件、上次打开的文件、默认文件的顺序，初始化系统内置graph。
        """
        for n in (filename, self._system["last_file"], self._system["default_file"]):
            if not n:
                continue
            try:
                self.graph.loadGraph(n)
            except:
                pass
            else:
                return

    def currentTrain(self) -> Train:
        """
        2019.06.06新增函数。将选中列车作为main窗口封装的属性之一。
        增加的动机：GraphWidget.selectedTrain无法满足无运行线车次的选择状态记录功能。
        """
        return self._selectedTrain

    def setCurrentTrain(self, train: Train):
        self._selectedTrain = train

    def _initUI(self):
        self.statusOut("系统正在初始化……")
        self.setCentralWidget(self.GraphWidget)

        self._initDockFrames()
        self._initMenuBar()
        self._initToolBar()

        self._initDockWidgetContents()
        self._initDockShow()

        self.statusOut("就绪")

    def _initDockFrames(self):
        self._initTrainDock()
        self._initLineDock()
        self._initConfigDock()
        self._initRulerDock()
        self._initTypeDock()
        self._initCurrentDock()
        self._initSysDock()
        self._initForbidDock()
        self._initCircuitDock()
        self._initTrainInfoDock()
        self._initTrainTimetableDock()
        self._initInteractiveTimetableDock()
        self.action_widget_dict = {
            '线路编辑': self.lineDockWidget,
            '车次编辑': self.trainDockWidget,
            '选中车次设置': self.currentDockWidget,
            '运行图设置': self.configDockWidget,
            '系统默认设置': self.sysDockWidget,
            '显示类型设置': self.typeDockWidget,
            '标尺编辑': self.rulerDockWidget,
            '天窗编辑': self.forbidDockWidget,
            '交路编辑': self.circuitDockWidget,
            '车次信息': self.trainInfoDockWidget,
            '车次时刻表': self.trainTimetableDockWidget,
            '交互式时刻表':self.interactiveTimetableDockWidget,
        }
        self.setDockOptions(QtWidgets.QMainWindow.VerticalTabs|QtWidgets.QMainWindow.AllowTabbedDocks
                            # |QtWidgets.QMainWindow.ForceTabbedDocks
                            )
        self.setDocumentMode(True)
        self.setTabShape(QtWidgets.QTabWidget.Triangular)

    def _initDockWidgetContents(self):
        self._initTrainWidget()
        self._initConfigWidget()
        self._initLineWidget()
        self._initRulerWidget()
        self._initTypeWidget()
        self._initCircuitWidget()  # circuit必须在current前初始化，后者有前者的slot连接。
        self._initCurrentWidget()
        self._initSysWidget()
        self._initForbidWidget()
        self._initTrainInfoWidget()
        self._initTrainTimetableWidget()
        self._initInteractiveTimetableWidget()

    def _initDockShow(self):
        """
        1.4版本新增，初始化停靠面板是否显示。
        """
        for key, dock in self.action_widget_dict.items():
            dock.setVisible(self._system['dock_show'].setdefault(key, False))

    def _refreshDockWidgets(self):
        """
        聚合所有停靠面板的更新信息调用。由刷新命令调用。
        要逐步把所有更新替换为专用更新函数，避免创建新对象。
        2019.07.19新增要求：打开新运行图也调用此函数。
        """
        self.statusOut('停靠面板刷新开始')
        self.trainWidget.setData()
        self.configWidget.setData()
        self.lineWidget.setData()
        self.rulerWidget.setData()
        self.typeWidget._setTypeList()
        self.currentWidget.setData(None)
        self.sysWidget.setData()
        self.forbidWidget.setData()
        self.circuitWidget.setData()
        self.trainInfoWidget.setData()
        self.trainTimetableWidget.setData(None)
        self.interactiveTimetableWidget.setData()
        self._refreshSelectedTrainCombo()
        if self.rulerPainter is not None:
            self.rulerPainter.refresh()
        self.statusOut('停靠面板刷新完毕')

    def _shortcut_action_triggered(self,action:QtWidgets.QAction):
        """
        2019.07.14新增，连接右键菜单
        """
        action_map = {
            '标尺对照(Ctrl+W)':self._check_ruler_from_menu,
            '两车次运行对照(Ctrl+Shift+Z)':self._train_compare,
            '车次事件表(Ctrl+Z)':self._train_event_out,
            '时刻调整(Ctrl+A)':self._adjust_train_time,
            '时刻重排(Ctrl+V)':self._correction_timetable,
            '批量复制(Ctrl+Shift+A)':self._batch_copy_train,
            '区间换线(Ctrl+5)':self._interval_exchange,
            '推定时刻(Ctrl+2)':self._detect_pass_time,
            '添加车次(Ctrl+Shift+C)':self._add_train_from_list,
            '标尺排图向导(Ctrl+R)':self._add_train_by_ruler,
        }
        try:
            action_map[action.text()]()
        except KeyError:
            print("mainGraphWindow::shortcut_action_triggered: 未定义的操作",action.text())

    def _initForbidDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("天窗编辑")
        dock.visibilityChanged.connect(lambda: self._dock_visibility_changed("天窗编辑", dock))
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setVisible(False)
        self.forbidDockWidget = dock

    def _initCircuitDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle('交路编辑')
        dock.visibilityChanged.connect(lambda: self._dock_visibility_changed('交路编辑', dock))
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setVisible(False)
        self.circuitDockWidget = dock

    def _initTrainInfoDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle('车次信息')
        dock.visibilityChanged.connect(lambda: self._dock_visibility_changed('车次信息', dock))
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        dock.setVisible(False)
        self.trainInfoDockWidget = dock

    def _initTrainTimetableDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle('车次时刻表')
        dock.visibilityChanged.connect(lambda: self._dock_visibility_changed('车次时刻表', dock))
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setVisible(False)
        self.trainTimetableDockWidget = dock

    def _initTrainTimetableWidget(self):
        widget = TrainTimetable(self.graph, self)
        self.trainTimetableDockWidget.setWidget(widget)
        self.trainTimetableWidget = widget

    def _initInteractiveTimetableDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle('交互式时刻表')
        dock.visibilityChanged.connect(lambda:self._dock_visibility_changed('交互式时刻表',dock))
        self.addDockWidget(Qt.RightDockWidgetArea,dock)
        dock.setVisible(False)
        self.interactiveTimetableDockWidget = dock

    def _initInteractiveTimetableWidget(self):
        widget = InteractiveTimetable(self.graph,self)
        self.interactiveTimetableDockWidget.setWidget(widget)
        self.interactiveTimetableWidget = widget
        widget.trainTimetableChanged.connect(self._interactive_timetable_changed)

    def _initForbidWidget(self):
        widget = ForbidTabWidget(self.graph.line)
        self.forbidWidget = widget
        self.forbidDockWidget.setWidget(widget)
        widget.showForbidChanged.connect(self.GraphWidget.on_show_forbid_changed)
        widget.currentShowedChanged.connect(self.GraphWidget.show_forbid)

    def _initCircuitWidget(self):
        widget = CircuitWidget(self.graph)
        self.circuitWidget = widget
        self.circuitDockWidget.setWidget(widget)

    def _initTrainInfoWidget(self):
        widget = QtWidgets.QScrollArea()
        w = TrainInfoWidget(self.graph, self)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        widget.setWidgetResizable(True)
        widget.setWidget(w)
        self.trainInfoWidget = w
        self.trainInfoDockWidget.setWidget(widget)
        w.editTrain.connect(self._train_table_doubleClicked)
        w.showTimeTable.connect(self._show_timetable)

    def _initGuideDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("标尺排图向导")
        dock.visibilityChanged.connect(lambda: self._dock_visibility_changed("标尺排图向导", dock))
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.close()
        self.guideDockWidget = dock

    def _initGuideWidget(self):
        widget = rulerPainter(self.GraphWidget)
        widget.trainOK.connect(self._updateCurrentTrainRelatedWidgets)
        self.guideDockWidget.setWidget(widget)

    def _initSysDock(self):
        colorDock = QtWidgets.QDockWidget()
        self.sysDockWidget = colorDock
        colorDock.setWindowTitle("系统默认设置")
        colorDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("系统默认设置", colorDock))

        self.addDockWidget(Qt.LeftDockWidgetArea, colorDock)
        colorDock.setVisible(False)

    def _initSysWidget(self):
        sysWidget = ConfigWidget(self.graph, True, self)
        self.sysWidget = sysWidget
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(sysWidget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sysDockWidget.setWidget(scroll)

    def _initCurrentDock(self):
        currentDock = QtWidgets.QDockWidget()
        currentDock.setWindowTitle("选中车次设置")
        currentDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("选中车次设置", currentDock))
        self.currentDockWidget = currentDock
        self.addDockWidget(Qt.RightDockWidgetArea, currentDock)
        currentDock.resize(280, currentDock.height())
        currentDock.setVisible(False)

    def _initCurrentWidget(self):
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        widget = CurrentWidget(self.graph)
        self.currentWidget = widget

        scroll.setWidget(widget)

        self.currentDockWidget.setWidget(scroll)
        self.currentDockWidget.visibilityChanged.connect(
            lambda: self.currentWidget.setData(self.currentTrain()))
        self.trainInfoDockWidget.visibilityChanged.connect(
            lambda: self.trainInfoWidget.setData(self.currentTrain())
        )
        self.trainTimetableDockWidget.visibilityChanged.connect(
            lambda: self.trainTimetableWidget.setData(self.currentTrain())
        )
        self.interactiveTimetableDockWidget.visibilityChanged.connect(
            lambda: self.interactiveTimetableWidget.setData(self.currentTrain())
        )

        # connect slots
        widget.checkCurrentTrainRuler.connect(self._check_ruler)
        widget.correctCurrentTrainTable.connect(self._correction_timetable)
        widget.showCurrentTrainEvents.connect(self._train_event_out)
        widget.showStatus.connect(self.statusOut)
        widget.currentTrainApplied.connect(self._current_applied)
        widget.currentTrainDeleted.connect(self._del_train_from_current)
        widget.editCurrentTrainCircuit.connect(self.circuitWidget.editCircuit)
        widget.addCircuitFromCurrent.connect(self.circuitWidget.add_circuit_from_current)
        self.circuitWidget.dialog.CircuitChangeApplied.connect(lambda x:widget.setData(widget.train))
        # 从当前车次列表添加交路

    def _current_applied(self, train: Train):
        """
        2019.06.30新增。将currentWidget中与main有关的全部移到这里。
        """
        if train.trainType() not in self.graph.typeList:
            self.graph.typeList.append(train.trainType())
            self.typeWidget._setTypeList()

        self.GraphWidget.repaintTrainLine(train)

        if not self.graph.trainExisted(train):
            self.graph.addTrain(train)
            self.trainWidget.addTrain(train)
        else:
            self.trainWidget.updateRowByTrain(train)
        self._updateCurrentTrainRelatedWidgets(train)
        self._refreshSelectedTrainCombo()
        self.statusOut("车次信息更新完毕")

    def _del_train_from_current(self, train: Train):
        tableWidget = self.trainWidget.trainTable
        isOld = self.graph.trainExisted(train)
        self.GraphWidget._line_un_selected()

        if isOld:
            # 旧车次，清除表格中的信息
            self.trainWidget.delTrain(train)
        self.GraphWidget.delTrainLine(train)
        self.graph.delTrain(train)

    def _check_ruler(self, train: Train):
        """
        检查对照标尺和实际时刻表.
        0-通通
        1-起通
        2-通停
        3-起停
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"标尺对照*{train.fullCheci()}")
        dialog.resize(800, 600)

        layout = QtWidgets.QVBoxLayout()
        rulerCombo = QtWidgets.QComboBox()
        rulerCombo.addItem("（空）")

        for ruler in self.graph.rulers():
            rulerCombo.addItem(ruler.name())
        layout.addWidget(rulerCombo)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(8)
        tableWidget.setHorizontalHeaderLabels(['区间', '标准', '起', '停', '实际', '均速', '附加', '差时'])

        rulerCombo.currentTextChanged.connect(lambda x: self._change_ruler_reference(tableWidget, x))

        tableWidget.setColumnWidth(0, 150)
        tableWidget.setColumnWidth(1, 60)
        tableWidget.setColumnWidth(2, 60)
        tableWidget.setColumnWidth(3, 60)
        tableWidget.setColumnWidth(4, 60)
        tableWidget.setColumnWidth(5, 80)
        tableWidget.setColumnWidth(6, 60)
        tableWidget.setColumnWidth(7, 60)

        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

        former = ""
        former_time = []
        for name, ddsj, cfsj in train.station_infos():
            # 这里填入车次信息，不填标尺信息
            # dir_ = Line.DownVia if train.stationDown(name,self.graph) else Line.UpVia
            if not former:
                if self.graph.stationInLine(name):
                    former = name
                    former_time = [ddsj, cfsj]
                continue

            if not self.graph.stationInLine(name):
                continue

            row = tableWidget.rowCount()
            tableWidget.insertRow(tableWidget.rowCount())
            tableWidget.setRowHeight(row, self.graph.UIConfigData()['table_row_height'])

            interval_str = f"{former}->{name}"
            item = QtWidgets.QTableWidgetItem(interval_str)
            tableWidget.setItem(row, 0, item)
            item.setData(-1, [former, name])

            dt = (ddsj - former_time[1]).seconds
            dt_str = "%02d:%02d" % (dt//60, dt % 60)
            item = QtWidgets.QTableWidgetItem(dt_str)
            item.setData(-1, dt)
            tableWidget.setItem(row, 4, item)

            appendix = ""
            appendix_value = 0
            if former_time[0] != former_time[1]:
                appendix += "起"
                appendix_value += 1
            elif train.isSfz(former):
                appendix += "始"
                appendix_value += 1

            if ddsj != cfsj:
                appendix += "停"
                appendix_value += 2
            elif train.isZdz(name):
                appendix += "终"
                appendix_value += 2

            item = QtWidgets.QTableWidgetItem(appendix)
            tableWidget.setItem(row, 6, item)
            item.setData(-1, appendix_value)

            mile = self.graph.gapBetween(former, name)
            try:
                speed = 1000 * mile / dt * 3.6
                speed_str = "%.2f" % speed

            except ZeroDivisionError:
                speed_str = "NA"
            item = QtWidgets.QTableWidgetItem(speed_str)
            tableWidget.setItem(row, 5, item)

            former = name
            former_time = [ddsj, cfsj]

        layout.addWidget(tableWidget)
        dialog.setLayout(layout)
        dialog.show()
        dialog.exec_()

    def _change_ruler_reference(self, tableWidget: QtWidgets.QTableWidget, name: str):
        ruler = self.graph.line.rulerByName(name)
        if name == '（空）' or ruler is None:
            ruler = Ruler()

        for row in range(tableWidget.rowCount()):
            former = tableWidget.item(row, 0).data(-1)[0]
            latter = tableWidget.item(row, 0).data(-1)[1]
            appendix = tableWidget.item(row, 6).data(-1)
            uiji = tableWidget.item(row, 4).data(-1)  # 实际区间用时

            note_item = tableWidget.item(row, 7)
            if note_item is not None:
                note_item.setText("")

            for c in range(8):
                try:
                    item: QtWidgets.QTableWidgetItem = tableWidget.item(row, c)
                    item.setBackground(QtGui.QBrush(Qt.transparent))
                except:
                    pass

            node = ruler.getInfo(former, latter, allow_multi=True)
            if node is None:
                interval, start, stop = "NULL", "NULL", "NULL"
                tudy = 0  # 图定区间时分

            else:
                interval = "%02d:%02d" % (int(node["interval"] / 60), node["interval"] % 60)
                start = "%01d:%02d" % (int(node["start"] / 60), node["start"] % 60)
                stop = "%01d:%02d" % (int(node["stop"] / 60), node["stop"] % 60)

                tudy = node["interval"]
                if appendix & 0x1:
                    # 起步附加
                    tudy += node["start"]
                if appendix & 0x2:
                    tudy += node["stop"]

            item = QtWidgets.QTableWidgetItem(interval)
            tableWidget.setItem(row, 1, item)

            item = QtWidgets.QTableWidgetItem(start)
            tableWidget.setItem(row, 2, item)

            item = QtWidgets.QTableWidgetItem(stop)
            tableWidget.setItem(row, 3, item)

            if tudy != uiji and node is not None:
                try:
                    rate = min(((uiji - tudy) / tudy,1))
                except ZeroDivisionError:
                    rate = 1

                ds = uiji - tudy
                ds_str = "%01d:%02d" % (abs(ds)//60, abs(ds) % 60)
                if ds < 0:
                    ds_str = '-' + ds_str

                tableWidget.setItem(row, 7, QtWidgets.QTableWidgetItem(ds_str))

                if rate > 0.0:
                    color = QtGui.QColor(Qt.blue)
                else:
                    color = QtGui.QColor(Qt.red)
                color.setAlpha(abs(200 * rate) + 55)

                for c in range(8):
                    item: QtWidgets.QTableWidgetItem = tableWidget.item(row, c)
                    item.setBackground(QtGui.QBrush(color))

    def _train_event_out(self):
        """
        meet = 0 #会车
        overTaking = 1 #越行
        avoid = 2 #待避
        arrive = 3 #到站
        leave = 4 #出发
        pass_settled = 5
        pass_calculated = 6
        """
        train: Train = self.GraphWidget.selectedTrain
        if train is None:
            self._derr("当前车次事件时刻表：当前没有选中车次！")
            return

        dialog = QtWidgets.QProgressDialog(self)
        dialog.setRange(0, 0)
        dialog.setMinimumDuration(100)
        dialog.setCancelButtonText('取消')
        dialog.setWindowTitle('正在处理')
        dialog.setLabelText('正在计算事件表，请稍候...')
        dialog.setValue(0)
        dialog.setAutoReset(True)

        # inner class
        class GetTrainEventThread(QtCore.QThread):
            eventOK = QtCore.pyqtSignal(list)
            def __init__(self,graphWidget:GraphicsWidget,parent=None):
                super(GetTrainEventThread, self).__init__(parent)
                self.graphWidget = graphWidget

            def run(self):
                events = self.graphWidget.listTrainEvent()
                self.eventOK.emit(events)


        thread = GetTrainEventThread(self.GraphWidget)
        thread.eventOK.connect(lambda events:self._train_event_out_ok(events,dialog))
        thread.start()
        while True:
            QtCore.QCoreApplication.processEvents()
            if dialog.wasCanceled():
                thread.terminate()
                return

        # events = self.GraphWidget.listTrainEvent()

    def _train_event_out_ok(self, events: list, dialog):
        print('list ok')
        dialog.close()
        train: Train = self.GraphWidget.selectedTrain
        if not events:
            return

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(6)
        tableWidget.setHorizontalHeaderLabels(['时间', '地点', '里程', '事件', '客体', '备注'])
        tableWidget.setRowCount(len(events))
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        widths = (100, 120, 90, 60, 80, 80)
        for i, s in enumerate(widths):
            tableWidget.setColumnWidth(i, s)

        for row, event in enumerate(events):
            tableWidget.setRowHeight(row, self.graph.UIConfigData()['table_row_height'])
            item = QtWidgets.QTableWidgetItem(event["time"].strftime('%H:%M:%S'))
            tableWidget.setItem(row, 0, item)

            space_str = event["former_station"]
            if event["later_station"] is not None:
                space_str += f'-{event["later_station"]}'
            item = QtWidgets.QTableWidgetItem(space_str)
            tableWidget.setItem(row, 1, item)

            mile_str = "%.2f" % event["mile"] if event["mile"] != -1 else "NA"
            item = QtWidgets.QTableWidgetItem(f"{event['mile']:.1f}")
            item.setData(Qt.DisplayRole, event["mile"])
            # item.setText(mile_str)
            tableWidget.setItem(row, 2, item)

            type: TrainEventType = event["type"]
            if type == TrainEventType.arrive:
                event_str = '到达'
            elif type == TrainEventType.leave:
                event_str = '出发'
            elif type == TrainEventType.pass_settled or type == TrainEventType.pass_calculated:
                event_str = '通过'
            elif type == TrainEventType.avoid:
                event_str = '让行'
            elif type == TrainEventType.overTaking:
                event_str = '越行'
            elif type == TrainEventType.meet:
                event_str = '交会'
            elif type == TrainEventType.origination:
                event_str = '始发'
            elif type == TrainEventType.destination:
                event_str = '终到'
            else:
                event_str = '未知'
            item = QtWidgets.QTableWidgetItem(event_str)
            tableWidget.setItem(row, 3, item)

            another = event["another"]
            if another is None:
                another = ''
            item = QtWidgets.QTableWidgetItem(another)
            tableWidget.setItem(row, 4, item)

            if event["type"] == TrainEventType.pass_calculated:
                add = '推定'
            else:
                add = event.get("note", '')
            item = QtWidgets.QTableWidgetItem(add)
            tableWidget.setItem(row, 5, item)

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("当前车次事件表")
        dialog.resize(600, 600)
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel(f"{train.fullCheci()}次列车在{self.graph.lineName()}"
                                 f"的事件时刻表如下。")
        label.setWordWrap(True)
        layout.addWidget(label)

        layout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnOut = QtWidgets.QPushButton("导出为表格")
        btnOut.clicked.connect(lambda: self._train_event_out_excel(tableWidget))
        hlayout.addWidget(btnOut)

        btnText = QtWidgets.QPushButton("导出为文字")
        btnText.clicked.connect(lambda: self._train_event_out_text(events))
        hlayout.addWidget(btnText)

        btnClose = QtWidgets.QPushButton("关闭")
        btnClose.clicked.connect(dialog.close)
        hlayout.addWidget(btnClose)

        layout.addLayout(hlayout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _train_event_out_excel(self, tableWidget):
        self.statusOut("正在准备导出……")
        try:
            import xlwt
        except ImportError:
            self._derr("需要'xlwt'库支持。如果您的程序依赖Python环境运行，请在终端执行："
                       "'pip3 install xlwt'")
            self.statusOut("就绪")
            return

        checi: str = self.GraphWidget.selectedTrain.fullCheci()
        checi_new = f"{checi.replace('/',',')}"
        filename = QtWidgets.QFileDialog.getSaveFileName(self, '选择文件',
                                                         directory=f'{checi_new}事件时刻表@{self.graph.lineName()}',
                                                         filter='*.xls')[0]
        if not filename:
            return

        wb = xlwt.Workbook(encoding='utf-8')
        ws: xlwt.Worksheet = wb.add_sheet("车次事件时刻表")

        ws.write(0, 0, f"{self.GraphWidget.selectedTrain.fullCheci()}在{self.graph.lineName()}运行的事件时刻表")
        for i, s in enumerate(['时间', '地点', '里程', '事件', '客体', '备注']):
            ws.write(1, i, s)

        for row in range(tableWidget.rowCount()):
            for col in range(6):
                ws.write(row + 2, col, tableWidget.item(row, col).text())
        wb.save(filename)
        self._dout("列车事件时刻表导出成功！")
        self.statusOut("就绪")

    def _train_event_out_text(self, events):
        checi: str = self.GraphWidget.selectedTrain.fullCheci()
        checi.replace('/', ',')
        filename = QtWidgets.QFileDialog.getSaveFileName(self, '选择文件',
                                                         directory=f'{checi}事件时刻表', filter='*.txt')[0]
        if not filename:
            return
        text = ""
        for event in events:
            if event["type"] == TrainEventType.arrive:
                text += "{},{}车站到达（图定）\n".format(event["time"].strftime("%H:%M:%S"), event["former_station"])
            elif event["type"] == TrainEventType.leave:
                text += "{},{}车站发车（图定）\n".format(event["time"].strftime("%H:%M:%S"), event["former_station"])
            elif event["type"] == TrainEventType.meet:
                if event["later_station"] is not None:
                    text += "{},在{}—{}区间 会 {} 次\n".format(
                        event["time"].strftime("%H:%M:%S"), event["former_station"], event["later_station"],
                        event["another"]
                    )
                else:
                    text += f"{event['time'].strftime('%H:%M:%S')}, 在{event['former_station']}" \
                            f" 会 {event['another']} 次\n"
            elif event["type"] == TrainEventType.overTaking:
                if event["later_station"] is not None:
                    text += "{},在{}—{}区间 越 {} 次\n".format(
                        event["time"].strftime("%H:%M:%S"), event["former_station"], event["later_station"],
                        event["another"]
                    )
                else:
                    text += f"{event['time'].strftime('%H:%M:%S')}, 在{event['former_station']}" \
                            f" 越 {event['another']} 次\n"
            elif event["type"] == TrainEventType.avoid:
                if event["later_station"] is not None:
                    text += "{},在{}—{}区间 让 {} 次\n".format(
                        event["time"].strftime("%H:%M:%S"), event["former_station"], event["later_station"],
                        event["another"]
                    )
                else:
                    text += f"{event['time'].strftime('%H:%M:%S')}, 在{event['former_station']}" \
                            f" 让 {event['another']} 次\n"
            elif event["type"] == TrainEventType.pass_settled:
                text += "{},{} 通过（图定）\n".format(event["time"].strftime("%H:%M:%S"), event["former_station"])
        with open(filename, 'w', encoding='utf-8', errors='ignore') as fp:
            fp.write(text)
        self._dout("导出成功！")

    def _initTypeDock(self):
        typeDock = QtWidgets.QDockWidget()
        typeDock.setWindowTitle("显示类型设置")
        typeDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("显示类型设置", typeDock))
        self.typeDockWidget = typeDock
        typeDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, typeDock)
        typeDock.setVisible(False)

    def _initTypeWidget(self):
        typeWidget = TypeWidget(self.graph, self)
        self.typeWidget = typeWidget
        typeWidget.TypeShowChanged.connect(self._apply_type_show)
        typeWidget.ItemWiseDirShowChanged.connect(self._apply_itemwise_dir_show)

        self.typeDockWidget.setWidget(typeWidget)

    def _apply_type_show(self):
        """
        由typeWidget的确定触发，修改运行图铺画。已知其他不变，只需要增减部分运行线，避免重新铺画。
        调用前已经修改过数据中的isShow。
        """
        self.trainWidget.updateShow()
        for train in self.graph.trains():
            self.GraphWidget.setTrainShow(train)

    def _apply_itemwise_dir_show(self, down, show):
        """
        精确到Item级别的显示变化控制。不再调用上一个函数。
        """
        self.trainWidget.updateShow()
        for train in self.graph.trains():
            self.GraphWidget.setTrainShow(train)
            for item in train.items():
                if (item.down == down) and not show:
                    item.setVisible(False)

    def _initRulerDock(self):
        rulerDock = QtWidgets.QDockWidget()
        rulerDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        rulerDock.setWindowTitle("标尺编辑")
        rulerDock.visibilityChanged.connect(lambda: self._dock_visibility_changed(
            '标尺编辑', rulerDock
        ))

        self.addDockWidget(Qt.RightDockWidgetArea, rulerDock)
        self.rulerDockWidget = rulerDock
        rulerDock.setVisible(False)

    def _initRulerWidget(self):
        if self.rulerDockWidget is None:
            return

        rulerWidget = RulerWidget(self.graph.line, self)
        self.rulerWidget = rulerWidget
        self.rulerDockWidget.setWidget(rulerWidget)

    def _initTrainDock(self):
        trainDock = QtWidgets.QDockWidget()
        trainDock.setWindowTitle("车次编辑")
        trainDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("车次编辑", trainDock))
        self.addDockWidget(Qt.LeftDockWidgetArea, trainDock)
        self.trainDockWidget = trainDock
        trainDock.setVisible(False)

    def _initTrainWidget(self):
        if self.trainDockWidget is None:
            return

        trainWidget = TrainWidget(self.graph, self, self)
        self.trainWidget = trainWidget
        trainWidget.search_train.connect(self._search_train)
        trainWidget.current_train_changed.connect(self._current_train_changed)
        trainWidget.train_double_clicked.connect(self._train_table_doubleClicked)
        trainWidget.trainShowChanged.connect(self._train_show_changed)
        trainWidget.addNewTrain.connect(self._add_train_from_list)
        trainWidget.showStatus.connect(self.statusOut)

        self.trainDockWidget.setWidget(trainWidget)

    def _train_table_doubleClicked(self, train: Train):
        """
        2018.12.28新增逻辑，强制显示运行线
        """
        print("double clicked!")
        train.setIsShow(True, affect_item=True)
        self.setCurrentTrain(train)
        self.GraphWidget.setTrainShow(train, True)
        for item in train.items():
            self.GraphWidget._line_selected(item)
            break
        dock: QtWidgets.QDockWidget = self.currentDockWidget
        dock.setVisible(True)

    def _show_timetable(self, train: Train):
        """
        2019.06.25新增，强制显示时刻表。
        """
        self.trainTimetableDockWidget.setVisible(True)
        self.trainTimetableWidget.setData(train)

    def _interactive_timetable_changed(self,train:Train,dct:dict):
        """
        2019.07.05新增，通过交互式界面调整列车时刻表
        """
        if train is None:
            return
        self._updateCurrentTrainRelatedWidgets(train,force=False,sender=3)
        if self.graph.stationInLine(dct['zhanming']):
            # 本线调整才重新铺画运行线
            self.GraphWidget.repaintTrainLine(train)

    def _search_train(self, checi: str):
        if self.updating:
            return
        if not checi:
            return
        train: Train = self.graph.trainFromCheci(checi)
        if train is None:
            self._derr("无此车次：{}".format(checi))
            return
        self.GraphWidget._line_un_selected()
        train.setIsShow(True, affect_item=True)
        if train.item is None:
            self.GraphWidget.addTrainLine(train)

        self.GraphWidget._line_selected(train.firstItem(), ensure_visible=True)
        self.setCurrentTrain(train)

    def _train_show_changed(self, train: Train, show: bool):
        """
        从trainWidget的同名函数触发
        2018.12.28修改：封装trainWidget部分，直接接受车次对象。这个函数只管划线部分
        """

        if show and not train.items():
            # 如果最初铺画没有铺画运行线而要求显示运行线，重新铺画。
            # print('重新铺画运行线。Line972')
            self.GraphWidget.addTrainLine(train)

        if train is self.GraphWidget.selectedTrain and not show:
            # 若取消显示当前选中的Item，则取消选择
            self.GraphWidget._line_un_selected()

    def _add_train_from_list(self):
        self.currentDockWidget.setVisible(True)
        self.currentWidget.setData()
        self.currentDockWidget.setFocus(True)
        self.currentWidget.checiEdit.setFocus(True)

    def _initLineDock(self):
        dockLine = QtWidgets.QDockWidget()
        dockLine.setWindowTitle("线路编辑")
        dockLine.visibilityChanged.connect(lambda: self._dock_visibility_changed("线路编辑", dockLine))
        self.addDockWidget(Qt.RightDockWidgetArea, dockLine)
        self.lineDockWidget = dockLine
        # dockLine.setVisible(False)

    def _initLineWidget(self):
        if self.lineDockWidget is None:
            return

        lineWidget = LineWidget(self.graph.line)
        self.lineWidget = lineWidget
        lineWidget.initWidget()
        self.lineDockWidget.setWidget(lineWidget)
        lineWidget.lineChangedApplied.connect(self._on_line_changed)
        lineWidget.showStatus.connect(self.statusOut)

    def _on_line_changed(self):
        """
        lineWidget确认线路信息触发
        """
        self.graph.line.resetRulers()
        for train in self.graph.trains():
            train.updateLocalFirst(self.graph)
            train.updateLocalLast(self.graph)
        try:
            self.GraphWidget.paintGraph()
        except:
            self.graph.setOrdinateRuler(None)
            self.GraphWidget.paintGraph()
        self.rulerWidget.updateRulerTabs()

    def _initConfigDock(self):
        configDock = QtWidgets.QDockWidget()
        configDock.setWindowTitle("运行图设置")

        configDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("运行图设置", configDock))
        configDock.setVisible(False)
        self.configDockWidget = configDock
        self.addDockWidget(Qt.RightDockWidgetArea, configDock)

    def _initConfigWidget(self):
        configWidget = ConfigWidget(self.graph, False, self)
        self.configWidget = configWidget
        configWidget.RepaintGraph.connect(self._apply_config_repaint)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(configWidget)

        self.configDockWidget.setWidget(scroll)

    def _apply_config_repaint(self):
        """
        由configWidget的repaint信号触发，进行铺画运行图操作。
        """
        try:
            self.GraphWidget.paintGraph(True)
        except Exception as e:
            self._derr("铺画失败，可能由于排图标尺不符合要求。已自动恢复为按里程排图。\n" + str(e))
            self.graph.setOrdinateRuler(None)
            self.GraphWidget.paintGraph()
            self.configWidget.setOrdinateCombo()

    def changeOrdinateRuler(self, ruler: Ruler):
        """
        调整排图标尺。返回是否成功。
        本函数只由rulerWidget中按钮调用。
        """
        former = self.graph.ordinateRuler()
        try:
            self.graph.setOrdinateRuler(ruler)
            self.GraphWidget.paintGraph(throw_error=True)
        except RulerNotCompleteError as e:
            self._derr(f"设置排图标尺失败！设为排图纵坐标的标尺必须填满每个区间数据。自动变更为按里程排图。"
                       f"\n缺数据区间：{e.start}-{e.end}")
            self.graph.setOrdinateRuler(former)
            self.GraphWidget.paintGraph()
            return False

        self.configWidget.setOrdinateCombo()
        return True

    def _initMenuBar(self):
        class PM(QtWidgets.QMenu):
            def __init__(self,text,main:'MainGraphWindow',parent):
                super(PM, self).__init__(text,parent)
                self.main = main

            def addAction(self, action):
                super(PM, self).addAction(action)
                self.main.addAction(action)

        menubar: QtWidgets.QMenuBar = self.menuBar()
        # 文件
        if True:
            m1: QtWidgets.QMenu = PM("文件(&F)",self, menubar)
            menubar.addMenu(m1)
            actionNew = QtWidgets.QAction("新建", self)
            actionNew.setShortcut('ctrl+N')
            actionNew.triggered.connect(self._newGraph)
            m1.addAction(actionNew)

            actionOpen = QtWidgets.QAction(QtGui.QIcon(), "打开", self)
            actionOpen.setShortcut('ctrl+O')
            actionOpen.triggered.connect(self._openGraph)
            m1.addAction(actionOpen)

            actionSave = QtWidgets.QAction("保存", self)
            actionSave.setShortcut('ctrl+S')
            actionSave.triggered.connect(self._saveGraph)
            m1.addAction(actionSave)

            actionSaveAs = QtWidgets.QAction("另存为", self)
            actionSaveAs.triggered.connect(self._saveGraphAs)
            actionSaveAs.setShortcut('F12')
            m1.addAction(actionSaveAs)

            actionToTrc = QtWidgets.QAction("导出为ETRC运行图（.trc）格式", self)
            actionToTrc.triggered.connect(self._toTrc)
            actionToTrc.setShortcut('ctrl+M')
            m1.addAction(actionToTrc)

            actionReset = QtWidgets.QAction("重新读取本运行图", self)
            actionReset.triggered.connect(self._reset_graph)
            m1.addAction(actionReset)

            actionRefresh = QtWidgets.QAction("刷新", self)
            actionRefresh.setShortcut('F5')
            actionRefresh.triggered.connect(self._refresh_graph)
            m1.addAction(actionRefresh)

            actionPaint = QtWidgets.QAction("立即铺画运行图", self)
            actionPaint.setShortcut('shift+F5')
            actionPaint.triggered.connect(lambda: self.GraphWidget.paintGraph(force=True))
            m1.addAction(actionPaint)

            actionOutput = QtWidgets.QAction(QtGui.QIcon(), "导出运行图", self)
            actionOutput.setShortcut("ctrl+T")
            actionOutput.triggered.connect(self._outputGraph)
            m1.addAction(actionOutput)
            # self.actionOutput=actionOutput

            actionOutPdf = QtWidgets.QAction(QtGui.QIcon(), "导出矢量pdf运行图", self)
            actionOutPdf.setShortcut("ctrl+shift+T")
            actionOutPdf.triggered.connect(self._outputPdf)
            m1.addAction(actionOutPdf)

            actionOutExcel = QtWidgets.QAction('导出点单', self)
            actionOutExcel.setShortcut('ctrl+alt+T')
            actionOutExcel.triggered.connect(self._outExcel)
            self.addAction(actionOutExcel)

            actionClose = QtWidgets.QAction("退出程序", self)
            actionClose.setShortcut('alt+F4')
            actionClose.triggered.connect(self.close)
            m1.addAction(actionClose)

        # 工具
        if True:
            menu = PM("工具(&T)",self, menubar)
            menubar.addMenu(menu)
            action = QtWidgets.QAction("标尺排图向导", self)
            action.setShortcut('ctrl+R')
            action.triggered.connect(self._add_train_by_ruler)
            menu.addAction(action)

            action = QtWidgets.QAction('当前车次区间重排', self)
            action.setShortcut('ctrl+shift+R')
            action.triggered.connect(self._change_train_interval)
            menu.addAction(action)

            action = QtWidgets.QAction('多车次标尺读取向导', self)
            action.setShortcut('ctrl+shift+B')
            action.triggered.connect(self._read_ruler_from_trains)
            menu.addAction(action)

            action = QtWidgets.QAction("搜索车次", self)
            action.setShortcut('ctrl+F')
            action.triggered.connect(self._search_from_menu)
            menu.addAction(action)

            action = QtWidgets.QAction("模糊检索车次", self)
            action.setShortcut('ctrl+shift+F')
            action.triggered.connect(self._multi_search_train)
            menu.addAction(action)

            action = QtWidgets.QAction("重置所有始发终到站", self)
            action.triggered.connect(self._reset_start_end)
            menu.addAction(action)

            action = QtWidgets.QAction("自动适配始发终到站", self)
            action.triggered.connect(self._auto_start_end)
            # action.setShortcut('ctrl+M')
            menu.addAction(action)

            action = QtWidgets.QAction("运行图拼接", self)
            action.triggered.connect(self._joint_graph)
            action.setShortcut('ctrl+J')
            menu.addAction(action)

            action = QtWidgets.QAction('运行图对照',self)
            action.setShortcut('ctrl+6')
            action.triggered.connect(self._graph_diff)
            menu.addAction(action)

            actionZoonIn = QtWidgets.QAction('放大视图', self)
            actionZoonIn.setShortcut('ctrl+=')
            actionZoomOut = QtWidgets.QAction('缩小视图', self)
            menu.addAction(actionZoonIn)

            actionZoomOut.setShortcut('ctrl+-')
            actionZoonIn.triggered.connect(lambda: self.GraphWidget.scale(1.25, 1.25))
            actionZoomOut.triggered.connect(lambda: self.GraphWidget.scale(0.8, 0.8))
            menu.addAction(actionZoomOut)

            menu.addSeparator()
            actionResetType = QtWidgets.QAction('重置所有列车营业站', self)
            actionResetType.triggered.connect(self._reset_business)
            menu.addAction(actionResetType)

            actionResetPassenger = QtWidgets.QAction("自动设置是否客车", self)
            actionResetPassenger.triggered.connect(self._reset_passenger)
            menu.addAction(actionResetPassenger)

            actionAutoType = QtWidgets.QAction('重置所有列车类型', self)
            actionAutoType.triggered.connect(self._auto_type)
            menu.addAction(actionAutoType)

            actionDeleteAll = QtWidgets.QAction('删除所有车次',self)
            actionDeleteAll.triggered.connect(self._delete_all)
            menu.addAction(actionDeleteAll)

            actionDeleteNonLocal = QtWidgets.QAction('删除时刻表中所有非本线站点', self)
            actionDeleteNonLocal.triggered.connect(self._delete_non_local)
            menu.addAction(actionDeleteNonLocal)

            menu.addSeparator()
            action = QtWidgets.QAction('批量解析交路',self)
            action.setShortcut('ctrl+P')
            menu.addAction(action)
            action.triggered.connect(self._batch_parse_circuits)

            action = QtWidgets.QAction("识别所有虚拟车次",self)
            action.triggered.connect(self._identify_virtual_trains)
            menu.addAction(action)

        # 查看
        if True:
            menu = PM("查看(&I)",self, menubar)
            menubar.addMenu(menu)

            action = QtWidgets.QAction("运行图信息", self)
            action.triggered.connect(self._line_info_out)
            menu.addAction(action)

            # action = QtWidgets.QAction("当前车次信息", self)
            # action.setShortcut('ctrl+Q')
            # action.triggered.connect(self._train_info)
            # menu.addAction(action)

            action = QtWidgets.QAction("当前车次标尺对照", self)
            action.setShortcut('ctrl+W')
            action.triggered.connect(self._check_ruler_from_menu)
            menu.addAction(action)

            action = QtWidgets.QAction("两车次时分对照", self)
            action.setShortcut('ctrl+shift+W')
            action.triggered.connect(self._train_compare)
            menu.addAction(action)

            action = QtWidgets.QAction("当前车次区间性质计算", self)
            action.setShortcut('ctrl+shift+Q')
            action.triggered.connect(self._get_interval_info)
            menu.addAction(action)

            action = QtWidgets.QAction("当前车次事件表", self)
            action.setShortcut('ctrl+Z')
            action.triggered.connect(self._train_event_out)
            menu.addAction(action)

            action = QtWidgets.QAction("车站时刻表输出", self)
            action.setShortcut('ctrl+E')
            action.triggered.connect(self._station_timetable)
            menu.addAction(action)

            action = QtWidgets.QAction("区间对数表", self)
            action.setShortcut('ctrl+3')
            action.triggered.connect(self._interval_count)
            menu.addAction(action)

            action = QtWidgets.QAction("区间车次表", self)
            action.setShortcut('ctrl+shift+3')
            action.triggered.connect(self._interval_trains)
            menu.addAction(action)

            action = QtWidgets.QAction('标尺一览表',self)
            action.triggered.connect(self._ruler_table)
            action.setShortcut('Ctrl+7')
            menu.addAction(action)

        # 调整
        if True:
            menu = PM("调整(&A)",self,menubar)
            menubar.addMenu(menu)

            action = QtWidgets.QAction("调整当前车次时刻", self)
            action.setShortcut('ctrl+A')
            action.triggered.connect(self._adjust_train_time)
            menu.addAction(action)

            action = QtWidgets.QAction("批量复制当前运行线", self)
            action.setShortcut('ctrl+shift+A')
            action.triggered.connect(self._batch_copy_train)
            menu.addAction(action)

            action = QtWidgets.QAction('区间换线', self)
            action.setShortcut('ctrl+5')
            action.triggered.connect(self._interval_exchange)
            menu.addAction(action)

            action = QtWidgets.QAction("反排运行图", self)
            action.triggered.connect(self._reverse_graph)
            menu.addAction(action)

            action = QtWidgets.QAction("修改站名", self)
            action.setShortcut('ctrl+U')
            action.triggered.connect(self._change_station_name)
            menu.addAction(action)

            action = QtWidgets.QAction("批量站名映射", self)
            action.setShortcut('ctrl+shift+U')
            action.triggered.connect(self._change_massive_station)
            menu.addAction(action)

            action = QtWidgets.QAction("推定通过时刻", self)
            action.setShortcut('ctrl+2')
            action.triggered.connect(self._detect_pass_time)
            menu.addAction(action)

            action = QtWidgets.QAction('撤销全部推定结果',self)
            action.triggered.connect(self._withdraw_detect)
            menu.addAction(action)

            action = QtWidgets.QAction('高级显示车次设置', self)
            action.setShortcut('ctrl+shift+L')
            action.triggered.connect(self.showFilter.setFilter)
            menu.addAction(action)

            action = QtWidgets.QAction('当前车次时刻表重排', self)
            action.setShortcut('ctrl+V')
            action.triggered.connect(self._correction_timetable)
            menu.addAction(action)

            action = QtWidgets.QAction('添加车次',self)
            action.setShortcut('ctrl+shift+C')
            action.triggered.connect(self._add_train_from_list)
            menu.addAction(action)

        # 数据
        if True:
            menu = PM("数据(&S)",self, menubar)
            menubar.addMenu(menu)

            action = QtWidgets.QAction("线路数据库", self)
            action.setShortcut('ctrl+H')
            action.triggered.connect(self._view_line_data)
            menu.addAction(action)

            action = QtWidgets.QAction("线路数据库(旧版)",self)
            action.setShortcut('ctrl+alt+H')
            action.triggered.connect(self._view_line_data_old)
            menu.addAction(action)

            action = QtWidgets.QAction("导入线路数据（旧版）", self)
            action.setShortcut('ctrl+K')
            action.triggered.connect(self._import_line)
            menu.addAction(action)

            action = QtWidgets.QAction("导入线路数据(Excel)", self)
            action.setShortcut('ctrl+shift+K')
            action.triggered.connect(self._import_line_excel)
            menu.addAction(action)

            action = QtWidgets.QAction("导入车次", self)
            action.setShortcut('ctrl+D')
            self.actionImportTrain = action
            action.triggered.connect(self._import_train)
            menu.addAction(action)

            action = QtWidgets.QAction('导入车次时刻表（Excel）', self)
            action.triggered.connect(self._import_train_excel)
            menu.addAction(action)

            action = QtWidgets.QAction("导入车次(旧版)",self)
            action.setShortcut('ctrl+alt+D')
            action.triggered.connect(self._import_train_old)
            menu.addAction(action)

            action = QtWidgets.QAction("导入实际运行线", self)
            action.setShortcut('ctrl+shift+D')
            action.triggered.connect(self._import_train_real)
            menu.addAction(action)

        # 窗口
        if True:
            menu = PM("窗口(&W)",self,menubar)
            menubar.addMenu(menu)
            self.actionWindow_list = []
            actions = (
                '线路编辑', '车次编辑', '标尺编辑', '选中车次设置', '运行图设置', '系统默认设置',
                '显示类型设置', '天窗编辑', '交路编辑', '车次信息', '车次时刻表','交互式时刻表'
            )
            shorcuts = (
                'X', 'C', 'B', 'I', 'G', 'shift+G', 'L', '1', '4', 'Q', 'Y','shift+Y'
            )
            for a, s in zip(actions, shorcuts):
                action = QtWidgets.QAction(a, self)
                # action.setText(a)
                action.setCheckable(True)
                action.setShortcut(f'ctrl+{s}')

                menu.addAction(action)
                self.actionWindow_list.append(action)

            menu.triggered[QtWidgets.QAction].connect(self._window_menu_triggered)

        # 帮助
        if True:
            menu = PM("帮助(&H)",self,menubar)
            menubar.addMenu(menu)

            action = QtWidgets.QAction("关于", self)
            action.triggered.connect(self._about)
            menu.addAction(action)

            action = QtWidgets.QAction("简明功能表", self)
            action.triggered.connect(self._function_list)
            action.setShortcut('F1')
            menu.addAction(action)
        self.menuBar().setVisible(False)

    def _checkGraph(self):
        """
        2019.06.21新增，打开运行图时检查文件，输出错误信息。
        """
        report = self.graph.checkGraph()
        if report:
            self._dout(report)

    def _window_menu_triggered(self, action: QtWidgets.QAction):
        widgets = {
            '线路编辑': self.lineDockWidget,
            '车次编辑': self.trainDockWidget,
            '选中车次设置': self.currentDockWidget,
            '运行图设置': self.configDockWidget,
            '显示类型设置': self.typeDockWidget,
            '标尺编辑': self.rulerDockWidget,
            '标尺排图向导': self.guideDockWidget,
            '天窗编辑': self.forbidDockWidget,
            '系统默认设置': self.sysDockWidget,
            '交路编辑': self.circuitDockWidget,
            '车次信息': self.trainInfoDockWidget,
            '车次时刻表': self.trainTimetableDockWidget,
            '交互式时刻表':self.interactiveTimetableDockWidget,
        }
        dock = widgets[action.text()]
        if dock is None:
            return
        if dock.isVisible():
            dock.setVisible(False)
            action.setChecked(False)
        else:
            dock.setVisible(True)
            action.setChecked(True)

    def _dock_visibility_changed(self, name, dock):
        """
        此slot由停靠面板方面来调用
        """
        self.GraphWidget._resetDistanceAxis()
        self.GraphWidget._resetTimeAxis()
        action = None
        for ac in self.actionWindow_list:
            if ac.text() == name:
                action = ac
                break
        if action is None:
            raise Exception("No action name {}, add or check it.".format(name))
        action.setChecked(dock.isVisible())
        for btn in self.dockToolButtons:
            if btn.dockName == name:
                btn.setChecked(dock.isVisible())

    def __addMenuAction(self,m:QtWidgets.QMenu,text:str,slot,toolTip:str=''):
        a = QtWidgets.QAction(text,self)
        a.triggered.connect(slot)
        if toolTip:
            a.setToolTip(toolTip)
        m.addAction(a)

    def _initToolBar(self):
        """
        https://blog.csdn.net/catamout/article/details/5545504
        """
        # self.menuBar().setVisible(False)
        self.dockToolButtons = []
        QI = QtGui.QIcon
        QG = QtWidgets.QGridLayout
        QM = QtWidgets.QMenu
        toolBar = QRibbonToolBar(self)

        # 开始选项卡
        if True:
            menu = toolBar.add_menu('开始')

            group = toolBar.add_group('文件', menu)
            grid = QG()
            btn = PEToolButton('新建', QI(':/new-file.png'), large=True)
            btn.clicked.connect(self._newGraph)
            btn.setToolTip('新建运行图（Ctrl+N）\n'
                           '关闭当前运行图并新建空白的运行图。')
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('打开', QI(':/open.png'), large=True)
            btn.setToolTip('打开运行图（Ctrl+O）\n'
                           '关闭当前运行图，并打开指定的运行图（pyETRC格式或ETRC格式）文件。')
            btn.clicked.connect(self._openGraph)
            grid.addWidget(btn, 0, 1, 2, 1)

            btn = PEToolButton('保存', QI(':/save1.png'), large=True)
            btn.setToolTip('保存运行图（Ctrl+S）\n'
                           '保存当前运行图到文件（以pyETRC格式）。如果没有保存过，需指定文件。')
            btn.clicked.connect(self._saveGraph)
            grid.addWidget(btn, 0, 2, 2, 1)

            btn = PEToolButton('另存为', QI(':/saveas.png'))
            btn.setToolTip('运行图另存为...\n'
                           '将当前运行图的修改保存到指定文件，而不是现有文件。')
            btn.clicked.connect(self._saveGraphAs)
            grid.addWidget(btn, 0, 3, 1, 1)

            group.add_layout(grid)

            group = toolBar.add_group('导出', menu)
            grid = QG()
            btn = PEToolButton('PDF文件', QI(':/pdf.png'), large=True)
            btn.clicked.connect(self._outputPdf)
            btn.setToolTip('导出PDF运行图（Ctrl+Shift+T）\n'
                           '将当前的整张运行图导出为PDF格式矢量图形文件，以便在多种设备上查看。')
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('PNG文件', QI(':/png.png'))
            btn.clicked.connect(self._outputGraph)
            btn.setToolTip('导出PNG运行图（Ctrl+T）\n'
                           '将当前的整张运行图导出为PNG格式的像素图。')
            grid.addWidget(btn, 0, 1, 1, 1)

            btn = PEToolButton('ETRC文件', QI(':/ETRC-dynamic.png'))
            btn.clicked.connect(self._toTrc)
            btn.setToolTip('导出为ETRC运行图文件（Ctrl+M）\n'
                           '导出为ETRC列车运行图系统的*.trc格式运行图文件。')
            grid.addWidget(btn, 1, 1, 1, 1)
            group.add_layout(grid)

            group = toolBar.add_group('更新', menu)
            grid = QG()

            btn = PEToolButton('刷新', QI(':/refresh.png'), large=True)
            btn.clicked.connect(self._refresh_graph)
            btn.setToolTip('刷新运行图（F5）\n'
                           '重新铺画运行图，并更新所有停靠面板数据。\n'
                           '当数据出现不同步异常时，可以调用此功能。')
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('重新铺画', QI(':/brush.png'))
            btn.clicked.connect(lambda: self.GraphWidget.paintGraph(force=True))
            btn.setToolTip('立即重新铺画运行图（Shift+F5）\n'
                           '强制重新铺画运行图，但不更新停靠面板数据。')
            grid.addWidget(btn, 0, 1, 1, 1)

            btn = PEToolButton('重新读取', QI(':/exchange.png'))
            btn.clicked.connect(self._reset_graph)
            btn.setToolTip('重新读取当前运行图\n'
                           '放弃所有未保存更改，重新从文件中读取本运行图。')
            grid.addWidget(btn, 1, 1, 1, 1)
            group.add_layout(grid)

            group = toolBar.add_group('控制', menu)
            grid = QG()
            btn = PEToolButton('水平放大', QI(':/h_expand.png'))
            btn.clicked.connect(self._h_expand)
            grid.addWidget(btn, 0, 0, 1, 1)

            btn = PEToolButton('水平缩小', QI(':/h_shrink.png'))
            btn.clicked.connect(self._h_shrink)
            grid.addWidget(btn, 1, 0, 1, 1)

            btn = PEToolButton('垂直放大', QI(':/v_expand.png'))
            btn.clicked.connect(self._v_expand)
            grid.addWidget(btn, 0, 1, 1, 1)

            btn = PEToolButton('垂直缩小', QI(':/v_shrink.png'))
            btn.clicked.connect(self._v_shrink)
            grid.addWidget(btn, 1, 1, 1, 1)
            group.add_layout(grid)

            group = toolBar.add_group('系统', menu)
            grid = QG()

            btn = PEToolButton('退出', QI(':/close.png'), large=True)
            btn.clicked.connect(self.close)
            btn.setToolTip('退出程序（Alt+F4）')
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('功能表', QI(':/help.png'))
            btn.clicked.connect(self._function_list)
            btn.setToolTip('简明功能表（F1）\n'
                           '查看以快捷键为主要索引方式的功能表。\n'
                           '详细文档请访问http://xep0268.top/pyetrc/doc')
            grid.addWidget(btn, 0, 1, 1, 1)

            btn = PEToolButton('关于', QI('icon.ico'))
            btn.clicked.connect(self._about)
            grid.addWidget(btn, 1, 1, 1, 1)

            # btn = PEToolButton('菜单栏', QI(':/menu.png'), large=True)
            # btn.setCheckable(True)
            # btn.clicked.connect(self.menuBar().setVisible)
            ac = QtWidgets.QAction('菜单栏',self)
            ac.setShortcut('F2')
            self.addAction(ac)
            ac.setCheckable(True)
            ac.triggered.connect(self.menuBar().setVisible)
            ac.setIcon(QI(':/menu.png'))
            ac.setToolTip('菜单栏开关（F2）\n'
                           '显示或隐藏上方的菜单栏。')
            btn = PEToolButton(action=ac,large=True)
            grid.addWidget(btn, 0, 2, 2, 1)

            group.add_layout(grid)

        # 线路 面板
        if True:
            menu = toolBar.add_menu('线路')

            group = toolBar.add_group('基础数据', menu)
            grid = QG()
            btn = PEDockButton('线路编辑', '线路编辑', QI(':/rail.png'), self.lineDockWidget)
            # btn = PEToolButton('线路编辑',QI(':/rail.png'),
            #                    self.__dockActions['线路编辑'],large=True)
            btn.setToolTip('线路编辑（Ctrl+X）\n编辑本线站名、里程等基础数据。')
            grid.addWidget(btn, 0, 0, 2, 1)
            self.dockToolButtons.append(btn)

            btn = PEToolButton('数据库', QI(':/database.png'),large=True)
            btn.clicked.connect(self._view_line_data)
            btn.setToolTip('线路数据库（Ctrl+H）\n查看、管理和导入系统线路数据库。')

            m = QM()
            self.__addMenuAction(m, '线路数据库（旧版）', self._view_line_data_old,
                                 '线路数据库（旧版）（Ctrl+Alt+H）\n'
                                 '查看和维护旧版的内置数据库。\n'
                                 '[警告] 过时功能，可能在将来版本中删除。请使用“线路数据库”功能。')
            self.__addMenuAction(m, '导入线路数据（旧版）', self._import_line,
                                 '导入线路数据（旧版）（Ctrl+K）\n从旧版内置数据库中导入线路数据。\n'
                                 '[警告] 过时功能，可能在将来版本中删除。请使用“线路数据库”功能。')
            btn.setMenu(m)
            grid.addWidget(btn, 0, 1, 2, 1)

            btn = PEToolButton('从Excel', QI(':/excel.png'))
            btn.setToolTip('导入线路数据（Excel）（Ctrl+Shift+K）\n'
                           '从Excel表中导入线路基础数据。')
            btn.clicked.connect(self._import_line_excel)
            grid.addWidget(btn, 0, 2, 1, 1)

            btn = PEToolButton('线路拼接', QI(':/joint.png'))
            btn.setToolTip('运行图拼接（Ctrl+J）\n'
                           '选择运行图，连接线路，导入和连接车次（可选）。')
            btn.clicked.connect(self._joint_graph)
            grid.addWidget(btn, 1, 2, 1, 1)

            btn = PEDockButton('标尺编辑', '标尺编辑', QI(':/ruler.png'), self.rulerDockWidget)
            self.dockToolButtons.append(btn)
            btn.setToolTip('标尺编辑（Ctrl+B）\n设置各个标尺数据，添加或删除标尺。')
            grid.addWidget(btn, 0, 3, 2, 1)

            btn = PEToolButton('标尺综合',QI(':/ruler_pen.png'),large=True)
            btn.clicked.connect(self._read_ruler_from_trains)
            btn.setToolTip('标尺综合（Ctrl+Shift+B）\n'
                           '从一组给定的车次中，综合分析区间标尺数据。')
            grid.addWidget(btn,0,4,2,1)

            btn = PEDockButton('天窗编辑', '天窗编辑', QI(':/forbid.png'), self.forbidDockWidget)
            self.dockToolButtons.append(btn)
            btn.setToolTip('天窗编辑（Ctrl+数字1）\n编辑综合维修天窗、综合施工天窗的时间段及是否显示等。')
            grid.addWidget(btn, 0, 5, 2, 1)

            btn = PEToolButton('标尺一览',QI(':/list.png'))
            btn.setToolTip('标尺一览表（Ctrl+7）\n'
                           '集中显示所有标尺的只读的数据表，以便对比。')
            btn.clicked.connect(self._ruler_table)
            grid.addWidget(btn,0,6,1,1)

            group.add_layout(grid)

            group = toolBar.add_group('微调', menu)
            grid = QG()
            btn = PEToolButton('修改站名', QI(':/exchange1.png'), large=True)
            btn.setToolTip('修改站名（Ctrl+U）\n'
                           '将车站列表及所有车次中的一个站名修改为另一个站名。')
            btn.clicked.connect(self._change_station_name)
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('站名映射', QI(':/arrow.png'))
            btn.setToolTip('站名映射（Ctrl+Shift+U）\n'
                           '批量将[北京西普速场]映射为[北京西::普速场]形式。')
            grid.addWidget(btn, 0, 1, 1, 1)
            btn.clicked.connect(self._change_massive_station)

            btn = PEToolButton('线路反排', QI(':/exchange.png'))
            btn.setToolTip('运行图反排\n'
                           '颠倒本线上下行，同时交换所有列车的上下行车次。')
            btn.clicked.connect(self._reverse_graph)
            grid.addWidget(btn, 1, 1, 1, 1)

            group.add_layout(grid)

            group = toolBar.add_group('分析', menu)
            grid = QG()

            btn = PEToolButton('车站时刻', QI(':/timetable.png'), large=True)
            btn.clicked.connect(self._station_timetable)
            btn.setToolTip('车站时刻表（Ctrl+E）\n'
                           '查看指定车站的时刻表、股道分析图。')
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('运行图信息', QI(':/info.png'))
            btn.clicked.connect(self._line_info_out)
            btn.setToolTip('运行图信息\n'
                           '查看和运行图和线路有关的基本信息。')
            grid.addWidget(btn, 0, 1, 1, 1)

            btn = PEToolButton('运行图对比', QI(':/compare.png'))
            btn.clicked.connect(self._graph_diff)
            btn.setToolTip('运行图对比（Ctrl+6）\n'
                           '对比本运行图和选定运行图（作为新运行图）所有车次的数据。')
            grid.addWidget(btn, 1, 1, 1, 1)
            group.add_layout(grid)

        # 选项卡列车
        if True:
            menu = toolBar.add_menu('列车')

            group = toolBar.add_group('车次管理',menu,use_corner=True)
            grid = QG()
            btn = PEDockButton('车次列表','车次编辑',
                               QI(':/list.png'),self.trainDockWidget)
            btn.setToolTip('车次编辑（Ctrl+C）\n查看车次列表，添加和删除车次。')
            grid.addWidget(btn,0,0,2,1)
            self.dockToolButtons.append(btn)

            combo = QtWidgets.QComboBox()
            self.selectTrainCombo = combo
            for train in self.graph.trains():
                combo.addItem(train.fullCheci())
            combo.currentTextChanged.connect(self._search_train)
            grid.addWidget(combo,0,1,1,2)

            btn = PEToolButton('搜索',QI(':/search.png'))
            btn.clicked.connect(self._search_from_menu)
            # btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setToolTip('搜索车次（Ctrl+F）\n'
                           '输入完整车次或完整的分方向车次来检索。')
            grid.addWidget(btn,1,1,1,1)

            m = QM()
            action = QtWidgets.QAction('模糊检索',self)
            action.triggered.connect(self._multi_search_train)
            action.setToolTip('模糊检索Ctrl+Shift+F')
            m.addAction(action)
            btn.setMenu(m)

            btn = PEToolButton('添加',QI(':/add.png'))
            btn.clicked.connect(self._add_train_from_list)
            # btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setToolTip('添加车次（Ctrl+Shift+C）\n添加新的空白车次。')
            grid.addWidget(btn,1,2,1,1)

            btn = PEToolButton('导入车次',QI(':/add_train.png'),large=True)
            btn.clicked.connect(self._import_train)
            btn.setToolTip('导入车次（Ctrl+D）\n从选定的运行图文件或数据库文件导入车次数据。')

            m = QM()
            self.__addMenuAction(m,'导入车次（旧版）',self._import_train_old)
            self.__addMenuAction(m,'导入实际运行线（旧版）',self._import_train_real,
                                 '从指定运行图中导入车次，并添加前缀R。')
            self.__addMenuAction(m,'导入车次时刻（Excel）',self._import_train_excel,
                                 '使用指定的格式导入Excel车次时刻文件。')
            btn.setMenu(m)

            grid.addWidget(btn,0,3,2,1)
            group.add_layout(grid)

            m = QM('车次管理工具')
            self.__addMenuAction(m,'重置始发终到',self._reset_start_end)
            self.__addMenuAction(m,'自动适配始发终到站',self._auto_start_end)
            self.__addMenuAction(m,'重置营业站',self._reset_business)
            self.__addMenuAction(m,'重置是否客车',self._reset_passenger)
            self.__addMenuAction(m,'重置列车类型',self._auto_type)
            m.addSeparator()
            self.__addMenuAction(m,'删除所有车次',self._delete_all)
            self.__addMenuAction(m,'删除时刻表中的非本线站点',self._delete_non_local)
            group.set_corner_menu(m)

            group = toolBar.add_group('当前车次',menu,use_corner=False)  # 2行
            grid = QtWidgets.QGridLayout()
            btn = PEDockButton('编辑','选中车次设置',
                               QI(':/timetable.png'),self.currentDockWidget)
            btn.setToolTip('当前车次信息编辑（Ctrl+I）\n'
                           '最完整的车次数据编辑面板。')
            grid.addWidget(btn,0,0,2,1)
            self.dockToolButtons.append(btn)

            btn = PEDockButton('时刻表','车次时刻表',
                               QI(':/clock.png'),
                               self.trainTimetableDockWidget)
            btn.setToolTip('车次时刻表（Ctrl+Y）\n只读的简洁形式列车时刻表。')
            grid.addWidget(btn,0,1,2,1)
            self.dockToolButtons.append(btn)

            btn = PEDockButton('微调','交互式时刻表',
                               QI(':/electronic-clock.png',),
                               self.interactiveTimetableDockWidget,large=False)
            btn.setToolTip('交互式列车时刻表（Ctrl+Shift+Y）\n'
                           '调整当且车次时刻，且立即生效。')
            grid.addWidget(btn,0,2,1,1)
            self.dockToolButtons.append(btn)

            btn = PEDockButton('信息','车次信息',QI(':/info.png'),
                               self.trainInfoDockWidget,large=False)
            self.dockToolButtons.append(btn)
            grid.addWidget(btn,1,2,1,1)

            btn = PEToolButton('平移',QI(':/adjust.png'))
            btn.clicked.connect(self._adjust_train_time)
            btn.setToolTip('平移时刻表（Ctrl+A）\n'
                           '将部分或全部站时刻表提早或者推迟一定时间。')
            grid.addWidget(btn,0,3,1,1)

            btn = PEToolButton('修正',QI(':/adjust-2.png'))
            btn.clicked.connect(lambda: self._correction_timetable(self.currentTrain()))
            btn.setToolTip('修正时刻表（Ctrl+V）\n'
                           '调整时刻表的顺序错误、发到站时刻排反等顺序问题。')
            grid.addWidget(btn,1,3,1,1)

            group.add_layout(grid)

            group = toolBar.add_group('分析',menu)
            grid = QG()

            btn = PEToolButton('标尺对照',QI(':/ruler.png'))
            btn.clicked.connect(self._check_ruler_from_menu)
            btn.setToolTip('标尺对照（Ctrl+W）\n'
                           '将当前车次时刻表与指定标尺对比。')
            grid.addWidget(btn,0,0,1,1)

            btn = PEToolButton('事件表',QI(':/clock.png'))
            btn.clicked.connect(self._train_event_out)
            btn.setToolTip('车次事件表（Ctrl+Z）\n'
                           '显示到开、越行、会让等事件表。')
            grid.addWidget(btn,0,1,1,1)

            btn = PEToolButton('车次对照',QI(':/compare.png'))
            btn.clicked.connect(self._train_compare)
            btn.setToolTip('两车次对照（Ctrl+Shift+W）\n'
                           '对比两个车次在本线的区间运行时分。')
            grid.addWidget(btn,1,1,1,1)

            btn = PEToolButton('区间分析',QI(':/data.png'))
            btn.clicked.connect(self._get_interval_info)
            btn.setToolTip('区间数据分析（Ctrl+Shift+Q）\n'
                           '显示列车在指定区间的停站数，均速等信息。')
            grid.addWidget(btn,1,0,1,1)
            group.add_layout(grid)

            group = toolBar.add_group('交路',menu)
            grid = QG()
            btn = PEDockButton('交路编辑','交路编辑',QI(':/polyline.png'),
                               self.circuitDockWidget)
            btn.setToolTip('交路编辑（Ctrl+4）\n'
                           '查看和编辑所有交路信息。')
            grid.addWidget(btn,0,0,2,1)
            self.dockToolButtons.append(btn)

            btn = PEToolButton('文本解析',QI(':/text.png'))
            btn.clicked.connect(self._batch_parse_circuits)
            btn.setToolTip('批量解析交路文本（Ctrl+P）\n'
                           '从文本形式的交路数据中，批量识别交路。')
            grid.addWidget(btn,0,1,1,1)

            btn = PEToolButton('批量识别',QI(':/identify.png'))
            btn.clicked.connect(self._identify_virtual_trains)
            btn.setToolTip('批量虚拟车次\n'
                           '识别交路中的虚拟车次。如果车次属于本运行图，'
                           '则设为实体车次。')
            grid.addWidget(btn,1,1,1,1)
            group.add_layout(grid)

            group = toolBar.add_group('排图',menu)
            grid = QG()
            btn = PEToolButton('标尺排图',QI(':/edit.png'),large=True)
            btn.clicked.connect(self._add_train_by_ruler)
            btn.setToolTip('标尺排图向导（Ctrl+R）\n'
                           '选择一种标尺，给定各站停车时间，计算时刻')
            grid.addWidget(btn,0,0,2,1)

            btn = PEDockButton('标尺编辑','标尺编辑',QI(':/ruler.png'),
                               self.rulerDockWidget,large=False)
            btn.setToolTip('标尺编辑（Ctrl+B）\n设置各个标尺数据，添加或删除标尺。')
            grid.addWidget(btn,0,1,1,1)
            self.dockToolButtons.append(btn)

            btn = PEToolButton('区间重排',QI(':/exchange.png'))
            btn.clicked.connect(self._change_train_interval)
            btn.setToolTip('区间重排图（Ctrl+Shift+R）\n'
                           '依据标尺，重新铺画某一区间运行线，并覆盖原有时刻。')
            m = QM()
            self.__addMenuAction(m,'区间换线',self._interval_exchange,
                                 '区间换线（Ctrl+5）\n交换两车次区间运行线。')
            btn.setMenu(m)
            grid.addWidget(btn,1,1,1,1)

            btn = PEToolButton('批量复制',QI(':/copy.png'))
            btn.clicked.connect(self._batch_copy_train)
            btn.setToolTip('批量复制运行线（Ctrl+Shift+A）\n'
                           '给定新车次及其始发时刻，批量复制当前车次运行线。')
            grid.addWidget(btn,0,2,1,1)

            btn = PEToolButton('推定时刻',QI(':/add.png'))
            btn.clicked.connect(self._detect_pass_time)
            btn.setToolTip('推定通过站时刻（Ctrl+2）\n'
                           '假定没有时刻信息的中间站都不停靠，依据标尺，'
                           '推定通过站时刻。')
            m = QM()
            self.__addMenuAction(m,'撤销所有推定结果',self._withdraw_detect)
            btn.setMenu(m)
            grid.addWidget(btn,1,2,1,1)
            group.add_layout(grid)

        # 分析 面板
        if True:
            menu = toolBar.add_menu('分析')

            group = toolBar.add_group('线路',menu)
            grid = QG()
            btn = PEToolButton('车站时刻', QI(':/timetable.png'), large=True)
            btn.clicked.connect(self._station_timetable)
            btn.setToolTip('车站时刻表（Ctrl+E）\n'
                           '查看指定车站的时刻表、股道分析图。')
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('区间对数',QI(':/counter.png'))
            btn.clicked.connect(self._interval_count)
            btn.setToolTip('区间对数表（Ctrl+3）\n'
                           '统计本线站点间各个区间的车次数、始发终到车次数等。')
            grid.addWidget(btn,0,1,1,1)

            btn = PEToolButton('区间车次',QI(':/train.png'))
            btn.clicked.connect(self._interval_trains)
            btn.setToolTip('区间车次表（Ctrl+Shift+3）\n'
                           '显示指定区间的车次列表，参照12306查找区间车次的逻辑。')
            grid.addWidget(btn,1,1,1,1)
            group.add_layout(grid)

            group = toolBar.add_group('车次时刻',menu)
            grid = QG()
            btn = PEToolButton('标尺对照', QI(':/ruler.png'), large=True)
            btn.clicked.connect(self._check_ruler_from_menu)
            btn.setToolTip('标尺对照（Ctrl+W）\n'
                           '将当前车次时刻表与指定标尺对比。')
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('事件表', QI(':/clock.png'), large=True)
            btn.clicked.connect(self._train_event_out)
            btn.setToolTip('车次事件表（Ctrl+Z）\n'
                           '显示到开、越行、会让等事件表。')
            grid.addWidget(btn, 0, 1, 2, 1)

            btn = PEToolButton('车次对照', QI(':/compare.png'))
            btn.clicked.connect(self._train_compare)
            btn.setToolTip('两车次对照（Ctrl+Shift+W）\n'
                           '对比两个车次在本线的区间运行时分。')
            grid.addWidget(btn, 1, 2, 1, 1)

            btn = PEToolButton('区间分析', QI(':/data.png'))
            btn.clicked.connect(self._get_interval_info)
            btn.setToolTip('区间数据分析（Ctrl+Shift+Q）\n'
                           '显示列车在指定区间的停站数，均速等信息。')
            grid.addWidget(btn, 0, 2, 1, 1)

            btn = PEToolButton('运行图对比', QI(':/compare.png'),large=True)
            btn.clicked.connect(self._graph_diff)
            btn.setToolTip('运行图对比（Ctrl+6）\n'
                           '对比本运行图和选定运行图（作为新运行图）所有车次的数据。')
            grid.addWidget(btn, 0, 3, 2, 1)

            group.add_layout(grid)

        # 显示 面板
        if True:
            menu = toolBar.add_menu('显示')

            group = toolBar.add_group('',menu)
            grid = QG()
            btn = PEDockButton('显示类型', '显示类型设置', QI(':/filter.png'), self.typeDockWidget)
            btn.setToolTip('显示类型设置（Ctrl+L）\n'
                           '选择要显示的车次种类，或控制上下行车次显示/隐藏。')
            grid.addWidget(btn,0,0,2,1)

            m = QM()
            self.__addMenuAction(m,'高级显示车次设置',self.showFilter.setFilter,
                                 '高级显示车次设置（Ctrl+Shift+L）\n'
                                 '调用通用列车筛选器筛选要显示的车次特征。')
            btn.setMenu(m)

            btn = PEDockButton('运行图设置','运行图设置',QI(':/config.png'),self.configDockWidget)
            btn.setToolTip('运行图设置（Ctrl+G）\n'
                           '主要与显示相关的运行图参数配置。')
            grid.addWidget(btn,0,1,2,1)

            btn = PEDockButton('默认设置','系统默认设置',QI(':/settings.png'),
                               self.sysDockWidget,large=False)
            btn.setToolTip('系统默认设置（Ctrl+Shift+G）\n'
                           '配置针对新运行图和缺省配置的运行图采用的默认参数。')
            grid.addWidget(btn,0,2,1,1)
            group.add_layout(grid)

            group = toolBar.add_group('坐标轴比例', menu)
            grid = QG()
            btn = PEToolButton('水平放大', QI(':/h_expand.png'))
            btn.clicked.connect(self._h_expand)
            grid.addWidget(btn, 0, 0, 1, 1)

            btn = PEToolButton('水平缩小', QI(':/h_shrink.png'))
            btn.clicked.connect(self._h_shrink)
            grid.addWidget(btn, 1, 0, 1, 1)

            btn = PEToolButton('垂直放大', QI(':/v_expand.png'))
            btn.clicked.connect(self._v_expand)
            grid.addWidget(btn, 0, 1, 1, 1)

            btn = PEToolButton('垂直缩小', QI(':/v_shrink.png'))
            btn.clicked.connect(self._v_shrink)
            grid.addWidget(btn, 1, 1, 1, 1)
            group.add_layout(grid)

            group = toolBar.add_group('视图缩放',menu)
            grid = QG()
            btn = PEToolButton('放大视图',QI(':/zoom-in.png'))
            btn.clicked.connect(lambda: self.GraphWidget.scale(1.25, 1.25))
            grid.addWidget(btn,0,0,1,1)

            btn = PEToolButton('缩小视图',QI(':/zoom-out.png'))
            btn.clicked.connect(lambda: self.GraphWidget.scale(0.8, 0.8))
            grid.addWidget(btn,1,0,1,1)
            group.add_layout(grid)

            group = toolBar.add_group('更新', menu)
            grid = QG()

            btn = PEToolButton('刷新', QI(':/refresh.png'), large=True)
            btn.clicked.connect(self._refresh_graph)
            btn.setToolTip('刷新运行图（F5）\n'
                           '重新铺画运行图，并更新所有停靠面板数据。\n'
                           '当数据出现不同步异常时，可以调用此功能。')
            grid.addWidget(btn, 0, 0, 2, 1)

            btn = PEToolButton('重新铺画', QI(':/brush.png'))
            btn.clicked.connect(lambda: self.GraphWidget.paintGraph(force=True))
            btn.setToolTip('立即重新铺画运行图（Shift+F5）\n'
                           '强制重新铺画运行图，但不更新停靠面板数据。')
            grid.addWidget(btn, 0, 1, 1, 1)

            btn = PEToolButton('重新读取', QI(':/exchange.png'))
            btn.clicked.connect(self._reset_graph)
            btn.setToolTip('重新读取当前运行图\n'
                           '放弃所有未保存更改，重新从文件中读取本运行图。')
            grid.addWidget(btn, 1, 1, 1, 1)
            group.add_layout(grid)


        self.addToolBar(toolBar)

    def _refreshSelectedTrainCombo(self):
        self.updating=True
        self.selectTrainCombo.clear()
        for train in self.graph.trains():
            self.selectTrainCombo.addItem(train.fullCheci())
        if self.currentTrain():
            self.selectTrainCombo.setCurrentText(self.currentTrain().fullCheci())
        self.updating = False

    def _h_expand(self):
        if self.graph.UIConfigData()['seconds_per_pix']>1:
            self.graph.UIConfigData()['seconds_per_pix']-=1
        self.GraphWidget.paintGraph()
        self.configWidget.setData()

    def _h_shrink(self):
        self.graph.UIConfigData()['seconds_per_pix'] += 1
        self.GraphWidget.paintGraph()
        self.configWidget.setData()

    def _v_expand(self):
        if self.graph.ordinateRuler():
            if self.graph.UIConfigData()['seconds_per_pix_y']>1:
                self.graph.UIConfigData()['seconds_per_pix_y']-=1
        else:
            self.graph.UIConfigData()['pixes_per_km']+=1
        self.GraphWidget.paintGraph()
        self.configWidget.setData()

    def _v_shrink(self):
        if self.graph.ordinateRuler():
            self.graph.UIConfigData()['seconds_per_pix_y']+=1
        else:
            if self.graph.UIConfigData()['pixes_per_km'] > 1:
                self.graph.UIConfigData()['pixes_per_km']-=1
        self.GraphWidget.paintGraph()
        self.configWidget.setData()

    def _newGraph(self):
        flag = QtWidgets.QMessageBox.question(self, self.title, "是否保存对运行图的修改？",
                                              QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                                              QtWidgets.QMessageBox.Cancel)
        if flag == QtWidgets.QMessageBox.Yes:
            self._saveGraph()
        elif flag == QtWidgets.QMessageBox.No:
            pass
        else:
            return

        self.graph.clearAll()
        self.GraphWidget.graph = self.graph
        self.GraphWidget.paintGraph()
        self._refreshDockWidgets()
        self.setWindowTitle(f"{self.title}   {self.graph.filename if self.graph.filename else '新运行图'}")

    def _openGraph(self):
        flag = QtWidgets.QMessageBox.question(self, self.title, "是否保存对运行图的修改？",
                                              QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                                              QtWidgets.QMessageBox.Cancel)
        if flag == QtWidgets.QMessageBox.Yes:
            self._saveGraph()
        elif flag == QtWidgets.QMessageBox.No:
            pass
        else:
            return

        filename,ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC运行图文件(*.pyetgr;*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')
        if not ok:
            return
        self.open_graph_ok(filename)

    def open_graph_ok(self,filename:str):
        self.GraphWidget._line_un_selected()
        self.graph.clearAll()
        self.showFilter.setGraph(self.graph)
        try:
            self.graph.loadGraph(filename)
            if 'DB' in self.graph.version():
                if not self.question('此文件可能被标记为数据库文件。如果没有特殊目的，'
                                    'pyETRC不建议您直接打开数据库文件（尽管这是可以的），'
                                    '而是使用ctrl+D向既有线路中导入车次。是否继续打开此文件？'):
                    return
            elif self.graph.version() > self.version:
                if not self.question(f'此文件可能由高于当前软件版本的pyETRC保存。如果继续打开并保存此文件，'
                                    f'可能损失一些新版本的信息。是否确认打开此文件？'
                                    f'当前软件版本：{self.version}；文件标记版本：{self.graph.version()}'):
                    return
            self.GraphWidget.setGraph(self.graph)
            self._system["last_file"] = filename
            # print("last file changed")
        except:
            self._derr("文件错误！请检查")
            traceback.print_exc()
        else:
            # self._initDockWidgetContents()
            self._refreshDockWidgets()
            self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")
            self._checkGraph()
        self.statusOut('就绪')

    def _outputGraph(self):
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
                                                             caption='导出运行图',
                                                             directory=self.graph.lineName(),
                                                             filter="图像(*.png)")
        if not filename or not ok:
            return
        self.GraphWidget.save(filename, f"由{self.name}{self.version}导出")
        self._dout("导出成功！")

    def _outputPdf(self):
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
                                                             caption='导出pdf运行图',
                                                             directory=self.graph.lineName(),
                                                             filter="PDF图像(*.pdf)")
        if not filename or not ok:
            return
        if self.GraphWidget.savePdf(filename, f"由{self.name}{self.version}导出"):
            self._dout("导出PDF成功！")

    def _outExcel(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, caption='导出运行图', filter="Excel文件(*.xlsx)")[0]
        if not filename:
            return
        self.graph.save_excel(filename)
        self._dout("导出完毕")

    def _saveGraph(self):
        filename = self.graph.graphFileName()
        # status: QtWidgets.QStatusBar = self.statusBar()
        self.statusOut("正在保存")
        if not self.graph.graphFileName():
            filename, ok = QtWidgets.QFileDialog.getSaveFileName(self, "选择文件",
                                                                 directory=self.graph.lineName() + '.pyetgr',
                                                                 filter='pyETRC运行图文件(*.pyetgr;*.json)\n所有文件(*.*)')
            if not ok:
                return
        self.graph.setVersion(self.version)
        self.graph.save(filename)
        self.graph.setGraphFileName(filename)
        self.statusOut("保存成功")
        self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")

    def _saveGraphAs(self):
        """
        另存为
        """
        filename,ok = QtWidgets.QFileDialog.getSaveFileName(self, "另存为...", directory=self.graph.lineName() + '.pyetgr',
                                                         filter='pyETRC运行图文件(*.pyetgr;*.json)\n所有文件(*.*)')
        if not ok:
            return
        self.statusOut("正在保存")
        self.graph.setVersion(self.version)
        self.graph.save(filename)
        self.graph.setGraphFileName(filename)
        self.statusOut("保存成功")
        self._system["last_file"] = filename
        self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")

    def _toTrc(self):
        """
        先显示提示信息，然后导出为trc。
        """
        text = "注意：显著的信息丢失。由于ETRC运行图格式不支持本系统的部分功能，导出的.trc格式运行图包含的信息少于本系统的.pyetgr/.json格式运行图。这就是说，若先导出.trc格式，再用本系统读取该文件，仍将造成显著的信息丢失。本功能不改变原运行图，只是导出一个副本。请确认知悉以上内容，并继续。"
        self._dout(text)
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self, "选择文件", directory=self.graph.lineName() + '.trc',
                                                             filter='ETRC运行图文件(*.trc)\n所有文件(*.*)')
        if not ok:
            return
        self.graph.toTrc(filename)

    def _reset_graph(self):
        flag = self.question("重新从文件中读取本运行图，所有未保存数据都将丢失，未保存过的运行图将重置为空运行图！"
                            "是否继续？")
        if not flag:
            return

        filename = self.graph.filename
        self.graph.clearAll()
        if not filename:
            self.GraphWidget.graph = self.graph
        else:
            try:
                self.graph.loadGraph(filename)
            except:
                self._derr("文件错误！请检查。")
        self.GraphWidget.scene.clear()
        self.GraphWidget.paintGraph()
        self._refreshDockWidgets()

    def _refresh_graph(self):
        self.statusOut("正在刷新数据")
        self.graph.refreshData()
        self.GraphWidget.paintGraph(force=True)
        self._refreshDockWidgets()
        self.statusOut('就绪')

    def _about(self):
        text = f"{self.title}  release {self.release}\n{self.date} \n六方车迷会谈 萧迩珀  保留一切权利\n"
        text += "联系方式： 邮箱 mxy0268@qq.com"
        text += '\n本系统官方交流群：865211882'
        text += '\n本系统在线文档：http://xep0268.top/pyetrc/doc'
        QtWidgets.QMessageBox.about(self, '关于', text)

    def _function_list(self):
        dialog = HelpDialog(self.graph,self.version, self)
        dialog.exec_()

    def statusOut(self, note: str, seconds: int = 0):
        self.statusBar().showMessage(f"{datetime.now().strftime('%H:%M:%S')} {note}", seconds)

    def on_focus_changed(self, train: Train):
        """
        slot。由GraphicsWidget中选中列车变化触发。改变trainWidget中的行，最终也会触发这里。
        """
        if train is None:
            return

        # 设置train编辑中的current
        self.trainWidget.setCurrentTrain(train)

        # 2019.03.24调整，移动到trainWidget的行号变化里面。
        # 设置currentWidget
        # if self.currentDockWidget.isVisible():
        #     # 2019.02.03增加：提高效率，只有currentWidget显示的时候才设置数据
        #     self.currentWidget.setData(train)

    def _current_train_changed(self, train: Train):
        """
        tableWidget选中的行变化触发。第一个参数是行数有效，其余无效。
        2018.12.28修改：把解读车次的逻辑放入trainWidget中。这里直接接受列车对象.
        2.0版本修改：把currentWidget信息变化的调用从Graphics那边的槽函数挪到这里。防止没有运行线的车不能显示。
        """
        if self.updating:
            return
        self.updating = True
        # print("current train changed. line 1708", row,train.fullCheci())

        # 取消不响应非显示列车的逻辑。2018年11月20日
        """
        if not train.isShow():
            return
            """

        focus = True
        # 这是为了避免间接递归。若不加检查，这里取消后再次引发改变，则item选中两次。
        if self.GraphWidget.selectedTrain is not train:
            self.GraphWidget._line_un_selected()
            focus = False
        self.selectTrainCombo.setCurrentText(train.fullCheci())

        self.setCurrentTrain(train)
        self.GraphWidget._line_selected(train.firstItem(), focus)  # 函数会检查是否重复选择
        self._updateCurrentTrainRelatedWidgets(train,force=False)
        self.updating = False

    def _updateCurrentTrainRelatedWidgets(self,train:Train,force=True,sender=-1):
        """
        更新与当前车次有关的几个面板。force=False时仅更新显示的面板。
        sender: 表示发来信号的窗口，是避免interactive间接递归。
        0-currentWidget; 1-trainInfoWidget; 2-trainTimetableWidget; 3-interactiveTimetableWidget.
        """
        if force or self.currentWidget.isVisible():
            self.currentWidget.setData(train)
        if force or self.trainInfoWidget.isVisible():
            self.trainInfoWidget.setData(train)
        if force or self.trainTimetableWidget.isVisible():
            self.trainTimetableWidget.setData(train)
        if force or self.interactiveTimetableWidget.isVisible() and sender != 3:
            self.interactiveTimetableWidget.setData(train)

    def _add_train_by_ruler(self):
        """
        标尺排图向导
        """
        if not self.graph.rulerCount():
            self._derr("标尺排图向导：无可用标尺！")
            return

        painter = rulerPainter(self.GraphWidget)
        self.rulerPainter = painter
        painter.trainOK.connect(self._updateCurrentTrainRelatedWidgets)
        painter.trainOK.connect(self.trainWidget.addTrain)
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("标尺排图向导")
        dock.setWidget(painter)
        dock.setFeatures(dock.DockWidgetMovable | dock.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.NoDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)
        dock.resize(700, 800)
        self.rulerPainterDock = dock
        painter.WindowClosed.connect(self._ruler_paint_cleanup)

    def _ruler_paint_cleanup(self):
        self.removeDockWidget(self.rulerPainterDock)
        self.rulerPainter = None
        self.rulerPainterDock = None

    def _change_train_interval(self):
        """
        当前车次区间时刻表重排，ctrl+shift+R。先选择区间，然后调起标尺排图向导。
        """
        train = self.currentTrain()
        if train is None:
            self._derr('当前车次区间时刻重排：当前没有选中的车次！')
            return
        if not self.graph.rulerCount():
            self._derr("当前车次区间时刻重排：无可用标尺！")
            return
        dialog = ChangeTrainIntervalDialog(train, self.graph, self)
        dialog.trainChangeOk.connect(self._change_train_interval_ok)
        self.changeTrainIntervalDialog = dialog
        dialog.exec_()

    def _change_train_interval_ok(self, train: Train, anTrain: Train):
        self.GraphWidget.delTrainLine(anTrain)
        self.GraphWidget.repaintTrainLine(train)
        self._updateCurrentTrainRelatedWidgets(train)
        self.trainWidget.updateRowByTrain(train)
        self.graph.delTrain(anTrain)
        self.statusOut('车次调整完毕')
        del self.changeTrainIntervalDialog

    def _read_ruler_from_trains(self):
        wizard = ReadRulerWizard(self.graph,self)
        wizard.rulerFinished.connect(self._read_ruler_from_trains_ok)
        wizard.exec_()

    def _read_ruler_from_trains_ok(self,ruler:Ruler, isNew:bool):
        if isNew:
            self.graph.addRuler(ruler)
        self.rulerWidget.setData()

    def _station_timetable(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("导出车站时刻表")
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel("请选择要输出时刻表的车站")
        layout.addWidget(label)

        listWidget = QtWidgets.QListWidget()
        for name in self.graph.stations():
            item = QtWidgets.QListWidgetItem(name)
            listWidget.addItem(item)
        layout.addWidget(listWidget)

        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        layout.addLayout(hlayout)
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(lambda: self._station_timetable_ok(listWidget))
        listWidget.itemDoubleClicked.connect(btnOk.click)

        dialog.setLayout(layout)
        dialog.exec_()

    def _station_timetable_ok(self, listWidget: QtWidgets.QListWidget):
        self.sender().parentWidget().close()
        try:
            station_name = listWidget.selectedItems()[0].text()
        except:
            self._derr("请先选择车站！")
            return

        dialog = StationTimetable(self.graph, station_name, self)
        dialog.showStatusInfo.connect(self.statusOut)
        dialog.exec_()

    def _interval_count(self):
        """
        计算区间停站车次数量
        """
        dialog = IntervaLCountDialog(self.graph, self)
        dialog.exec_()

    def _reverse_graph(self):
        flag = self.question("将本线上下行交换，所有里程交换。是否继续？\n"
                            "此功能容易导致上下行逻辑混乱，除非当前运行图上下行错误，否则不建议使用此功能。\n"
                            "车站原里程和对里程也将同时交换。如果原来缺少对里程数据，则默认用原里程覆盖。")
        if not flag:
            return
        self.graph.reverse()
        self.GraphWidget.paintGraph()
        self._refreshDockWidgets()
        self.lineWidget.apply_line_info_change()  # 临时增加。解决标尺窗口似乎没有及时更新的问题。

    def _line_info_out(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("线路信息")
        dialog.resize(400, 400)
        layout = QtWidgets.QVBoxLayout()
        text = ""
        text += f"线名：{self.graph.lineName()}\n"
        text += f"文件名：{self.graph.filename}\n"
        text += f"里程：{self.graph.lineLength()}km\n"
        text += f"起点站：{self.graph.firstStation()}\n"
        text += f"终点站：{self.graph.lastStation()}\n"
        text += f"站点数：{self.graph.stationCount()}\n"
        text += f"车次数：{self.graph.trainCount()}\n"
        text += f"下行车次数：{self.graph.downTrainCount()}\n"
        text += f"上行车次数：{self.graph.upTrainCount()}\n"

        textView = QtWidgets.QTextBrowser()
        textView.setText(text)
        layout.addWidget(textView)

        btnClose = QtWidgets.QPushButton("关闭")
        # btnClose.setMaximumWidth(100)
        btnClose.clicked.connect(dialog.close)
        layout.addWidget(btnClose)
        layout.setAlignment(Qt.AlignCenter)

        dialog.setLayout(layout)
        dialog.exec_()

    def _interval_trains(self):
        """
        给出区间车次表，类似12306查询车票
        """
        dialog = IntervalTrainDialog(self.graph, self)
        dialog.exec_()

    def _ruler_table(self):
        w = RulerTable(self.graph)
        d = DialogAdapter(w)
        d.exec_()

    def _search_from_menu(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "搜索车次", "请输入车次：")
        if ok:
            self._search_train(name)

    def _multi_search_train(self):
        """
        模糊检索车次
        """
        name, ok = QtWidgets.QInputDialog.getText(self, "模糊检索", "请输入车次：")
        if not ok:
            return
        selected_train = self.graph.multiSearch(name)
        if not selected_train:
            self._derr("无满足条件的车次！")
            return

        if len(selected_train) >= 2:
            checi, ok = QtWidgets.QInputDialog.getItem(self, "选择车次", "有下列车次符合，请选择：",
                                                       [train.fullCheci() for train in selected_train])
            if not ok:
                return
            train = self.graph.trainFromCheci(checi, full_only=True)
            if train is None:
                self._derr("非法车次！")
                return
        else:
            # 唯一匹配
            train = selected_train[0]

        self.GraphWidget._line_un_selected()
        train.setIsShow(True, affect_item=True)
        if train.item is None:
            self.GraphWidget.addTrainLine(train)

        self.GraphWidget._line_selected(train.item, ensure_visible=True)
        self.setCurrentTrain(train)

    def closeEvent(self, event):
        """
        """
        flag = QtWidgets.QMessageBox.question(self, self.title, "是否保存对运行图的修改？",
                                              QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                                              QtWidgets.QMessageBox.Cancel)
        if flag == QtWidgets.QMessageBox.Yes:
            self._saveGraph()
            event.accept()
        elif flag == QtWidgets.QMessageBox.No:
            event.accept()
        else:
            event.ignore()
            return

        if self.rulerPainter is not None:
            self.rulerPainter._cancel()
        # 记录各个dock的状态
        for name, dock in self.action_widget_dict.items():
            self._system.setdefault("dock_show", {})[name] = dock.isVisible()
        self._saveSystemSetting()

    def _check_ruler_from_menu(self):
        train = self.currentTrain()
        if train is None:
            self._derr("当前没有选中车次！")
            return
        self._check_ruler(train)

    def _train_compare(self):
        """
        两车次运行对照
        """
        dialog = TrainComparator(self.graph, self)
        dialog.exec_()

    def _get_interval_info(self):
        """
        计算当前车次在选定区间内的主要性质，参见ctrl+Q面板。sample:
        """
        train = self.currentTrain()
        if train is None:
            self._derr("当前没有选中车次！")
            return
        dialog = IntervalWidget(self.graph, self)
        dialog.setTrain(train)
        dialog.exec_()

    def _reset_start_end(self):
        flag = self.question("将本线所有列车始发站设置时刻表首站、终到站设置为时刻表末站，是否继续？")
        if not flag:
            return
        for train in self.graph.trains():
            train.setStartEnd(train.firstStation(), train.endStation())
        self.trainWidget.updateAllTrains()
        self.statusOut("始发终到站重置成功")

    def _auto_start_end(self):
        """
        自动推广适配始发终到站，通过修改符合一定条件的车次的始发站。例如成都东->成都东达成场。
        """
        text = "遍历所有车次，当车次满足以下条件时，将该车次的始发站调整为在本线的第一个车站，终到站调整为" \
               "在本线的最后一个车站。\n（1）该车次在本线的第一个（最后一个）车站是时刻表中的" \
               "第一个（最后一个）站；\n（2）该车次时刻表中第一个（最后一个）站站名形式符合：" \
               "“{A}xx场”格式，其中A表示车次信息中的始发（终到）站。\n" \
               "是否继续？"
        if not self.question(text):
            return
        for train in self.graph.trains():
            train.autoStartEnd()
        self.trainWidget.updateAllTrains()
        self._dout('自动设置完成！可手动重新铺画运行图（shift+F5）以查看效果。')

    def _graph_diff(self):
        dialog = GraphDiffDialog(self.graph,self)
        dialog.exec_()

    def _joint_graph(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("线路拼接")
        layout = QtWidgets.QFormLayout()

        label = QtWidgets.QLabel("将本线与另一条线的站表拼接，并拼接所有车次时刻表（可选）。"
                                 "请注意，本运行图中所有车次的非本线站点时刻表信息都将被清除。")
        label.setWordWrap(True)
        layout.addRow(label)

        hlayout = QtWidgets.QHBoxLayout()
        fileEdit = QtWidgets.QLineEdit()
        fileEdit.setEnabled(False)
        dialog.fileEdit = fileEdit
        btnOpen = QtWidgets.QPushButton("浏览")
        hlayout.addWidget(fileEdit)
        hlayout.addWidget(btnOpen)
        btnOpen.clicked.connect(lambda: self._joint_select(dialog))
        layout.addRow("文件名", hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        group = QtWidgets.QButtonGroup()
        radio1 = QtWidgets.QRadioButton("置于本线之前")
        radio2 = QtWidgets.QRadioButton("置于本线之后")
        group.addButton(radio1)
        group.addButton(radio2)
        hlayout.addWidget(radio1)
        hlayout.addWidget(radio2)
        layout.addRow("连接顺序", hlayout)
        dialog.radio1 = radio1
        radio1.setChecked(True)

        vlayout = QtWidgets.QVBoxLayout()
        checkReverse = QtWidgets.QCheckBox("线路上下行交换")
        dialog.checkReverse = checkReverse
        checkLineOnly = QtWidgets.QCheckBox("仅导入线路(不导入车次)")
        dialog.checkLineOnly = checkLineOnly
        vlayout.addWidget(checkReverse)
        vlayout.addWidget(checkLineOnly)
        layout.addRow("高级", vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定(&Y)")
        btnCancel = QtWidgets.QPushButton("取消(&C)")
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(lambda: self._joint_ok(dialog))
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        layout.addRow(hlayout)

        dialog.setLayout(layout)
        dialog.exec_()

    def _joint_select(self, dialog):
        """
        选择文件
        """
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC运行图文件(*.pyetgr;*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')[0]
        if not filename:
            return

        dialog.fileEdit.setText(filename)

    def _joint_ok(self, dialog):
        filename = dialog.fileEdit.text()
        if not filename:
            self._derr("请选择文件！")
            return
        graph_another = Graph()
        try:
            graph_another.loadGraph(filename)
        except:
            self._derr("文件无效，请检查！")
            return

        former = dialog.radio1.isChecked()
        reverse = dialog.checkReverse.isChecked()
        line_only = dialog.checkLineOnly.isChecked()

        self.statusOut("正在更新运行图信息")
        self.graph.setOrdinateRuler(None)

        self.graph.jointGraph(graph_another, former, reverse, line_only)
        self.GraphWidget.paintGraph()
        self._refreshDockWidgets()
        self.statusOut("就绪")
        dialog.close()

    def _reset_business(self):
        if not self.question('此操作将重置所有列车营业站信息，手动手动设置的营业站信息将丢失。是否继续？'):
            return
        if not self.question('再次确认，您是否确实要重置所有列车营业站信息？此操作不可撤销。'):
            return
        for train in self.graph.trains():
            train.autoBusiness()
        self.statusOut('重置营业站信息完毕')

    def _reset_passenger(self):
        if not self.question('按系统设置中的“类型管理”信息设置所有列车的“是否旅客列车”字段为'
                            '“是”或者“否”。此操作有助于提高效率，但今后修改类型管理信息时，'
                            '车次的数据不会随之更新。是否继续？'):
            return
        for train in self.graph.trains():
            if train.isPassenger() == train.PassengerAuto:
                train.setIsPassenger(train.isPassenger(detect=True))
        self.statusOut('自动设置旅客列车信息完毕')

    def _auto_type(self):
        if not self.question('按照所有列车的车次（全车次），根据本系统规定的正则判据，重置所有列车的类型。'
                            '是否继续？'):
            return
        for train in self.graph.trains():
            train.autoTrainType()

    def _delete_all(self):
        if not self.question('删除本图中所有车次，以便重新导入或铺画，此操作不可撤销。'
                            '是否继续？'):
            return
        self.graph.clearTrains()
        self.GraphWidget.paintGraph()
        self._refreshDockWidgets()

    def _delete_non_local(self):
        if not self.question('删除所有列车时刻表中不在本线的站点，此操作不可撤销。'
                            '是否继续？'):
            return
        self.graph.delAllNonLocalStations()
        self.GraphWidget.paintGraph()
        self._refreshDockWidgets()

    def _batch_parse_circuits(self):
        self.circuitWidget.batch_parse()

    def _identify_virtual_trains(self):
        self.circuitWidget.identify()

    def _view_line_data(self):
        class T(DialogAdapter):
            def keyPressEvent(self, event: QtGui.QKeyEvent):
                """
                禁用ESC退出
                """
                if event.key() != Qt.Key_Escape:
                    super().keyPressEvent(event)
                else:
                    self.close()

            def closeEvent(self, event: QtGui.QCloseEvent):
                # if self.toSave:
                if self.widget.checkUnsavedLib():
                    event.ignore()
                    return
                event.accept()

        dialog = LineLibWidget(self.graph.sysConfigData()['default_db_file'],fromPyetrc=True)
        dialog.DefaultDBFileChanged.connect(self._default_db_file_changed)
        dialog.ExportLineToGraph.connect(self._import_line_from_db)
        adapter = T(dialog,self,False)
        adapter.exec_()

    def _default_db_file_changed(self,name):
        self.graph.sysConfigData()['default_db_file'] = name
        self.graph.saveSysConfig()

    def _import_line_from_db(self,line:Line):
        self.graph.line.copyData(line, True)
        self.graph.resetAllItems()
        self.graph.setOrdinateRuler(None)
        self.GraphWidget.paintGraph()
        self._refreshDockWidgets()
        self.statusOut("导入线路数据成功")

    def _view_line_data_old(self):
        lineDB = LineDB()
        lineDB.resize(1100, 700)
        lineDB.exec_()

    def _adjust_train_time(self):
        """
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('调整当前车次时刻')
        dialog.resize(500,600)
        train = self.currentTrain()
        if train is None:
            self._derr("当前没有选中车次！")
            return

        layout = QtWidgets.QVBoxLayout()

        flayout = QtWidgets.QFormLayout()
        currentLabel = QtWidgets.QLabel(train.fullCheci())
        flayout.addRow("当前车次", currentLabel)

        hlayout = QtWidgets.QHBoxLayout()
        radio1 = QtWidgets.QRadioButton("提早")
        radio2 = QtWidgets.QRadioButton("延后")
        hlayout.addWidget(radio1)
        hlayout.addWidget(radio2)
        radio1.setChecked(True)
        dialog.radio = radio1
        flayout.addRow("调整方向", hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        spinMin = QtWidgets.QSpinBox()
        spinMin.setRange(0, 9999)
        spinSec = QtWidgets.QSpinBox()
        spinSec.setSingleStep(10)
        spinSec.setRange(0, 59)
        label = QtWidgets.QLabel('分')
        label.setFixedWidth(20)
        hlayout.addWidget(spinMin)
        hlayout.addWidget(label)
        hlayout.addWidget(spinSec)
        label = QtWidgets.QLabel('秒')
        label.setFixedWidth(20)
        hlayout.addWidget(label)
        flayout.addRow("调整时间", hlayout)

        dialog.spinMin = spinMin
        spinMin.setMaximumWidth(100)
        dialog.spinSec = spinSec
        spinSec.setMaximumWidth(80)

        layout.addLayout(flayout)

        label = QtWidgets.QLabel('提示：请在下表中选择要调整时刻的站，到发时刻同时调整。如果不选择，则没有时刻会被调整。')
        label.setWordWrap(True)
        layout.addWidget(label)

        listWidget = QtWidgets.QListWidget()
        listWidget.setSelectionMode(listWidget.MultiSelection)
        for name, ddsj, cfsj in train.station_infos():
            ddsj_str = ddsj.strftime('%H:%M:%S')
            cfsj_str = cfsj.strftime('%H:%M:%S')
            if (cfsj - ddsj).seconds == 0:
                cfsj_str = '...'

            item = QtWidgets.QListWidgetItem(f"{name}\t{ddsj_str}/{cfsj_str}")
            item.setData(-1, name)
            listWidget.addItem(item)
            item.setSelected(True)
        dialog.listWidget = listWidget

        layout.addWidget(listWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        btnOk.clicked.connect(lambda: self._adjust_ok(dialog))
        btnCancel.clicked.connect(dialog.close)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        layout.addLayout(hlayout)

        dialog.setLayout(layout)
        dialog.exec_()

    def _adjust_ok(self, dialog):
        train: Train = self.currentTrain()
        spinMin: QtWidgets.QSpinBox = dialog.spinMin
        spinSec: QtWidgets.QSpinBox = dialog.spinSec
        radio: QtWidgets.QRadioButton = dialog.radio
        listWidget: QtWidgets.QListWidget = dialog.listWidget
        ds_int = spinMin.value() * 60 + spinSec.value()
        if radio.isChecked():
            ds_int = -ds_int

        for item in listWidget.selectedItems():
            name = item.data(-1)
            train.setStationDeltaTime(name, ds_int)

        self.GraphWidget.repaintTrainLine(train)
        self._updateCurrentTrainRelatedWidgets(train)
        dialog.close()

    def _import_line(self):
        try:
            self.statusOut("正在读取数据库文件……")
            fp = open('lines.json', encoding='utf-8', errors='ignore')
            line_dicts = json.load(fp)
        except:
            self._derr("线路数据库文件错误！请检查lines.json文件。此功能已被标记过时，请在新版的线路数据库维护中，选择“导出到运行图”来完成此功能。")
            self.statusOut('就绪')
            return

        lines = []

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('导入线路')

        vlayout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel("导入数据库中的线路作为本运行图线路。当前线路数据都将丢失！")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        progessDialog = QtWidgets.QProgressDialog()
        progessDialog.setMinimum(0)
        total = len(line_dicts)
        progessDialog.setRange(0, total)
        progessDialog.setWindowModality(Qt.WindowModal)
        progessDialog.setWindowTitle(self.tr("正在读取线路信息"))

        self.statusOut("正在解析线路数据……")
        listWidget = QtWidgets.QListWidget()
        count = 0

        for name, line_dict in line_dicts.items():
            count += 1
            line = Line(origin=line_dict)
            lines.append(line)
            # widget = QtWidgets.QWidget()
            item = QtWidgets.QListWidgetItem(f"{count} {name}")

            listWidget.addItem(item)
            progessDialog.setValue(count)
            progessDialog.setCancelButtonText(self.tr('取消'))
            if progessDialog.wasCanceled():
                return
            progessDialog.setLabelText(self.tr(f"正在载入线路数据：{name} ({count}/{total})"))
            QtCore.QCoreApplication.processEvents()
            self.statusOut(f"读取线路数据：{name}")
        self.statusOut("读取线路数据成功")

        vlayout.addWidget(listWidget)

        dialog.listWidget = listWidget
        dialog.lines = lines

        btnOk = QtWidgets.QPushButton("确定")
        listWidget.itemDoubleClicked.connect(lambda: self._import_line_ok(dialog))
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        btnOk.clicked.connect(lambda: self._import_line_ok(dialog))
        btnCancel.clicked.connect(dialog.close)
        vlayout.addLayout(hlayout)

        dialog.setLayout(vlayout)
        dialog.exec_()

    def _import_line_ok(self, dialog):
        """
        2019.03.19新增：先选择车站再导入。
        """
        listWidget = dialog.listWidget
        lines = dialog.lines
        line = lines[listWidget.currentRow()]

        stDialog = QtWidgets.QDialog(dialog)
        stDialog.setWindowTitle('选择车站')
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("请在下表中选择要导入的车站（按ctrl或shift或直接拖动来多选），"
                                 "或直接选择下方的“全选”。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        listWidget = QtWidgets.QListWidget()
        listWidget.setSelectionMode(listWidget.MultiSelection)
        for st in line.stationDicts():
            name, mile = st["zhanming"], st["licheng"]
            listWidget.addItem(f"{mile} km  {name}")
        vlayout.addWidget(listWidget)
        stDialog.listWidget = listWidget

        btnOk = QtWidgets.QPushButton("确定")
        btnAll = QtWidgets.QPushButton("全选")
        btnCancel = QtWidgets.QPushButton("取消")

        btnOk.clicked.connect(lambda: self._import_line_stations(line, dialog, stDialog, False))
        btnAll.clicked.connect(lambda: self._import_line_stations(line, dialog, stDialog, True))
        btnCancel.clicked.connect(stDialog.close)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnAll)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)

        stDialog.setLayout(vlayout)
        stDialog.exec_()

    def _import_line_stations(self, line: Line, dialogLines, dialogStations, all: bool = False):
        """
        选择导入的站点后确定。
        """
        newLine = Line(line.name)
        if all:
            newLine.copyData(line, withRuler=True)
        else:
            listWidget: QtWidgets.QListWidget = dialogStations.listWidget
            for idx in listWidget.selectedIndexes():
                row = idx.row()
                newLine.addStationDict(line.stationDictByIndex(row))
            newLine.rulers = line.rulers

        self.graph.line.copyData(line,True)
        self.graph.resetAllItems()
        self.graph.setOrdinateRuler(None)
        self.GraphWidget.paintGraph()
        self._refreshDockWidgets()
        self.statusOut("导入线路数据成功")
        dialogStations.close()
        dialogLines.close()

    def _import_line_excel(self):
        flag = self.question("从Excel表格中导入线路数据，抛弃当前线路数据，是否继续？"
                            "Excel表格应包含四列，分别是站名、里程、等级、对里程（可选），不需要表头。")
        if not flag:
            return

        filename, ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开Excel表",
                                                             filter='Microsoft Excel工作簿(*.xls;*.xlsx)\n所有文件(*)')
        if not ok:
            return
        try:
            from xlrd import open_workbook
        except ImportError:
            traceback.print_exc()
            self._derr("错误：此功能需要'xlrd'库的支持。")
        try:
            wb = open_workbook(filename)
            ws = wb.sheet_by_index(0)
        except:
            self._derr("文件错误，请检查！")
            return

        new_line = Line(name=self.graph.lineName())
        for row in range(ws.nrows):
            try:
                name = ws.cell_value(row, 0)
                mile = float(ws.cell_value(row, 1))
                level = int(ws.cell_value(row, 2))
                try:
                    counter = float(ws.cell_value(row,3))
                except:
                    counter = None
            except:
                pass
            else:
                new_line.addStation_by_info(name, mile, level, counter=counter)
        self.graph.line.copyData(new_line,True)
        self.GraphWidget.paintGraph(throw_error=False)
        self._refreshDockWidgets()
        self._dout("导入成功！")

    def _change_station_name(self):
        dialog = ChangeStationDialog(self.graph, parent=self)
        dialog.OkClicked.connect(self._change_station_name_ok)
        dialog.showStatus.connect(self.statusOut)
        dialog.exec_()

    def _change_station_name_ok(self):
        """
        由dialog信号触发，执行重新铺画等更新操作。
        """
        self.GraphWidget.paintGraph()
        self.trainWidget.updateAllTrains()
        self.lineWidget.updateData()
        self.rulerWidget.updateRulerTabs()
        self.forbidWidget.setData()

        self.statusOut("站名变更成功")

    def _out_domain_info(self):
        """
        检测到域解析符时，输出提示
        """
        self._dout("您使用了域解析符(::)。本程序中域解析符用于分隔站名与场名，在没有完全匹配时生效。"
                   "例如，“成都东::达成场”可以匹配到“成都东”。\n"
                   "请确认您知悉以上内容并继续。\n本提示不影响确认动作的执行。")

    def _import_train_old(self):
        flag = self.question("选择运行图，导入其中所有在本线的车次。您是否希望覆盖重复的车次？"
                            "选择“是”以覆盖重复车次，“否”以忽略重复车次。")

        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC运行图文件(*.pyetgr;*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')[0]
        if not filename:
            return

        graph = Graph()
        try:
            graph.loadGraph(filename)
        except Exception as e:
            self._derr("运行图文件无效，请检查！" + str(repr(e)))
            traceback.print_exc()
            return
        else:
            num = self.graph.addTrainByGraph(graph, flag)
            self.GraphWidget.paintGraph()
            self.trainWidget.addTrainsFromBottom(num)
            self.typeWidget._setTypeList()
            self._dout(f"成功导入{num}个车次。")

    def _import_train(self):
        dialog = ImportTrainDialog(self.graph,parent=self)
        dialog.importTrainOk.connect(self._import_train_ok)
        dialog.exec_()

    def _import_train_ok(self):
        self.GraphWidget.paintGraph()
        self.trainWidget.setData()
        self.circuitWidget.setData()
        self.typeWidget.setData()

    def _import_train_excel(self):
        """
        2020.04.03新增。导入一种指定格式的车次时刻表数据。
        格式：【车次，站名，到达时刻，出发时刻，[股道]，[备注]】
        """
        if not self.question('导入指定格式的车次数据表。表格应有六列，不要表头：\n'
                             '车次，站名，到达时刻，出发时刻，股道（可选），备注（可选）\n'
                             '其中车次必须是全车次。各行数据将按顺序插入到车次时刻表中；如果车次不存在，将'
                             '新建车次。\n'
                             '所选工作簿的每个工作表都会被导入。\n'
                             '是否确认继续？'):
            return
        filename, ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开Excel表",
                                                             filter='Microsoft Excel工作簿(*.xls;*.xlsx)\n所有文件(*)')
        if not ok:
            return
        try:
            suc,fail,new = self.graph.importTrainFromExcel(filename)
            self._dout(f'成功导入{suc}条时刻数据，并新建{new}个车次。另有{fail}条数据导入失败。\n'
                       f'详细导入报错请看控制台。')
            if suc:
                self.GraphWidget.paintGraph()
                self._refreshDockWidgets()
        except Exception as e:
            self._derr('导入错误：\n'+repr(e))

    def _import_train_real(self):
        flag = self.question("选择运行图，导入其中所有在本线的车次，车次前冠以“R”，类型为“实际”。是否继续？")
        if not flag:
            return

        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC运行图文件(*.pyetgr;*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')[0]
        if not filename:
            return

        graph = Graph()
        try:
            graph.loadGraph(filename)
        except:
            self._derr("运行图文件无效，请检查！")
            return
        else:
            for train in graph.trains():
                train.setCheci('R' + train.fullCheci(), 'R' + train.downCheci(), 'R' + train.upCheci())
                train.setType('实际')
            num = self.graph.addTrainByGraph(graph)
            self._dout(f"成功导入{num}个车次的实际运行线。")
            self.GraphWidget.paintGraph()
            self._refreshDockWidgets()

    def _change_massive_station(self):
        """
        显示table，批量映射站名。
        list<dict>
        dict {
            'origin':str,  //原始名称
            'station_field':str,  //站::场
        """
        dialog = BatchChangeStationDialog(self.graph, self)
        dialog.showStatus.connect(self.statusOut)
        dialog.changeApplied.connect(self._apply_station_map)
        dialog.exec_()

    def _apply_station_map(self):
        """
        由dialog的信号触发。
        """
        self.GraphWidget.paintGraph()
        self.lineWidget.updateData()
        self.trainWidget.updateAllTrains()

    def _detect_pass_time(self):
        if not self.graph.rulerCount():
            self._derr("推定通过时刻：请先添加标尺！")
            return
        else:
            if not self.question('此操作将删除要推定时刻列车时刻表中【非本线】的站点，是否继续？'):
                return
        dialog = DetectWidget(self, self)
        dialog.okClicked.connect(self._detect_ok)
        dialog.exec_()

    def _detect_ok(self):
        self._dout('计算完毕！')
        self.GraphWidget.paintGraph()
        self._updateCurrentTrainRelatedWidgets(self.currentTrain())

    def _withdraw_detect(self):
        if not self.question('此操作将删除时刻表中所有备注为“推定”的站，无论是否是由系统推定添加的。此操作不可撤销，是否继续？'):
            return
        for train in self.graph.trains():
            train.withdrawDetectStations()
        self.GraphWidget.paintGraph()
        self._updateCurrentTrainRelatedWidgets(self.currentTrain())


    def _correction_timetable(self, train=None):
        if not isinstance(train, Train):
            train = self.currentTrain()
        if train is None:
            self._derr('当前车次时刻表重排：当前没有选中车次！')
            return
        dialog = CorrectionWidget(train, self.graph, self)
        dialog.correctionOK.connect(self._correction_ok)
        dialog.exec_()

    def _correction_ok(self, train):
        self._updateCurrentTrainRelatedWidgets(train)
        self.GraphWidget.repaintTrainLine(train)

    def _train_show_filter_ok(self):
        for train in self.graph.trains():
            if self.showFilter.check(train):
                train.setIsShow(True, affect_item=False)
            else:
                train.setIsShow(False, affect_item=False)
        self.trainWidget.updateShow()
        self.GraphWidget.paintGraph()

    def _batch_copy_train(self):
        """
        批量复制列车运行线
        """
        if self.currentTrain() is None:
            self._derr("批量复制当前运行线：当前没有选中车次！")
            return

        train: Train = self.currentTrain()

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f'批量复制运行线*{train.fullCheci()}')
        vlayout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel("批量复制当前车次运行线，请设置需要复制的车次的始发时间和车次。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        flayout = QtWidgets.QFormLayout()
        lineEdit = QtWidgets.QLineEdit()
        lineEdit.setFocusPolicy(Qt.NoFocus)
        lineEdit.setText(train.fullCheci())
        flayout.addRow("当前车次", lineEdit)
        vlayout.addLayout(flayout)

        tableWidget = QtWidgets.QTableWidget()
        dialog.tableWidget = tableWidget
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)

        tableWidget.setColumnCount(2)
        tableWidget.setHorizontalHeaderLabels(('车次', '始发时刻'))
        tableWidget.setColumnWidth(0, 120)
        tableWidget.setColumnWidth(1, 120)

        self._add_batch_copy_line(tableWidget)
        vlayout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton("添加")
        btnDel = QtWidgets.QPushButton("删除")
        btnOk = QtWidgets.QPushButton("应用")
        btnCancel = QtWidgets.QPushButton("关闭")

        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)

        btnAdd.clicked.connect(lambda: self._add_batch_copy_line(tableWidget))
        btnDel.clicked.connect(lambda: tableWidget.removeRow(tableWidget.currentRow()))
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(lambda: self._add_batch_train_ok(dialog))

        dialog.setLayout(vlayout)
        dialog.exec_()

    def _add_batch_copy_line(self, tableWidget: QtWidgets.QTableWidget):
        row = tableWidget.rowCount()
        tableWidget.insertRow(row)

        tableWidget.setRowHeight(row, self.graph.UIConfigData()['table_row_height'])
        timeEdit = QtWidgets.QTimeEdit()
        timeEdit.setDisplayFormat('hh:mm:ss')
        timeEdit.setMinimumSize(1, 1)
        tableWidget.setCellWidget(row, 1, timeEdit)

    def _add_batch_train_ok(self, dialog):
        tableWidget: QtWidgets.QTableWidget = dialog.tableWidget
        train: Train = self.currentTrain()
        start_time = train.start_time()

        failed = []

        for row in range(tableWidget.rowCount()):
            try:
                checi = tableWidget.item(row, 0).text()
            except:
                checi = ''

            timeQ: QtCore.QTime = tableWidget.cellWidget(row, 1).time()
            s_t = datetime(1900, 1, 1, timeQ.hour(), timeQ.minute(), timeQ.second())
            dt = s_t - start_time

            if not checi or self.graph.checiExisted(checi):
                failed.append((checi, s_t))
                continue
            # print(train.fullCheci(),dt)
            new_train = train.translation(checi, dt)
            self.graph.addTrain(new_train)
            self.GraphWidget.addTrainLine(new_train)

        cnt = tableWidget.rowCount() - len(failed)
        print("to add to checi-list:", cnt)
        self.trainWidget.addTrainsFromBottom(cnt)

        text = f"成功复制{cnt}个车次。"
        if failed:
            text += '\n以下信息车次未能成功复制。可能由于车次已经存在，或者车次为空：'
            for checi, s_t in failed:
                text += f'\n{checi if checi else "空"},{s_t.strftime("%H:%M:%S")}'
        self._dout(text)

    def _interval_exchange(self):
        train = self.currentTrain()
        if train is None:
            self._derr("区间换线：当前没有选中车次！")
            return
        dialog = ExchangeIntervalDialog(train, self.graph, self)
        dialog.exchangeOk.connect(self._interval_exchange_ok)
        dialog.exec_()

    def _interval_exchange_ok(self, train1: Train, train2: Train):
        self.GraphWidget.repaintTrainLine(train1)
        self.GraphWidget.repaintTrainLine(train2)
        self.currentWidget.setData(train1)
        self._updateCurrentTrainRelatedWidgets(train1)

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, self.title, note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainGraphWindow()
    mainWindow.show()
    sys.exit(app.exec_())

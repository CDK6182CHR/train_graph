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
"""
import sys
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt
from .graph import Graph
from .ruler import Ruler
from .line import Line
from .train import Train
from datetime import datetime, timedelta
from .forbidWidget import ForbidWidget
from .rulerWidget import RulerWidget
from .currentWidget import CurrentWidget
from .lineWidget import LineWidget
from .trainWidget import TrainWidget
from .trainFilter import TrainFilter
from .configWidget import ConfigWidget
from .typeWidget import TypeWidget
import json
from .GraphicWidget import GraphicsWidget, TrainEventType
from .rulerPaint import rulerPainter
from .stationvisualize import StationGraphWidget
from .lineDB import LineDB
from .intervalWidget import IntervalWidget
from .intervalCountDialog import IntervaLCountDialog
from .intervalTrainDialog import IntervalTrainDialog
from .detectWidget import DetectWidget
from .changeStationDialog import ChangeStationDialog
from .batchChangeStationDialog import BatchChangeStationDialog
from .trainComparator import TrainComparator
from .correctionWidget import CorrectionWidget
import time
from .thread import ThreadDialog
import traceback
import cgitb

cgitb.enable(format='text')

system_file = "system.json"

class mainGraphWindow(QtWidgets.QMainWindow):
    stationVisualSizeChanged = QtCore.pyqtSignal(int)

    def __init__(self,filename=None):
        super().__init__()
        self.name = "pyETRC列车运行图系统"
        self.version = "V2.1.1"
        self.title = f"{self.name} {self.version}"  # 一次commit修改一次版本号
        self.build = '20190519'
        self._system = None
        self.setWindowTitle(f"{self.title}   正在加载")
        self.setWindowIcon(QtGui.QIcon('icon.ico'))
        self.showMaximized()
        self._readSystemSetting()

        self.graph = Graph()
        self._initGraph(filename)
        self.GraphWidget = GraphicsWidget(self.graph,self)

        self.setWindowTitle(f"{self.title}   {self.graph.filename if self.graph.filename else '新运行图'}")

        self.showFilter = TrainFilter(self.graph, self)
        self.showFilter.FilterChanged.connect(self._train_show_filter_ok)

        self.GraphWidget.showNewStatus.connect(self.statusOut)
        self.GraphWidget.focusChanged.connect(self.on_focus_changed)

        self.lineDockWidget = None
        self.configDockWidget = None
        self.sysDockWidget = None
        self.currentDockWidget = None  # 当前选中车次信息
        self.typeDockWidget = None
        self.trainDockWidget = None
        self.rulerDockWidget = None
        self.guideDockWidget = None
        self.forbidDockWidget = None
        self.to_repaint = False

        self.action_widget_dict = {}

        self._initUI()
        self.rulerPainter = None

    def _readSystemSetting(self):
        """
        1.4版本新增函数。
        """
        try:
            with open(system_file,encoding='utf-8',errors='ignore') as fp:
                self._system = json.load(fp)
        except:
            self._system={}
        self._checkSystemSetting()

    def _checkSystemSetting(self):
        """
        1.4版本新增函数。
        """
        system_default = {
            "last_file":'',
            "default_file":'sample.json',
            "dock_show":{}
        }
        system_default.update(self._system)
        self._system = system_default

    def _saveSystemSetting(self):
        """
        1.4版本新增函数
        """
        with open(system_file,'w',encoding='utf-8',errors='ignore') as fp:
            json.dump(self._system,fp,ensure_ascii=False)

    def _initGraph(self,filename=None):
        """
        1.4版本新增函数。按照给定文件、上次打开的文件、默认文件的顺序，初始化系统内置graph。
        """
        for n in (filename,self._system["last_file"],self._system["default_file"]):
            if not n:
                continue
            try:
                self.graph.loadGraph(n)
            except:
                pass
            else:
                return

    def _initUI(self):
        self.statusBar().showMessage("系统正在初始化……")
        self.setCentralWidget(self.GraphWidget)
        self._initMenuBar()
        self._initToolBar()

        self._initDockFrames()
        self._initDockWidgetContents()

        self.statusBar().showMessage("就绪")

    def _initDockFrames(self):
        self._initTrainDock()
        self._initLineDock()
        self._initConfigDock()
        self._initRulerDock()
        self._initTypeDock()
        self._initCurrentDock()
        self._initSysDock()
        self._initForbidDock()
        self.action_widget_dict = {
            '线路编辑': self.lineDockWidget,
            '车次编辑': self.trainDockWidget,
            '选中车次设置': self.currentDockWidget,
            '运行图设置': self.configDockWidget,
            '系统默认设置': self.sysDockWidget,
            '显示类型设置': self.typeDockWidget,
            '标尺编辑': self.rulerDockWidget,
            '天窗编辑': self.forbidDockWidget,
        }

    def _initDockWidgetContents(self):
        self._initTrainWidget()
        self._initConfigWidget()
        self._initLineWidget()
        self._initRulerWidget()
        self._initTypeWidget()
        self._initCurrentWidget()
        self._initSysWidget()
        self._initForbidWidget()
        self._initDockShow()

    def _initDockShow(self):
        """
        1.4版本新增，初始化停靠面板是否显示。
        """
        for key,dock in self.action_widget_dict.items():
            dock.setVisible(self._system['dock_show'].setdefault(key,False))

    def _refreshDockWidgets(self):
        """
        聚合所有停靠面板的更新信息调用。由刷新命令调用。
        要逐步把所有更新替换为专用更新函数，避免创建新对象。
        """
        self.statusOut('停靠面板刷新开始')
        self.trainWidget.setData()
        self.statusOut('车次面板刷新完毕')
        self.configWidget.setData()
        self.statusOut('设置面板刷新完毕')
        self.lineWidget.setData()
        self.statusOut('线路面板刷新完毕')
        self.rulerWidget.updateRulerTabs()  # 效率考虑
        self.statusOut('标尺面板刷新完毕')
        self.typeWidget._setTypeList()
        self.statusOut('类型面板刷新完毕')
        self.currentWidget.setData()
        self.statusOut('当前车次面板刷新完毕')
        self.sysWidget.setData()
        self.statusOut('默认面板刷新完毕')
        self.forbidWidget.setData()
        self.statusOut('所有停靠面板刷新完毕')

    def _initForbidDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("天窗编辑")
        dock.visibilityChanged.connect(lambda: self._dock_visibility_changed("天窗编辑", dock))
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setVisible(False)
        self.forbidDockWidget = dock

    def _initForbidWidget(self):
        widget = ForbidWidget(self.graph.line.forbid)
        self.forbidWidget = widget
        self.forbidDockWidget.setWidget(widget)
        widget.showForbidChanged.connect(self.GraphWidget.on_show_forbid_changed)
        widget.currentShowedChanged.connect(self.GraphWidget.show_forbid)

    def _initGuideDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("标尺排图向导")
        dock.visibilityChanged.connect(lambda: self._dock_visibility_changed("标尺排图向导", dock))
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.close()
        self.guideDockWidget = dock

    def _initGuideWidget(self):
        widget = rulerPainter(self.GraphWidget)
        widget.trainOK.connect(self.currentWidget.setData)
        self.guideDockWidget.setWidget(widget)

    def _initSysDock(self):
        colorDock = QtWidgets.QDockWidget()
        self.sysDockWidget = colorDock
        colorDock.setWindowTitle("系统默认设置")
        colorDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("系统默认设置", colorDock))

        self.addDockWidget(Qt.LeftDockWidgetArea, colorDock)
        colorDock.setVisible(False)

    def _initSysWidget(self):
        sysWidget = ConfigWidget(self.graph,True,self)
        self.sysWidget = sysWidget
        self.sysDockWidget.setWidget(sysWidget)

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
        widget = CurrentWidget(self)
        self.currentWidget = widget

        scroll.setWidget(widget)

        self.currentDockWidget.setWidget(scroll)
        self.currentDockWidget.visibilityChanged.connect(
            lambda: self.currentWidget.setData(self.GraphWidget.selectedTrain))

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
        tableWidget.setHorizontalHeaderLabels(['区间', '时分', '起', '停', '实际', '均速', '附加', '差时'])

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
            dt_str = "%02d:%02d" % (int(dt / 60), dt % 60)
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

            if tudy != uiji:
                try:
                    rate = (uiji - tudy) / tudy
                except ZeroDivisionError:
                    rate = 1

                ds = uiji - tudy
                ds_str = "%01d:%02d" % (int(ds / 60), ds % 60)
                if ds_str[0] != '-' and ds < 0:
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
        thread = ThreadDialog(self, self.GraphWidget)
        dialog = QtWidgets.QProgressDialog(self)
        dialog.setRange(0, 100)
        dialog.setWindowTitle('正在处理')
        dialog.setValue(1)

        thread.eventsOK.connect(lambda events: self._train_event_out_ok(events, dialog))
        thread.start()
        # print('start ok')
        i = 1
        while i <= 99:
            if i <= 90:
                time.sleep(0.05)
            else:
                time.sleep(1)
            dialog.setValue(i)
            i += 1
            QtCore.QCoreApplication.processEvents()
            if dialog.wasCanceled():
                thread.terminate()
                return
        return

        # events = self.GraphWidget.listTrainEvent()

    def _train_event_out_ok(self, events: list, dialog):
        print('list ok')
        dialog.setValue(100)
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
                add = event.get("note",'')
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
        typeWidget = TypeWidget(self.graph,self)
        self.typeWidget = typeWidget
        typeWidget.TypeShowChanged.connect(self._apply_type_show)

        self.typeDockWidget.setWidget(typeWidget)

    def _apply_type_show(self):
        """
        由typeWidget的确定触发，修改运行图铺画。已知其他不变，只需要增减部分运行线，避免重新铺画。
        调用前已经修改过数据中的isShow。
        """
        self.trainWidget.updateShow()
        for train in self.graph.trains():
            self.GraphWidget.setTrainShow(train)

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
        rulerWidget.setData()

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
        trainWidget.initWidget()
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
        self.GraphWidget.setTrainShow(train,True)
        for item in train.items():
            self.GraphWidget._line_selected(item)
            break
        dock: QtWidgets.QDockWidget = self.currentDockWidget
        dock.setVisible(True)

    def _search_train(self, checi: str):
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
        self.currentWidget.setData()
        self.currentDockWidget.setVisible(True)
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
        configWidget = ConfigWidget(self.graph,False,self)
        self.configWidget = configWidget
        configWidget.RepaintGraph.connect(self._apply_config_repaint)

        self.configDockWidget.setWidget(configWidget)

    def _apply_config_repaint(self):
        """
        由configWidget的repaint信号触发，进行铺画运行图操作。
        """
        try:
            self.GraphWidget.paintGraph(True)
        except:
            self._derr("铺画失败，可能由于排图标尺不符合要求。已自动恢复为按里程排图。")
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
        except:
            self._derr("设置排图标尺失败！设为排图纵坐标的标尺必须填满每个区间数据。自动变更为按里程排图。")
            self.graph.setOrdinateRuler(former)
            self.GraphWidget.paintGraph()
            return False

        self.configWidget.setOrdinateCombo()
        return True

    def _initMenuBar(self):
        menubar: QtWidgets.QMenuBar = self.menuBar()
        # 文件
        m1: QtWidgets.QMenu = menubar.addMenu("文件(&F)")
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

        actionToTrc = QtWidgets.QAction("导出为ETRC运行图（.trc）格式",self)
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

        actionPaint = QtWidgets.QAction("立即铺画运行图",self)
        actionPaint.setShortcut('shift+F5')
        actionPaint.triggered.connect(lambda :self.GraphWidget.paintGraph(force=True))
        m1.addAction(actionPaint)

        actionOutput = QtWidgets.QAction(QtGui.QIcon(), "导出运行图", self)
        actionOutput.setShortcut("ctrl+T")
        actionOutput.triggered.connect(self._outputGraph)
        m1.addAction(actionOutput)
        # self.actionOutput=actionOutput

        actionOutPdf = QtWidgets.QAction(QtGui.QIcon(),"导出矢量pdf运行图",self)
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
        menu: QtWidgets.QMenu = menubar.addMenu("工具(&T)")
        action = QtWidgets.QAction("标尺排图向导", self)
        action.setShortcut('ctrl+R')
        action.triggered.connect(self._add_train_by_ruler)
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

        action = QtWidgets.QAction("自动适配始发终到站",self)
        action.triggered.connect(self._auto_start_end)
        # action.setShortcut('ctrl+M')
        menu.addAction(action)

        action = QtWidgets.QAction("运行图拼接", self)
        action.triggered.connect(self._joint_graph)
        action.setShortcut('ctrl+J')
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
        actionResetType = QtWidgets.QAction('重置所有列车营业站',self)
        actionResetType.triggered.connect(self._reset_business)
        menu.addAction(actionResetType)

        actionResetPassenger = QtWidgets.QAction("自动设置是否客车",self)
        actionResetPassenger.triggered.connect(self._reset_passenger)
        menu.addAction(actionResetPassenger)

        actionAutoType = QtWidgets.QAction('重置所有列车类型',self)
        actionAutoType.triggered.connect(self._auto_type)
        menu.addAction(actionAutoType)

        # 查看
        menu = menubar.addMenu("查看(&I)")

        action = QtWidgets.QAction("运行图信息", self)
        action.setShortcut('ctrl+P')
        action.triggered.connect(self._line_info_out)
        menu.addAction(action)

        action = QtWidgets.QAction("当前车次信息", self)
        action.setShortcut('ctrl+Q')
        action.triggered.connect(self._train_info)
        menu.addAction(action)

        action = QtWidgets.QAction("当前车次标尺对照", self)
        action.setShortcut('ctrl+W')
        action.triggered.connect(self._check_ruler_from_menu)
        menu.addAction(action)

        action = QtWidgets.QAction("两车次时分对照",self)
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

        # 调整
        menu = menubar.addMenu("调整(&A)")

        action = QtWidgets.QAction("调整当前车次时刻", self)
        action.setShortcut('ctrl+A')
        action.triggered.connect(self._adjust_train_time)
        menu.addAction(action)

        action = QtWidgets.QAction("批量复制当前运行线", self)
        action.setShortcut('ctrl+shift+A')
        action.triggered.connect(self._batch_copy_train)
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

        action = QtWidgets.QAction('高级显示车次设置', self)
        action.setShortcut('ctrl+shift+L')
        action.triggered.connect(self.showFilter.setFilter)
        menu.addAction(action)

        action = QtWidgets.QAction('当前车次时刻表重排',self)
        action.setShortcut('ctrl+V')
        action.triggered.connect(self._correction_timetable)
        menu.addAction(action)

        # 数据
        menu = menubar.addMenu("数据(&S)")

        action = QtWidgets.QAction("线路数据库维护", self)
        action.setShortcut('ctrl+H')
        action.triggered.connect(self._view_line_data)
        menu.addAction(action)

        action = QtWidgets.QAction("导入线路数据", self)
        action.setShortcut('ctrl+K')
        action.triggered.connect(self._import_line)
        menu.addAction(action)

        action = QtWidgets.QAction("导入线路数据(Excel)", self)
        action.setShortcut('ctrl+shift+K')
        action.triggered.connect(self._import_line_excel)
        menu.addAction(action)

        action = QtWidgets.QAction("导入车次", self)
        action.setShortcut('ctrl+D')
        action.triggered.connect(self._import_train)
        menu.addAction(action)

        action = QtWidgets.QAction("导入实际运行线", self)
        action.setShortcut('ctrl+shift+D')
        action.triggered.connect(self._import_train_real)
        menu.addAction(action)

        # 窗口
        menu: QtWidgets.QMenu = menubar.addMenu("窗口(&W)")
        self.actionWindow_list = []
        actions = (
            '线路编辑', '车次编辑', '标尺编辑', '选中车次设置', '运行图设置', '系统默认设置',
            '显示类型设置', '天窗编辑'
        )
        shorcuts = (
            'X', 'C', 'B', 'I', 'G', 'shift+G', 'L', '1'
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
        menu = menubar.addMenu("帮助(&H)")

        action = QtWidgets.QAction("关于", self)
        action.triggered.connect(self._about)
        menu.addAction(action)

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
            '系统默认设置':self.sysDockWidget,
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

    def _initToolBar(self):
        pass
        # toolBar=QtWidgets.QToolBar()
        # actionZoonIn = QtWidgets.QAction('放大视图',self)
        # toolBar.addAction(actionZoonIn)
        # actionZoonIn.setShortcut('ctrl+=')
        # actionZoomOut = QtWidgets.QAction('缩小视图',self)
        # toolBar.addAction(actionZoomOut)
        # actionZoomOut.setShortcut('ctrl+-')
        # actionZoonIn.triggered.connect(lambda:self.GraphWidget.scale(1.25,1.25))
        # actionZoomOut.triggered.connect(lambda:self.GraphWidget.scale(0.8,0.8))
        # self.addToolBar(Qt.TopToolBarArea,toolBar)

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

        self.graph = Graph()
        self.GraphWidget.graph = self.graph
        self.GraphWidget.paintGraph()
        self._initDockWidgetContents()
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

        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC运行图文件(*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')[0]
        if not filename:
            return

        self.GraphWidget._line_un_selected()
        self.graph = Graph()
        self.showFilter.setGraph(self.graph)
        try:
            self.graph.loadGraph(filename)
            if 'DB' in self.graph.version():
                if not self.qustion('此文件可能被标记为数据库文件。如果没有特殊目的，'
                                    'pyETRC不建议您直接打开数据库文件（尽管这是可以的），'
                                    '而是使用ctrl+D向既有线路中导入车次。是否继续打开此文件？'):
                    return
            elif self.graph.version() > self.version:
                if not self.qustion(f'此文件可能由高于当前软件版本的pyETRC保存。如果继续打开并保存此文件，'
                                    f'可能损失一些新版本的信息。是否确认打开此文件？'
                                    f'当前软件版本：{self.version}；文件标记版本：{self.graph.version}'):
                    return
            self.GraphWidget.setGraph(self.graph)
            self._system["last_file"] = filename
            # print("last file changed")
        except:
            self._derr("文件错误！请检查")
            traceback.print_exc()
        else:
            self._initDockWidgetContents()
            self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")

    def _outputGraph(self):
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
                                                             caption='导出运行图',
                                                             directory=self.graph.lineName(),
                                                             filter="图像(*.png)")
        if not filename or not ok:
            return
        self.GraphWidget.save(filename,f"由{self.name}{self.version}导出")
        self._dout("导出成功！")

    def _outputPdf(self):
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
                                                             caption='导出pdf运行图',
                                                             directory=self.graph.lineName(),
                                                             filter="PDF图像(*.pdf)")
        if not filename or not ok:
            return
        if self.GraphWidget.savePdf(filename,f"由{self.name}{self.version}导出"):
            self._dout("导出PDF成功！")

    def _outExcel(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, caption='导出运行图', filter="Excel文件(*.xlsx)")[0]
        if not filename:
            return
        self.graph.save_excel(filename)
        self._dout("导出完毕")

    def _saveGraph(self):
        filename = self.graph.graphFileName()
        status: QtWidgets.QStatusBar = self.statusBar()
        status.showMessage("正在保存")
        if not self.graph.graphFileName():
            filename = QtWidgets.QFileDialog.getSaveFileName(self, "选择文件", directory=self.graph.lineName() + '.json',
                                                             filter='pyETRC运行图文件(*.json)\n所有文件(*.*)')[0]
        self.graph.setVersion(self.version)
        self.graph.save(filename)
        self.graph.setGraphFileName(filename)
        status.showMessage("保存成功")
        self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")

    def _saveGraphAs(self):
        """
        另存为
        """
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "选择文件", directory=self.graph.lineName() + '.json',
                                                         filter='pyETRC运行图文件(*.json)\n所有文件(*.*)')[0]
        self.statusBar().showMessage("正在保存")
        self.graph.setVersion(self.version)
        self.graph.save(filename)
        self.graph.setGraphFileName(filename)
        self.statusBar().showMessage("保存成功")
        self._system["last_file"] = filename
        self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")

    def _toTrc(self):
        """
        先显示提示信息，然后导出为trc。
        """
        text = "注意：显著的信息丢失。由于文本运行图格式不支持本系统的部分功能，导出的.trc格式运行图包含的信息少于本系统的.json格式运行图。这就是说，若先导出.trc格式，再用本系统读取该文件，仍将造成显著的信息丢失。本功能不改变原运行图，只是导出一个副本。请确认知悉以上内容，并继续。"
        self._dout(text)
        filename,ok = QtWidgets.QFileDialog.getSaveFileName(self, "选择文件", directory=self.graph.lineName() + '.trc',
                                                         filter='ETRC运行图文件(*.trc)\n所有文件(*.*)')
        if not ok:
            return
        self.graph.toTrc(filename)

    def _reset_graph(self):
        flag = self.qustion("重新从文件中读取本运行图，所有未保存数据都将丢失，未保存过的运行图将重置为空运行图！"
                            "是否继续？")
        if not flag:
            return

        filename = self.graph.filename
        if not filename:
            self.graph = Graph()
            self.GraphWidget.graph = Graph()
        else:
            try:
                self.graph.loadGraph(filename)
            except:
                self._derr("文件错误！请检查。")
        self.GraphWidget.scene.clear()
        self.GraphWidget.paintGraph()
        self._initDockWidgetContents()

    def _refresh_graph(self):
        self.statusOut("正在刷新数据")
        self.graph.refreshData()
        self.GraphWidget.paintGraph(force=True)
        self._refreshDockWidgets()
        self.statusOut('就绪')

    def _about(self):
        text = f"{self.title}  {self.build}\n六方车迷会谈 马兴越  保留一切权利\n"
        text += "联系方式： 邮箱 mxy0268@outlook.com"
        text += '\n本系统官方交流群：865211882'
        QtWidgets.QMessageBox.about(self, '关于', text)

    def statusOut(self, note: str, seconds: int = 0):
        try:
            self.statusBar().showMessage(note, seconds)
        except:
            traceback.print_exc()

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

        # print("current train changed. line 1708", row,train.fullCheci())

        # 取消不响应非显示列车的逻辑。2018年11月20日
        """
        if not train.isShow():
            return
            """

        # 这是为了避免间接递归。若不加检查，这里取消后再次引发改变，则item选中两次。
        if self.GraphWidget.selectedTrain is not train:
            self.GraphWidget._line_un_selected()
        self.GraphWidget._line_selected(train.firstItem(), True)  # 函数会检查是否重复选择
        if self.currentWidget.isVisible():
            self.currentWidget.setData(train)

    def _add_train_by_ruler(self):
        """
        标尺排图向导
        """
        if not self.graph.rulerCount():
            self._derr("标尺排图向导：无可用标尺！")
            return

        painter = rulerPainter(self.GraphWidget)
        self.rulerPainter = painter
        painter.trainOK.connect(self.currentWidget.setData)
        painter.trainOK.connect(self.trainWidget.addTrain)
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("标尺排图向导")
        dock.setWidget(painter)
        dock.setFeatures(dock.DockWidgetMovable | dock.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.NoDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)
        dock.resize(600, 800)

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

        dialog.setLayout(layout)
        dialog.exec_()

    def _station_timetable_ok(self, listWidget: QtWidgets.QListWidget):
        self.sender().parentWidget().close()
        try:
            station_name = listWidget.selectedItems()[0].text()
        except:
            self._derr("请先选择车站！")
            return
        timetable_dicts = self.graph.stationTimeTable(station_name)

        dialog = QtWidgets.QDialog(self)
        dialog.resize(600, 600)
        dialog.setWindowTitle(f"车站时刻表*{station_name}")
        layout = QtWidgets.QVBoxLayout()

        checkStopOnly = QtWidgets.QCheckBox('不显示通过列车')
        layout.addWidget(checkStopOnly)
        checkStopOnly.toggled.connect(lambda x: self._station_timetable_stop_only_changed(timetable_dicts,
                                                                                          tableWidget, station_name, x))

        label = QtWidgets.QLabel(f"*{station_name}*在本线时刻表如下：")
        layout.addWidget(label)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(10)
        tableWidget.setHorizontalHeaderLabels(['车次', '站名', '到点', '开点',
                                               '类型', '停站', '方向', '始发', '终到','备注'])
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        column_width = (80, 100, 100, 100, 80, 80, 80, 90, 90,90)
        for i, s in enumerate(column_width):
            tableWidget.setColumnWidth(i, s)

        self._setStationTimetable(timetable_dicts, tableWidget, station_name, False)

        layout.addWidget(tableWidget)
        hlayout = QtWidgets.QHBoxLayout()
        btnOut = QtWidgets.QPushButton("导出")
        btnVisual = QtWidgets.QPushButton("可视化")
        btnClose = QtWidgets.QPushButton("关闭")
        btnClose.clicked.connect(dialog.close)
        btnOut.clicked.connect(lambda: self._station_timetable_out(tableWidget))
        btnVisual.clicked.connect(lambda: self._station_visualize(timetable_dicts, station_name))
        hlayout.addWidget(btnOut)
        hlayout.addWidget(btnVisual)
        hlayout.addWidget(btnClose)
        layout.addLayout(hlayout)

        dialog.setLayout(layout)
        dialog.exec_()

    def _setStationTimetable(self, timetable_dicts, tableWidget, station_name, stop_only):
        tableWidget.setRowCount(0)
        row = -1
        for _, node in enumerate(timetable_dicts):
            train = node["train"]
            stop_text = train.stationStopBehaviour(station_name)
            if stop_only and stop_text in ('通过', '不通过'):
                # print(train.fullCheci(),stop_text)
                continue

            row += 1
            tableWidget.insertRow(row)
            tableWidget.setRowHeight(row, self.graph.UIConfigData()['table_row_height'])

            item = QtWidgets.QTableWidgetItem(train.fullCheci())
            tableWidget.setItem(row, 0, item)

            item = QtWidgets.QTableWidgetItem(node["station_name"])
            tableWidget.setItem(row, 1, item)

            item = QtWidgets.QTableWidgetItem(node["ddsj"].strftime('%H:%M:%S'))
            tableWidget.setItem(row, 2, item)

            item = QtWidgets.QTableWidgetItem(node["cfsj"].strftime('%H:%M:%S'))
            tableWidget.setItem(row, 3, item)

            item = QtWidgets.QTableWidgetItem(train.trainType())
            tableWidget.setItem(row, 4, item)

            tableWidget.setItem(row, 5, QtWidgets.QTableWidgetItem(stop_text))

            down = train.stationDown(station_name,self.graph)
            text = '下行' if  down is True else ('上行' if down is False else '未知')
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 6, item)

            text = train.sfz
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 7, item)

            text = train.zdz
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 8, item)

            text = node['note']
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 9, item)


    def _station_timetable_stop_only_changed(self, timetable_dicts, tableWidget, station_name,
                                             stopOnly: bool):
        self._setStationTimetable(timetable_dicts, tableWidget, station_name, stopOnly)

    def _station_visualize(self, station_dicts: list, station_name):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"车站停车示意图*{station_name}")
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("说明：此功能将各个车次在本线到开时间可视化，绘出股道占用时间图。"
                                 "本图只是提供一种可能的情况，并不代表实际情况，如有雷同，纯属巧合；"
                                 "本图默认采用双线股道铺排模式，Ⅰ、Ⅱ为上下行正线，其他为侧线；"
                                 "所有下行车安排在下行股道；且通过车优先安排在正线，停车列车只安排在侧线。")
        label.setWordWrap(True)
        layout.addWidget(label)

        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setRange(1, 120)
        # slider.valueChanged.connect(lambda x:print(x))
        slider.setMaximumWidth(800)
        slider.setValue(20)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(QtWidgets.QLabel("水平缩放"))
        hlayout.addStretch(10)
        hlayout.addWidget(QtWidgets.QLabel("大"))
        hlayout.addStretch(2)
        hlayout.addWidget(slider)
        hlayout.addStretch(2)
        hlayout.addWidget(QtWidgets.QLabel("小"))
        hlayout.addStretch(20)
        btnAdvance = QtWidgets.QPushButton("高级")
        hlayout.addWidget(btnAdvance)

        slider.valueChanged.connect(lambda x: self.stationVisualSizeChanged.emit(x))
        layout.addLayout(hlayout)

        widget = StationGraphWidget(station_dicts, self.graph,station_name, self)
        btnAdvance.clicked.connect(lambda: self._station_visualize_advance(widget))
        layout.addWidget(widget)
        dialog.setLayout(layout)
        dialog.exec_()

    def _station_visualize_advance(self, visualWidget: StationGraphWidget):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('高级')
        flayout = QtWidgets.QFormLayout()

        group = QtWidgets.QButtonGroup()
        radioDouble = QtWidgets.QRadioButton("双线铺画")
        dialog.radioDouble = radioDouble
        radioSingle = QtWidgets.QRadioButton("单线铺画")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(radioDouble)
        group.addButton(radioDouble)
        hlayout.addWidget(radioSingle)
        group.addButton(radioSingle)
        flayout.addRow("铺画模式", hlayout)
        if visualWidget.doubleLine():
            radioDouble.setChecked(True)
        else:
            radioSingle.setChecked(True)
        radioDouble.toggled.connect(visualWidget.setDoubleLine)

        group = QtWidgets.QButtonGroup()
        hlayout = QtWidgets.QHBoxLayout()
        radioMainStay = QtWidgets.QRadioButton("允许")
        radioMainStayNo = QtWidgets.QRadioButton("不允许")
        hlayout.addWidget(radioMainStay)
        hlayout.addWidget(radioMainStayNo)
        dialog.radioMainStay = radioMainStay
        group.addButton(radioMainStay)
        group.addButton(radioMainStayNo)
        flayout.addRow("正线停车", hlayout)
        if visualWidget.allowMainStay():
            radioMainStay.setChecked(True)
        else:
            radioMainStayNo.setChecked(True)
        radioMainStay.toggled.connect(visualWidget.setAllowMainStay)

        spinSame = QtWidgets.QSpinBox()
        spinSame.setValue(visualWidget.sameSplitTime())
        spinSame.setRange(0, 999)
        spinSame.valueChanged.connect(visualWidget.setSameSplitTime)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinSame)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        flayout.addRow("同向接车间隔", hlayout)

        spinOpposite = QtWidgets.QSpinBox()
        spinOpposite.setValue(visualWidget.oppositeSplitTime())
        spinOpposite.setRange(0, 999)
        spinOpposite.valueChanged.connect(visualWidget.setOppositeSplitTime)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinOpposite)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        flayout.addRow("对向接车间隔", hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        flayout.addRow(hlayout)

        btnOk.clicked.connect(visualWidget.rePaintGraphAdvanced)
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(dialog.close)

        dialog.setLayout(flayout)
        dialog.exec_()

    def _station_timetable_out(self, tableWidget: QtWidgets.QTableWidget):
        self.statusOut("正在准备导出……")
        try:
            import xlwt
        except ImportError:
            self._derr("错误：此功能需要'xlwt'库支持。")
            self.statusOut("就绪")
            return

        filename = QtWidgets.QFileDialog.getSaveFileName(self, '选择文件', filter='*.xls')[0]
        if not filename:
            return

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('车站时刻表')

        for i, s in enumerate(['车次', '站名', '到点', '开点', '类型', '停站', '方向', '始发', '终到']):
            ws.write(0, i, s)

        for row in range(tableWidget.rowCount()):
            for col in range(9):
                ws.write(row + 1, col, tableWidget.item(row, col).text())
        wb.save(filename)
        self._dout("时刻表导出成功！")
        self.statusOut("就绪")

    def _interval_count(self):
        """
        计算区间停站车次数量
        """
        dialog = IntervaLCountDialog(self.graph,self)
        dialog.exec_()

    def _reverse_graph(self):
        flag = self.qustion("将本线上下行交换，所有里程交换。是否继续？\n"
                            "此功能容易导致上下行逻辑混乱，除非当前运行图上下行错误，否则不建议使用此功能。")
        if not flag:
            return
        self.graph.reverse()
        self.GraphWidget.paintGraph()
        self._initDockWidgetContents()

    def _line_info_out(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("线路信息")
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
        btnClose.setMaximumWidth(100)
        btnClose.clicked.connect(dialog.close)
        layout.addWidget(btnClose)
        layout.setAlignment(Qt.AlignCenter)

        dialog.setLayout(layout)
        dialog.exec_()

    def _interval_trains(self):
        """
        给出区间车次表，类似12306查询车票
        """
        dialog = IntervalTrainDialog(self.graph,self)
        dialog.exec_()

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
        for name,dock in self.action_widget_dict.items():
            self._system.setdefault("dock_show",{})[name]=dock.isVisible()
        self._saveSystemSetting()

    def _train_info(self):
        train: Train = self.GraphWidget.selectedTrain
        if train is None:
            self._derr("当前车次为空！")
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("车次信息")
        dialog.resize(400,400)
        layout = QtWidgets.QVBoxLayout()
        text = ""

        text += f"车次：{train.fullCheci()}\n"
        text += f"分方向车次：{train.downCheci()}/{train.upCheci()}\n"
        text += f"始发终到：{train.sfz}->{train.zdz}\n"
        text += f"列车种类：{train.trainType()}\n"
        text += f"本线运行入图方向：{train.firstDownStr()}\n"
        text += f"本线运行出图方向：{train.lastDownStr()}\n"
        text += f"本线入图点：{train.localFirst(self.graph)}\n"
        text += f"本线出图点：{train.localLast(self.graph)}\n"
        text += f"本线图定站点数：{train.localCount(self.graph)}\n"
        text += f"本线运行里程：{train.localMile(self.graph)}\n"
        running, stay = train.localRunStayTime(self.graph)
        time = running + stay
        text += f"本线运行时间：{'%d:%02d:%02d'%(int(time/3600),int((time%3600)/60),int(time%60))}\n"
        try:
            speed = 1000 * train.localMile(self.graph) / time * 3.6
            speed_str = "%.2fkm/h" % (speed)
        except ZeroDivisionError:
            speed_str = 'NA'
        text += f"本线旅行速度：{speed_str}\n"
        text += f"本线纯运行时间：{'%d:%02d:%02d'%(int(running/3600),int((running%3600)/60),int(running%60))}\n"
        text += f"本线总停站时间：{'%d:%02d:%02d'%(int(stay/3600),int((stay%3600)/60),int(stay%60))}\n"
        try:
            running_speed = 1000 * train.localMile(self.graph) / running * 3.6
            running_speed_str = "%.2f" % running_speed
        except ZeroDivisionError:
            running_speed_str = 'NA'
        text += f"本线技术速度：{running_speed_str}km/h\n"

        textBrowser = QtWidgets.QTextBrowser()
        textBrowser.setText(text)

        layout.addWidget(textBrowser)

        btnClose = QtWidgets.QPushButton("关闭")
        btnClose.clicked.connect(dialog.close)
        layout.addWidget(btnClose)

        dialog.setLayout(layout)
        dialog.exec_()

    def _check_ruler_from_menu(self):
        train = self.GraphWidget.selectedTrain
        if train is None:
            self._derr("当前没有选中车次！")
            return
        self._check_ruler(train)

    def _train_compare(self):
        """
        两车次运行对照
        """
        dialog = TrainComparator(self.graph,self)
        dialog.exec_()

    def _get_interval_info(self):
        """
        计算当前车次在选定区间内的主要性质，参见ctrl+Q面板。sample:
        :return:
        """
        train = self.GraphWidget.selectedTrain
        if train is None:
            self._derr("当前没有选中车次！")
            return
        dialog = IntervalWidget(self.graph, self)
        dialog.setTrain(train)
        dialog.exec_()

    def _reset_start_end(self):
        flag = self.qustion("将本线所有列车始发站设置时刻表首站、终到站设置为时刻表末站，是否继续？")
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
        if not self.qustion(text):
            return
        for train in self.graph.trains():
            train.autoStartEnd()
        self.trainWidget.updateAllTrains()
        self._dout('自动设置完成！可手动重新铺画运行图（shift+F5）以查看效果。')

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
        :param dialog:
        :return:
        """
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC运行图文件(*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')[0]
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
        self._initDockWidgetContents()
        self.statusOut("就绪")
        dialog.close()

    def _reset_business(self):
        if not self.qustion('此操作将重置所有列车营业站信息，手动手动设置的营业站信息将丢失。是否继续？'):
            return
        if not self.qustion('再次确认，您是否确实要重置所有列车营业站信息？此操作不可撤销。'):
            return
        for train in self.graph.trains():
            train.autoBusiness()
        self.statusOut('重置营业站信息完毕')

    def _reset_passenger(self):
        if not self.qustion('按系统设置中的“类型管理”信息设置所有列车的“是否旅客列车”字段为'
                            '“是”或者“否”。此操作有助于提高效率，但今后修改类型管理信息时，'
                            '车次的数据不会随之更新。是否继续？'):
            return
        for train in self.graph.trains():
            if train.isPassenger() == train.PassengerAuto:
                train.setIsPassenger(train.isPassenger(detect=True))
        self.statusOut('自动设置旅客列车信息完毕')

    def _auto_type(self):
        if not self.qustion('按照所有列车的车次（全车次），根据本系统规定的正则判据，重置所有列车的类型。'
                            '是否继续？'):
            return
        for train in self.graph.trains():
            train.autoTrainType()

    def _view_line_data(self):
        lineDB = LineDB()
        lineDB.resize(1100, 700)
        lineDB.exec_()

    def _adjust_train_time(self):
        """
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('调整当前车次时刻')
        train = self.GraphWidget.selectedTrain
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
        label = QtWidgets.QLabel(':')
        label.setFixedWidth(10)
        hlayout.addWidget(spinMin)
        hlayout.addWidget(label)
        hlayout.addWidget(spinSec)
        flayout.addRow("调整时间", hlayout)

        dialog.spinMin = spinMin
        spinMin.setMaximumWidth(100)
        dialog.spinSec = spinSec
        spinSec.setMaximumWidth(80)

        layout.addLayout(flayout)

        listWidget = QtWidgets.QListWidget()
        for name, ddsj, cfsj in train.station_infos():
            ddsj_str = ddsj.strftime('%H:%M:%S')
            cfsj_str = cfsj.strftime('%H:%M:%S')
            if (cfsj - ddsj).seconds == 0:
                cfsj_str = '...'

            item = QtWidgets.QListWidgetItem(f"{name}\t{ddsj_str}/{cfsj_str}")
            item.setData(-1, name)
            listWidget.addItem(item)
        listWidget.setSelectionMode(listWidget.MultiSelection)
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
        train: Train = self.GraphWidget.selectedTrain
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

        self.GraphWidget.delTrainLine(train)
        self.GraphWidget.addTrainLine(train)
        dialog.close()

    def _import_line(self):
        try:
            self.statusOut("正在读取数据库文件……")
            fp = open('lines.json', encoding='utf-8', errors='ignore')
            line_dicts = json.load(fp)
        except:
            self._derr("线路数据库文件错误！请检查lines.json文件。")
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
        listWidget.itemDoubleClicked.connect(lambda:self._import_line_ok(dialog))
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
            name,mile = st["zhanming"],st["licheng"]
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


    def _import_line_stations(self,line:Line,dialogLines,dialogStations,all:bool=False):
        """
        选择导入的站点后确定。
        """
        newLine = Line(line.name)
        if all:
            newLine.copyData(line,withRuler=True)
        else:
            listWidget:QtWidgets.QListWidget = dialogStations.listWidget
            for idx in listWidget.selectedIndexes():
                row = idx.row()
                newLine.addStationDict(line.stationDictByIndex(row))
            newLine.rulers = line.rulers

        self.graph.setLine(newLine)
        self.graph.resetAllItems()
        self.graph.setOrdinateRuler(None)
        self.GraphWidget.paintGraph()
        self._initDockWidgetContents()
        self.statusOut("导入线路数据成功")
        dialogStations.close()
        dialogLines.close()

    def _import_line_excel(self):
        flag = self.qustion("从Excel表格中导入线路数据，抛弃当前线路数据，是否继续？"
                            "Excel表格应包含三列，分别是站名、里程、等级，不需要表头。")
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
            except:
                pass
            else:
                new_line.addStation_by_info(name, mile, level)
        self.graph.setLine(new_line)
        self.GraphWidget.paintGraph(throw_error=False)
        self._initDockWidgetContents()
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
        self.rulerWidget.setData()

        self.statusOut("站名变更成功")

    def _out_domain_info(self):
        """
        检测到域解析符时，输出提示
        """
        self._dout("您使用了域解析符(::)。本程序中域解析符用于分隔站名与场名，在没有完全匹配时生效。"
                   "例如，“成都东::达成场”可以匹配到“成都东”。\n"
                   "请确认您知悉以上内容并继续。\n本提示不影响确认动作的执行。")

    def _import_train(self):
        flag = self.qustion("选择运行图，导入其中所有在本线的车次。您是否希望覆盖重复的车次？"
                            "选择“是”以覆盖重复车次，“否”以忽略重复车次。")

        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC运行图文件(*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')[0]
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
            num = self.graph.addTrainByGraph(graph,flag)
            self.GraphWidget.paintGraph()
            self.trainWidget.addTrainsFromBottom(num)
            self._dout(f"成功导入{num}个车次。")

    def _import_train_real(self):
        flag = self.qustion("选择运行图，导入其中所有在本线的车次，车次前冠以“R”，类型为“实际”。是否继续？")
        if not flag:
            return

        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC运行图文件(*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')[0]
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
            self._initDockWidgetContents()

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
            if not self.qustion('此操作将删除要推定时刻列车时刻表中【非本线】的站点，是否继续？'):
                return
        dialog = DetectWidget(self, self)
        # dialog.okClicked.connect(self.GraphWidget.paintGraph)
        dialog.exec_()

    def _correction_timetable(self,train=None):
        if not isinstance(train,Train):
            train = self.GraphWidget.selectedTrain
        if train is None:
            self._derr('当前车次时刻表重排：当前没有选中车次！')
            return
        dialog = CorrectionWidget(train,self.graph,self)
        dialog.correctionOK.connect(self._correction_ok)
        dialog.exec_()

    def _correction_ok(self,train):
        self.currentWidget.setData(train)
        self.GraphWidget.delTrainLine(train)
        self.GraphWidget.addTrainLine(train)

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
        :return:
        """
        if self.GraphWidget.selectedTrain is None:
            self._derr("批量复制当前运行线：当前没有选中车次！")
            return

        train: Train = self.GraphWidget.selectedTrain

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f'批量复制运行线*{train.fullCheci()}')
        vlayout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel("批量复制当前车次运行线，请设置需要复制的车次的始发时间和车次。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        flayout = QtWidgets.QFormLayout()
        lineEdit = QtWidgets.QLineEdit()
        lineEdit.setEnabled(False)
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
        train: Train = self.GraphWidget.selectedTrain
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
        self.trainWidget.addTrainsFromBottom(cnt)

        text = f"成功复制{cnt}个车次。"
        if failed:
            text += '\n以下信息车次未能成功复制。可能由于车次已经存在，或者车次为空：'
            for checi, s_t in failed:
                text += f'\n{checi if checi else "空"},{s_t.strftime("%H:%M:%S")}'
        self._dout(text)

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def qustion(self, note: str, default=True):
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
    mainWindow = mainGraphWindow()
    mainWindow.show()
    sys.exit(app.exec_())

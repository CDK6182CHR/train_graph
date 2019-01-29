"""
拟使用的正式mainwindow.不用Designer.
copyright (c) mxy 2018
"""
import sys
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt
from graph import Graph
from ruler import Ruler
from line import Line
from train import Train
from datetime import datetime, timedelta
from forbidWidget import ForbidWidget
from rulerWidget import RulerWidget
from currentWidget import CurrentWidget
from lineWidget import LineWidget
from trainWidget import TrainWidget
from trainFilter import TrainFilter
import json
from GraphicWidget import GraphicsWidget, TrainEventType,config_file
from rulerPaint import rulerPainter
from stationvisualize import StationGraphWidget
from lineDB import LineDB
from intervalWidget import IntervalWidget
from detectWidget import DetectWidget
import traceback
import cgitb
cgitb.enable(format='text')


class mainGraphWindow(QtWidgets.QMainWindow):
    stationVisualSizeChanged = QtCore.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.title = "运行图系统V1.3.2"  # 一次commit修改一次版本号
        self.build = '20190129'
        self.setWindowTitle(f"{self.title}   正在加载")
        self.setWindowIcon(QtGui.QIcon('icon.ico'))
        self.showMaximized()
        self.show()
        try:
            fp = open(config_file,encoding='utf-8',errors='ignore')
            json.load(fp)
        except:
            self._derr(f"配置文件{config_file}错误，请检查！")
            sys.exit(1)
        else:
            fp.close()

        self.GraphWidget = GraphicsWidget(self)

        self.graph = self.GraphWidget.graph
        self.setWindowTitle(f"{self.title}   {self.graph.filename if self.graph.filename else '新运行图'}")

        self.showFilter = TrainFilter(self.graph, self)
        self.showFilter.FilterChanged.connect(self._train_show_filter_ok)

        self.GraphWidget.showNewStatus.connect(self.statusOut)
        self.GraphWidget.focusChanged.connect(self.on_focus_changed)

        self.lineDockWidget = None
        self.configDockWidget = None
        self.currentDockWidget = None  # 当前选中车次信息
        self.colorDockWidget = None
        self.typeDockWidget = None
        self.trainDockWidget = None
        self.rulerDockWidget = None
        self.guideDockWidget = None
        self.forbidDockWidget = None
        self.to_repaint = False

        self.action_widget_dict = {
            '线路编辑': self.lineDockWidget,
            '车次编辑': self.trainDockWidget,
            '选中车次设置': self.currentDockWidget,
            '运行图设置': self.configDockWidget,
            '颜色设置': self.colorDockWidget,
            '显示类型设置': self.typeDockWidget,
            '标尺编辑': self.rulerDockWidget,
            '标尺排图向导': self.guideDockWidget,
            '天窗编辑':self.forbidDockWidget,
        }

        self._initUI()
        self.rulerPainter = None

    def _initUI(self):
        self.statusBar().showMessage("系统正在初始化……")
        self.setCentralWidget(self.GraphWidget)
        self._initMenuBar()

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
        self._initColorDock()
        self._initForbidDock()

    def _initDockWidgetContents(self):
        self._initTrainWidget()
        self._initConfigWidget()
        self._initLineWidget()
        self._initRulerWidget()
        self._initTypeWidget()
        self._initCurrentWidget()
        self._initColorWidget()
        self._initForbidWidget()

    def _initForbidDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("天窗编辑")
        dock.visibilityChanged.connect(lambda: self._dock_visibility_changed("天窗编辑", dock))
        self.addDockWidget(Qt.RightDockWidgetArea,dock)
        dock.setVisible(False)
        self.forbidDockWidget = dock

    def _initForbidWidget(self):
        widget = ForbidWidget(self.graph.line.forbid)
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
        widget.trainOK.connect(lambda x: self._setCurrentWidgetData(x))
        self.guideDockWidget.setWidget(widget)

    def _initColorDock(self):
        colorDock = QtWidgets.QDockWidget()
        self.colorDockWidget = colorDock
        colorDock.setWindowTitle("默认颜色设置")
        colorDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("颜色设置", colorDock))

        self.addDockWidget(Qt.LeftDockWidgetArea, colorDock)
        colorDock.setVisible(False)

    def _initColorWidget(self):
        if self.colorDockWidget is None:
            return

        UIDict = self.graph.UIConfigData()

        widget = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        gridBtn = QtWidgets.QPushButton(UIDict["grid_color"])
        gridColor = QtGui.QColor(UIDict["grid_color"])
        widget.gridColor = gridColor
        widget.gridBtn = gridBtn
        gridBtn.setStyleSheet(f"background-color:rgb({gridColor.red()},{gridColor.green()},{gridColor.blue()})")
        gridBtn.setMaximumWidth(150)
        gridBtn.clicked.connect(lambda: self._choose_color(gridColor, widget))
        flayout.addRow("运行线格颜色", gridBtn)

        textBtn = QtWidgets.QPushButton(UIDict["text_color"])
        textColor = QtGui.QColor(UIDict["text_color"])
        widget.textColor = textColor
        widget.textBtn = textBtn
        textBtn.setStyleSheet(f"background-color:rgb({textColor.red()},{textColor.green()},{textColor.blue()})")
        textBtn.setMaximumWidth(150)
        textBtn.clicked.connect(lambda: self._choose_color(textColor))
        flayout.addRow("文字颜色", textBtn)

        defaultBtn = QtWidgets.QPushButton(UIDict["default_colors"]["default"])
        defaultColor = QtGui.QColor(UIDict["default_colors"]["default"])
        widget.defaultColor = defaultColor
        widget.defaultBtn = defaultBtn
        defaultBtn.setStyleSheet(
            f"background-color:rgb({defaultColor.red()},{defaultColor.green()},{defaultColor.blue()})")
        defaultBtn.setMaximumWidth(150)
        defaultBtn.clicked.connect(lambda: self._choose_color(defaultColor))
        flayout.addRow("默认运行线颜色", defaultBtn)

        layout.addLayout(flayout)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(2)
        tableWidget.setHorizontalHeaderLabels(["类型", "颜色"])
        tableWidget.setRowCount(len(UIDict["default_colors"]) - 1)
        tableWidget.setColumnWidth(0, 80)
        tableWidget.setColumnWidth(1, 120)
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)

        tableWidget.cellClicked.connect(self._choose_color_table)
        widget.tableWidget = tableWidget

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

        btnAdd.clicked.connect(lambda: self._add_color_row(tableWidget))
        btnDel.clicked.connect(lambda: self._del_color_row(tableWidget))
        btnOk.clicked.connect(lambda: self._apply_color(widget))
        btnCancel.clicked.connect(lambda: self._default_color(widget))

        layout.addLayout(hlayout)

        widget.setLayout(layout)

        self.colorDockWidget.setWidget(widget)

    def _add_color_row(self, table: QtWidgets.QTableWidget):
        row = table.rowCount()
        table.insertRow(table.rowCount())
        table.setRowHeight(row, 30)

        item = QtWidgets.QTableWidgetItem('#FFFFFF')
        item.setFlags(Qt.NoItemFlags)
        table.setItem(row, 1, item)

    def _del_color_row(self, table: QtWidgets.QTableWidget):
        table.removeRow(table.currentRow())

    def _apply_color(self, widget: QtWidgets.QWidget):
        UIDict = {}
        UIDict["grid_color"] = widget.gridBtn.text()
        UIDict["text_color"] = widget.textBtn.text()
        UIDict["default_colors"] = {}
        UIDict["default_colors"]["default"] = widget.defaultBtn.text()

        tableWidget: QtWidgets.QTableWidget = widget.tableWidget
        for row in range(tableWidget.rowCount()):
            key = tableWidget.item(row, 0).text()
            value = tableWidget.item(row, 1).text()
            try:
                UIDict["default_colors"][key] = value
            except:
                self._derr(f"类型名称重复：{key}，请重新编辑！")
                return

        flag = self.qustion("是否将数据保存为系统默认？\n选择是（Yes）保存系统默认，选择“否（No）”仅应用到本运行图")

        for key, value in UIDict.items():
            self.graph.UIConfigData()[key] = value

        if flag:
            self.GraphWidget.saveSysConfig(Copy=True)

        self.GraphWidget.paintGraph()

    def _default_color(self, widget: QtWidgets.QWidget):
        flag = self.qustion("将颜色设置恢复为系统默认，当前运行图相关设置的修改将丢失。是否继续？")
        if not flag:
            return

        keys = ("grid_color", "default_colors", "text_color")
        for key in keys:
            self.graph.UIConfigData()[key] = self.GraphWidget.sysConfig[key]

        self._initColorWidget()

    def _choose_color(self, initColor: QtGui.QColor, widget):
        btn: QtWidgets.QPushButton = self.sender()
        color: QtGui.QColor = QtWidgets.QColorDialog.getColor(initColor, title=btn.text())
        btn.setText("#%02X%02X%02X" % (color.red(), color.green(), color.blue()))
        btn.setStyleSheet(f"background-color:rgb({color.red()},{color.green()},{color.blue()})")
        arribute_dict = {
            '运行线格颜色': widget.gridColor,
            '文字颜色': widget.textColor,
            '默认运行线颜色': widget.defaultColor,
        }
        arribute_dict[btn.text()] = color

    def _choose_color_table(self, row):
        """
        slot。colorDock中的表格双机进入。
        :param row:
        :param col:
        :return:
        """
        table: QtWidgets.QTableWidget = self.sender()
        initColor = QtGui.QColor(table.item(row, 1).text())
        color = QtWidgets.QColorDialog.getColor(initColor, title=f"默认颜色: {table.item(row,0).text()}")
        table.item(row, 1).setBackground(QtGui.QBrush(color))
        table.item(row, 1).setText("#%02X%02X%02X" % (color.red(), color.green(), color.blue()))

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

    def _check_ruler(self, train: Train):
        """
        检查对照标尺和实际时刻表
        0-通通
        1-起通
        2-通停
        3-起停
        :param train:
        :return:
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
            dir_ = Line.DownVia if train.isDown() else Line.UpVia
            if not former:
                if self.graph.stationInLine(name) and self.graph.stationDirection(name) & dir_:
                    former = name
                    former_time = [ddsj, cfsj]
                continue

            if not self.graph.stationInLine(name) or not self.graph.stationDirection(name) & dir_:
                continue

            row = tableWidget.rowCount()
            tableWidget.insertRow(tableWidget.rowCount())
            tableWidget.setRowHeight(row, 30)

            interval_str = f"{former}->{name}"
            item = QtWidgets.QTableWidgetItem(interval_str)
            tableWidget.setItem(row, 0, item)
            item.setData(-1, [former, name])

            dt = train.gapBetweenStation(former, name)
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
                if ds_str[0]!='-' and ds<0:
                    ds_str = '-'+ds_str

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
        :return:
        """
        import time
        from thread import ThreadDialog
        train:Train = self.GraphWidget.selectedTrain
        if train is None:
            self._derr("当前车次事件时刻表：当前没有选中车次！")
            return
        thread = ThreadDialog(self, self.GraphWidget)
        dialog=QtWidgets.QProgressDialog(self)
        dialog.setRange(0,100)
        dialog.setWindowTitle('正在处理')
        dialog.setValue(1)

        thread.eventsOK.connect(lambda events: self._train_event_out_ok(events, dialog))
        thread.start()
        # print('start ok')
        i=1
        while i<=99:
            if i<=90:
                time.sleep(0.05)
            else:
                time.sleep(1)
            dialog.setValue(i)
            i+=1
            QtCore.QCoreApplication.processEvents()
            if dialog.wasCanceled():
                return
        return

        #events = self.GraphWidget.listTrainEvent()
    def _train_event_out_ok(self,events:list,dialog):
        print('list ok')
        dialog.setValue(100)
        dialog.close()
        train: Train = self.GraphWidget.selectedTrain
        if not events:
            return

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(6)
        tableWidget.setHorizontalHeaderLabels(['时间','地点','里程','事件','客体','备注'])
        tableWidget.setRowCount(len(events))
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        widths = (100,120,90,60,80,80)
        for i,s in enumerate(widths):
            tableWidget.setColumnWidth(i,s)

        for row,event in enumerate(events):
            tableWidget.setRowHeight(row,30)
            item = QtWidgets.QTableWidgetItem(event["time"].strftime('%H:%M:%S'))
            tableWidget.setItem(row,0,item)

            space_str = event["former_station"]
            if event["later_station"] is not None:
                space_str += f'-{event["later_station"]}'
            item = QtWidgets.QTableWidgetItem(space_str)
            tableWidget.setItem(row,1,item)

            mile_str = "%.2f"%event["mile"] if event["mile"] != -1 else "NA"
            item = QtWidgets.QTableWidgetItem()
            item.setData(0,event["mile"])
            # item.setText(mile_str)
            tableWidget.setItem(row,2,item)

            type:TrainEventType = event["type"]
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
            else:
                event_str = '未知'
            item = QtWidgets.QTableWidgetItem(event_str)
            tableWidget.setItem(row,3,item)

            another = event["another"]
            if another is None:
                another = ''
            item = QtWidgets.QTableWidgetItem(another)
            tableWidget.setItem(row,4,item)

            if event["type"] == TrainEventType.pass_calculated:
                add = '推定'
            else:
                add = ''
            item = QtWidgets.QTableWidgetItem(add)
            tableWidget.setItem(row,5,item)

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("当前车次事件表")
        dialog.resize(600,600)
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel(f"{train.fullCheci()}次列车在{self.graph.lineName()}"
                                 f"按{train.downStr()}方向运行的事件时刻表如下。")
        label.setWordWrap(True)
        layout.addWidget(label)

        layout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnOut = QtWidgets.QPushButton("导出为表格")
        btnOut.clicked.connect(lambda :self._train_event_out_excel(tableWidget))
        hlayout.addWidget(btnOut)

        btnText = QtWidgets.QPushButton("导出为文字")
        btnText.clicked.connect(lambda :self._train_event_out_text(events))
        hlayout.addWidget(btnText)

        btnClose = QtWidgets.QPushButton("关闭")
        btnClose.clicked.connect(dialog.close)
        hlayout.addWidget(btnClose)

        layout.addLayout(hlayout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _train_event_out_excel(self,tableWidget):
        self.statusOut("正在准备导出……")
        try:
            import xlwt
        except ImportError:
            self._derr("需要'xlwt'库支持。如果您的程序依赖Python环境运行，请在终端执行："
                       "'pip3 install xlwt'")
            self.statusOut("就绪")
            return

        checi:str = self.GraphWidget.selectedTrain.fullCheci()
        checi_new=f"{checi.replace('/',',')}"
        filename = QtWidgets.QFileDialog.getSaveFileName(self, '选择文件',
                                                         directory=f'../{checi_new}事件时刻表@{self.graph.lineName()}', filter='*.xls')[0]
        if not filename:
            return

        wb = xlwt.Workbook(encoding='utf-8')
        ws:xlwt.Worksheet = wb.add_sheet("车次事件时刻表")

        ws.write(0,0,f"{self.GraphWidget.selectedTrain.fullCheci()}在{self.graph.lineName()}运行的事件时刻表")
        for i,s in enumerate(['时间','地点','里程','事件','客体','备注']):
            ws.write(1,i,s)

        for row in range(tableWidget.rowCount()):
            for col in range(6):
                ws.write(row+2,col,tableWidget.item(row,col).text())
        wb.save(filename)
        self._dout("列车事件时刻表导出成功！")
        self.statusOut("就绪")

    def _train_event_out_text(self,events):
        checi: str = self.GraphWidget.selectedTrain.fullCheci()
        checi.replace('/', ',')
        filename = QtWidgets.QFileDialog.getSaveFileName(self, '选择文件',
                                directory=f'../{checi}事件时刻表', filter='*.txt')[0]
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
        with open(filename,'w',encoding='utf-8',errors='ignore') as fp:
            fp.write(text)
        self._dout("导出成功！")

    def _setCurrentWidgetData(self, train: Train = None):
        """
        将current中的信息变为train的信息
        :param train:
        :return:
        """
        self.currentWidget.setData(train)

    def _initTypeDock(self):
        typeDock = QtWidgets.QDockWidget()
        typeDock.setWindowTitle("显示类型设置")
        typeDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("显示类型设置", typeDock))
        self.typeDockWidget = typeDock
        typeDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, typeDock)
        typeDock.setVisible(False)

    def _initTypeWidget(self):
        typeWidget = QtWidgets.QWidget(self)

        vlayout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()
        btnShowDown = QtWidgets.QPushButton("显示下行")
        btnShowDown.clicked.connect(lambda: self._set_dir_show(True, True))
        btnShowUp = QtWidgets.QPushButton("显示上行")
        btnShowUp.clicked.connect(lambda: self._set_dir_show(False, True))
        hlayout.addWidget(btnShowDown)
        hlayout.addWidget(btnShowUp)
        vlayout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnNoDown = QtWidgets.QPushButton("隐藏下行")
        btnNoDown.clicked.connect(lambda: self._set_dir_show(True, False))
        btnNoUp = QtWidgets.QPushButton("隐藏上行")
        btnNoUp.clicked.connect(lambda: self._set_dir_show(False, False))
        hlayout.addWidget(btnNoDown)
        hlayout.addWidget(btnNoUp)
        vlayout.addLayout(hlayout)

        listWidget = QtWidgets.QListWidget()
        listWidget.setSelectionMode(listWidget.MultiSelection)

        self._setTypeList(listWidget)

        vlayout.addWidget(listWidget)

        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("还原")

        btnOk.clicked.connect(lambda: self._apply_type_show(listWidget))
        btnCancel.clicked.connect(lambda: self._setTypeList(listWidget))

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        vlayout.addLayout(hlayout)

        typeWidget.setLayout(vlayout)

        self.typeDockWidget.setWidget(typeWidget)

    def _set_dir_show(self, down, show):
        self.graph.setDirShow(down, show)
        # print("set_dir_show ok")

    def _apply_type_show(self, listWidget: QtWidgets.QListWidget):
        not_show = []
        for i in range(listWidget.count()):
            item: QtWidgets.QListWidgetItem = listWidget.item(i)
            if not item.isSelected():
                not_show.append(item.text())

        self.graph.setNotShowTypes(not_show)
        self._initTrainWidget()
        self.GraphWidget.paintGraph()


    def _setTypeList(self, listWidget: QtWidgets.QListWidget):
        listWidget.clear()
        for type in self.graph.typeList:
            item = QtWidgets.QListWidgetItem(type)
            listWidget.addItem(item)
            if type not in self.graph.UIConfigData()["not_show_types"]:
                item.setSelected(True)

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

        rulerWidget = RulerWidget(self.graph.line,self)
        self.rulerDockWidget.setWidget(rulerWidget)
        rulerWidget.setData()

    def _initTrainDock(self):
        trainDock = QtWidgets.QDockWidget()
        trainDock.setWindowTitle("车次编辑")
        trainDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("车次编辑", trainDock))
        self.addDockWidget(Qt.LeftDockWidgetArea, trainDock)
        self.trainDockWidget = trainDock
        trainDock.close()

    def _initTrainWidget(self):
        if self.trainDockWidget is None:
            return

        trainWidget = TrainWidget(self.graph,self,self)
        self.trainWidget = trainWidget
        trainWidget.initWidget()
        trainWidget.search_train.connect(self._search_train)
        trainWidget.current_train_changed.connect(self._current_train_changed)
        trainWidget.train_double_clicked.connect(self._train_table_doubleClicked)
        trainWidget.trainShowChanged.connect(self._train_show_changed)
        trainWidget.addNewTrain.connect(self._add_train_from_list)
        trainWidget.showStatus.connect(self.statusOut)

        self.trainDockWidget.setWidget(trainWidget)

    def _train_table_doubleClicked(self, train:Train):
        """
        2018.12.28新增逻辑，强制显示运行线
        """
        train.setIsShow(True,affect_item=True)
        self.GraphWidget._line_selected(train.getItem())
        dock: QtWidgets.QDockWidget = self.currentDockWidget
        dock.setVisible(True)

    def _search_train(self, checi: str):
        train: Train = self.graph.trainFromCheci(checi)
        if train is None:
            self._derr("无此车次：{}".format(checi))
            return
        self.GraphWidget._line_un_selected()
        train.setIsShow(True,affect_item=True)
        if train.item is None:
            self.GraphWidget.addTrainLine(train)

        self.GraphWidget._line_selected(train.item, ensure_visible=True)

    def _train_show_changed(self,train:Train,show:bool):
        """
        从trainWidget的同名函数触发
        2018.12.28修改：封装trainWidget部分，直接接受车次对象。这个函数只管划线部分
        """

        if show and train.getItem() is None:
            # 如果最初铺画没有铺画运行线而要求显示运行线，重新铺画。
            # print('重新铺画运行线。Line972')
            self.GraphWidget.addTrainLine(train)

        if train is self.GraphWidget.selectedTrain and not show:
            #若取消显示当前选中的Item，则取消选择
            self.GraphWidget._line_un_selected()

    def _add_train_from_list(self):
        self._setCurrentWidgetData()
        self.currentDockWidget.setVisible(True)
        self.currentDockWidget.setFocus(True)

    def _initLineDock(self):
        dockLine = QtWidgets.QDockWidget()
        dockLine.setWindowTitle("线路编辑")
        dockLine.visibilityChanged.connect(lambda: self._dock_visibility_changed("线路编辑", dockLine))
        self.addDockWidget(Qt.RightDockWidgetArea, dockLine)
        self.lineDockWidget = dockLine
        dockLine.setVisible(False)

    def _initLineWidget(self):
        if self.lineDockWidget is None:
            return

        lineWidget = LineWidget(self.graph.line)
        lineWidget.setData()
        self.lineDockWidget.setWidget(lineWidget)
        lineWidget.lineChangedApplied.connect(self._on_line_changed)
        lineWidget.showStatus.connect(self.statusOut)

    def _on_line_changed(self):
        """
        lineWidget确认线路信息触发
        :return:
        """
        self.graph.line.resetRulers()

        try:
            self.main.GraphWidget.paintGraph()
        except:
            self.graph.setOrdinateRuler(None)
            self.GraphWidget.paintGraph()

    def _initConfigDock(self):
        configDock = QtWidgets.QDockWidget()
        configDock.setWindowTitle("运行图设置")

        configDock.visibilityChanged.connect(lambda: self._dock_visibility_changed("运行图设置", configDock))
        configDock.setVisible(False)
        self.configDockWidget = configDock
        self.addDockWidget(Qt.RightDockWidgetArea, configDock)

    def _initConfigWidget(self):
        if self.configDockWidget is None:
            return

        configWidget = QtWidgets.QWidget(self)

        vlayout = QtWidgets.QVBoxLayout()
        layout = QtWidgets.QFormLayout()
        vlayout.addLayout(layout)

        label1 = QtWidgets.QLabel("起始时刻")
        spin1 = QtWidgets.QSpinBox()
        spin1.setSingleStep(1)
        spin1.setRange(0, 24)
        spin1.setValue(self.graph.UIConfigData()["start_hour"])
        layout.addRow(label1, spin1)

        label2 = QtWidgets.QLabel("结束时刻")
        spin2 = QtWidgets.QSpinBox()
        spin2.setSingleStep(1)
        spin2.setRange(0, 24)
        spin2.setValue(self.graph.UIConfigData()["end_hour"])
        layout.addRow(label2, spin2)

        label3 = QtWidgets.QLabel("默认客车线宽")
        spin3 = QtWidgets.QDoubleSpinBox()
        spin3.setSingleStep(0.5)
        spin3.setValue(self.graph.UIConfigData()["default_keche_width"])
        layout.addRow(label3, spin3)

        label4 = QtWidgets.QLabel("默认货车线宽")
        spin4 = QtWidgets.QDoubleSpinBox()
        spin4.setSingleStep(0.5)
        spin4.setValue(self.graph.UIConfigData()["default_huoche_width"])
        layout.addRow(label4, spin4)

        # TODO 使用slider
        label7 = QtWidgets.QLabel("横轴每像素秒数")
        spin7 = QtWidgets.QDoubleSpinBox()
        spin7.setSingleStep(1)
        spin7.setRange(0, 240)
        spin7.setValue(self.graph.UIConfigData()["seconds_per_pix"])
        layout.addRow(label7, spin7)

        label8 = QtWidgets.QLabel("纵轴每像素秒数")
        spin8 = QtWidgets.QDoubleSpinBox()
        spin8.setSingleStep(1)
        spin8.setRange(0, 240)
        spin8.setValue(self.graph.UIConfigData()["seconds_per_pix_y"])
        layout.addRow(label8, spin8)

        label9 = QtWidgets.QLabel("纵轴每公里像素")
        spin9 = QtWidgets.QDoubleSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(0, 20)
        spin9.setValue(self.graph.UIConfigData()["pixes_per_km"])
        layout.addRow(label9, spin9)

        label9 = QtWidgets.QLabel("最低粗线等级")
        spin9 = QtWidgets.QSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(0, 20)
        spin9.setValue(self.graph.UIConfigData()["bold_line_level"])
        layout.addRow(label9, spin9)

        label9 = QtWidgets.QLabel("每小时纵线数")
        spin9 = QtWidgets.QSpinBox()
        spin9.setSingleStep(1)
        spin9.setRange(1, 20)
        spin9.setValue(60 / (self.graph.UIConfigData()["minutes_per_vertical_line"]) - 1)
        layout.addRow(label9, spin9)

        label10 = QtWidgets.QLabel("纵坐标标尺")
        combo = QtWidgets.QComboBox()
        self._setOrdinateCombo(combo)
        self.ordinateCombo = combo
        layout.addRow(label10, combo)

        check = QtWidgets.QCheckBox()
        check.setChecked(self.graph.UIConfigData().setdefault('showFullCheci',False))
        layout.addRow("显示完整车次",check)

        vlayout.addLayout(layout)

        label = QtWidgets.QLabel("运行图说明或备注")
        vlayout.addWidget(label)
        textEdit = QtWidgets.QTextEdit()
        textEdit.setText(self.graph.markdown())
        self.configDockWidget.textEdit = textEdit
        vlayout.addWidget(textEdit)

        btn1 = QtWidgets.QPushButton("确定")
        btn1.clicked.connect(self._applyConfig)
        btn2 = QtWidgets.QPushButton("默认")
        btn2.clicked.connect(self._clearConfig)
        btnlay = QtWidgets.QHBoxLayout()
        btnlay.addWidget(btn1)
        btnlay.addWidget(btn2)

        vlayout.addLayout(btnlay)

        configWidget.setLayout(vlayout)

        self.configDockWidget.setWidget(configWidget)

    def _setOrdinateCombo(self, combo: QtWidgets.QComboBox):
        combo.clear()
        combo.addItem("按里程")
        for ruler in self.graph.rulers():
            combo.addItem(ruler.name())
        ordinate = self.graph.ordinateRuler()
        if ordinate is None:
            combo.setCurrentIndex(0)
        else:
            combo.setCurrentText(ordinate.name())

    def _typeShowConfig(self):
        """
        设置要显示的车次类型
        :return:
        """
        self.mdi = QtWidgets.QMdiArea()
        widget = QtWidgets.QWidget(self)
        configWindow = QtWidgets.QMdiSubWindow()
        configWindow.setWidget(widget)
        self.mdi.addSubWindow(configWindow)
        configWindow.show()

    def _applyConfig(self):
        vlayout: QtWidgets.QVBoxLayout = self.configDockWidget.widget().layout()

        UIDict = self.graph.UIConfigData()

        layout: QtWidgets.QFormLayout = vlayout.itemAt(0)
        for i in range(layout.rowCount()):
            label = layout.itemAt(i, layout.LabelRole).widget()
            field = layout.itemAt(i, layout.FieldRole).widget()
            if label.text() == '起始时刻':
                UIDict["start_hour"] = field.value()
            elif label.text() == '结束时刻':
                UIDict["end_hour"] = field.value()
            elif label.text() == '默认客车线宽':
                UIDict["default_keche_width"] = field.value()
            elif label.text() == '默认货车线宽':
                UIDict["default_huoche_width"] = field.value()
            elif label.text() == '横轴每像素秒数':
                UIDict["seconds_per_pix"] = field.value()
            elif label.text() == '纵轴每像素秒数':
                UIDict["seconds_per_pix_y"] = field.value()
            elif label.text() == '纵轴每公里像素':
                UIDict["pixes_per_km"] = field.value()
            elif label.text() == '最低粗线等级':
                UIDict["bold_line_level"] = field.value()
            elif label.text() == '每小时纵线数':
                UIDict["minutes_per_vertical_line"] = 60 / (field.value() + 1)
            elif label.text() == '纵坐标标尺':
                former = self.graph.ordinateRuler()
                name = field.currentText()
                if field.currentIndex() == 0:
                    ruler = None
                else:
                    ruler = self.graph.line.rulerByName(name)

                rulerChanged=True
                if ruler is former:
                    # 标尺不变
                    rulerChanged=False
            elif label.text() == '显示完整车次':
                UIDict['showFullCheci'] = field.isChecked()

            else:
                print("无效的label")
                raise Exception("Invalid label. Add elif here.",label.text())

        textEdit = self.configDockWidget.textEdit
        self.graph.setMarkdown(textEdit.toPlainText())

        dialog = QtWidgets.QMessageBox()
        btnOk = QtWidgets.QPushButton("保存默认(&D)")
        #btnOk.setShortcut('D')
        btnOk.clicked.connect(lambda: self.GraphWidget.saveSysConfig(Copy=True))
        btnCancel = QtWidgets.QPushButton("仅运行图(&G)")
        #btnCancel.setShortcut('G')
        dialog.addButton(btnOk, dialog.AcceptRole)
        dialog.addButton(btnCancel, dialog.RejectRole)
        dialog.setText("请选择将以上设置保存为系统默认设置，还是仅应用到本运行图？")
        dialog.setWindowTitle(self.title)
        dialog.exec_()

        flag=self.changeOrdinateRuler(ruler)
        if not flag:
            self.changeOrdinateRuler(former)
        #注意：变更纵坐标标尺操作引起重新铺画运行图操作，故替代原有代码。


    def _clearConfig(self):
        """
        将所有设置恢复为默认设置
        :return:
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
        try:
            for key in keys:
                self.graph.UIConfigData()[key] = buff[key]
        except:
            traceback.print_exc()
        self._initConfigWidget()

    def changeOrdinateRuler(self, ruler: Ruler):
        """
        调整排图标尺。返回是否成功。
        :param ruler:
        :return:
        """
        former = self.graph.ordinateRuler()
        try:
            self.graph.setOrdinateRuler(ruler)
            self.GraphWidget.paintGraph(throw_error=True)
        except:
            self._derr("设置排图标尺失败！设为排图纵坐标的标尺必须填满每个区间数据。自动变更为按里程排图。")
            traceback.print_exc()
            self.graph.setOrdinateRuler(former)
            self.GraphWidget.paintGraph()
            return False

        self._setOrdinateCombo(self.ordinateCombo)
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

        actionReset = QtWidgets.QAction("重新读取本运行图",self)
        actionReset.triggered.connect(self._reset_graph)
        m1.addAction(actionReset)

        actionRefresh = QtWidgets.QAction("刷新",self)
        actionRefresh.setShortcut('F5')
        actionRefresh.triggered.connect(self.GraphWidget.paintGraph)
        actionRefresh.triggered.connect(self._initDockWidgetContents)
        m1.addAction(actionRefresh)

        actionOutput = QtWidgets.QAction(QtGui.QIcon(), "导出运行图", self)
        actionOutput.setShortcut("ctrl+T")
        actionOutput.triggered.connect(self._outputGraph)
        m1.addAction(actionOutput)
        # self.actionOutput=actionOutput

        actionOutExcel = QtWidgets.QAction('导出点单',self)
        actionOutExcel.setShortcut('ctrl+Shift+T')
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

        action = QtWidgets.QAction("模糊检索车次",self)
        action.setShortcut('ctrl+shift+F')
        action.triggered.connect(self._multi_search_train)
        menu.addAction(action)

        action = QtWidgets.QAction("重置所有始发终到站",self)
        action.triggered.connect(self._reset_start_end)
        menu.addAction(action)

        action = QtWidgets.QAction("运行图拼接",self)
        action.triggered.connect(self._joint_graph)
        action.setShortcut('ctrl+J')
        menu.addAction(action)

        #查看
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

        action = QtWidgets.QAction("当前车次区间性质计算",self)
        action.setShortcut('ctrl+shift+W')
        action.triggered.connect(self._get_interval_info)
        menu.addAction(action)

        action = QtWidgets.QAction("当前车次事件表",self)
        action.setShortcut('ctrl+Z')
        action.triggered.connect(self._train_event_out)
        menu.addAction(action)

        action = QtWidgets.QAction("车站时刻表输出", self)
        action.setShortcut('ctrl+E')
        action.triggered.connect(self._station_timetable)
        menu.addAction(action)

        action = QtWidgets.QAction("区间对数表",self)
        action.setShortcut('ctrl+3')
        action.triggered.connect(self._interval_count)
        menu.addAction(action)

        action = QtWidgets.QAction("区间车次表",self)
        action.setShortcut('ctrl+shift+3')
        action.triggered.connect(self._interval_trains)
        menu.addAction(action)

        #调整
        menu = menubar.addMenu("调整(&A)")

        action = QtWidgets.QAction("调整当前车次时刻",self)
        action.setShortcut('ctrl+A')
        action.triggered.connect(self._adjust_train_time)
        menu.addAction(action)

        action = QtWidgets.QAction("批量复制当前运行线",self)
        action.setShortcut('ctrl+shift+A')
        action.triggered.connect(self._batch_copy_train)
        menu.addAction(action)

        action = QtWidgets.QAction("反排运行图", self)
        action.triggered.connect(self._reverse_graph)
        menu.addAction(action)

        action = QtWidgets.QAction("修改站名",self)
        action.setShortcut('ctrl+U')
        action.triggered.connect(self._change_station_name)
        menu.addAction(action)

        action = QtWidgets.QAction("批量站名映射",self)
        action.setShortcut('ctrl+shift+U')
        action.triggered.connect(self._change_massive_station)
        menu.addAction(action)

        action = QtWidgets.QAction("推定通过时刻",self)
        action.setShortcut('ctrl+2')
        action.triggered.connect(self._detect_pass_time)
        menu.addAction(action)

        action = QtWidgets.QAction('高级显示车次设置',self)
        action.setShortcut('ctrl+shift+L')
        action.triggered.connect(self.showFilter.setFilter)
        menu.addAction(action)

        #数据
        menu = menubar.addMenu("数据(&S)")

        action = QtWidgets.QAction("线路数据库维护",self)
        action.setShortcut('ctrl+H')
        action.triggered.connect(self._view_line_data)
        menu.addAction(action)

        action = QtWidgets.QAction("导入线路数据",self)
        action.setShortcut('ctrl+K')
        action.triggered.connect(self._import_line)
        menu.addAction(action)

        action = QtWidgets.QAction("导入线路数据(Excel)",self)
        action.setShortcut('ctrl+shift+K')
        action.triggered.connect(self._import_line_excel)
        menu.addAction(action)

        action = QtWidgets.QAction("导入车次",self)
        action.setShortcut('ctrl+D')
        action.triggered.connect(self._import_train)
        menu.addAction(action)

        action = QtWidgets.QAction("导入实际运行线",self)
        action.setShortcut('ctrl+shift+D')
        action.triggered.connect(self._import_train_real)
        menu.addAction(action)

        # 窗口
        menu: QtWidgets.QMenu = menubar.addMenu("窗口(&W)")
        self.actionWindow_list = []
        actions = (
            '线路编辑', '车次编辑', '标尺编辑', '选中车次设置', '运行图设置', '颜色设置', '显示类型设置',
            '天窗编辑'
        )
        shorcuts = (
            'X', 'C', 'B', 'I', 'G', 'Y', 'L','1'
        )
        for a, s in zip(actions, shorcuts):
            action = QtWidgets.QAction(a, self)
            # action.setText(a)
            action.setCheckable(True)
            action.setShortcut(f'ctrl+{s}')

            menu.addAction(action)
            self.actionWindow_list.append(action)

        menu.triggered[QtWidgets.QAction].connect(self._window_menu_triggered)

        #帮助
        menu = menubar.addMenu("帮助(&H)")

        action = QtWidgets.QAction("关于",self)
        action.triggered.connect(self._about)
        menu.addAction(action)

    def _window_menu_triggered(self, action: QtWidgets.QAction):
        # print("_window_triggered")
        widgets = {
            '线路编辑': self.lineDockWidget,
            '车次编辑': self.trainDockWidget,
            '选中车次设置': self.currentDockWidget,
            '运行图设置': self.configDockWidget,
            '颜色设置': self.colorDockWidget,
            '显示类型设置': self.typeDockWidget,
            '标尺编辑': self.rulerDockWidget,
            '标尺排图向导': self.guideDockWidget,
            '天窗编辑':self.forbidDockWidget,
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
        # print("dock visibility changed! ", name)
        action = None
        for ac in self.actionWindow_list:
            if ac.text() == name:
                action = ac
                break
        if action is None:
            raise Exception("No action name {}, add or check it.".format(name))
        action.setChecked(dock.isVisible())

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
                        filter='JSON运行图文件(*.json)\n文本运行图文件(*.trc)\n所有文件(*.*)')[0]
        if not filename:
            return

        self.graph = Graph()
        self.showFilter.setGraph(self.graph)
        try:
            self.graph.loadGraph(filename)
            self.GraphWidget.setGraph(self.graph)
            self.GraphWidget.sysConfig["last_file"] = filename
            # print("last file changed")
        except:
            self._derr("文件错误！请检查")
            traceback.print_exc()
        else:
            self._initDockWidgetContents()
            self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")

    def _outputGraph(self):
        filename,ok = QtWidgets.QFileDialog.getSaveFileName(self,
                                                         caption='导出运行图',
                                                         directory=self.graph.lineName(),
                                                         filter="图像(*.png)")
        if not filename or not ok:
            return
        self.GraphWidget.save(filename)
        self._dout("导出成功！")

    def _outExcel(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, caption='导出运行图', filter="图像(*.xlsx)")[0]
        if not filename:
            return
        self.graph.save_excel(filename)
        self._dout("导出完毕")

    def _saveGraph(self):
        filename = self.graph.graphFileName()
        status: QtWidgets.QStatusBar = self.statusBar()
        status.showMessage("正在保存")
        if not self.graph.graphFileName():
            filename = QtWidgets.QFileDialog.getSaveFileName(self, "选择文件",directory=self.graph.lineName()+'.json',
                                                             filter='JSON运行图文件(*.json)\n所有文件(*.*)')[0]
        self.graph.save(filename)
        self.graph.setGraphFileName(filename)
        status.showMessage("保存成功")
        self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")

    def _saveGraphAs(self):
        """
        另存为
        :return:
        """
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "选择文件",directory=self.graph.lineName()+'.json',
                                                         filter='JSON运行图文件(*.json)\n所有文件(*.*)')[0]
        self.statusBar().showMessage("正在保存")
        self.graph.save(filename)
        self.graph.setGraphFileName(filename)
        self.statusBar().showMessage("保存成功")
        self.GraphWidget.sysConfig["last_file"] = filename
        self.setWindowTitle(f"{self.title} {self.graph.filename if self.graph.filename else '新运行图'}")

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

    def _about(self):
        text = f"{self.title}  {self.build}\n六方车迷会谈 马兴越  保留一切权利\n"
        text += "联系方式： 邮箱 mxy0268@outlook.com"
        text += '\n本系统官方交流群：865211882'
        QtWidgets.QMessageBox.about(self,'关于',text)

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def statusOut(self, note: str, seconds: int = 0):
        try:
            self.statusBar().showMessage(note, seconds)
        except:
            traceback.print_exc()

    def qustion(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, self.title, note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

    def on_focus_changed(self, train: Train):
        """
        slot。由GraphicsWidget中选中列车变化触发。
        """
        if train is None:
            return

        # 设置train编辑中的current
        self.trainWidget.setCurrentTrain(train)

        # 设置currentWidget
        self._setCurrentWidgetData(train)

    def _current_train_changed(self, train:Train):
        """
        tableWidget选中的行变化触发。第一个参数是行数有效，其余无效。
        2018.12.28修改：把解读车次的逻辑放入trainWidget中。这里直接接受列车对象
        """

        # print("current train changed. line 1708", row,train.fullCheci())

        #取消不响应非显示列车的逻辑。2018年11月20日
        """
        if not train.isShow():
            return
            """

        # 这是为了避免间接递归。若不加检查，这里取消后再次引发改变，则item选中两次。
        if self.GraphWidget.selectedTrain is not train:
            self.GraphWidget._line_un_selected()

        self.GraphWidget._line_selected(train.item, True)  # 函数会检查是否重复选择

    def _add_train_by_ruler(self):
        """
        标尺排图向导
        :return:
        """
        if not self.graph.rulerCount():
            self._derr("标尺排图向导：无可用标尺！")
            return

        painter = rulerPainter(self.GraphWidget)
        self.rulerPainter = painter
        painter.trainOK.connect(lambda x: self._setCurrentWidgetData(x))
        painter.trainOK.connect(lambda :self._initTrainWidget())
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
        checkStopOnly.toggled.connect(lambda x:self._station_timetable_stop_only_changed(timetable_dicts,
                                                                            tableWidget,station_name,x))

        label = QtWidgets.QLabel(f"*{station_name}*在本线时刻表如下：")
        layout.addWidget(label)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(9)
        tableWidget.setHorizontalHeaderLabels(['车次','站名', '到点', '开点', '类型', '停站','方向', '始发', '终到'])
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)

        header: QtWidgets.QHeaderView = tableWidget.horizontalHeader()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(tableWidget.sortByColumn)

        column_width = (80, 100, 100, 100, 80,80, 80, 90, 90)
        for i, s in enumerate(column_width):
            tableWidget.setColumnWidth(i, s)

        self._setStationTimetable(timetable_dicts,tableWidget,station_name,False)

        layout.addWidget(tableWidget)
        hlayout = QtWidgets.QHBoxLayout()
        btnOut = QtWidgets.QPushButton("导出")
        btnVisual = QtWidgets.QPushButton("可视化")
        btnClose = QtWidgets.QPushButton("关闭")
        btnClose.clicked.connect(dialog.close)
        btnOut.clicked.connect(lambda: self._station_timetable_out(tableWidget))
        btnVisual.clicked.connect(lambda :self._station_visualize(timetable_dicts,station_name))
        hlayout.addWidget(btnOut)
        hlayout.addWidget(btnVisual)
        hlayout.addWidget(btnClose)
        layout.addLayout(hlayout)

        dialog.setLayout(layout)
        dialog.exec_()

    def _setStationTimetable(self,timetable_dicts, tableWidget, station_name, stop_only):
        tableWidget.setRowCount(0)
        row = -1
        for _, node in enumerate(timetable_dicts):
            train = node["train"]
            stop_text = train.stationStopBehaviour(station_name)
            if stop_only and stop_text in ('通过','不通过'):
                # print(train.fullCheci(),stop_text)
                continue

            row += 1
            tableWidget.insertRow(row)
            tableWidget.setRowHeight(row, 30)

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

            text = '下行' if train.isDown() == True else ('上行' if train.isDown() == False else '未知')
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 6, item)

            text = train.sfz
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 7, item)

            text = train.zdz
            item = QtWidgets.QTableWidgetItem(text)
            tableWidget.setItem(row, 8, item)

    def _station_timetable_stop_only_changed(self,timetable_dicts,tableWidget,station_name,
                                             stopOnly:bool):
        self._setStationTimetable(timetable_dicts,tableWidget,station_name,stopOnly)

    def _station_visualize(self,station_dicts:list,station_name):
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
        slider.setRange(1,120)
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

        slider.valueChanged.connect(lambda x:self.stationVisualSizeChanged.emit(x))
        layout.addLayout(hlayout)

        widget = StationGraphWidget(station_dicts,self.graph,self)
        btnAdvance.clicked.connect(lambda: self._station_visualize_advance(widget))
        layout.addWidget(widget)
        dialog.setLayout(layout)
        dialog.exec_()

    def _station_visualize_advance(self,visualWidget:StationGraphWidget):
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
        flayout.addRow("铺画模式",hlayout)
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
        flayout.addRow("正线停车",hlayout)
        if visualWidget.allowMainStay():
            radioMainStay.setChecked(True)
        else:
            radioMainStayNo.setChecked(True)
        radioMainStay.toggled.connect(visualWidget.setAllowMainStay)

        spinSame = QtWidgets.QSpinBox()
        spinSame.setValue(visualWidget.sameSplitTime())
        spinSame.setRange(0,999)
        spinSame.valueChanged.connect(visualWidget.setSameSplitTime)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinSame)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        flayout.addRow("同向接车间隔",hlayout)

        spinOpposite = QtWidgets.QSpinBox()
        spinOpposite.setValue(visualWidget.oppositeSplitTime())
        spinOpposite.setRange(0,999)
        spinOpposite.valueChanged.connect(visualWidget.setOppositeSplitTime)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(spinOpposite)
        hlayout.addWidget(QtWidgets.QLabel("分钟"))
        flayout.addRow("对向接车间隔",hlayout)

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

        for i,s in enumerate(['车次', '站名', '到点', '开点', '类型', '停站','方向', '始发', '终到']):
            ws.write(0,i,s)

        for row in range(tableWidget.rowCount()):
            for col in range(9):
                ws.write(row+1,col,tableWidget.item(row, col).text())
        wb.save(filename)
        self._dout("时刻表导出成功！")
        self.statusOut("就绪")

    def _interval_count(self):
        """
        计算区间停站车次数量
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('区间对数表')
        dialog.resize(600,600)
        layout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        hlayout = QtWidgets.QHBoxLayout()
        radioStart = QtWidgets.QRadioButton('出发站')
        radioEnd = QtWidgets.QRadioButton('到达站')
        group = QtWidgets.QButtonGroup(self)
        group.addButton(radioStart)
        group.addButton(radioEnd)
        radioStart.setChecked(True)
        hlayout.addWidget(radioStart)
        hlayout.addWidget(radioEnd)
        flayout.addRow('查询方式',hlayout)
        dialog.startView=True

        radioStart.toggled.connect(lambda x:self._interval_count_method_changed(dialog,x))

        combo = QtWidgets.QComboBox()
        combo.setMaximumWidth(120)
        combo.setEditable(True)
        for st in self.graph.stations():
            combo.addItem(st)
        dialog.combo = combo
        flayout.addRow('查询车站',combo)
        layout.addLayout(flayout)
        dialog.station = ''
        combo.currentTextChanged.connect(lambda x:self._interval_count_station_changed(dialog,x))

        dialog.filter = TrainFilter(self.graph,dialog)
        btnFilt = QtWidgets.QPushButton("筛选")
        btnFilt.setMaximumWidth(120)
        dialog.filter.FilterChanged.connect(lambda :self._set_interval_count_table(dialog))
        btnFilt.clicked.connect(dialog.filter.setFilter)
        flayout.addRow('车次筛选',btnFilt)
        
        tableWidget = QtWidgets.QTableWidget()
        dialog.tableWidget = tableWidget
        tableWidget.setColumnCount(6)
        tableWidget.setHorizontalHeaderLabels(('发站','到站','车次数','始发数','终到数','始发终到'))
        widths = (80,80,80,80,80,80)
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        for i,s in enumerate(widths):
            tableWidget.setColumnWidth(i,s)
        self._set_interval_count_table(dialog)
        layout.addWidget(tableWidget)

        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(dialog.close)
        layout.addWidget(btnClose)
        dialog.setLayout(layout)
        dialog.exec_()

    def _interval_count_method_changed(self,dialog,x):
        dialog.startView = x
        self._set_interval_count_table(dialog)

    def _interval_count_station_changed(self,dialog,st):
        dialog.station = st
        self._set_interval_count_table(dialog)

    def _set_interval_count_table(self,dialog):
        tableWidget: QtWidgets.QTableWidget = dialog.tableWidget
        startView = dialog.startView
        station = dialog.station
        if not station:
            return
        tableWidget.setRowCount(0)
        count_list = self.graph.getIntervalCount(station,startView,dialog.filter)
        for i,s in enumerate(count_list):
            tableWidget.insertRow(i)
            tableWidget.setRowHeight(i,30)
            tableWidget.setItem(i,0,QtWidgets.QTableWidgetItem(s['from']))
            tableWidget.setItem(i,1,QtWidgets.QTableWidgetItem(s['to']))
            tableWidget.setItem(i,2,QtWidgets.QTableWidgetItem(str(s['count']) if s['count'] else '-'))
            tableWidget.setItem(i,3,QtWidgets.QTableWidgetItem(str(s['countSfz']) if s['countSfz'] else '-'))
            tableWidget.setItem(i,4,QtWidgets.QTableWidgetItem(str(s['countZdz']) if s['countZdz'] else '-'))
            tableWidget.setItem(i,5,QtWidgets.QTableWidgetItem(str(s['countSfZd']) if s['countSfZd'] else '-'))

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
        :return:
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('区间车次表')
        dialog.resize(600,600)
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()

        comboStart = QtWidgets.QComboBox()
        comboEnd = QtWidgets.QComboBox()
        dialog.start = self.graph.firstStation()
        dialog.end = self.graph.lastStation()
        for st in self.graph.stations():
            comboStart.addItem(st)
            comboEnd.addItem(st)
        comboStart.setEditable(True)
        comboStart.setCurrentText(dialog.start)
        comboEnd.setEditable(True)
        comboEnd.setCurrentText(dialog.end)
        comboStart.currentTextChanged.connect(lambda x:self._interval_trains_start_changed(dialog,x))
        comboEnd.currentTextChanged.connect(lambda x:self._interval_trains_end_changed(dialog,x))

        flayout.addRow('发站',comboStart)
        flayout.addRow('到站',comboEnd)

        dialog.filter = TrainFilter(self.graph, dialog)
        btnFilt = QtWidgets.QPushButton("筛选")
        btnFilt.setMaximumWidth(120)
        dialog.filter.FilterChanged.connect(lambda :self._interval_trains_table(dialog))
        btnFilt.clicked.connect(dialog.filter.setFilter)
        flayout.addRow('车次筛选', btnFilt)

        vlayout.addLayout(flayout)

        tableWidget = QtWidgets.QTableWidget()
        dialog.tableWidget = tableWidget

        tableWidget.setColumnCount(10)
        tableWidget.setHorizontalHeaderLabels(('车次','类型','发站','发时','到站','到时',
                                               '历时','旅速','始发','终到'))
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        for i,s in enumerate((80,60,80,120,80,120,120,80,80,80)):
            tableWidget.setColumnWidth(i,s)
        self._interval_trains_table(dialog)

        vlayout.addWidget(tableWidget)
        btnClose = QtWidgets.QPushButton('关闭')
        vlayout.addWidget(btnClose)
        btnClose.clicked.connect(dialog.close)

        dialog.setLayout(vlayout)
        dialog.exec_()

    def _interval_trains_start_changed(self,dialog,start):
        dialog.start = start
        self._interval_trains_table(dialog)

    def _interval_trains_end_changed(self,dialog,end):
        dialog.end = end
        self._interval_trains_table(dialog)

    def _interval_trains_table(self,dialog):
        if dialog.start==dialog.end or not dialog.start or not dialog.end:
            return
        tb:QtWidgets.QTableWidget = dialog.tableWidget
        IT = QtWidgets.QTableWidgetItem

        # ('车次','类型','发站','发时','到站','到时', '历时','旅速','始发','终到')
        # print(dialog.start,dialog.end)
        info_dicts = self.graph.getIntervalTrains(dialog.start,dialog.end,dialog.filter)
        tb.setRowCount(0)

        for i,tr in enumerate(info_dicts):
            train:Train = tr['train']
            tb.insertRow(i)
            tb.setRowHeight(i,30)

            tb.setItem(i,0,IT(train.fullCheci()))
            tb.setItem(i,1,IT(train.type))
            tb.setItem(i, 2, IT(train.stationDict(dialog.start)['zhanming']))
            tb.setItem(i,3,IT(train.stationDict(dialog.start)['cfsj'].strftime('%H:%M:%S')))
            tb.setItem(i, 4, IT(train.stationDict(dialog.end)['zhanming']))
            tb.setItem(i,5,IT(train.stationDict(dialog.end)['ddsj'].strftime('%H:%M:%S')))
            tm_int = train.gapBetweenStation(dialog.start,dialog.end)
            tm_int = int(tm_int)
            tm_str = f"{int(tm_int/3600):02d}:{int(tm_int/60)%60:02d}:{tm_int%60:02d}"
            try:
                mile = self.graph.gapBetween(dialog.start,dialog.end)
                mile_str = f"{mile}"
            except:
                mile_str = "NA"
            try:
                speed = mile/tm_int*1000*3.6
                speed_str = f"{speed:.2f}"
            except:
                speed = 0
                speed_str = 'NA'
            tb.setItem(i,6,IT(tm_str))
            item = IT(speed_str)
            if speed:
                item.setData(0,speed)
            tb.setItem(i,7,item)
            tb.setItem(i,8,IT(train.sfz))
            tb.setItem(i,9,IT(train.zdz))


    def _search_from_menu(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "搜索车次", "请输入车次：")
        if ok:
            self._search_train(name)

    def _multi_search_train(self):
        """
        模糊检索车次
        :return:
        """
        name, ok = QtWidgets.QInputDialog.getText(self, "模糊检索", "请输入车次：")
        if not ok:
            return
        selected_train = self.graph.multiSearch(name)
        if not selected_train:
            self._derr("无满足条件的车次！")
            return

        if len(selected_train) >= 2:
            checi,ok = QtWidgets.QInputDialog.getItem(self,"选择车次","有下列车次符合，请选择：",
                                                   [train.fullCheci() for train in selected_train])
            if not ok:
                return
            train = self.graph.trainFromCheci(checi,full_only=True)
            if train is None:
                self._derr("非法车次！")
                return
        else:
            #唯一匹配
            train = selected_train[0]

        self.GraphWidget._line_un_selected()
        train.setIsShow(True, affect_item=True)
        if train.item is None:
            self.GraphWidget.addTrainLine(train)

        self.GraphWidget._line_selected(train.item, ensure_visible=True)


    def closeEvent(self, event):
        self.GraphWidget.saveSysConfig()
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

    def _train_info(self):
        train: Train = self.GraphWidget.selectedTrain
        if train is None:
            self._derr("当前车次为空！")
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("车次信息")
        layout = QtWidgets.QVBoxLayout()
        text = ""

        text += f"车次：{train.fullCheci()}\n"
        text += f"分方向车次：{train.downCheci()}/{train.upCheci()}\n"
        text += f"始发终到：{train.sfz}->{train.zdz}\n"
        text += f"列车种类：{train.trainType()}\n"
        text += f"本线运行方向：{train.downStr()}\n"
        text += f"本线入图点：{train.localFirst(self.graph)}\n"
        text += f"本线出图点：{train.localLast(self.graph)}\n"
        text += f"本线图定站点数：{train.localCount(self.graph)}\n"
        text += f"本线运行里程：{train.localMile(self.graph)}\n"
        running,stay = train.localRunStayTime(self.graph)
        time = running+stay
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
            running_speed = 1000*train.localMile(self.graph)/running*3.6
            running_speed_str = "%.2f"%running_speed
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

    def _get_interval_info(self):
        """
        计算当前车次在选定区间内的主要性质，参见ctrl+Q面板。sample:
        :return:
        """
        train = self.GraphWidget.selectedTrain
        if train is None:
            self._derr("当前没有选中车次！")
            return
        dialog=IntervalWidget(self.graph,self)
        dialog.setTrain(train)
        dialog.exec_()

    def _reset_start_end(self):
        flag = self.qustion("将本线所有列车始发站设置时刻表首站、终到站设置为时刻表末站，是否继续？")
        if not flag:
            return
        for train in self.graph.trains():
            train.setStartEnd(train.firstStation(),train.endStation())
        self._initTrainWidget()
        self.statusOut("始发终到站重置成功")

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
        btnOpen.clicked.connect(lambda :self._joint_select(dialog))
        layout.addRow("文件名",hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        group = QtWidgets.QButtonGroup()
        radio1 = QtWidgets.QRadioButton("置于本线之前")
        radio2 = QtWidgets.QRadioButton("置于本线之后")
        group.addButton(radio1)
        group.addButton(radio2)
        hlayout.addWidget(radio1)
        hlayout.addWidget(radio2)
        layout.addRow("连接顺序",hlayout)
        dialog.radio1 = radio1
        radio1.setChecked(True)

        vlayout = QtWidgets.QVBoxLayout()
        checkReverse = QtWidgets.QCheckBox("线路上下行交换")
        dialog.checkReverse = checkReverse
        checkLineOnly = QtWidgets.QCheckBox("仅导入线路(不导入车次)")
        dialog.checkLineOnly = checkLineOnly
        vlayout.addWidget(checkReverse)
        vlayout.addWidget(checkLineOnly)
        layout.addRow("高级",vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定(&Y)")
        btnCancel = QtWidgets.QPushButton("取消(&C)")
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(lambda :self._joint_ok(dialog))
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        layout.addRow(hlayout)

        dialog.setLayout(layout)
        dialog.exec_()

    def _joint_select(self,dialog):
        """
        选择文件
        :param dialog:
        :return:
        """
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                    filter='JSON运行图文件(*.json)\n文本运行图文件(*.trc)\n所有文件(*.*)')[0]
        if not filename:
            return

        dialog.fileEdit.setText(filename)

    def _joint_ok(self,dialog):
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

        self.graph.jointGraph(graph_another,former,reverse,line_only)
        self.GraphWidget.paintGraph()
        self._initDockWidgetContents()
        self.statusOut("就绪")
        dialog.close()

    def _view_line_data(self):
        lineDB = LineDB()
        lineDB.resize(1100,700)
        lineDB.exec_()

    def _adjust_train_time(self):
        """
        :return:
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
        flayout.addRow("当前车次",currentLabel)

        hlayout = QtWidgets.QHBoxLayout()
        radio1 = QtWidgets.QRadioButton("提早")
        radio2 = QtWidgets.QRadioButton("延后")
        hlayout.addWidget(radio1)
        hlayout.addWidget(radio2)
        radio1.setChecked(True)
        dialog.radio = radio1
        flayout.addRow("调整方向",hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        spinMin = QtWidgets.QSpinBox()
        spinMin.setRange(0,9999)
        spinSec = QtWidgets.QSpinBox()
        spinSec.setSingleStep(10)
        spinSec.setRange(0,59)
        label = QtWidgets.QLabel(':')
        label.setFixedWidth(10)
        hlayout.addWidget(spinMin)
        hlayout.addWidget(label)
        hlayout.addWidget(spinSec)
        flayout.addRow("调整时间",hlayout)

        dialog.spinMin = spinMin
        spinMin.setMaximumWidth(100)
        dialog.spinSec = spinSec
        spinSec.setMaximumWidth(80)

        layout.addLayout(flayout)

        listWidget = QtWidgets.QListWidget()
        for name,ddsj,cfsj in train.station_infos():
            ddsj_str = ddsj.strftime('%H:%M:%S')
            cfsj_str = cfsj.strftime('%H:%M:%S')
            if (cfsj-ddsj).seconds == 0:
                cfsj_str = '...'

            item = QtWidgets.QListWidgetItem(f"{name}\t{ddsj_str}/{cfsj_str}")
            item.setData(-1,name)
            listWidget.addItem(item)
        listWidget.setSelectionMode(listWidget.MultiSelection)
        dialog.listWidget = listWidget

        layout.addWidget(listWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        btnOk.clicked.connect(lambda :self._adjust_ok(dialog))
        btnCancel.clicked.connect(dialog.close)
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)
        layout.addLayout(hlayout)

        dialog.setLayout(layout)
        dialog.exec_()

    def _adjust_ok(self,dialog):
        train:Train = self.GraphWidget.selectedTrain
        spinMin:QtWidgets.QSpinBox = dialog.spinMin
        spinSec:QtWidgets.QSpinBox = dialog.spinSec
        radio:QtWidgets.QRadioButton = dialog.radio
        listWidget:QtWidgets.QListWidget = dialog.listWidget
        ds_int = spinMin.value()*60 + spinSec.value()
        if radio.isChecked():
            ds_int = -ds_int

        for item in listWidget.selectedItems():
            name = item.data(-1)
            train.setStationDeltaTime(name,ds_int)

        self.GraphWidget.delTrainLine(train)
        self.GraphWidget.addTrainLine(train)
        dialog.close()

    def _import_line(self):
        try:
            self.statusOut("正在读取数据库文件……")
            fp = open('lines.json',encoding='utf-8',errors='ignore')
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
        progessDialog.setRange(0,total)
        progessDialog.setWindowModality(Qt.WindowModal)
        progessDialog.setWindowTitle(self.tr("正在读取线路信息"))

        self.statusOut("正在解析线路数据……")
        listWidget = QtWidgets.QListWidget()
        count = 0

        for name,line_dict in line_dicts.items():
            count += 1
            line = Line(origin=line_dict)
            lines.append(line)
            widget = QtWidgets.QWidget()
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
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        btnOk.clicked.connect(lambda :self._import_line_ok(dialog))
        btnCancel.clicked.connect(dialog.close)
        vlayout.addLayout(hlayout)

        dialog.setLayout(vlayout)
        dialog.exec_()

    def _import_line_ok(self,dialog):
        listWidget = dialog.listWidget
        lines = dialog.lines
        line = lines[listWidget.currentRow()]
        self.graph.setLine(line)
        self.graph.resetAllItems()
        self.graph.setOrdinateRuler(None)
        self.GraphWidget.paintGraph()
        self._initDockWidgetContents()
        self.statusOut("导入线路数据成功")
        dialog.close()

    def _import_line_excel(self):
        flag = self.qustion("从Excel表格中导入线路数据，抛弃当前线路数据，是否继续？"
                            "Excel表格应包含三列，分别是站名、里程、等级，不需要表头。")
        if not flag:
            return

        filename,ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开Excel表",
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
                name = ws.cell_value(row,0)
                mile = float(ws.cell_value(row,1))
                level = int(ws.cell_value(row,2))
            except:
                pass
            else:
                new_line.addStation_by_info(name,mile,level)
        self.graph.setLine(new_line)
        self.GraphWidget.paintGraph(throw_error=False)
        self._initDockWidgetContents()
        self._dout("导入成功！")

    def _change_station_name(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("站名修改")
        flayout = QtWidgets.QFormLayout()

        label = QtWidgets.QLabel("修改本线某一站名，同时调整所有车次的该站站名，重新铺画运行图。")
        label.setWordWrap(True)
        flayout.addRow(label)

        comboBefore = QtWidgets.QComboBox()
        comboBefore.setEditable(True)
        for name in self.graph.stations():
            comboBefore.addItem(name)
        flayout.addRow("原站名",comboBefore)
        dialog.comboBefore = comboBefore

        editNew = QtWidgets.QLineEdit()
        dialog.editNew = editNew
        flayout.addRow("新站名",editNew)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        btnOk.clicked.connect(lambda :self._change_station_name_ok(dialog))
        btnCancel.clicked.connect(dialog.close)
        flayout.addRow(hlayout)

        dialog.setLayout(flayout)
        dialog.exec_()

    def _change_station_name_ok(self,dialog):
        """
        逻辑说明：不允许将已经存在的站改为另一个存在的站，防止冲突。允许修改不存在于线路表的站名。
        :param dialog:
        :return:
        """
        comboBefore = dialog.comboBefore
        editNew = dialog.editNew
        old = comboBefore.currentText()
        new = editNew.text()

        old_dict = self.graph.stationByDict(old)
        new_dict = self.graph.stationByDict(new)

        if old_dict is not None and new_dict is not None:
            self._derr("错误：不能将一个本线上的站名修改为另一个本线上的站名。")
            return
        elif not old or not new:
            self._derr("错误：站名不能为空！")
            return

        self.graph.resetStationName(old,new)

        dialog.close()
        self.GraphWidget.paintGraph()
        self._initDockWidgetContents()
        if '::' in new:
            self._out_domain_info()

        self.statusOut("站名变更成功")

    def _out_domain_info(self):
        """
        检测到域解析符时，输出提示
        :return:
        """
        self._dout("您使用了域解析符(::)。本程序中域解析符用于分隔站名与场名，在没有完全匹配时生效。"
                   "例如，“成都东::达成场”可以匹配到“成都东”。\n"
                   "请确认您知悉以上内容并继续。\n本提示不影响确认动作的执行。")

    def _import_train(self):
        flag = self.qustion("选择运行图，导入其中所有在本线的车次，忽略已存在的车次。是否继续？")
        if not flag:
            return

        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                            filter='JSON运行图文件(*.json)\n文本运行图文件(*.trc)\n所有文件(*.*)')[0]
        if not filename:
            return

        graph = Graph()
        try:
            graph.loadGraph(filename)
        except Exception as e:
            self._derr("运行图文件无效，请检查！"+str(repr(e)))
            traceback.print_exc()
            return
        else:
            num = self.graph.addTrainByGraph(graph)
            self._initTrainWidget()
            self.GraphWidget.paintGraph()
            self._initTrainWidget()
            self._dout(f"成功导入{num}个车次。")

    def _import_train_real(self):
        flag = self.qustion("选择运行图，导入其中所有在本线的车次，车次前冠以“R”，类型为“实际”。是否继续？")
        if not flag:
            return

        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='JSON运行图文件(*.json)\n文本运行图文件(*.trc)\n所有文件(*.*)')[0]
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
                train.setCheci('R'+train.fullCheci(),'R'+train.downCheci(),'R'+train.upCheci())
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
        dialog = QtWidgets.QDialog(self)
        layout = QtWidgets.QVBoxLayout()
        dialog.setWindowTitle('批量站名映射')
        label = QtWidgets.QLabel("设置以下映射规则。把车次时刻表中站名变为站::场解析形式的站名，线路信息表"
                                 "中站名变为纯站名（无场名）。选中的行将被执行。")
        label.setWordWrap(True)
        layout.addWidget(label)

        map_list = self._readStationMap()
        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setColumnCount(2)
        tableWidget.setColumnWidth(0,160)
        tableWidget.setColumnWidth(1,160)
        tableWidget.setHorizontalHeaderLabels(['原名','映射名'])
        tableWidget.setSelectionBehavior(tableWidget.SelectRows)
        tableWidget.setRowCount(len(map_list))
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)

        for row,st_dict in enumerate(map_list):
            tableWidget.setRowHeight(row,30)

            item = QtWidgets.QTableWidgetItem(st_dict["origin"])
            tableWidget.setItem(row,0,item)

            item = QtWidgets.QTableWidgetItem(st_dict["station_field"])
            tableWidget.setItem(row,1,item)

            if self.graph.stationInLine(st_dict["origin"]):
                item.setSelected(True)

        layout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton("添加")
        btnDel = QtWidgets.QPushButton("删除")
        btnSave = QtWidgets.QPushButton("保存")

        btnAdd.clicked.connect(lambda :tableWidget.insertRow(tableWidget.rowCount()))
        btnAdd.clicked.connect(lambda :tableWidget.setRowHeight(tableWidget.rowCount()-1,30))
        btnDel.clicked.connect(lambda :tableWidget.removeRow(tableWidget.currentRow()))
        btnSave.clicked.connect(lambda :self._save_station_map(tableWidget))

        btnAdd.setMinimumWidth(60)
        btnDel.setMinimumWidth(60)
        btnSave.setMinimumWidth(60)

        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        hlayout.addWidget(btnSave)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("应用")
        btnClose = QtWidgets.QPushButton("关闭")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnClose)

        btnOk.clicked.connect(lambda :self._apply_station_map(tableWidget))
        btnClose.clicked.connect(dialog.close)
        layout.addLayout(hlayout)

        dialog.setLayout(layout)
        dialog.exec_()

    def _readStationMap(self):
        try:
            fp = open('station_map.json',encoding='utf-8',errors='ignore')
            map_list = json.load(fp)
        except:
            self._dout("未找到映射数据库文件或格式错误！请检查station_map.json，或继续维护信息。")
            return []
        else:
            fp.close()
            return map_list

    def _save_station_map(self,tableWidget:QtWidgets.QTableWidget):
        map_list = []
        for row in range(tableWidget.rowCount()):
            st_dict = {
                'origin':tableWidget.item(row,0).text(),
                'station_field':tableWidget.item(row,1).text()
            }
            map_list.append(st_dict)
        with open('station_map.json','w',encoding='utf-8',errors='ignore') as fp:
            json.dump(map_list,fp,ensure_ascii=False)
            self.statusOut('保存站名映射信息成功')

    def _apply_station_map(self,tableWidget:QtWidgets.QTableWidget):
        rows = []
        failed_rows = []
        failed_index = []
        for index in tableWidget.selectedIndexes():
            row = index.row()
            if row in rows or row in failed_index:
                continue

            item0 = tableWidget.item(row,0)
            item1 = tableWidget.item(row,1)
            old = item0.text() if item0 else ''
            new = item1.text() if item1 else ''

            if self.graph.stationInLine(old,strict=True) and self.graph.stationInLine(new,strict=True):
                failed_rows.append((old,new))
                failed_index.append(row)
                continue
            if not old or not new:
                failed_rows.append((old,new))
                failed_index.append(row)
                continue
            self.graph.resetStationName(old,new,auto_field=True)
            rows.append(row)
        text = f"成功执行{len(rows)}条映射。"
        if failed_rows:
            text += "\n以下映射未能执行，可能因为原站名、新站名都是已存在的站名或存在空格：\n"
            for row in failed_rows:
                old = row[0]
                new = row[1]
                text += f"{old}->{new}\n"
        self._dout(text)
        if rows:
            self.GraphWidget.paintGraph()
            self._initDockWidgetContents()

    def _detect_pass_time(self):
        if not self.graph.rulerCount():
            self._derr("推定通过时刻：请先添加标尺！")
            return
        else:
            if not self.qustion('此操作将删除要推定时刻列车时刻表中【非本线】的站点，是否继续？'):
                return
        dialog=DetectWidget(self,self)
        #dialog.okClicked.connect(self.GraphWidget.paintGraph)
        dialog.exec_()

    def _train_show_filter_ok(self):
        for train in self.graph.trains():
            if self.showFilter.check(train):
                train.setIsShow(True,affect_item=False)
            else:
                train.setIsShow(False,affect_item=False)
        self._initTrainWidget()
        self.GraphWidget.paintGraph()

    def _batch_copy_train(self):
        """
        批量复制列车运行线
        :return:
        """
        if self.GraphWidget.selectedTrain is None:
            self._derr("批量复制当前运行线：当前没有选中车次！")
            return

        train:Train = self.GraphWidget.selectedTrain

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
        flayout.addRow("当前车次",lineEdit)
        vlayout.addLayout(flayout)

        tableWidget = QtWidgets.QTableWidget()
        dialog.tableWidget = tableWidget
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)

        tableWidget.setColumnCount(2)
        tableWidget.setHorizontalHeaderLabels(('车次','始发时刻'))
        tableWidget.setColumnWidth(0,120)
        tableWidget.setColumnWidth(1,120)

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

        btnAdd.clicked.connect(lambda :self._add_batch_copy_line(tableWidget))
        btnDel.clicked.connect(lambda :tableWidget.removeRow(tableWidget.currentRow()))
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(lambda :self._add_batch_train_ok(dialog))

        dialog.setLayout(vlayout)
        dialog.exec_()

    def _add_batch_copy_line(self,tableWidget:QtWidgets.QTableWidget):
        row = tableWidget.rowCount()
        tableWidget.insertRow(row)

        tableWidget.setRowHeight(row,30)
        timeEdit = QtWidgets.QTimeEdit()
        timeEdit.setDisplayFormat('hh:mm:ss')
        timeEdit.setMinimumSize(1,1)
        tableWidget.setCellWidget(row,1,timeEdit)

    def _add_batch_train_ok(self,dialog):
        tableWidget:QtWidgets.QTableWidget = dialog.tableWidget
        train:Train = self.GraphWidget.selectedTrain
        start_time = train.start_time()

        failed = []

        for row in range(tableWidget.rowCount()):
            try:
                checi = tableWidget.item(row,0).text()
            except:
                checi = ''

            timeQ:QtCore.QTime = tableWidget.cellWidget(row,1).time()
            s_t = datetime(1900,1,1,timeQ.hour(),timeQ.minute(),timeQ.second())
            dt = s_t-start_time

            if not checi or self.graph.checiExisted(checi):
                failed.append((checi,s_t))
                continue
            # print(train.fullCheci(),dt)
            new_train = train.translation(checi,dt)
            self.graph.addTrain(new_train)
            self.GraphWidget.addTrainLine(new_train)

        self._initTrainWidget()

        text = f"成功复制{tableWidget.rowCount()-len(failed)}个车次。"
        if failed:
            text += '\n以下信息车次未能成功复制。可能由于车次已经存在，或者车次为空：'
            for checi,s_t in failed:
                text += f'\n{checi if checi else "空"},{s_t.strftime("%H:%M:%S")}'
        self._dout(text)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = mainGraphWindow()
    mainWindow.show()
    sys.exit(app.exec_())

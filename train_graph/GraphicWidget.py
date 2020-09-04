"""
时间使用：datetime.datetime对象
copyright (c) mxy 2018
2019年4月27日批注，自2.0.2版本开始规范化图形空间的z_value。分配如下
0：基本层。包含底图框线。
[1,5) 区间安排底图上的修饰内容。目前仅有天窗。天窗为1.
[5,10)区间安排列车运行线。目前统一安排为5.
10：选中车次运行线层。
[10,15)预留。
[15,20)软件悬浮层。目前安排距离轴、时间轴15，选中车次名称16.
"""
import cgitb
import traceback
from .pyETRCExceptions import *

cgitb.enable(format='text')

import sys
from PyQt5 import QtWidgets, QtGui, QtCore, QtPrintSupport
from PyQt5.QtCore import Qt
from .data.graph import Graph,Train,Ruler,Line
from .data.forbid import Forbid,ServiceForbid,ConstructionForbid
from datetime import timedelta, datetime
import time
from enum import Enum
from .trainItem import TrainItem


class TrainEventType(Enum):
    meet = 0  # 会车
    overTaking = 1  # 越行
    avoid = 2  # 待避
    arrive = 3  # 到站
    leave = 4  # 出发
    pass_settled = 5
    pass_calculated = 6
    unknown = -1
    origination = 7  # 始发
    destination = 8  # 终到


class GraphicsWidget(QtWidgets.QGraphicsView):
    focusChanged = QtCore.pyqtSignal(Train)  # 定义信号，选中车次变化
    rulerChanged = QtCore.pyqtSignal(Ruler)
    showNewStatus = QtCore.pyqtSignal([str], [str, int])  # 显示状态栏信息
    lineDoubleClicked = QtCore.pyqtSignal()

    def __init__(self, graph:Graph, parent=None):
        super().__init__(parent)

        self.setWindowTitle("GraphicsViewsTestWindow")
        self.setWindowIcon(QtGui.QIcon('icon.ico'))
        QtWidgets.QScroller.grabGesture(self,QtWidgets.QScroller.TouchGesture)
        # self.setGeometry(200, 200, 1200, 600)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.graph = graph
        self._initMenu()

        self.appendix_margins = {
            "title_row_height":40,  # 左侧表格的表头高度
            "first_row_append":15,  # 第一行表格附加的高度
        }
        self.marginItemGroups = {
            "up": None,
            "down": None,
            "left": None,
            "right": None
        }

        self.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.selectedTrain = None

        self.setGraph(self.graph)
        self.setMouseTracking(True)

    def _initMenu(self):
        """
        右键快捷菜单。
        """
        menu = QtWidgets.QMenu()
        self.menu = menu
        action = QtWidgets.QAction('标尺对照(Ctrl+W)',self)
        menu.addAction(action)
        action = QtWidgets.QAction('两车次运行对照(Ctrl+Shift+Z)', self)
        menu.addAction(action)
        action = QtWidgets.QAction('车次事件表(Ctrl+Z)',self)
        menu.addAction(action)
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction('时刻调整(Ctrl+A)',self))
        menu.addAction(QtWidgets.QAction('时刻重排(Ctrl+V)',self))
        menu.addAction(QtWidgets.QAction('批量复制(Ctrl+Shift+A)',self))
        menu.addAction(QtWidgets.QAction('区间换线(Ctrl+5)',self))
        menu.addAction(QtWidgets.QAction('推定时刻(Ctrl+2)',self))
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction('添加车次(Ctrl+Shift+C)',self))
        menu.addAction(QtWidgets.QAction('标尺排图向导(Ctrl+R)',self))

    def setMargin(self):
        """
        1.4版本修改：新增precondition：已知进入本函数时graph._config中的margins已经初始化完毕。
        """
        self.margins = self.graph.UIConfigData().get("margins",None)

    def setGraph(self, graph: Graph, paint=True):
        self.selectedTrain = None
        self.graph = graph
        if paint:
            self.paintGraph()

    def paintGraph(self, throw_error=False, force=False):
        """
        throw_error:出现标尺排图错误时是否继续向外抛出。
        force: 强制绘制，表示不是由系统自动调用，而是用户手动要求绘制的，此时不受“自动铺画”选项限制。
        在标尺编辑面板调整重新排图是置为True，显示报错信息。
        """
        self.scene.clear()
        self.selectedTrain = None
        # if self.graph.isEmpty():
        #     return
        if not force and not self.graph.UIConfigData().get('auto_paint',True):
            return
        self.showNewStatus.emit("正在铺画运行图：{}".format(self.graph.lineName()))
        self.setMargin()
        try:
            self.initSecne()
        except RulerNotCompleteError as e:
            if throw_error:
                raise e
            else:
                # 静默处理错误
                # traceback.print_exc()  #debug only
                self.graph.setOrdinateRuler(None)
                self.initSecne()
        except Exception as e:
            traceback.print_exc()
            print("Unexpected Exception while painting graph",repr(e))

        self._resetDistanceAxis()
        self._resetTimeAxis()
        self.showNewStatus.emit("运行图：{}铺画完毕".format(self.graph.lineName()))

    def initSecne(self):
        # self.setStyleSheet("padding:0px;border:0px")
        if self.graph is None:
            return
        self.graph.line.enableNumberMap()

        UIDict = self.graph.UIConfigData()
        if isinstance(UIDict["ordinate"], str):
            UIDict["ordinate"] = self.graph.line.rulerByName(UIDict["ordinate"])

        valid_hours = []  # 允许时间的小时数。最后一个的整点不写进去。
        start = self.graph.UIConfigData()["start_hour"]
        end = self.graph.UIConfigData()["end_hour"]
        if end <= start:
            end += 24

        for h in range(start, end):
            valid_hours.append(h % 24)
        self.valid_hours = valid_hours

        gridColor = QtGui.QColor(UIDict["grid_color"])
        hour_count = self.graph.UIConfigData()["end_hour"] - self.graph.UIConfigData()["start_hour"]
        if hour_count <= 0:
            hour_count += 24

        width = hour_count * (3600 / UIDict["seconds_per_pix"])

        if UIDict["ordinate"] is None:
            height = self.graph.lineLength() * UIDict["pixes_per_km"]
        else:
            height = UIDict["ordinate"].totalTime() / UIDict["seconds_per_pix_y"]

        self.scene.setSceneRect(0, 0, width + self.margins["left"] + self.margins["right"],
                                height + self.margins["up"] + self.margins["down"])
        self.scene.addRect(self.margins["left"], self.margins["up"], width, height, gridColor)

        self._setHLines(UIDict, gridColor, width, height)
        self._setVLines(UIDict, gridColor, height, width, hour_count)

        if self.parent():
            progressDialog = QtWidgets.QProgressDialog()
            progressDialog.setRange(0, self.graph.trainCount())
            progressDialog.setCancelButtonText('中止铺画')
            progressDialog.setWindowTitle('正在铺画')
            progressDialog.setValue(0)
        i = 0
        QtCore.QCoreApplication.processEvents()
        for train in self.graph.trains():
            train.clearItems()
            i += 1
            if train.trainType() not in self.graph.typeList:
                self.graph.typeList.append(train.trainType())

            # 2018.12.15修改：取消这个逻辑。设置显示类型面板确定时已经设置过，这里不重复。
            # if train.trainType() in UIDict["not_show_types"]:
            #     train.setIsShow(False,affect_item=False)

            # 2018.12.23补正：如果车次在本线里程为0会绕过下面的set None过程，故这里先加一个无条件set。
            train.setItem(None)
            if train.isShow():
                self.addTrainLine(train)
            # else:
            #     # 2018.12.15补正：对show=False的将item设为None，相当于删除item对象，防止再次要求显示时发生错误。
            #     train.clearItems()

            if self.parent():
                progressDialog.setValue(i)
                progressDialog.setLabelText(f'正在铺画运行线({i}/{self.graph.trainCount()}): {train.fullCheci()}')
                if i % 10 == 0:
                    # 平衡更新界面和整体速度。仅在整10才更新界面。
                    QtCore.QCoreApplication.processEvents()
                if progressDialog.wasCanceled():
                    break

        self._resetForbidShow(self.graph.line.forbid)
        self._resetForbidShow(self.graph.line.forbid2)

        self.verticalScrollBar().valueChanged.connect(self._resetTimeAxis)
        self.horizontalScrollBar().valueChanged.connect(self._resetDistanceAxis)
        self.graph.line.disableNumberMap()

    def _resetForbidShow(self,forbid:Forbid):
        if forbid.downShow():
            self.show_forbid(forbid,True)
        if forbid.upShow():
            self.show_forbid(forbid,False)


    def _setHLines(self, UIDict: dict, gridColor: QtGui.QColor, width: int, height: int):
        """
        保证每个站都有y_value
        """
        leftItems, rightItems = [], []

        textColor = QtGui.QColor(UIDict["text_color"])
        brushColor = QtGui.QColor(Qt.white)
        brushColor.setAlpha(200)
        label_start_x = self.margins["mile_label_width"]+self.margins["ruler_label_width"]
        rectLeft = self.scene.addRect(0,
                                      self.margins["up"] - self.appendix_margins["title_row_height"]-
                                      self.appendix_margins["first_row_append"],
                                      self.margins["label_width"]+self.margins["ruler_label_width"]+
                                      self.margins["mile_label_width"]+self.margins["left_white"],
                                      height + 2*self.appendix_margins["first_row_append"]+
                                      self.appendix_margins["title_row_height"])
        rectLeft.setBrush(QtGui.QBrush(brushColor))
        rectLeft.setPen(QtGui.QPen(Qt.transparent))
        rectLeft.setZValue(-1)
        leftItems.append(rectLeft)

        rectRight = self.scene.addRect(self.scene.width() - self.margins["label_width"]-
                                       self.margins["right_white"],
                                       self.margins["up"] - self.appendix_margins["title_row_height"] -
                                       self.appendix_margins["first_row_append"],
                                       self.margins["label_width"],
                                       height + 2 * self.appendix_margins["first_row_append"] +
                                       self.appendix_margins["title_row_height"])
        rectRight.setBrush(QtGui.QBrush(brushColor))
        rectRight.setPen(QtGui.QPen(Qt.transparent))
        rightItems.append(rectRight)

        defaultPen = QtGui.QPen(gridColor, UIDict.setdefault("default_grid_width",1))
        boldPen = QtGui.QPen(gridColor, UIDict.setdefault("bold_grid_width",2.5))
        least_bold = UIDict["bold_line_level"]

        textFont = QtGui.QFont()
        textFont.setBold(True)

        ruler: Ruler = self.graph.UIConfigData()["ordinate"]

        rect_start_y = self.margins["up"] - \
                       self.appendix_margins["title_row_height"] - self.appendix_margins["first_row_append"]
        rulerRect:QtWidgets.QGraphicsRectItem = self.scene.addRect(self.margins["left_white"],rect_start_y,
                                       self.margins["mile_label_width"]+self.margins["ruler_label_width"],
                                       self.scene.height()-rect_start_y-self.margins["down"]+
                                       self.appendix_margins["first_row_append"])
        rulerRect.setPen(defaultPen)
        leftItems.append(rulerRect)

        # 表格纵向分界线
        line = self.scene.addLine(self.margins["ruler_label_width"]+self.margins["left_white"],
                                  rect_start_y,
                                  self.margins["ruler_label_width"]+self.margins["left_white"],
                                  self.scene.height()-self.margins["down"]+self.appendix_margins["first_row_append"]
                                  )
        line.setPen(defaultPen)
        leftItems.append(line)

        # 标尺栏横向分界线
        line = self.scene.addLine(self.margins["left_white"],rect_start_y+self.appendix_margins["title_row_height"]/2,
                                  self.margins["ruler_label_width"]+self.margins["left_white"],
                                  rect_start_y+self.appendix_margins["title_row_height"]/2)
        line.setPen(defaultPen)
        leftItems.append(line)

        # 表头下横分界线
        line = self.scene.addLine(self.margins["left_white"],
                                  rect_start_y + self.appendix_margins["title_row_height"],
                                  self.margins["ruler_label_width"]+self.margins["mile_label_width"]+
                                  self.margins["left_white"],
                                  rect_start_y + self.appendix_margins["title_row_height"])
        line.setPen(defaultPen)
        leftItems.append(line)

        nowItem: QtWidgets.QGraphicsSimpleTextItem = self.scene.addSimpleText(' ',
                                                                  font=QtGui.QFont('Sim sum', 12))  # 当前车次信息显示在左上角
        # timeItems.append(nowItem)
        self.nowItem = nowItem
        # nowItem.setDefaultTextColor(QtGui.QColor(UIDict["text_color"]))
        nowItem.setBrush(QtGui.QBrush(QtGui.QColor(UIDict['text_color'])))
        nowItem.setZValue(16)

        rulerTitle = self._addLeftTableText('排图标尺',textFont,textColor,0,rect_start_y,
                                            self.margins["ruler_label_width"],
                                            self.appendix_margins["title_row_height"]/2)
        leftItems.append(rulerTitle)

        downTitle = self._addLeftTableText('下行',textFont,textColor,0,
                                           rect_start_y+self.appendix_margins["title_row_height"]/2,
                                            self.margins["ruler_label_width"]/2,
                                            self.appendix_margins["title_row_height"]/2)
        leftItems.append(downTitle)

        upTitle = self._addLeftTableText('上行',textFont,textColor,
                                         self.margins["ruler_label_width"]/2,
                                           rect_start_y+self.appendix_margins["title_row_height"]/2,
                                            self.margins["ruler_label_width"]/2,
                                            self.appendix_margins["title_row_height"]/2)
        leftItems.append(upTitle)

        mileTitle = self._addLeftTableText('延长公里',textFont,textColor,
                                            self.margins["ruler_label_width"],
                                           rect_start_y,
                                            self.margins["mile_label_width"],
                                            self.appendix_margins["title_row_height"])
        leftItems.append(mileTitle)

        if ruler is not None and ruler.different():
            # 上下行分设，在标尺中间划线
            line = self.scene.addLine(self.margins["ruler_label_width"]/2+self.margins["left_white"],
                                      rect_start_y+self.appendix_margins["title_row_height"]/2,
                                      self.margins["ruler_label_width"]/2+self.margins["left_white"],
                                      height+self.margins["up"]+self.appendix_margins["first_row_append"]
                                      # +self.appendix_margins["title_row_height"]/2,
                                      )
            line.setPen(defaultPen)
            leftItems.append(line)


        if ruler is None:
            # 按里程排图
            print("按里程排图")
            for st_dict in self.graph.stationDicts():
                name,mile,level = st_dict["zhanming"],st_dict["licheng"],st_dict["dengji"]
                dir_ = st_dict.setdefault("direction",0x3)
                isShow = st_dict.setdefault("show",True)
                h = mile * UIDict["pixes_per_km"] + self.margins["up"]
                if isShow:
                    pen = boldPen if level <= least_bold else defaultPen
                    self._drawSingleHLine(textColor, textFont, h, name, pen, width, leftItems, rightItems, dir_,
                                          label_start_x)
                    mileText = self._addStationTableText(f'{mile:.1f}',textFont,textColor,
                                                         self.margins["ruler_label_width"],
                                                         h,
                                                         self.margins["mile_label_width"])
                    leftItems.append(mileText)
                self.graph.setStationYValue(name, h)

        else:
            # 按标尺排图
            print("按标尺排图")
            last_station = ''
            y = self.margins["up"]
            last_y = y
            last_showed_y = y  # 这两个用于对付区间存在通过但不显示车站的情况。
            this_interval_sum = 0
            line_width = self.margins["ruler_label_width"] if not ruler.different() else \
                self.margins["ruler_label_width"] / 2
            for st_dict in self.graph.stationDicts():
                name,mile,level = st_dict["zhanming"],st_dict["licheng"],st_dict["dengji"]
                dir_ = st_dict.setdefault("direction",0x3)
                isShow = st_dict.setdefault("show",True)
                if not self.graph.stationDirection(name):
                    # 上下行都不经过的站不铺画
                    isShow = False
                # textItem = self.scene.addText(name + str(mile))
                if ruler.isDownPassed(name):
                    # 第一轮先铺画下行经由的站
                    continue

                if not last_station:
                    # 第一个站
                    last_station = name
                    # textItem.setY(y-13)
                    self.graph.setStationYValue(name, y)
                    if not isShow:
                        continue
                    self._drawSingleHLine(textColor, textFont, y, name,
                                          defaultPen, width, leftItems, rightItems, dir_,label_start_x)
                    mileText = self._addStationTableText(f'{mile:.1f}', textFont, textColor,
                                                         self.margins["ruler_label_width"],
                                                         y,
                                                         self.margins["mile_label_width"])
                    leftItems.append(mileText)
                    line = self.scene.addLine(self.margins["left_white"], y,
                                              line_width+self.margins["left_white"], y)
                    line.setZValue(3)
                    line.setPen(defaultPen)
                    leftItems.append(line)
                    continue
                info = ruler.getInfo(last_station, name)

                if info is None:
                    # 标尺不完整，不能用于排图
                    raise RulerNotCompleteError(last_station,name)
                    # y += (mile - last_mile) * UIDict["pixes_per_km"]
                    # labeItem = self.scene.addText("{}km".format(mile-last_mile))
                    # labeItem.setY((y + last_y) / 2 - 13)
                    # self.graph.setStationYValue(name, y)
                else:
                    y += info["interval"] / UIDict["seconds_per_pix_y"]
                    # labeItem = self.scene.addText("{}s".format(info["interval"]))
                    # labeItem.setY((y+last_y)/2-13)
                    self.graph.setStationYValue(name, y)

                this_interval_sum += info["interval"]
                if isShow:
                    if level <= least_bold:
                        self._drawSingleHLine(textColor, textFont, y, name,
                                              boldPen, width, leftItems, rightItems, dir_,label_start_x)
                        # self.scene.addLine(self.margins["left"], y, width+self.margins["left"] , y,boldPen)
                    else:
                        # self.scene.addLine(self.margins["left"], y, width + self.margins["left"], y, defaultPen)
                        self._drawSingleHLine(textColor, textFont, y, name,
                                              defaultPen, width, leftItems, rightItems, dir_,label_start_x)
                    # 延长公里标记
                    mileText = self._addStationTableText(f'{mile:.1f}', textFont, textColor,
                                                         self.margins["ruler_label_width"],
                                                         y,
                                                         self.margins["mile_label_width"])
                    leftItems.append(mileText)
                    # 区间标尺标记
                    line = self.scene.addLine(self.margins["left_white"],y,
                                              line_width+self.margins["left_white"],y)
                    line.setPen(defaultPen)
                    leftItems.append(line)
                    int_str = f'{int(this_interval_sum/60)}:{this_interval_sum%60:02d}'
                    intervalText = self._addStationTableText(int_str,
                                                             textFont, textColor,
                                                         0,(y+last_showed_y)/2,
                                                         line_width)
                    # print(int_str,last_station,name,last_y,y)
                    leftItems.append(intervalText)
                    last_showed_y = y
                    this_interval_sum = 0


                last_y = y
                last_station = name

            for station in ruler.downPass():
                st_dict = self.graph.stationByDict(station,True)
                dir_ = st_dict.setdefault('direction',0x3)
                mile = st_dict["licheng"]
                # 补刀，画上行。注意不显示的站要画上行。
                if station in ruler.upPass():
                    continue

                former_dict = self.graph.formerBothStation(station)
                latter_dict = self.graph.latterBothStation(station)

                total_y = latter_dict["y_value"] - former_dict["y_value"]
                try:
                    t1 = ruler.getInfo(station, former_dict["zhanming"], True)["interval"]
                    t2 = ruler.getInfo(latter_dict["zhanming"], station, True)["interval"]
                except:
                    print(station, former_dict["zhanming"], latter_dict["zhanming"])
                    raise RulerNotCompleteError(former_dict['zhanming'],station)
                dy = t1 / (t1 + t2) * total_y
                y = former_dict["y_value"] + dy

                self.graph.setStationYValue(station, y)

                if self.graph.stationIsShow(station):
                    level = self.graph.stationLevel(station)
                    pen = boldPen if level <= UIDict["bold_line_level"] else defaultPen
                    self._drawSingleHLine(textColor, textFont, y,
                                          station, pen, width, leftItems, rightItems, dir_,label_start_x)
                    text = self._addStationTableText(f'{mile:.1f}',textFont,textColor,
                                              self.margins["ruler_label_width"],y,
                                              self.margins["mile_label_width"])
                    leftItems.append(text)

            # 标记上行方向标尺的区间历时
            if ruler.different():
                last_y = self.margins["up"]+height
                last_station = ''
                last_showed_y = last_y
                this_interval_sum = 0
                for st_dict in self.graph.stationDicts(reverse=True):
                    name, mile, level = st_dict["zhanming"], st_dict["licheng"], st_dict["dengji"]
                    dir_ = st_dict.setdefault("direction", 0x3)
                    isShow = st_dict.setdefault("show", True)
                    if not dir_ & Line.UpVia:
                        continue

                    info = ruler.getInfo(last_station, name)
                    if info is None:
                        int_str = 'NA'
                    else:
                        this_interval_sum += info["interval"]
                        int_str = f'{int(this_interval_sum/60)}:{this_interval_sum%60:02d}'
                    if isShow:
                        if not last_station:
                            last_station = name
                            y = self.graph.stationYValue(name)
                            last_y = y
                            line = self.scene.addLine(line_width+self.margins["left_white"], y,
                                                      line_width*2+self.margins["left_white"], y)
                            line.setZValue(3)
                            line.setPen(defaultPen)
                            leftItems.append(line)
                            continue

                        # 只要能画出来，y_value是一定存在的，不用判断
                        y = self.graph.stationYValue(name)
                        line = self.scene.addLine(line_width+self.margins["left_white"],y,
                                                  2*line_width+self.margins["left_white"],y)
                        line.setPen(defaultPen)
                        line.setZValue(0.2)
                        leftItems.append(line)
                        # print(name,y,sep='\t')
                        intervalText = self._addStationTableText(int_str,
                                                                 textFont, textColor,
                                                                 line_width, (y + last_showed_y) / 2,
                                                                 line_width)
                        leftItems.append(intervalText)
                        last_showed_y = y
                        this_interval_sum = 0
                    last_y = y
                    last_station = name



        group1 = self.scene.createItemGroup(leftItems)
        group1.setZValue(15)
        group2 = self.scene.createItemGroup(rightItems)
        group2.setZValue(15)
        self.marginItemGroups["left"] = group1
        self.marginItemGroups["right"] = group2

    def _addLeftTableText(self,text:str,textFont,textColor,start_x,start_y,width,height):
        """
        左侧排图标尺表格中添加文字的函数。自动附加左侧白边宽度。
        """
        start_x += self.margins["left_white"]
        rulerTitle:QtWidgets.QGraphicsSimpleTextItem = self.scene.addSimpleText(text)
        font = QtGui.QFont()
        font.setRawName(textFont.rawName())
        width1 = rulerTitle.boundingRect().width()
        if width1 > width:
            stretch = 100*width//width1
            font.setStretch(stretch)
        rulerTitle.setFont(font)
        rulerTitle.setBrush(QtGui.QBrush(textColor))
        rect = rulerTitle.boundingRect()
        rulerTitle.setX(start_x + (width-rect.width())/2)
        rulerTitle.setY(start_y +
                        (height-rect.height())/2)
        return rulerTitle

    def _addStationTableText(self,text,textFont,textColor,start_x,center_y,width):
        """
        左侧排图标尺表格中【每个站】位置的字体。与上一个的区别是设置中心y而不是高度。自动附加左侧白边。
        """
        start_x += self.margins["left_white"]
        rulerTitle: QtWidgets.QGraphicsSimpleTextItem = self.scene.addSimpleText(text)
        font = QtGui.QFont()
        font.setRawName(textFont.rawName())
        rulerWidth1 = rulerTitle.boundingRect().width()
        if rulerWidth1 > width:
            stretch = int(100 * width / rulerWidth1)
            font.setStretch(stretch)
        rulerTitle.setFont(font)
        rulerTitle.setBrush(QtGui.QBrush(textColor))
        rulerRect = rulerTitle.boundingRect()
        rulerTitle.setX(start_x + (width - rulerRect.width()) / 2)
        rulerTitle.setY(center_y-rulerRect.height() / 2)
        return rulerTitle

    def _drawSingleHLine(self, textColor, textFont, y, name, pen, width, leftItems, rightItems, dir_,
                         label_start_x):
        """
        """
        textFont.setBold(False)
        name=name.replace('::','*')
        # print(name,dir_)
        # dir_dict = {
        #     0x0: 'N', 0x1: 'D', 0x2: 'U', 0x3: '',
        # }
        # name = dir_dict[dir_] + name

        self.scene.addLine(self.margins["left"], y, width + self.margins["left"], y, pen)
        textItem: QtWidgets.QGraphicsSimpleTextItem = self.scene.addSimpleText(name)
        # textItem.setDefaultTextColor(textColor)
        # textItem.setPen(QtGui.QPen(textColor))
        textItem.setBrush(QtGui.QBrush(textColor))
        textItem.setFont(textFont)
        textItem.setY(y - textItem.boundingRect().height()/2)
        # textItem.setX(self.margins["label_width"] - len(name) * 18.2 - 5)
        textWidth = textItem.boundingRect().width()
        font = QtGui.QFont()
        font.setBold(textFont.bold())
        font.setRawName(textFont.rawName())
        label_width = self.margins["label_width"] - 5  #左侧稍微多留出一点点边
        if textWidth > label_width:
            # 超大的字
            stretch = int(100*label_width / textWidth+0.5)
            font.setStretch(stretch)
            textItem.setFont(font)
        textWidth = textItem.boundingRect().width()
        cnt = len(name)
        if textWidth < label_width and cnt>1:
            # 两端对齐
            font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing,(label_width-textWidth)/(cnt-1))
            textItem.setFont(font)

        textItem.setX(label_start_x+self.margins["left_white"]+5)
        leftItems.append(textItem)

        # 右侧
        textItem = self.scene.addSimpleText(name)
        textItem.setBrush(QtGui.QBrush(textColor))
        textItem.setFont(textFont)
        textItem.setY(y - textItem.boundingRect().height()/2)
        textItem.setX(self.scene.width() - self.margins["label_width"]-self.margins["right_white"])
        textWidth = textItem.boundingRect().width()
        label_width = self.margins["label_width"]
        font = QtGui.QFont()
        font.setBold(textFont.bold())
        font.setRawName(textFont.rawName())
        if textWidth > self.margins["label_width"]:
            # 超大的字
            stretch = int(100 * self.margins["label_width"] / textWidth + 0.5)
            font.setStretch(stretch)
            textItem.setFont(font)
        textWidth = textItem.boundingRect().width()
        cnt = len(name)
        if textWidth < label_width and cnt > 1:
            # 两端对齐
            font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, (label_width - textWidth) / (cnt - 1))
            textItem.setFont(font)

        rightItems.append(textItem)

    def _setVLines(self, UIDict: dict, gridColor: QtGui.QColor, height: int, width: int, hour_count: int):
        gap = UIDict["minutes_per_vertical_line"]
        line_count = gap * hour_count
        pen_hour = QtGui.QPen(gridColor, UIDict.setdefault("bold_grid_width",2.5))
        pen_half = QtGui.QPen(gridColor, UIDict.setdefault("default_grid_width",1), Qt.DashLine)
        pen_other = QtGui.QPen(gridColor, UIDict["default_grid_width"])

        timeItems = []  # 顶上的时间坐标行
        downItems = []
        rectItem: QtWidgets.QGraphicsRectItem = self.scene.addRect(self.margins["left"] - 15, 0,
                                                                   width + self.margins["left"] + 30, 35)
        lineItem = self.scene.addLine(self.margins["left"] - 15, 35, width + self.margins["left"] + 15, 35)
        lineItem.setPen(QtGui.QPen(gridColor, 2))
        rectItem.setPen(QtGui.QPen(Qt.transparent))
        # brush = QtGui.QBrush(Qt.white)
        color = QtGui.QColor(Qt.white)
        color.setAlpha(200)  # 0~255,255全不透明
        rectItem.setBrush(QtGui.QBrush(color))

        timeItems.append(rectItem)
        timeItems.append(lineItem)

        rectItem: QtWidgets.QGraphicsRectItem = \
            self.scene.addRect(self.margins["left"] - 15, self.scene.height() - 35,
                               width + self.margins["left"] + 30, 35)
        lineItem = self.scene.addLine(self.margins["left"] - 15, self.scene.height() - 35,
                                      width + self.margins["left"] + 15, self.scene.height() - 35)
        lineItem.setPen(QtGui.QPen(gridColor, 2))
        rectItem.setPen(QtGui.QPen(Qt.transparent))
        # brush = QtGui.QBrush(Qt.white)
        color = QtGui.QColor(Qt.white)
        color.setAlpha(200)  # 0~255,255全不透明
        rectItem.setBrush(QtGui.QBrush(color))
        downItems.append(rectItem)
        downItems.append(lineItem)

        # 注意，第1和最后不用画
        font = QtGui.QFont()
        font.setPixelSize(25)
        font.setBold(True)

        for i in range(hour_count + 1):

            x = self.margins["left"] + i * 3600 / UIDict["seconds_per_pix"]
            hour = (i + UIDict["start_hour"]) % 24

            textItem1: QtWidgets.QGraphicsSimpleTextItem = self.scene.addSimpleText(str(hour))
            textItem2: QtWidgets.QGraphicsSimpleTextItem = self.scene.addSimpleText(str(hour))
            textItem1.setFont(font)
            textItem1.setX(x - textItem1.boundingRect().width()/2)
            textItem1.setBrush(QtGui.QBrush(gridColor))
            # textItem1.setDefaultTextColor(gridColor)
            timeItems.append(textItem1)

            # 下时间坐标
            textItem2.setFont(font)
            textItem2.setX(x - textItem2.boundingRect().width()/2)
            textItem2.setY(self.scene.height() - 30)
            textItem2.setBrush(QtGui.QBrush(gridColor))
            # textItem2.setDefaultTextColor(gridColor)
            downItems.append(textItem2)

            if i == hour_count:
                break

            # 画小时线，第一个不用画
            if i != 0:
                self.scene.addLine(x, self.margins["up"], x, self.margins["up"] + height, pen_hour)

            for j in range(1, int(60 / gap)):
                x += gap * 60 / UIDict["seconds_per_pix"]
                if j * gap == 30:
                    self.scene.addLine(x, self.margins["up"], x, self.margins["up"] + height, pen_half)
                else:
                    self.scene.addLine(x, self.margins["up"], x, self.margins["up"] + height, pen_other)

        group1 = self.scene.createItemGroup(timeItems)
        group1.setZValue(15)
        self.marginItemGroups["up"] = group1

        group2 = self.scene.createItemGroup(downItems)
        group2.setZValue(15)
        # print("y is: ",group2.y())
        self.marginItemGroups["down"] = group2

    def addTrainLine(self, train):
        """
        """
        if not train.isShow():
            # 若设置为不显示，忽略此命令
            # print("addTrainLine:not show train",train.fullCheci())
            return
        try:
            self.graph.UIConfigData()["showFullCheci"]
        except KeyError:
            self.graph.UIConfigData()["showFullCheci"] = False

        if train.autoItem():
            start = 0
            status = None
            train.clearItemInfo()
            while status != TrainItem.End:
                # 扫描到最后总是会返回end
                item = TrainItem(train,self.graph,self,
                                 validWidth=self.graph.UIConfigData().setdefault('valid_width',3),
                                 showFullCheci=self.graph.UIConfigData()['showFullCheci'],
                                 markMode=self.graph.UIConfigData()['show_time_mark']
                                 )
                if status != TrainItem.Reversed:
                    showStart = True
                else:
                    showStart = False
                end, status = item.setLine(start, showStartLabel=showStart)
                if status != TrainItem.Invalid:
                    if item.station_count >= 2:
                        # 暂不确定是否要完全封杀station_count<2的车次
                        # 2020.09.01注：这个封杀好像没起到作用
                        train.addItem(item)
                        # 铺画完毕后，item.start/endStation参数被补齐。
                        if item.down is not None:
                            # 只要铺画了有效的运行线，down就不可能是None
                            dct = {
                                "start":item.startStation,
                                "end":item.endStation,
                                "down":item.down,
                                "show_start_label":showStart,
                                "show_end_label":False if status == TrainItem.Reversed else True,
                            }
                            train.addItemInfoDict(dct)
                            self.scene.addItem(item)
                            item.setZValue(5)
                    else:
                        # 如果下一段的运行线不存在，而上一段的被以Reversed方向终止，则需要补上终止标签。
                        # 2019.11.18添加，解决杭深线D6315问题。
                        lastItemDict = train.lastItemInfo()
                        if status == TrainItem.Pass and lastItemDict is not None\
                                and not lastItemDict['show_end_label']:
                            print(f"返回添加上一级标签：车次{train.fullCheci()}")
                            lastItemDict['show_end_label'] = True
                            newItem = TrainItem(train,self.graph,self,lastItemDict['start'],lastItemDict['end'],
                                        lastItemDict['down'],
                                        validWidth=self.graph.UIConfigData().setdefault('valid_width', 3),
                                        showFullCheci=self.graph.UIConfigData()['showFullCheci'],
                                        markMode=self.graph.UIConfigData()['show_time_mark']
                                    )
                            newItem.setLine(showStartLabel=lastItemDict['show_start_label'],
                                            showEndLabel=True)
                            oldItem = train.takeLastItem()
                            self.scene.removeItem(oldItem)
                            self.scene.addItem(newItem)
                            train.addItem(newItem)
                            newItem.setZValue(5)

                start = end

        else:  # 手动模式，按照要求铺画
            for dct in train.itemInfo():
                start = 0
                item = TrainItem(train,self.graph,self,
                                 dct['start'],dct['end'],dct['down'],
                                 self.graph.UIConfigData()['valid_width'],
                                 self.graph.UIConfigData()['showFullCheci'],
                                 self.graph.UIConfigData()['show_time_mark']
                                 )
                end,status = item.setLine(start,showStartLabel=dct['show_start_label'],
                                          showEndLabel=dct['show_end_label'])
                if status != TrainItem.Invalid:
                    self.scene.addItem(item)
                    train.addItem(item)
                    item.setZValue(5)
                    dct['start'] = item.startStation
                    dct['end'] = item.endStation
                else:
                    train.removeItemInfo(dct)
                start = end
        # item.setLine()  # 重复调用，init中已经调用过一次了，故删去。

    def delTrainLine(self, train):
        if train is self.selectedTrain:
            self._line_un_selected()

        # item = train.getItem()
        for item in train.items():
            # 这里需要遍历检查items，是因为防止ctrl+R操作中的train未添加进来，尝试删除引发错误。暂未找到更合适方案。
            # if item in self.scene.items():
            # if item.scene() is self.scene:
            self.scene.removeItem(item)
        train.clearItems()

    def repaintTrainLine(self, train):
        """
        重新铺画，先删除再铺画，但保留选择。2019.07.04新增。
        """
        isSelected = (train==self.selectedTrain)
        self.delTrainLine(train)
        self.addTrainLine(train)
        if isSelected:
            self._line_selected(train.firstItem(),emit=False)

    def _resetTimeAxis(self):
        point = QtCore.QPoint(0, 0)
        scenepoint = self.mapToScene(point)
        self.marginItemGroups["up"].setY(scenepoint.y())
        try:
            self.nowItem.setY(scenepoint.y())
        except RuntimeError:
            # 可能报错：Wrapped C++ class have been deleted.
            # 怀疑是打开新运行图时nowItem已经被析构，然后由引起resize或者类似问题。
            print("Wrapped C++ class NowItem has been deleted.")
            pass

        point = QtCore.QPoint(0, self.height())
        scenepoint = self.mapToScene(point)
        self.marginItemGroups["down"].setY(scenepoint.y() - self.scene.height() - 27)

    def _resetDistanceAxis(self):
        point = QtCore.QPoint(0, 0)
        scenepoint = self.mapToScene(point)
        self.marginItemGroups["left"].setX(scenepoint.x())
        try:
            self.nowItem.setX(scenepoint.x())
        except RuntimeError:
            pass

        point = QtCore.QPoint(self.width(), 0)
        scenepoint = self.mapToScene(point)
        self.marginItemGroups["right"].setX(scenepoint.x() - self.scene.width() - 20)

    def stationPosCalculate(self, zm: str, sj: datetime)->QtCore.QPoint:
        """
        计算时间、车站对应的点。
        保证数据是datetime对象而不是str。
        use attribute status to show the status of the point.
        -1：不在显示（时间）范围内
        0：合法
        对合法但坐标越界的做处理了
        """
        # calculate start hour
        start_time = datetime(1900, 1, 1, hour=self.graph.UIConfigData()["start_hour"])
        dt = sj - start_time

        dct_line = self.graph.stationByDict(zm)
        if dct_line is None:
            return None  # 线路上不存在这个站

        y = dct_line.get('y_value',-1)
        if self.graph.UIConfigData()["ordinate"] is not None:
            # if self.graph.stationExisted(zm):# 不必判断！
            if dct_line.get('direction',Line.BothVia) == 0x0:
                # 说明：按标尺排图时，若本线该站是“不通过”状态。
                y = -1

        if y is None or y == -1:
            return None

        # width = self.scene.width() - self.margins["left"] - self.margins["right"]
        x = dt.seconds / self.graph.UIConfigData()["seconds_per_pix"] + self.margins["left"]

        point = QtCore.QPoint(int(x), int(y))
        if sj.hour in self.valid_hours or (sj.minute == 0 and sj.hour - 1 in self.valid_hours):
            point.inRange = True
        else:
            point.inRange = False

        return point

    def _line_selected(self, item: QtWidgets.QGraphicsPathItem, ensure_visible=False,emit=True):
        # print(item)
        if item is None:
            return
        if not isinstance(item, TrainItem):
            return
        train = item.train
        if train is self.selectedTrain:
            return
        for item in train.items():
            item.select()

        if ensure_visible:
            self.ensureVisible(item)

        self.selectedTrain = train
        if emit:
            self.focusChanged.emit(self.selectedTrain)
        self.nowItem.setText(train.fullCheci())

    def _line_un_selected(self):
        train = self.selectedTrain
        if train is None:
            return
        for item in train.items():
            item.unSelect()

        self.nowItem.setText(' ')
        self.selectedTrain = None

    def mousePressEvent(self, QMouseEvent:QtGui.QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            pos = self.mapToScene(QMouseEvent.pos())
            # print("mousePressEvent",pos)
            # self.scene.addRect(pos.x()-1,pos.y()-1,2,2)
            if self.selectedTrain is not None:
                self._line_un_selected()

            item: QtWidgets.QGraphicsItem = self.scene.itemAt(pos, self.transform())
            if item is None:
                return
            # print(item)
            while item.parentItem():
                item = item.parentItem()
            if isinstance(item, TrainItem):
                self._line_selected(item, ensure_visible=False)
        elif QMouseEvent.button() == Qt.RightButton:
            self.menu.popup(QMouseEvent.globalPos())
        super(GraphicsWidget, self).mousePressEvent(QMouseEvent)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        pos = self.mapToScene(event.pos())
        # print("mousePressEvent",pos)
        # self.scene.addRect(pos.x()-1,pos.y()-1,2,2)
        if self.selectedTrain is not None:
            self._line_un_selected()

        item: QtWidgets.QGraphicsItem = self.scene.itemAt(pos, self.transform())
        if item is None:
            return
        # print(item)
        while item.parentItem():
            item = item.parentItem()
        if isinstance(item, TrainItem):
            self._line_selected(item, ensure_visible=False)
        else:
            return
        self.lineDoubleClicked.emit()

    def posTrain(self,pos)->Train:
        """
        返回某点处的运行线对应列车对象
        """
        pos = self.mapToScene(pos)
        item: QtWidgets.QGraphicsItem = self.scene.itemAt(pos, self.transform())
        if item is None:
            return None
        while item.parentItem():
            item = item.parentItem()
        if item is None:
            return None
        if isinstance(item, TrainItem):
            return item.train

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        """
        若鼠标停留在当前选中运行线上，显示有关信息。
        """
        train=self.posTrain(event.pos())
        pos = self.mapToScene(event.pos())
        if train is None or train is not self.selectedTrain:
            self.setToolTip('')
            return
        dct_pre,dct_lat = train.yToStationInterval(pos.y())
        if dct_pre is None:
            self.setToolTip('')
            return
        elif dct_lat is None:
            # 站内事件
            text = f"{train.fullCheci()}次({train.sfz}->{train.zdz})在{dct_pre['zhanming']}车站 "
            if train.stationStopped(dct_pre):
                text += f"{dct_pre['ddsj'].strftime('%H:%M:%S')}/{dct_pre['cfsj'].strftime('%H:%M:%S')}\n"
                dt:timedelta = dct_pre['cfsj'] - dct_pre['ddsj']
                sec = dt.seconds
                if sec < 0:
                    sec += 24*3600
                sec_str = f"{sec%60:02d}秒"
                text += f"停车{int(sec/60)}分{sec_str if sec%60 else ''}"
            else:
                text += f"{dct_pre['ddsj'].strftime('%H:%M:%S')}/..."
            self.setToolTip(text)
            self.setStatusTip(text)
        else:
            # 区间事件. 效率考虑，直接弄成作差。
            dt1:timedelta = dct_lat['ddsj'] - dct_pre['cfsj']
            dt2:timedelta = dct_pre['ddsj'] - dct_lat['cfsj']
            sec1 = dt1.seconds
            sec2 = dt2.seconds
            if sec1 < 0:
                sec1 += 3600*24
            if sec2 < 0:
                sec2 += 3600*24
            if sec1 < sec2:
                pre = dct_pre;lat=dct_lat;sec=sec1
            else:
                pre = dct_lat;lat=dct_pre;sec=sec2
            text = f"{train.fullCheci()}次({train.sfz}->{train.zdz})在{pre['zhanming']}-{lat['zhanming']}区间 "
            text += f"{pre['cfsj'].strftime('%H:%M:%S')}-{lat['ddsj'].strftime('%H:%M:%S')} "
            sec_str = f"{sec%60:02d}秒"
            text += f"区间运行{int(sec/60)}分{sec_str if sec%60 else ''}\n"
            try:
                mile = self.graph.gapBetween(pre['zhanming'],lat['zhanming'])
            except:
                text += "区间里程数据错误，可使用ctrl+W查看区间均速等数据"
            else:
                try:
                    speed = mile*1000/sec*3.6
                except ZeroDivisionError:
                    speed_str = 'NA'
                else:
                    speed_str = f"{speed:.2f} km/h"
                text += f"区间里程{mile:.2f} km，技术速度{speed_str}"
            self.setToolTip(text)
            self.setStatusTip(text)
        super(GraphicsWidget, self).mouseMoveEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)
        self._resetTimeAxis()
        self._resetDistanceAxis()

    def save(self,filename, mark:str):
        """
        导出为PNG。
        """
        self.marginItemGroups["left"].setX(0)
        self.marginItemGroups["right"].setX(0)
        self.marginItemGroups["up"].setY(0)
        self.marginItemGroups["down"].setY(0)
        self.nowItem.setX(0)
        self.nowItem.setY(0)

        # image = QtGui.QImage(self.scene.width(),self.scene.height(),QtGui.QImage.Format_ARGB32)
        # image = QtGui.QImage(self.scene.sceneRect().toSize,QtGui.QImage.Format_ARGB32)
        note_apdx = 80
        image = QtGui.QImage(self.scene.width(), self.scene.height() + 100 + note_apdx, QtGui.QImage.Format_ARGB32)
        image.fill(Qt.white)

        painter = QtGui.QPainter()
        painter.begin(image)
        painter.setPen(QtGui.QPen(QtGui.QColor(self.graph.UIConfigData()["text_color"])))
        font = QtGui.QFont()
        font.setPixelSize(50)
        font.setBold(True)
        # font.setUnderline(True)
        painter.setFont(font)
        painter.drawText(self.margins["left"], 80, "{}{}-{}间列车运行图".format(self.graph.lineName(),
                                                                                self.graph.firstStation(),
                                                                                self.graph.lastStation(),
                                                                               ),
                         )
        font.setPixelSize(20)
        font.setBold(False)
        font.setUnderline(False)
        painter.setFont(font)
        if self.graph.markdown():
            nnn = '\n'
            painter.drawText(self.margins["left"], self.scene.height() + 100 + 40,
                             f"备注：{self.graph.markdown().replace(nnn,' ')}"
                             )
        painter.drawText(self.scene.width()-400,self.scene.height()+100+40,mark)

        painter.setRenderHint(painter.Antialiasing, True)
        self.scene.render(painter, target=QtCore.QRectF(0, 100, self.scene.width(), self.scene.height()))
        # if not flag:
        #    print("make failed",flag)
        flag = image.save(filename)
        painter.end()
        print(flag)
        print("save ok")
        self._resetDistanceAxis()
        self._resetTimeAxis()

    def savePdf(self,filename:str,mark:str)->bool:
        self.marginItemGroups["left"].setX(0)
        self.marginItemGroups["right"].setX(0)
        self.marginItemGroups["up"].setY(0)
        self.marginItemGroups["down"].setY(0)
        self.nowItem.setX(0)
        self.nowItem.setY(0)

        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
        # printer.setResolution(300)
        printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        note_apdx = 80
        size = QtCore.QSize(self.scene.width(),self.scene.height()+100+note_apdx)
        pageSize = QtGui.QPageSize(size)
        printer.setPageSize(pageSize)

        # printer = QtGui.QPdfWriter(filename)
        # size = QtCore.QSize(self.scene.width(),self.scene.height()+200)
        # pageSize = QtGui.QPageSize(size)
        # pageSize = QtGui.QPagedPaintDevice.PageSize()
        # printer.setPageSize(pageSize)

        painter = QtGui.QPainter()
        painter.begin(printer)
        if not painter.isActive():
            QtWidgets.QMessageBox.warning(self,'错误','保存pdf失败，可能是文件占用。')
            return False
        painter.scale(printer.width()/self.scene.width(),printer.width()/self.scene.width())
        painter.setPen(QtGui.QPen(QtGui.QColor(self.graph.UIConfigData()["text_color"])))
        font = QtGui.QFont()
        font.setPixelSize(50)
        font.setBold(False)
        # font.setUnderline(True)
        painter.setFont(font)
        painter.drawText(self.margins["left"], 80, "{}{}-{}间列车运行图".format(self.graph.lineName(),
                                                                                self.graph.firstStation(),
                                                                                self.graph.lastStation(),
                                                                                ),
                         )
        font.setPixelSize(20)
        font.setBold(False)
        font.setUnderline(False)
        painter.setFont(font)
        if self.graph.markdown():
            nnn = '\n'
            painter.drawText(self.margins["left"], self.scene.height() + 100 + 40,
                             f"备注：{self.graph.markdown().replace(nnn,' ')}"
                             )
        painter.drawText(self.scene.width() - 400, self.scene.height() + 100 + 40, mark)
        self.scene.render(painter, target=QtCore.QRectF(0, 100, self.scene.width(), self.scene.height()))
        painter.end()
        self._resetDistanceAxis()
        self._resetTimeAxis()
        return True

    def _stationFromYValue(self, event_y: int):
        """
        返回：区间起点，区间终点，事件里程
        """
        last_station, last_y = "", 0
        last_mile = 0
        for name, mile, y in self.graph.stationMileYValues():
            if y is None:
                continue
            if abs(y - event_y) < 2:  # 2019.02.23  1改为2
                return name, None, mile  # 在本站内发生的事件
            if y > event_y:
                try:
                    event_mile = last_mile + (mile - last_mile) * (event_y - last_y) / (y - last_y)
                except ZeroDivisionError:
                    return last_station, name, -1
                else:
                    return last_station, name, event_mile
            last_station, last_y, last_mile = name, y, mile

        return None, None, -1

    def _timeFromXValue(self, x):
        """
        用横坐标值反推时刻数据
        """
        UIDict = self.graph.UIConfigData()
        start_time = datetime(1900, 1, 1, hour=UIDict["start_hour"])
        dt = timedelta(seconds=(x - self.margins["left"]) * UIDict["seconds_per_pix"])
        return start_time + dt

    def listTrainEvent(self):
        """
        获取已选中的车次在本线的事件表。
        :return: list<Dict>
        dict: {
            "event_type": enum:TrainEventType,
            "time": datetime.datetime,
            "former_station": str,
            "later_station": str,
            "another": str //客体车次。不需要的用None.
        """
        print("listTrainEvent")
        if self.selectedTrain is None:
            return []
        # item:QtWidgets.QGraphicsPathItem
        self.selectedTrain: Train
        events = []
        # 图定到开时间
        train = self.selectedTrain
        for dct in train.stationDicts():
            name, ddsj, cfsj = dct['zhanming'], dct['ddsj'], dct['cfsj']
            if not self.graph.stationInLine(name):
                continue
            if ddsj == cfsj:
                typ = TrainEventType.pass_settled
                if train.isSfz(name):
                    typ = TrainEventType.origination
                elif train.isZdz(name):
                    typ = TrainEventType.destination
                dict = {
                    "type": typ,
                    "time": ddsj,
                    "former_station": name,
                    "later_station": None,
                    "another": None,
                    "mile": self.graph.stationMile(name),
                    "note": dct.get("note", ''),
                }
                events.append(dict)

            else:
                dict1 = {
                    "type": TrainEventType.arrive,
                    "time": ddsj,
                    "former_station": name,
                    "later_station": None,
                    "another": None,
                    "mile": self.graph.stationMile(name)
                }
                dict2 = {
                    "type": TrainEventType.leave,
                    "time": cfsj,
                    "former_station": name,
                    "later_station": None,
                    "another": None,
                    "mile": self.graph.stationMile(name),
                }
                events.append(dict1)
                events.append(dict2)
        # collidItems = self.selectedTrain.getItem().collidingItems()

        # 2.0版本调整。逻辑不确定。
        for item in self.selectedTrain.items():
            collidItems = []
            collidItems.extend(item.collidingItems())
            # print("collid calculate ok")
            selfItem = item
            # 多车次事件
            for item in collidItems:
                # 2018.12.14：封装item后，collid会同时包含TrainItem和pathItem，此时不可以取parent，否则重复计算
                # while item.parentItem():
                #     item = item.parentItem()
                if item is self.selectedTrain.item:
                    continue
                if isinstance(item, TrainItem):
                    train = item.train
                    if (train is None):
                        # 表明是标签对象，无意义
                        continue
                    # print(self.selectedTrain.fullCheci(), train.fullCheci())
                    events += self._trains_collid(selfItem, item, self.selectedTrain, train)
                elif isinstance(item, QtWidgets.QGraphicsLineItem):
                    # events += self._line_collid(selfItem,item,self.selectedTrain)
                    # TODO 推算时刻
                    pass

        # 事件排序
        self._sort_event(events)

        return events

    def _sort_event(self, event_source):
        """
        按列车时刻表的【车站】出现顺序排序。
        TODO 这个排序可能不大靠谱
        """
        # # 先按时间排序
        # event_source.sort(key=lambda x: x["time"])
        # # 按里程排序
        # train: Train = self.selectedTrain
        # event_source.sort(key=lambda x: x["mile"])
        # 2019.02.23修改：按里程优先，时间次之的顺序排序。
        train:Train = self.selectedTrain
        if train.firstDown():
            event_source.sort(key=lambda x:(x["mile"],x["time"]))
        else:
            event_source.sort(key=lambda x: (-x["mile"], x["time"]))

    def _line_collid(self, pathItem: QtWidgets.QGraphicsPathItem, lineItem: QtWidgets.QGraphicsLineItem, train):
        # TODO 推算时刻
        # print(lineItem.line())
        # line:QtCore.QLineF=lineItem.line()
        return []

    def _trains_collid(self, item1: TrainItem, item2: TrainItem,
                       train1: Train, train2: Train):
        path1: QtGui.QPainterPath = item1.pathItem.path()
        path2 = item2.pathItem.path()
        inter: QtGui.QPainterPath = path1.intersected(path2)

        elements = []
        # print(train1,train2)
        for i in range(inter.elementCount()):
            ele = inter.elementAt(i)
            # print(ele,ele.type)
            if ele.type == 0:
                tm = self._timeFromXValue(ele.x)
                former, later, mile = self._stationFromYValue(ele.y)
                dict = {
                    "type": self._multi_train_event_type(train1, train2, former, later),
                    "time": tm,
                    "former_station": former,
                    "later_station": later,
                    "another": train2.fullCheci(),
                    "mile": float(mile),
                }
                elements.append(dict)
        return elements

    def _multi_train_event_type(self, train1: Train, train2: Train, former: str, later: str):
        """
        判断两车次事件是交会、越行还是避让。
        交会 iff 上下行不一致
        站内：停车的一方为待避，另一方为越行。
        站外：比较两站时刻。用时短的一方是越行。
        """
        if train1.stationDown(former,self.graph) != train2.stationDown(former,self.graph):
            return TrainEventType.meet

        if later is None:
            # 站内事件
            try:
                ddsj, cfsj = train1.stationTime(former)
            except:
                # 如果没有这个车站，就直接认为是通过，则应当是越行
                print("No station in timetable: ", train1.fullCheci(), former, train2.fullCheci())
                return TrainEventType.overTaking
            else:
                if ddsj != cfsj:
                    return TrainEventType.avoid
                else:
                    return TrainEventType.overTaking
        else:
            dt1 = train1.gapBetweenStation(former, later, self.graph)
            dt2 = train2.gapBetweenStation(former, later, self.graph)
            if dt1 < dt2:
                return TrainEventType.overTaking
            else:
                return TrainEventType.avoid
        return TrainEventType.unknown

    def on_show_forbid_changed(self, forbid:Forbid,checked, down):
        if checked:
            self.show_forbid(forbid,down)
        else:
            self._remove_forbid(forbid,down)

    def show_forbid(self, forbid_data:Forbid, down, remove=True):
        print("show forbid",forbid_data)
        if remove:
            self._remove_forbid(forbid_data,down)
        pen = QtGui.QPen(Qt.transparent)
        isService = isinstance(forbid_data,ServiceForbid)
        if isService:
            color = QtGui.QColor('#555555')
        else:
            color = QtGui.QColor('#5555FF')
        color.setAlpha(200)
        brush = QtGui.QBrush(color)
        if not forbid_data.different():
            brush.setStyle(Qt.DiagCrossPattern)
        elif down:
            brush.setStyle(Qt.FDiagPattern)
        else:
            brush.setStyle(Qt.BDiagPattern)
        brush2=None
        if not isService:
            color=QtGui.QColor('#AAAAAA')
            color.setAlpha(80)
            brush2=QtGui.QBrush(color)
        for node in forbid_data.nodes(down):
            items = self._add_forbid_rect(node, pen, brush)
            if not isService:
                items.extend(self._add_forbid_rect(node,pen,brush2))
            for item in items:
                forbid_data.addItem(down, item)

    def _add_forbid_rect(self, node, pen, brush):
        start_point = self.stationPosCalculate(node["fazhan"], node["begin"])
        if start_point is None:
            # 正常现象。当显示的时间段不包含天窗时会出问题。
            # print("GW::add_forbid_rect: start_point is None!",node.get('fazhan',''),node.get('daozhan',''))
            return []
        start_x, start_y = start_point.x(), start_point.y()
        end_point = self.stationPosCalculate(node["daozhan"], node["end"])
        if end_point is None:
            # print("GW::add_forbid_rect: end_point is None!",node.get('fazhan',''),node.get('daozhan',''))
            return []
        end_x, end_y = end_point.x(), end_point.y()
        if start_y > end_y:
            # 如果上下反了，直接交换，这个无所谓
            start_y, end_y = end_y, start_y
        if start_x == end_x:
            # 天窗时间为0，不用画
            return []
        if start_x < end_x:
            # 不跨日天窗，正常画
            rectItem: QtWidgets.QGraphicsRectItem = self.scene.addRect(start_x, start_y, end_x - start_x,
                                                                       end_y - start_y)
            rectItem.setPen(pen)
            rectItem.setBrush(brush)
            rectItem.setZValue(1)
            return [rectItem,]
        else:
            # 跨日
            left_x = self.margins["left"]
            right_x = self.scene.width() - self.margins["right"]
            rectItem1 = self.scene.addRect(start_x, start_y, right_x - start_x, end_y - start_y)
            rectItem1.setPen(pen)
            rectItem1.setBrush(brush)
            rectItem2 = self.scene.addRect(left_x, start_y, end_x - left_x, end_y - start_y)
            rectItem2.setPen(pen)
            rectItem2.setBrush(brush)
            rectItem1.setZValue(1)
            rectItem2.setZValue(1)
            return [rectItem1, rectItem2,]

    def _remove_forbid(self,forbid, down):
        for item in forbid.items(down):
            if item in self.scene.items():  # 临时使用这种方法避免出错
                self.scene.removeItem(item)
        forbid.clearItemList(down)

    def setTrainShow(self,train:Train,show:bool=None):
        """
        涵盖各种情况的设置是否显示问题，包含数据变更和铺画调整。
        凡修改是否显示运行线的问题只需要调用这个函数。2019.02.05新增。
        """
        if show is None:
            show = train.isShow()
        else:
            train.setIsShow(show, affect_item=False)
        if show:
            if not train.items():
                self.addTrainLine(train)
            else:
                for item in train.items():
                    item.setVisible(True)
        else:
            for item in train.items():
                item.setVisible(False)



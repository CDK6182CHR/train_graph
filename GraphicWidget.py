"""
时间使用：datetime.datetime对象
copyright (c) mxy 2018
"""
import cgitb
import traceback

cgitb.enable(format='text')

import sys
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from graph import Graph, config_file
from train import Train
from datetime import timedelta, datetime
from Timetable_new.utility import isKeche
from ruler import Ruler
from line import Line
from enum import Enum
from forbid import Forbid
from trainItem import TrainItem


class TrainEventType(Enum):
    meet = 0  # 会车
    overTaking = 1  # 越行
    avoid = 2  # 待避
    arrive = 3  # 到站
    leave = 4  # 出发
    pass_settled = 5
    pass_calculated = 6
    unknown = -1


class GraphicsWidget(QtWidgets.QGraphicsView):
    focusChanged = QtCore.pyqtSignal(Train)  # 定义信号，选中车次变化
    rulerChanged = QtCore.pyqtSignal(Ruler)
    showNewStatus = QtCore.pyqtSignal([str], [str, int])  # 显示状态栏信息

    def __init__(self, parent=None):
        super(GraphicsWidget, self).__init__(parent)

        self.setWindowTitle("GraphicsViewsTestWindow")
        self.setWindowIcon(QtGui.QIcon('icon.ico'))
        self.setGeometry(200, 200, 1200, 600)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.graph = Graph()

        self.sysConfig = self.readSysConfig()
        self.margins = {
            "left_white":15, # 左侧白边，不能有任何占用的区域
            "right_white":10,
            "left": 325,
            "up": 90,
            "down": 90,
            "right": 170,
            "label_width": 100,
            "mile_label_width":50,
            "ruler_label_width":100,
        }
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

        if True:
            graphUse = 0  # 0 for last, 1 for default, 2 for empty
            if graphUse == 0 and self.sysConfig["last_file"] is None:
                graphUse = 1

            if graphUse == 0:
                print("open last file")
                try:
                    self.graph.loadGraph(self.sysConfig["last_file"])
                    self.setGraph(self.graph)
                except:
                    graphUse = 1

            if graphUse == 1:
                print("open default file")
                try:
                    self.graph.loadGraph(self.sysConfig["default_file"])
                    self.setGraph(self.graph)
                except:
                    graphUse = 2
                    self.showNewStatus.emit("默认运行图错误，使用空运行图")

            if graphUse == 2:
                print("open empty file")
                self.graph = Graph()
                self.setGraph(self.graph)

        self.setRenderHint(QtGui.QPainter.Antialiasing, True)

        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.selectedTrain = None
        self.tempRect = None
        self.tempRect2 = None

        self.setGraph(self.graph, paint=False)

    def readSysConfig(self):
        fp = open(config_file, encoding='utf-8', errors='ignore')
        data = json.load(fp)
        return data

    def saveSysConfig(self, Copy=False):
        if Copy:
            from copy import copy
            self.sysConfig = copy(self.graph.UIConfigData())
            if self.sysConfig["ordinate"] is not None:
                self.sysConfig["ordinate"] = self.sysConfig["ordinate"].name()
        fp = open(config_file, 'w', encoding='utf-8', errors='ignore')
        json.dump(self.sysConfig, fp, ensure_ascii=False)
        fp.close()

    def setGraph(self, graph: Graph, paint=True):
        self.selectedTrain = None
        self.graph = graph
        if paint:
            self.paintGraph()

    def paintGraph(self, throw_error=False):
        """
        throw_error:出现标尺排图错误时是否继续向外抛出。
        在标尺编辑面板调整重新排图是置为True，显示报错信息。
        """
        self.scene.clear()
        self.selectedTrain = None
        if self.graph.isEmpty():
            return
        self.showNewStatus.emit("正在铺画运行图：{}".format(self.graph.lineName()))
        try:
            self.initSecne()
        except Exception as e:
            if throw_error:
                raise e
            else:
                # 静默处理错误
                traceback.print_exc()  #debug only
                self.graph.setOrdinateRuler(None)
                self.initSecne()

        self.showNewStatus.emit("运行图：{}铺画完毕".format(self.graph.lineName()))

    def initSecne(self):
        # self.setStyleSheet("padding:0px;border:0px")
        if self.graph is None:
            return

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
            progressDialog.setCancelButton(None)
            progressDialog.setWindowTitle('正在铺画')
        i = 0
        for train in self.graph.trains():
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
            #     train.setItem(None)

            if self.parent():
                progressDialog.setValue(i)
                progressDialog.setLabelText(f'正在铺画运行线({i}/{self.graph.trainCount()}): {train.fullCheci()}')
                if i % 10 == 0:
                    # 平衡更新界面和整体速度。仅在整10才更新界面。
                    QtCore.QCoreApplication.processEvents()

        forbid = self.graph.line.forbid
        if forbid.downShow():
            self.show_forbid(True)
        if forbid.upShow():
            self.show_forbid(False)

        self.verticalScrollBar().valueChanged.connect(self._resetTimeAxis)
        self.horizontalScrollBar().valueChanged.connect(self._resetDistanceAxis)

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

        defaultPen = QtGui.QPen(gridColor, 1)
        boldPen = QtGui.QPen(gridColor, 2.5)
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
                    raise Exception("不完整标尺排图错误:", "区间：{}-{}标尺无数据".format(last_station, name))
                    y += (mile - last_mile) * UIDict["pixes_per_km"]
                    # labeItem = self.scene.addText("{}km".format(mile-last_mile))
                    # labeItem.setY((y + last_y) / 2 - 13)
                    self.graph.setStationYValue(name, y)
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
        group1.setZValue(4)
        group2 = self.scene.createItemGroup(rightItems)
        group2.setZValue(4)
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
        if rulerTitle.boundingRect().width() > width:
            stretch = int(100*width/rulerTitle.boundingRect().width())
            font.setStretch(stretch)
        rulerTitle.setFont(font)
        rulerTitle.setBrush(QtGui.QBrush(textColor))
        rulerTitle.setX(start_x + (width-rulerTitle.boundingRect().width())/2)
        rulerTitle.setY(start_y +
                        (height-rulerTitle.boundingRect().height())/2)
        return rulerTitle

    def _addStationTableText(self,text,textFont,textColor,start_x,center_y,width):
        """
        左侧排图标尺表格中【每个站】位置的字体。与上一个的区别是设置中心y而不是高度。自动附加左侧白边。
        """
        start_x += self.margins["left_white"]
        rulerTitle: QtWidgets.QGraphicsSimpleTextItem = self.scene.addSimpleText(text)
        font = QtGui.QFont()
        font.setRawName(textFont.rawName())
        if rulerTitle.boundingRect().width() > width:
            stretch = int(100 * width / rulerTitle.boundingRect().width())
            font.setStretch(stretch)
        rulerTitle.setFont(font)
        rulerTitle.setBrush(QtGui.QBrush(textColor))
        rulerTitle.setX(start_x + (width - rulerTitle.boundingRect().width()) / 2)
        rulerTitle.setY(center_y-rulerTitle.boundingRect().height() / 2)
        return rulerTitle

    def _drawSingleHLine(self, textColor, textFont, y, name, pen, width, leftItems, rightItems, dir_,
                         label_start_x):
        """
        """
        textFont.setBold(False)
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
        textItem.setY(y - 13)
        textItem.setX(self.scene.width() - self.margins["label_width"]-self.margins["right_white"])
        textWidth = textItem.boundingRect().width()
        if textWidth > self.margins["label_width"]:
            # 超大的字
            font = QtGui.QFont()
            font.setBold(textFont.bold())
            font.setRawName(textFont.rawName())
            stretch = int(100 * self.margins["label_width"] / textWidth + 0.5)
            font.setStretch(stretch)
            textItem.setFont(font)
        cnt = len(name)
        textWidth = textItem.boundingRect().width()
        if textWidth < self.margins['label_width'] and cnt > 1:
            # 两端对齐
            font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing,(self.margins["label_width"] - textWidth) / (cnt - 1))
            textItem.setFont(font)

        rightItems.append(textItem)

    def _setVLines(self, UIDict: dict, gridColor: QtGui.QColor, height: int, width: int, hour_count: int):
        gap = UIDict["minutes_per_vertical_line"]
        line_count = gap * hour_count
        pen_hour = QtGui.QPen(gridColor, 2.5)
        pen_half = QtGui.QPen(gridColor, 1, Qt.DashLine)
        pen_other = QtGui.QPen(gridColor, 1)

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
        nowItem: QtWidgets.QGraphicsTextItem = self.scene.addText(' ',
                                                                  font=QtGui.QFont('Sim sum', 12))  # 当前车次信息显示在左上角
        timeItems.append(nowItem)
        self.nowItem = nowItem
        nowItem.setDefaultTextColor(QtGui.QColor(UIDict["text_color"]))
        nowItem.setZValue(4)
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
            textItem1.setX(x - 12)
            textItem1.setBrush(QtGui.QBrush(gridColor))
            # textItem1.setDefaultTextColor(gridColor)
            timeItems.append(textItem1)

            # 下时间坐标
            textItem2.setFont(font)
            textItem2.setX(x - 12)
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
        group1.setZValue(2)
        self.marginItemGroups["up"] = group1

        group2 = self.scene.createItemGroup(downItems)
        group2.setZValue(2)
        # print("y is: ",group2.y())
        self.marginItemGroups["down"] = group2

    def addTrainLine(self, train):
        """
        """
        if not train.isShow():
            # 若设置为不显示，忽略此命令
            return
        try:
            self.graph.UIConfigData()["showFullCheci"]
        except KeyError:
            self.graph.UIConfigData()["showFullCheci"] = False
        item = TrainItem(train, self.graph, self,
                         self.graph.UIConfigData()['showFullCheci'])
        # item.setLine()  # 重复调用，init中已经调用过一次了，故删去。
        if train.item is not None:
            self.scene.addItem(item)

    def delTrainLine(self, train):
        if train is self.selectedTrain:
            self._line_un_selected()

        item = train.getItem()

        # 这里需要遍历检查items，是因为防止ctrl+R操作中的train未添加进来，尝试删除引发错误。暂未找到更合适方案。
        if item in self.scene.items():
            self.scene.removeItem(item)
        train.setItem(None)

    def _resetTimeAxis(self):
        point = QtCore.QPoint(0, 0)
        scenepoint = self.mapToScene(point)
        self.marginItemGroups["up"].setY(scenepoint.y())
        # self.nowItem.setY(scenepoint.y())

        point = QtCore.QPoint(0, self.height())
        scenepoint = self.mapToScene(point)
        self.marginItemGroups["down"].setY(scenepoint.y() - self.scene.height() - 27)

    def _resetDistanceAxis(self):
        point = QtCore.QPoint(0, 0)
        scenepoint = self.mapToScene(point)
        self.marginItemGroups["left"].setX(scenepoint.x())
        self.nowItem.setX(scenepoint.x())

        point = QtCore.QPoint(self.width(), 0)
        scenepoint = self.mapToScene(point)
        self.marginItemGroups["right"].setX(scenepoint.x() - self.scene.width() - 20)

    def stationPosCalculate(self, zm: str, sj: datetime):
        """
        计算时间、车站对应的点。
        保证数据是datetime对象而不是str。
        use attribute status to show the status of the point.
        -1：不在显示（时间）范围内
        0：合法
        对合法但坐标越界的做处理了
        """
        x, y = -1, -1
        # calculate start hour
        start_time = datetime(1900, 1, 1, hour=self.graph.UIConfigData()["start_hour"])
        dt = sj - start_time

        y = self.graph.stationYValue(zm)
        if self.graph.UIConfigData()["ordinate"] is not None:
            if self.graph.stationExisted(zm):
                if self.graph.stationDirection(zm) == 0x0:
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

    def _line_selected(self, item: QtWidgets.QGraphicsPathItem, ensure_visible=False):
        # print(item)
        if item is None:
            return
        if not isinstance(item, TrainItem):
            return
        train = item.train
        if train is self.selectedTrain:
            return
        item.select()

        if ensure_visible:
            self.ensureVisible(item)

        self.selectedTrain = train
        self.focusChanged.emit(self.selectedTrain)
        self.nowItem.setPlainText(train.fullCheci())

    def _line_un_selected(self):
        train = self.selectedTrain
        if train is None:
            return
        item: TrainItem = train.getItem()
        item.unSelect()

        self.nowItem.setPlainText(' ')
        self.selectedTrain = None

    def mousePressEvent(self, QMouseEvent):
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

        self.lastpos = pos

    def save(self, filename: str = 'output/test.png'):
        """
        导出为PNG。
        """
        self.marginItemGroups["left"].setX(0)
        self.marginItemGroups["right"].setX(0)
        self.marginItemGroups["up"].setY(0)
        self.marginItemGroups["down"].setY(0)
        self.nowItem.setX(0);
        self.nowItem.setY(0)

        # image = QtGui.QImage(self.scene.width(),self.scene.height(),QtGui.QImage.Format_ARGB32)
        # image = QtGui.QImage(self.scene.sceneRect().toSize,QtGui.QImage.Format_ARGB32)
        note_apdx = 0
        if self.graph.markdown():
            note_apdx = 80
        image = QtGui.QImage(self.scene.width(), self.scene.height() + 100 + note_apdx, QtGui.QImage.Format_ARGB32)
        image.fill(Qt.white)

        painter = QtGui.QPainter()
        painter.begin(image)
        painter.setPen(QtGui.QPen(QtGui.QColor(self.graph.UIConfigData()["text_color"])))
        font = QtGui.QFont()
        font.setPixelSize(50)
        font.setBold(True)
        font.setUnderline(True)
        painter.setFont(font)
        painter.drawText(self.margins["left"], 80, "{}{}-{}间列车运行图  {}km".format(self.graph.lineName(),
                                                                                self.graph.firstStation(),
                                                                                self.graph.lastStation(),
                                                                                self.graph.lineLength()),
                         )
        if self.graph.markdown():
            font.setPixelSize(20)
            font.setBold(False)
            font.setUnderline(False)
            painter.setFont(font)
            nnn = '\n'
            painter.drawText(self.margins["left"], self.scene.height() + 100 + 40,
                             f"备注：{self.graph.markdown().replace(nnn,' ')}"
                             )

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

    def _stationFromYValue(self, event_y: int):
        """
        :param y:
        :return: tuple: 纵坐标区间，两个站名，里程
        """
        last_station, last_y = "", 0
        last_mile = 0
        for name, mile, y in self.graph.stationMileYValues():
            if y is None:
                continue
            if abs(y - event_y) < 1:
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
        :param x:
        :return:
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
        collidItems = self.selectedTrain.getItem().collidingItems()
        print("collid calculate ok")
        selfItem = self.selectedTrain.getItem()

        events = []
        # 图定到开时间
        for name, ddsj, cfsj in self.selectedTrain.station_infos():
            if not self.graph.stationInLine(name):
                continue
            if ddsj == cfsj:
                dict = {
                    "type": TrainEventType.pass_settled,
                    "time": ddsj,
                    "former_station": name,
                    "later_station": None,
                    "another": None,
                    "mile": self.graph.stationMile(name)
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
                events.append(dict1);
                events.append(dict2)

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
                print(self.selectedTrain.fullCheci(), train.fullCheci())
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
        # 先按时间排序
        event_source.sort(key=lambda x: x["time"])
        # 按里程排序
        train: Train = self.selectedTrain
        event_source.sort(key=lambda x: x["mile"])
        if not train.isDown():
            event_source.reverse()

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
                    "another": train2.localCheci(),
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
        :param train1:
        :param train2:
        :param former:
        :param later:
        :return:
        """
        if train1.isDown() != train2.isDown():
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

    def on_show_forbid_changed(self, checked, down):
        if checked:
            self.show_forbid(down)
        else:
            self._remove_forbid(down)

    def show_forbid(self, down, remove=True):
        print("show forbid")
        if remove:
            self._remove_forbid(down)
        print("remove ok")
        forbid_data: Forbid = self.graph.line.forbid
        pen = QtGui.QPen(Qt.transparent)
        color = QtGui.QColor('#AAAAAA')
        color.setAlpha(150)
        brush = QtGui.QBrush(color)
        for node in forbid_data.nodes(down):
            items = self._add_forbid_rect(node, pen, brush)
            for item in items:
                forbid_data.addItem(down, item)

    def _add_forbid_rect(self, node, pen, brush):
        start_point = self.stationPosCalculate(node["fazhan"], node["begin"])
        start_x, start_y = start_point.x(), start_point.y()
        end_point = self.stationPosCalculate(node["daozhan"], node["end"])
        end_x, end_y = end_point.x(), end_point.y()
        if start_y > end_y:
            # 如果上下反了，直接交换，这个无所谓
            start_y, end_y = end_y, start_y
        if start_x == end_x:
            # 天窗时间为0，不用画
            return ()
        if start_x < end_x:
            # 不跨日天窗，正常画
            rectItem: QtWidgets.QGraphicsRectItem = self.scene.addRect(start_x, start_y, end_x - start_x,
                                                                       end_y - start_y)
            rectItem.setPen(pen)
            rectItem.setBrush(brush)
            return (rectItem,)
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
            return (rectItem1, rectItem2,)

    def _remove_forbid(self, down):
        forbid = self.graph.line.forbid
        print(forbid._downItems)
        print(forbid._upItems)
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
            item:TrainItem = train.item
            if item is None:
                self.addTrainLine(train)
            elif not item.isVisible():
                item.setVisible(True)
        else:
            item:TrainItem = train.item
            if item is not None and item.isVisible():
                item.setVisible(False)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = GraphicsWidget()
    window.showMaximized()
    sys.exit(app.exec_())

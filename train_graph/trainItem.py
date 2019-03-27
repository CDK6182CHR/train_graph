"""
2018.12.13新增文件
重构车次运行线，封装为item类。以前的path, text等item全都作为childItem。
目前设置为不可变，初始化时绘制，其后不可改变，只能重画。但做好抽象，允许扩展。
数据来源于graph对象。GraphWidget只用来计算位置，不可直接往图上画。
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt

from .graph import Graph
from .train import Train
from Timetable_new.utility import isKeche
from datetime import datetime,timedelta

class TrainItem(QtWidgets.QGraphicsItem):
    # 标记数字所在方向的常量
    NE = 1
    NW = 2
    SW = 3
    SE = 4
    # 结束判断的标记
    Pass = 1  # 因跨越站超过限制值终止
    End = 0
    Invalid = -1  # 运行线无效
    Setted = 2  # 用户设置终止
    Reversed = 3  # 因上下行翻转终止
    def __init__(self,train:Train,graph:Graph,graphWidget,start=None,end=None,down=None,
                 validWidth = 1,
                 showFullCheci=False,markMode=1,
                 parent=None):
        super().__init__(parent)
        self.train = train
        self.graph = graph
        self.startStation = start
        self.endStation = end
        self.graphWidget = graphWidget
        self.showFullCheci=showFullCheci
        self.validWidth = validWidth
        self.down = down
        self.markMode = markMode
        self.markTime = (markMode == 2)

        self.pathItem = None
        self.expandItem = None
        self.startLabelItem = None
        self.startLabelText = None
        self.endLabelItem = None
        self.endLabelText = None
        self.spanItems = []
        self.markLabels = []
        self.startRect = None
        self.endRect = None
        self.isHighlighted = False
        self.startAtThis = True
        self.endAtThis = False

        self.spanItemWidth=None
        self.spanItemHeight=None
        self.startPoint=None
        self.endPoint=None
        # self.labelItemWidth=None
        # self.labelItemHeight=None
        self.maxPassed = graph.UIConfigData().setdefault("max_passed_stations",3)

        self.color = self._trainColor()

    def setLine(self,start:int=0,end:int=-1,showStartLabel=True,showEndLabel = True)->(int,int):
        """
        2019.02.11新增逻辑：绘图过程中记录下每个车站的y_value。
        返回铺画结束的标号。如果有特殊情况，返回-1.
        铺画时从startIndex开始扫描站表，遇到startStation时开始铺画。
        如果end=None表明是自动判别，当判别到上下行翻转时返回。
        运行线有效是当且仅当返回不是-1.
        """
        end_setted = (self.startStation is not None)
        self.start_index = start
        if not self.train.isShow():
            # 若设置为不显示，忽略此命令
            return -1,self.Invalid
        train = self.train
        station_count = 0  # 本线站点数

        pen = self._trainPen()
        lineColor = pen.color()
        labelPen = self._trainPen()
        self.pen = pen
        labelPen.setWidth(1)

        span_left = []
        span_right = []

        width = self.graphWidget.scene.width() - self.graphWidget.margins['left'] - \
                self.graphWidget.margins['right']

        # 绘制主要部分pathItem
        path,start_point,end_point,end,status = self._setPathItem(span_left,span_right,False,start)
        down = self.down

        expand_path = None
        if self.validWidth > 1:
            expand_path,_,_,_,_ = self._setPathItem([],[],False,start,valid_only=True)

        station_count = self.station_count
        if station_count < 2:
            # print("station count < 2")
            return end,status

        if start_point is None:
            print(train.fullCheci())
            return end,status
        else:
            self.startPoint = start_point

        # train.setIsDown(down)
        checi = train.fullCheci() if self.showFullCheci else train.getCheci(down) # todo 修改逻辑

        brush = QtGui.QBrush(pen.color())
        # 终点标签
        # 绘制终点标签的条件是：自动计算Item且不是由转向终止的，或者用户指定。
        if showEndLabel and (end_setted or status != self.Reversed):
            endLabel = self._setEndItem(end_point,brush,checi,down,self.endAtThis)
            endLabelItem = QtWidgets.QGraphicsPathItem(endLabel, self)
            endLabelItem.setPen(labelPen)
            self.endLabelItem = endLabelItem

        # 起点标签
        if showStartLabel:
            label = self._setStartItem(start_point,brush,checi,down,self.startAtThis)
            labelItem = QtWidgets.QGraphicsPathItem(label, self)
            labelItem.setPen(labelPen)
            self.startLabelItem = labelItem

        # 跨界点标签
        UIDict = self.graph.UIConfigData()
        span_width = UIDict["margins"]["right"]-UIDict["margins"]["label_width"]
        font = QtGui.QFont()

        if self.spanItemWidth is None:
            self._setStartEndLabelText(checi,brush)
        if self.spanItemWidth > span_width:
            stretch = int(100 * span_width / self.spanItemWidth)
            font.setStretch(stretch)
        for y in span_left:
            textItem = QtWidgets.QGraphicsSimpleTextItem(checi, self)
            textItem.setBrush(brush)
            textItem.setFont(font)
            textItem.setX(self.graphWidget.margins["left"] - textItem.boundingRect().width())
            textItem.setY(y - self.spanItemHeight / 2)
            self.spanItems.append(textItem)

        for y in span_right:
            textItem = QtWidgets.QGraphicsSimpleTextItem(checi, self)
            textItem.setBrush(brush)
            textItem.setX(self.graphWidget.margins["left"] + width)
            textItem.setFont(font)
            textItem.setY(y - 10)
            self.spanItems.append(textItem)

        stroker = QtGui.QPainterPathStroker()
        stroker.setWidth(0.5)
        outpath = stroker.createStroke(path)

        # item = QtWidgets.QGraphicsItem
        pen.setJoinStyle(Qt.SvgMiterJoin)
        pen.setCapStyle(Qt.SquareCap)
        if expand_path is not None:
            outexpand = stroker.createStroke(expand_path)
            expandItem = QtWidgets.QGraphicsPathItem(outexpand,self)
            expandPen = QtGui.QPen(Qt.transparent,pen.width()*self.validWidth)
            expandItem.setPen(expandPen)
            expandItem.setZValue(-1)
            self.expandItem = expandItem
        pathItem = QtWidgets.QGraphicsPathItem(outpath, self)
        pathItem.setPen(pen)
        self.pathItem = pathItem
        return end,status


    def isDownInterval(self,last_point,this_point)->bool:
        """
        判定上下行区间。
        """
        if this_point.y() > last_point.y():
            return True
        return False

    def _setPathItem(self,
            span_left:list,span_right:list,
            mark_only:bool,
            startIndex:int,*,valid_only=False
        )->(QtGui.QPainterPath,QtCore.QRectF,QtCore.QRectF,int,int):
        """
        从setLine中抽离出来的绘制pathItem函数。返回：path,start_point,end_point, endIndex, status（终止原因）
        """
        train = self.train
        path = QtGui.QPainterPath()
        station_count = 0
        down = self.down  # 本线上下行判断
        last_point = None
        start_point = None
        start_dd,start_cf = None,None
        last_station = None
        passedCount = 0
        started = False if self.startStation is not None else True
        status = None
        curIndex = -1
        last_loop_station = None
        end_point = None
        for index,dct in enumerate(train.stationDicts(startIndex)):
            curIndex = index + startIndex  # 标记当前处理对象在时刻表中的index
            # 计算并添加运行线，上下行判断
            station, ddsj, cfsj = dct["zhanming"],dct["ddsj"],dct["cfsj"]
            ddpoint = self.graphWidget.stationPosCalculate(station, ddsj)
            cfpoint = self.graphWidget.stationPosCalculate(station, cfsj)
            stopped = (ddsj!=cfsj)

            if not started:
                if station == self.startStation:
                    started = True
                else:
                    continue
            if ddpoint is None or cfpoint is None:
                if start_point is not None:
                    passedCount += 1  # 这是列车区间跑到别的区段上的站点数
                if passedCount > self.maxPassed and self.endStation is None:
                    status = self.Pass
                    last_station = last_loop_station
                    end_point = last_point
                    # print("passedCount > maxPassed 227",self.train.fullCheci(),station)
                    break
                continue
            else:
                passedCount = 0

            if self.graph.stationDirection(station) == 0x0:
                # 取消贪心策略，设置为不通过的站一律不画
                continue

            train.setTrainStationYValue(dct,ddpoint.y())

            station_count += 1
            last_station = station

            if station_count == 1:
                # 第一个站
                self.startAtThis = train.isSfz(station)
                self.startStation = station
                start_dd,start_cf = ddsj,cfsj
                path.moveTo(ddpoint)
                start_point = ddpoint
                last_loop_station = station

            else:
                # path.lineTo(ddpoint)
                # 上下行判别
                newDown = self.isDownInterval(last_point,ddpoint)
                if down is None:
                    down = newDown
                elif down != newDown and self.endStation is None:
                    # 行别变化，终止铺画
                    status = self.Reversed
                    print("行别变化",down,newDown,station,self.train.fullCheci(),curIndex,station_count)
                    curIndex -= 1
                    last_station = last_loop_station
                    # 注意：保持last_station是上一个。
                    break
                if last_loop_station is not None:
                    # 当down是None时这里的判断引起问题. 故把这一块移动到上下行判断之后去。
                    passed_stations_left = self.graph.passedStationCount(last_loop_station,station,down)
                    passedCount += passed_stations_left  # 叠加此区间内的【车次时刻表】和【本线站表】不重合的数量
                    if passedCount > self.maxPassed and self.endStation is None:
                        status = self.Pass
                        last_station = last_loop_station
                        end_point = last_point
                        # print("passedCount > maxPassed line238",self.train.fullCheci(),station)
                        print(passed_stations_left,last_loop_station,station,down)
                        break
                if not mark_only:
                    self._incline_line(path, last_point, ddpoint, span_left, span_right)
            if not mark_only:
                self._H_line(path, ddpoint, cfpoint, span_left, span_right,
                         self.graph.UIConfigData()["show_line_in_station"])
            if self.markTime:
                # 标记停点。precondition: for station_count>=2, down is whether True or False, i.e. not None
                if station_count == 1:
                    last_point = cfpoint
                    continue
                elif station_count == 2:
                    # 先补画第一个站的
                    first_stopped = (last_point != start_point)
                    if first_stopped and down:
                        self.addTimeMark(start_point,start_dd,self.NE)
                        self.addTimeMark(last_point,start_cf,self.SW)
                    elif first_stopped and not down:
                        self.addTimeMark(start_point,start_dd,self.SE)
                        self.addTimeMark(last_point,start_cf,self.NW)
                    elif not first_stopped and not down:
                        self.addTimeMark(last_point,start_dd,self.NW)
                    else:
                        self.addTimeMark(last_point,start_dd,self.SW)
                if stopped and down:
                    self.addTimeMark(ddpoint,ddsj,self.NE)
                    self.addTimeMark(cfpoint,cfsj,self.SW)
                elif stopped and not down:
                    self.addTimeMark(ddpoint,ddsj,self.SE)
                    self.addTimeMark(cfpoint,cfsj,self.NW)
                elif not stopped and not down:
                    self.addTimeMark(ddpoint,ddsj,self.NW)
                else:
                    self.addTimeMark(ddpoint,ddsj,self.SW)
            last_point = cfpoint
            last_loop_station = station
            if self.endStation is not None and self.endStation == station:
                status = self.Setted
                last_station = station
                break

        self.endStation = last_station
        if status is None:
            status = self.End
        if end_point is None:
            end_point = path.currentPosition()
        if last_station is not None:
            self.endAtThis = train.isZdz(last_station)
        if not mark_only and not valid_only:
            self.endPoint = end_point
        self.down = down
        self.station_count = station_count
        return path,start_point,end_point,curIndex,status

    def _setStartEndLabelText(self,checi,brush)->QtWidgets.QGraphicsSimpleTextItem:
        """
        生成一个simpleTextItem，并设置好self.spanItemWidth等。
        """
        endLabelText = QtWidgets.QGraphicsSimpleTextItem(checi, self)
        endLabelText.setBrush(brush)
        self.spanItemWidth = endLabelText.boundingRect().width()
        self.spanItemHeight = endLabelText.boundingRect().height()
        return endLabelText

    def _setEndItem(self,end_point:QtCore.QPointF,brush:QtGui.QBrush,
                    checi:str,down:bool,endAtThis:bool)->QtGui.QPainterPath:
        """
        绘制终点标签。
        同时设定spanItemHeight和~width两个attribute。
        """
        # 终点标签
        endLabelText = self._setStartEndLabelText(checi,brush)
        w,h = self.spanItemWidth,self.spanItemHeight
        endLabel = QtGui.QPainterPath()
        self.endLabelText = endLabelText
        end_height = self.graph.UIConfigData()['end_label_height']
        if endAtThis:
            if down:
                endLabel.moveTo(end_point)
                curPoint = QtCore.QPointF(end_point.x(),end_point.y())
                curPoint.setY(curPoint.y()+end_height/2)
                endLabel.lineTo(curPoint)
                poly = QtGui.QPolygonF((QtCore.QPointF(curPoint.x()-end_height/3,curPoint.y()),
                                QtCore.QPointF(curPoint.x()+end_height/3,curPoint.y()),
                                QtCore.QPointF(curPoint.x(),curPoint.y()+end_height/2),
                                QtCore.QPointF(curPoint.x() - end_height / 3, curPoint.y())))
                endLabel.addPolygon(poly)
                curPoint.setY(end_point.y()+end_height)
                curPoint.setX(curPoint.x()-w/2)
                endLabel.moveTo(curPoint)
                endLabelText.setX(curPoint.x())
                endLabelText.setY(curPoint.y())
                curPoint.setX(curPoint.x()+w)
                endLabel.lineTo(curPoint)

            else:
                endLabel.moveTo(end_point)
                curPoint = QtCore.QPointF(end_point)
                curPoint.setY(end_point.y()-end_height/2)
                endLabel.lineTo(curPoint)
                curPoint.setY(end_point.y()-end_height)
                endLabel.moveTo(curPoint)
                poly = QtGui.QPolygonF((
                    curPoint,
                    QtCore.QPointF(curPoint.x()-end_height/3,curPoint.y()+end_height/2),
                    QtCore.QPointF(curPoint.x()+end_height/3,curPoint.y()+end_height/2),
                    curPoint
                ))
                endLabel.addPolygon(poly)
                curPoint.setX(curPoint.x()-w/2)
                endLabel.moveTo(curPoint)
                endLabelText.setX(curPoint.x())
                endLabelText.setY(curPoint.y()-h)
                curPoint.setX(curPoint.x()+w)
                endLabel.lineTo(curPoint)
        else: # not endAtThis
            if down:
                endLabel.moveTo(end_point)
                curPoint = QtCore.QPointF(end_point)
                curPoint.setY(curPoint.y()+h)
                endLabel.lineTo(curPoint)
                endLabelText.setPos(curPoint)
                curPoint.setX(curPoint.x()+w+h)
                endLabel.lineTo(curPoint)
                curPoint.setX(curPoint.x()-h)
                curPoint.setY(curPoint.y()+h)
                endLabel.lineTo(curPoint)
            else:
                endLabel.moveTo(end_point)
                curPoint = QtCore.QPointF(end_point)
                curPoint.setY(curPoint.y()-h)
                endLabel.lineTo(curPoint)
                endLabelText.setX(curPoint.x())
                endLabelText.setY(curPoint.y()-h)
                curPoint.setX(curPoint.x()+w+h)
                endLabel.lineTo(curPoint)
                curPoint.setX(curPoint.x()-h)
                curPoint.setY(curPoint.y()-h)
                endLabel.lineTo(curPoint)

        return endLabel

    def _setStartItem(self, start_point: QtCore.QPointF, brush: QtGui.QBrush,
                    checi: str, down: bool, startAtThis: bool) -> QtGui.QPainterPath:
        label = QtGui.QPainterPath()
        label.moveTo(start_point)
        startLabelText = self._setStartEndLabelText(checi,brush)
        self.startLabelText = startLabelText
        start_height = self.graph.UIConfigData()['start_label_height']
        w,h = self.spanItemWidth,self.spanItemHeight
        if startAtThis:
            if down:
                label.moveTo(start_point)
                next_point = QtCore.QPoint(start_point.x(), start_point.y() - start_height)
                label.lineTo(next_point)
                next_point.setX(next_point.x() - self.spanItemWidth / 2)
                label.moveTo(next_point)
                # label.addText(next_point.x() + 30 - (len(checi) * 9) / 2, next_point.y(), QtGui.QFont(),
                #               checi)
                startLabelText.setX(next_point.x())
                startLabelText.setY(next_point.y() - self.spanItemHeight)
                # label.moveTo(next_point)
                next_point.setX(next_point.x() + self.spanItemWidth)
                label.lineTo(next_point)

            else:
                next_point = QtCore.QPoint(start_point.x(), start_point.y() + start_height)
                label.lineTo(next_point)
                next_point.setX(next_point.x() - self.spanItemWidth / 2)
                next_point.setY(next_point.y())
                label.moveTo(next_point)
                self.startLabelText.setX(next_point.x())
                self.startLabelText.setY(next_point.y())
                next_point.setY(next_point.y())
                next_point.setX(next_point.x() + self.spanItemWidth)
                label.lineTo(next_point)

        else:
            if down:
                label.moveTo(start_point)
                curPoint = QtCore.QPointF(start_point)
                curPoint.setY(curPoint.y()-start_height)
                label.lineTo(curPoint)
                curPoint.setX(curPoint.x()-w)
                label.lineTo(curPoint)
                startLabelText.setX(curPoint.x())
                startLabelText.setY(curPoint.y()-h)
                curPoint.setX(curPoint.x()-h)
                curPoint.setY(curPoint.y()-h)
                label.lineTo(curPoint)
            else:
                label.moveTo(start_point)
                curPoint = QtCore.QPointF(start_point)
                curPoint.setY(curPoint.y()+start_height)
                label.lineTo(curPoint)
                curPoint.setX(curPoint.x()-w)
                label.lineTo(curPoint)
                startLabelText.setPos(curPoint)
                curPoint.setX(curPoint.x()-h)
                curPoint.setY(curPoint.y()+h)
                label.lineTo(curPoint)

        return label

    def _trainColor(self):
        color_str = self.train.color()
        if not color_str:
            try:
                color_str = self.graph.UIConfigData()["default_colors"][self.train.trainType()]
            except KeyError:
                color_str = self.graph.UIConfigData()["default_colors"]["default"]
            # train.setUI(color=color_str)
        color = QtGui.QColor(color_str)
        return color

    def _trainPen(self)->QtGui.QPen:
        """
        Decide QPen used to draw path.
        """
        train = self.train
        color = self.color

        width = train.lineWidth()
        if width == 0:
            if isKeche(train.trainType()) or train.trainType() == "特快行包":
                width = self.graph.UIConfigData()["default_keche_width"]
            else:
                width = self.graph.UIConfigData()["default_huoche_width"]
            # train.setUI(width=width)

        return QtGui.QPen(color,width)

    def _incline_line(self,path:QtGui.QPainterPath,point1:QtCore.QPoint,
                      point2:QtCore.QPoint,span_left:list,span_right:list):
        #绘制站间的斜线
        #TODO 暂未考虑直接跨过无定义区域的情况
        width = self.graphWidget.scene.width() - \
                self.graphWidget.margins["left"] - self.graphWidget.margins["right"]
        if point1.inRange and point2.inRange:
            if point1.x() <= point2.x():
                path.lineTo(point2)
            else:
                # 跨界运行线
                dx = point2.x()-point1.x()+width
                dy = point2.y()-point1.y()
                ax = width+self.graphWidget.margins["left"]-point1.x()
                h = ax*dy/dx
                span_right.append(point1.y()+h)
                span_left.append(point1.y()+h)
                path.lineTo(self.graphWidget.margins["left"]+width,point1.y()+h)
                path.moveTo(self.graphWidget.margins["left"],point1.y()+h)
                path.lineTo(point2)
        elif not point1.inRange and not point2.inRange:
            return

        elif point1.inRange:
            #右侧点越界
            dx = point2.x() - point1.x() + width
            dy = point2.y() - point1.y()
            ax = width + self.graphWidget.margins["left"] - point1.x()
            h = ax * dy / dx
            span_right.append(point1.y() + h)
            path.lineTo(self.graphWidget.margins["left"] + width, point1.y() + h)

        else:
            #左侧点越界
            dx = point2.x() - point1.x() + width
            dy = point2.y() - point1.y()
            ax = width + self.graphWidget.margins["left"] - point1.x()
            h = ax * dy / dx
            span_left.append(point1.y() + h)
            path.moveTo(self.graphWidget.margins["left"], point1.y() + h)
            path.lineTo(point2)

    def _H_line(self,path:QtGui.QPainterPath,point1:QtCore.QPoint,
                point2:QtCore.QPoint,span_left:list,span_right:list,show:bool):
        #绘制站内水平线
        width = self.graphWidget.scene.width() - self.graphWidget.margins["left"] \
                - self.graphWidget.margins["right"]
        if point1.inRange and point2.inRange:
            #都在范围内，直接画
            if point1.x() <= point2.x():
                if show:
                    path.lineTo(point2)
                else:
                    path.moveTo(point2)
            else:
                span_left.append(point1.y())
                span_right.append(point1.y())
                if show:
                    path.lineTo(width+self.graphWidget.margins["left"],point2.y())
                    path.moveTo(self.graphWidget.margins["left"],point2.y())
                    path.lineTo(point2)
                else:
                    path.moveTo(point2)
        elif not point1.inRange and not point2.inRange:
            return
        elif point1.inRange:
            #右侧点跨界
            span_right.append(point1.y())
            if show:
                path.lineTo(width+self.graphWidget.margins["left"],point1.y())
            else:
                path.moveTo(width + self.graphWidget.margins["left"], point1.y())
        elif point2.inRange:
            span_left.append(point1.y())
            if show:
                path.moveTo(self.graphWidget.margins["left"],point1.y())
                path.lineTo(point2)
            else:
                path.moveTo(point2)

    def addTimeMark(self,point:QtCore.QPoint,tm:datetime,dir_:int):
        """
        给一个点增加精确时刻标注。
        """
        d = tm.minute
        if tm.second >= 30:
            d += 1
        d %=10
        item = QtWidgets.QGraphicsSimpleTextItem(str(d),self)
        h,w = item.boundingRect().height(),item.boundingRect().width()
        x_off,y_off = 0*w,0*h
        if dir_ == self.SW:
            item.setX(point.x()-w+x_off)
            item.setY(point.y()-y_off)
        elif dir_ == self.SE:
            item.setX(point.x()-x_off)
            item.setY(point.y()-y_off)
        elif dir_ == self.NW:
            item.setX(point.x()-w+x_off)
            item.setY(point.y()-h+y_off)
        else: # NE
            item.setX(point.x()-x_off)
            item.setY(point.y()-h+y_off)
        # item.setDefaultTextColor(self.color)
        item.setBrush(QtGui.QBrush(self.color))
        self.markLabels.append(item)

    def select(self):
        """
        封装选中本车次的所有操作，主要是运行线加粗。
        """
        train = self.train

        if train is None or self.isHighlighted:
            # 若重复选中，无操作
            return

        path = self.pathItem
        label = self.startLabelItem

        #path:QtWidgets.QGraphicsPathItem
        #label:QtWidgets.QGraphicsPathItem

        if path is None:
            return

        #运行线加粗显示
        pen = path.pen()
        pen.setWidth(pen.width()+1)
        path.setPen(pen)
        path.setZValue(1)

        brush = QtGui.QBrush(pen.color())
        UIDict = self.graph.UIConfigData()

        #标签突出显示
        rectPen = QtGui.QPen(pen.color())
        rectPen.setWidth(0.5)
        pen.setWidth(2)
        if label is not None:
            label.setZValue(1)
            label.setPen(pen)

            # 起点
            startPoint = self.startPoint
            x_append = self.spanItemWidth / 2 if self.startAtThis else self.spanItemWidth
            if self.down:
                Rect = QtCore.QRectF(startPoint.x()-x_append,
                                              startPoint.y()-self.spanItemHeight-UIDict['start_label_height'],
                                              self.spanItemWidth,
                                              self.spanItemHeight)
            else:
                Rect = QtCore.QRectF(startPoint.x() - x_append,
                                              startPoint.y()+UIDict['start_label_height'],
                                              self.spanItemWidth,
                                              self.spanItemHeight)
            self.tempRect = QtWidgets.QGraphicsRectItem(Rect,self)

            self.tempRect.setPen(rectPen)
            self.tempRect.setBrush(brush)
            self.tempRect.setZValue(0.5)
            self.startLabelText.setZValue(1)
            self.startLabelText.setBrush(Qt.white)


        # 终点标签突出显示
        label = self.endLabelItem
        if label is not None:
            label.setZValue(1)
            pen.setWidth(2)
            label.setPen(pen)
            brush = QtGui.QBrush(pen.color())
            endPoint = self.endPoint
            x_append = self.spanItemWidth/2 if self.endAtThis else 0
            if self.down:
                rect = QtCore.QRectF(endPoint.x()-x_append,
                                     endPoint.y()+UIDict['end_label_height'],
                                     self.spanItemWidth,
                                     self.spanItemHeight
                )
            else:
                rect = QtCore.QRectF(endPoint.x() - x_append,
                                     endPoint.y() - UIDict['end_label_height'] - self.spanItemHeight,
                                     self.spanItemWidth,
                                     self.spanItemHeight
                                     )
            self.tempRect2 = QtWidgets.QGraphicsRectItem(rect,self)
            self.tempRect2.setPen(rectPen)
            self.tempRect2.setBrush(brush)
            self.tempRect2.setZValue(0.5)
            self.endLabelText.setZValue(1)
            self.endLabelText.setBrush(Qt.white)

        # 设置跨界点标签突出显示
        if self.spanItems:
            bfont = self.spanItems[0].font()
            bfont.setBold(True)
            for sub in self.spanItems:
                # sub:QtWidgets.QGraphicsTextItem
                sub.setFont(bfont)
        self.setZValue(2)

        # 显示详细停点
        if self.markMode == 1:
            self.markTime = True
            if self.markLabels:
                for it in self.markLabels:
                    it.setVisible(True)
            else:
                self._setPathItem([],[],startIndex=self.start_index,mark_only=True)
        self.isHighlighted = True

    def unSelect(self):
        if not self.isHighlighted:
            return
        train = self.train
        path = self.pathItem
        label = self.startLabelItem
        endlabel = self.endLabelItem

        if path is not None:
            pathPen = path.pen()
            pathPen.setWidth(pathPen.width() - 1)
            path.setPen(pathPen)
            path.setZValue(0)

            if label is not None:
                pathPen.setWidth(1)
                label.setPen(pathPen)
                label.setZValue(0)
                self.startLabelText.setZValue(0)
                self.startLabelText.setBrush(pathPen.color())
                self.graphWidget.scene.removeItem(self.tempRect)

            if endlabel is not None:
                endlabel.setPen(pathPen)
                endlabel.setZValue(0)
                self.endLabelText.setZValue(0)
                self.endLabelText.setBrush(pathPen.color())
                self.graphWidget.scene.removeItem(self.tempRect2)

        self.tempRect = None
        self.tempRect2 = None

        # 取消跨界点标签突出显示
        if self.spanItems:
            bfont = self.spanItems[0].font()
            bfont.setBold(False)
            for sub in self.spanItems:
                # sub:QtWidgets.QGraphicsTextItem
                sub.setFont(bfont)
        self.setZValue(0)

        if self.markMode == 1:
            for item in self.markLabels:
                item.setVisible(False)
            self.markTime = False

        self.isHighlighted = False

    def setColor(self,color:QtGui.QColor=None):
        if color is self.color:
            return
        if color is None:
            color = self._trainColor()
        for sub in self.validItems(containSpan=True):
            if sub is None:
                continue
            if isinstance(sub,QtWidgets.QGraphicsPathItem):
                pen:QtGui.QPen = sub.pen()
                pen.setColor(color)
                sub.setPen(pen)
            elif isinstance(sub,QtWidgets.QGraphicsSimpleTextItem):
                sub.setBrush(QtGui.QBrush(color))
            elif isinstance(sub,QtWidgets.QGraphicsTextItem):
                sub.setDefaultTextColor(color)
        self.color = color

    def resetUI(self):
        """
        2019.02.27添加，由trainWidget批量修改调用。已知train对象数据已经修改好，更新item的颜色和宽度。
        """
        self.setColor()
        pen:QtGui.QPen = self._trainPen()
        self.pathItem.setPen(pen)

    def paint(self, QPainter, QStyleOptionGraphicsItem, widget=None):
        return
        # for sub in (self.pathItem,
        # self.startLabelItem,
        # self.endLabelItem,
        # self.startRect,
        # self.endRect ):
        #     if sub is not None:
        #         sub.paint(QPainter, QStyleOptionGraphicsItem,widget)

        # for sub in self.spanItems:
        #     sub.paint(QPainter, QStyleOptionGraphicsItem,widget)

    def boundingRect(self):
        """
        返回的是所有元素的bounding rect的并
        """
        minStartX,minStartY = 1000000,1000000
        maxEndX,maxEndY = 0,0
        for sub in self.validItems():
            rect:QtCore.QRectF = sub.boundingRect()
            if rect.x()<minStartX:
                minStartX = rect.x()
            if rect.x() + rect.width() > maxEndX:
                maxEndX = rect.x() + rect.width()
            if rect.y()<minStartY:
                minStartY = rect.y()
            if rect.y() + rect.height() > maxEndY:
                maxEndY = rect.y() + rect.height()
        return QtCore.QRectF(minStartX,minStartY,maxEndX-minStartX,maxEndY-minStartY)


    def contains(self, point):
        result = False
        for sub in self.validItems():
            result = result or sub.contains(point)
        return result


    def validItems(self,containSpan=True,containExpand=False,containMark=True):
        """
        依次给出自身的所有非None子item
        """
        valids = [self.pathItem,self.startLabelItem,self.endLabelItem,
                  self.startLabelText,self.endLabelText]
        if containSpan:
            valids += self.spanItems
        if containExpand:
            valids.append(self.expandItem)
        if containMark:
            valids += self.markLabels
        for sub in valids:
            if sub is not None:
                yield sub

"""
2018.12.13新增文件
重构车次运行线，封装为item类。以前的path, text等item全都作为childItem。
目前设置为不可变，初始化时绘制，其后不可改变，只能重画。但做好抽象，允许扩展。
数据来源于graph对象。GraphWidget只用来计算位置，不可直接往图上画。
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt

from graph import Graph
from train import Train
from utility import isKeche

class TrainItem(QtWidgets.QGraphicsItem):
    def __init__(self,train:Train,graph:Graph,graphWidget,parent=None):
        super().__init__(parent)
        self.train = train
        self.graph = graph
        self.graphWidget = graphWidget

        self.pathItem = None
        self.startLabelItem = None
        self.endLabelItem = None
        self.spanItems = []
        self.startRect = None
        self.endRect = None
        self.isHighlighted = False
        self.setLine()

    def setLine(self):
        if not self.train.isShow():
            # 若设置为不显示，忽略此命令
            return
        train = self.train
        station_count = 0  # 本线站点数
        path = QtGui.QPainterPath()

        pen = self._trainPen()
        lineColor = pen.color()
        labelPen = self._trainPen()
        labelPen.setWidth(1)
        start_point = None
        down = train.down  # 本线上下行判断
        last_point = None
        span_left = []
        span_right = []

        width = self.graphWidget.scene.width() - self.graphWidget.margins['left'] - \
                self.graphWidget.margins['right']

        for station, ddsj, cfsj in train.station_infos():
            # 计算并添加运行线，上下行判断
            ddpoint = self.graphWidget.stationPosCalculate(station, ddsj)
            cfpoint = self.graphWidget.stationPosCalculate(station, cfsj)

            if ddpoint is None:
                continue

            station_count += 1

            if station_count == 1:
                path.moveTo(ddpoint)
                start_point = ddpoint

            else:
                # path.lineTo(ddpoint)
                self._incline_line(path, last_point, ddpoint, span_left, span_right)
                # 上下行判别
                if down is None:
                    if station_count == 2:
                        if ddpoint.y() - start_point.y() > 0:
                            down = True
                        else:
                            down = False

            self._H_line(path, ddpoint, cfpoint, span_left, span_right,
                         self.graph.UIConfigData()["show_line_in_station"])

            last_point = cfpoint

        if start_point is None:
            print(train.fullCheci())
            return

        end_point = path.currentPosition()
        checi = train.downCheci() if down else train.upCheci()

        # 在跨界点添加标签
        for y in span_left:
            textItem: QtWidgets.QGraphicsTextItem = QtWidgets.QGraphicsTextItem(checi,self)
            textItem.setDefaultTextColor(pen.color())
            textItem.setX(self.graphWidget.margins["left"] - 12 * len(checi))
            textItem.setY(y - 10)
            self.spanItems.append(textItem)

        for y in span_right:
            textItem: QtWidgets.QGraphicsTextItem = QtWidgets.QGraphicsTextItem(checi,self)
            textItem.setDefaultTextColor(pen.color())
            textItem.setX(self.graphWidget.margins["left"] + width)
            textItem.setY(y - 10)
            self.spanItems.append(textItem)

        label = QtGui.QPainterPath()
        label.moveTo(start_point)

        train.setIsDown(down)

        # 终点标签
        endLabel = QtGui.QPainterPath()
        if down:
            endLabel.moveTo(end_point)
            endLabel.lineTo(end_point.x(), end_point.y() + 18)
            endLabel.moveTo(end_point.x() - 30, end_point.y() + 18)
            endLabel.addText(end_point.x() - (len(train.downCheci()) * 9) / 2,
                             end_point.y() + 20 + 12, QtGui.QFont(), train.downCheci())
            endLabel.moveTo(end_point.x() - 30, end_point.y() + 18)
            endLabel.lineTo(end_point.x() + 30, end_point.y() + 18)

        else:
            endLabel.moveTo(end_point)
            endLabel.lineTo(end_point.x(), end_point.y() - 18)
            endLabel.moveTo(end_point.x() - 30, end_point.y() - 18)
            endLabel.addText(end_point.x() - (len(train.upCheci()) * 9) / 2, end_point.y() - 18, QtGui.QFont(),
                             train.upCheci())
            endLabel.moveTo(end_point.x() - 30, end_point.y() - 18)
            endLabel.lineTo(end_point.x() + 30, end_point.y() - 18)

        # 处理车次标签
        if down:
            label.moveTo(start_point)
            next_point = QtCore.QPoint(start_point.x(), start_point.y() - 30)
            label.lineTo(next_point)
            next_point.setX(next_point.x() - 30)
            label.moveTo(next_point)
            label.addText(next_point.x() + 30 - (len(train.downCheci()) * 9) / 2, next_point.y(), QtGui.QFont(),
                          train.downCheci())
            label.moveTo(next_point)
            next_point.setX(next_point.x() + 60)
            label.lineTo(next_point)

        else:
            next_point = QtCore.QPoint(start_point.x(), start_point.y() + 30)
            label.lineTo(next_point)
            next_point.setX(next_point.x() - 30)
            next_point.setY(next_point.y() + 12)
            label.moveTo(next_point)
            label.addText(next_point.x() + 30 - (len(train.upCheci()) * 9) / 2, next_point.y(), QtGui.QFont(),
                          train.upCheci())
            next_point.setY(next_point.y() - 12)
            label.moveTo(next_point)
            next_point.setX(next_point.x() + 60)
            label.lineTo(next_point)

        brush = QtGui.QBrush(lineColor)
        brush.setColor(lineColor)

        stroker = QtGui.QPainterPathStroker()
        stroker.setWidth(0.5)
        outpath = stroker.createStroke(path)

        if station_count >= 2:
            item = QtWidgets.QGraphicsItem
            pen.setJoinStyle(Qt.SvgMiterJoin)
            pen.setCapStyle(Qt.SquareCap)
            pathItem = QtWidgets.QGraphicsPathItem(outpath, self)
            pathItem.setPen(pen)
            self.pathItem = pathItem
            labelItem = QtWidgets.QGraphicsPathItem(label, self)
            labelItem.setPen(labelPen)
            self.startLabelItem = labelItem
            endLabelItem = QtWidgets.QGraphicsPathItem(endLabel,self)
            endLabelItem.setPen(labelPen)
            self.endLabelItem=endLabelItem
            train.setItem(self)
        else:
            train.setItem(None)

    def _trainPen(self):
        """
        Decide QPen used to draw path.
        """
        train = self.train
        color_str = train.color()
        if not color_str:
            try:
                color_str = self.graph.UIConfigData()["default_colors"][train.trainType()]
            except KeyError:
                color_str = self.graph.UIConfigData()["default_colors"]["default"]
            #train.setUI(color=color_str)
        color = QtGui.QColor(color_str)

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
                print("跨日：",point1,point2)
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
        label.setZValue(1)

        #标签突出显示
        rectPen = QtGui.QPen(pen.color())
        rectPen.setWidth(0.5)
        pen.setWidth(2)
        label.setPen(pen)
        brush = QtGui.QBrush(QtGui.QColor("#FFFFFF"))
        point = label.path().currentPosition()  #右下角
        if train.isDown():
            self.tempRect = QtWidgets.QGraphicsRectItem(QtCore.QRectF(point.x()-62,point.y()-14,64,15),self)

        else:
            self.tempRect = QtWidgets.QGraphicsRectItem(QtCore.QRectF(point.x() - 62, point.y()-1, 64, 15),self)

        self.tempRect.setPen(rectPen)
        self.tempRect.setBrush(brush)
        self.tempRect.setZValue(0.5)

        label = self.endLabelItem
        label.setZValue(1)
        # 终点标签突出显示
        pen.setWidth(2)
        label.setPen(pen)
        brush = QtGui.QBrush(Qt.white)
        point = label.path().currentPosition()  # 右下角
        if not train.isDown():
            self.tempRect2 = QtWidgets.QGraphicsRectItem(QtCore.QRectF(point.x() - 64, point.y() - 14, 64, 15), self)
        else:
            self.tempRect2 = QtWidgets.QGraphicsRectItem(QtCore.QRectF(point.x() - 64, point.y() - 1, 64, 15), self)
        self.tempRect2.setPen(rectPen)
        self.tempRect2.setBrush(brush)
        self.tempRect2.setZValue(0.5)

        # 设置跨界点标签突出显示
        bfont = QtGui.QFont()
        bfont.setBold(True)
        for sub in self.spanItems:
            # sub:QtWidgets.QGraphicsTextItem
            sub.setFont(bfont)
        self.setZValue(2)
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

            pathPen.setWidth(1)
            label.setPen(pathPen)
            label.setZValue(0)

            endlabel.setPen(pathPen)
            endlabel.setZValue(0)

        self.graphWidget.scene.removeItem(self.tempRect)
        self.graphWidget.scene.removeItem(self.tempRect2)
        self.tempRect = None
        self.tempRect2 = None

        # 取消跨界点标签突出显示
        bfont = QtGui.QFont()
        bfont.setBold(False)
        for sub in self.spanItems:
            # sub:QtWidgets.QGraphicsTextItem
            sub.setFont(bfont)
        self.setZValue(0)

        self.isHighlighted = False

    def paint(self, QPainter, QStyleOptionGraphicsItem, widget=None):
        return
        for sub in (self.pathItem,
        self.startLabelItem,
        self.endLabelItem,
        self.startRect,
        self.endRect ):
            if sub is not None:
                sub.paint(QPainter, QStyleOptionGraphicsItem,widget)

        for sub in self.spanItems:
            sub.paint(QPainter, QStyleOptionGraphicsItem,widget)

    def boundingRect(self):
        """
        返回的是所有元素的bounding rect的并
        :return:
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


    def validItems(self,containSpan=True):
        """
        依次给出自身的所有非None子item
        """
        if containSpan:
            for sub in [self.pathItem,self.startLabelItem,self.endLabelItem] + self.spanItems:
                if sub is not None:
                    yield sub
        else:
            for sub in [self.pathItem,self.startLabelItem,self.endLabelItem]:
                if sub is not None:
                    yield sub

"""
2019.07.07新建。
交路图功能，这里实现图形部分，继承GraphicsWidget。连接线的布置方向由前车决定。
"""
from PyQt5 import QtWidgets,QtGui,QtCore,QtPrintSupport
from PyQt5.QtCore import Qt
from .graph import Graph,Train,Circuit,CircuitNode
from datetime import datetime,timedelta
from .pyETRCExceptions import *
from Timetable_new.utility import stationEqual

class CircuitDiagram(QtWidgets.QGraphicsView):
    """
    list<dict> datas;
    dict{
        "node":CircuitNode;
        "start_day":int,
        "end_day":int,
    }
    dict<str,y> stationYValues;
    eg. {
        "成都东",120,
        "重庆北":300,
    }
    """
    def __init__(self,graph,circuit,parent=None):
        super(CircuitDiagram, self).__init__(parent)
        self.graph = graph  # type:Graph
        self.circuit = circuit  # type:Circuit
        self._multiDayByTimetable = False  # False: 仅根据首末站时刻。True: 根据所有时刻。
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.maxDay = 1  # 最大天数。注意天数从0开始。
        self.sizes = {
            "dayWidth":700,  # 每日宽度
            "totalWidth":...,  # 总宽度，可改变
            "height":500,  # 总高度，定值
            "left":140,  # 以下是边距。左侧边距划线用以标出站名，右侧边界为最后一日边界。
            "right":20,
            "top":40,  # 上下边界是最上和最下的站出现的位置。
            "bottom":40,
            "stationDistance":40,  # 两站间的垂直距离
            "extraHeight":20,  # 车次线超过车站线的距离
        }
        self.setWindowTitle('交路图测试')
        self.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.datas = []
        self.stationYValues = {}
        self.topNext = self.sizes['top']  # 将要分配的下一个顶部车站的纵坐标
        self.bottomNext = self.sizes['height'] - self.sizes['bottom']

        self.transData()
        self.initUI()

    def transData(self):
        self.datas.clear()
        self.stationYValues.clear()
        currentDay = 0
        last_time = "00:00:00"
        for node in self.circuit.nodes():
            train = node.train()
            dep = train.departure()  # 这里已经保证时刻表非空
            des = train.destination()
            if dep is None:
                raise StartOrEndNotMatchedError(train.sfz,train.firstStation(),train)
            if des is None:
                raise StartOrEndNotMatchedError(train.zdz,train.endStation(),train)
            # dep, des都不是None。
            if dep['ddsj'].strftime('%H:%M:%S') < last_time:
                currentDay+=1
            start_day = currentDay
            currentDay += train.deltaDays(self.multiDayByTimetable())
            end_day = currentDay
            last_time = des['cfsj'].strftime('%H:%M:%S')
            dct = {
                "node":node,
                "start_day":start_day,
                "end_day":end_day,
            }
            self.datas.append(dct)
        self.maxDay = currentDay


    def initUI(self):
        self.scene.clear()
        self._setVLines()
        self._setHLines()

        # 先直接在这里写添加车次线的部分，有需要时再独立封装。
        dir_down = None  # None-第一个。True: 上一车次是向下的。False: 上一车次是向上的。
        last_point:QtCore.QPointF = None  # 上一车次的终止点
        for data in self.datas:
            train:Train = data['node'].train()
            startPoint = self._posCalculate(train.sfz,data['start_day'],train.timetable[0]['ddsj'])
            endPoint = self._posCalculate(train.zdz,data['end_day'],train.timetable[-1]['cfsj'])
            if dir_down is not None:
                # 先给出连接线。如果非同一站点，画虚线。
                if last_point.y() != startPoint.y():
                    pen = QtGui.QPen(Qt.DashLine)
                    self.scene.addLine(last_point.x(),last_point.y(),
                                                  startPoint.x(),startPoint.y(),pen)
                else:
                    y = last_point.y()
                    if dir_down:
                        maxY = y+self.sizes["extraHeight"]
                    else:
                        maxY = y-self.sizes["extraHeight"]
                    self.scene.addLine(last_point.x(),y,last_point.x(),maxY)
                    self.scene.addLine(last_point.x(),maxY,startPoint.x(),maxY)
                    self.scene.addLine(startPoint.x(),maxY,startPoint.x(),y)
            self.scene.addLine(startPoint.x(),startPoint.y(),endPoint.x(),endPoint.y())
            cx,cy = ((startPoint.x()+endPoint.x())/2,(startPoint.y()+endPoint.y())/2)
            textItem = self.scene.addSimpleText(train.fullCheci())
            w,h = textItem.boundingRect().width(),textItem.boundingRect().height()
            # 车次统一标在左侧
            textItem.setPos(cx-w,cy-h/2)
            self._adjustCheciItem(textItem,startPoint,endPoint)
            last_point = endPoint
            dir_down = (endPoint.y()>startPoint.y())

            # 始发站时刻标签
            textItem = self.scene.addSimpleText(train.timetable[0]['ddsj'].strftime('%H:%M'))
            w,h = textItem.boundingRect().width(),textItem.boundingRect().height()
            # 始发时刻标在右侧，终到时刻标在左侧
            scale = 1 if dir_down else 0  # 垂直位置系数
            textItem.setX(startPoint.x())
            textItem.setY(startPoint.y()-scale*h)
            self._adjustTimeItem(textItem,-2*scale+1)

            # 终到时刻
            textItem = self.scene.addSimpleText(train.timetable[-1]['cfsj'].strftime('%H:%M'))
            w, h = textItem.boundingRect().width(), textItem.boundingRect().height()
            textItem.setX(endPoint.x()-w)
            textItem.setY(endPoint.y() - (1-scale) * h)
            self._adjustTimeItem(textItem,-1+2*scale)

    def _adjustCheciItem(self,textItem:QtWidgets.QGraphicsSimpleTextItem,
                         startPoint:QtCore.QPointF,endPoint:QtCore.QPointF):
        """
        沿着斜线向endPoint方向调整车次标签的位置。必须保证垂直方向不越界。
        """
        minY=min((startPoint.y(),endPoint.y()))
        maxY=max((startPoint.y(),endPoint.y()))
        w,h = textItem.boundingRect().width(),textItem.boundingRect().height()
        if endPoint.x() == startPoint.x():
            # 斜率不存在的特殊情况
            dx=0
            dy=h
        elif endPoint.y() == startPoint.y():
            # k=0的特殊情况
            dy=h
            dx=w
        else:
            k = (endPoint.y()-startPoint.y())/(endPoint.x()-startPoint.x())
            dy=h
            dx = dy/k
        if endPoint.y() < startPoint.y():
            dy=-dy;dx=-dx
        x,y = textItem.x(),textItem.y()
        while minY <= y <= maxY:
            for item in textItem.collidingItems():
                if isinstance(item,QtWidgets.QGraphicsSimpleTextItem):
                    x+=dx
                    y+=dy
                    textItem.setPos(x,y)
                    break
            else:
                break

    def _adjustTimeItem(self,textItem:QtWidgets.QGraphicsSimpleTextItem,scale:int):
        """
        向远离运行线的方向调整冲突的始发终到时刻标签的位置。scale为正负1，表示移动方向。
        """
        w,h = textItem.boundingRect().width(),textItem.boundingRect().height()
        y=textItem.y()
        dy=h*scale
        while 0<=y<=self.sizes["height"]-h:
            for item in textItem.collidingItems():
                if isinstance(item,QtWidgets.QGraphicsSimpleTextItem):
                    y+=dy
                    textItem.setY(y)
                    break
            else:
                break

    def _setVLines(self):
        """
        画每一日的分界线，同时决定宽度。
        """
        # 第一日的左线，贯穿。
        l = self.scene.addLine(self.sizes["left"],0,self.sizes["left"],self.sizes["height"])
        pen = QtGui.QPen()
        pen.setWidthF(1.1)
        l.setPen(pen)

        for day in range(self.maxDay+1):
            x = (day+1)*self.sizes["dayWidth"]+self.sizes["left"]
            # 给出每一日的右线
            l = self.scene.addLine(x,self.sizes["top"],x,self.sizes["height"]-self.sizes["bottom"])
            l.setPen(pen)
            # 在每一日的右线上方左侧给出天数标号
            text = self.scene.addText(str(day))
            w,h = text.boundingRect().width(),text.boundingRect().height()
            text.setPos(x-w,self.sizes["top"]-h)

        self.sizes["totalWidth"] = (self.maxDay+1)*self.sizes["dayWidth"]+\
                                   self.sizes["left"]+self.sizes["right"]

    def _setHLines(self):
        fromTop=True
        self.stationYValues.clear()
        self.topNext = self.sizes["top"]
        self.bottomNext = self.sizes["height"] - self.sizes["bottom"]
        for data in self.datas:
            train:Train = data['node'].train()
            start_station = train.sfz
            end_station = train.zdz
            if fromTop:
                topStation,bottomStation = start_station,end_station
            else:
                topStation,bottomStation = end_station,start_station
            try:
                self.stationYValues[topStation]
            except KeyError:
                self.stationYValues[topStation] = self.topNext
                self.topNext += self.sizes["stationDistance"]
                self._addStationLine(topStation, self.stationYValues[topStation])
            try:
                self.stationYValues[bottomStation]
            except KeyError:
                # 对于大于30分钟的，排列在异侧。否则认为是出库一类的小交路，排列在同侧（都是顶部）
                if train.totalMinTime() >= 1800:
                    self.stationYValues[bottomStation] = self.bottomNext
                    self.bottomNext -= self.sizes["stationDistance"]
                    self._addStationLine(bottomStation,self.stationYValues[bottomStation])
                else:
                    self.stationYValues[bottomStation] = self.topNext
                    self.topNext += self.sizes["stationDistance"]
                    self._addStationLine(bottomStation, self.stationYValues[bottomStation])
                    fromTop = not fromTop
            fromTop = not fromTop

    def _addStationLine(self,station,y):
        maxX = self.sizes["totalWidth"] - self.sizes["right"]
        self.scene.addLine(self.sizes["left"], y,maxX, y)
        textItem1 = self.scene.addSimpleText(station)
        w, h = textItem1.boundingRect().width(), textItem1.boundingRect().height()
        textItem1.setPos(self.sizes["left"] - w-5, y - h // 2)

    def _posCalculate(self,station:str,day:int,tm:datetime)->QtCore.QPointF:
        """
        计算station,day,time所指定的点。保证station存在于self.stationYValue中。
        """
        y = self.stationYValues[station]
        x = self.sizes["left"]
        x+=day*self.sizes["dayWidth"]
        dt:timedelta = tm-datetime(1900,1,1,0,0,0)
        sec:int = dt.seconds
        x += sec/(3600*24)*self.sizes["dayWidth"]
        return QtCore.QPointF(x,y)

    def multiDayByTimetable(self)->bool:
        return self._multiDayByTimetable

    def setMultiDayByTimetable(self,on:bool):
        self._multiDayByTimetable = on
        self.transData()
        self.initUI()

    def setDayWidth(self,w:int):
        self.sizes["dayWidth"] = w
        self.initUI()

    def setHeight(self,h:int):
        self.sizes["height"] = h
        self.initUI()

    def outPixel(self,filename:str)->bool:
        image = QtGui.QImage(self.scene.width(), self.scene.height() + 200, QtGui.QImage.Format_ARGB32)
        image.fill(Qt.white)
        self.renderDiagram(image)
        flag = image.save(filename)
        return flag

    def outVector(self,filename:str)->bool:
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
        printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        size = QtCore.QSize(self.scene.width(), self.scene.height() + 200)
        pageSize = QtGui.QPageSize(size)
        printer.setPageSize(pageSize)
        return self.renderDiagram(printer)

    def renderDiagram(self,img:QtGui.QPaintDevice)->bool:
        painter = QtGui.QPainter()
        painter.begin(img)
        if not painter.isActive():
            return False
        painter.scale(img.width() / self.scene.width(), img.width() / self.scene.width())
        font = QtGui.QFont()
        font.setPixelSize(20)
        painter.setFont(font)
        self.scene.render(painter, target=QtCore.QRectF(0, 100, self.scene.width()+30, self.scene.height()))
        painter.drawText(self.sizes["left"],40, f"{self.circuit.name()}交路示意图")
        painter.drawText(self.sizes["left"],70,f"在运行图{self.graph.lineName()}上")
        h = self.scene.height()+200
        painter.drawText(self.sizes["left"],h-70,f"{self.circuit.model()}型 {self.circuit.owner()}担当 备注：{self.circuit.note()}")
        painter.drawText(self.sizes["left"],h-40,f"{self.circuit.orderStr()}")
        painter.drawText(self.scene.width()-400,h-20,f"由pyETRC列车运行图系统{self.graph.sysVersion()}导出")
        return True


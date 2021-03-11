"""
车站股道占用情况可视化图表。
2019.07.07注意：本模块时间皆归一化到2000-1-1。
1900-1-1是时间戳起点，再往前减会出问题。

2020年1月24日新增对手动录入数据的支持。注意事项
1. 新增_manual参数，决定是否按照手动录入的数据铺排股道。如果是手动模式，则优先铺画所有给了股道的车次，其他的按照【单线】【允许正线停车】模式安排。手动模式下，所有数据都保存在down_list中，up_list无用。
2. 新增股道命名和排序。命名由down_names和up_names决定，其元素一一对应到down_list和up_list中，表示该股道的名称；新增track_order，保存股道名称（str）列表，是从上到下的股道名称表。新增down_map和up_map，记录股道名称和对应的编号。
3. 重新设计UI。增加上层的HBoxLayout级别，选项放在左侧。

注意：track的默认值是空串，不是None！
"""

import sys
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .data.graph import Graph,Train,Circuit
from datetime import datetime,timedelta
from typing import Dict
from .pyETRCExceptions import *

class StationGraphWidget(QtWidgets.QGraphicsView):
    # enum constants for stop type, judged when make_list.
    Stop = 0x0
    Pass = 0x1
    Link = 0x2  # 接续交路间的贯穿线
    Departure = 0x3  # 无接续的始发
    Destination = 0x4  # 无接续的终到
    def __init__(self,station_list,graph:Graph,station_name,init_tracks,mainWindow):
        """
        :param station_list see:
        >>> graph.stationTimeTable(station_name)
        station_list由graph.stationTimetable给出。
        list<dict>
        dict{
            "station_name":str,
            "ddsj":datetime,
            "cfsj":datetime,
            "down":bool,
            "train":Train,
            "type":enum[int],
        }
        """
        super().__init__()
        self.scene = QtWidgets.QGraphicsScene()
        self.station_name = station_name
        mainWindow.stationVisualizeChanged.connect(self._repaint)
        self.seconds_per_pix = 15
        self.row_height = 40
        self.down_list = []
        self.up_list = []
        # 新增：股道名称的定义、股道顺序的规定
        self.down_names = []
        self.up_names = []
        self.track_order = []
        self.single_map = {}  # type: Dict[str,int] # 股道名称映射到down_list中的序号。
        self.single_list = []
        self.single_names = []
        self.margins = {
            "left": 60,
            "right": 20,
            "top": 50,
            "bottom": 50
        }
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        self.graph = graph

        self._doubleLine = False  # 按双线铺画
        self._allowMainStay = True  # 正线停车准许
        self._manual = True  # 手动模式。使用录入的股道数据
        self._sameSplitTime = 0  # 单位：分钟
        self._oppositeSplitTime = 0

        self.station_list = station_list
        if init_tracks:
            self._parseInitTrackOrder(init_tracks)
        self.msg = []  # 警告信息
        self._makeList()
        # 初始化时，对股道做一次自动排序，但以后不按照这个。
        if not init_tracks:
            self.track_order.sort()
        self._initUI()

    def allowMainStay(self):
        return self._allowMainStay

    def setAllowMainStay(self,allow:bool):
        self._allowMainStay = allow

    def setManual(self,manual:bool):
        self._manual = manual
        if manual:
            self._allowMainStay=True
            self._doubleLine=False

    def doubleLine(self):
        return self._doubleLine

    def setDoubleLine(self,isDouble:bool):
        if isDouble == self._doubleLine:
            return
        self._doubleLine=isDouble

    def sameSplitTime(self):
        return self._sameSplitTime

    def setSameSplitTime(self,minute):
        self._sameSplitTime = minute

    def oppositeSplitTime(self):
        return self._oppositeSplitTime

    def setOppositeSplitTime(self,minute):
        self._oppositeSplitTime = minute

    def repaintGraphAdvanced(self):
        if self._manual: # 手动模式下保留股道但清空所有信息
            for lst in self.down_list+self.up_list+self.single_list:
                lst.clear()
        else: # 自动模式下删除所有股道信息
            self.down_list.clear()
            self.up_list.clear()
            self.single_list.clear()
            self.single_map.clear()
            self.down_names.clear()
            self.up_names.clear()
            self.track_order.clear()
        self._makeList()
        self._initUI()

    def _repaint(self,seconds_per_pix:int=-1):
        if seconds_per_pix != -1:
            self.seconds_per_pix = seconds_per_pix
        self._initUI()

    def _makeList(self):
        """
        将数据分别放入list中. 数据准备.
        list<dict>
        dict{
            "ddsj":datetime,
            "cfsj":datetime,
            "down":bool,
            "train":Train,
        }
        2019.06.24处理bug: 在0:00前后半分钟内通过的列车引起问题。解决方案：先将通过者处理成1分钟，
        再处理跨日。在train_dict中新增关于是否是通过的判据。
        2020.01.25注：
        只有两处调用，即初始化和重新铺画。调用前，应当已经初始化好股道信息。
        若是初始调用或者自动重新铺画，则股道表全空；若是手动重新铺画，则股道表为所设置的股道表。
        """
        if self._manual:
            self._allowMainStay=True
            self._doubleLine=False
        # self.down_list = []  # 下行股道表，每个元素（list）是一个股道的占用次序。
        # self.up_list = []
        # self.single_list = []
        self.msg.clear()

        newlist = []
        toDeleteTrains = []  # 要删除的列车。是因为接续而被删除的对象。保存原来的train对象。

        # 第一轮处理，删除要删除的，调整有关的类型，归一化日期。
        for train_dict in self.station_list:
            try:
                train_dict['type']
            except KeyError:
                # 首先判断是否是需要删除的。
                train:Train = train_dict['train']
                if train in toDeleteTrains:
                    toDeleteTrains.remove(train)
                    continue
                if not self._judgeType(train_dict,toDeleteTrains):
                    continue
            else:
                # 已经添加好，不必再处理
                pass
            # 将日期归一化到2000-1-1
            # datetime.date().replace()不能有效改变日期
            o:datetime = train_dict['ddsj']
            train_dict["ddsj"]=datetime(2000,1,1,o.hour,o.minute,o.second)
            o: datetime = train_dict['cfsj']
            train_dict["cfsj"]=datetime(2000,1,1,o.hour,o.minute,o.second)
            newlist.append(train_dict)
        self.station_list = newlist

        # 第二轮，跨日处理，铺画
        for train_dict in self.station_list:
            if train_dict["cfsj"] < train_dict["ddsj"]:
                # 跨日处理
                new_dict = {
                    "ddsj":datetime(2000,1,1,0,0,0),
                    "cfsj":train_dict["cfsj"],
                    "down":train_dict["down"],
                    "train":train_dict["train"],
                    "station_name":train_dict["station_name"],
                    "type":train_dict['type'],
                    "track":train_dict['track'],
                }
                print("跨日处理，新增",new_dict)
                # print("addNewDict",new_dict)
                train_dict["cfsj"] = datetime(2000, 1, 1, 23, 59, 59)
                self.station_list.append(new_dict)
            if self._isPassed(train_dict):
                self._addPassTrain(train_dict)
            else:
                self._addStopTrain(train_dict)
        self._autoTrackNames()
        self._autoTrackOrder()

    def _parseInitTrackOrder(self,tracks:list):
        """
        仅在初始化调用，解析股道顺序表。
        保证所有的表都是空的。
        """
        for t in tracks:
            self.single_names.append(t)
            self.track_order.append(t)
            self.single_list.append([])
            self.single_map[t] = len(self.single_names)-1

    def _autoTrackNames(self):
        """
        2020.01.24新增。
        自动股道名称。初始化调用一次。不管股道顺序。
        手动模式下做补充，自动模式下分单双线铺画。
        """
        if self._manual:
            # 下行
            for i in range(len(self.single_list)-len(self.single_names)):
                name = self._validNewTrackName(i + 1)
                self.single_names.append(name)
        else:
            if self._doubleLine:
                self.down_names.clear()
                self.down_names.extend([str(2*i+1) for i in range(len(self.down_list))])
                self.up_names.clear()
                self.up_names.extend([str(2*i+2) for i in range(len(self.up_list))])
                if self.down_names:
                    self.down_names[0] = 'Ⅰ'
                if self.up_names:
                    self.up_names[0] = 'Ⅱ'
            else:
                # 单线模式
                self.single_names.clear()
                self.single_names.extend([str(i+1) for i in range(len(self.single_list))])
                if self.single_names:
                    self.single_names[0] = 'Ⅰ'

    def _validNewTrackName(self, i=0)->str:
        """
        返回一个合法的股道名。仅在手动模式下启用。
        """
        name = f"A{i}"
        while name in self.single_names:
            i+=1
            name = f"A{i}"
        return name

    def _autoTrackOrder(self):
        """
        2020.01.24新增。
        自动股道顺序。遍历一遍股道名称表，添加进去。
        """
        if self._manual:
            # 手动模式下，仅作追加和排序，并且仅考虑单线
            for name in self.single_names:
                if name not in self.track_order:
                    self.track_order.append(name)
            # 是否排序？排序放在哪里？
        else:
            self.track_order.clear()
            if self._doubleLine:
                self.track_order.extend(reversed(self.down_names))
                self.track_order.extend(self.up_names)
            else:
                self.track_order.extend(self.single_names)


    def _judgeType(self,train_dict:dict,toDeleteTrains:list)->bool:
        """
        返回是否保留本车次。
        """
        train = train_dict['train']
        # 始发情况处理
        if self.station_name == train.sfz:
            circuit = train.carriageCircuit()
            if circuit is not None:
                preTrain, preTime = circuit.preorderLinked(train)
                if preTrain is not None:
                    # 是一个接续的后车，创建一个虚拟的车次，删除前车和本车。方向由后车给出。
                    toDeleteTrains.append(preTrain)
                    ntrain = Train(self.graph, f"{preTrain.fullCheci()}-{train.fullCheci()}")
                    dct = {
                        "ddsj": preTime,
                        "cfsj": train_dict['cfsj'],
                        "down": train_dict['down'],
                        "train": ntrain,
                        "type": self.Link,
                        "track":train_dict['track'],  # 出发车决定股道
                        "station_name":train_dict['station_name'],
                    }
                    # print("新增临时车次！", ntrain)
                    self.station_list.append(dct)
                    return False
            train_dict['type'] = self.Departure

        # 终到站处理
        elif self.station_name == train.zdz:
            circuit = train.carriageCircuit()
            if circuit is not None:
                postTrain, postTime = circuit.postorderLinked(train)
                if postTrain is not None:
                    # 是一个接续的前车，创建一个虚拟的车次，删除后车和本车。方向由后车给出。
                    toDeleteTrains.append(postTrain)
                    ntrain = Train(self.graph, f"{train.fullCheci()}-{postTrain.fullCheci()}")
                    # print("新增临时车次！",ntrain)
                    dct = {
                        "ddsj": train_dict['ddsj'],
                        "cfsj": postTime,
                        "down": postTrain.stationDown(self.station_name),
                        "train": ntrain,
                        "type": self.Link,
                        "track": postTrain.stationTrack(self.station_name),
                        "station_name":postTrain.sfz,
                    }
                    self.station_list.append(dct)
                    return False
            train_dict['type'] = self.Destination
        else:
            if train_dict['ddsj'] == train_dict['cfsj']:
                train_dict['type'] = self.Pass
            else:
                train_dict['type'] = self.Stop
        return True

    def _isPassed(self,train_dict)->bool:
        """
        2019.06.26注明：功能改变。
        只决定是否需要将时刻延拓为1分钟。
        """
        if (train_dict["ddsj"]-train_dict["cfsj"]).seconds == 0:
            return True
        else:
            return False

    def _getTrackIndex(self,name:str)->int:
        """
        2020.01.24新增，
        根据股道名称返回股道编号（在下行股道序列中），如果没有这条股道的数据则做好新建工作。
        """
        idx = self.single_map.get(name,None)
        if idx is not None:
            return idx
        # 新建股道
        self.single_map[name] = len(self.single_list)
        self.single_names.append(name)
        self.single_list.append([])
        self.track_order.append(name)
        return len(self.single_list)-1

    def _addPassTrain(self,train_dict):
        down = train_dict["down"]
        added = False
        if self._manual and train_dict.get("track"):
            # 按手动添加车次
            track_name = train_dict['track']
            track_index = self._getTrackIndex(track_name)
            track = self.single_list[track_index]
            if not self._isIdle(track,train_dict):
                self.msg.append(f"通过时刻冲突：车次{train_dict['train'].fullCheci()}, "
                                f"时刻{train_dict['ddsj'].strftime('%H:%M:%S')}, 股道{track_name}")
            track.append(train_dict)
        elif self._doubleLine:
            # 双线铺画
            if down:
                for i,rail in enumerate(self.down_list):
                    if self._isIdle(rail,train_dict):
                        rail.append(train_dict)
                        added = True
                        break
                if not added:
                    new_rail = [train_dict,]
                    self.down_list.append(new_rail)
            else:
                for i,rail in enumerate(self.up_list):
                    if self._isIdle(rail,train_dict):
                        rail.append(train_dict)
                        added = True
                        break
                if not added:
                    new_rail = [train_dict,]
                    self.up_list.append(new_rail)
        else:
            # 单线铺画
            for i,rail in enumerate(self.single_list):
                if self._isIdle(rail,train_dict):
                    rail.append(train_dict)
                    added = True
                    break
            if not added:
                new_rail = [train_dict,]
                self.single_list.append(new_rail)

    def _addStopTrain(self,train_dict):
        down = train_dict["down"]
        added = False
        if self._manual and train_dict.get("track"):
            idx = self._getTrackIndex(train_dict['track'])
            track = self.single_list[idx]
            if not self._isIdle(track,train_dict):
                self.msg.append(f"停车时刻冲突：车次{train_dict['train'].fullCheci()}, "
                                f"时刻{train_dict['ddsj'].strftime('%H:%M:%S')}-"
                                f"{train_dict['cfsj'].strftime('%H:%M:%S')}, 股道{train_dict.get('track')}")
            track.append(train_dict)
        elif self._doubleLine:
            #双线铺画
            if down:
                for i, rail in enumerate(self.down_list):
                    if not self._allowMainStay and i == 0:
                        continue
                    if self._isIdle(rail, train_dict):
                        rail.append(train_dict)
                        added = True
                        break
                if not added:
                    new_rail = [train_dict, ]
                    self.down_list.append(new_rail)
            else:
                for i, rail in enumerate(self.up_list):
                    if not self._allowMainStay and i == 0:
                        continue
                    if self._isIdle(rail, train_dict):
                        rail.append(train_dict)
                        added = True
                        break
                if not added:
                    new_rail = [train_dict, ]
                    self.up_list.append(new_rail)
        else:
            #单线铺画
            for i, rail in enumerate(self.single_list):
                if not self._allowMainStay and i == 0:
                    continue
                if self._isIdle(rail, train_dict):
                    rail.append(train_dict)
                    added = True
                    break
            if not added:
                new_rail = [train_dict, ]
                self.single_list.append(new_rail)

    def _isIdle(self,rail:list,new_train):
        ddsj,cfsj = self._occupyTime(new_train)
        for train_dict in rail:
            arrive,depart = self._occupyTime(train_dict)  # 已经占用的时间
            if new_train["down"] == train_dict["down"]:
                # 同向车次，扣去同向间隔
                dt = timedelta(days=0,seconds=self._sameSplitTime*60)
            else:
                dt = timedelta(days=0, seconds=self._oppositeSplitTime * 60)
            if (ddsj >= (arrive-dt) and ddsj <= (depart+dt)) or (cfsj >= (arrive-dt) and cfsj <= (depart+dt)):
                return False
        return True

    def _occupyTime(self,new_train:dict):
        if self._isPassed(new_train):
            if new_train['ddsj'] < datetime(2000,1,1,0,0,30):
                ddsj = datetime(2000,1,1,0,0,0)
            else:
                ddsj = new_train["ddsj"] - timedelta(days=0,seconds=30)
            if new_train['cfsj'] > datetime(2000,1,1,23,59,29):
                cfsj = datetime(2000,1,1,23,59,59)
            else:
                cfsj = new_train["cfsj"] + timedelta(days=0,seconds=30)
        else:
            ddsj = new_train["ddsj"]
            cfsj = new_train["cfsj"]
        ddsj = datetime(2000,1,1,ddsj.hour,ddsj.minute,ddsj.second)
        cfsj = datetime(2000,1,1,cfsj.hour,cfsj.minute,cfsj.second)
        return ddsj,cfsj

    def _initUI(self):
        self.scene.clear()
        gridColor = QtGui.QColor("#00FF00")
        defaultPen = QtGui.QPen(QtGui.QColor("#00FF00"),1)
        boldPen = QtGui.QPen(QtGui.QColor("#00FF00"),2)
        width = 24*3600/self.seconds_per_pix
        down_count = len(self.down_list)
        up_count = len(self.up_list)
        single_count = len(self.single_list)
        if self._doubleLine:
            height = self.row_height*(down_count+up_count)
        else:
            height = self.row_height*(single_count)
        self.scene.setSceneRect(0,0,self.margins["left"]+self.margins["right"]+width,
                                self.margins["top"]+self.margins["bottom"]+height)
        rectItem = self.scene.addRect(self.margins["left"],self.margins["top"],
                                      width,height)
        rectItem.setPen(defaultPen)

        self._initXAxis(width,height,gridColor)
        self._initYAxis(width,defaultPen,boldPen)
        self._addTrains()

    def _initXAxis(self,width,height,gridColor):
        pen_half = QtGui.QPen(gridColor, 1, Qt.DashLine)
        pen_hour = QtGui.QPen(gridColor, 2)
        pen_other = QtGui.QPen(gridColor, 1)

        lineItem = self.scene.addLine(self.margins["left"] - 15, 35, width + self.margins["left"] + 15, 35)
        lineItem.setPen(pen_hour)

        lineItem = self.scene.addLine(self.margins["left"] - 15, self.margins["top"]+height+15,
                                      width + self.margins["left"] + 15, self.margins["top"]+height+15)
        lineItem.setPen(pen_hour)


        for i in range(25):

            x = self.margins["left"] + i * 3600 / self.seconds_per_pix
            hour = i

            textItem1:QtWidgets.QGraphicsTextItem = self.scene.addText(str(hour))
            textItem2: QtWidgets.QGraphicsTextItem = self.scene.addText(str(hour))
            textItem1.setX(x-12)
            textItem1.setDefaultTextColor(gridColor)

            #下时间坐标
            textItem2.setX(x - 12)
            textItem2.setY(self.scene.height()-30)
            textItem2.setDefaultTextColor(gridColor)

            if i == 24:
                break

            # 画小时线，第一个不用画
            if i != 0:
                self.scene.addLine(x,self.margins["top"],x,self.margins["top"] + height,pen_hour)

            for j in range(1,6):
                x += 10*60/self.seconds_per_pix
                if j*10 == 30:
                    self.scene.addLine(x, self.margins["top"], x, self.margins["top"] + height, pen_half)
                else:
                    self.scene.addLine(x, self.margins["top"], x, self.margins["top"] + height, pen_other)

    def _initYAxis(self,width,defaultPen,boldPen):
        # if self._doubleLine:
        #     down_count = len(self.down_list)
        #     up_count = len(self.up_list)
        #     for i in range(down_count):
        #         y = self.margins["top"]+(i+1)*self.row_height
        #         lineItem = self.scene.addLine(self.margins["left"],self.margins["top"]+(i+1)*self.row_height,
        #                                       self.margins["left"]+width,self.margins["top"]+(i+1)*self.row_height)
        #         if i == down_count-1:
        #             lineItem.setPen(boldPen)
        #         else:
        #             lineItem.setPen(defaultPen)
        #         rail_num = 2*down_count - 1 - 2*i
        #         textItem:QtWidgets.QGraphicsTextItem = self.scene.addText(str(rail_num)if rail_num != 1 else 'Ⅰ')
        #         textItem.setY(y-self.row_height/2-textItem.boundingRect().height()/2)
        #
        #     for i in range(up_count):
        #         y = self.margins["top"]+(i+1)*self.row_height + down_count*self.row_height
        #         if i != up_count - 1:
        #             lineItem = self.scene.addLine(self.margins["left"], y,
        #                                           self.margins["left"] + width, y)
        #             lineItem.setPen(defaultPen)
        #
        #         rail_num = 2*i+2
        #         textItem: QtWidgets.QGraphicsTextItem = self.scene.addText(str(rail_num) if rail_num != 2 else 'Ⅱ')
        #         textItem.setY(y - self.row_height / 2 - textItem.boundingRect().height() / 2)
        # else:
        #     #单线铺画
        #     single_count = len(self.single_list)
        #     for i in range(single_count):
        #         y = self.margins["top"] + (i + 1) * self.row_height
        #
        #         lineItem = self.scene.addLine(self.margins["left"], y,
        #                                       self.margins["left"] + width, y)
        #         lineItem.setPen(defaultPen)
        #
        #         rail_num = i+1
        #         textItem: QtWidgets.QGraphicsTextItem = self.scene.addText(str(rail_num) if rail_num != 1 else 'Ⅰ')
        #         textItem.setY(y - self.row_height / 2 - textItem.boundingRect().height() / 2)
        for i,name in enumerate(self.track_order):
            y = self.margins["top"] + (i+1)*self.row_height
            lineItem = self.scene.addLine(self.margins["left"],y,
                                          self.margins["left"]+width,y)
            lineItem.setPen(defaultPen)
            textItem:QtWidgets.QGraphicsTextItem = self.scene.addText(name)
            textItem.setY(y - self.row_height / 2 - textItem.boundingRect().height() / 2)

    def _addTrains(self):
        start_y = self.margins["top"]
        # if self._doubleLine:
        #     for down_rail in reversed(self.down_list):
        #         for train_dict in down_rail:
        #             self._addTrainRect(train_dict,start_y)
        #
        #         start_y += self.row_height
        #
        #     for up_rail in self.up_list:
        #         for train_dict in up_rail:
        #             self._addTrainRect(train_dict, start_y)
        #
        #         start_y += self.row_height
        # else:
        #     for single_rail in self.single_list:
        #         for train_dict in single_rail:
        #             self._addTrainRect(train_dict,start_y)
        #         start_y += self.row_height
        for rail_name in self.track_order:
            rail = self._railListByName(rail_name)
            for train_dict in rail:
                self._addTrainRect(train_dict,start_y)
            start_y+=self.row_height

    def _railListByName(self,name:str)->list:
        """
        根据股道名返回对应的数据。2020.01.24新增。
        """
        if self._doubleLine:
            if name in self.down_names:
                # 是下行
                return self.down_list[self.down_names.index(name)]
            return self.up_list[self.up_names.index(name)]
        return self.single_list[self.single_names.index(name)]


    def _addTrainRect(self,train_dict,start_y):
        ddsj, cfsj = self._occupyTime(train_dict)
        dd_x = self._xValueCount(ddsj)
        cf_x = self._xValueCount(cfsj)
        train = train_dict["train"]
        color = QtGui.QColor(train.color(self.graph))
        width = cf_x - dd_x
        rectItem: QtWidgets.QGraphicsRectItem = self.scene.addRect(dd_x, start_y, width, self.row_height)
        rectItem.setBrush(QtGui.QBrush(color))

        text = f"{train.fullCheci()} {Train.downStr(train_dict['down'])} "
        if train_dict['type'] == self.Pass:
            text += f"通过  {(train_dict['ddsj']).strftime('%H:%M:%S')}"
        elif train_dict['type'] == self.Departure:
            text += f"始发  {(train_dict['ddsj']).strftime('%H:%M:%S')}"
        elif train_dict['type'] == self.Destination:
            text += f"终到  {(train_dict['ddsj']).strftime('%H:%M:%S')}"
        elif train_dict['type'] == self.Stop:
            text += f"停车  {ddsj.strftime('%H:%M:%S')} — {cfsj.strftime('%H:%M:%S')}"
        else:
            # 接续
            text = f"交路接续 {train.fullCheci()} {ddsj.strftime('%H:%M:%S')} — {cfsj.strftime('%H:%M:%S')}"
        if self._manual and train_dict.get("track"):
            text = '[图定股道] '+text
        else:
            text = '[推定股道] '+text
        text += f" {train_dict['station_name']}"
        rectItem.setToolTip(text)

    def _xValueCount(self,time:datetime):
        dt_int = (time-datetime(2000,1,1,0,0,0)).seconds
        dx = dt_int/self.seconds_per_pix
        return dx + self.margins["left"]
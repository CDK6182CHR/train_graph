"""
列车信息模块
时间统一使用：datetime.datetime实例
2019.04.27修改计划：
1. 在列车数据中新增“旅客列车”参数，严格判定是否为旅客列车。增加到currentWidget中。注意，使用checkBox时允许中间状态，即由系统自动判定。默认是这种状态。ok
2. 在列车时刻表数据每一行新增“营业”字段，标记是否办理业务。在currentWidget中新增按钮自动设置所有站是否办理业务。默认全为True。同时修改ctrl+2功能中的筛选条件。
3. 取消Train中所有依据Timetable_new.utility判定类型、判定是否为客车的逻辑，此操作改为需要graph介入。ok
4. 新增类型映射表。规定一系列的列车种类名称，是否属于旅客列车，对应的车次正则表达式。作为系统默认数据中的一项，也作为graph中的数据。判定是否为客车的逻辑，经由此处。此项数据在车次的类型设置为空时生效；在全局新增自动设置所有列车类型操作。ok
5. 在线路基数据中新增两个字段“默认办客”“默认办货”。此项数据在第2条所述的自动设置以及标尺排图时生效。ok
"""
from Timetable_new.checi3 import Checi
from datetime import datetime, timedelta
from Timetable_new.utility import judge_type, stationEqual, strToTime
import re, bisect, warnings
from typing import Iterable, Union
from .circuit import Circuit
from ..pyETRCExceptions import *
from enum import Enum
from typing import List, Dict, Union
from .trainstation import TrainStation

import cgitb

cgitb.enable(format='text')


class Train():
    """
    列车信息类，数据结构：
    Graph& graph;//2.0.2开始新增，对graph的引用
    List<Str> checi;
    Str sfz,zdz;
    Str type;
    List<Dict> timetable;
    Dict UI; #显示设置，如线形，颜色等
    bool down;//本线的上下行 取消
    int _passenger;//是否客车, 用常量表达. 常量正好对应Qt中的CheckState。
    QtWidgets.QGraphicsViewPathItem pathItem;
    QtWidgets.QGraphicsViewItem labelItem;

    Timetable 中Dict数据结构：
    dict = {
            "zhanming":name,
            "ddsj":ddsj,
            "cfsj":cfsj,
            "business":bool,  //是否办理业务。新增
            "track":str,  //股道。任何非空表示有数据。
        }
    items 中数据结构：
    dict{
        start:开始站，
        end:结束站，
        down:下行，
        show:显示，
        show_start_label:开始标记bool
        show_end_label:结束标记bool
    }
    """
    PassengerFalse = 0
    PassengerAuto = 1
    PassengerTrue = 2

    def __init__(self, graph, checi_full='', checi_down='', checi_up='', sfz='', zdz='',
                 origin=None, passenger=PassengerAuto):
        self.item = None
        self.graph = graph
        self._items = []
        self._itemInfo = []
        self._autoItem = True
        # self.down = None
        self.shown = True  # 是否显示运行线
        self._localFirst = None
        self._localLast = None
        self._yToStationMap = []  # 数据结构：List<tuple<float,dict>>
        self._passenger = passenger
        self._carriageCircuitName = None
        self._carriageCircuit = None
        self._nameToIndexMap = None  # type: Dict[str,List[int]]  # 临时的随机访问工具
        if origin is not None:
            # 从既有字典读取数据
            self.loadTrain(origin)
        else:
            self.checi = [checi_full, checi_down, checi_up]
            self.type = ''
            self.timetable = []
            self.sfz = sfz
            self.zdz = zdz
            self.UI = {}
            print("新车次", self.checi)

            if not checi_down and not checi_up and checi_full:
                # 没有给出上下行车次，重新拆分初始化
                tempcheci = Checi(checi_full)
                self.checi[1] = tempcheci.down
                self.checi[2] = tempcheci.up
                self.type = tempcheci.type
            # self.autoType()  # 取消
            # self._autoUI()

    def enableRandomAccess(self):
        """
        启用临时的站名->index随机访问映射。
        """
        self._nameToIndexMap = {}
        for i, dct in enumerate(self.timetable):
            self._nameToIndexMap.setdefault(dct['zhanming'], []).append(i)

    def disableRandomAccess(self):
        self._nameToIndexMap = None

    def loadTrain(self, origin):
        self.checi = origin["checi"]
        self.UI = origin["UI"]
        self.timetable = origin["timetable"]
        self.type = origin["type"]
        self.sfz = origin["sfz"]
        self.zdz = origin["zdz"]
        self._localFirst = origin.get('localFirst', None)
        self._localLast = origin.get('localLast', None)
        self._itemInfo = origin.get("itemInfo", [])
        self._autoItem = origin.get("autoItem", True)
        self._passenger = origin.get("passenger", True)
        self._carriageCircuitName = origin.get("carriageCircuit", None)

        try:
            origin["shown"]
        except KeyError:
            self.shown = True
        else:
            self.shown = origin["shown"]

        self._transfer_time()
        # 如果UI为空，自动初始化
        if not self.type:
            pass
            # self.autoType()
        if not self.UI:
            pass
            # self._autoUI()

    def _transfer_time(self):
        """
        将读取到的时刻中的时间转为datetime.datetime对象
        """
        for i in range(len(self.timetable)):
            dct = self.timetable[i]
            if isinstance(dct["ddsj"], str):
                ddsj = strToTime(dct['ddsj'])
                cfsj = strToTime(dct['cfsj'])
                dct["ddsj"] = ddsj
                dct["cfsj"] = cfsj
            self.timetable[i] = TrainStation(dct)

    def setType(self, type: str):
        self.type = type

    def autoTrainType(self) -> str:
        """
        2.0.2新增，调用graph获得自动类型。取代autoType函数。
        """
        self.setType(self.graph.checiType(self.fullCheci()))
        return self.type

    def fullCheci(self):
        return self.checi[0]

    def downCheci(self):
        return self.checi[1]

    def upCheci(self):
        return self.checi[2]

    def getCheci(self, down: bool):
        if down:
            return self.checi[1]
        else:
            return self.checi[2]

    def addStation(self, name: str, ddsj, cfsj, *, business=None, auto_cover=False, to_end=True, note='', track=''):
        # 增加站。暂定到达时间、出发时间用datetime类。
        if isinstance(ddsj, str):
            ddsj = strToTime(ddsj)
            cfsj = strToTime(cfsj)

        dct = TrainStation({
            "zhanming": name,
            "ddsj": ddsj,
            "cfsj": cfsj,
            "note": note,
            "track": track,
        })
        if business is None:
            business = self.graph.lineStationBusiness(name,
                                                      self.isPassenger(detect=True),
                                                      default=None) and self.stationStoppedOrStartEnd(dct)
        if business is not None:
            dct['business'] = business
        if auto_cover:
            former_dict = self.stationDict(name)
            if former_dict is not None:
                index = self.timetable.index(former_dict)
                self.timetable[index] = dct
            else:
                if to_end:
                    self.timetable.append(dct)
                else:
                    self.timetable.insert(0, dct)
        else:
            if to_end:
                self.timetable.append(dct)
            else:
                self.timetable.insert(0, dct)

    def setStartEnd(self, sfz='', zdz=''):
        if sfz:
            self.sfz = sfz
        if zdz:
            self.zdz = zdz

    def autoStartEnd(self):
        """
        自动设置始发终到站。使用itemInfo作为判据，而不使用localFirst/Last。
        """
        if not self.timetable:
            return
        first, last = None, None
        for item in self.itemInfo():
            if first is None:
                first = item
            last = item
        firstT, lastT = self.timetable[0]['zhanming'], self.timetable[-1]['zhanming']
        if firstT == first['start'] and re.match(f'{self.sfz}.*?场', firstT):
            self.setStartEnd(sfz=firstT)
        if lastT == last['end'] and re.match(f'{self.zdz}.*?场', lastT):
            self.setStartEnd(zdz=lastT)

    def station_infos(self):
        for st in self.timetable:
            yield st["zhanming"], st["ddsj"], st["cfsj"]

    def color(self, graph=None) -> str:
        """
        graph为None时只取本身设定的颜色。graph为非None时，如果没有设定就返回默认。
        """
        try:
            color_str = self.UI["Color"]
        except KeyError:
            color_str = ''
        if graph is not None and not color_str:
            UIDict = graph.UIConfigData()
            try:
                color_str = UIDict["default_colors"][self.type]
            except:
                color_str = UIDict["default_colors"]["default"]
        return color_str

    def lineWidth(self):
        try:
            return self.UI["LineWidth"]
        except KeyError:
            return 0

    def isShow(self):
        try:
            return self.shown
        except AttributeError:
            self.shown = True
            return True

    def setIsShow(self, show: bool, affect_item=True):
        """
        注意，affect_item只影响True->False情况
        """
        if self.isShow() == show:
            # 未做改动，直接返回
            return
        self.shown = show
        if not affect_item:
            return
        for item in self.items():
            item.setVisible(show)

    def isPassenger(self, detect=False) -> int:
        """
        旅客列车。如果detect=True，则利用graph引用，依据【类型】推定是否为客车。
        """
        if self._passenger != self.PassengerAuto or not detect:
            return self._passenger
        else:
            return self.graph.typePassenger(self.trainType(), default=self.PassengerFalse)

    def setIsPassenger(self, t):
        """
        旅客列车
        """
        self._passenger = t

    def show(self):
        # 调试用
        print(self.checi)
        print(self.sfz, self.zdz)
        print(self.type, self.UI)
        for i, dict in enumerate(self.timetable):
            print(dict["zhanming"], dict["ddsj"], dict["cfsj"])
            if i > 3:
                print("...")
                break

    def outInfo(self):
        # 输出字典结构，仅用于文件
        info = {
            "checi": self.checi,
            "UI": self.UI,
            "type": self.type,
            "timetable": [],
            "sfz": self.sfz,
            "zdz": self.zdz,
            "shown": self.shown,
            "localFirst": self._localFirst,
            "localLast": self._localLast,
            "autoItem": self._autoItem,
            "itemInfo": self._itemInfo,
            "passenger": self._passenger,
            "carriageCircuit": self._carriageCircuit.name() if self._carriageCircuit is not None else \
                self._carriageCircuitName,
        }
        for dct in self.timetable:
            ddsj: datetime = dct["ddsj"]
            cfsj: datetime = dct["cfsj"]
            outDict = {
                "zhanming": dct["zhanming"],
                "ddsj": ddsj.strftime("%H:%M:%S"),
                "cfsj": cfsj.strftime("%H:%M:%S"),
                "note": dct.setdefault('note', ''),
                "track": dct.setdefault('track', '')
            }
            try:
                outDict['business'] = dct['business']
            except KeyError:
                pass
            info["timetable"].append(outDict)
        return info

    def trainType(self):
        return self.type

    def setItem(self, item):
        self.item = item
        if self.item is None:
            self.resetYValueMap()

    def items(self):
        return self._items

    def firstItem(self):
        for item in self._items:
            return item
        return None

    def lastItem(self):
        for item in reversed(self._items):
            return item
        return None

    def takeLastItem(self):
        if self._items:
            return self._items.pop()

    def lastItemInfo(self) -> dict:
        for item in reversed(self._itemInfo):
            return item
        return None

    def itemInfo(self) -> Iterable[dict]:
        for it in self._itemInfo:
            yield it

    def removeItemInfo(self, dct: dict):
        """
        手动铺画情况下调用的。删除无效的铺画区间。直接调用remove即可。
        """
        try:
            self._itemInfo.remove(dct)
        except:
            print("Train::removeItemInfo: remove failed. ")

    def addItemInfoDict(self, info: dict):
        self._itemInfo.append(info)

    def addItem(self, item):
        self._items.append(item)

    def clearItems(self):
        """
        清空item对象但不删除信息
        """
        self._items.clear()

    def clearItemInfo(self):
        self._itemInfo.clear()

    def autoItem(self)->bool:
        return self._autoItem

    def setAutoItem(self, on: bool):
        self._autoItem = on

    def model(self) -> str:
        """
        2019.06.25新增。将车底、担当局段逻辑上也作为Train的只读属性，实际通过circuit调用。
        如果没有交路数据，返回None.
        """
        circuit = self.carriageCircuit()
        if circuit is not None:
            return circuit.model()
        return None

    def owner(self) -> str:
        """
        2019.06.25新增。将车底、担当局段逻辑上也作为Train的只读属性，实际通过circuit调用。
        如果没有交路数据，返回None.
        """
        circuit = self.carriageCircuit()
        if circuit is not None:
            return circuit.owner()
        return None

    def previousCheci(self) -> str:
        """
        前序车次，如果没有，返回空串。此接口提供给trainInfoWidget。
        """
        circuit = self.carriageCircuit()
        if circuit is None:
            return ''
        pr, _ = circuit.preorderLinked(self)
        if pr is not None:
            return pr.fullCheci()
        return '-'

    def nextCheci(self) -> str:
        """
        后序车次，如果没有返回空串。
        """
        circuit = self.carriageCircuit()
        if circuit is None:
            return ''
        nx, _ = circuit.postorderLinked(self)
        if nx is not None:
            return nx.fullCheci()
        return '-'

    def firstDown(self) -> bool:
        """
        返回第一个区间的上下行情况。2.0新增。
        """
        for dct in self.itemInfo():
            return dct["down"]
        return None

    def stationTrack(self, station: str) -> str:
        dct = self.stationDict(station)
        return dct['track']

    def lastDown(self) -> bool:
        """
        本线最后一个区间的上下行情况。2.0新增，主要为了满足jointGraph的需要。
        """
        for dct in reversed(list(self.itemInfo())):
            return dct["down"]
        return None

    def stationDown(self, station: str, graph=None) -> bool:
        """
        2.0新增。返回本车次在某个车站及其左邻域内的上下行情况。
        调用了线性算法。需要依赖于线路上的y_value，这就是说必须保证本站是铺画了的。
        """
        if graph is None:
            graph = self.graph
        idx = self.stationIndexByName(station)
        if idx == -1:
            return None
        y = graph.stationYValue(station)
        if y == -1:
            return None
        # 先向左查找
        leftY = -1
        i = idx
        while i > 0:
            i -= 1
            leftY = graph.stationYValue(self.stationNameByIndex(i))
            if leftY != -1:
                break
        if leftY != -1:
            if leftY < y:
                return True
            return False

        # 如果左边没有了，向右查找
        i = idx
        rightY = -1
        while i < len(self.timetable) - 1:
            i += 1
            rightY = graph.stationYValue(self.stationNameByIndex(i))
            if rightY != -1:
                break
        if rightY != -1:
            if y < rightY:
                return True
            return False
        return None

    def reverseAllItemDown(self):
        """
        2.0新增，转置所有item的上下行。
        """
        for dct in self.itemInfo():
            dct['down'] = not dct['down']

    def stationIndexByName(self, name, strict=False) -> int:
        """
        2.0新增。线性算法。
        """
        if self._nameToIndexMap is not None and strict:
            return self._nameToIndexMap.get(name, [-1])[0]
        for i, st in enumerate(self.timetable):
            if stationEqual(st['zhanming'], name, strict):
                return i
        return -1

    def stationNameByIndex(self, idx: int):
        """
        保证数据有效。
        """
        try:
            return self.timetable[idx]['zhanming']
        except IndexError:
            print("train::stationNameByIndex: index error", idx, len(self.timetable))
            raise Exception("Exception in train.py line 473")

    def setUI(self, color: str = None, width=None):
        if color is not None:
            self.UI["Color"] = color
        if width is not None:
            self.UI["LineWidth"] = width

    def stationTime(self, name: str):
        st = self.stationDict(name)
        if st is None:
            raise Exception("No such station in timetable.")
        return st["ddsj"], st["cfsj"]

    def gapBetweenStation(self, st1, st2, graph=None) -> int:
        """
        返回两站间的运行时间
        :param graph:依赖的线路。不为None表示允许向前后推断邻近站。
        :return: seconds:int
        """
        st_dict1, st_dict2 = None, None
        for dict in self.timetable:
            if stationEqual(st1, dict['zhanming']):
                st_dict1 = dict
            elif stationEqual(st2, dict['zhanming']):
                st_dict2 = dict
        print("detect", self.fullCheci(), st1, st2)
        if st_dict1 is None or st_dict2 is None:
            if graph is None:
                raise Exception("No such station gap.", st1, st2)
            else:
                ignore_f = [st1, st2]
                station = st1
                while st_dict1 is None:
                    station = graph.adjacentStation(station, ignore_f)
                    print("adjacent found", station, ignore_f)
                    ignore_f.append(station)
                    if station is None:
                        break
                    st_dict1 = self.stationDict(station)
                print("st_dict1 found", st_dict1)

                ignore_l = [st1, st2]
                station = st2
                while st_dict2 is None:
                    station = graph.adjacentStation(station, ignore_l)
                    ignore_l.append(station)
                    if station is None:
                        break
                    st_dict2 = self.stationDict(station)
        if st_dict1 is None or st_dict2 is None:
            return -1  # no such gap

        dt = st_dict2["ddsj"] - st_dict1["cfsj"]
        return dt.seconds
        # if dt.days<0:
        #    dt = st_dict1["ddsj"]-st_dict2["cfsj"]
        #    return dt.seconds
        # else:
        #    return dt.seconds

    def totalMinTime(self) -> int:
        """
        2019.07.07新增
        终到站减去始发站的时间。
        """
        if not self.timetable:
            return 0
        dt: timedelta = self.timetable[-1]['cfsj'] - self.timetable[0]['ddsj']
        sec = dt.seconds
        return sec

    def stationCount(self):
        return len(self.timetable)

    def setCheci(self, full, down, up):
        # print("set checi:",full,down,up)
        self.checi = [full, down, up]

    def setFullCheci(self, name: str):
        try:
            checi = Checi(name)
        except:
            down = ''
            up = ''
        else:
            down = checi.down
            up = checi.up
        self.setCheci(name, down, up)
        # print(name,down,up)

    def clearTimetable(self):
        self.timetable = []
        self._yToStationMap.clear()

    def firstDownStr(self):
        if self.firstDown() is True:
            return '下行'
        elif self.firstDown() is False:
            return '上行'
        else:
            return '未知'

    def stationDownStr(self, name, graph):
        down = self.stationDown(name, graph)
        if down is True:
            return '下行'
        elif down is False:
            return '上行'
        else:
            return '未知'

    def lastDownStr(self):
        if self.lastDown() is True:
            return '下行'
        elif self.lastDown() is False:
            return '上行'
        else:
            return '未知'

    def updateLocalFirst(self, graph):
        for st in self.timetable:
            name = st["zhanming"]
            for station in graph.line.stations:
                if stationEqual(name, station["zhanming"]):
                    self._localFirst = name
                    return name

    def localFirst(self, graph=None):
        if graph is None:
            graph = self.graph
        if self._localFirst is not None:
            return self._localFirst
        else:
            return self.updateLocalFirst(graph)

    def updateLocalLast(self, graph):
        """
        2019.02.03修改：时间换空间，计算并维护好数据。原函数名: localLast
        """
        for st in reversed(self.timetable):
            name = st["zhanming"]
            for station in graph.line.stations:
                if stationEqual(name, station["zhanming"]):
                    self._localLast = name
                    return name

    def localLast(self, graph=None):
        if graph is None:
            graph = self.graph
        if self._localLast is not None:
            return self._localLast
        else:
            return self.updateLocalLast(graph)

    def intervalCount(self, graph, start, end):
        count = 0
        started = False
        for st in self.timetable:
            name = st["zhanming"]
            if stationEqual(name, start):
                started = True
            if not started:
                continue
            if graph.stationInLine(name):
                count += 1
            if stationEqual(name, end):
                break
        return count

    def localCount(self, graph=None):
        """
        只由车次信息计算过程调用，暂时保留线性算法
        """
        if graph is None:
            graph = self.graph
        count = 0
        for st in self.timetable:
            name = st["zhanming"]
            if graph.stationInLine(name):
                count += 1
        return count

    def isLocalTrain(self, graph) -> bool:
        """
        2019.11.16新增：
        在导入车次和车次对比中调用，判断本线在graph中的站数是否大于2.
        由于localCount()是线性算法，而这一步判断根本不需要具体的站数，如此调用代价太过昂贵。
        前置条件：graph已经实现了根据站名的近似常数时间查找，但train没实现。遍历本车次站名，依次判断到2直接返回。
        """
        cnt = 0
        for st_dict in self.stationDicts():
            if graph.stationInLine(st_dict['zhanming']):
                cnt += 1
            if cnt >= 2:
                return True
        return False

    def intervalStopCount(self, graph, start, end):
        count = 0
        started = False
        for st in self.timetable:
            name = st["zhanming"]
            if stationEqual(name, start):
                started = True
            if not started:
                continue
            if graph.stationInLine(name) and (st["cfsj"] - st["ddsj"]).seconds != 0 and \
                    name not in (start, end):
                count += 1
            if stationEqual(name, end):
                break
        return count

    def localMile(self, graph, *, fullAsDefault=True):
        """
        2.0版本修改算法：改为依赖于运行线铺画管理数据计算，每一段的localMile相加。
        如果没有数据，则使用老版本的程序。
        """
        if not self._itemInfo:
            if fullAsDefault:
                # print("localMile:没有铺画数据，使用全程数据",self.fullCheci())
                try:
                    return graph.gapBetween(self.localFirst(graph), self.localLast(graph))
                except:
                    return 0
            else:
                # print("localMile:没有铺画数据，里程默认为0", self.fullCheci())
                return 0
        else:
            mile = 0
            for dct in self.itemInfo():
                try:
                    mile += graph.gapBetween(dct['start'], dct['end'])
                except:
                    pass
            return mile

    def intervalRunStayTime(self, graph, start, end):
        """
        不算起点和终点
        """
        started = False
        running = 0
        stay = 0
        former = None

        for st in self.timetable:
            if stationEqual(st["zhanming"], start):
                started = True

            if not started:
                continue

            if former is None:
                former = st
                continue
            running += (st["ddsj"] - former["cfsj"]).seconds
            thisStay = (st["cfsj"] - st["ddsj"]).seconds
            if st["zhanming"] not in (start, end):
                stay += thisStay
            former = st
            if stationEqual(st["zhanming"], end):
                break
        # print(running, stay)
        return running, stay

    def localRunStayTime(self, graph) -> (int, int):
        """
        计算本线纯运行时间的总和、本线停站时间总和。算法是从本线入图点开始，累加所有区间时分。
        2.0版本修改：计算所有【运行线铺画区段】的上述数值。区段包括首末站。不铺画运行线的区段不累计。
        """
        started = False
        n = 0  # 即将开始的铺画区段
        running = 0
        stay = 0
        former = None

        bounds = []
        for dct in self.itemInfo():
            bounds.append((dct['start'], dct['end']))
        if not bounds:
            return 0, 0
        # if self.fullCheci() == 'K1156/7':
        #     print(bounds)
        for st in self.timetable:
            if not started and stationEqual(st['zhanming'], bounds[n][0], strict=True):
                # if self.fullCheci() == 'K8361/4/1':
                #     print("start seted to True",st['zhanming'])
                started = True
            if not started:
                continue
            if former is None:
                former = st
                stay += (st["cfsj"] - st["ddsj"]).seconds
                continue
            running += (st["ddsj"] - former["cfsj"]).seconds
            stay += (st["cfsj"] - st["ddsj"]).seconds
            # if self.fullCheci() == 'K8361/4/1':
            #     print("train.runStayTime",running,stay,former['zhanming'],st['zhanming'],n)
            former = st
            if stationEqual(st['zhanming'], bounds[n][1], strict=True):
                if n < len(bounds) - 1 and stationEqual(st['zhanming'], bounds[n + 1][0]):
                    # if self.fullCheci() == 'K1156/7':
                    #     print("end but go on",st['zhanming'])
                    pass
                else:
                    started = False
                    former = None
                n += 1
                if n >= len(bounds):
                    break
        return running, stay

    def localSpeed(self, graph, *, fullAsDefault=True):
        """
        本线旅行速度。非法时返回-1.
        """
        mile = self.localMile(graph, fullAsDefault=fullAsDefault)
        run, stay = self.localRunStayTime(graph)
        tm = run + stay
        try:
            spd = mile / tm * 1000 * 3.6
        except ZeroDivisionError:
            spd = -1
        return spd

    def firstStation(self):
        try:
            return self.timetable[0]["zhanming"]
        except IndexError:
            return ""

    def endStation(self):
        try:
            return self.timetable[-1]["zhanming"]
        except IndexError:
            return ""

    def jointTrain(self, train, former: bool, graph):
        """
        将train连接到本车次上。
        """
        if former:
            for st in reversed(train.timetable):
                if not graph.stationInLine(st["zhanming"]):
                    continue  # 非本线站点不处理，以免出错
                find = False
                for node in self.timetable:
                    if stationEqual(st["zhanming"], node["zhanming"], strict=True):
                        find = True
                        break
                if find:
                    continue
                self.timetable.insert(0, st)
        else:
            for st in train.timetable:
                if not graph.stationInLine(st["zhanming"]):
                    continue  # 非本线站点不处理，以免出错
                find = False
                for node in self.timetable:
                    if stationEqual(st["zhanming"], node["zhanming"], strict=True):
                        find = True
                        break
                if find:
                    continue
                self.timetable.append(st)

    def setStationDeltaTime(self, name: str, ds_int):
        st_dict = None
        for st in self.timetable:
            if stationEqual(st["zhanming"], name):
                st_dict = st
                break

        if st_dict is None:
            raise Exception("No such station", name)

        dt = timedelta(days=0, seconds=ds_int)
        st_dict["ddsj"] += dt
        st_dict["cfsj"] += dt

    def stationDict(self, name, strict=False) -> TrainStation:
        """
        线性算法
        """
        for st in self.timetable:
            if stationEqual(st["zhanming"], name, strict):
                return st
        return None

    def stationBusiness(self, dct: TrainStation) -> bool:
        """
        2.0.2开始新增函数。返回某个站是否办理业务。注意，此项数据原则上只能从这里获取，不能直接用dict取得。
        若dct中有business字段，直接返回；若没有此项数据，则从graph中查询后返回。这个过程会比较慢。
        正常情况下，旧版用新版第一次打开时会大量执行这个函数。
        此操作会改变数据域。
        """
        if dct is None:
            return False
        try:
            return dct['business']
        except KeyError:
            # 2019.06.27调整：先判断始发终到再判断是否停车。
            if self.isSfz(dct['zhanming']) or self.isZdz(dct['zhanming']):
                dct['business'] = True
            elif dct['ddsj'] == dct['cfsj']:
                dct['business'] = False
            else:
                dct['business'] = self.graph.lineStationBusiness(dct['zhanming'],
                                                                 self.isPassenger(detect=True), default=True)
            # print("train::stationBusiness: detect",dct['business'],dct['zhanming'],self)
            return dct['business']

    def autoBusiness(self):
        """
        根据本次列车是否为客车以及基线数据中是否办客/办货的设置，自动设置在各个站是否办理业务。
        通过的站自动设为不办业务。
        """
        for st in self.stationDicts():
            if self.isSfz(st['zhanming']) or self.isZdz(st['zhanming']):
                st['business'] = True
            elif st['ddsj'] == st['cfsj']:
                st['business'] = False
            else:
                st['business'] = self.graph.lineStationBusiness(st['zhanming'],
                                                                self.isPassenger(detect=True), default=False)
                # print("train::autoBusiness",st['zhanming'],self,st['business'])

    def isSfz(self, name: str):
        if not self.sfz:
            return False

        if self.sfz == name:
            return True

        if self.sfz.split('::')[0] == name.split('::')[0]:
            return True
        return False

    def isZdz(self, name: str):
        if not self.zdz:
            return False

        if self.zdz == name:
            return True

        if self.zdz.split('::')[0] == name.split('::')[0]:
            return True
        return False

    def translation(self, checi: str, dt_time: timedelta):
        """
        复制当前车次数据，返回新的Train对象。checi已经保证合法。
        """
        # print("train::translation",checi,dt_time,self.start_time())
        from copy import copy, deepcopy
        newtrain = Train(self.graph)
        newtrain.setFullCheci(checi)
        newtrain.setStartEnd(self.sfz, self.zdz)
        newtrain.autoTrainType()
        newtrain.timetable = deepcopy(self.timetable)
        newtrain.UI = copy(self.UI)

        for st_dict in newtrain.timetable:
            st_dict["ddsj"] += dt_time
            st_dict["cfsj"] += dt_time

        return newtrain

    def start_time(self) -> datetime:
        return self.timetable[0]["ddsj"]

    def delNonLocal(self, graph):
        """
        删除非本线站点信息
        """
        toDel = []
        for st in self.timetable:
            if not graph.stationInLine(st["zhanming"]):
                toDel.append(st)
        for st in toDel:
            self.timetable.remove(st)

    def coverData(self, train):
        """
        2.0版本注释：本函数只由rulerPaint调用，所以保留items不变，目的是方便后面删除。不会引起问题。
        用train的信息覆盖本车次信息
        """
        from copy import copy, deepcopy
        self.checi = copy(train.checi)
        self.sfz, self.zdz = train.sfz, train.zdz
        self.type = train.type
        self.UI = copy(train.UI)
        self._itemInfo = train._itemInfo
        self.timetable = deepcopy(train.timetable)

    def intervalExchange(self, start1: int, end1: int, train, start2: int, end2: int, *,
                         includeStart=True, includeEnd=True):
        """
        区间换线。
        用train的start2-end2数据（包含收尾）交换本次列车start1至end1的点单。
        参数都是数组下标。如果越界，忽略处理。
        直接使用slice方法，自动忽略越界的数据。
        """
        from copy import deepcopy
        inter1 = deepcopy(self.timetable[start1:end1 + 1])
        inter2 = deepcopy(train.timetable[start2:end2 + 1])
        if not includeStart:
            try:
                inter1[0]['ddsj'] = train.timetable[start2]['ddsj']
                inter2[0]['ddsj'] = self.timetable[start1]['ddsj']
            except IndexError:
                print("Train::intervalExchange: includeStart IndexError")
                pass
        if not includeEnd:
            try:
                inter1[-1]['cfsj'] = train.timetable[end2]['cfsj']
                inter2[-1]['cfsj'] = self.timetable[end1]['cfsj']
            except IndexError:
                print("Train::intervalExchange: includeEnd IndexError")
                pass

        self.timetable = self.timetable[:start1] + inter2 + self.timetable[end1 + 1:]
        train.timetable = train.timetable[:start2] + inter1 + train.timetable[end2 + 1:]

    def sfzIsValid(self) -> bool:
        """
        排除无效的始发站。
        如果始发站是某一个中间站，返回False。否则True。
        ====
        暂不启用。线性算法启用代价太高。
        """
        return True

    def zdzIsValid(self) -> bool:
        return True

    def relativeError(self, ruler):
        """
        计算本车次关于标尺的相对误差。返回百分比。非本线站点已经删除。
        """
        former = None
        this_time = 0
        error_time = 0
        for st_dict in self.timetable:
            if former is None:
                former = st_dict
                continue
            interval_ruler = ruler.getInfo(former["zhanming"], st_dict['zhanming'], allow_multi=True)
            try:
                int_ruler = interval_ruler["interval"] + interval_ruler["start"] + interval_ruler["stop"]
                interval_this = self.gapBetweenStation(former["zhanming"], st_dict["zhanming"])
                this_time += interval_this
                error_time += abs(int_ruler - interval_this)
            except TypeError:
                print("None info", self.fullCheci(), former["zhanming"], st_dict["zhanming"])
            former = st_dict
        try:
            return error_time / this_time
        except ZeroDivisionError:
            return 0.0

    def detectPassStation(self, graph, ruler, toStart, toEnd, precision: int):
        """
        按标尺推定通过站的时刻。保证非本线站已经删除。
        """
        if not self.timetable:
            return
        new_timetable = []
        # 将针对线路的toStart、End转变为针对本次列车的
        down = self.firstDown()
        if down:
            # 本次列车下行，toStart对应始发，toEnd对应终到
            fromStart = toStart and not graph.stationInLine(self.sfz)  # 计算原来入图以前的区段
            toEnd = toEnd and not graph.stationInLine(self.zdz)  # 计算原来出图以后的区段
        else:
            fromStart = toEnd and not graph.stationInLine(self.sfz)
            toEnd = toStart and not graph.stationInLine(self.zdz)
        first_in_graph = self.timetable[0]  # 图定本线入图结点
        firstStopped = bool((first_in_graph['ddsj'] - first_in_graph['cfsj']).seconds)
        last_in_graph = self.timetable[-1]  # 图定本线出图
        lastStopped = bool((last_in_graph['ddsj'] - last_in_graph['cfsj']).seconds)

        last_tudy_dict = None  # 上一个有效图定站点
        interval_queue = []
        for name in graph.stations(not down):
            if not int(0b01 if down else 0b10) & graph.stationDirection(name):
                # 本方向不通过本站点
                # print("不通过",name)
                continue
            this_dict = self.stationDict(name)
            if this_dict is not None:
                # 本站在图定时刻表中
                if not interval_queue:
                    # 区间没有站，直接跳过。这里也直接跳过了开头的站
                    new_timetable.append(this_dict)
                    last_tudy_dict = this_dict
                    continue
                # 计算一个本区间实际运行时分和图定运行时分的比例
                if not last_tudy_dict:
                    new_timetable.append(this_dict)
                    last_tudy_dict = this_dict
                    interval_queue = []
                    continue
                real_interval = self.gapBetweenStation(last_tudy_dict['zhanming'], name)
                ruler_interval_dict = ruler.getInfo(last_tudy_dict['zhanming'], name, allow_multi=True)
                if not ruler_interval_dict:
                    # 理论上这是不会发生的
                    new_timetable.append(this_dict)
                    last_tudy_dict = this_dict
                    interval_queue = []
                    continue
                ruler_interval = ruler_interval_dict['interval']
                if self.stationStopped(last_tudy_dict):
                    real_interval -= ruler_interval_dict['start']
                if self.stationStopped(this_dict):
                    real_interval -= ruler_interval_dict['stop']
                try:
                    rate = real_interval / ruler_interval
                except ZeroDivisionError:
                    new_timetable.append(this_dict)
                    last_tudy_dict = this_dict
                    interval_queue = []
                    continue
                for name in interval_queue:
                    ruler_node = ruler.getInfo(last_tudy_dict['zhanming'], name, allow_multi=True)
                    if ruler_node:
                        new_dict = self.makeStationDict(name, rate, last_tudy_dict, ruler_node, precision)
                        new_timetable.append(new_dict)
                new_timetable.append(this_dict)
                last_tudy_dict = this_dict
                interval_queue = []
                continue

            if last_tudy_dict is None:
                # 本次列车尚未入图
                if not fromStart:
                    continue
                gap_dict = ruler.getInfo(name, first_in_graph['zhanming'], allow_multi=True)
                gap_int = gap_dict['interval']
                if firstStopped:
                    # 图定第一站停了车，加上一个停车附加
                    gap_int += gap_dict['stop']
                dt = timedelta(days=0, seconds=gap_int)
                this_time = first_in_graph['ddsj'] - dt
                this_cf = first_in_graph['ddsj'] - dt
                new_dct = {
                    "zhanming": name,
                    "ddsj": this_time,
                    "cfsj": this_cf,
                    'note': '推定',
                }
                new_timetable.append(new_dct)
            # 本次列车已经入图，且本站不在图定运行图中，加入队列，遇到中止时刻处理
            interval_queue.append(name)

        if toEnd and interval_queue:
            for name in interval_queue:
                ruler_node = ruler.getInfo(last_tudy_dict['zhanming'], name, allow_multi=True)
                new_dict = self.makeStationDict(name, 1.0, last_tudy_dict, ruler_node, precision)
                new_timetable.append(new_dict)
        self.timetable = new_timetable

    def withdrawDetectStations(self):
        for st in self.timetable.copy():
            if st['note'] == '推定':
                self.timetable.remove(st)

    def stationInTimetable(self, name: str, strict=False) -> bool:
        return bool(filter(lambda x: stationEqual(name, x, strict),
                           map(lambda x: x['zhanming'], self.timetable)))

    def stationStopped(self, station: TrainStation) -> bool:
        """
        注意，输入的是字典。不考虑始发终到。
        """
        return bool((station['ddsj'] - station['cfsj']).seconds)

    def stationStoppedOrStartEnd(self, station: dict) -> bool:
        """
        如果始发终到，或者停车，返回True。否则返回False.
        """
        zm = station['zhanming']
        return bool((station['ddsj'] - station['cfsj']).seconds) or self.isSfz(zm) or self.isZdz(zm)

    def makeStationDict(self, name, rate: float, reference: dict, ruler_node: dict, precision: int):
        """
        从参考点开始，移动interval_sec秒作为新车站的通过时刻。
        """
        # print("detect",self.fullCheci(),"station",name,'reference',reference)
        interval_sec = int(rate * ruler_node['interval'])
        if interval_sec % precision >= precision / 2:
            interval_sec = interval_sec - interval_sec % precision + precision
        else:
            interval_sec = interval_sec - interval_sec % precision
        if interval_sec > 0:
            # 从参考车站开始往【后】推定时间
            nextStopped_bool = self.stationStopped(reference)
            if nextStopped_bool:
                interval_sec += ruler_node['start']
            dt = timedelta(days=0, seconds=interval_sec)
            this_time = reference['cfsj'] + dt
            this_cf = reference['cfsj'] + dt
            return {
                'zhanming': name,
                'ddsj': this_time,
                'cfsj': this_cf,
                'note': '推定',
            }
        else:
            lastStopped_bool = self.stationStopped(reference)
            if lastStopped_bool:
                interval_sec -= ruler_node['stop']
            dt = timedelta(days=0, seconds=-interval_sec)
            ddsj = reference['ddsj'] - dt
            cfsj = reference['ddsj'] - dt
            return {
                'zhanming': name,
                'ddsj': ddsj,
                'cfsj': cfsj,
                'note': '推定',
            }

    def stationStopBehaviour(self, station: str):
        """
        返回本站停车类型的文本。包括：通过，停车，始发，终到，不通过。
        """
        dct = self.stationDict(station)
        if not dct:
            return '不通过'
        elif (dct['ddsj'] - dct['cfsj']).seconds != 0:
            return '停车'
        elif self.isSfz(station):
            return '始发'
        elif self.isZdz(station):
            return '终到'
        else:
            return '通过'

    def stationStopBehaviour_single(self, station: str, pre: bool):
        """
        返回单字的本站起停标注。pre=True表示为区间前一个站，否则为后一个站。
        """
        dct = self.stationDict(station)
        if not dct:
            return '-'
        elif (dct['ddsj'] - dct['cfsj']).seconds != 0:
            return '起' if pre else '停'
        elif self.isSfz(station):
            return '始'
        elif self.isZdz(station):
            return '终'
        else:
            return ''

    def stationBefore(self, st1, st2):
        """
        返回st1是否在st2之前。线性算法。
        """
        findStart = False
        for st_dict in self.timetable:
            if stationEqual(st1, st_dict['zhanming']):
                findStart = True
            if stationEqual(st2, st_dict['zhanming']):
                if findStart:
                    return True
                else:
                    return False
        return False

    def intervalPassedCount(self, graph, start=None, end=None):
        """
        计算start-end区间跨越的站点的个数。start,end两站必须在时刻表上。缺省则使用本线第一个/最后一个站。
        todo 2.0版本此功能去留？
        """
        if start is None:
            start = self.localFirst(graph)
            if start is None:
                return 0
        if end is None:
            end = self.localLast(graph)

        # from graph import Graph
        # graph:Graph
        try:
            startIdx = graph.stationIndex(start)
            endIdx = graph.stationIndex(end)
        except:
            # 贵阳北::渝贵贵广场改为贵阳北渝贵贵广场会报错，暂时用这种低级方法处理。
            start, end = self.updateLocalFirst(graph), self.updateLocalLast(graph)
            if start is None:
                return 0
            startIdx = graph.stationIndex(start)
            endIdx = graph.stationIndex(end)
        if startIdx >= endIdx:
            startIdx, endIdx = endIdx, startIdx
        cnt = 0
        stations = list(map(lambda x: x["zhanming"], self.timetable))
        for i in range(startIdx, endIdx + 1):
            name = graph.stationByIndex(i)['zhanming']
            if (graph.stationDirection(name) & self.binDirection()) and name not in stations:
                cnt += 1
        return cnt

    def binDirection(self, default=0b11):
        """
        返回通过方向的常量表示形式。
        """
        down = self.firstDown()
        if down is True:
            return 0b01
        elif down is False:
            return 0b10
        else:
            return default

    def updateColor(self):
        """
        由颜色面板修改调用。重绘运行线。
        """
        if self.item is not None:
            self.item.setColor()

    def updateUI(self):
        if self.item is not None:
            self.item.resetUI()

    def stationDicts(self, startIndex=0):
        for dct in self.timetable[startIndex:]:
            yield dct

    def setTrainStationYValue(self, st: dict, y: float):
        """
        维护y_value查找表。查找表是有序的对象。
        """
        new_value = StationMap(y, st)
        bisect.insort(self._yToStationMap, new_value)

    def resetYValueMap(self):
        self._yToStationMap = []

    def yToStationInterval(self, y: float) -> (dict, dict):
        """
        返回区间的y值较小者，较大者。
        """
        if not self._yToStationMap:
            return None, None
        idx_left = bisect.bisect_right(self._yToStationMap, StationMap(y, None))
        if y < self._yToStationMap[0][0] or y > self._yToStationMap[-1][0]:
            return None, None
        if idx_left >= len(self._yToStationMap):
            return None, None
        if abs(self._yToStationMap[idx_left][0] - y) <= 2:
            # 站内事件
            return self._yToStationMap[idx_left][1], None
        if idx_left == 0:
            # 第一个站
            return self._yToStationMap[idx_left][1], None
        return self._yToStationMap[idx_left - 1][1], self._yToStationMap[idx_left][1]

    def carriageCircuit(self) -> Circuit:
        """
        如果没有交路信息，返回None. 如果交路名称无效，抛出异常。
        """
        if self._carriageCircuit is not None:
            return self._carriageCircuit
        elif self._carriageCircuitName is None:
            return None
        # print("carriageCircuit existed: ",self.fullCheci(), self._carriageCircuitName)
        # 2020.10.04  找不到标尺不报错，而是删除。不确定这个设置。
        try:
            return self.graph.circuitByName(self._carriageCircuitName)
        except CircuitNotFoundError as e:
            warnings.warn(f'Unexpected {repr(e)}, reset circuit to None', RuntimeWarning)
            self._carriageCircuitName = None
            return None

    def setCarriageCircuit(self, circuit: Circuit):
        if circuit is None:
            self._carriageCircuit = None
            self._carriageCircuitName = None
        else:
            self._carriageCircuit = circuit
            self._carriageCircuitName = circuit.name()

    def highlightItems(self, containLink=False):
        for item in self.items():
            try:
                item.select(containLink)
            except:
                pass

    def unHighlightItems(self, containLink=False):
        for item in self.items():
            try:
                item.unSelect(containLink)
            except:
                pass

    # 列车在区间起停附加的标记
    AttachStart: int = 0b01
    AttachStop: int = 0b10
    AttachNone: int = 0b00
    AttachBoth: int = 0b11

    def intervalAttachType(self, start: TrainStation, end: TrainStation) -> int:
        """
        返回区间起停标记。
        """
        d = self.AttachNone
        if self.stationStoppedOrStartEnd(start):
            d |= self.AttachStart
        if self.stationStoppedOrStartEnd(end):
            d |= self.AttachStop
        return d

    @staticmethod
    def dt(tm1: datetime, tm2: datetime) -> int:
        """
        工具性函数，返回tm2-tm1的时间，单位秒。
        """
        return (tm2 - tm1).seconds

    @staticmethod
    def sec2str(sec: int) -> str:
        """
        工具性函数，将秒数转换为形如“x分x秒”的字符串。如果时间差为0，返回空。
        """
        if not sec:
            return ''
        elif sec % 60:
            return f"{sec//60}分{sec%60:02d}秒"
        else:
            return f"{sec//60}分"

    @staticmethod
    def sec2strmin(s:int)->str:
        """将秒数转换为形如 1:20 的字符串"""
        sec = abs(int(round(s,0)))
        res = f"{sec//60}:{sec%60:02d}"
        if s < 0:
            res = '-'+res
        return res

    def stopTimeStr(self, dct: dict) -> str:
        """
        2019.06.25新增工具性函数。
        从currentWidget中拿过来。返回描述停时和是否是始发站的字符串。
        """
        ddsj, cfsj = dct['ddsj'], dct['cfsj']
        station = dct['zhanming']
        dt: timedelta = cfsj - ddsj
        seconds = dt.seconds
        if seconds == 0:
            time_str = ""
        else:
            m = int(seconds / 60)
            s = seconds % 60
            time_str = "{}分".format(m)
            if s:
                time_str += str(s) + "秒"
        add = ''
        if self.isSfz(station):
            add = '始'
        elif self.isZdz(station):
            add = '终'

        if not time_str:
            time_str = add
        elif add != '':
            time_str += f', {add}'
        return time_str

    def departure(self) -> TrainStation:
        """
        如果时刻表第一个站是始发站，返回它。否则返回None。
        适用于严格要求判断始发站的场景，如交路连接。
        """
        if not self.timetable:
            return None
        if not self.sfz:
            return None
        dct = self.timetable[0]
        if stationEqual(dct['zhanming'], self.sfz):
            return dct
        return None

    def destination(self) -> TrainStation:
        """
        如果时刻表最后一个站是终到站，返回。否则返回None。
        """
        if not self.timetable:
            return None
        if not self.zdz:
            return None
        dct = self.timetable[-1]
        if stationEqual(dct['zhanming'], self.zdz):
            return dct
        return None

    def deltaDays(self, byTimetable: bool = False) -> int:
        """
        2019.07.07新增，为交路图做准备。
        设始发是第0日，返回终到是第几日。
        byTimetable为True时，逐个车站判断是否跨日。否则只判断首末。
        需要保证日期都是1900-1-1.
        """
        if not self.timetable:
            return 0
        if not byTimetable:
            if self.timetable[-1]['ddsj'] >= self.timetable[0]['cfsj']:
                return 0
            return 1
        # 每个站先比较是否站内跨日，再比较与【上一站】的区间是否跨日。
        day = 0
        last_dict = None
        for st_dict in self.stationDicts():
            if last_dict is None:
                if st_dict['cfsj'] < st_dict['ddsj']:
                    day += 1
                last_dict = st_dict
                continue
            if st_dict['ddsj'] < last_dict['cfsj']:
                day += 1
            if st_dict['cfsj'] < st_dict['ddsj']:
                day += 1
            last_dict = st_dict
        return day

    def businessOrStoppedStations(self) -> list:
        lst = []
        for st in self.timetable:
            if self.stationStopped(st) or st.get('business', False):
                lst.append(st)
        return lst

    class StationDiffType(Enum):
        """
        仅支持列出的这些。如果时刻和站名都改了，就不能认为有关联，直接定成不相关的，一个added一个deleted。
        支持小于比较：越小表示修改程度越小。
        """
        Unchanged = 0b0  # 站名，时刻完全一致
        ArriveModified = 0b01  # 名字没变，但时刻变了
        DepartModified = 0b10
        BothModified = 0b11
        NameChanged = 0b100  # 站名改了，但时刻没变，一般用不到。
        NewAdded = 0b1000  # 原来的没有，新增的
        Deleted = 0b10000  # 本车次有，对方删了

        def __lt__(self, other):
            return self.value < other.value

    def localDiff(self, train) -> (list, int):
        """
        只考虑本线站，且不考虑折返情况下的粗糙比较。
        """

    def globalDiff(self, train) -> (list, int):
        """
        2019年11月12日：未完成。
        与train所示对象比较时刻表信息，返回加标签的时刻表和不同的数目。
        以本车次为中心，对方车次修改本车次的视角来看。
        返回：带有标记的本次列车时刻表和新时刻表序列并集，以及不同的数目。
        返回数据结构：List<Tuple>
        [
            ( 调整类型，{原始时刻表结点数据1},{数据2}),
            ...
        ]
        考虑洛谷P1140 相似基因的动态规划算法，或者编辑距离问题。对两个时刻表进行比较。
        DP目标：使得两个时刻表的重叠度总和最大。
        重叠度定义为：两个站表站名相同重叠度3，时刻相同重叠度1.
        """
        train: Train

        def similarity(st1: dict, st2: dict) -> int:
            """
            暂时只考虑站名相匹配而不考虑修改站名的情况
            """
            if st1['zhanming'] == st2['zhanming']:
                return 1
            elif st1['ddsj'] == st2['ddsj'] and st1['cfsj'] == st2['cfsj']:
                return 0
            return 0

        table = []  # 动规字典。规定table[i][j]表示本车次从第i位开始，对方车次从第j位开始的子问题的解。
        next_i = []  # 记录动规路径。记载table[i][j]的解跳转到了哪一个。
        next_j = []
        for i in range(len(self.timetable)):
            lst = [-1 for j in range(len(train.timetable))]
            table.append(lst)
            next_i.append(lst[:])
            next_j.append(lst[:])

        def solve(s1: int, s2: int) -> int:
            """
            递归的动规求解过程。s1, s2表示本车次和对方车次的开始下标子问题。返回相似度。
            """
            if s1 >= len(self.timetable) and s2 >= len(train.timetable):
                # 一起越界，直接返回0
                return 0
            elif s1 >= len(self.timetable):
                # s1越界，则2和空白匹配一位，并移动一位。
                next_i[s1 - 1][s2] = s1
                next_j[s1 - 1][s2] = s2 + 1
                return 0 + solve(s1, s2 + 1)
            elif s2 >= len(train.timetable):
                next_i[s1][s2 - 1] = s1 + 1
                next_j[s1][s2 - 1] = s2
                return 0 + solve(s1 + 1, s2)

            if table[s1][s2] != -1:
                return table[s1][s2]
            rec1 = similarity(self.timetable[s1], train.timetable[s2]) + solve(s1 + 1, s2 + 1)  # 直接对应
            rec2 = 0 + solve(s1, s2 + 1)  # 插入一个站
            rec3 = 0 + solve(s1 + 1, s2)  # 删除一个站
            sol = max((rec1, rec2, rec3))
            table[s1][s2] = sol
            if sol == rec1:
                next_i[s1][s2] = s1 + 1
                next_j[s1][s2] = s2 + 1
            elif sol == rec2:
                next_i[s1][s2] = s1
                next_j[s1][s2] = s2 + 1
            else:
                next_i[s1][s2] = s1 + 1
                next_j[s1][s2] = s2
            return sol

        result = []  # 约定的返回格式

        def addTuple(i: int, j: int) -> int:
            diff = 1
            if i == -1:
                tp = Train.StationDiffType.NewAdded
                st1 = None
                st2 = train.timetable[j]
            elif j == -1:
                tp = Train.StationDiffType.Deleted
                st2 = None
                st1 = self.timetable[i]
            else:
                st1 = self.timetable[i]
                st2 = train.timetable[j]
                tp = Train.stationCompareType(st1, st2)
                if tp == Train.StationDiffType.Unchanged:
                    diff = 0
                if tp == Train.StationDiffType.NewAdded:
                    # 说明两个没有关系，要分别新增。
                    result.append(
                        (Train.StationDiffType.Deleted, st1, None)
                    )
                    diff = 2
                    st1 = None
            result.append(
                (tp, st1, st2)
            )
            return diff

        def generate_result(s1: int, s2: int) -> int:
            """
            递归地根据结果索引回去。
            """
            if s1 == -1 or s2 == -1:
                return 0
            if s1 >= len(self.timetable) and s2 >= len(train.timetable):
                return 0
            elif s1 >= len(self.timetable):
                addTuple(-1, s2)
                return 1 + generate_result(s1, s2 + 1)
            elif s2 >= len(train.timetable):
                addTuple(s1, -1)
                return 1 + generate_result(s1 + 1, s2)
            nxi = next_i[s1][s2]
            nxj = next_j[s1][s2]
            if nxi != s1 and nxj != s2:
                diff = addTuple(s1, s2)
            elif nxi != s1:
                diff = addTuple(s1, -1)
            else:
                diff = addTuple(-1, s2)
            return diff + generate_result(nxi, nxj)

        simi_value = solve(0, 0)
        diff_count = generate_result(0, 0)
        return result, diff_count

    @staticmethod
    def stationCompareType(st1: dict, st2: dict) -> StationDiffType:
        """
        独立的比较两个车站信息。返回仅限于：
        Unchanged
        ArriveModified
        DepartModified
        BothModified
        NameChanged
        NewAdded  //约定表示其他一切情况。本函数无法判断二者的关系。
        """
        if st1['zhanming'] == st2['zhanming']:
            if st1['ddsj'] == st2['ddsj'] and st1['cfsj'] == st2['cfsj']:
                return Train.StationDiffType.Unchanged
            elif st1['ddsj'] == st2['ddsj']:
                return Train.StationDiffType.DepartModified
            elif st1['cfsj'] == st2['cfsj']:
                return Train.StationDiffType.ArriveModified
            else:
                return Train.StationDiffType.BothModified
        else:
            if st1['ddsj'] == st2['ddsj'] and st1['cfsj'] == st2['cfsj']:
                return Train.StationDiffType.NameChanged
        return Train.StationDiffType.NewAdded

    def __str__(self):
        return f"Train {self.fullCheci()} ({self.sfz}->{self.zdz}) "

    def __repr__(self):
        return f"Train object at <0x{id(self):X}> {self.fullCheci()}  {self.sfz}->{self.zdz}"

    # 2020年6月8日删除：hash不可以对车次做，直接用默认的id()就好。
    # 如果用车次做，则导致车次总是无法修改。
    # def __hash__(self):
    #     return hash(self.fullCheci())


class StationMap:
    def __init__(self, y, dct):
        self._y = y
        self._dct = dct

    def __getitem__(self, item):
        if item == 0:
            return self._y
        else:
            return self._dct

    def __gt__(self, other):
        """
        大于比较
        """
        if self._y > other._y:
            return True
        return False

    def __lt__(self, other):
        if self._y < other._y:
            return True
        return False

    def __str__(self):
        return f"{self._y} {self._dct['zhanming']}"

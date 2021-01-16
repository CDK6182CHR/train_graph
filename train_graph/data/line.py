"""
线路类
"""
from .ruler import Ruler
from .forbid import Forbid,ServiceForbid,ConstructionForbid
from .route import Route
from .linestation import LineStation
from typing import Union,List,Generator,Tuple
from Timetable_new.utility import stationEqual
from ..pyETRCExceptions import *
from copy import deepcopy

class Line():
    """
    线路类，数据结构：
    str name;
    list<dict> stations;  //站信息表
    list<Ruler> rulers; //标尺
    车站结点信息结构：
    {
        "zhanming": "罗岗线路所",
        "licheng": 1.093,
        "counter":1.551,  //对里程，或反向里程，仍按下行递增
         "dengji": 4,
        "y_value":1244,
        "direction":0x3,
        "show":True,
        "passenger":True, //办客
        "freight":False, //办货
        "tracks":str, //股道表。空白字符作为分隔。
    }
    """
    NoVia = 0x0
    DownVia = 0x1
    UpVia = 0x2
    BothVia = 0x3

    DirMap = {
        DownVia: '下行',
        UpVia: '上行',
        BothVia: '上下行',
        NoVia: '不通过'
    }

    def __init__(self,name='',origin=None):
        #默认情况下构造空对象。从文件读取时，用dict构造。
        self.nameMap = {}  # 站名查找表
        self.fieldMap = {}  # 站名-站名::场名映射表
        self.numberMap = None  # 站名->序号映射表。用于初始化时临时使用。使用期间保证站表是不变的。
        self.name = name
        self.stations = []
        self.rulers = []  # type:List[Ruler]
        self.routes = []
        self.notes = {}
        self.tracks = []
        self.forbid = ServiceForbid(self)
        self.forbid2 = ConstructionForbid(self)
        self.item = None  # lineDB中使用。
        self.parent = None  # lineDB中使用
        if origin is not None:
            self.loadLine(origin)
        self.verifyNotes()

    def setItem(self,item):
        self.item = item

    def getItem(self):
        return self.item

    def setParent(self,p):
        self.parent=p

    def getParent(self):
        return self.parent

    def setLineName(self,name:str):
        self.name = name

    def verifyNotes(self):
        """
        2019.11.02新增线路备注数据，此函数提供默认版本。
        """
        default_notes = {
            "author":"",
            "version":"",
            "note":"",
        }
        default_notes.update(self.notes)
        self.notes=default_notes

    def getNotes(self)->dict:
        return self.notes

    def setNameMap(self):
        """
        线性算法，重置站名查找表
        """
        self.nameMap = {}
        for st in self.stations:
            self.nameMap[st['zhanming']] = st

    def setFieldMap(self):
        """
        线性算法，重置所有站名-场名映射表
        """
        self.fieldMap = {}
        for st in self.stations:
            self.fieldMap.setdefault(st["zhanming"].split('::')[0],[]).append(st['zhanming'])

    def addFieldMap(self,name):
        self.fieldMap.setdefault(name.split('::')[0],[]).append(name)

    def delFieldMap(self,name):
        bare = name.split('::')[0]
        lst = self.fieldMap[bare]
        if len(lst) > 1:
            lst.remove(name)
        else:
            del self.fieldMap[bare]

    def enableNumberMap(self):
        """
        启用序号映射表。
        """
        if self.numberMap is not None:
            return
        self.numberMap = {}
        for i,st_dict in enumerate(self.stations):
            self.numberMap[st_dict['zhanming']] = i

    def disableNumberMap(self):
        self.numberMap=None

    def findStation(self,name):
        """
        在支持域解析符的前提下，返回匹配的站名列表。返回的是map中的元素，可以直接修改。
        """
        return self.fieldMap.get(name.split('::')[0],list())

    def stationDictByName(self,name:str,strict:bool=False):
        """
        基于查找表，按站名返回站名对应的字典对象。strict=False时允许按域解析符进行模糊匹配。
        如有多个结果，返回第一个。如果没有结果，返回None。
        """
        if strict:  # 严格匹配时直接返回，提高效率
            return self.nameMap.get(name,None)

        selectedName = self.findStation(name)
        if not selectedName:
            return None
        else:
            return self.nameMap[selectedName[0]]

    def loadLine(self,origin):
        self.name = origin["name"]
        self.stations = origin["stations"]
        self.notes = origin.get("notes",{})
        self.tracks = origin.get('tracks',[])
        try:
            self.rulers
        except:
            self.rulers = []
        for ruler_dict in origin["rulers"]:
            new_ruler = Ruler(origin=ruler_dict,line=self)
            self.rulers.append(new_ruler)
        for route_dict in origin.get('routes',[]):
            r = Route(self)
            r.parseData(route_dict)
            self.routes.append(r)

        self.forbid.loadForbid(origin.get("forbid",None))
        self.forbid2.loadForbid(origin.get("forbid2",None))
        self.setNameMap()
        self.setFieldMap()
        self.verifyNotes()
        self.resetRulers()

    def addStation_by_origin(self,origin,index=-1):
        if not isinstance(origin,LineStation):
            origin=LineStation(origin)
        if index==-1:
            self.stations.append(origin)
        else:
            self.stations.insert(index,origin)
        self.nameMap[origin["zhanming"]] = origin
        self.addFieldMap(origin['zhanming'])

    def addStation_by_info(self,zhanming,licheng,dengji=4,index=-1,counter=None,direction=0x3):
        info = LineStation({
            "zhanming":zhanming,
            "licheng":licheng,
            "dengji":dengji,
            "y_value":-1,
            "show":True,
            "direction":direction,
        })
        if counter is not None:
            info['counter']=counter
        self.addStation_by_origin(info,index)

    def show(self):
        #Debug Only
        print(self.name)
        for station in self.stations:
            print(station["zhanming"],station["licheng"],station["dengji"])

        print("rulers:")
        for ruler in self.rulers:
            ruler.show()

    def outInfo(self):
        #整理为json所用格式，返回dict，仅用于文件操作
        info = {
            "name":self.name,
            "rulers":[],
            "routes":[],
            "stations":self.stations,
            "forbid":self.forbid.outInfo(),
            "forbid2":self.forbid2.outInfo(),
            "notes":self.notes,
            "tracks":self.tracks,
        }
        try:
            self.rulers
        except:
            self.rulers = []

        for ruler in self.rulers:
            info["rulers"].append(ruler.outInfo())
        for route in self.routes:
            info['routes'].append(route.outInfo())
        return info

    def stationInLine(self,station,strict=False):
        """
        2018.08.06 加入域解析符的支持
        2019.02.02 删去线性算法
        """
        if strict:
            return bool(self.nameMap.get(station))
        else:
            return bool(self.findStation(station))

    def stationIndex(self, name: str):
        """
        2019.07.12新增常量级别算法。理论上应保证站名存在。
        """
        if self.numberMap is None:
            return self.stationIndex_bf(name)
        else:
            try:
                return self.numberMap[self.nameMapToLine(name)]
            except KeyError:
                print("Line::stationIndex: Unexpected station name:",name)
                return self.stationIndex_bf(name)

    def stationIndex_bf(self,name:str):
        """
        原来的暴力方法查找序号。分离此函数是为了尝试统计有多少次使用暴力方法。
        """
        for i, st in enumerate(self.stations):
            if stationEqual(st["zhanming"], name):
                return i
        raise StationNotInLineException(name)

    def nameMapToLine(self,name:str):
        """
        支持域解析符的情况下，将车次中的站名映射到本线站名。
        """
        dct = self.stationDictByName(name)
        try:
            return dct['zhanming']
        except TypeError:
            return name

    def rulerByName(self,name:str)->Ruler:
        for ruler in self.rulers:
            if ruler._name == name or set(ruler._name.split('*')) == set(name.split('*')):
                return ruler
        return None

    def delStation(self,name):
        """
        2019.02.02删除线性算法。name应该严格匹配。
        """
        dct = self.nameMap.get(name,None)
        if dct is None:
            return
        self.stations.remove(dct)
        # 更新映射表
        del self.nameMap[name]
        if len(self.findStation(name))>1:
            self.findStation(name).remove(name)
        else:
            del self.fieldMap[name]

    def stationExisted(self,name:str):
        """
        删除线性算法。不支持域解析符。
        """
        return bool(self.nameMap.get(name,False))

    def addStationDict(self,info):
        if not isinstance(info,LineStation):
            info=LineStation(info)
        self.stations.append(info)
        self.addFieldMap(info['zhanming'])
        self.nameMap[info['zhanming']] = info

    def adjustLichengTo0(self):
        """
        将起始站里程归零，同时平移所有站里程。
        2020.01.23新增调整对里程的逻辑。
        """
        if not self.stations:
            return
        start_mile = self.stations[0]["licheng"]
        start_counter = self.stations[0].get("counter",None)
        for st in self.stations:
            st["licheng"] = st["licheng"]-start_mile
        if start_counter is not None:
            for st in self.stations:
                if st.get('counter') is not None:
                    st['counter']-=start_counter

    def isDownGap(self,st1:str,st2:str):
        """
        判断给定的区间是否为下行区间
        线性算法。
        """
        s1 = None
        s2 = None
        for st in self.stations:
            if stationEqual(st["zhanming"],st1):
                s1 = st
            elif stationEqual(st["zhanming"],st2):
                s2 = st
            if s1 is not None and s2 is not None:
                break
        try:
            if s1["licheng"]-s2["licheng"] >0.0:
                return False
        except:
            pass
        return True

    def isDownGapByDict(self,st1:LineStation,st2:LineStation)->bool:
        """
        判定是否是下行区间，常量级别算法，按里程计算。
        """
        return st1['licheng'] <= st2['licheng']

    def gapBetween(self, st1: str, st2: str)->float:
        """
        计算两个站间距离.
        2020.01.23新增：如果是上行方向，则尝试使用对里程。
        对里程按照点对点原则使用，只考虑两端点的对里程数据，不考虑中间的。
        """
        station1 = self.stationDictByName(st1)
        station2 = self.stationDictByName(st2)

        if station1 is None:
            raise StationNotInLineException(st1)
        if station2 is None:
            raise StationNotInLineException(st2)

        if not self.isDownGapByDict(station1, station2):
            if station1.get('counter') is not None and \
                    station2.get('counter') is not None:
                return abs(station1['counter'] - station2['counter'])
        return abs(station1["licheng"] - station2["licheng"])

    def stationViaDirection(self,name:str):
        """
        返回name指向车站的direction参数，若无此key，设为0x3；若无此车站，返回None.
        2019.02.02 删除线性算法。
        2019.02.28 增加域解析符支持。
        """
        lst = self.fieldMap.get(name.split('::')[0],None)
        dct = self.nameMap.get(lst[0],None) if lst else None
        if dct is None:
            return None
        return dct.setdefault('direction',0x3)

    def setStationViaDirection(self,name:str,via:int):
        """
        设置name指向车站的direction属性。不支持域解析符。若无此车站，不作操作。
        """
        self.nameMap.get(name,{})['direction'] = via

    def isSplited(self):
        """
        返回本线是否存在上下行分设站的情况
        :return:
        """
        for st in self.stations:
            st.setdefault('direction',0x3)

            if st["direction"] == 0x1 or st["direction"] == 0x2:
                return True
        return False

    def resetRulers(self):
        for ruler in self.rulers:
            ruler._line = self
            ruler.resetAllPassed()

        if self.isSplited():
            for ruler in self.rulers:
                ruler.setDifferent(True,change=True)

    def stationCount(self):
        return len(self.stations)

    def stationDicts(self,start_index=0):
        """
        依次迭代所有车站的dict。
        """
        for station in self.stations[start_index:]:
            yield station

    def reversedStationDicts(self):
        for station in reversed(self.stations):
            yield station

    def copyData(self,line,withRuler=False):
        """
        复制并覆盖本线所有数据
        """
        self.name = line.name
        self.stations = line.stations
        if withRuler:
            self.rulers = line.rulers
            for ruler in self.rulers:
                ruler._line = self
        self.nameMap = line.nameMap
        self.fieldMap = line.fieldMap

    def rulerNameExisted(self,name,ignore:Ruler=None):
        for r in self.rulers:
            if r is not ignore and r.name() == name:
                return True
        return False

    def isNewRuler(self,ruler:Ruler):
        for r in self.rulers:
            if ruler is r:
                return False
        return True

    def delRuler(self,ruler:Ruler):
        """
        返回被删除的标尺是否是排图标尺
        :param ruler:
        :return:
        """
        try:
            self.rulers.remove(ruler)
        except ValueError:
            pass

    def addRuler(self,ruler:Ruler):
        self.rulers.append(ruler)

    def addEmptyRuler(self,name:str,different:bool=False)->Ruler:
        ruler = Ruler(name=name,different=different,line=self)
        self.rulers.append(ruler)
        return ruler

    def setStationYValue(self,name,y):
        """
        设置某个站的纵坐标值。
        2019.02.02从graph类移植，并删除线性算法。暂时不允许域解析符。
        若无此车站，不作操作。
        """
        self.nameMap.get(name,{})['y_value'] = y

    def changeStationNameUpdateMap(self,old,new):
        """
        修改站名时调用，修改映射查找表。调用时已经修改完毕。
        """
        print(self.nameMap)
        try:
            dct = self.nameMap[old]
        except KeyError:
            # 表明原站名不在站名表中，不用修改
            return
        del self.nameMap[old]
        self.nameMap[new] = dct
        self.delFieldMap(old)
        self.addFieldMap(new)

    def stationDictByIndex(self,idx)->LineStation:
        try:
            return self.stations[idx]
        except IndexError:
            return None

    def lineLength(self)->float:
        if self.stations:
            return self.stations[-1]["licheng"]
        else:
            return 0

    def counterLength(self)->float:
        """
        [对里程]意义下的线路长度，或者说是上行线的长度。仅考虑最后一个站。
        如果最后一个站的对里程数据不存在，则使用正里程长度数据。
        """
        if not self.stations:
            return 0
        ctlen = self.stations[-1].get("counter")
        if ctlen is not None:
            return ctlen
        return self.lineLength()

    def clear(self):
        """
        清除所有信息。2019.06.30新增，解决天窗造成的异常问题。
        """
        self.stations.clear()
        self.rulers.clear()
        self.forbid.clear()
        self.forbid2.clear()

    def firstStationName(self)->str:
        if not self.stations:
            return ''
        return self.stations[0]['zhanming']

    def lastStationName(self)->str:
        if not self.stations:
            return ''
        return self.stations[-1]['zhanming']

    def splitStationDirection(self,old_name:str,down_name:str,up_name:str):
        """
        2019.11.28新增
        将线路中一站拆分为两个站。拆分后的站具有相同的里程，并分别为下行单向和上行单向站。
        同时修改站名映射表，修改天窗信息表，标尺信息表。
        """
        old_idx = self.stationIndex(old_name)
        old_dict:dict = self.stations[old_idx]
        if old_dict['direction'] != Line.BothVia:
            print("Line::splitStationDirection: 必须是双向通过站，才可以拆分")
            return
        elif down_name!=old_name and self.stationExisted(down_name):
            print("Line::splitStationDirection: 下行站名重复")
            return
        elif up_name!=old_name and self.stationExisted(up_name) or up_name==down_name:
            print("Line::splitStationDirection: 上行站名重复")
            return
        for ruler in self.rulers:
            ruler.onStationDirectionSplited(old_name,down_name,up_name)
        old_dict['zhanming'] = down_name
        old_dict['direction'] = Line.DownVia
        del self.nameMap[old_name]
        self.delFieldMap(old_name)
        # 添加新的车站信息
        up_dict = old_dict.copy()
        up_dict['zhanming'] = up_name
        up_dict['direction'] = Line.UpVia
        self.stations.insert(old_idx+1,up_dict)
        self.nameMap[up_name] = up_dict
        self.addFieldMap(up_name)

    def reverse(self):
        """
        2020年1月24日增加，
        反排线路数据。
        1. 反排站表数据。
        2. 重新计算里程，交换正里程和对里程。
        3. 交换单向站性质。
        """
        length = self.lineLength()
        ctlen = self.counterLength()

        viaMap = {
            Line.DownVia:Line.UpVia,
            Line.UpVia:Line.DownVia,
            Line.NoVia:Line.NoVia,
            Line.BothVia:Line.BothVia,
        }

        for st_dict in self.stations:
            st_dict["licheng"] = length - st_dict["licheng"]
            if st_dict.get("counter") is not None:
                st_dict["counter"] = ctlen-st_dict["counter"]
            else:
                st_dict["counter"] = st_dict["licheng"]
            # 交换正里程和对里程
            st_dict['counter'],st_dict['licheng'] = st_dict['licheng'],st_dict['counter']
            st_dict['direction'] = viaMap[st_dict.get("direction",Line.BothVia)]
        self.stations.reverse()

    def adjIntervals(self, down)->List[Tuple[str,str]]:
        """
        依次产生所有的邻接区间。
        :param different 是否上下行分设。如果不是，则只关心下行。
        """
        if not self.stations:
            return []
        res = []
        if down:
            last = self.stations[0]['zhanming']
            for st in self.stations[1:]:
                if not st['direction'] & self.DownVia:
                    continue
                res.append((last,st['zhanming']))
                last = st['zhanming']
        else:
            last = self.stations[-1]['zhanming']
            for st in self.stations[-2::-1]:
                if not st['direction'] & self.UpVia:
                    continue
                res.append((last,st['zhanming']))
                last = st['zhanming']
        return res

    @staticmethod
    def bool2CheckState(t):
        """
        工具函数，将bool转换成Qt.CheckState。
        """
        if t:
            return 0x2
        return 0x0

    @staticmethod
    def speedStr(mile:float,sec:int)->str:
        """
        工具函数，计算均速，并转换为字符串。
        """
        if sec:
            return f"{mile*1000/sec*3.6:.3f}"
        else:
            return "NA"

    def setStationTracks(self,name:str,tracks:list):
        dct = self.stationDictByName(name,strict=True)
        dct['tracks'] = tracks

    def stationTracks(self,name:str)->list:
        dct = self.stationDictByName(name, strict=True)
        if dct is None:
            return []
        return dct.get('tracks',[])

    def mergeCounter(self, counter:'Line'):
        """
        2021.01.14
        合并反向的线路信息，也即整合对里程和经由方向。
        precondition:
        1. counter的起点是当前线路的终点，但counter的终点未见得是当前线路起点。
        2. counter中的“下行”是本线的“上行”。
        3. 两边的各个站本来都设置的是Line.DownVia，即按照单向站处理的。
        4. 两边的站序是差不多相同的。
        :param counter: 当前线路的上行版本。const语义
        :return:
        """
        i = 0  # 当前线路位置指针
        j = counter.stationCount()-1  # 对线路的位置指针
        while True:  # 暂时不写条件
            if i >= self.stationCount() or j < 0:
                break
            si = self.stations[i]
            sj = counter.stations[j]
            if si['zhanming'] == sj['zhanming']:
                # 两边刚好对上，情况最简单
                si['direction'] |= Line.UpVia
                si['counter'] = counter.lineLength()-sj['licheng']
                i += 1
                j -= 1
            else:
                if not self.stationExisted(sj['zhanming']):
                    # 上行单向站, 做插入处理
                    m = counter.lineLength()-sj['licheng']
                    self.addStation_by_info(sj['zhanming'],m,index=i,counter=m)
                    self.setStationViaDirection(sj['zhanming'],Line.UpVia)
                    i += 1  # 注意：这里i的下标指向变了
                    j -= 1
                else:
                    # not counter.stationExisted(si['zhanming'])
                    # 以上两个条件都不成立的情况理论上不该存在
                    # 下行单向站，这个很好处理
                    i += 1
        # [对里程]的修正：使得零点和正里程一样
        if not Line.UpVia & self.stations[0]['direction']:
            i = 0
            while i < self.stationCount() and not self.stations[i]['direction'] & Line.UpVia:
                i += 1
            if i < self.stationCount():
                m0 = self.stations[i]['licheng']
                for st_dict in self.stationDicts(i):
                    if st_dict.get('counter') is not None:
                        st_dict['counter'] += m0

    def slice(self, start_index:int, end_index:int)->'Line':
        """
        产生切片线路。
        :param start_index: 起始站下标（含）
        :param end_index: 终止站下标（不含）
        :return:
        """
        sub = Line(self.name)
        sub.stations = deepcopy(self.stations[start_index:end_index])
        sub.setNameMap()
        sub.setNameMap()
        sub.setFieldMap()
        sub.verifyNotes()
        sub.resetRulers()
        return sub

    def copy(self):
        return self.slice(0,self.stationCount())

    def jointLine(self, line, former, reverse):
        if former:
            for station in self.stationDicts():
                station["licheng"] += line.lineLength()
                if station.get('counter') is not None:
                    station['counter'] += line.counterLength()

            for st in reversed(line.stations):
                st = st.copy()
                if not self.stationExisted(st["zhanming"]):
                    self.addStation_by_origin(st, index=0)
        else:
            length = self.lineLength()
            cnt = self.counterLength()
            for st in line.stationDicts():
                st = st.copy()
                st["licheng"] += length
                if st.get('counter') is not None:
                    st['counter'] += cnt
                if not self.stationExisted(st["zhanming"]):
                    self.addStation_by_origin(st)

        # 标尺的处理，直接复制过来就好
        for ruler in line.rulers:
            thisruler = self.rulerByName(ruler.name())
            if thisruler is not None:
                thisruler._nodes.extend(ruler._nodes)
            else:
                self.addRuler(ruler)

        # 天窗处理，直接附加
        self.forbid._nodes.extend(line.forbid._nodes)
        self.forbid2._nodes.extend(line.forbid2._nodes)

    def filtRuler(self,minCount:int):
        """
        删除小于指定站数的标尺。
        :param minCount:
        :return:
        """
        for ruler in self.rulers.copy():
            if ruler.count() < minCount:
                self.rulers.remove(ruler)




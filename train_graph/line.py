"""
线路类
"""
from .ruler import Ruler
from .forbid import Forbid
from typing import Union
from Timetable_new.utility import stationEqual

class Line():
    """
    线路类，数据结构：
    str name;
    list<dict> stations;  //站信息表
    list<Ruler> rulers; //标尺
    车站结点信息结构：
    {
        "zhanming": "罗岗线路所",
        "licheng": 1,
         "dengji": 4,
        "y_value":1244,
        "direction":0x3,
        "show":True,
        "passenger":True, //办客
        "freight":False, //办货
    }
    """
    NoVia = 0x0
    DownVia = 0x1
    UpVia = 0x2
    BothVia = 0x3

    def __init__(self,name='',origin=None):
        #默认情况下构造空对象。从文件读取时，用dict构造。
        self.nameMap = {} # 站名查找表
        self.fieldMap = {} # 站名-站名::场名映射表
        self.numberMap = None  # 站名->序号映射表。用于初始化时临时使用。使用期间保证站表是不变的。
        if origin is not None:
            self.loadLine(origin)
        else:
            self.name = name
            self.stations = []
            self.rulers = []
            self.forbid = Forbid(self)

    def setLineName(self,name:str):
        self.name = name

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
        try:
            self.rulers
        except:
            self.rulers = []
        for ruler_dict in origin["rulers"]:
            new_ruler = Ruler(origin=ruler_dict,line=self)
            self.rulers.append(new_ruler)

        try:
            self.forbid
        except AttributeError:
            self.forbid = Forbid(self)
        try:
            origin["forbid"]
        except KeyError:
            pass
        else:
            self.forbid.loadForbid(origin["forbid"])
        self.setNameMap()
        self.setFieldMap()

    def addStation_by_origin(self,origin,index=-1):
        if index==-1:
            self.stations.append(origin)
        else:
            self.stations.insert(index,origin)
        self.nameMap[origin["zhanming"]] = origin
        self.addFieldMap(origin['zhanming'])

    def addStation_by_info(self,zhanming,licheng,dengji=4,index=-1):
        info = {
            "zhanming":zhanming,
            "licheng":licheng,
            "dengji":dengji,
            "y_value":-1,
            "show":True,
            "direction":0x3,
        }
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
            "stations":self.stations,
            "forbid":self.forbid.outInfo()
        }
        try:
            self.rulers
        except:
            self.rulers = []

        for ruler in self.rulers:
            info["rulers"].append(ruler.outInfo())
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
        self.stations.append(info)
        self.addFieldMap(info['zhanming'])
        self.nameMap[info['zhanming']] = info

    def adjustLichengTo0(self):
        if not self.stations:
            return
        start_mile = self.stations[0]["licheng"]
        for st in self.stations:
            st["licheng"] = st["licheng"]-start_mile

    def isDownGap(self,st1:str,st2:str):
        """
        判断给定的区间是否为下行区间
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
        print("line 180:",self.rulers)
        for ruler in self.rulers:
            ruler._line = self
            ruler.resetAllPassed()

        if self.isSplited():
            print("设置ruler splited")
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

    def stationDictByIndex(self,idx):
        try:
            return self.stations[idx]
        except IndexError:
            return None

    def lineLength(self)->float:
        try:
            return self.stations[-1]["licheng"]
        except IndexError:
            return 0

    def clear(self):
        """
        清除所有信息。2019.06.30新增，解决天窗造成的异常问题。
        """
        self.stations.clear()
        self.rulers.clear()
        self.forbid.clear()

    @staticmethod
    def bool2CheckState(t):
        """
        工具函数，将bool转换成Qt.CheckState。
        """
        if t:
            return 0x2
        return 0x0


if __name__ == '__main__':
    line = Line("宁芜线")
    line.addStation_by_info("南京",0,0)
    line.addStation_by_info("光华门",12,3)
    line.addStation_by_info("南京东",8,3,index=1)
    line.show()
    dict = line.outInfo()

    newline = Line(origin=dict)
    newline.show()



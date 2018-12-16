"""
线路类
"""
from ruler import Ruler
from forbid import Forbid
class Line():
    """
    线路类，数据结构：
    str name;
    list<dict> stations;  //站信息表
    list<Ruler> rulers; //标尺
    车站结点信息结构：
    {"zhanming": "罗岗线路所", "licheng": 1, "dengji": 4,
    "y_value":1244,"direction":0x3,"show":True}
    """
    NoVia = 0x0
    DownVia = 0x1
    UpVia = 0x2

    def __init__(self,name='',origin=None):
        #默认情况下构造空对象。从文件读取时，用dict构造。
        if origin is not None:
            self.loadLine(origin)
        else:
            self.name = name
            self.stations = []
            self.rulers = []
            self.forbid = Forbid(self)

    def setLineName(self,name:str):
        self.name = name

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

    def addStation_by_origin(self,origin,index=-1):
        if index==-1:
            self.stations.append(origin)
        else:
            self.stations.insert(index,origin)

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

    def mileages(self):
        """
        yield function
        :return:
        """
        for st in self.stations:
            yield st["licheng"]

    def stationInLine(self,station,strict=False):
        """
        2018.08.06 加入域解析符的支持
        :param station:
        strict: 严格匹配
        :return:
        """
        for st in self.stations:
            if station == st["zhanming"]:
                return True
            elif not strict:
                if station.split('::')[0] == st["zhanming"].split('::')[0]:
                    print("域解析符有效",station)
                    return True
        return False

    def rulerByName(self,name:str):
        for ruler in self.rulers:
            if ruler._name == name:
                return ruler
        return None

    def delStation(self,name):
        dict = None
        for i in self.stations:
            if name == i["zhanming"]:
                dict = i
                break
        if dict is not None:
            self.stations.remove(dict)

    def _station_dict_by_name(self,name:str):
        for st in self.stations:
            if st["zhanming"] == name:
                return st

    def stationExisted(self,name:str):
        for st in self.stations:
            if name == st["zhanming"]:
                return True

        return False

    def addStationDict(self,info):
        self.stations.append(info)

    def adjustLichengTo0(self):
        if not self.stations:
            return
        start_mile = self.stations[0]["licheng"]
        for st in self.stations:
            st["licheng"] = st["licheng"]-start_mile

    def isDownGap(self,st1:str,st2:str):
        """
        判断给定的区间是否为下行区间
        :param st1:
        :param st2:
        :return:
        """
        from utility import stationEqual
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
        for st in self.stations:
            if st["zhanming"] == name:
                try:
                    return st["direction"]
                except:
                    st["direction"] = 0x3
                    return 0x3
        return None

    def setStationViaDirection(self,name:str,via:int):
        for st in self.stations:
            if st["zhanming"] == name:
                st["direction"] = via

    def isSplited(self):
        """
        返回本线是否存在上下行分设站的情况
        :return:
        """
        for st in self.stations:
            try:
                st["direction"]
            except KeyError:
                st["direction"] = 0x3

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

    def stationDicts(self):
        for station in self.stations:
            yield station

    def copyData(self,line,withRuler=False):
        """
        复制并覆盖本线所有数据
        :param line:
        :return:
        """
        self.name = line.name
        self.stations = line.stations
        if withRuler:
            self.rulers = line.rulers

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


if __name__ == '__main__':
    line = Line("宁芜线")
    line.addStation_by_info("南京",0,0)
    line.addStation_by_info("光华门",12,3)
    line.addStation_by_info("南京东",8,3,index=1)
    line.show()
    dict = line.outInfo()

    newline = Line(origin=dict)
    newline.show()

    print("yield test")
    for n,m in line.name_mileages():
        print(n,m)


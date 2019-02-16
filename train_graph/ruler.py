"""
标尺类，高度封装
"""
from datetime import datetime,timedelta
from copy import copy
from utility import stationEqual

class Ruler():
    """
    数据结构：
    str _name;
    bool _different;//上下行是否不一致
    list<dict> _nodes;//区间结点列表
    list<str> _down_pass;//下行不通过站
    list<str> _up_pass;//上行不通过站
    结点数据结构：
    dict _nodes{
        "fazhan":str,//区间起始站
        "daozhan":str,//区间终点站
        "interval":int,//区间用时，单位秒
        "start":int,//起车附加
        "stop":int,//停车附加
    """
    def __init__(self,origin:dict=None,name:str="",different:bool=True,nodes:list=None,line=None):
        if origin is not None:
            # 直接给字典格式，读文件时
            self.loadRuler(origin)
            self._line = line
        else:
            self._line = line
            self._name = name
            self._different = different
            self._nodes = nodes if nodes is not None else []
            self._down_pass = []
            self._up_pass = []
            if self._line is not None:
                self.resetAllPassed()

    def loadRuler(self,origin:dict):
        self._name = origin["name"]
        self._different = origin["different"]
        self._nodes = origin["nodes"]
        try:
            self._down_pass = origin["down_pass"]
            self._up_pass = origin["up_pass"]
        except KeyError:
            self._down_pass = []
            self._up_pass = []

    def addStation_info(self,fazhan:str,daozhan:str,interval:int,start:int,stop:int,
                        del_existed=False):
        if interval == 0:
            return
        if del_existed:
            existed = self.getInfo(fazhan,daozhan)
            if existed is not None:
                self._nodes.remove(existed)

        dict = {
            "fazhan":fazhan,
            "daozhan":daozhan,
            "interval":interval,
            "start":start,
            "stop":stop
        }
        self.addStation_dict(dict,del_existed=False)

    def addStation_dict(self,info:dict,del_existed=False):
        if info["interval"] == 0:
            return
        if del_existed:
            existed = self.getInfo(info["fazhan"],info["daozhan"])
            if existed is not None:
                self._nodes.remove(existed)
        self._nodes.append(info)

    def changeStationName(self,old:str,new:str):
        """
        修改某站站名，同步修改所有标尺站名
        """
        for node in self._nodes:
            if node["fazhan"] == old:
                node["fazhan"] = new
            if node["daozhan"] == old:
                node["daozhan"] = new

    def del_station(self,station_name:str):
        """
        TODO
        删除某个站点，连接前后区间数据
        :param station_name:
        :return:
        """

    def getInfo(self,fazhan:str,daozhan:str,allow_multi=False):
        """
        :param fazhan:
        :param daozhan:
        :param allow_multi:是否允许跨区间。
        :return:
        """
        for node in self._nodes:
            if stationEqual(node['fazhan'],fazhan,strict=True) and \
                    stationEqual(node['daozhan'],daozhan,strict=True):
                return node

        for node in self._nodes:
            if stationEqual(node['fazhan'],fazhan) and stationEqual(node['daozhan'],daozhan):
                return node

        if not self._different:
            for dict in self._nodes:
                if dict["fazhan"] == daozhan and dict["daozhan"] == fazhan:
                    return dict
            for node in self._nodes:
                if stationEqual(node['daozhan'], fazhan) and stationEqual(node['fazhan'], daozhan):
                    return node

        if allow_multi:
            return self._multiBFS(fazhan,daozhan)

        return None

    def _multiBFS(self,start,end):
        """
        BFS框架搜索从start到end的路径
        :param start:
        :param end:
        :return:
        """
        length_dict={}
        last_dict={}  #记住每个站路径中的上一个站，方便回溯
        queue=[]
        for w in self._find_neighbors(start):
            length_dict[w]=self.getInfo(start,w,allow_multi=False)['interval']
            last_dict[w]=start
            queue.append(w)

        while queue:
            v=queue.pop(0)
            if stationEqual(v,end):
                #找到要找的结点，直接返回
                interval = length_dict[v]  #区间运行时分
                t = last_dict[v]
                stop=self.getInfo(t,v)['stop']
                while last_dict[v]!=start:
                    v=last_dict[v]
                # 现在v的last就是start
                start=self.getInfo(start,v)['start']
                return {
                    'interval':interval,
                    'start':start,
                    'stop':stop,
                }

            for w in self._find_neighbors(v):
                if w not in length_dict.keys():  # w is unreached
                    length_dict[w]=length_dict[v]+self.getInfo(v,w,False)['interval']
                    last_dict[w] = v
                    queue.append(w)
        return None

    def stationEqual(self,st1,st2):
        if st1==st2:
            return True
        elif ('::' in st1) != ('::' in st2) and st1.split('::')[0]==st2.split('::')[0]:
            return True
        return False

    def _find_path(self,fazhan,daozhan,passed:list):
        """
        找出从fazhan到daozhan间的一条路径，返回经过的站点表
        :param fazhan:
        :param daozhan:
        :return:
        """
        neighbors = self._find_neighbors(fazhan)

        for name in neighbors:
            if name in passed:
                continue

            if name == daozhan:
                return passed

            else:
                path = self._find_path(name,daozhan,passed[:])
                if path is not None:
                    return path

    def _find_neighbors(self,name:str):
        neighbors = []
        for st in self._nodes:
            if self.stationEqual(st["fazhan"],name):
                neighbors.append(st["daozhan"])

        if not self._different:
            for st in self._nodes:
                if self.stationEqual(st['daozhan'],name):
                    neighbors.append(st["fazhan"])

        return neighbors

    def setDifferent(self,different:bool,change:bool=False):
        will_change = False  #是否需要修改内置数据
        if self._different != different:
            will_change = True
        self._different = different
        if not change or not will_change:
            return

        #若是设为True,则复制数据
        if different:
            new_nodes = []
            for node in self._nodes:
                if self._line.isDownGap(node["fazhan"],node["daozhan"]):
                    #复制下行区间数据
                    up_dict = copy(node)
                    up_dict["fazhan"] = node["daozhan"]
                    up_dict["daozhan"] = node["fazhan"]
                    new_nodes.append(up_dict)
            self._nodes += new_nodes

        #设置为False，删除所有上行区间数据
        else:
            up_dicts = []
            for node in self._nodes:
                if node is None:
                    continue
                if not self._line.isDownGap(node["fazhan"],node["daozhan"]):
                    up_dicts.append(node)
            for node in up_dicts:
                self._nodes.remove(node)

    def different(self):
        return self._different

    def outInfo(self):
        #向文件输出
        dict = {
            "name":self._name,
            "different":self._different,
            "nodes":self._nodes,
            "down_pass":self._down_pass,
            "up_pass":self._up_pass,
        }
        # print("ruler outInfo: ",dict)
        return dict

    def show(self):
        #Debug only
        pass

    def rulerFromTrain(self,train,stop:int=120,start:int=120):
        """
        从既有运行图自动推算同方向标尺，覆盖原有标尺
        :param train:
        :param stop:
        :param start:
        :return:
        """
        if train is None:
            return
        last_station = {}

        for station in train.timetable:
            if not last_station:
                #first station
                if self._line.stationInLine(station["zhanming"]):
                    last_station = station
                else:
                    print("非本线站名：", station["zhanming"])
                continue

            #非第一个站
            if not self._line.stationInLine(station["zhanming"]):
                print("非本线站名：",station["zhanming"])
                continue

            interval = (station["ddsj"] - last_station["cfsj"]).seconds

            if last_station["ddsj"] != last_station["cfsj"]:
                interval -= start
            elif last_station["zhanming"] == train.sfz:
                interval -= start  #始发站

            if station["ddsj"] != station["cfsj"]:
                interval -= stop
            elif station["zhanming"] == train.zdz:
                interval -= stop

            node = {
                "fazhan":last_station["zhanming"],
                "daozhan":station["zhanming"],
                "interval":interval,
                "start":start,
                "stop":stop,
            }
            # print("add station",last_station["zhanming"],station["zhanming"])
            self.addStation_dict(node,True)
            last_station = station

    def findStart(self,start,ignore_list):
        """
        找到起始站为所求的标尺结点
        :param start:
        :return:
        """
        for st in self._nodes:
            if st["fazhan"] == start and st["daozhan"] not in ignore_list:
                return st
            elif st["daozhan"] not in ignore_list and \
                    ('::' in st["fazhan"])!=('::' in start) and \
                st['fazhan'].split('::')[0]==start.split('::')[0]:
                return st

        if not self._different:
            for st in self._nodes:
                if st["daozhan"] == start and st["fazhan"] not in ignore_list:
                    return st
                elif st["fazhan"] not in ignore_list and \
                        ('::' in st["daozhan"]) != ('::' in start) and \
                        st['daozhan'].split('::')[0] == start.split('::')[0]:
                    # print('findStart 域解析符有效', st['daozhan'], start)
                    return st
        return None

    def totalTime(self,down:bool=True):
        """
        按下行排图，计算标尺总长度。跳过_down_pass中。
        :param down:
        :return:
        """
        # print("total time calculate")
        total = 0
        start_station = self._line.stations[0]["zhanming"]
        end_station = self._line.stations[-1]["zhanming"]
        passed = []

        former_station = None
        for st in self._line.stations:
            if former_station is None:
                if st["zhanming"] not in self._down_pass:
                    former_station = st
                continue

            if st["zhanming"] in self._down_pass:
                continue

            node = self.getInfo(former_station["zhanming"],st["zhanming"])
            if node is None:
                raise Exception("Unexpected None node while find station: ",st["zhanming"])
            total += node["interval"]
            former_station = st

        # print("total time ok")
        return total

    def name(self):
        return self._name

    def setName(self,name:str):
        self._name = name

    def downPass(self):
        return self._down_pass

    def upPass(self):
        return self._up_pass

    def addDownPass(this,name:str):
        this._down_pass.append(str)

    def addUpPass(self,name:str):
        self._up_pass.append(name)

    def isDownPassed(self,name:str):
        if name in self._down_pass:
            return True
        return False

    def isUpPassed(self,name:str):
        if name in self._up_pass:
            return True
        return False

    def setWidget(self,widget):
        self._widget = widget

    def widget(self):
        try:
            return self._widget
        except AttributeError:
            self._widget = None
            return None

    def resetAllPassed(self):
        self._down_pass = []
        self._up_pass = []
        for station in self._line.stations:
            if not self._line.DownVia & station["direction"] and station["zhanming"] not in self._down_pass:
                self._down_pass.append(station["zhanming"])
            if not self._line.UpVia & station["direction"] and station["zhanming"] not in self._up_pass:
                self._up_pass.append(station["zhanming"])
        # print("reset pass",self._down_pass,self._up_pass)

    def coveredStations(self,down:bool):
        """
        返回某方向的覆盖车站表.
        :param down:
        :return:
        """
        stations:list = self._line.stations[:]
        if not down:
            stations.reverse()

        covered = []
        former:dict = None

        dir = 0x1 if down else 0x2

        for st in stations:
            if not dir&st["direction"]:
                continue
            if former is None:
                former = st
                continue

            node = self.getInfo(former["zhanming"],st["zhanming"])
            if node is not None:
                if former["zhanming"] not in covered:
                    covered.append(former["zhanming"])
                covered.append(st["zhanming"])

            former=st

        return covered

    def line(self):
        return self._line


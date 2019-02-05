"""
列车信息模块
时间统一使用：datetime.datetime实例
"""
from Timetable_new.checi3 import Checi
from datetime import datetime,timedelta
from Timetable_new.utility import judge_type,stationEqual,strToTime
import re

import cgitb
cgitb.enable(format='text')

class Train():
    """
    列车信息类，数据结构：
    List<Str> checi;
    Str sfz,zdz;
    Str type;
    List<Dict> timetable;
    Dict UI; #显示设置，如线形，颜色等
    bool down;//本线的上下行
    QtWidgets.QGraphicsViewPathItem pathItem;
    QtWidgets.QGraphicsViewItem labelItem;

    Timetable 中Dict数据结构：
    dict = {
            "zhanming":name,
            "ddsj":ddsj,
            "cfsj":cfsj
        }
    """
    def __init__(self,checi_full='',checi_down='',checi_up='',sfz='',zdz='',origin=None):
        self.item = None
        self.down = None
        self.shown = True  #是否显示运行线
        self._localFirst=None
        self._localLast=None
        if origin is not None:
            #从既有字典读取数据
            self.loadTrain(origin)
        else:
            print("新")
            self.checi = [checi_full,checi_down,checi_up]
            self.type = ''
            self.timetable = []
            self.sfz=sfz
            self.zdz=zdz
            self.UI={}

            if not checi_down and not checi_up and checi_full:
                #没有给出上下行车次，重新拆分初始化
                tempcheci = Checi  (checi_full)
                self.checi[1]=tempcheci.down
                self.checi[2]=tempcheci.up
                self.type = tempcheci.type
            self.autoType()
            # self._autoUI()


    def loadTrain(self,origin):
        self.checi = origin["checi"]
        self.UI = origin["UI"]
        self.timetable = origin["timetable"]
        self.type = origin["type"]
        self.sfz = origin["sfz"]
        self.zdz = origin["zdz"]
        self._localFirst = origin.get('localFirst',None)
        self._localLast = origin.get('localLast',None)

        try:
            origin["shown"]
        except KeyError:
            self.shown=True
        else:
            self.shown=origin["shown"]

        self._transfer_time()
        #如果UI为空，自动初始化
        if not self.type:
            self.autoType()
        if not self.UI:
            pass
            #self._autoUI()

    def _transfer_time(self):
        """
        将读取到的时刻中的时间转为datetime.datetime对象
        """
        for dict in self.timetable:
            if isinstance(dict["ddsj"],str):
                ddsj = strToTime(dict['ddsj'])

                cfsj = strToTime(dict['cfsj'])

                dict["ddsj"] = ddsj
                dict["cfsj"] = cfsj

    def setType(self,type:str):
        self.type = type

    def autoType(self):
        checi = self.checi[1]
        if not checi or checi == 'null':
            checi = self.checi[2]
        if not checi:
            return
        try:
            self.type = judge_type(checi)
        except:
            print("judge checi",checi,self.checi)
            #traceback.print_exc()
        # print(self.type)

    def _autoUI(self):
        #默认颜色
        if self.type == '快速':
            self.UI["Color"] = '#FF0000'
        elif self.type == '特快':
            self.UI["Color"] = '#0000FF'
        else:
            self.UI["Color"] = ''

        self.UI["LineWidth"] = 2

    def fullCheci(self):
        return self.checi[0]

    def downCheci(self):
        return self.checi[1]

    def upCheci(self):
        return self.checi[2]

    def localCheci(self):
        if self.down:
            return self.downCheci()
        elif self.isDown() == False:
            return self.upCheci()
        else:
            return self.fullCheci()

    def addStation(self,name:str,ddsj,cfsj,auto_cover=False,to_end=True):
        #增加站。暂定到达时间、出发时间用datetime类。
        if isinstance(ddsj,str):
            ddsj = strToTime(ddsj)

            cfsj = strToTime(cfsj)

        dict = {
            "zhanming":name,
            "ddsj":ddsj,
            "cfsj":cfsj
        }
        if auto_cover:
            former_dict = self.stationDict(name)
            if former_dict is not None:
                index = self.timetable.index(former_dict)
                self.timetable[index] = dict
            else:
                if to_end:
                    self.timetable.append(dict)
                else:
                    self.timetable.insert(0,dict)
        else:
            if to_end:
                self.timetable.append(dict)
            else:
                self.timetable.insert(0, dict)

    def setStartEnd(self,sfz='',zdz=''):
        if sfz:
            self.sfz=sfz
        if zdz:
            self.zdz=zdz

    def station_infos(self):
        for st in self.timetable:
            yield st["zhanming"],st["ddsj"],st["cfsj"]

    def color(self,graph=None):
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

    def setIsShow(self,show:bool,affect_item=True):
        """
        注意，affect_item只影响True->False情况
        """
        if self.isShow() == show:
            # 未做改动，直接返回
            return
        self.shown = show
        if not affect_item:
            return
        if self.item:
            try:
                self.item.setVisible(show)
            except:
                pass

    def show(self):
        #调试用
        print(self.checi)
        print(self.sfz,self.zdz)
        print(self.type,self.UI)
        for i,dict in enumerate(self.timetable):
            print(dict["zhanming"],dict["ddsj"],dict["cfsj"])
            if i > 3:
                print("...")
                break

    def outInfo(self):
        #输出字典结构，仅用于文件
        info = {
            "checi":self.checi,
            "UI":self.UI,
            "type":self.type,
            "timetable":[],
            "sfz":self.sfz,
            "zdz":self.zdz,
            "shown":self.shown,
            "localFirst":self._localFirst,
            "localLast":self._localLast,
        }
        for dict in self.timetable:
            ddsj:datetime = dict["ddsj"]
            cfsj:datetime = dict["cfsj"]
            try:
                outDict = {
                "zhanming":dict["zhanming"],
                "ddsj":ddsj.strftime("%H:%M:%S"),
                "cfsj":cfsj.strftime("%H:%M:%S"),
                "note":dict.setdefault('note','')
            }
            except TypeError as e:
                print(dict,repr(e))
                print(type(dict["ddsj"].strftime))
            info["timetable"].append(outDict)
        return info

    def trainType(self):
        return self.type

    def setItem(self,item):
        self.item = item

    def getItem(self):
        return self.item

    def setIsDown(self,down):
        self.down = down

    def isDown(self,auto_guess=False,graph=None,default=None):
        not_decided = False
        if self.down is None:
            not_decided = True
        if not_decided and auto_guess:
            self.autoDown(graph)
        if not_decided and default is not None:
            return default

        return self.down

    def setUI(self,color=None,width=None):
        if color is not None:
            self.UI["Color"] = color
        if width is not None:
            self.UI["LineWidth"] = width

    def stationTime(self,name:str):
        st = self.stationDict(name)
        if st is None:
            raise Exception("No such station in timetable.")
        return st["ddsj"],st["cfsj"]

    def gapBetweenStation(self,st1,st2,graph=None):
        """
        返回两站间的运行时间
        :param st1:
        :param st2:
        :param assure_postive:
        :param graph:依赖的线路。不为None表示允许向前后推断邻近站。
        :return: seconds:int
        """
        st_dict1,st_dict2 = None,None
        for dict in self.timetable:
            if stationEqual(st1,dict['zhanming']):
                st_dict1 = dict
            elif stationEqual(st2,dict['zhanming']):
                st_dict2 = dict

        if st_dict1 is None or st_dict2 is None:
            if graph is None:
                raise Exception("No such station gap.",st1,st2)
            else:
                ignore_f = [st1,st2]
                station = st1
                while st_dict1 is None:
                    station = graph.adjacentStation(station,ignore_f)
                    ignore_f.append(station)
                    if station is None:
                        break
                    st_dict1 = self.stationDict(station)

                ignore_l = [st1,st2]
                station = st2
                while st_dict2 is None:
                    station = graph.adjacentStation(station,ignore_l)
                    ignore_l.append(station)
                    st_dict2 = self.stationDict(station)


        dt = st_dict2["ddsj"]-st_dict1["cfsj"]
        return dt.seconds
        #if dt.days<0:
        #    dt = st_dict1["ddsj"]-st_dict2["cfsj"]
        #    return dt.seconds
        #else:
        #    return dt.seconds

    def stationCount(self):
        return len(self.timetable)

    def setCheci(self,full,down,up):
        # print("set checi:",full,down,up)
        self.checi = [full,down,up]

    def setFullCheci(self,name:str):
        try:
            checi = Checi(name)
        except:
            down = ''
            up = ''
        else:
            down = checi.down
            up = checi.up
        self.setCheci(name,down,up)
        # print(name,down,up)

    def clearTimetable(self):
        self.timetable = []

    def downStr(self):
        if self.isDown() is True:
            return '下行'
        elif self.isDown() is False:
            return '上行'
        else:
            return '未知'

    def updateLocalFirst(self,graph):
        for st in self.timetable:
            name = st["zhanming"]
            for station in graph.line.stations:
                if stationEqual(name,station["zhanming"]):
                    self._localFirst = name
                    return name

    def localFirst(self,graph):
        if self._localFirst is not None:
            return self._localFirst
        else:
            return self.updateLocalFirst(graph)

    def updateLocalLast(self,graph):
        """
        2019.02.03修改：时间换空间，计算并维护好数据。原函数名: localLast
        """
        for st in reversed(self.timetable):
            name = st["zhanming"]
            for station in graph.line.stations:
                if stationEqual(name,station["zhanming"]):
                    self._localLast = name
                    return name

    def localLast(self,graph):
        if self._localLast is not None:
            return self._localLast
        else:
            return self.updateLocalLast(graph)

    def intervalCount(self,graph,start,end):
        count = 0
        started=False
        for st in self.timetable:
            name = st["zhanming"]
            if stationEqual(name,start):
                started=True
            if not started:
                continue
            if graph.stationInLine(name):
                count+=1
            if stationEqual(name,end):
                break
        return count

    def localCount(self,graph):
        """
        只由车次信息计算过程调用，暂时保留线性算法
        """
        count = 0
        for st in self.timetable:
            name = st["zhanming"]
            if graph.stationInLine(name):
                count+=1
        return count

    def intervalStopCount(self,graph,start,end):
        count = 0
        started = False
        for st in self.timetable:
            name = st["zhanming"]
            if stationEqual(name,start):
                started = True
            if not started:
                continue
            if graph.stationInLine(name) and (st["cfsj"]-st["ddsj"]).seconds!=0 and\
                name not in (start,end):
                count+=1
            if stationEqual(name,end):
                break
        return count

    def localMile(self,graph):
        try:
            return graph.gapBetween(self.localFirst(graph),self.localLast(graph))
        except:
            return 0

    def localTime(self,graph):
        firstDD,_ = self.stationTime(self.localFirst(graph))
        _,lastCF = self.stationTime(self.localLast(graph))
        dt = lastCF - firstDD
        return dt.seconds

    def intervalRunStayTime(self,graph,start,end):
        """
        不算起点和终点
        """
        started = False
        running = 0
        stay = 0
        former = None

        for st in self.timetable:
            if stationEqual(st["zhanming"],start):
                started = True

            if not started:
                continue

            if former is None:
                former = st
                continue
            running += (st["ddsj"] - former["cfsj"]).seconds
            thisStay=(st["cfsj"] - st["ddsj"]).seconds
            if st["zhanming"] not in (start,end):
                stay += thisStay
            former = st
            if stationEqual(st["zhanming"],end):
                break
        # print(running, stay)
        return running, stay

    def localRunStayTime(self,graph):
        """
        计算本线纯运行时间的总和、本线停站时间总和。算法是从本线入图点开始，累加所有区间时分。
        """
        started = False
        running = 0
        stay = 0
        former = None
        for st in self.timetable:
            if stationEqual(st["zhanming"],self.localFirst(graph)):
                started = True
            if not started:
                continue
            if former is None:
                former = st
                stay += (st["cfsj"] - st["ddsj"]).seconds
                continue
            running += (st["ddsj"] - former["cfsj"]).seconds
            stay += (st["cfsj"] - st["ddsj"]).seconds
            former = st
            if stationEqual(st["zhanming"],self.localLast(graph)):
                break
        # print(running, stay)
        return running, stay

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

    def autoDown(self,graph):
        in_stations = []
        for st in self.timetable:
            if graph.stationExisted(st["zhanming"]):
                in_stations.append(st["zhanming"])
            if len(in_stations) == 2:
                if graph.line.isDownGap(in_stations[0],in_stations[1]):
                    self.setIsDown(True)
                    return
                else:
                    self.setIsDown(False)
                    return

    def jointTrain(self,train,former:bool,graph):
        """
        将train连接到本车次上。
        """
        if former:
            for st in reversed(train.timetable):
                if not graph.stationInLine(st["zhanming"]):
                    continue  #非本线站点不处理，以免出错
                find = False
                for node in self.timetable:
                    if stationEqual(st["zhanming"],node["zhanming"],strict=True):
                        find = True
                        break
                if find:
                    continue
                self.timetable.insert(0,st)
        else:
            for st in train.timetable:
                if not graph.stationInLine(st["zhanming"]):
                    continue  #非本线站点不处理，以免出错
                find = False
                for node in self.timetable:
                    if stationEqual(st["zhanming"],node["zhanming"],strict=True):
                        find = True
                        break
                if find:
                    continue
                self.timetable.append(st)

    def setStationDeltaTime(self,name:str,ds_int):
        st_dict = None
        for st in self.timetable:
            if stationEqual(st["zhanming"],name):
                st_dict = st
                break

        if st_dict is None:
            raise Exception("No such station",name)

        dt = timedelta(days=0,seconds=ds_int)
        st_dict["ddsj"] += dt
        st_dict["cfsj"] += dt

    def stationDict(self,name,strict=False):
        for st in self.timetable:
            if stationEqual(st["zhanming"],name,strict):
                return st
        return None

    def isSfz(self,name:str):
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

    def translation(self,checi:str,dt_time:timedelta):
        """
        复制当前车次数据，返回新的Train对象。checi已经保证合法。
        :param dt_int:
        :return:
        """
        # print("train::translation",checi,dt_time,self.start_time())
        from copy import copy,deepcopy
        newtrain = Train()
        newtrain.setFullCheci(checi)
        newtrain.setStartEnd(self.sfz,self.zdz)
        newtrain.autoType()
        newtrain.timetable = deepcopy(self.timetable)
        newtrain.UI = copy(self.UI)
        newtrain.setIsDown(self.down)

        for st_dict in newtrain.timetable:
            st_dict["ddsj"] += dt_time
            st_dict["cfsj"] += dt_time

        return newtrain

    def start_time(self):
        return self.timetable[0]["ddsj"]

    def delNonLocal(self,graph):
        """
        删除非本线站点信息
        :param graph:
        :return:
        """
        toDel = []
        for st in self.timetable:
            if not graph.stationInLine(st["zhanming"]):
                toDel.append(st)
        for st in toDel:
            self.timetable.remove(st)

    def coverData(self,train):
        """
        用train的信息覆盖本车次信息
        :param train:
        :return:
        List<Str> checi;
    Str sfz,zdz;
    Str type;
    List<Dict> timetable;
    Dict UI; #显示设置，如线形，颜色等
    bool down;//本线的上下行
    QtWidgets.QGraphicsViewPathItem pathItem;
    QtWidgets.QGraphicsViewItem labelItem;
        """
        from copy import copy,deepcopy
        self.checi = copy(train.checi)
        self.sfz,self.zdz = train.sfz,train.zdz
        self.type = train.type
        self.UI = copy(train.UI)
        self.down = train.down
        self.timetable = deepcopy(train.timetable)

    def relativeError(self,ruler):
        """
        计算本车次关于标尺的相对误差。返回百分比。非本线站点已经删除。
        """
        former=None
        this_time=0
        error_time=0
        for st_dict in self.timetable:
            if former is None:
                former=st_dict
                continue
            interval_ruler=ruler.getInfo(former["zhanming"],st_dict['zhanming'],allow_multi=True)
            try:
                int_ruler=interval_ruler["interval"]+interval_ruler["start"]+interval_ruler["stop"]
                interval_this=self.gapBetweenStation(former["zhanming"],st_dict["zhanming"])
                this_time+=interval_this
                error_time+=abs(int_ruler-interval_this)
            except TypeError:
                print("None info",self.fullCheci(),former["zhanming"],st_dict["zhanming"])
            former=st_dict
        try:
            return error_time/this_time
        except ZeroDivisionError:
            return 0.0

    def detectPassStation(self,graph,ruler,toStart,toEnd):
        """
        按标尺推定通过站的时刻。保证非本线站已经删除。
        """
        if not self.timetable:
            return
        new_timetable=[]
        #将针对线路的toStart、End转变为针对本次列车的
        if self.down:
            #本次列车下行，toStart对应始发，toEnd对应终到
            fromStart=toStart and not graph.stationInLine(self.sfz)
            toEnd=toEnd and not graph.stationInLine(self.zdz)
        else:
            toEnd = toEnd and not graph.stationInLine(self.sfz)
            fromStart = toStart and not graph.stationInLine(self.zdz)
        first_in_graph = self.timetable[0] #图定本线入图结点
        firstStopped=bool((first_in_graph['ddsj']-first_in_graph['cfsj']).seconds)
        last_in_graph = self.timetable[-1]  #图定本线出图
        lastStopped=bool((last_in_graph['ddsj']-last_in_graph['cfsj']).seconds)

        last_tudy_dict=None  #上一个有效图定站点
        interval_queue=[]
        for name in graph.stations(not self.down):
            if not int(0b01 if self.down else 0b10) & graph.stationDirection(name):
                #本方向不通过本站点
                # print("不通过",name)
                continue
            this_dict=self.stationDict(name)
            if this_dict is not None:
                #本站在图定时刻表中
                if not interval_queue:
                    #区间没有站，直接跳过。这里也直接跳过了开头的站
                    new_timetable.append(this_dict)
                    last_tudy_dict = this_dict
                    continue
                #计算一个本区间实际运行时分和图定运行时分的比例
                if not last_tudy_dict:
                    new_timetable.append(this_dict)
                    last_tudy_dict = this_dict
                    interval_queue=[]
                    continue
                real_interval=self.gapBetweenStation(last_tudy_dict['zhanming'],name)
                ruler_interval_dict=ruler.getInfo(last_tudy_dict['zhanming'],name,allow_multi=True)
                if not ruler_interval_dict:
                    #理论上这是不会发生的
                    new_timetable.append(this_dict)
                    last_tudy_dict = this_dict
                    interval_queue = []
                    continue
                ruler_interval=ruler_interval_dict['interval']
                if self.stationStopped(last_tudy_dict):
                    real_interval-=ruler_interval_dict['start']
                if self.stationStopped(this_dict):
                    real_interval-=ruler_interval_dict['stop']
                try:
                    rate=real_interval/ruler_interval
                except ZeroDivisionError:
                    new_timetable.append(this_dict)
                    last_tudy_dict = this_dict
                    interval_queue = []
                    continue
                for name in interval_queue:
                    ruler_node=ruler.getInfo(last_tudy_dict['zhanming'],name,allow_multi=True)
                    new_dict=self.makeStationDict(name,rate,last_tudy_dict,ruler_node)
                    new_timetable.append(new_dict)
                new_timetable.append(this_dict)
                last_tudy_dict = this_dict
                interval_queue=[]
                continue

            if last_tudy_dict is None:
                #本次列车尚未入图
                if not fromStart:
                    continue
                gap_dict=ruler.getInfo(name,first_in_graph['zhanming'],allow_multi=True)
                gap_int=gap_dict['interval']
                if firstStopped:
                    #图定第一站停了车，加上一个停车附加
                    gap_int+=gap_dict['stop']
                dt=timedelta(days=0,seconds=gap_int)
                this_time=first_in_graph['ddsj']-dt
                this_cf=first_in_graph['ddsj']-dt
                new_dct = {
                    "zhanming":name,
                    "ddsj":this_time,
                    "cfsj":this_cf,
                    'note': '推定',
                }
                new_timetable.append(new_dct)
            #本次列车已经入图，且本站不在图定运行图中，加入队列，遇到中止时刻处理
            interval_queue.append(name)

        if toEnd and interval_queue:
            for name in interval_queue:
                ruler_node = ruler.getInfo(last_tudy_dict['zhanming'], name, allow_multi=True)
                new_dict = self.makeStationDict(name, 1.0, last_tudy_dict, ruler_node)
                new_timetable.append(new_dict)
        self.timetable=new_timetable

    def stationInTimetable(self,name:str,strict=False):
        return bool(filter(lambda x:stationEqual(name,x,strict),
                           map(lambda x:x['zhanming'],self.timetable)))

    def stationStopped(self,station:dict):
        """
        注意，输入的是字典
        """
        return bool((station['ddsj']-station['cfsj']).seconds)

    def makeStationDict(self,name,rate:float,reference:dict,ruler_node:dict):
        """
        从参考点开始，移动interval_sec秒作为新车站的通过时刻。
        """
        # print("detect",self.fullCheci(),"station",name,'reference',reference)
        interval_sec = int(rate*ruler_node['interval'])
        if interval_sec > 0:
            #从参考车站开始往【后】推定时间
            nextStopped_bool = self.stationStopped(reference)
            if nextStopped_bool:
                interval_sec += ruler_node['start']
            dt=timedelta(days=0,seconds=interval_sec)
            this_time=reference['cfsj']+dt
            this_cf=reference['cfsj']+dt
            return {
                'zhanming':name,
                'ddsj':this_time,
                'cfsj':this_cf,
                'note': '推定',
            }
        else:
            lastStopped_bool = self.stationStopped(reference)
            if lastStopped_bool:
                interval_sec-=ruler_node['stop']
            dt=timedelta(days=0,seconds=-interval_sec)
            ddsj=reference['ddsj']-dt
            cfsj=reference['ddsj']-dt
            return {
                'zhanming':name,
                'ddsj':ddsj,
                'cfsj':cfsj,
                'note':'推定',
            }

    def stationStopBehaviour(self,station:str):
        """
        返回本站停车类型的文本。包括：通过，停车，始发，终到，不通过。
        """
        dct = self.stationDict(station)
        if not dct:
            return '不通过'
        elif (dct['ddsj']-dct['cfsj']).seconds != 0:
            return '停车'
        elif self.isSfz(station):
            return '始发'
        elif self.isZdz(station):
            return '终到'
        else:
            return '通过'

    def stationBefore(self,st1,st2):
        """
        返回st1是否在st2之前。
        """
        findStart = False
        for st_dict in self.timetable:
            if stationEqual(st1,st_dict['zhanming']):
                findStart = True
            if stationEqual(st2,st_dict['zhanming']):
                if findStart:
                    return True
                else:
                    return False
        return False

    def intervalPassedCount(self,graph,start=None,end=None):
        """
        计算start-end区间跨越的站点的个数。start,end两站必须在时刻表上。缺省则使用本线第一个/最后一个站。
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
            start,end = self.updateLocalFirst(graph),self.updateLocalLast(graph)
            if start is None:
                return 0
            startIdx = graph.stationIndex(start)
            endIdx = graph.stationIndex(end)
        if startIdx >= endIdx:
            startIdx,endIdx = endIdx,startIdx
        cnt = 0
        stations = list(map(lambda x:x["zhanming"],self.timetable))
        for i in range(startIdx,endIdx+1):
            name = graph.stationByIndex(i)['zhanming']
            if (graph.stationDirection(name) & self.binDirection()) and name not in stations:
                cnt += 1
        return cnt

    def binDirection(self,default=0x11):
        """
        返回通过方向的常量表示形式。
        """
        if self.down is True:
            return 0b01
        elif self.down is False:
            return 0b10
        else:
            return default

    def updateColor(self):
        """
        由颜色面板修改调用。重绘运行线。
        """
        if self.item is not None:
            self.item.setColor()

    def __str__(self):
        return f"Train object at <0x{id(self):X}> {self.fullCheci()}  {self.sfz}->{self.zdz}"


if __name__ == '__main__':
    #debug only
    train = Train("K9484/1/4")
    train.setStartEnd(sfz='成都',zdz='攀枝花')
    time1 = datetime.strptime("18:00","%H:%M")
    train.addStation("成都",time1,time1)
    train.addStation("安靖","18:12","18:13")

    info = train.outInfo()

    newtrain = Train(origin=info)
    newtrain.show()

"""
此文件从train_graph_db项目迁移过来，并且以后以这个文件为主要文件。
初期暂不支持保存和读取文件。

列车运行图数据库系统基础数据类，基于networkX.digraph格式，按照OO要求进行封装。
有向边数据格式：dict
dict{
    "name":str,  //线路名称。2021.01.02新增
    "length":float, //区间距离
    "down":bool,//本区间是否属于下行区间
    "rulers": dict<dict>{
        str /*标尺名称*/:{
            "interval":int, //区间运行秒数
            "start":int, //起步附加秒数
            "end":int, //停车附加秒数
        }
    }, //标尺数据列表
    "forbid":dict{
        "start":str,//天窗开始时间
        "end":str,//天窗结束时间
    }, //天窗数据，可选。初期直接给None。
    "forbid2": 同上,
}
"""
import networkx as nx
from typing import List,Union
from ..data import *
from ..linedb.lineLib import LineLib

class RailNet:
    def __init__(self):
        self._digraph:nx.DiGraph = None
        self._filename = 'data/railnet.gml'

    def reset(self):
        self._digraph = nx.DiGraph()

    def read(self,filename=None):
        if filename is None:
            filename = self._filename
        try:
            # self._digraph = nx.read_gml(filename)
            self._digraph = nx.read_yaml(filename)
        except Exception as e:
            print("read failed",repr(e))
            self._digraph = nx.DiGraph()

    def backup(self,filename=None):
        if filename is None:
            filename = self._filename+"_backup"
        nx.write_yaml(self._digraph,filename)

    def save(self,filename=None):
        if filename is None:
            filename = self._filename
        nx.write_yaml(self._digraph,filename)

    def graph(self)->nx.DiGraph:
        return self._digraph

    def loadLineLib(self,lib:LineLib):
        """
        清空数据，并读取lib所示数据库中所有线路。
        """
        self._digraph.clear()
        for line in lib.lines():
            self.addLine(line)

    def addLine(self,line:Line):
        """
        2020.02.02新增，
        从pyETRC线路文件中读取数据。
        2021.01.02：新增线路名称作为数据之一。但暂时只作为附加数据（不作为合并条件等）
        """
        last_st_dict = None
        # 下行
        for st_dict in line.stationDicts():
            if last_st_dict is None:
                last_st_dict = st_dict
                continue
            if not st_dict['direction'] & Line.DownVia:
                continue
            # 添加下行边数据
            dct_down = {
                "name":line.name,
                "length":abs(st_dict['licheng']-last_st_dict['licheng']),
                "down":True,
                "rulers":{},
                "forbid":line.forbid.getInfo(
                    last_st_dict['zhanming'],st_dict['zhanming']),
                "forbid2":line.forbid2.getInfo(
                    last_st_dict['zhanming'],st_dict['zhanming']),
            }
            for ruler in line.rulers:
                node = ruler.getInfo(last_st_dict['zhanming'],st_dict['zhanming'])
                if node:
                    dct_down["rulers"][ruler.name()] = node
            self.addInterval(last_st_dict['zhanming'],st_dict['zhanming'],dct_down)
            last_st_dict = st_dict

        # 上行
        last_st_dict = None
        for st_dict in reversed(line.stations):
            if last_st_dict is None:
                last_st_dict = st_dict
                continue
            if not st_dict['direction'] & Line.UpVia:
                continue
            dct_up = {
                "name":line.name,
                "length":line.gapBetween(last_st_dict['zhanming'],st_dict['zhanming']),
                "down":False,
                "rulers":{},
                "forbid":line.forbid.getInfo(
                    last_st_dict['zhanming'],st_dict['zhanming']),
                "forbid2":line.forbid2.getInfo(
                    last_st_dict['zhanming'],st_dict['zhanming']),
            }
            for ruler in line.rulers:
                node = ruler.getInfo(last_st_dict['zhanming'],st_dict['zhanming'])
                if node:
                    dct_up["rulers"][ruler.name()] = node
            self.addInterval(last_st_dict['zhanming'], st_dict['zhanming'], dct_up)

            last_st_dict = st_dict

    def addInterval(self,start,end,attr:dict,cover=False):
        """
        将数据添加到图中。如果边已经存在，整理数据。
        cover：为False时遇到冲突的值忽略新的值；为True时遇到冲突值覆盖原值。
        """
        ed = self._digraph.get_edge_data(start,end,default=None)
        if ed is None:
            self._digraph.add_edge(start,end,**attr)
        else:
            self._digraph.remove_edge(start,end)
            if cover:
                ed['rulers'].update(attr['rulers'])
                del attr['rulers']
                ed.update(attr)
                self._digraph.add_edge(start,end,**ed)
            else:
                attr['rulers'].update(ed['rulers'])
                del ed['rulers']
                attr.update(ed)
                self._digraph.add_edge(start,end,**attr)

    def outLine(self,path:List[str],withRuler=True,minRulerCount=0)->Line:
        """
        按照给出的关键路径搜索路径，返回Line对象。path对应的路径是下行，反之为下行。
        假定：上下行路径指向相同的路径。
        2020.01.26新增：同时导出上行里程为对里程counter。
        """
        line = Line()
        if len(path)<=1:
            return line

        stations = path[:1]
        for i in range(1,len(path)):
            subpath = nx.shortest_path(self._digraph,path[i-1],path[i],weight='length')
            stations.extend(subpath[1:])

        extend_mile = 0
        line.addStation_by_info(stations[0],0)  # 此时线路只有一个站
        line.stations[0]['counter'] = 0.0
        # 添加下行站表
        for i in range(1,len(stations)):
            previous,current = stations[i-1:i+1]
            data = self._digraph.get_edge_data(previous,current)
            extend_mile += data['length']
            dct = {
                "zhanming":current,
                "licheng":extend_mile,
                "dengji":4,
                "direction":Line.DownVia,
            }
            line.addStationDict(dct)
            if withRuler:
                for n,r in data["rulers"].items():
                    ruler = line.rulerByName(n)
                    if ruler is None:
                        ruler=line.addEmptyRuler(n,True)
                    ruler.addStation_info(previous,current,r["interval"],r["start"],r["stop"])

        # 添加上行站表。重新找路径。
        # 对里程先按照负数添加。
        path = path[::-1]
        for i in range(1,len(path)):
            subpath = nx.shortest_path(self._digraph,path[i-1],path[i],weight='length')
            stations.extend(subpath[1:])

        current_mile = line.lineLength()
        counter_extend = 0  # 反向延长公里数
        for i in range(1,len(stations)):
            previous,current = stations[i-1:i+1]
            st_dict = line.stationDictByName(current,strict=True)
            data = self._digraph.get_edge_data(previous,current)
            counter_extend -= data['length']
            if st_dict is not None:
                st_dict["direction"] |= Line.UpVia
                st_dict['counter'] = counter_extend
            else:
                current_mile += data['length']
                dct = {
                    "zhanming": current,
                    "licheng": counter_extend,
                    "counter": counter_extend,
                    "dengji": 4,
                    "direction": Line.UpVia,
                }
                line.addStationDict(dct)
            if withRuler:
                for n,r in data["rulers"].items():
                    ruler=line.rulerByName(n)
                    if ruler is None:
                        ruler=line.addEmptyRuler(n,True)
                    ruler.addStation_info(previous,current,r["interval"],r["start"],r["stop"])
            for ruler in line.rulers.copy():
                if ruler.count() < minRulerCount:
                    line.rulers.remove(ruler)
        counter_length = -counter_extend
        # 处理对里程。只有上行通过的站，里程也按照对里程处置。
        for st_dict in line.stations:
            if st_dict.get('counter') is not None:
                st_dict['counter'] += counter_length
            if st_dict['direction'] == Line.UpVia:
                st_dict['licheng'] += counter_length
        # 按原里程排序，此操作暂不确定
        line.stations.sort(key=lambda x:x['licheng'])
        return line

    def outGraph(self, path: List[str], filename=None, withRuler=True, minRulerCount=0) -> Graph:
        line = self.outLine(path,withRuler,minRulerCount)
        graph = Graph()
        graph.setLine(line)
        if filename:
            graph.save(filename)
        return graph

    def stationExists(self, name:str)->bool:
        """
        返回指定站名是否存在于图中。
        """
        return self._digraph.adj.get(name,None) is not None

    def adjStations(self, name:str)->dict:
        """
        返回指定站的邻接站及边信息。对digraph相关人操作的封装。
        :param name: 站名
        :return:
        """
        return self._digraph.adj.get(name)

    def getLine(self, first,second,lineName,firstAdj:float,down:bool)->Line:
        """
        2021.01.14 由两个给定的站，用类似DFS的方法找到整条线的数据。
        【注意】暂定只考虑了下行。
        :param first: 首站站名。【不包含在返回值中】
        :param second: 次站站名
        :param lineName: 指定线路名称
        :return:
        """
        line = Line(lineName)
        passed = {first,second}
        line.addStation_by_info(first, 0)
        line.setStationViaDirection(first,Line.DownVia)
        line.addStation_by_info(second, firstAdj)
        line.setStationViaDirection(second,Line.DownVia)
        self._get_line_rec(second,passed,line,down)
        linerev = Line(lineName)
        end = line.lastStationName()
        linerev.addStation_by_info(end,0)
        linerev.setStationViaDirection(end,Line.DownVia)
        # 以最多超出下行10个站来搜索反向的线路
        passed = {end}
        self._get_rev_line_rec(end,passed,linerev,first,max_cnt=line.stationCount()+10, down=not down)
        if linerev.lastStationName() != first:
            # 说明反向的搜索并没有收敛，也就是所给second不是双向通过站。
            while not line.stationExisted(linerev.lastStationName()):
                linerev.delStation(linerev.lastStationName())
        line.mergeCounter(linerev)
        return line

    def _get_line_rec(self,start:str, passed:set, line:Line, down:bool):
        """
        递归DFS查找线路。暂时只考虑单方向
        :param start: 已经包含在line中，且确定存在。
        :param passed: 已选过的站，不能重复选择
        :param line: 按传引用语义
        :param max_cnt: 最大站数。
        :return:
        """
        for nd,ed in self._digraph.adj[start].items():
            if ed['name'] == line.name and nd not in passed and ed['down'] == down:
                line.addStation_by_info(nd,line.lineLength()+ed['length'])
                line.setStationViaDirection(nd,Line.DownVia)
                passed.add(nd)
                self._get_line_rec(nd,passed,line,down)
                return

    def _get_rev_line_rec(self, start:str, passed:set, line:Line, end:str, max_cnt:int, down:bool):
        """
        用相似的算法搜索反向的线路。返回【独立】的反向线路数据。
        :param start: 反向线路起点（原终点）
        :param passed: 已经搜过的站
        :param line: 反向线路
        :param end: 反向线路终点（原起点）
        :param max_cnt: 最大站数
        """
        if start == end or line.stationCount() > max_cnt:
            return
        for nd,ed in self._digraph.adj[start].items():
            if ed['name'] == line.name and nd not in passed and ed['down'] == down:
                line.addStation_by_info(nd,line.lineLength()+ed['length'])
                line.setStationViaDirection(nd,Line.DownVia)
                passed.add(nd)
                self._get_rev_line_rec(nd,passed,line,end,max_cnt,down)
                return





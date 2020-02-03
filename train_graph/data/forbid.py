"""
天窗或禁行时段数据结构。此数据集成在line内。
2020年1月23日注记：
每个运行图中存在两个实例对象，即【综合维修天窗】和【综合施工天窗】，在line中用forbid和forbid2表示。
其基础数据没有区别，都调用本类。
"""
from datetime import datetime,timedelta
from Timetable_new.utility import stationEqual
from typing import Union

class Forbid:
    """
    分为综合维修天窗和综合施工天窗，属于哪一类由RTTI给出。
    数据结构：
    Line& _line; //线路数据的引用
    bool _different;//上下行分设
    list<dict> _nodes;
    dict{
        "fazhan":str,
        "daozhan":str,
        "begin":datetime.datetime,
        "end":datetime.datetime
    }
    """
    def __init__(self,line,different=True):
        self._line = line
        self._different = different
        self._nodes = []
        self._downItems = []
        self._upItems = []
        self._upShow = False
        self._downShow = False

    def loadForbid(self,origin:Union[dict,None]):
        if origin is None:
            return
        self._different=origin["different"]
        self._nodes=origin["nodes"]
        self._upShow = origin["upShow"]
        self._downShow = origin["downShow"]
        for gap_info in self._nodes:
            if not isinstance(gap_info["begin"],str):
                continue
            try:
                gap_info["begin"] = datetime.strptime(gap_info["begin"],'%H:%M:%S')
            except:
                gap_info["begin"] = datetime.strptime(gap_info["begin"], '%H:%M')

            try:
                gap_info["end"] = datetime.strptime(gap_info["end"],'%H:%M:%S')
            except:
                gap_info["end"] = datetime.strptime(gap_info["end"], '%H:%M')

    def outInfo(self):
        from copy import deepcopy
        nodes_cpy = deepcopy(self._nodes)
        for gap_info in nodes_cpy:
            gap_info["begin"] = gap_info["begin"].strftime('%H:%M')
            gap_info["end"] = gap_info["end"].strftime('%H:%M')

        data = {
            "different":self._different,
            "nodes":nodes_cpy,
            "upShow":self._upShow,
            "downShow":self._downShow,
        }
        return data

    def clear(self):
        self._nodes = []

    def addForbid(self,fazhan:str,daozhan:str,begin:datetime,end:datetime,auto_cover=False):
        if auto_cover:
            oldNode = self.getInfo(fazhan,daozhan)
            if oldNode is not None:
                self._nodes.remove(oldNode)

        newNode = {
            "fazhan":fazhan,
            "daozhan":daozhan,
            "begin":begin,
            "end":end,
        }
        self._nodes.append(newNode)

    def getInfo(self,fazhan,daozhan)->dict:
        for node in self._nodes:
            if stationEqual(node["fazhan"],fazhan) and stationEqual(node["daozhan"],daozhan):
                return node
        if not self._different:
            for node in self._nodes:
                if stationEqual(node["daozhan"], fazhan) and stationEqual(node["fazhan"], daozhan):
                    return node
        return None

    def different(self):
        return self._different

    def setDifferent(self,different,del_up=False):
        self._different = different
        if not del_up or different is True:
            return

        to_del = []
        for node in self._nodes:
            if not self._line.isDownGap(node["fazhan"],node["daozhan"]):
                to_del.append(node)
        for node in to_del:
            self._nodes.remove(node)

    def setLine(self,line):
        self._line = line

    def line(self):
        return self._line

    def setShow(self,show,down):
        if down:
            self._downShow=show
        else:
            self._upShow=show

    def nodes(self,down:bool):
        if down:
            for node in self._nodes:
                if self._line.isDownGap(node["fazhan"],node["daozhan"]):
                    yield node
        else:
            for node in self._nodes:
                if not self._line.isDownGap(node["fazhan"],node["daozhan"]):
                    yield node

    def items(self,down:bool):
        if down:
            for item in self._downItems:
                yield item
        else:
            for item in self._upItems:
                yield item

    def addItem(self,down,item):
        if down:
            self._downItems.append(item)
        else:
            self._upItems.append(item)

    def downShow(self):
        if self._downShow:
            return True
        return False

    def upShow(self):
        if self._upShow:
            return True
        return False

    def clearItemList(self,down):
        if down:
            self._downItems = []
        else:
            self._upItems = []

    def changeStationName(self,old:str,new:str):
        """
        2019.07.03新增，修改站名。站名要严格匹配。
        """
        for node in self._nodes:
            if node['fazhan'] == old:
                node['fazhan']=new
            if node['daozhan'] == old:
                node['daozhan'] = new

    def onStationDirectionSplited(self,old_name:str,down_name:str,up_name:str):
        """
        2019.11.28新增。
        在将一个站拆成上下行两个站且没有动Line数据时调用。
        """
        if not self.different():
            self.setDifferent(True)
        for node in self._nodes:
            if stationEqual(node['fazhan'],old_name,strict=True):
                if self._line.isDownGap(node['fazhan'],node['daozhan']):
                    node['fazhan'] = down_name
                else:
                    node['fazhan'] = up_name
            elif stationEqual(node['daozhan'],old_name,strict=True):
                if self._line.isDownGap(node['fazhan'],node['daozhan']):
                    node['daozhan'] = down_name
                else:
                    node['daozhan'] = up_name


class ServiceForbid(Forbid):
    def __init__(self,line,different=True):
        super(ServiceForbid, self).__init__(line,different)


class ConstructionForbid(Forbid):
    def __init__(self,line,different=True):
        super(ConstructionForbid, self).__init__(line,different)

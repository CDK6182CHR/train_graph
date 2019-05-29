"""
2.1.2添加 circuit 交路数据结构
todo 任何train修改要映射到circuit修改
"""
from .train import Train
from .line import Line
from .pyETRCExceptions import *

class CircuitNode:
    """
    str _checi;
    str start,end; // 本区间的始发终到站。主要用于机车交路，暂不启用。
    Train& _train=None; // Train对象的引用。初始为空，第一次引用后存储。不写入json对象。
    bool! link=None; // 是否和【前一个】车次之间建立连接线。对第一个是None或任意值。
    Train train();
    void setCheci(str checi);
    void setTrain(Train train);
    dict outInfo();
    Graph& graph;
    """
    def __init__(self,graph,*,origin=None,checi=None,train=None,start=None,end=None,link=None):
        self._checi = checi
        self._train = train
        self.start=start
        self.end=end
        self.link=link
        self.graph=graph
        if origin is not None:
            self.parseInfo(origin)

    def parseInfo(self,origin:dict):
        self._checi = origin['checi']
        self.link = origin['link']
        self.start = origin['start']
        self.end = origin['end']

    def outInfo(self)->dict:
        return {
            "checi":self._checi,
            "start":self.start,
            "end":self.end,
            "link":self.link,
        }

    def train(self)->Train:
        """
        保证checi是有效的。否则直接raise.
        """
        if self._train is not None:
            return self._train
        self._train = self.graph.trainFromCheci(self._checi)
        if self._train is None:
            raise TrainNotFoundException(self._checi)
        return self._train

    def checi(self)->str:
        """
        若有train对象，则以train对象为准。
        """
        if self._train is not None:
            self._checi = self._train.fullCheci()
        return self._checi

    def setCheci(self,checi:str):
        self._checi=checi

    def setTrain(self,train:Train):
        self._train = train
        self._checi = train.fullCheci()

class Circuit:
    """
    str _name;//交路名称，保证不重复
    list<CircuitNode> _order;//套用顺序
    static const int CARRIAGE=0x0,MOTER=0x1; // 机车交路和车底交路的枚举常量。目前只支持车底交路。
    int _type; // CARRIAGE or MOTER
    str _note; //交路说明，任意字符串
    Graph& graph;
    """
    CARRIAGE = 0x0
    MOTER = 0x1
    def __init__(self,graph,name=None,origin=None):
        self.graph=graph
        self._name = name
        self._order = []
        self._type = self.CARRIAGE
        self._note = ""
        if origin is not None:
            self.parseInfo(origin)

    def parseInfo(self,origin:list):
        for n in origin:
            self._order.append(CircuitNode(self.graph,origin=n))

    def outInfo(self)->list:
        lst = []
        for node in self._order:
            lst.append(node.outInfo())
        return lst

    def name(self)->str:
        return self._name

    def setName(self,name:str):
        self._name = name

    def type(self)->int:
        return self._type

    def setType(self,type_:int):
        self._type = type_

    def note(self)->str:
        return self._note

    def setNote(self,note:str):
        self._note = note


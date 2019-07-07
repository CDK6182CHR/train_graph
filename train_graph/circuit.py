"""
2.1.2添加 circuit 交路数据结构
交路部分数据域注意事项
1. 在graph中新增列表_circuits。每个Circuit对象有不同的名字，可以根据名称查找到。在graph中新增函数circuitByName，暂定线性查找，有必要时可以更新为查找表。ok
2. 在Train中新增“_carriageCircuitName”和"_carriageCircuit"两项属性。后者初始为None。在Train中新增方法carriageCircuit，返回Circuit对象。_carriageCircuitName属性需要向json读写。新增setCarriageCircuit方法。这一对方法只负责管理Train中的引用。ok
3. 注意删除车次时的处理。ok
2019.06.03备忘：
注意导入车次、线路拼接时交路的处理。（跨graph对象引起的Train->Graph牵连问题）
2019.06.26备注，关于交路连线：
1. 交路连线等价于计算车站股道占用时判定连线。
2. 在两车次之间连线，当且仅当：
（1）用户勾选了连线；
（2）前一车次终到站、后一车次始发站为本线同一车站。
3. 连线图元由后车的TrainItem负责管理。连线格式为细实线，颜色、粗细皆同后车的起始标签。每个Item允许管理最多两个连线对象，用于处理跨日连线。加粗时应予以加粗。允许单独开关连线。
4. //连线图元所处的高度由UIConfigData给出。默认为10. 字段：link_line_height. 使用虚线。
连线暂定直接走站线上通过。
"""
from .line import Line
from .pyETRCExceptions import *
from Timetable_new.utility import stationEqual

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
    def __init__(self,graph,*,origin=None,checi=None,train=None,start=None,end=None,link=True):
        self._checi = checi
        self._train = train
        self._start=start
        self._end=end
        self.link=link
        self.graph=graph
        if origin is not None:
            self.parseInfo(origin)
        if train is not None and self._checi is None:
            self._checi = train.fullCheci()

    def parseInfo(self,origin:dict):
        self._checi = origin['checi']
        self.link = origin['link']
        self._start = origin['start']
        self._end = origin['end']

    def outInfo(self)->dict:
        return {
            "checi":self._checi,
            "start":self._start,
            "end":self._end,
            "link":self.link,
        }

    def train(self):
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

    def setTrain(self,train):
        self._train = train
        self._checi = train.fullCheci()

    def startStation(self)->str:
        if self.train() is not None:
            return self.train().localFirst(self.graph)
        else:
            return None

    def endStation(self)->str:
        if self.train() is not None:
            return self.train().localLast(self.graph)
        else:
            return None

class Circuit:
    """
    str _name;//交路名称，保证不重复
    list<CircuitNode> _order;//套用顺序
    static const int CARRIAGE=0x0,MOTER=0x1; // 机车交路和车底交路的枚举常量。目前只支持车底交路。
    int _type; // CARRIAGE or MOTER
    str _note; //交路说明，任意字符串
    str _model; //车底，任何字符串
    str _owner; // 担当局
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
        self._model = ""
        self._owner = ""
        if origin is not None:
            self.parseInfo(origin)

    def parseInfo(self,origin:dict):
        self._name = origin.get('name','')
        self._note = origin.get('note','')
        self._model = origin.get('model','')
        self._owner = origin.get('owner','')
        for n in origin.get('order',[]):
            self._order.append(CircuitNode(self.graph,origin=n))

    def outInfo(self)->list:
        dct = {
            "name":self._name,
            "note":self._note,
            "model":self._model,
            "owner":self._owner,
        }
        lst = []
        for node in self._order:
            lst.append(node.outInfo())
        dct['order'] = lst
        return dct

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

    def model(self)->str:
        return self._model

    def setModel(self,m:str):
        self._model = m

    def owner(self)->str:
        return self._owner

    def setOwner(self,o:str):
        self._owner = o

    def removeTrain(self,train):
        for node in self._order:
            if node.train() is train:
                self._order.remove(node)
                train.setCarriageCircuit(None)
                return

    def addTrain(self,train,index=None):
        """
        要求train不能属于其他交路。否则抛出TrainHasCircuitError。
        """
        if train.carriageCircuit() is not None:
            raise TrainHasCircuitError(train,train.carriageCircuit())
        if index is None:
            self._order.append(CircuitNode(self.graph,train=train))
        else:
            self._order.insert(index,CircuitNode(self.graph,train=train))
        train.setCarriageCircuit(self)

    def __str__(self):
        return f"Circuit<{self.name()}>"

    def orderStr(self)->str:
        try:
            return '-'.join(map(lambda x:x.train().fullCheci(),self._order))
        except TrainNotFoundException as e:
            print("Circuit::orderStr",e)
            return 'NA'


    def trainCount(self)->int:
        return len(self._order)

    def nodes(self):
        for node in self._order:
            yield node

    def clear(self):
        self._order.clear()

    def addNode(self,node:CircuitNode):
        self._order.append(node)

    def preorderLinked(self,train)->tuple:
        """
        [Train,datetime] or [None,None]
        返回有Link的前一个车次及其终到时间。如果本车次没有Link，则返回None。
        返回的充要条件是符合连线条件。
        关于本交路长度的线性算法。
        """
        preNode = None
        preTrain = None
        for node in self.nodes():
            if node.train() is train:
                if preNode is None:
                    return None,None
                elif not node.link:
                    return None,None
                else:
                    preTrain = preNode.train()
                    break
            preNode = node
        if preTrain is None:
            return None,None
        preEnd = preTrain.destination()
        thisStart = train.departure()

        if preEnd is None or thisStart is None:
            return None,None
        if stationEqual(preEnd['zhanming'],thisStart['zhanming']) and \
            self.graph.stationInLine(preEnd['zhanming']):
            return preTrain,preEnd['ddsj']
        return None,None

    def postorderLinked(self,train)->tuple:
        """
        [Train,datetime] or [None,None]
        返回后续连接的车次。如果没有后续或者后续没有勾选link，返回None.
        """
        found = False
        postTrain = None
        for node in self.nodes():
            if node.train() is train:
                found=True
                continue
            if found:
                if not node.link:
                    return None,None
                else:
                    postTrain = node.train()
                    break
        if postTrain is None:
            return None,None
        thisEnd = train.destination()
        postStart = postTrain.departure()
        if thisEnd is None or postStart is None:
            return None,None
        if stationEqual(thisEnd['zhanming'],postStart['zhanming']) and \
            self.graph.stationInLine(thisEnd['zhanming']):
            return postTrain,postStart['cfsj']
        return None,None


    def trainOrderNum(self,train)->int:
        """
        车次在交路中的位置序号，从0起始。如果不存在，抛出TrainNotInCircuitError。
        """
        for i,node in enumerate(self._order):
            if node.train() is train:
                return i
        raise TrainNotInCircuitError(train,self)

    def replaceTrain(self,old,new):
        """
        导入车次时覆盖。将车次用新车次对象替换。
        """
        for node in self.nodes():
            if node.train() is old:
                node.setTrain(new)
                return

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
# from .line import Line
from ..pyETRCExceptions import *
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
    def __init__(self,graph,*,origin=None,checi=None,train=None,start=None,end=None,link=True,virtual=False):
        self._checi = checi
        self._train = train
        self._start=start
        self._end=end
        self._virtual = virtual
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
        self._virtual = origin.get('virtual',False)

    def outInfo(self)->dict:
        return {
            "checi":self.checi(),
            "start":self._start,
            "end":self._end,
            "link":self.link,
            "virtual":self._virtual,
        }

    def train(self):
        """
        保证checi是有效的。否则直接raise.
        如果是virtual，直接返回None
        """
        if self._virtual:
            return None
        if self._train is not None:
            return self._train
        self._train = self.graph.trainFromCheci(self._checi)
        if self._train is None:
            raise TrainNotFoundException(self._checi)
        return self._train

    def trainFromCheci(self):
        """
        导入车次时调用。仅按照车次，在运行图中查找Train对象。如果找不到，返回None。
        """
        if self._virtual:
            return None
        return self.graph.trainFromCheci(self._checi,full_only=True)

    def checi(self)->str:
        """
        若有train对象，则以train对象为准。
        """
        if self._virtual:
            return self._checi
        if self._train is not None:
            self._checi = self._train.fullCheci()
        return self._checi

    def checiWithMark(self)->str:
        """
        2019.11.28新增：在虚拟车次后添加“(虚拟)备注”
        """
        if self._virtual:
            return self.checi()+"(虚拟)"
        else:
            return self.checi()

    def setCheci(self,checi:str):
        self._checi=checi

    def setTrain(self,train):
        self._train = train
        if train is not None:
            self._checi = train.fullCheci()

    def startStation(self)->str:
        if self.train() is not None:
            return self.train().localFirst(self.graph)
        else:
            return self._start

    def endStation(self)->str:
        if self.train() is not None:
            return self.train().localLast(self.graph)
        else:
            return self._end

    def setGraph(self,graph):
        """
        将Circuit对象移交给另一个运行图。清除Train对象。
        """
        self.graph=graph
        self._train=None

    def isVirtual(self)->bool:
        return self._virtual

    def setVirtual(self,v:bool):
        self._virtual = v


class Circuit:
    """
    str _name;//交路名称，保证不重复
    list<CircuitNode> _order;//套用顺序
    static const int CARRIAGE=0x0,MOTER=0x1; // 机车交路和车底交路的枚举常量。目前只支持车底交路。
    bool _virtual; //是否是虚拟车次。虚拟车次指在本线没有对应Train实体。
    int _type; // CARRIAGE or MOTER
    str _note; //交路说明，任意字符串
    str _model; //车底，任何字符串
    str _owner; // 担当局
    Graph& graph;
    """
    CARRIAGE = 0x0
    MOTER = 0x1
    Spliters = ('-','~','—','～')
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
        self.checkRealTrains()

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

    def removeTrainByCheci(self,train):
        for node in self._order:
            if node._checi == train.fullCheci():
                self._order.remove(node)
                train.setCarriageCircuit(None)
                return

    def changeTrainToVirtual(self,train):
        """
        当删除车次时，将该车次结点设为虚拟车次。
        """
        for node in self._order:
            if node.train() is train:
                node.setTrain(None)
                node.setVirtual(True)
                train.setCarriageCircuit(None)
                return

    def addTrain(self,train,index=None):
        """
        要求train不能属于其他交路。否则抛出TrainHasCircuitError。
        完成一切操作。
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
        """
        2019.11.28兼容虚拟车次：使用node.checi()方法。
        """
        # try:
        #     return '-'.join(map(lambda x:x.train().fullCheci(),self._order))
        # except TrainNotFoundException as e:
        #     print("Circuit::orderStr",e)
        #     return 'NA'
        return '-'.join(map(lambda x:x.checiWithMark(),self._order))

    def checiList(self):
        """
        依次产生车次，且只运用_checi属性，不考虑Train属性。
        """
        for node in self.nodes():
            yield node._checi

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

    def anyValidTrains(self)->bool:
        """
        只要有一个节点能找到Train对象，就返回True。否则返回False。
        """
        for node in self.nodes():
            try:
                node.train()
            except TrainNotFoundException:
                pass
            else:
                return True
        return False

    def setGraph(self,graph):
        self.graph=graph
        for node in self.nodes():
            node.setGraph(graph)

    def coverBaseData(self,circuit):
        """
        复制不包括nodes在内的基数据。
        """
        self._name = circuit.name()
        self._type = circuit._type
        self._note = circuit._note
        self._model = circuit._model
        self._owner = circuit._owner

    def parseText(self,text:str,spliter:str,full_only:bool=False)->list:
        """
        解析车次序列字符串。如果不提供分隔符，则按系统自带来找。
        样例：G2189/92—C6263—乐山过夜—C6256—G2191/0—上海虹桥动车所检修—G2189/92
        如果分隔出来的有“过夜”“检修”这样的字，则删除。
        :returns 报告信息的列表。
        """
        reports = [f'[info]在交路{self.name()}中解析车次信息字符串']
        if not spliter:
            for sp in Circuit.Spliters:
                if sp in text:
                    spliter=sp
                    break
        if not spliter:
            return ['[error]解析失败：没有找到合适的分隔符']
        checis = text.split(spliter)
        for checi in checis:
            checi = checi.strip()
            if '检修' in checi or '过夜' in checi:
                reports.append(f'[warning]不符合车次格式，不添加：{checi}')
                continue
            train = self.graph.trainFromCheci(checi,full_only=full_only)
            if checi in list(self.checiList()):
                reports.append(f"[warning]本交路中已经存在的车次，不添加：{checi}")
                continue
            virtual = False
            if train is None:
                reports.append(f"[warning]车次{checi}不存在，设为虚拟车次")
                virtual=True
            else:
                cir = train.carriageCircuit()
                if cir is not None:
                    reports.append(f'[warning]车次{checi}存在，但已经添加到交路{cir.name()}，设为虚拟车次')
                    virtual=True
                else:  # 添加实体车次
                    reports.append(f'[info]添加实体车次{train}')
                    virtual = False
            if virtual:
                node = CircuitNode(self.graph,checi=checi,start='',end='',virtual=True)
                self.addNode(node)
            else:
                # node = CircuitNode(self.graph,checi=train.fullCheci(),train=train,start=train.localFirst(),
                #                    end=train.localLast(),link=True,virtual=False)
                self.addTrain(train)
                train.setCarriageCircuit(self)
        return reports

    def identifyTrain(self,full_only=False)->list:
        """
        尝试从虚拟车次中识别存在的车次，变成实体车次。
        2020.02.02新增：如果车次错误设置为实体，变为虚拟。
        :returns 解析报告
        """
        reports = [f'在{self}中进行车次识别']
        for node in self._order:
            if node.isVirtual():
                checi = node.checi()
                train = self.graph.trainFromCheci(checi,full_only=full_only)
                if train is None:
                    reports.append(f"[warning]车次不存在: {checi}")
                else:
                    cir = train.carriageCircuit()
                    if cir is not None:
                        reports.append(f"[warning]车次{train}已经属于交路: {cir}")
                    else:
                        reports.append(f'[info]将车次{train}识别为实体车次')
                        node.setVirtual(False)
                        node.setTrain(train)
                        train.setCarriageCircuit(self)
            else:  # 非虚拟车次
                checi = node.checi()
                train = self.graph.trainFromCheci(checi, full_only=full_only)
                if train is None:
                    node.setVirtual(True)
                    reports.append(f'[info]将车次{checi}判定为虚拟车次')
        return reports

    def checkRealTrains(self):
        """
        检查所有非虚拟车次，将不存在的设置成虚拟。
        """
        for node in self.nodes():
            try:
                node.train()
            except TrainNotFoundException:
                node.setVirtual(True)

    def firstCheci(self)->str:
        if self._order:
            return self._order[0].checi()
        return ''

    def realCount(self)->int:
        return len(list(filter(lambda x:not x.isVirtual(),self._order)))

    def virtualCount(self)->int:
        return len(list(filter(lambda x: x.isVirtual(), self._order)))

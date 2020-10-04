"""
2.1.2添加
异常处理类在的集合。
usage:
>>> from .pyETRCExceptions import *
>>> raise TrainNotFoundException("K101")
"""
from pprint import pprint as printf

class TrainNotFoundException(Exception):
    """
    搜索某个车次时，找不到对应车次。
    """
    def __init__(self,checi:str):
        self.checi=checi

    def __str__(self):
        return f"无此车次：{self.checi}"

class RulerNotCompleteError(Exception):
    def __init__(self,start,end):
        self.start=start
        self.end=end

    def __str__(self):
        return f"区间{self.start}-{self.end}没有标尺数据，无法按标尺排图"

class CircuitNotFoundError(Exception):
    def __init__(self,name, checi=None):
        self.name = name
        self.checi = checi

    def __str__(self):
        return f"根据名称找不到交路：{self.name}, 由车次{self.checi}调起"

class CircuitExistedError(Exception):
    def __init__(self,name):
        self.name = name

    def __str__(self):
        return f"交路名称已存在：{self.name}"


class TrainHasCircuitError(Exception):
    def __init__(self,train,circuit):
        self.train=train
        self.circuit=circuit

    def __str__(self):
        return f"列车{self.train}已有交路信息{self.circuit}"

class TrainNotInCircuitError(Exception):
    def __init__(self,train,circuit):
        self.train=train
        self.circuit = circuit

    def __str__(self):
        return f"列车{self.train}不在交路{self.circuit}中！"

class StartOrEndNotMatchedError(Exception):
    def __init__(self,startOrEnd,firstOrLast,train):
        self.startOrEnd = startOrEnd
        self.firstOrLast = firstOrLast
        self.train = train

    def __str__(self):
        return f"列车{self.train}的始发或终到站{self.startOrEnd}与时刻表首末站{self.firstOrLast}不匹配！"

class VirtualTrainError(Exception):
    def __init__(self,checi):
        self.checi = checi
    def __str__(self):
        return f"{self.checi}是虚拟车次! "

class StationNotInLineException(Exception):
    def __init__(self,st):
        self.st = st

    def __str__(self):
        return f"车站{self.st}不属于本线！"
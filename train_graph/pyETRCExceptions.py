"""
2.1.2添加
异常处理类在的集合。
usage:
>>> from .pyETRCExceptions import *
>>> raise TrainNotFoundException("K101")
"""

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


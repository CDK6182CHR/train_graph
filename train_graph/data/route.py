"""
2019.08.02新增，列车径路。作为Line的属性。
初步设计只考虑一次性判断，不保存状态；并且只考虑一个车次在本线单方向运行一个区间。
数据结构设计：
    str entranceStation;
    str exitStation;
    List<str> startStations;//不支持域解析符。为空表示任意。
    List<str> endStations;
    bool unidirectional;//单方向。只支持entrance->exit方向，不允许反向。默认为False
"""

from .train import Train
# from .line import Line

class Route:
    def __init__(self,line,name:str=''):
        self.line = line  # type:Line
        self.name = name
        self.unidirectional = False  # 仅单向
        self.entranceStation = line.firstStationName()
        self.exitStation = line.lastStationName()
        self.startStations = []
        self.endStations = []

    def parseData(self,origin:dict):
        self.name = origin["name"]
        self.unidirectional = origin["unidirectional"]
        self.entranceStation = origin['entranceStation']
        self.exitStation = origin['exitStation']
        self.startStations = origin['startStations']
        self.endStations = origin['endStations']

    def outInfo(self)->dict:
        return {
            "name":self.name,
            "entranceStation":self.entranceStation,
            "exitStation":self.exitStation,
            "startStations":self.startStations,
            "endStations":self.endStations,
            "unidirectional":self.unidirectional,
        }

    def intervalCheck(self,train:Train)->bool:
        """
        检查车次在本线运行的区间是否包含于本路径给出的区间。
        """
        self.line.enableNumberMap()
        trainInterval = list(map(self.line.stationIndex,(train.localFirst(),train.localLast())))
        routeInterval = list(map(self.line.stationIndex,(self.entranceStation,self.exitStation)))
        if min(routeInterval)<=min(trainInterval) and max(routeInterval)>=max(trainInterval):
            return True
        return False

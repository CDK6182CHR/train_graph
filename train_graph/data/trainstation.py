"""
2019.11.15新增，
车次数据中的车站信息类，继承dict，按需添加功能。
"""
from datetime import datetime


class TrainStation(dict):
    def __init__(self,an=None):
        if an is None:
            super(TrainStation, self).__init__()
        else:
            super(TrainStation, self).__init__(an)

    def __str__(self):
        try:
            return f"{self['zhanming']} {self['ddsj'].strftime('%H:%M:%S')} {self['cfsj'].strftime('%H:%M:%S')}"
        except KeyError:
            return "Not Complete TrainStation"

    def __repr__(self):
        return str(self)

import train_graph.data as ped
from datetime import datetime, timedelta


def adjust_station_depart_time(train:ped.Train, station_name:str, secs:int):
    """
    将列车时刻表中指定车站的出发时刻前移或者后移一段时间，而到达时刻不变。
    如果时刻表中出现多个同名站，只处理第一个。
    see also: Train.setStationDeltaTime
    :param train 列车对象
    :param station_name 站名，要求用严格匹配的站名
    :param secs 调整时长，以**秒**为单位。正值表示推后，负值表示提前。
    """

    # 这是个简单的线性搜索算法，详见源码
    st = train.stationDict(station_name, strict=True)

    if st is None:
        # 没有找到该站
        pass
    else:
        dt = timedelta(days=0, seconds=secs)
        # 对出发时间做调整。
        # 如果是到达时间，key为ddsj  (拼音首字母)
        st['cfsj'] += dt

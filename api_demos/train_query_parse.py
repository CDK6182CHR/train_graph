"""
2022.01.19
train query结果解析  保存到pyETRC文件
"""

import json
from train_graph import data as ped

graph = ped.Graph()


def train_query_parse(text:str)->ped.Train:
    """
    解析单个车次，返回pyETRC的Train对象。
    注意所给数据没有车次信息，这里不负责设置车次名称。
    :param text: JSON文件的内容。
    :returns: 当前车次的pyETRC对象。
    """
    d = json.loads(text)['data']['data']
    train = ped.Train(graph)
    for dct in d:
        train.addStation(dct['station_name'],dct['arrive_time'],dct['start_time'],
            business=True)
        if sfz:=dct.get('start_station_name'):
            train.sfz=sfz
        if zdz:=dct.get('end_station_name'):
            train.zdz=zdz
    return train


if __name__ == '__main__':
    with open('data/queryByTrainNo.json', encoding='utf-8', errors='ignore') as fp:
        text = fp.read()
    train = train_query_parse(text)
    train.setFullCheci('D1911')
    graph.addTrain(train)

    graph.save('data/query_parse.pyetdb')

    # for multi JSONs, do as follows:
    # for txt in ...:
    #     train = train_query_parse(txt)
    #     train.setFullCheci('...')
    #     graph.addTrain(train)
    # graph.save('....')



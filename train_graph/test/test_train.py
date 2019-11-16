"""
2019.11.15：
测试Train的相似度计算动态规划算法。
"""
from ..data import *
from pprint import pprint as printf

graph1 = Graph()
graph1.loadGraph('source/西成客专线广成段20190410.json')
train1 = graph1.trainFromCheci('D1911',True)  # 410图的D1911

graph2 = Graph()
graph2.loadGraph('source/西成客专线广成段20190105.json')
train2 = graph2.trainFromCheci('D1911',True)

re1,value1 = train1.globalDiff(train2)
printf(re1)
print(value1)

# 测试两个完全无关的车次
print("totally different train test")
train3 = graph1.trainFromCheci('D1913',True)
re2,value2 = train1.globalDiff(train3)
printf(re2)
print(value2)

# 测试两个不同运行图上的车次
print("trains from different graphs")
graph3 = Graph()
graph3.loadGraph('source/京沪线上局段20190410.json')
train4 = graph3.trainFromCheci('D707',True)

re3,value3 = train1.globalDiff(train4)
printf(re3)
print(value3)

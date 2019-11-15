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

re,value = train1.globalDiff(train2)
printf(re)
print(value)
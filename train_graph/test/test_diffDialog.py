from ..trainDiffDialog import *
from PyQt5 import QtWidgets,QtGui,QtCore

app = QtWidgets.QApplication([])

graph1 = Graph()
graph1.loadGraph('source/西成客专线广成段20190410.json')
train1 = graph1.trainFromCheci('D1911',True)  # 410图的D1911

graph2 = Graph()
graph2.loadGraph('source/西成客专线广成段20190105.json')
train2 = graph2.trainFromCheci('D1911',True)

re1,value1 = train2.globalDiff(train1)

dialog = TrainDiffDialog(train2,train1,graph2,re1)
dialog.exec()
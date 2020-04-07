"""
Excel风格展示本线的所有标尺。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .data import *

TWI = QtWidgets.QTableWidgetItem


class CTWI(QtWidgets.QTableWidgetItem):
    def __init__(self, *args):
        super(CTWI, self).__init__(*args)
        self.setTextAlignment(Qt.AlignCenter)


class RulerTable(QtWidgets.QTableWidget):
    def __init__(self, graph:Graph, parent=None):
        super(RulerTable, self).__init__(parent)
        self.graph = graph
        self.setWindowTitle('标尺一览表')
        # self.setAlternatingRowColors(True)
        self.resize(1200,800)
        self.initUI()
        self.setData()

    def initUI(self):
        """
        确定表格参数。直接确定标尺数量。
        """
        self.setEditTriggers(self.NoEditTriggers)
        n = self.graph.rulerCount()  # 标尺数量
        rulers = list(self.graph.rulers())
        # self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setColumnCount(n*6+3)
        m = n*3+1  # 中央列，即站名列的编号
        self.setRowCount(self.graph.stationCount()*2+1)

        headers = ['里程','站名','里程']
        s = ['区间','起停','均速']
        headers = s*n+headers+s*n
        self.setHorizontalHeaderLabels(headers)

        # 处理表头
        self.setItem(0,m,CTWI('站名'))
        self.setItem(0,m-1,CTWI('区间距离'))
        self.setSpan(0,m-1,2,1)
        self.setItem(0,m+1,CTWI('区间距离'))
        self.setSpan(0,m+1,2,1)

        # 合并方向表头
        if n:
            self.setSpan(0,m+2,1,n*3)
            self.setItem(0,m+2,CTWI('下行'))
            self.setSpan(0,0,1,n*3)
            self.setItem(0,0,CTWI('上行'))

        # 每个标尺，合并表头
        for t in range(n):
            i=t+1
            self.setSpan(1,m+i*3-1,1,3)
            self.setItem(1,m+i*3-1,CTWI(rulers[t].name()))
            self.setSpan(1,m-i*3-1,1,3)
            self.setItem(1,m-i*3-1,CTWI(rulers[t].name()))
            for col in ((m+i*3, m-i*3)):
                self.setColumnWidth(col,60)
            for col in ((m+i*3-1,m+i*3+1,m-i*3-1,m-i*3+1)):
                self.setColumnWidth(col,80)

        # 每个站. 同时算出所有区间，并把区间数据放到里程那一列的data里面
        last_down, last_up = None,None
        last_down_i, last_up_i = 0,0
        for i,st_dict in enumerate(self.graph.stationDicts()):
            zm = st_dict['zhanming']
            self.setSpan(i*2+1,m,2,1)
            item = CTWI(zm)
            item.setBackground(QtGui.QBrush(QtGui.QColor('#f5f5f5')))
            self.setItem(i*2+1,m,item)
            if last_down is None:
                # 第一个站，一定双向通过
                last_down = last_up = st_dict
                continue

            if st_dict['direction'] & Line.DownVia:
                # 下行通过站
                zm0 = last_down['zhanming']
                c = i-last_down_i
                self.setSpan(last_down_i*2+2,m+1,c*2,1)
                mile = self.graph.gapBetween(last_down['zhanming'],st_dict['zhanming'])
                item = CTWI(f'{mile:.3f}')
                item.setData(Qt.UserRole,(last_down_i,i,last_down,st_dict))
                self.setItem(last_down_i*2+2,m+1,item)

                r1 = last_down_i*2+2  # 区间数据第一行的写入地方
                r2 = r1+c

                for j,ruler in enumerate(rulers):
                    col = m+2+j*3  # 标尺第一列所对应的全局列号
                    self.setSpan(last_down_i * 2 + 2, col, 2*c, 1)
                    self.setSpan(last_down_i * 2 + 2, col + 2, 2*c, 1)
                    if c > 1:
                        self.setSpan(last_down_i * 2 + 2, col+1, c, 1)
                        self.setSpan(last_down_i * 2 + 2 + c, col+1, c, 1)

                    node = ruler.getInfo(zm0,zm)
                    if node is None:
                        continue
                    self.setItem(r1,col,CTWI(Train.sec2strmin(node['interval'])))
                    item = CTWI(Line.speedStr(mile,node['interval']))
                    self.setItem(r1,col+2,item)
                    self.setItem(r1,col+1,CTWI(Train.sec2strmin(node['start'])))
                    self.setItem(r2,col+1,CTWI(Train.sec2strmin(node['stop'])))

            if st_dict['direction'] & Line.UpVia:
                c = i - last_up_i
                zm0 = last_up['zhanming']
                self.setSpan(last_up_i * 2 + 2, m - 1, c * 2, 1)
                mile = self.graph.gapBetween(st_dict['zhanming'],last_up['zhanming'])
                item = CTWI(f'{mile:.3f}')
                item.setData(Qt.UserRole, (i,last_up_i,st_dict, last_up))
                self.setItem(last_up_i * 2 + 2, m - 1, item)

                r1 = last_up_i * 2 + 2  # 区间数据第一行的写入地方
                r2 = r1 + c
                for j,ruler in enumerate(rulers):
                    col = m-4-j*3  # 标尺第一列所对应的全局列号
                    self.setSpan(last_up_i * 2 + 2, col, c*2, 1)
                    self.setSpan(last_up_i * 2 + 2, col + 2, c*2, 1)
                    if c > 1:
                        self.setSpan(last_up_i * 2 + 2, col+1, c, 1)
                        self.setSpan(last_up_i * 2 + 2 + c, col+1, c, 1)

                    node = ruler.getInfo(zm,zm0)
                    if node is None:
                        continue
                    self.setItem(r1,col,CTWI(Train.sec2strmin(node['interval'])))
                    item = CTWI(Line.speedStr(mile, node['interval']))
                    self.setItem(r1, col+2, item)
                    self.setItem(r1,col+1,CTWI(Train.sec2strmin(node['stop'])))
                    self.setItem(r2,col+1,CTWI(Train.sec2strmin(node['start'])))

            if st_dict['direction'] & Line.DownVia:
                last_down = st_dict
                last_down_i = i
            if st_dict['direction'] & Line.UpVia:
                last_up = st_dict
                last_up_i = i


    def setData(self):
        pass

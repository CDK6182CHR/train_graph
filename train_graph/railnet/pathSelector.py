"""
2021.01.14
交互式经由选择界面。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from ..data import *
from ..linedb.lineLib import LineLib
from .railnet import RailNet

__all__ = ['PathSelector']

# alias:
TW = QtWidgets.QTableWidget
TWI = QtWidgets.QTableWidgetItem

class PathSelector(QtWidgets.QWidget):
    lineGenerated = QtCore.pyqtSignal(Line,list)
    def __init__(self,graphdb:Graph,lineLib:LineLib,net:RailNet,parent=None):
        super(PathSelector, self).__init__(parent)
        self.graphdb = graphdb
        self.lineLib = lineLib
        self.net = net
        self.currentLine = None
        self.initUI()

    def initUI(self):
        hlayout = QtWidgets.QHBoxLayout()

        # 第一列：已选节点
        vlayout = QtWidgets.QVBoxLayout()

        # 关于是否导出标尺的选项
        chlayout = QtWidgets.QHBoxLayout()
        chk = QtWidgets.QCheckBox()
        self.checkWithRuler = chk
        chk.setChecked(False)
        chlayout.addWidget(chk)
        label = QtWidgets.QLabel('同时导出区间数不少于')
        chlayout.addWidget(label)
        sp = QtWidgets.QSpinBox()
        chk.toggled.connect(sp.setEnabled)
        sp.setRange(0, 1000)
        sp.setValue(10)
        self.spinRulerCount = sp
        sp.setEnabled(False)
        chlayout.addWidget(sp)

        label = QtWidgets.QLabel('的标尺')
        chlayout.addWidget(label)

        vlayout.addLayout(chlayout)

        chlayout = QtWidgets.QHBoxLayout()
        nameEdit = QtWidgets.QLineEdit()
        self.nameEdit = nameEdit
        chlayout.addWidget(nameEdit)
        btn = QtWidgets.QPushButton('添加首站')
        btn.clicked.connect(self._add_station_fast)
        chlayout.addWidget(btn)
        vlayout.addLayout(chlayout)
        vlayout.addWidget(QtWidgets.QLabel('已选节点表：'))
        self.btnAdd = btn

        tw = TW()
        self.tableSelected = tw
        tw.setSelectionBehavior(TW.SelectRows)
        tw.setColumnCount(5)
        tw.setHorizontalHeaderLabels(['站名','里程','对里程','选择方式','线名'])
        tw.setEditTriggers(TW.NoEditTriggers)
        for i,s in enumerate((100,80,80,80,160)):
            tw.setColumnWidth(i,s)
        vlayout.addWidget(tw)

        chlayout = QtWidgets.QHBoxLayout()
        btn = QtWidgets.QPushButton('删除')
        chlayout.addWidget(btn)
        btn.clicked.connect(self._del_select)
        btn = QtWidgets.QPushButton('预览')
        chlayout.addWidget(btn)
        btn.clicked.connect(self._generate_line)
        vlayout.addLayout(chlayout)

        hlayout.addLayout(vlayout)

        # 第二列：当前车站邻接表
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()
        editStationName = QtWidgets.QLineEdit()
        editStationName.setFocusPolicy(Qt.NoFocus)
        self.editStationName = editStationName
        flayout.addRow('当前站名',editStationName)
        vlayout.addLayout(flayout)

        vlayout.addWidget(QtWidgets.QLabel('当前车站邻接站表：'))
        tw = TW()
        self.tableAdj = tw
        tw.setColumnCount(7)
        tw.setHorizontalHeaderLabels(['线名','站名','方向','里程','对里程','标尺数','对标尺'])
        tw.setEditTriggers(TW.NoEditTriggers)
        for i,s in enumerate((120,120,60,100,100,60,60)):
            tw.setColumnWidth(i,s)
        tw.currentCellChanged.connect(self._adj_line_changed)
        tw.setSelectionBehavior(TW.SelectRows)
        vlayout.addWidget(tw)

        btn = QtWidgets.QPushButton('添加至节点表')
        vlayout.addWidget(btn)
        btn.clicked.connect(self._adj_add)
        hlayout.addLayout(vlayout)

        # 第三列：同线路站表
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()
        edit = QtWidgets.QLineEdit()
        edit.setFocusPolicy(Qt.NoFocus)
        self.lineNameEdit = edit
        flayout.addRow('当前线名',edit)
        vlayout.addLayout(flayout)

        vlayout.addWidget(QtWidgets.QLabel('当前线路（方向）站表：'))
        tw = TW()
        tw.setEditTriggers(TW.NoEditTriggers)
        tw.setColumnCount(4)
        tw.setHorizontalHeaderLabels(['站名','里程','对里程','单向'])
        for i,s in enumerate((120,120,120,80)):
            tw.setColumnWidth(i,s)
        self.tableLine = tw
        tw.setSelectionBehavior(TW.SelectRows)
        vlayout.addWidget(tw)
        btn = QtWidgets.QPushButton('添加到节点表')
        btn.clicked.connect(self._line_add)
        vlayout.addWidget(btn)

        hlayout.addLayout(vlayout)

        self.setLayout(hlayout)

    def stationCount(self)->int:
        """
        节点表数量。
        :return:
        """
        return self.tableSelected.rowCount()

    def lastSelected(self)->str:
        """
        返回当前最后一个已选站。
        :return:
        """
        if not self.stationCount():
            return None
        else:
            return self.tableSelected.item(self.stationCount()-1,0).text()

    def addSelectStation(self, name, line:Line=None, method='',lineName=''):
        """
        向已选表中添加一行。
        :param name: 站名
        :param mile: 里程
        :param counter: 对里程
        :param method: 添加来源
        :param lineName: 线名
        :return:
        """
        tw = self.tableSelected
        row = tw.rowCount()
        tw.insertRow(row)
        tw.setRowHeight(row,self.graphdb.UIConfigData()['table_row_height'])

        if line is None:
            mile = 0
            counter = 0
        else:
            mile = line.lineLength()
            counter = line.counterLength()
            if row > 0:
                # 找上一行的里程和对里程
                mile += tw.item(row-1,1).data(Qt.UserRole)
                counter += tw.item(row-1,2).data(Qt.UserRole)

        it = TWI(name)
        it.setData(Qt.UserRole, line)
        tw.setItem(row,0,it)

        it = TWI(f'{mile:.3f}')
        it.setData(Qt.UserRole, mile)
        tw.setItem(row,1,it)

        ct_str = 'NA' if counter is None else f'{counter:.3f}'
        it = TWI(ct_str)
        it.setData(Qt.UserRole, counter)
        tw.setItem(row,2,it)

        tw.setItem(row,3,TWI(method))
        tw.setItem(row,4,TWI(lineName))

        self._select_last_changed()

    def updateAdjTable(self):
        """
        0. 设置提示站名
        1. 更新邻接站表。
        2. 清空邻接站表的选择。
        3. 清空当前线路站表。
        """
        tw = self.tableAdj
        if self.stationCount():
            dct = self.net.adjStations(self.lastSelected())
            tw.setRowCount(len(dct))
            self.editStationName.setText(self.lastSelected())
            for row,(nd, ed )in enumerate(dct.items()):
                # 数据存储：线名->正向  站名 -> 反向  里程、对里程->里程数值。
                # ['线名','站名','方向','里程','对里程','标尺数','对标尺数']
                it = TWI(ed.get('name',''))
                it.setData(Qt.UserRole,ed)
                tw.setItem(row,0,it)

                it = TWI(nd)
                edrev = self.net.graph().get_edge_data(nd,self.lastSelected())
                it.setData(Qt.UserRole,edrev)
                tw.setItem(row,1,it)

                it = TWI('下行' if ed['down'] else '上行')
                it.setData(Qt.UserRole,ed['down'])
                tw.setItem(row,2,it)

                it = TWI(f'{ed["length"]:.3f}')
                it.setData(Qt.UserRole,ed['length'])
                tw.setItem(row,3,it)

                counter = edrev["length"] if edrev else None
                it = TWI('' if edrev is None else f'{counter:.3f}')
                it.setData(Qt.UserRole,counter)
                tw.setItem(row,4,it)

                tw.setItem(row,5,TWI(str(len(ed['rulers']))))
                tw.setItem(row,6,TWI('' if edrev is None else str(len(edrev['rulers']))))

        else:
            # 清空邻接表
            tw.setRowCount(0)
            self.editStationName.setText('')
        tw.clearSelection()
        self.clearLineTable()

    def clearLineTable(self):
        self.lineNameEdit.setText('')
        self.tableLine.setRowCount(0)

    def setLineTable(self, adjStation:str, lineName:str, firstAdj:float, down:bool):
        """
        更新当前线路的表。
        """
        line = self.net.getLine(self.lastSelected(),adjStation,lineName,firstAdj,down)
        self.lineNameEdit.setText(lineName)
        # ['站名','里程','对里程','单向']
        tw = self.tableLine
        tw.setRowCount(line.stationCount())

        for row,st in enumerate(line.stationDicts()):
            tw.setRowHeight(row,self.graphdb.UIConfigData()['table_row_height'])
            tw.setItem(row,0,TWI(st['zhanming']))
            tw.setItem(row,1,TWI(f'{st["licheng"]:.3f}'))
            ctr_str = '' if st.get('counter') is None else f'{st["counter"]:.3f}'
            tw.setItem(row,2,TWI(ctr_str))
            tw.setItem(row,3,TWI(Line.DirMap[st['direction']]))
        self.currentLine = line

    # slots
    def _add_station_fast(self):
        """
        快速添加节点。包括添加第一个站和后续用最短路模型添加。
        """
        st = self.nameEdit.text()
        if not self.net.stationExists(st):
            QtWidgets.QMessageBox.warning(self,'错误',f'站名[{st}]不在当前线路数据库中')
            return
        if self.stationCount() == 0:  # 添加第一个站
            self.addSelectStation(st)
        else:
            # 使用最短路算法
            try:
                line = self.net.outLine([self.lastSelected(),st],
                                        withRuler=self.checkWithRuler.isChecked(),
                                        minRulerCount=self.spinRulerCount.value())
                self.addSelectStation(st,line,'最短路径')
            except Exception as e:
                QtWidgets.QMessageBox.warning(self,'错误','找不到最短路：\n'+repr(e))
                return

        self._select_last_changed()

    def _del_select(self):
        tw = self.tableSelected
        row = tw.currentRow()
        if row != tw.rowCount() -1:
            if not self.question('当前所选的非节点表最后一个站。\n'
                                 '如果确定要删除，则当前站及之后所有节点都将被删除，是否继续？'):
                return
        while tw.rowCount() > row:
            tw.removeRow(tw.rowCount()-1)
        self._select_last_changed()

    def _select_last_changed(self):
        # 更新添加按钮
        if self.stationCount():
            self.btnAdd.setText('最短路')
        else:
            self.btnAdd.setText('添加首站')
        self.updateAdjTable()

    def _generate_line(self):
        tw = self.tableSelected
        if tw.rowCount() < 2:
            return
        line = tw.item(1,0).data(Qt.UserRole)
        line = line.slice(0,line.stationCount())  # 复制
        via = [tw.item(0,0).text(),tw.item(1,0).text()]
        for row in range(2,tw.rowCount()):
            line.jointLine(tw.item(row,0).data(Qt.UserRole),False,False)
            via.append(tw.item(row,0).text())
        if not self.checkWithRuler.isChecked():
            line.rulers.clear()
        else:
            line.filtRuler(self.spinRulerCount.value())
        self.lineGenerated.emit(line,via)

    def _adj_line_changed(self,row,col,row0,col0):
        tw = self.tableAdj
        if 0<=row<self.tableAdj.rowCount():
            self.setLineTable(tw.item(row,1).text(),tw.item(row,0).text(),
                              tw.item(row,3).data(Qt.UserRole),tw.item(row,2).data(Qt.UserRole))
        else:
            self.clearLineTable()

    def _adj_add(self):
        """
        从邻接表添加区间数据。
        """
        line = Line()
        tw = self.tableAdj
        row = tw.currentRow()
        if not 0<=row<tw.rowCount():
            return
        line.addStation_by_info(self.lastSelected(),0,counter=0)
        # ['线名','站名','方向','里程','对里程','标尺数','对标尺']
        dir_ = Line.DownVia
        if tw.item(row,1).data(Qt.UserRole) is not None:
            dir_ |= Line.UpVia
        line.addStation_by_info(
            tw.item(row,1).text(),
            tw.item(row,3).data(Qt.UserRole),
            counter=tw.item(row,4).data(Qt.UserRole),
            direction=dir_
        )
        self.addSelectStation(tw.item(row,1).text(),line,'邻站',tw.item(row,0).text())

    def _line_add(self):
        tw = self.tableLine
        row = tw.currentRow()
        if not 1<=row<tw.rowCount():
            return
        subline = self.currentLine.slice(0,row+1)
        self.addSelectStation(tw.item(row,0).text(),subline,'邻线',subline.name)

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, 'pyETRC路网管理模块', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default
"""
帮助对话框，2019.06.25新增，直接显示简明功能表对话框。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .graph import Graph

help_str = """
ctrl+V	当前车次时刻表重排	2.0.2	调整当前车次时刻表顺序错误问题，主要是点单转换过程中的常见错误。
ctrl+W	标尺对照	1.0.7	将当前车次区间运行情况与标尺做对照
ctrl+shift+W	两车次运行对照	1.3.4	选择两个车次，比较区间运行情况
ctrl+X	线路编辑	1.0.7	打开或关闭“线路编辑”停靠面板
ctrl+Y	车次时刻表	2.2.2	打开或关闭只读的“车次时刻表”面板
ctrl+Z	当前车次事件表	1.0.7	显示当前车次在本线的事件表（又称：运行切片）
ctrl+1	天窗编辑	1.2.3	打开或关闭“天窗编辑”停靠面板，编辑和设置显示本线的天窗信息
ctrl+2	推定通过时刻	1.2.5	选择部分车次，根据标尺和已知的停站时刻，推定未在时刻表中的通过站时刻。
ctrl+3	区间对数表	1.3.2	显示到或发本线某站的车次数量。车次被计入，当且仅当车次在两站都有停点。
ctrl+shift+3	区间车次表	1.3.2	显示某两站（不一定是本线）之间（在两站皆有停点）的所有车次。逻辑类似时刻表软件搜索两站之间车次。
ctrl+4	交路编辑	2.2.0	打开或关闭“交路编辑”停靠面板，设置车底交路相关数据。
ctrl+5	区间换线	2.2.4	交换两列车某区间的运行线。原则上只能交换两个交点之间的数据，实际不设限制。
ctrl+=	放大运行图	1.5.2	将运行图显示比例放大至当前的125%。
ctrl+-	缩小运行图	1.5.2	将运行图显示比例缩小至当前的80%。
F1	简明功能表	2.2.2	显示“简明功能表”帮助信息
F5	刷新	1.2.0	重新铺画运行图，重新设置所有停靠面板的数据。
shift+F5	立即铺画运行图	1.3.4	重新铺画运行图，但不更改停靠面板数据。
-	重新读取本运行图	1.0.7	放弃所有更改，重新从文件中读取本运行图。
-	重置所有始发终到站	1.0.7	将所有车次的始发终到站设置为在本线的第一个及最后一个站
-	反排运行图	1.0.7	将车站顺序颠倒，所有车次上下行车次交换
-	重置所有列车营业站	2.1.0	根据线路的默认营业信息，设置所有列车时刻表中的是否办理业务。此操作不可撤销，请慎用。
-	自动设置是否客车	2.1.0	根据类型对应是否客车的信息，将所有“客车”字段为“自动”的车次设置为是或者否。
Alt+D	复制到发时刻	1.0.7	在“选中车次设置”面板有效，将当前行的到达时刻复制到出发时刻中
Alt+C	复制天窗（一行）	1.2.3	在“天窗编辑”面板有效，将当前行数据复制到下一行。同时将光标下移一行。
Alt+shift+C	复制天窗（本方向）	1.2.3	在“天窗编辑”面板有效，将当前行数据复制到本方向（上行或下行）自本行开始的所有行。
Alt+C	排图冲突检查	1.0.7	在“标尺排图向导”运行时有效，检查当前行到发时刻附近的其他列车时刻。
"""

class HelpDialog(QtWidgets.QDialog):
    """
    list<dict> functions
    dict{
        "shortcut":str,
        "name":str,
        "since":str,
        "description":str,
    """
    def __init__(self,graph:Graph,parent=None):
        super(HelpDialog, self).__init__(parent)
        self.graph = graph
        self.functions = []
        self.parseData()
        self.initUI()

    def parseData(self):
        global help_str
        for line in help_str.split('\n'):
            line = line.strip()
            if not line:
                continue
            s = line.split('\t',3)
            if len(s) != 4:
                print("invalid help line!",line)
            dct = {
                "shortcut":s[0],
                "name":s[1],
                "since":s[2],
                "note":s[3],
            }
            self.functions.append(dct)

    def initUI(self):
        self.setWindowTitle('简明功能表')
        self.resize(600,600)
        vlayout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel("双击表中的功能以显示详细信息。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        tableWidget = QtWidgets.QTableWidget()
        tableWidget.setEditTriggers(tableWidget.NoEditTriggers)
        self.tableWidget =tableWidget

        tableWidget.setColumnCount(3)
        tableWidget.setHorizontalHeaderLabels(('快捷键','起始版本','功能'))
        for i,s in enumerate((130,70,290)):
            tableWidget.setColumnWidth(i,s)
        tableWidget.itemDoubleClicked.connect(self._item_double_clicked)

        tableWidget.setRowCount(len(self.functions))
        for row,f in enumerate(self.functions):
            tableWidget.setRowHeight(row,self.graph.UIConfigData()['table_row_height'])
            tableWidget.setItem(row,0,QtWidgets.QTableWidgetItem(f['shortcut']))
            tableWidget.setItem(row,1,QtWidgets.QTableWidgetItem(f['since']))
            tableWidget.setItem(row,2,QtWidgets.QTableWidgetItem(f['name']))
        vlayout.addWidget(tableWidget)
        self.setLayout(vlayout)

    def _item_double_clicked(self,item:QtWidgets.QTableWidgetItem):
        row = item.row()
        note = self.functions[row]['note']
        text = f"{self.functions[row]['name']}的说明：\n"
        text += note
        QtWidgets.QMessageBox.information(self,'详细信息',text)
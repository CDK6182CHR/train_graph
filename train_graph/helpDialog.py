"""
帮助对话框，2019.06.25新增，直接显示简明功能表对话框。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .data.graph import Graph

help_str = """
ctrl+A	调整当前车次时刻	1.0.7	将当前车次的某些站点的到发时刻向前或后移动一定时间
ctrl+shift+A	批量复制当前运行线	1.0.9	将当前车次运行线平移并复制为一组车次。适用于铺画停站情况相同的一组车次。
ctrl+B	标尺编辑	1.0.7	打开或关闭“标尺编辑”停靠面板
ctrl+C	车次编辑	1.0.7	打开或关闭“车次编辑”停靠面板
ctrl+shift+C	添加车次	2.4.0	添加新的车次。相当于在“车次编辑”面板中点击“添加”。
ctrl+D	导入车次	2.2.7	弹出“导入车次”对话框，选择文件，导入其中指定的车次，并可选择是否覆盖冲突车次以及是否引入/覆盖交路，也可添加前缀。此功能合并“导入实际运行线”功能。
ctrl+alt+D	导入车次（旧版）	1.0.7	选择运行图文件，导入其中所有在本线2站以上的车次。可选择是否覆盖既有冲突的车次。旧版快捷键为Ctrl+D，自2.2.7版本改为ctrl+alt+D。
ctrl+shift+D	导入实际运行线（旧版）	1.0.7	选择运行图文件，将其中在本线的车次导入为“实际”类型的车次，其车次前冠以R
ctrl+E	车站时刻表输出	1.0.7	选择本线的车站，给出其时刻表，并支持可视化和导出为Excel.
ctrl+F	搜索车次	1.0.7	输入车次，当车次严格匹配到列车的完整车次或单车次之一时，选中该车次
ctrl+shift+F	模糊检索车次	1.0.9	输入关键字，显示一组包含关键字的完整车次，从下拉列表中选择一个并选中该车次
ctrl+G	运行图设置	1.0.7	打开或关闭“运行图设置”停靠面板，包含运行图比例、边距、线条宽度等设置项
ctrl+shift+G	系统默认设置	1.4.0	打开或关闭“系统默认设置”停靠面板，包含系统默认的比例、边距等设置项。
ctrl+H	线路数据库维护	2.3.0	管理线路数据库。支持导入导出等功能。集成旧版本的线路数据库和导入线路两项功能。
ctrl+alt+H	线路数据库（旧版）	1.0.7	查看或编辑系统的线路数据库。数据存储在lines.json文件中。自2.3.0版本开始，标记为过时。原快捷键为ctrl+H。
ctrl+I	选中车次设置	1.0.7	打开或关闭“选中车次设置”面板。包含当前选中车次的车次名称、时刻表等设置项。
ctrl+J	运行图拼接	1.0.7	选择运行图文件，将该运行图与当前打开的运行图按一定规则拼接
ctrl+K	导入线路（旧版）	1.0.7	从系统的线路数据库lines.json中导入线路数据。自2.3.0版本开始，标记为过时。推荐使用新编的线路数据库管理功能。
ctrl+shift+K	导入线路(Excel)	1.2.0	从Excel表格中导入线路数据
ctrl+L	显示类型设置	1.0.7	打开或关闭“显示类型设置”停靠面板。可选择显示特定类型或行别（上行或下行）的车次运行线。
ctrl+shift+L	高级显示车次设置	1.3.2	使用“车次筛选器”根据类型，车次，上下行等选择显示特定车次。
-	自动适配始发终到站	2.0.2	将符合一定条件的始发终到站站名与时刻表首末站名相适配。原快捷键ctrl+M，将在2.1.0之后的版本中撤销。
ctrl+M	导出为trc格式	1.3.4	将当前运行图导出.trc格式的副本（但不影响原.json格式的运行图文件）。快捷键自2.2.0版本开始启用。
ctrl+N	新建	1.0.7	建立新的空运行图
ctrl+O	打开	1.0.7	打开既有运行图文件
-	线路信息	1.0.7	显示当前线路信息，包含站点总数，里程，车次数量统计等。原快捷键ctrl+P，自2.3.3版本撤销。
ctrl+P	批量识别交路	2.3.3	输入一系列交路的车次序列，每行一个交路，自动识别交路数据。
ctrl+Q	当前车次信息	1.0.7	显示当前车次的始发终到，在本线的停站数，均速等信息。
ctrl+shift+Q	当前车次区间性质计算	1.2.5	计算当前车次在本线某两站间的运行时分，停站数量，均速等，其逻辑类似购票界面的信息。原快捷键是ctrl+shift+W。
ctrl+R	标尺排图向导	1.0.7	根据某一标尺，由用户给出始发时间和各站停靠时长，系统自动计算区间运行时间，铺画列车运行线。
ctrl+shift+R	当前车次区间重排	2.2.4	调用标尺排图向导功能，重新铺画当前选中列车的某一中间区段的运行线。
ctrl+S	保存	1.0.7	将当前运行图信息保存到文件。若本运行图没有保存过，则相当于“另存为”。
F12	另存为	1.0.7	将当前运行图信息保存到一个新的文件。
ctrl+T	导出运行图	1.0.7	导出PNG格式的运行图
ctrl+shift+T	导出pdf矢量运行图	1.4.3	导出PDF格式的矢量运行图
ctrl+U	修改站名	1.0.7	修改站名，同时将所有车次中的原站名修改为新站名
ctrl+shift+U	批量站名映射	1.0.7	维护站名映射表，将站名原站名映射为新站名；选择某些映射来执行。默认选中原站名在本线中的映射。
ctrl+V	当前车次时刻表重排	2.0.2	调整当前车次时刻表顺序错误问题，主要是点单转换过程中的常见错误。
ctrl+W	标尺对照	1.0.7	将当前车次区间运行情况与标尺做对照
ctrl+shift+W	两车次运行对照	1.3.4	选择两个车次，比较区间运行情况
ctrl+X	线路编辑	1.0.7	打开或关闭“线路编辑”停靠面板
ctrl+Y	车次时刻表	2.2.2	打开或关闭只读的“车次时刻表”面板
ctrl+shift+Y	交互式时刻表	2.2.4	打开或关闭交互式修改车次时刻表的面板。在此面板中修改的时刻立即生效，运行线实时变化。
ctrl+Z	当前车次事件表	1.0.7	显示当前车次在本线的事件表（又称：运行切片）
ctrl+1	天窗编辑	1.2.3	打开或关闭“天窗编辑”停靠面板，编辑和设置显示本线的天窗信息
ctrl+2	推定通过时刻	1.2.5	选择部分车次，根据标尺和已知的停站时刻，推定未在时刻表中的通过站时刻。
ctrl+3	区间对数表	1.3.2	显示到或发本线某站的车次数量。车次被计入，当且仅当车次在两站都有停点。
ctrl+shift+3	区间车次表	1.3.2	显示某两站（不一定是本线）之间（在两站皆有停点）的所有车次。逻辑类似时刻表软件搜索两站之间车次。
ctrl+4	交路编辑	2.2.0	打开或关闭“交路编辑”停靠面板，设置车底交路相关数据。
ctrl+5	区间换线	2.2.4	交换两列车某区间的运行线。原则上只能交换两个交点之间的数据，实际不设限制。
ctrl+6	运行图对比	2.3.2	选择运行图文件或车次数据库文件，对比两运行图中车次的时刻表。
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
Alt+X	排图冲突检查	2.2.6	在“标尺排图向导”运行时有效，检查当前行到发时刻附近的其他列车时刻。自2.2.6版本开始由Alt+C改为Alt+X。
Alt+Z	复制“对里程”	2.4.0	在“线路编辑”面板有效，将当前行的“里程”数据复制到“对里程”栏。
Alt+E	计算天窗结束时间	2.4.1	在“天窗编辑”面板有效，根据默认时长和当前行的开始时间，计算当前行结束时间。
Alt+R	计算天窗开始时间	2.4.1	在“天窗编辑”面板有效，根据默认时长和当前行结束时间，反推当前行开始时间。
Alt+Shift+E	计算所有天窗结束时间	2.4.1	在“天窗编辑”面板有效，根据默认时长和所有行的开始时间，计算所有行的结束时间。
Alt+Shift+R	计算天窗开始时间	2.4.1	在“天窗编辑”面板有效，根据默认时长和所有行的结束时间，反推所有行的开始时间。
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
    def __init__(self,graph:Graph,version:str,parent=None):
        super(HelpDialog, self).__init__(parent)
        self.graph = graph
        self.version = version
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
            item = QtWidgets.QTableWidgetItem(f['since'])
            if f['since'] == self.version.lstrip('V'):
                item.setForeground(QtGui.QBrush(Qt.red))
            tableWidget.setItem(row,1,item)
            tableWidget.setItem(row,2,QtWidgets.QTableWidgetItem(f['name']))
        vlayout.addWidget(tableWidget)
        self.setLayout(vlayout)

    def _item_double_clicked(self,item:QtWidgets.QTableWidgetItem):
        row = item.row()
        note = self.functions[row]['note']
        text = f"{self.functions[row]['name']}的说明：\n"
        text += note
        QtWidgets.QMessageBox.information(self,'详细信息',text)
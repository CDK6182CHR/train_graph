"""
线路数据库部分
2018.12.14，抽离main部分，允许单独运行
2019.10.07，将listWidget改为treeWidget, 支持多级分组
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .line import Line
from .lineWidget import LineWidget
from .rulerWidget import RulerWidget
from .forbidWidget import ForbidWidget
from .graph import Graph
import json

class LineDB(QtWidgets.QDialog):
    showStatus = QtCore.pyqtSignal(str)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setParent(parent)
        self.setWindowTitle('线路数据库维护')
        self._initUI()

    def checkAndUpdateData(self,line_dicts:dict):
        """
        2019.10.07新增。检查数据是否为新版本的数据，即支持分类的。
        如果不是，则添加一个“默认分类”。
        直接修改参数。
        """
        old=False
        # 以能找到name和stations两个标签为Line的标志
        for name,value in line_dicts.items():
            if self.dictIsLine(value):
                old=True
        if old:
            line_dicts={"默认分组":line_dicts}

    @staticmethod
    def dictIsLine(dct:dict):
        """
        检查dict是否是有效的Line对象。
        """
        return dct.get("name",None) is not None and dct.get("stations",None) is not None


    def _initUI(self):
        stackedWidget = QtWidgets.QStackedWidget()
        try:
            self.showStatus.emit("正在读取数据库文件……")
            fp = open('lines.json', encoding='utf-8', errors='ignore')
            line_dicts = json.load(fp)
        except:
            self._derr("线路数据库文件错误！请检查lines.json文件。")
            self.showStatus.emit('就绪')
            return
        self.checkAndUpdateData(line_dicts)

        lines = {}  # 分组->Line列表

        progessDialog = QtWidgets.QProgressDialog()
        progessDialog.setMinimum(0)
        total = len(line_dicts)
        progessDialog.setRange(0, total)
        progessDialog.setWindowModality(Qt.WindowModal)
        progessDialog.setWindowTitle(self.tr("正在读取线路信息"))

        self.showStatus.emit("正在解析线路数据……")
        # listWidget = QtWidgets.QListWidget()
        treeWidget=QtWidgets.QTreeWidget()
        count = 0

        # 先支持一级分类
        for category,data in line_dicts.items():
            count += 1
            lines[category]=[]
            topItem=QtWidgets.QTreeWidgetItem(category)
            treeWidget.addTopLevelItem(topItem)
            for name,line_dict in data.items():
                line = Line(origin=line_dict)
                lines[category].append(line)
                widget = LineWidget(line)
                item = QtWidgets.QTreeWidgetItem(f"{count} {name}")
                if count == 1:
                    widget.initWidget()
                    widget.setData()
                    widget.btnOk.clicked.connect(self._update_line)
                    item.setData(-1, (widget,True))  # widget，是否初始化过
                else:
                    item.setData(-1,(widget,False))
                stackedWidget.addWidget(widget)
                # listWidget.addItem(item)
                topItem.addChild(item)
                progessDialog.setValue(count)
                progessDialog.setCancelButtonText(self.tr('取消'))
                if progessDialog.wasCanceled():
                    return
                progessDialog.setLabelText(self.tr(f"正在载入线路数据：{name} ({count}/{total})"))
                QtCore.QCoreApplication.processEvents()
        self.showStatus.emit("读取线路数据成功")

        # listWidget.currentRowChanged.connect(self._change_stacked_current)
        treeWidget.currentItemChanged.connect(self._change_stacked_current)

        cvlayout = QtWidgets.QVBoxLayout()
        cchlayout = QtWidgets.QHBoxLayout()
        lineEdit = QtWidgets.QLineEdit('搜索站名')
        btnSearch = QtWidgets.QPushButton("搜索")

        btnSearch.clicked.connect(lambda: self._search_line_db(lineEdit.text(), lines))
        # lineEdit.editingFinished.connect(lambda :self._search_line_db(lineEdit.text(),lines,dialog))
        cchlayout.addWidget(lineEdit)
        cchlayout.addWidget(btnSearch)
        cvlayout.addLayout(cchlayout)
        cvlayout.addWidget(treeWidget)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addLayout(cvlayout)

        # self.listWidget = listWidget
        self.treeWidget = treeWidget
        self.lines = lines
        self.stackedWidget = stackedWidget

        vlayout = QtWidgets.QVBoxLayout()
        chlayout = QtWidgets.QHBoxLayout()
        btnSave = QtWidgets.QPushButton("保存")
        btnAdd = QtWidgets.QPushButton("新增")
        btnDel = QtWidgets.QPushButton("删除")
        btnRuler = QtWidgets.QPushButton("标尺")
        btnForbid = QtWidgets.QPushButton("天窗")
        btnLoad = QtWidgets.QPushButton("导入")
        chlayout.addWidget(btnSave)
        chlayout.addWidget(btnAdd)
        chlayout.addWidget(btnDel)
        chlayout.addWidget(btnRuler)
        chlayout.addWidget(btnForbid)
        chlayout.addWidget(btnLoad)
        vlayout.addLayout(chlayout)
        vlayout.addWidget(stackedWidget)

        btnSave.clicked.connect(lambda: self._save_line_data(lines))
        btnAdd.clicked.connect(lambda: self._add_line(listWidget, stackedWidget, lines))
        btnDel.clicked.connect(lambda: self._del_line(listWidget, stackedWidget, lines))
        btnRuler.clicked.connect(self._show_line_ruler)
        btnForbid.clicked.connect(self._show_line_forbid)
        btnLoad.clicked.connect(self._load_line_to_database)

        hlayout.addLayout(vlayout)
        self.setLayout(hlayout)


    #slots
    def _search_line_db(self,st_name:str,lines:list):
        """
        搜索站名
        """
        self._derr("对不起，此功能重构中!")
        return
        mathched_int = []
        for i,line in enumerate(lines):
            if line.stationInLine(st_name,strict=False):
                mathched_int.append(i)

        if not mathched_int:
            self._derr("无符合条件线路！")
            return

        if len(mathched_int) > 1:
            lineName,ok = QtWidgets.QInputDialog.getItem(self,"选择线名","下列线路包含所选站名，请选择：",
                                                         [lines[i].name for i in mathched_int])
            if not ok:
                return
            for i,line in enumerate(lines):
                if line.name == lineName:
                    index = i
                    break
        else:
            #唯一匹配
            index = mathched_int[0]

        listWidget:QtWidgets.QListWidget = self.listWidget
        listWidget.setCurrentRow(index)

    def _save_line_data(self,lines:list):
        info_dict = {}
        info_list = []
        for line in lines:
            info_list.append(line.outInfo())
        #排序
        try:
            from xpinyin import Pinyin
        except ImportError:
            self._dout("无法导入xpinyin库，将跳过排序操作。")
        else:
            p = Pinyin()
            takeName = lambda line:p.get_pinyin(line["name"],'')
            info_list.sort(key=takeName)
        for line_dict in info_list:
            info_dict[line_dict["name"]] = line_dict
        with open('lines.json','w',encoding='utf-8',errors='ignore') as fp:
            json.dump(info_dict,fp,ensure_ascii=False)
        self.showStatus.emit("保存线路数据库成功")

    def _add_line(self,listWidget:QtWidgets.QListWidget,stackedWidget,lines:list,line=None):
        index = listWidget.count()
        if line is None:
            line = Line(name='新建线路')
        item = QtWidgets.QListWidgetItem(f"{index+1} {line.name}")
        lines.append(line)
        widget = LineWidget(line)
        stackedWidget.addWidget(widget)
        listWidget.addItem(item)
        listWidget.setCurrentRow(index)  #这一步切换的时候会自动初始化数据。如果提前初始化，会造成重复。

    def _del_line(self,listWidget,stackedWidget,lines:list):
        flag = self.qustion("确认删除当前线路信息？")
        if not flag:
            return
        line = stackedWidget.currentWidget().line
        stackedWidget.removeWidget(stackedWidget.currentWidget())
        listWidget.removeItemWidget(listWidget.currentItem())
        listWidget.takeItem(listWidget.currentRow())
        lines.remove(line)
        for row in range(listWidget.currentRow(),listWidget.count()):
            listWidget.item(row).setText(f"{row+1} {lines[row].name}")

    def _show_line_ruler(self):
        line:Line = self.stackedWidget.currentWidget().line

        rulerDialog = QtWidgets.QDialog(self)
        rulerDialog.setWindowTitle(f"标尺编辑*{line.name}")
        tabWidget = RulerWidget(line)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabWidget)

        rulerDialog.setLayout(layout)
        rulerDialog.exec_()

    def _show_line_forbid(self):
        line: Line = self.stackedWidget.currentWidget().line

        forbidDialog = QtWidgets.QDialog(self)
        forbidDialog.setWindowTitle(f'天窗编辑*{line.name}')
        widget = ForbidWidget(line.forbid)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(widget)

        forbidDialog.setLayout(vlayout)
        forbidDialog.exec_()

    def _load_line_to_database(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                            filter='JSON运行图文件(*.json)\n文本运行图文件(*.trc)\n所有文件(*.*)')[0]
        if not filename:
            return
        graph = Graph()
        try:
            graph.loadGraph(filename)
        except:
            self._derr("文件错误，请重试！")
            return
        self._add_line(self.listWidget,self.stackedWidget,self.lines,graph.line)

    def _update_line(self):
        """
        由点击确定的第二个槽函数触发。
        """
        lines = self.lines
        listWidget:QtWidgets.QListWidget = self.listWidget
        index = listWidget.currentRow()
        line = lines[index]
        widget = self.stackedWidget.currentWidget()
        print("update_line_database", line.name,line,widget)
        listWidget.item(index).setText(f"{index+1} {line.name}")
        for i in lines:
            if i.name == line.name and i is not line:
                self._dout("请注意，重名的线路将会被覆盖！")
                break

    def _change_stacked_current(self,item:QtWidgets.QTreeWidgetItem):
        """
        2019.10.07重构
        """
        widget,inited = item.data(-1)
        if not inited:
            #已经初始化
            widget.initWidget()
            widget.setData()
            widget.btnOk.clicked.connect(lambda: self._update_line)
            item.setData(-1, (widget,True))

        self.stackedWidget.setCurrentWidget(widget)

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def qustion(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '线路数据库', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    dialog = LineDB()
    mainWindow.setCentralWidget(dialog)
    mainWindow.setWindowTitle('线路数据库维护')
    mainWindow.resize(1100,700)
    mainWindow.show()
    sys.exit(app.exec_())
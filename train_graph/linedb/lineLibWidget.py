"""
2019.10.07新增，重新设计的lineDB界面。
注意，线名不可重复。
"""
from .lineLib import Line,LineLib,Category
from ..lineWidget import LineWidget
from .lineTreeWidget import LineTreeWidget
from ..data.graph import Graph
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt


class LineLibWidget(QtWidgets.QWidget):
    ExportLineToGraph = QtCore.pyqtSignal(Line)
    DefaultDBFileChanged = QtCore.pyqtSignal(str)
    def __init__(self,filename='linesNew.pyetlib',fromPyetrc=True,parent=None):
        super(LineLibWidget, self).__init__(parent)
        self.filename=filename
        self.fromPyetrc=fromPyetrc
        self.lineLib = LineLib(filename)
        self.updating=False  # 此状态不弹出对话框
        self.toSave = False
        try:
            self.lineLib.loadLib(filename)
        except:
            QtWidgets.QMessageBox.warning(self,"警告",f"无法解析数据文件{filename}！"
                                                    f"数据为空，可自行构建。")
        self.initUI()
        self.setData()

    def updateBegins(self):
        self.updating=True
        self.treeWidget.updating=True

    def updateEnds(self):
        self.updating=False
        self.treeWidget.updating=False

    def initUI(self):
        """
        这次建立Layout后先添加到父级，再添加下级内容。
        """
        self.setWindowTitle("线路数据库维护")
        self.resize(1300,700)

        vlayout = QtWidgets.QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        vlayout.addLayout(hlayout)
        editSearch = QtWidgets.QLineEdit()
        self.editSearch = editSearch
        hlayout.addWidget(editSearch)

        btnSearchStation = QtWidgets.QPushButton('搜索站名')
        hlayout.addWidget(btnSearchStation)
        btnSearchStation.clicked.connect(self._search_station)
        btnSearchLine = QtWidgets.QPushButton('搜索线名')
        hlayout.addWidget(btnSearchLine)
        btnSearchLine.clicked.connect(self._search_line)

        editFile = QtWidgets.QLineEdit(self.filename)
        editFile.setFocusPolicy(Qt.NoFocus)
        self.editFile = editFile
        hlayout.addWidget(editFile)

        btnChangeFile = QtWidgets.QPushButton('选择文件')
        hlayout.addWidget(btnChangeFile)
        btnChangeFile.clicked.connect(self.change_filename)

        btnDefaultFile = QtWidgets.QPushButton('设为默认文件')
        hlayout.addWidget(btnDefaultFile)
        btnDefaultFile.clicked.connect(self._set_default_filename)

        hlayout = QtWidgets.QHBoxLayout()
        vlayout.addLayout(hlayout)

        treeWidget = LineTreeWidget(self.lineLib,detail=True)
        treeWidget.ShowLine.connect(self._show_line)
        treeWidget.currentItemChanged.connect(self._tree_item_changed)
        hlayout.addWidget(treeWidget)
        self.treeWidget = treeWidget

        cvlayout = QtWidgets.QVBoxLayout()
        hlayout.addLayout(cvlayout)
        buttons = {
            "添加线路":self._new_line,
            "添加子类":self._new_category,
            "添加平行类":self.treeWidget.new_parallel_category,
            "删除选定":self._del_element,
            "移动选定":self._move_line,
            "标尺":self._edit_ruler,
            "天窗":self._edit_forbid,
            "导入文件":self._import_line,
            "批量导入":self._batch_import_line,
            "合并数据":self._merge_lib,
            "导出文件":self._export_data,
            "导出到运行图":self._export_to_graph,
            "保存":self.save_lib,
        }
        for txt,func in buttons.items():
            btn = QtWidgets.QPushButton(txt)
            cvlayout.addWidget(btn)
            btn.clicked.connect(func)
        check = QtWidgets.QCheckBox('批量模式')
        check.toggled.connect(self.treeWidget.batch_changed)
        cvlayout.addWidget(check)

        lineWidget = LineWidget(self.lineLib.firstLine())
        lineWidget.initWidget()
        # lineWidget.setData()  # !!setData不可以重复调用
        self.lineWidget = lineWidget
        hlayout.addWidget(lineWidget)

        lineWidget.lineNameChanged.connect(self.treeWidget.line_name_changed)
        lineWidget.LineApplied.connect(self._line_applied)

    def setData(self):
        """

        """
        self.treeWidget.setData()

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '提示', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

    def checkUnsavedLine(self, line)->bool:
        """
        询问是否保存，返回是否要返回原来的位置。
        i.e. 返回True iff 选择Cancel或直接关闭。
        """
        if not isinstance(line,Line):
            return
        flag = QtWidgets.QMessageBox.question(self, "提示", f"是否保存对线路[{line.name}]的修改？",
                                              QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                                              QtWidgets.QMessageBox.Cancel)
        if flag == QtWidgets.QMessageBox.Yes:
            self.lineWidget.apply_line_info_change()
        elif flag == QtWidgets.QMessageBox.Cancel or flag == QtWidgets.QMessageBox.NoButton:
            return True
        return False

    def checkUnsavedLib(self):
        flag = QtWidgets.QMessageBox.question(self, "提示",
                                              f"是否保存对数据库文件[{self.filename}]的修改？",
                                              QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                                              QtWidgets.QMessageBox.Cancel)
        if flag == QtWidgets.QMessageBox.Yes:
            self.save_lib()
        elif flag == QtWidgets.QMessageBox.Cancel or flag == QtWidgets.QMessageBox.NoButton:
            return True
        return False

    def selectSearchedItems(self,matched:dict)->QtWidgets.QTreeWidgetItem:
        """
        搜索之后弹出选择对话框，返回要设为当前的item。
        """
        if len(matched) == 0:
            QtWidgets.QMessageBox.information(self,'搜索站名','无符合条件线路！')
            return None
        elif len(matched) == 1:
            selected = list(matched.keys())[0]
        else:
            selected,ok = QtWidgets.QInputDialog.getItem(self,'选择线名','有下列线路符合,请选择: ',list(matched.keys()))
            if not ok:
                return None
        line:Line = matched[selected]
        item:QtWidgets.QTreeWidgetItem = line.getItem()
        return item

    def importLine(self,newLine:Line,filename:str)->bool:
        """
        先创建好Line对象，再将其数据设置为filename所指向的运行图文件中的线路数据。
        返回是否成功。
        为批量导入提供接口。
        """
        graph = Graph()
        try:
            graph.loadGraph(filename)
        except:
            self._derr("文件错误，请重试！")
            return False
        newLine.copyData(graph.line, True)
        return True


    # slots
    def _search_station(self):
        kw = self.editSearch.text()
        matched = self.lineLib.searchStation(kw)
        item = self.selectSearchedItems(matched)
        if item is not None:
            self.treeWidget.setCurrentItem(item)

    def _search_line(self):
        kw = self.editSearch.text()
        matched = self.lineLib.searchLineName(kw)
        item = self.selectSearchedItems(matched)
        if item is not None:
            self.treeWidget.setCurrentItem(item)

    def change_filename(self):
        if self.checkUnsavedLib():
            return
        filename,ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC数据库文件(*.pyetlib;*.json)\n所有文件(*.*)')
        if not ok:
            return
        self.filename = filename
        try:
            self.lineLib.loadLib(filename)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','文件错误：\n'+repr(e))
            return
        self.editFile.setText(filename)
        self.setData()

    def _set_default_filename(self):
        if not self.fromPyetrc:
            QtWidgets.QMessageBox.warning(self,'提示','设为默认数据库文件：此功能仅当在pyETRC主系统启动本维护窗口时有效！')
            return
        if not self.question('此功能设置当前的数据库文件为默认数据库文件，以后从pyETRC主系统启动数据库管理时，将自动打开该文件。是否继续？'):
            return
        self.DefaultDBFileChanged.emit(self.editFile.text())

    def _new_line(self)->Line:
        item = self.treeWidget.currentItem()
        if not isinstance(item,QtWidgets.QTreeWidgetItem):
            # 添加到根目录下
            return self.treeWidget.newRootLine()
        self.toSave = True
        if item.type()==0:
            return self.treeWidget.newLine(item)
        parent = item.parent()
        if isinstance(parent,QtWidgets.QTreeWidgetItem):
            return self.treeWidget.newLine(parent)
        else:
            return self.treeWidget.newRootLine()

    def _new_category(self):
        item = self.treeWidget.currentItem()
        if not isinstance(item, QtWidgets.QTreeWidgetItem):
            # 根目录
            self.treeWidget.newRootCategory()
            return
        if item.type() == 0:
            self.treeWidget.newCategory(item)
            return
        parent = item.parent()
        if isinstance(parent, QtWidgets.QTreeWidgetItem):
            self.treeWidget.newCategory(parent)
        else:
            self.treeWidget.newParallelCategory(item)
        self.toSave=True

    def _del_element(self):
        self.treeWidget.del_item()
        self.toSave=True

    def _move_line(self):
        self.treeWidget.moveSomeItems(self.treeWidget.selectedItems())

    def _edit_ruler(self):
        self.treeWidget.showRuler(self.lineWidget.line)

    def _edit_forbid(self):
        self.treeWidget.showForbid(self.lineWidget.line)

    def _import_line(self):
        """
        导入线路，先执行添加线路的逻辑，再导入和读取，然后执行。
        """
        newLine = self._new_line()
        if newLine is None:
            return
        filename, ok = QtWidgets.QFileDialog.getOpenFileName(self, "导入运行图",
                                                             filter='pyETRC运行图文件(*.pyetgr;*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')
        if not ok:
            return
        self.updateBegins()
        if self.importLine(newLine,filename):
            self.lineWidget.setLine(newLine)
            self.lineWidget.apply_line_info_change()
            self.treeWidget.setCurrentLine(newLine)
        else:
            self.treeWidget.setCurrentLine(newLine)
            self.treeWidget.del_line(force=True)
        self.updateEnds()


    def _batch_import_line(self):
        newLine = self._new_line()
        if newLine is None:
            return
        filenames, ok = QtWidgets.QFileDialog.getOpenFileNames(self, "批量导入运行图",
                                                              filter='pyETRC运行图文件(*.pyetgr;*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')
        if not ok:
            return
        self.updateBegins()
        cntok,cntignore = 0,0
        for filename in filenames:
            oldName = newLine.name
            if self.importLine(newLine,filename):
                # 读取成功，先检查名字
                if self.lineLib.nameExisted(newLine.name,newLine):
                    print('名称冲突',newLine.name)
                    cntignore+=1
                else:
                    cntok+=1
                    self._line_applied(newLine)
                    self.treeWidget.line_name_changed(newLine,newLine.name,oldName)
                    newLine=self._new_line()
        self.treeWidget.setCurrentLine(newLine)  # 最后一个肯定是多余的！
        self.treeWidget.del_line(force=True)
        self.updateEnds()
        QtWidgets.QMessageBox.information(self,'提示',f'成功导入{cntok}条线路，另有{cntignore}条线路因名称冲突被忽略。')


    def _merge_lib(self):
        """
        选择数据库文件，然后合并两个数据库，忽略所有重复项。
        """
        cat = self.treeWidget.currentWorkingCategory()
        if not self.question(f'选择另一个数据库文件，将其和本数据库合并，并忽略所有名称重复项。\n'
                             f'当前将导入{cat.name}分类下。是否继续？'):
            return
        filename, ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                             filter='pyETRC数据库文件(*.pyetlib;*.json)\n所有文件(*.*)')
        if not ok:
            return
        newLib = LineLib()
        try:
            newLib.loadLib(filename)
        except:
            QtWidgets.QMessageBox.warning(self,'错误','文件无效！')
            return
        c,d = cat.merge(self.lineLib,newLib)  # 有问题！
        QtWidgets.QMessageBox.information(self,'提示',f'成功导入{c}条线路。\n有{d}条线路因名称或类名称冲突而被忽略。')
        self.setData()

    def save_lib(self):
        self.lineLib.saveLib(self.filename)
        self.toSave=False

    def _show_line(self,line:Line):
        self.lineWidget.setLine(line)

    def _line_applied(self,line:Line):
        self.treeWidget.updateLineRow(line)
        self.toSave=True

    def _tree_item_changed(self,item:QtWidgets.QTreeWidgetItem,pre:QtWidgets.QTreeWidgetItem):
        if self.updating:
            return
        elif pre is item:
            return
        if not isinstance(item,QtWidgets.QTreeWidgetItem):
            return
        line = item.data(0,Qt.UserRole)
        if not isinstance(line,Line):
            return
        if pre is None:
            self._show_line(line)
            return
        oldLine = pre.data(0,Qt.UserRole)
        if not isinstance(oldLine,Line):
            return
        if self.lineWidget.toSave:
            if self.updating or self.checkUnsavedLine(oldLine):
                self.updating=True
                self.treeWidget.setCurrentItem(pre)
                self.updating=False
            else:
                self._show_line(line)
        else:
            self._show_line(line)

    def _export_data(self):
        """
        导出数据，如果选中的是类则导出数据库文件，如果选中的是线路则导出运行图文件。
        """
        item:QtWidgets.QTreeWidgetItem = self.treeWidget.currentItem()
        if item is None:
            QtWidgets.QMessageBox.warning(self,'提示','导出数据：请先选择一个类或者线路再执行此操作。如果选中一个类则导出数据库文件，如果选中一条线路则导出运行图文件。')
            return
        data = item.data(0,Qt.UserRole)
        if isinstance(data,Category):
            newLib = LineLib()
            newLib.copyData(data)
            filename, ok = QtWidgets.QFileDialog.getSaveFileName(self, "导出子数据库",newLib.name,
                                                                 filter='pyETRC数据库文件(*.pyetlib;*.json)\n所有文件(*.*)')
            if not ok:
                return
            newLib.saveLib(filename)
        elif isinstance(data,Line):
            newGraph = Graph()
            newGraph.setLine(data)
            filename, ok = QtWidgets.QFileDialog.getSaveFileName(self, "导出运行图",newGraph.lineName(),
                                                                 filter='pyETRC运行图文件(*.pyetgr;*.json)\n所有文件(*.*)')
            if not ok:
                return
            newGraph.save(filename)

    def _export_to_graph(self):
        if not self.fromPyetrc:
            QtWidgets.QMessageBox.warning(self,'提示','导出到运行图：此功能仅当在pyETRC主系统启动本维护窗口时有效！')
            return
        line = self.treeWidget.currentLine()
        if line is None:
            QtWidgets.QMessageBox.warning(self,'提示','导出到运行图：请先在列表中选择一条线路再执行本操作！')
            return
        if not self.question('此功能相当于旧版的导入线路（ctrl+K）功能。此操作将覆盖当前运行图的线路数据，是否确认？'):
            return
        stDialog = QtWidgets.QDialog(self)
        stDialog.setWindowTitle('选择车站')
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("请在下表中选择要导入的车站（按ctrl或shift或直接拖动来多选），"
                                 "或直接选择下方的“全选”。")
        label.setWordWrap(True)
        vlayout.addWidget(label)

        listWidget = QtWidgets.QListWidget()
        listWidget.setSelectionMode(listWidget.MultiSelection)
        for st in line.stationDicts():
            name, mile = st["zhanming"], st["licheng"]
            listWidget.addItem(f"{mile} km  {name}")
        vlayout.addWidget(listWidget)
        stDialog.listWidget = listWidget

        btnOk = QtWidgets.QPushButton("确定")
        btnAll = QtWidgets.QPushButton("全选")
        btnCancel = QtWidgets.QPushButton("取消")

        btnOk.clicked.connect(lambda: self._export_line_ok(line, stDialog, False))
        btnAll.clicked.connect(lambda: self._export_line_ok(line, stDialog, True))
        btnCancel.clicked.connect(stDialog.close)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnAll)
        hlayout.addWidget(btnCancel)
        vlayout.addLayout(hlayout)

        stDialog.setLayout(vlayout)
        stDialog.exec_()

    def _export_line_ok(self,line:Line,dialog:QtWidgets.QDialog,all:bool):
        newLine = Line(line.name)
        if all:
            newLine.copyData(line, withRuler=True)
        else:
            listWidget: QtWidgets.QListWidget = dialog.listWidget
            for idx in listWidget.selectedIndexes():
                row = idx.row()
                newLine.addStationDict(line.stationDictByIndex(row))
            newLine.rulers = line.rulers
        self.ExportLineToGraph.emit(newLine)
        dialog.close()

    def closeEvent(self, event:QtGui.QCloseEvent):
        # if self.toSave:
        if self.checkUnsavedLib():
            event.ignore()
            return
        event.accept()

    # def keyPressEvent(self, event:QtGui.QKeyEvent):
    #     """
    #     禁用ESC退出
    #     """
    #     if event.key() != Qt.Key_Escape:
    #         super().keyPressEvent(event)
    #     else:
    #         self.close()





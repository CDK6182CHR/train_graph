"""
2019.10.08新增。
用于显示线路列表的treeWidget派生类。所有信号只允许通过Line或Category传递。

Item中的规定：
item.data(0,Qt.UserRole)  存储对应的Category或Line对象
item.type 0->Category 1->Line
"""
from .lineLib import LineLib,Category,Line
from ..rulerWidget import RulerWidget
from ..forbidWidget import ForbidWidget
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt

class LineTreeWidget(QtWidgets.QTreeWidget):
    ShowLine = QtCore.pyqtSignal(Line)
    def __init__(self,lineLib,parent=None):
        super(LineTreeWidget, self).__init__(parent)
        self.lineLib = lineLib  # type: LineLib
        self.initUI()

    def initUI(self):
        self.setColumnCount(4)
        self.setHeaderLabels(('线名','里程','起点','终点'))
        for i,s in enumerate((200,60,90,90)):
            self.setColumnWidth(i,s)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.initActions()
        self.currentItemChanged.connect(self._item_changed)
        self.itemDoubleClicked.connect(self._show_item)

    def initActions(self):
        """
        右键菜单
        """
        # 线路右键菜单
        lineMenu = QtWidgets.QMenu(self)
        self.lineMenu = lineMenu
        actionShow = QtWidgets.QAction('显示',self)
        lineMenu.addAction(actionShow)
        actionShow.triggered.connect(self._show_item)
        actionDelete = QtWidgets.QAction('删除',self)
        lineMenu.addAction(actionDelete)
        actionDelete.triggered.connect(self.del_line)
        actionRuler = QtWidgets.QAction('标尺',self)
        lineMenu.addAction(actionRuler)
        actionRuler.triggered.connect(self._show_ruler)
        actionForbid = QtWidgets.QAction('天窗',self)
        actionForbid.triggered.connect(self._show_forbid)
        lineMenu.addAction(actionForbid)
        lineMenu.addSeparator()
        actionMoveLine = QtWidgets.QAction('移动到...',self)
        lineMenu.addAction(actionMoveLine)
        actionMoveLine.triggered.connect(self._move_line)
        actionNewParallel = QtWidgets.QAction('新建平行分类', self)
        actionNewParallel.triggered.connect(self.new_parallel_category)
        lineMenu.addAction(actionNewParallel)

        # 分类右键菜单
        categoryMenu = QtWidgets.QMenu(self)
        self.categoryMenu = categoryMenu
        actionExpand = QtWidgets.QAction('展开',self)
        categoryMenu.addAction(actionExpand)
        actionExpand.triggered.connect(self._expand_current)
        actionCollapse = QtWidgets.QAction('折叠',self)
        categoryMenu.addAction(actionCollapse)
        actionCollapse.triggered.connect(self._collapse_current)
        actionRename = QtWidgets.QAction('重命名',self)
        actionRename.triggered.connect(self._rename_category)
        categoryMenu.addAction(actionRename)
        categoryMenu.addSeparator()

        actionNewLine = QtWidgets.QAction('新建线路',self)
        actionNewLine.triggered.connect(self.new_line)
        categoryMenu.addAction(actionNewLine)
        actionNewCat = QtWidgets.QAction('新建子分类',self)
        actionNewCat.triggered.connect(self.new_category)
        categoryMenu.addAction(actionNewCat)
        actionNewParallel = QtWidgets.QAction('新建平行分类',self)
        actionNewParallel.triggered.connect(self.new_parallel_category)
        categoryMenu.addAction(actionNewParallel)

        categoryMenu.addSeparator()

        actionMoveCategory = QtWidgets.QAction('移动到...',self)
        categoryMenu.addAction(actionMoveCategory)
        actionMoveCategory.triggered.connect(self._move_category)
        actionDeleteCategory = QtWidgets.QAction('删除', self)
        actionDeleteCategory.triggered.connect(self.del_category)
        categoryMenu.addAction(actionDeleteCategory)


    def contextMenuEvent(self, event:QtGui.QContextMenuEvent):
        pos = self.mapToGlobal(event.pos())
        item:QtWidgets.QTreeWidgetItem = self.currentItem()
        if item is None:
            return
        elif item.type()==0:
            self.categoryMenu.popup(pos)
        elif item.type()==1:
            self.lineMenu.popup(pos)

    def setData(self):
        """
        解析并显示LineLib中的全部线路内容。
        """
        for name,t in self.lineLib.items():
            if isinstance(t,Category):
                self.addData(t,self)
            elif isinstance(t,Line):
                item0 = QtWidgets.QTreeWidgetItem(self,
                        (t.name,str(t.lineLength()),
                         t.firstStationName(),t.lastStationName()),1)
                item0.setData(0,Qt.UserRole,t)
            else:
                print("invalid",type(t))
        self.expandAll()

    def addData(self,data:Category,parentItem=None):
        """
        DFS，递归添加所有线路信息
        """
        item = QtWidgets.QTreeWidgetItem(parentItem,(data.name,),0)
        item.setData(0,Qt.UserRole,data)  # col,role
        for name,t in data.items():
            if isinstance(t,Category):
                self.addData(t,item)
            elif isinstance(t,Line):
                item0 = QtWidgets.QTreeWidgetItem(item,
                        (t.name,str(t.lineLength()),
                         t.firstStationName(),t.lastStationName()),1)
                item0.setData(0,Qt.UserRole,t)
            else:
                print("invalid",type(t))

    def updateLineRow(self,line:Line):
        pass

    def showRuler(self,line:Line):
        """
        这一组作为接口函数，由dialog和本类的slots调用。
        代码直接从旧版复制过来。
        """
        rulerDialog = QtWidgets.QDialog(self)
        rulerDialog.setWindowTitle(f"标尺编辑*{line.name}")
        tabWidget = RulerWidget(line)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabWidget)

        rulerDialog.setLayout(layout)
        rulerDialog.exec_()

    def showForbid(self,line:Line):
        forbidDialog = QtWidgets.QDialog(self)
        forbidDialog.setWindowTitle(f'天窗编辑*{line.name}')
        widget = ForbidWidget(line.forbid)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(widget)

        forbidDialog.setLayout(vlayout)
        forbidDialog.exec_()

    def newLine(self,item:QtWidgets.QTreeWidgetItem):
        cat = item.data(0,Qt.UserRole)
        if item.type()!=0 or not isinstance(cat,Category):
            return
        line = Line(self.lineLib.validNewName('新线路'))
        cat.addLine(line)
        item0 = QtWidgets.QTreeWidgetItem(item,(line.name,str(line.lineLength()),line.firstStationName(),line.lastStationName()),1)
        item0.setData(0,Qt.UserRole,line)

    def newRootLine(self):
        line = Line(self.lineLib.validNewName('新线路'))
        self.lineLib.addLine(line)
        item0 = QtWidgets.QTreeWidgetItem(self, (
        line.name, str(line.lineLength()), line.firstStationName(), line.lastStationName()), 1)
        item0.setData(0, Qt.UserRole, line)

    def newCategory(self,item:QtWidgets.QTreeWidgetItem):
        cat = item.data(0, Qt.UserRole)
        if item.type() != 0 or not isinstance(cat, Category):
            return
        newCat = Category(self.lineLib.validNewName('新分类'),parent=cat)
        cat.addCategory(newCat)
        item0 = QtWidgets.QTreeWidgetItem(item, (
        newCat.name,), 0)
        item0.setData(0, Qt.UserRole, newCat)

    def newParallelCategory(self,item:QtWidgets.QTreeWidgetItem):
        parent = item.parent()
        if isinstance(parent,QtWidgets.QTreeWidgetItem):
            self.newCategory(parent)
        else:
            # 表明是根目录下新增
            newCat = Category(self.lineLib.validNewName('新分类'),parent=None)
            self.lineLib.addCategory(newCat)
            item = QtWidgets.QTreeWidgetItem(
                self,(newCat.name,),0,
            )
            item.setData(0,Qt.UserRole,newCat)

    def itemByLine(self,line:Line)->QtWidgets.QTreeWidgetItem:
        pass

    def currentLine(self)->Line:
        item: QtWidgets.QTreeWidgetItem = self.currentItem()
        line: Line = item.data(0, Qt.UserRole)
        if not isinstance(line, Line):
            return None
        return line

    def currentCategory(self)->Category:
        item: QtWidgets.QTreeWidgetItem = self.currentItem()
        cat:Category = item.data(0, Qt.UserRole)
        if not isinstance(cat, Category):
            return None
        return cat

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, '提示', note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

    def _deleteItem(self,item:QtWidgets.QTreeWidgetItem):
        parent = item.parent()
        item.takeChildren()
        if isinstance(parent,QtWidgets.QTreeWidgetItem):
            parent.removeChild(item)
        else:
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))

    # slots
    def _show_item(self):
        self.ShowLine.emit(self.currentLine())

    def del_line(self):
        line = self.currentLine()
        item:QtWidgets.QTreeWidgetItem = self.currentItem()
        if item is None or not self.question(f'是否确认删除线路[{line.name}]？'):
            return
        self.lineLib.delLine(line)
        self._deleteItem(item)

    def del_item(self):
        """
        由dialog调用，删除line或者cat。
        """
        item = self.currentItem()
        if not isinstance(item,QtWidgets.QTreeWidgetItem):
            return
        if item.type()==0:
            self.del_category()
        elif item.type()==1:
            self.del_line()

    def _show_ruler(self):
        line = self.currentLine()
        if line is not None:
            self.showRuler(line)

    def _show_forbid(self):
        line = self.currentLine()
        if line is not None:
            self.showForbid(line)

    def _move_line(self):
        pass

    def _expand_current(self):
        self.currentItem().expand()

    def _collapse_current(self):
        self.currentItem().collapse()

    def _move_category(self):
        pass

    def del_category(self):
        cat = self.currentCategory()
        item = self.currentItem()
        if cat is None or not isinstance(item,QtWidgets.QTreeWidgetItem):
            return
        if not self.question(f'删除分类[{cat.name}]及其下所有分类和线路，是否确认？'):
            return
        self.lineLib.delChildCategory(cat)
        self._deleteItem(item)

    def _item_changed(self,item:QtWidgets.QTreeWidgetItem):
        """

        """
        if isinstance(item.data(0,Qt.UserRole),Line):
            self.ShowLine.emit(item.data(0,Qt.UserRole))

    def new_category(self):
        item = self.currentItem()
        if isinstance(item,QtWidgets.QTreeWidgetItem):
            self.newCategory(item)

    def new_parallel_category(self):
        item = self.currentItem()
        if isinstance(item,QtWidgets.QTreeWidgetItem):
            self.newParallelCategory(item)

    def new_line(self):
        item = self.currentItem()
        if isinstance(item,QtWidgets.QTreeWidgetItem):
            self.newLine(item)

    def _rename_category(self):
        cat = self.currentCategory()
        item = self.currentItem()
        if not isinstance(cat,Category) or not isinstance(item,QtWidgets.QTreeWidgetItem):
            return
        name,ok = QtWidgets.QInputDialog.getText(self,'重命名',f'将{cat.name}重命名为')
        if not ok:
            return
        while self.lineLib.nameExisted(name):
            QtWidgets.QMessageBox.warning(self,'提示',f'名称{name}已存在！')
            name, ok = QtWidgets.QInputDialog.getText(self, '重命名', f'将{cat.name}重命名为')
            if not ok:
                return
        cat.setName(name)
        item.setText(0,name)

    def line_name_changed(self,line:Line,newName:str,oldName:str):
        """
        线名修改，需要修改映射关系。 todo here
        """
        pass



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
from typing import List

class LineTreeWidget(QtWidgets.QTreeWidget):
    ShowLine = QtCore.pyqtSignal(Line)
    def __init__(self,lineLib,detail=True,parent=None):
        super(LineTreeWidget, self).__init__(parent)
        self.lineLib = lineLib  # type: LineLib
        self.updating=False
        self.detail=detail
        self.initUI()

    def initUI(self):
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
        if not self.detail:
            return
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
        self.clear()
        self.setColumnCount(4)
        self.setHeaderLabels(('线名', '里程', '起点', '终点'))
        for i, s in enumerate((200, 60, 90, 90)):
            self.setColumnWidth(i, s)
        self.addData(self.lineLib)

    def addData(self,data:Category,parentItem=None):
        """
        DFS，递归添加所有线路信息
        """
        if parentItem is not None:
            item = QtWidgets.QTreeWidgetItem(parentItem,(data.name,str(data.lineCount())),0)
            item.setData(0,Qt.UserRole,data)  # col,role
        else:
            item = self
        for name,t in data.items():
            if isinstance(t,Category):
                self.addData(t,item)
            elif isinstance(t,Line) and self.detail:
                item0 = QtWidgets.QTreeWidgetItem(item,
                        (t.name,str(t.lineLength()),
                         t.firstStationName(),t.lastStationName()),1)
                item0.setData(0,Qt.UserRole,t)
                t.setItem(item0)

    def updateParentItemCount(self,item:QtWidgets.QTreeWidgetItem,dx=1):
        item = item.parent()
        while isinstance(item,QtWidgets.QTreeWidgetItem):
            if item.type()==0:
                try:
                    cur = int(item.text(1))
                except ValueError:
                    cur=0
                item.setText(1,str(cur+dx))
            item=item.parent()

    def addItem(self,obj,parent):
        """
        将Line或者Category添加到treeWidget中，对Line设置映射。
        主要由move过程调用。
        """
        if isinstance(obj,Line):
            item = QtWidgets.QTreeWidgetItem(parent,
                                             (obj.name,str(obj.lineLength()),obj.firstStationName(),
                                              obj.lastStationName()),1
                                             )
        elif isinstance(obj,Category):
            item = QtWidgets.QTreeWidgetItem(parent,
                                             (obj.name,str(obj.lineCount())),0)
        item.setData(0,Qt.UserRole,obj)
        self.updateParentItemCount(item,1)


    def updateLineRow(self,line:Line):
        """
        线路那边提交了信息，更新treeWidget中的。
        """
        item:QtWidgets.QTreeWidgetItem = line.getItem()
        if item is None:
            print("LineTreeWidget::updateLineRow: item is None",line)
            return
        for i,s in enumerate((line.name,str(line.lineLength()),
                              line.firstStationName(),line.lastStationName())):
            item.setText(i,s)


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

    def newLine(self,item:QtWidgets.QTreeWidgetItem)->Line:
        """
        返回新增的线路
        """
        cat = item.data(0,Qt.UserRole)
        if item.type()!=0 or not isinstance(cat,Category):
            return None
        line = Line(self.lineLib.validNewName('新线路'))
        cat.addLine(line)
        item0 = QtWidgets.QTreeWidgetItem(item,(line.name,str(line.lineLength()),line.firstStationName(),line.lastStationName()),1)
        item0.setData(0,Qt.UserRole,line)
        line.setItem(item0)
        self.setCurrentItem(item0)
        self.updateParentItemCount(item0, 1)
        return line

    def newRootLine(self)->Line:
        line = Line(self.lineLib.validNewName('新线路'))
        self.lineLib.addLine(line)
        item0 = QtWidgets.QTreeWidgetItem(self, (
        line.name, str(line.lineLength()), line.firstStationName(), line.lastStationName()), 1)
        item0.setData(0, Qt.UserRole, line)
        line.setItem(item0)
        self.setCurrentItem(item0)
        return line

    def newCategory(self,item:QtWidgets.QTreeWidgetItem):
        cat = item.data(0, Qt.UserRole)
        if item.type() != 0 or not isinstance(cat, Category):
            return
        newCat = Category(self.lineLib.validNewName('新分类'),parent=cat)
        cat.addCategory(newCat)
        item0 = QtWidgets.QTreeWidgetItem(item, (
        newCat.name,'0'), 0)
        item0.setData(0, Qt.UserRole, newCat)
        self.updateParentItemCount(item0, 1)
        self.setCurrentItem(item0)

    def newParallelCategory(self,item:QtWidgets.QTreeWidgetItem):
        parent = item.parent()
        if isinstance(parent,QtWidgets.QTreeWidgetItem):
            self.newCategory(parent)
        else:
            # 表明是根目录下新增
            newCat = Category(self.lineLib.validNewName('新分类'),parent=None)
            self.lineLib.addCategory(newCat)
            item = QtWidgets.QTreeWidgetItem(
                self,(newCat.name,'0'),0,
            )
            item.setData(0,Qt.UserRole,newCat)
            self.setCurrentItem(item)

    def itemByLine(self,line:Line)->QtWidgets.QTreeWidgetItem:
        itr = QtWidgets.QTreeWidgetItemIterator(self)
        while(itr.value()):
            if itr.value().data(0,Qt.UserRole) is line:
                return itr.value()
            itr+=1
        return None

    def itemByName(self,name:str)->QtWidgets.QTreeWidgetItem:
        """
        给出名称，返回item。
        """
        for i in range(self.topLevelItemCount()):
            item:QtWidgets.QTreeWidgetItem = self.topLevelItem(i)
            if item.type()==0:  # Cat结点
                sub = self.findSubItemByName(name,item)
                if sub is not None:
                    return sub
            else:
                if item.text(0)==name:
                    return item
        return None

    def findSubItemByName(self,name:str,root:QtWidgets.QTreeWidgetItem)->QtWidgets.QTreeWidgetItem:
        for i in range(root.childCount()):
            item:QtWidgets.QTreeWidgetItem = root.child(i)
            if item.type()==0:
                rec = self.findSubItemByName(name,item)
                if rec is not None:
                    return rec
            else:
                if item.text(0)==name:
                    return item
        return None

    def currentLine(self)->Line:
        item: QtWidgets.QTreeWidgetItem = self.currentItem()
        line: Line = item.data(0, Qt.UserRole)
        if not isinstance(line, Line):
            return None
        return line

    def setCurrentLine(self,line:Line):
        if isinstance(line,Line):
            item = line.getItem()
            if item is not None:
                self.setCurrentItem(item)

    def currentCategory(self)->Category:
        item: QtWidgets.QTreeWidgetItem = self.currentItem()
        cat:Category = item.data(0, Qt.UserRole)
        if not isinstance(cat, Category):
            return None
        return cat

    def currentWorkingCategory(self)->Category:
        """
        当前选中的item对应category，并必须返回值。
        如果当前选中的是Line，返回它的父对象。
        如果没有父对象，返回根目录！
        """
        item = self.currentItem()
        if isinstance(item,QtWidgets.QTreeWidgetItem):
            if item.type() == 0:
                # 目录
                return item.data(0,Qt.UserRole)
            else:
                parent = item.parent()
                if isinstance(parent,QtWidgets.QTreeWidgetItem):
                    return parent.data(0,Qt.UserRole)
                else:
                    return self.lineLib
        else:
            return self.lineLib

    def moveSomeItems(self,items:List[QtWidgets.QTreeWidgetItem]):
        """
        接口。移动一组选中的对象到指定的分类下。
        items中的数据可能是None，跨过它们。
        先显示对话框来选择对象，再调起相关操作。
        对每一个对象分别调用。先处理数据域，再处理item。item就在本类处理。数据域不管item。
        数据域处理方法：目标cat.moveDrops(obj).
        """
        for item in items.copy():
            if item is None:
                items.remove(item)
        if not items:
            QtWidgets.QMessageBox.warning(self,'提示','请先选择一个（一组）线路或分类，再执行此操作！')
            return
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('选择目标目录')
        vlayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(f'请选择目标目录。如果不选择，则放到根目录下。\n'
                                 f'当前选择了{len(items)}个对象，所选的线路、分类及其下所有线路都将被移动到目标目录下，且选择的所有对象，除非存在包含关系，都视为平级。\n'
                                 f'不要尝试会引发递归的操作，否则可能导致不可预料的结果。')
        label.setWordWrap(True)
        vlayout.addWidget(label)
        label = QtWidgets.QLabel(f"当前选择的分类为：[root]")
        vlayout.addWidget(label)
        dialog.label = label
        self.moveDialog = dialog

        tree = LineTreeWidget(self.lineLib,detail=False)
        tree.setData()
        # 只有Line->Item存在映射，但Line部分被跳过了，所以对lineLib应该没影响
        self.subTree = tree
        vlayout.addWidget(tree)
        btnRoot = QtWidgets.QPushButton('选择根目录')
        btnRoot.clicked.connect(self._move_select_root)
        vlayout.addWidget(btnRoot)
        tree.currentItemChanged.connect(lambda x:self._move_target_changed(x,dialog))

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton('确定')
        hlayout.addWidget(btnOk)
        btnCancel = QtWidgets.QPushButton('取消')
        hlayout.addWidget(btnCancel)
        btnOk.clicked.connect(lambda:self._move_ok(items,dialog))
        btnCancel.clicked.connect(dialog.close)
        vlayout.addLayout(hlayout)
        dialog.setLayout(vlayout)

        dialog.exec_()

    def _move_select_root(self):
        self.subTree.setCurrentItem(None)

    def _move_target_changed(self,item,dialog):
        dialog.label.setText(f"当前选择的分类为：[{item.text(0) if item is not None else 'root'}]")

    def _move_ok(self,items:List[QtWidgets.QTreeWidgetItem],dialog):
        """
        items不会有None
        """
        targetItem0 = self.subTree.currentItem()
        if targetItem0 is None:
            target = self.lineLib
        else:
            target:Category = targetItem0.data(0,Qt.UserRole)
        del targetItem0
        while items:
            item = items.pop(0)
            data = item.data(0,Qt.UserRole)
            # 数据域
            target.moveDrops(data)
            # 显示域。从以前的位置删除。
            parent = item.parent()
            self.updateParentItemCount(item, -1)
            if isinstance(parent,QtWidgets.QTreeWidgetItem):
                parent.removeChild(item)
            else:
                self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            # 添加到新位置
            if target is self.lineLib:
                self.addItem(data,self)
            else:
                targetParent = self.itemByName(target.name)
                if targetParent is item:
                    QtWidgets.QMessageBox.warning(self,'错误','不能将自己移动到自己下面！')
                self.addItem(data,targetParent)
            for it in items[1:]:
                if it.parent() is item:
                    items.remove(it)
        dialog.close()
        self.setData()


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
        self.updateParentItemCount(item, -1)

    # slots
    def _show_item(self):
        self.ShowLine.emit(self.currentLine())

    def del_line(self,*,force=False):
        line = self.currentLine()
        item:QtWidgets.QTreeWidgetItem = self.currentItem()
        if item is None or not force and not self.question(f'是否确认删除线路[{line.name}]？'):
            return
        self.lineLib.delLine(line)
        self._deleteItem(item)

    def del_item(self):
        """
        由dialog调用，批量删除！
        """
        if not self.question(f"选中的{len(self.selectedItems())}个对象将被删除，其中分类的所有下属内容都将删除。是否确认？"):
            return
        if self.selectionMode() == self.MultiSelection:
            while self.selectedItems():
                item:QtWidgets.QTreeWidgetItem = self.selectedItems()[0]
                if item.type()==0:
                    cat:Category = item.data(0,Qt.UserRole)
                    self.lineLib.delChildCategory(cat)
                    item.takeChildren()
                    self._deleteItem(item)
                else:
                    line:Line = item.data(0,Qt.UserRole)
                    self.lineLib.delLine(line)
                    self._deleteItem(item)
        else:
            item = self.currentItem()
            if item is None:
                return
            elif item.type() == 0:
                cat: Category = item.data(0, Qt.UserRole)
                self.lineLib.delChildCategory(cat)
                item.takeChildren()
                self._deleteItem(item)
            else:
                line: Line = item.data(0, Qt.UserRole)
                self.lineLib.delLine(line)
                self._deleteItem(item)


    def _show_ruler(self):
        line = self.currentLine()
        if line is not None:
            self.showRuler(line)

    def _show_forbid(self):
        line = self.currentLine()
        if line is not None:
            self.showForbid(line)

    def _move_line(self):
        self.moveSomeItems([self.currentItem(),])

    def _expand_current(self):
        self.currentItem().setExpanded(True)

    def _collapse_current(self):
        self.currentItem().setExpanded(False)

    def _move_category(self):
        self.moveSomeItems([self.currentItem(),])

    def del_category(self):
        cat = self.currentCategory()
        item = self.currentItem()
        if cat is None or not isinstance(item,QtWidgets.QTreeWidgetItem):
            return
        if not self.question(f'删除分类[{cat.name}]及其下所有分类和线路，是否确认？'):
            return
        self.lineLib.delChildCategory(cat)
        self._deleteItem(item)

    def _item_changed(self,item:QtWidgets.QTreeWidgetItem,pre:QtWidgets.QTreeWidgetItem):
        """
        逻辑移动到上一层去
        """
        # if not isinstance(item.data(0,Qt.UserRole),Line):
        #     return
        # self.ShowLine.emit(item.data(0,Qt.UserRole))

    def new_category(self):
        item = self.currentItem()
        if isinstance(item,QtWidgets.QTreeWidgetItem):
            self.newCategory(item)

    def new_parallel_category(self):
        item = self.currentItem()
        if isinstance(item,QtWidgets.QTreeWidgetItem):
            self.newParallelCategory(item)
        else:
            QtWidgets.QMessageBox.warning(self,'提示','请先选中一线路或分类，再执行此操作！')

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
        线名修改，需要修改映射关系。
        """
        if self.lineLib.nameExisted(newName,line):
            QtWidgets.QMessageBox.warning(self,'警告','线名冲突！请重新修改一个不与其他类名、线名重合的线名。'
                                            '如果忽略此警告，可能导致不可预料的结果。')
            return
        cat = line.getParent()
        if cat is None:
            return
        try:
            del cat[oldName]
        except KeyError:
            print("LineNameChanged::oldName not existed",oldName,newName)
        cat[newName]=line

    showTip = True
    def batch_changed(self,batch:bool):
        if batch:
            self.setSelectionMode(self.MultiSelection)
            if LineTreeWidget.showTip:
                QtWidgets.QMessageBox.information(self,'提示',
                                                  '批量模式下，右键菜单只对最后一个选中的对象有效。\n'
                                                  '此消息在程序每次运行中显示一次。')
                LineTreeWidget.showTip=False
        else:
            self.setSelectionMode(self.SingleSelection)


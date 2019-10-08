"""
2019.10.07新增，重新设计的lineDB界面。
注意，线名不可重复。
"""
from .lineLib import Line,LineLib
from ..lineWidget import LineWidget
from .lineTreeWidget import LineTreeWidget
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt

class LineLibDialog(QtWidgets.QDialog):
    def __init__(self,filename='linesNew.json',parent=None):
        super(LineLibDialog, self).__init__(parent)
        self.filename=filename
        self.lineLib = LineLib(filename)
        try:
            self.lineLib.loadLib(filename)
        except:
            QtWidgets.QMessageBox.warning(self,"警告",f"无法解析数据文件{filename}！"
                                                    f"数据为空，可自行构建。")
        self.initUI()
        self.setData()

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
        btnChangeFile.clicked.connect(self._change_filename)

        btnDefaultFile = QtWidgets.QPushButton('设为默认文件')
        hlayout.addWidget(btnDefaultFile)
        btnDefaultFile.clicked.connect(self._set_default_filename)

        hlayout = QtWidgets.QHBoxLayout()
        vlayout.addLayout(hlayout)

        treeWidget = LineTreeWidget(self.lineLib)
        treeWidget.ShowLine.connect(self._show_line)
        hlayout.addWidget(treeWidget)
        self.treeWidget = treeWidget

        cvlayout = QtWidgets.QVBoxLayout()
        hlayout.addLayout(cvlayout)
        buttons = {
            "添加线路":self._new_line,
            "添加子类":self._new_line,
            "添加平行类":self.treeWidget.new_parallel_category,
            "删除选定":self._del_element,
            "移动线路":self._move_line,
            "标尺":self._edit_ruler,
            "天窗":self._edit_forbid,
            "导入文件":self._import_line,
            "合并数据":self._merge_line,
            "保存":self._save_lib,
        }
        for txt,func in buttons.items():
            btn = QtWidgets.QPushButton(txt)
            cvlayout.addWidget(btn)
            btn.clicked.connect(func)

        lineWidget = LineWidget(self.lineLib.firstLine())
        lineWidget.initWidget()
        # lineWidget.setData()  # !!setData不可以重复调用
        self.lineWidget = lineWidget
        hlayout.addWidget(lineWidget)

        lineWidget.lineNameChanged.connect(self.treeWidget.line_name_changed)
        lineWidget.lineChangedApplied.connect(self._line_applied)

    def setData(self):
        """

        """
        self.treeWidget.setData()

    # slots
    def _search_station(self):
        pass

    def _search_line(self):
        pass

    def _change_filename(self):
        filename,ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                         filter='pyETRC数据库文件(*.json)\n所有文件(*.*)')
        if not ok:
            return
        self.filename = filename
        self.editFile.setText(filename)

    def _set_default_filename(self):
        pass

    def _new_line(self):
        item = self.treeWidget.currentItem()
        if not isinstance(item,QtWidgets.QTreeWidgetItem):
            return
        if item.type()==0:
            self.treeWidget.newLine(item)
            return
        parent = item.parent()
        if isinstance(parent,QtWidgets.QTreeWidgetItem):
            self.treeWidget.newLine(parent)
        else:
            self.treeWidget.newRootLine()

    def _new_category(self):
        item = self.treeWidget.currentItem()
        if not isinstance(item, QtWidgets.QTreeWidgetItem):
            return
        if item.type() == 0:
            self.treeWidget.newCategory(item)
            return
        parent = item.parent()
        if isinstance(parent, QtWidgets.QTreeWidgetItem):
            self.treeWidget.newCategory(parent)
        else:
            self.treeWidget.newParallelCategory(item)

    def _del_element(self):
        self.treeWidget.del_item()

    def _move_line(self):
        pass

    def _edit_ruler(self):
        pass

    def _edit_forbid(self):
        pass

    def _import_line(self):
        pass

    def _merge_line(self):
        pass

    def _save_lib(self):
        self.lineLib.saveLib(self.filename)

    def _show_line(self,line:Line):
        self.lineWidget.setLine(line)

    def _line_applied(self):
        line = self.lineWidget.line
        self.treeWidget.updateLineRow(line)





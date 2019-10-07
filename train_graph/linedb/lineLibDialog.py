"""
2019.10.07新增，重新设计的lineDB界面。
注意，线名不可重复。
"""
from .lineLib import Line,LineLib
from ..lineWidget import LineWidget
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
        self.resize(1100,700)

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

        treeWidget = QtWidgets.QTreeWidget()
        hlayout.addWidget(treeWidget)
        self.treeWidget = treeWidget

        cvlayout = QtWidgets.QVBoxLayout()
        hlayout.addLayout(cvlayout)
        buttons = {
            "添加线路":self._add_line,
            "添加类别":self._add_category,
            "删除线路":self._del_line,
            "删除类别":self._del_category,
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
        lineWidget.setData()
        self.lineWidget = lineWidget
        hlayout.addWidget(lineWidget)

    def setData(self):
        """
        sample
        """
        treeWidget = self.treeWidget
        item0 = QtWidgets.QTreeWidgetItem(treeWidget)
        item0.setText(0,"成局")
        item1 = QtWidgets.QTreeWidgetItem(item0,("达成线",))
        item2 = QtWidgets.QTreeWidgetItem(item0,("宁蓉线成局段",))
        item0 = QtWidgets.QTreeWidgetItem(treeWidget)
        item0.setText(0, "上局")
        item1 = QtWidgets.QTreeWidgetItem(item0, ("京沪线上局段",))
        item2 = QtWidgets.QTreeWidgetItem(item0, ("宁芜线","12"))


    # slots
    def _search_station(self):
        pass

    def _search_line(self):
        pass

    def _change_filename(self):
        pass

    def _set_default_filename(self):
        pass

    def _add_line(self):
        print("addLine")

    def _add_category(self):
        print("addCategory")

    def _del_line(self):
        pass

    def _del_category(self):
        pass

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
        pass



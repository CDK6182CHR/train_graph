"""
2019.02.05抽离typeWidget
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from .data.graph import Graph
from .data.train import Train


class TypeWidget(QtWidgets.QWidget):
    TypeShowChanged = QtCore.pyqtSignal()
    ItemWiseDirShowChanged = QtCore.pyqtSignal(bool, bool)  # down, show

    def __init__(self, graph: Graph, parent=None):
        super(TypeWidget, self).__init__(parent)
        self.graph = graph
        self.initWidget()

    def initWidget(self):
        vlayout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()
        btnShowDown = QtWidgets.QPushButton("显示下行")
        btnShowDown.clicked.connect(lambda: self._set_dir_show(True, True))
        btnShowUp = QtWidgets.QPushButton("显示上行")
        btnShowUp.clicked.connect(lambda: self._set_dir_show(False, True))
        hlayout.addWidget(btnShowDown)
        hlayout.addWidget(btnShowUp)
        vlayout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnNoDown = QtWidgets.QPushButton("隐藏下行")
        btnNoDown.clicked.connect(lambda: self._set_dir_show(True, False))
        btnNoUp = QtWidgets.QPushButton("隐藏上行")
        btnNoUp.clicked.connect(lambda: self._set_dir_show(False, False))
        hlayout.addWidget(btnNoDown)
        hlayout.addWidget(btnNoUp)
        vlayout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnPas = QtWidgets.QPushButton('客车类型')
        btnPas.clicked.connect(self._select_passenger)
        hlayout.addWidget(btnPas)
        btnRev = QtWidgets.QPushButton('反选')
        btnRev.clicked.connect(self._reverse_select)
        hlayout.addWidget(btnRev)
        vlayout.addLayout(hlayout)

        check = QtWidgets.QCheckBox('运行线级别行别显示控制')
        check.setToolTip('如果启用，则对每一段运行线判断是否符合显示条件，可能导致运行线不完整；'
                         '否则仅根据入图方向判定是否显示。\n'
                         '如果使用此功能后，想要显示完整运行线，请用[刷新]或[重新铺画运行图]功能。')
        self.checkEnableItemWise = check
        vlayout.addWidget(check)

        listWidget = QtWidgets.QListWidget()
        self.listWidget = listWidget
        listWidget.setSelectionMode(listWidget.MultiSelection)

        self._setTypeList()

        vlayout.addWidget(listWidget)

        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("还原")

        btnOk.clicked.connect(self._apply_type_show)
        btnCancel.clicked.connect(self._setTypeList)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)

    def setData(self):
        self._setTypeList()

    def _setTypeList(self):
        """
        影响不大，暂时保留
        """
        listWidget = self.listWidget
        listWidget.clear()
        for type in self.graph.typeList:
            item = QtWidgets.QListWidgetItem(type)
            listWidget.addItem(item)
            if type not in self.graph.UIConfigData()["not_show_types"]:
                item.setSelected(True)

    # slots
    def _set_dir_show(self, down, show):
        itemWise = self.checkEnableItemWise.isChecked()
        self.graph.setDirShow(down, show, itemWise)
        if itemWise:
            self.ItemWiseDirShowChanged.emit(down,show)
        else:
            self.TypeShowChanged.emit()

    def _select_passenger(self):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if self.graph.typePassenger(item.text(),default=Train.PassengerFalse):
                item.setSelected(True)
            else:
                item.setSelected(False)

    def _reverse_select(self):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            item.setSelected(not item.isSelected())

    def _apply_type_show(self):
        listWidget = self.listWidget
        not_show = []
        for i in range(listWidget.count()):
            item: QtWidgets.QListWidgetItem = listWidget.item(i)
            if not item.isSelected():
                not_show.append(item.text())

        self.graph.setNotShowTypes(not_show)
        self.TypeShowChanged.emit()

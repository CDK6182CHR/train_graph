"""
2019.02.05抽离typeWidget
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from .data.graph import Graph
from .data.train import Train


class TypeWidget(QtWidgets.QWidget):
    TypeShowChanged = QtCore.pyqtSignal()

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
        self.graph.setDirShow(down, show)
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

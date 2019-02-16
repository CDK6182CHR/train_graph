"""
将修改站名的对话框独立成单独的对象
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .graph import Graph

class ChangeStationDialog(QtWidgets.QDialog):
    OkClicked = QtCore.pyqtSignal()
    showStatus = QtCore.pyqtSignal(str)
    def __init__(self,graph:Graph,parent=None):
        super().__init__(parent)
        self.graph = graph
        self.initUI()

    def initUI(self):
        self.setWindowTitle("站名修改")
        flayout = QtWidgets.QFormLayout()

        label = QtWidgets.QLabel("修改本线某一站名，同时调整所有车次的该站站名，重新铺画运行图。")
        label.setWordWrap(True)
        flayout.addRow(label)

        comboBefore = QtWidgets.QComboBox()
        comboBefore.setEditable(True)
        for name in self.graph.stations():
            comboBefore.addItem(name)
        flayout.addRow("原站名", comboBefore)
        self.comboBefore = comboBefore

        editNew = QtWidgets.QLineEdit()
        self.editNew = editNew
        flayout.addRow("新站名", editNew)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("取消")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        btnOk.clicked.connect(self._change_station_name_ok)
        btnCancel.clicked.connect(self.close)
        flayout.addRow(hlayout)

        self.setLayout(flayout)

    def _change_station_name_ok(self):
        """
        逻辑说明：不允许将已经存在的站改为另一个存在的站，防止冲突。允许修改不存在于线路表的站名。
        """
        comboBefore = self.comboBefore
        editNew = self.editNew
        old = comboBefore.currentText()
        new = editNew.text()

        old_dict = self.graph.stationByDict(old)
        new_dict = self.graph.stationByDict(new)

        if old_dict is not None and new_dict is not None:
            self._derr("错误：不能将一个本线上的站名修改为另一个本线上的站名。")
            return
        elif not old or not new:
            self._derr("错误：站名不能为空！")
            return

        self.graph.resetStationName(old,new)
        self.OkClicked.emit()
        self.close()

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)
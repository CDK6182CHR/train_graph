"""
车次管理界面。
聚合车次编辑，当前车次编辑和交路编辑三个部分。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from ..data import *
from ..trainWidget import TrainWidget
from ..currentWidget import CurrentWidget
from ..circuitWidget import CircuitWidget
from ..correctionWidget import CorrectionWidget
from datetime import datetime


class TrainManager(QtWidgets.QWidget):
    def __init__(self,graphdb:Graph,parent=None):
        super(TrainManager, self).__init__(parent)
        self.graphdb = graphdb

        self.trainWidget = TrainWidget(self.graphdb)
        self.currentWidget = CurrentWidget(self.graphdb)
        self.circuitWidget = CircuitWidget(self.graphdb)

        self.initUI()

    def initUI(self):
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.trainWidget)
        hlayout.addWidget(self.currentWidget)
        hlayout.addWidget(self.circuitWidget)
        self.setLayout(hlayout)

        # train
        trainWidget = self.trainWidget
        trainWidget.search_train.connect(self._search_train)
        trainWidget.current_train_changed.connect(self.currentWidget.setData)
        trainWidget.addNewTrain.connect(self._add_train_from_list)
        trainWidget.showStatus.connect(self.statusOut)
        # current
        widget = self.currentWidget
        widget.btnEvent.setEnabled(False)
        widget.btnLoad.setEnabled(False)
        widget.correctCurrentTrainTable.connect(self._correction_timetable)
        widget.showStatus.connect(self.statusOut)
        widget.currentTrainApplied.connect(self._current_applied)
        widget.currentTrainDeleted.connect(self._del_train_from_current)
        widget.editCurrentTrainCircuit.connect(self.circuitWidget.editCircuit)
        widget.addCircuitFromCurrent.connect(self.circuitWidget.add_circuit_from_current)
        self.circuitWidget.dialog.CircuitChangeApplied.connect(lambda x: widget.setData(widget.train))
        # 从当前车次列表添加交路

    def setData(self):
        self.trainWidget.setData()
        self.currentWidget.setData()
        self.circuitWidget.setData()

    def openFile(self, filename:str):
        """
        无需确认。
        """
        try:
            self.graphdb.clearAll()
            self.graphdb.loadGraph(filename)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','不能识别文件:\n'+str(e))
            return
        self.setData()

    def _derr(self, note: str):
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

    def question(self, note: str, default=True):
        flag = QtWidgets.QMessageBox.question(self, self.title, note,
                                              QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if flag == QtWidgets.QMessageBox.Yes:
            return True
        elif flag == QtWidgets.QMessageBox.No:
            return False
        else:
            return default

    def statusOut(self, note: str, seconds: int = 0):
        pass
        # self.statusBar().showMessage(f"{datetime.now().strftime('%H:%M:%S')} {note}", seconds)

    # slots
    def _search_train(self, checi: str):
        if not checi:
            return
        train: Train = self.graphdb.trainFromCheci(checi)
        if train is None:
            self._derr("无此车次：{}".format(checi))
            return
        self.trainWidget.setCurrentTrain(train)

    def _add_train_from_list(self):
        self.currentWidget.setData()
        self.currentWidget.setFocus(Qt.TabFocusReason)

    def _correction_timetable(self, train=None):
        if not isinstance(train, Train):
            train = self.currentTrain()
        if train is None:
            self._derr('当前车次时刻表重排：当前没有选中车次！')
            return
        dialog = CorrectionWidget(train, self.graphdb, self)
        dialog.correctionOK.connect(self.currentWidget.setData)
        dialog.exec_()

    def _current_applied(self, train: Train):
        """
        2019.06.30新增。将currentWidget中与main有关的全部移到这里。
        """
        if train.trainType() not in self.graphdb.typeList:
            self.graphdb.typeList.append(train.trainType())

        if not self.graphdb.trainExisted(train):
            self.graphdb.addTrain(train)
            self.trainWidget.addTrain(train)
        else:
            self.trainWidget.updateRowByTrain(train)
        self.statusOut("车次信息更新完毕")

    def _del_train_from_current(self, train: Train):
        isOld = self.graphdb.trainExisted(train)

        if isOld:
            # 旧车次，清除表格中的信息
            self.trainWidget.delTrain(train)
        self.graphdb.delTrain(train)

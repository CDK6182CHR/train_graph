"""
2019.06.07新增。
车次信息面板，由ctrl+Q（当前车次信息）功能独立出来。保留ctrl+Q功能的原始部分，扩展为停靠面板。
增加常用功能的链接，设计为常驻的停靠面板之一。快捷键仍为ctrl+Q。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .train import Train
from .graph import Graph
from .pyETRCExceptions import *

class TrainInfoWidget(QtWidgets.QWidget):
    def __init__(self,graph:Graph,parent=None):
        super(TrainInfoWidget, self).__init__(parent)
        self.graph = graph # type:Graph
        self.train = Train(self.graph) # type:Train

        self.fullCheciEdit = None # type:QtWidgets.QLineEdit
        self.trainTypeEdit = None # type:QtWidgets.QLineEdit
        self.inDownEdit = ...  # type:QtWidgets.QLineEdit
        self.outDownEdit = ...  # type:QtWidgets.QLineEdit
        self.localFirstEdit = ...  # type:QtWidgets.QLineEdit
        self.localLastEdit = ... # type:QtWidgets.QLineEdit
        self.localCountEdit = ... # type:QtWidgets.QLineEdit
        self.localMileEdit = ... # type:QtWidgets.QLineEdit
        self.localTimeEdit = ... # type:QtWidgets.QLineEdit
        self.localTotalSpeedEdit = ... # type:QtWidgets.QLineEdit
        self.localRunTimeEdit = ... # type:QtWidgets.QLineEdit
        self.localStopTimeEdit = ... # type:QtWidgets.QLineEdit
        self.localRunSpeedEdit = ... # type:QtWidgets.QLineEdit
        self.circuitNameEdit = ... # type:QtWidgets.QLineEdit
        self.directionCheciEdit = ... # type:QtWidgets.QLineEdit
        self.startEndEdit = ... # type:QtWidgets.QLineEdit
        self.initUI()

    def initUI(self):
        """

        """
        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()
        self.flayout = flayout  # type:QtWidgets.QFormLayout

        self._addFormRow('车次','fullCheciEdit')
        self._addFormRow('分方向车次','directionCheciEdit')
        self._addFormRow('始发终到','startEndEdit')

        self._addFormRow('列车种类','trainTypeEdit')
        self._addFormRow('本线入图方向','inDownEdit')
        self._addFormRow('本线出图方向','outDownEdit')
        self._addFormRow('本线入图点','localFirstEdit')
        self._addFormRow('本线出图点','localLastEdit')
        self._addFormRow('本线图定站点数','localCountEdit')
        self._addFormRow('本线里程','localMileEdit')
        self._addFormRow('本线运行时间','localTimeEdit')
        self._addFormRow('本线旅行速度','localTotalSpeedEdit')
        self._addFormRow('本线纯运行时间','localRunTimeEdit')
        self._addFormRow('本线停站时间','localStopTimeEdit')
        self._addFormRow('本线技术速度', 'localRunSpeedEdit')
        self._addFormRow('所属交路名','circuitNameEdit')
        vlayout.addLayout(flayout)

        vlayout.addWidget(QtWidgets.QLabel('交路序列'))
        circuitOrderEdit = QtWidgets.QTextBrowser()
        self.circuitOrderEdit = circuitOrderEdit
        circuitOrderEdit.setMaximumHeight(120)
        vlayout.addWidget(circuitOrderEdit)

        vlayout.addWidget(QtWidgets.QLabel('交路说明'))
        circuitNoteEdit = QtWidgets.QTextBrowser()
        self.circuitNoteEdit = circuitNoteEdit
        circuitNoteEdit.setMaximumHeight(120)
        vlayout.addWidget(circuitNoteEdit)

        btnText = QtWidgets.QPushButton('导出文本信息')
        vlayout.addWidget(btnText)
        btnText.clicked.connect(self._out_text)

        self.setLayout(vlayout)

    def _lineEdit(self)->QtWidgets.QLineEdit:
        line = QtWidgets.QLineEdit()
        line.setFocusPolicy(Qt.NoFocus)
        return line

    def _addFormRow(self,labelText:str,objName:str):
        """
        向self.flayout中新增一行，以labelText为label域内容，field域是不可编辑的lineEdit，self.objName=lineEdit。
        """
        line = QtWidgets.QLineEdit()
        line.setFocusPolicy(Qt.NoFocus)
        self.flayout.addRow(labelText,line)
        setattr(self,objName,line)

    def setData(self,train:Train=None):
        """
        如果train是None，保留原始的数据不作处理。
        """
        if train is not None:
            self.train = train
        else:
            train = self.train
        self.fullCheciEdit.setText(train.fullCheci())
        self.directionCheciEdit.setText(f"{train.downCheci()}/{train.upCheci()}")
        self.startEndEdit.setText(f"{train.sfz}->{train.zdz}")
        self.trainTypeEdit.setText(train.trainType())
        self.inDownEdit.setText(train.firstDownStr())
        self.outDownEdit.setText(train.lastDownStr())
        self.localFirstEdit.setText(train.localFirst())
        self.localLastEdit.setText(train.localLast())
        self.localCountEdit.setText(str(train.localCount()))
        mile = train.localMile(self.graph,fullAsDefault=False)
        self.localMileEdit.setText(f"{mile:.1f}")
        running, stay = train.localRunStayTime(self.graph)
        time = running + stay
        self.localTimeEdit.setText(self._sec2str(time))
        self.localRunTimeEdit.setText(self._sec2str(running))
        self.localStopTimeEdit.setText(self._sec2str(stay))
        self.localTotalSpeedEdit.setText(self._calSpeedStr(mile,time))
        self.localRunSpeedEdit.setText(self._calSpeedStr(mile,time))

        circuit = self.train.carriageCircuit()
        if circuit is not None:
            self.circuitNameEdit.setText(circuit.name())
            self.circuitOrderEdit.setText(circuit.orderStr())
            self.circuitNoteEdit.setText(circuit.note())
        else:
            self.circuitNameEdit.setText('(无交路信息)')
            self.circuitNoteEdit.setText('')
            self.circuitOrderEdit.setText('')


    def _calSpeedStr(self,mile:float,sec:int)->str:
        try:
            speed = mile/sec*1000*3.6
            return f"{speed:.2f} km/h"
        except ZeroDivisionError:
            return "NA"

    def _sec2str(self,sec:int)->str:
        return f"{sec//3600:02d}:{sec%3600//60:02d}:{sec%60:02d}"

    # slots
    def _out_text(self):
        """
        输出为文本模式。从原mainGraphWidget中移植过来。
        """
        train: Train = self.train
        if train is None:
            self._derr("当前车次为空！")
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("车次信息文本")
        dialog.resize(400,400)
        layout = QtWidgets.QVBoxLayout()
        text = ""

        text += f"车次：{train.fullCheci()}\n"
        text += f"分方向车次：{train.downCheci()}/{train.upCheci()}\n"
        text += f"始发终到：{train.sfz}->{train.zdz}\n"
        text += f"列车种类：{train.trainType()}\n"
        text += f"本线运行入图方向：{train.firstDownStr()}\n"
        text += f"本线运行出图方向：{train.lastDownStr()}\n"
        text += f"本线入图点：{train.localFirst(self.graph)}\n"
        text += f"本线出图点：{train.localLast(self.graph)}\n"
        text += f"本线图定站点数：{train.localCount(self.graph)}\n"
        text += f"本线运行里程：{train.localMile(self.graph):.1f}\n"
        running, stay = train.localRunStayTime(self.graph)
        time = running + stay
        text += f"本线运行时间：{'%d:%02d:%02d'%(int(time/3600),int((time%3600)/60),int(time%60))}\n"
        try:
            speed = 1000 * train.localMile(self.graph) / time * 3.6
            speed_str = "%.2fkm/h" % (speed)
        except ZeroDivisionError:
            speed_str = 'NA'
        text += f"本线旅行速度：{speed_str}\n"
        text += f"本线纯运行时间：{'%d:%02d:%02d'%(int(running/3600),int((running%3600)/60),int(running%60))}\n"
        text += f"本线总停站时间：{'%d:%02d:%02d'%(int(stay/3600),int((stay%3600)/60),int(stay%60))}\n"
        try:
            running_speed = 1000 * train.localMile(self.graph) / running * 3.6
            running_speed_str = "%.2f" % running_speed
        except ZeroDivisionError:
            running_speed_str = 'NA'
        text += f"本线技术速度：{running_speed_str}km/h\n"
        circuit = train.carriageCircuit()
        if circuit is None:
            text += f"本次列车没有交路信息\n"
        else:
            text += f"交路名称：{circuit.name()}\n"
            text += f"套跑序列：{circuit.orderStr()}\n"
            text += f"交路备注：{circuit.note()}\n"

        textBrowser = QtWidgets.QTextBrowser()
        textBrowser.setText(text)

        layout.addWidget(textBrowser)

        btnClose = QtWidgets.QPushButton("关闭")
        btnClose.clicked.connect(dialog.close)
        layout.addWidget(btnClose)

        dialog.setLayout(layout)
        dialog.exec_()
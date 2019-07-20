"""
2019.07.19新增。
导入车次（ctrl+D）功能对话框。
"""
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from .graph import Graph,Train,Ruler,Circuit,CircuitNode
from .trainWidget import TrainWidget
from .trainTimetable import TrainTimetable
from .trainInfoWidget import TrainInfoWidget
from .pyETRCExceptions import *

class ImportTrainDialog(QtWidgets.QDialog):
    importTrainOk = QtCore.pyqtSignal()
    def __init__(self,graph:Graph,parent=None):
        super(ImportTrainDialog, self).__init__(parent)
        self.graph = graph
        self.anGraph = Graph()
        self.anGraph.line.copyData(self.graph.line)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('导入车次')
        self.resize(1200,800)
        hlayout = QtWidgets.QHBoxLayout()
        self.trainWidget = TrainWidget(self.anGraph,parent=self)
        hlayout.addWidget(self.trainWidget)

        actionTimetable = QtWidgets.QAction('时刻表(Alt+Y)',self.trainWidget.trainTable)
        actionTimetable.triggered.connect(self._show_timetable)
        actionTimetable.setShortcut('Alt+Y')
        self.trainWidget.trainTable.addAction(actionTimetable)

        actionInfo = QtWidgets.QAction('车次信息(Alt+Q)',self.trainWidget.trainTable)
        actionInfo.triggered.connect(self._show_info)
        actionInfo.setShortcut('Alt+Q')
        self.trainWidget.trainTable.addAction(actionInfo)
        self.trainWidget.trainTable.setContextMenuPolicy(Qt.ActionsContextMenu)

        vlayout = QtWidgets.QVBoxLayout()
        flayout = QtWidgets.QFormLayout()
        filenameEdit = QtWidgets.QLineEdit()
        self.filenameEdit = filenameEdit
        filenameEdit.setFocusPolicy(Qt.NoFocus)
        chlayout = QtWidgets.QHBoxLayout()
        chlayout.addWidget(filenameEdit)
        btnView = QtWidgets.QPushButton('浏览')
        chlayout.addWidget(btnView)
        btnView.clicked.connect(self._view_file)
        flayout.addRow('文件名',chlayout)

        group1 = QtWidgets.QButtonGroup(self)
        radioIgnore = QtWidgets.QRadioButton('忽略冲突车次')
        self.radioIgnore = radioIgnore
        radioIgnore.setChecked(True)
        group1.addButton(radioIgnore)
        radioCover = QtWidgets.QRadioButton('覆盖冲突车次')
        group1.addButton(radioCover)
        cvlayout = QtWidgets.QVBoxLayout()
        cvlayout.addWidget(radioIgnore)
        cvlayout.addWidget(radioCover)
        flayout.addRow('冲突车次',cvlayout)

        group2 = QtWidgets.QButtonGroup(self)
        radioOldCircuit = QtWidgets.QRadioButton('以原图交路为准')
        radioNewCircuit = QtWidgets.QRadioButton('以新图交路为准')
        self.radioOldCircuit = radioOldCircuit
        self.radioNewCircuit = radioNewCircuit
        radioOldCircuit.setChecked(True)
        radioNoCircuit = QtWidgets.QRadioButton('不导入任何交路')
        self.radioNoCircuit = radioNoCircuit
        group2.addButton(radioOldCircuit)
        group2.addButton(radioNewCircuit)
        group2.addButton(radioNoCircuit)
        cvlayout = QtWidgets.QVBoxLayout()
        cvlayout.addWidget(radioOldCircuit)
        cvlayout.addWidget(radioNewCircuit)
        cvlayout.addWidget(radioNoCircuit)
        flayout.addRow('冲突交路',cvlayout)

        vlayout.addLayout(flayout)

        label = QtWidgets.QLabel('先选择要导入的文件名。左侧车次表中显示红色的行是冲突的车次。删除不导入的车次，然后点击确定以完成导入。'
                                 '\n在对应行按Alt+Y显示车次时刻表，按Alt+Q显示车次信息。也可以按右键实现。\n'
                                 '当不选择“不导入任何交路”时，将导入所有导入的车次中涉及到的交路数据；如果交路名称与原来的重复则自动重命名。如果有车次既属于原图中的一个交路，又属于新导入的一个交路时，如果选择的是“以原图交路为准”，则将该车次划给原图的交路，而删除新导入交路中的这个车次；反之若选择的是“以新图交路为准”，则将该车次划给新图，而删除原图已存在交路中的这个车次。')
        label.setWordWrap(True)
        vlayout.addWidget(label)

        chlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton('确定(&O)')
        btnCancel = QtWidgets.QPushButton('取消(&C)')
        btnOk.clicked.connect(self._ok_clicked)
        btnCancel.clicked.connect(self.close)
        chlayout.addWidget(btnOk)
        chlayout.addWidget(btnCancel)
        vlayout.addLayout(chlayout)
        hlayout.addLayout(vlayout)

        hlayout.setStretchFactor(self.trainWidget,6)
        hlayout.setStretchFactor(vlayout,4)

        self.setLayout(hlayout)

    # slots
    def _view_file(self):
        filename, ok = QtWidgets.QFileDialog.getOpenFileName(self, "打开文件",
                                                             filter='pyETRC运行图文件(*.json)\nETRC运行图文件(*.trc)\n所有文件(*.*)')
        if not ok:
            return
        newGraph = Graph()
        try:
            newGraph.loadGraph(filename)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','运行图文件错误\n'+str(e))
            return
        self.filenameEdit.setText(filename)
        self.anGraph.clearTrains()
        self.anGraph.preAddTrainByGraph(newGraph)
        self.trainWidget.setData()
        for i,train in enumerate(self.anGraph.trains()):
            if self.graph.checiExisted(train.fullCheci()):
                for c in range(7):
                    try:
                        self.trainWidget.trainTable.item(i,c).setForeground(QtGui.QBrush(Qt.red))
                    except Exception as e:
                        pass

    def _show_timetable(self):
        row = self.trainWidget.trainTable.currentRow()
        train = self.trainWidget.trainByRow(row)
        if train is None:
            return
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f'车次时刻表*{train.fullCheci()}')
        dialog.resize(400,600)
        vlayout = QtWidgets.QVBoxLayout()
        widget = TrainTimetable(self.anGraph)
        widget.setData(train)
        vlayout.addWidget(widget)

        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(dialog.close)
        vlayout.addWidget(btnClose)

        dialog.setLayout(vlayout)
        dialog.exec_()

    def _show_info(self):
        row = self.trainWidget.trainTable.currentRow()
        train = self.trainWidget.trainByRow(row)
        if train is None:
            return
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f'车次信息*{train.fullCheci()}')
        dialog.resize(400, 600)
        vlayout = QtWidgets.QVBoxLayout()
        widget = TrainInfoWidget(self.anGraph)
        widget.setData(train)
        vlayout.addWidget(widget)

        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(dialog.close)
        vlayout.addWidget(btnClose)

        dialog.setLayout(vlayout)
        dialog.exec_()

    def _ok_clicked(self):
        """

        """
        cover = not self.radioIgnore.isChecked()
        # 删除新导入运行图中不牵连的交路（车次可能会被删除）
        circuits = []
        for circuit in self.anGraph.circuits():
            if circuit.anyValidTrains():
                circuits.append(circuit)
        self.anGraph._circuits = circuits

        # 导入车次。无论交路导入设置如何，都先把覆盖的车次的circuit指向原图中的circuit。
        new_cnt = 0
        for train in self.anGraph.trains():
            oldTrain = self.graph.trainFromCheci(train.fullCheci())
            if oldTrain is None:
                self.graph.addTrain(train)
                new_cnt+=1
            elif cover:
                circuit = oldTrain.carriageCircuit()
                if circuit is not None:
                    circuit.replaceTrain(oldTrain,train)
                train.setCarriageCircuit(circuit)
                self.graph.delTrain(oldTrain)
                self.graph.addTrain(train)

        # 导入交路。重新创建所有的交路对象。
        if not self.radioNoCircuit.isChecked():
            coverCircuit = self.radioNewCircuit.isChecked()
            for circuit in self.anGraph.circuits():
                newCircuit = Circuit(self.graph)
                newCircuit.coverBaseData(circuit)
                while self.graph.circuitNameExisted(newCircuit.name()):
                    newCircuit.setName(newCircuit.name()+'_导入')
                for checi in circuit.checiList():
                    train = self.graph.trainFromCheci(checi)
                    if train is None:
                        continue
                    oldCircuit = train.carriageCircuit()
                    if oldCircuit is None:
                        # 原来没有，放心添加
                        newCircuit.addTrain(train)
                    elif coverCircuit:
                        # 冲突，且以新图中交路为准，则删除老交路中的这个结点。
                        # 注意，train对象不一定是原来的，所以按照车次来删除。
                        oldCircuit.removeTrainByCheci(train)
                        newCircuit.addTrain(train)
                if newCircuit.anyValidTrains():
                    self.graph.addCircuit(newCircuit)
        self.anGraph.clearTrains()
        self.importTrainOk.emit()
        self.close()
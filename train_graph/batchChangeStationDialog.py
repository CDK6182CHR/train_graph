"""
批量修改站名对话框
"""

from PyQt5 import QtWidgets,QtCore,QtGui
from graph import Graph
import json

class BatchChangeStationDialog(QtWidgets.QDialog):
    showStatus = QtCore.pyqtSignal(str)
    changeApplied = QtCore.pyqtSignal()
    def __init__(self,graph,parent=None):
        super(BatchChangeStationDialog, self).__init__(parent)
        self.graph = graph
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        self.setWindowTitle('批量站名映射')
        label = QtWidgets.QLabel("设置以下映射规则。把车次时刻表中站名变为站::场解析形式的站名，线路信息表"
                                 "中站名变为纯站名（无场名）。选中的行将被执行。")
        label.setWordWrap(True)
        layout.addWidget(label)

        map_list = self._readStationMap()
        tableWidget = QtWidgets.QTableWidget()
        self.tableWidget = tableWidget
        tableWidget.setColumnCount(2)
        tableWidget.setColumnWidth(0, 160)
        tableWidget.setColumnWidth(1, 160)
        tableWidget.setHorizontalHeaderLabels(['原名', '映射名'])
        tableWidget.setSelectionBehavior(tableWidget.SelectRows)
        tableWidget.setRowCount(len(map_list))
        tableWidget.setEditTriggers(tableWidget.CurrentChanged)

        for row, st_dict in enumerate(map_list):
            tableWidget.setRowHeight(row, 30)

            item = QtWidgets.QTableWidgetItem(st_dict["origin"])
            tableWidget.setItem(row, 0, item)

            item = QtWidgets.QTableWidgetItem(st_dict["station_field"])
            tableWidget.setItem(row, 1, item)

            if self.graph.stationInLine(st_dict["origin"]):
                item.setSelected(True)

        layout.addWidget(tableWidget)

        hlayout = QtWidgets.QHBoxLayout()
        btnAdd = QtWidgets.QPushButton("添加")
        btnDel = QtWidgets.QPushButton("删除")
        btnSave = QtWidgets.QPushButton("保存")

        btnAdd.clicked.connect(lambda: tableWidget.insertRow(tableWidget.rowCount()))
        btnAdd.clicked.connect(lambda: tableWidget.setRowHeight(tableWidget.rowCount() - 1, 30))
        btnDel.clicked.connect(lambda: tableWidget.removeRow(tableWidget.currentRow()))
        btnSave.clicked.connect(self._save_station_map)

        btnAdd.setMinimumWidth(60)
        btnDel.setMinimumWidth(60)
        btnSave.setMinimumWidth(60)

        hlayout.addWidget(btnAdd)
        hlayout.addWidget(btnDel)
        hlayout.addWidget(btnSave)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnOk = QtWidgets.QPushButton("应用")
        btnClose = QtWidgets.QPushButton("关闭")
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnClose)

        btnOk.clicked.connect(self._apply_station_map)
        btnClose.clicked.connect(self.close)
        layout.addLayout(hlayout)

        self.setLayout(layout)

    def _readStationMap(self):
        try:
            fp = open('station_map.json',encoding='utf-8',errors='ignore')
            map_list = json.load(fp)
        except:
            self._dout("未找到映射数据库文件或格式错误！请检查station_map.json，或继续维护信息。")
            return []
        else:
            fp.close()
            return map_list

    def _save_station_map(self):
        map_list = []
        tableWidget = self.tableWidget
        for row in range(tableWidget.rowCount()):
            st_dict = {
                'origin':tableWidget.item(row,0).text(),
                'station_field':tableWidget.item(row,1).text()
            }
            map_list.append(st_dict)
        with open('station_map.json','w',encoding='utf-8',errors='ignore') as fp:
            json.dump(map_list,fp,ensure_ascii=False)
            self.showStatus.emit('保存站名映射信息成功')

    def _apply_station_map(self):
        tableWidget = self.tableWidget
        rows = []
        failed_rows = []
        failed_index = []
        for index in tableWidget.selectedIndexes():
            row = index.row()
            if row in rows or row in failed_index:
                continue

            item0 = tableWidget.item(row,0)
            item1 = tableWidget.item(row,1)
            old = item0.text() if item0 else ''
            new = item1.text() if item1 else ''

            if self.graph.stationInLine(old,strict=True) and self.graph.stationInLine(new,strict=True):
                failed_rows.append((old,new))
                failed_index.append(row)
                continue
            if not old or not new:
                failed_rows.append((old,new))
                failed_index.append(row)
                continue
            self.graph.resetStationName(old,new,auto_field=True)
            rows.append(row)
        text = f"成功执行{len(rows)}条映射。"
        if failed_rows:
            text += "\n以下映射未能执行，可能因为原站名、新站名都是已存在的站名或存在空格：\n"
            for row in failed_rows:
                old = row[0]
                new = row[1]
                text += f"{old}->{new}\n"
        self._dout(text)
        if rows:
            self.changeApplied.emit()

    def _derr(self, note: str):
        # print("_derr")
        QtWidgets.QMessageBox.warning(self, "错误", note)

    def _dout(self, note: str):
        QtWidgets.QMessageBox.information(self, "提示", note)

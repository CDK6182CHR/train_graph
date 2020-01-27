from PyQt5.QtWidgets import *
from .peCellWidget import PECellWidget,CellWidgetFactory


class PECelledTable(QTableWidget):
    def __init__(self,parent=None):
        super(PECelledTable, self).__init__(parent)

    def setCellWidget(self, p_int, p_int_1, QWidget):
        super(PECelledTable, self).setCellWidget(p_int,p_int_1,QWidget)
        if isinstance(QWidget,PECellWidget):
            QWidget.row = p_int
            QWidget.col = p_int_1
            QWidget.table = self
        else:
            print("[warning] PECelledTable: not PECellWidget ",self, QWidget)

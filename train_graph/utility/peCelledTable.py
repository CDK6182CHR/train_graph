from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtGui
from .peCellWidget import PECellWidget,CellWidgetFactory


class PECelledTable(QTableWidget):
    def __init__(self,parent=None):
        super(PECelledTable, self).__init__(parent)

    def setCellWidget(self, row, column, widget):
        super(PECelledTable, self).setCellWidget(row, column, widget)
        if isinstance(widget, PECellWidget):
            widget.row = row
            widget.col = column
            widget.index: QPersistentModelIndex = QPersistentModelIndex(
                self.model().index(row,column,QModelIndex()))
            widget.table = self
        else:
            print("[warning] PECelledTable: not PECellWidget ", self, widget)

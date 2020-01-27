from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
from typing import *

class PECellWidget:
    """
    只用来做类型检查
    """
    pass

class CellWidgetFactory:
    @staticmethod
    def new(meta,*args,**kwargs)->PECellWidget:
        """
        创建meta所示类型的实例。args, kwargs皆为实例化参数。
        """
        class A(meta,PECellWidget):
            def __init__(self,*args,**kwargs):
                super(A, self).__init__(*args,**kwargs)
                self.row = 0
                self.col = 0
                self.table = None

            def focusInEvent(self,event):
                if isinstance(self,QtWidgets.QWidget) \
                        and isinstance(self.table,QtWidgets.QTableWidget):
                    super(A, self).focusInEvent(event)
                    self.table.setCurrentCell(self.row,self.col)
                else:
                    print("Invalid call of focusInEvent",self.table)
        return A(*args,**kwargs)

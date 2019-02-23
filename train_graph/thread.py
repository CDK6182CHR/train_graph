"""
显示进度条的窗口
"""
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
import time
import cgitb
cgitb.enable(format='text')
class ThreadDialog(QtCore.QThread):
    eventsOK=QtCore.pyqtSignal(list)
    def __init__(self,parent,GraphicWidget):
        super().__init__()
        self.setParent(parent)
        #self.dialog=QtWidgets.QProgressDialog()
        #self.dialog.setRange(0,100)
        self.GraphicWidget=GraphicWidget

    def run(self):
        """
        self.dialog.show()
        value=self.dialog.value()
        while value <=90:
            time.sleep(0.5)
            value+=1
            self.dialog.setValue(value)
            QtCore.QCoreApplication.processEvents()
        """
        events = self.GraphicWidget.listTrainEvent()
        print('work thread ok')
        self.eventsOK.emit(events)

    def finish(self):
        self.dialog.setValue(100)

    def setValue(self, value):
        self.dialog.setValue(value)
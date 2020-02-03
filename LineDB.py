from PyQt5 import QtWidgets
from train_graph.linedb.lineLibWidget import LineLibWidget
import sys

app = QtWidgets.QApplication(sys.argv)
mainWindow = QtWidgets.QMainWindow()
vlayout = QtWidgets.QVBoxLayout()
mainWindow.setWindowTitle('pyETRC线路数据库维护系统')
dialog = LineLibWidget(fromPyetrc=False)
mainWindow.setCentralWidget(dialog)
mainWindow.resize(1300,800)
mainWindow.show()
app.exec_()

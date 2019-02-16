from train_graph.mainGraphWindow import mainGraphWindow
from PyQt5.QtWidgets import QApplication
import sys
import os
os.chdir('train_graph')

app = QApplication(sys.argv)
mainWindow = mainGraphWindow()
mainWindow.show()

app.exec_()
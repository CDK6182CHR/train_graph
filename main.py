from train_graph.mainGraphWindow import mainGraphWindow
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
mainWindow = mainGraphWindow()
mainWindow.show()

app.exec_()
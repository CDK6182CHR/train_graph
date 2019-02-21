from train_graph.mainGraphWindow import mainGraphWindow
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
try:
    f = sys.argv[1]
except IndexError:
    f = None
mainWindow = mainGraphWindow(f)
mainWindow.show()

app.exec_()
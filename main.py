from train_graph.MainGraphWindow import MainGraphWindow
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
try:
    f = sys.argv[1]
except IndexError:
    f = None
mainWindow = MainGraphWindow(f)
# mainWindow.showMaximized()

app.exec_()
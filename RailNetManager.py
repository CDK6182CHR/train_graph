from PyQt5.QtWidgets import *
import sys
from train_graph.railnet.mainNetWindow import MainNetWindow

app = QApplication(sys.argv)
w = MainNetWindow()
w.showMaximized()
app.exec_()
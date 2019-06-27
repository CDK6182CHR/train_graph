"""
2019.06.26新增，运行trainDB.
"""
from train_graph.trainDatabase import TrainDatabase
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
w = TrainDatabase()
w.showMaximized()
app.exec_()
from train_graph.mainGraphWindow import mainGraphWindow
import cProfile
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
import sys,pstats

def cmds(w: mainGraphWindow):
    for i in range(100):
        w.trainWidget.trainTable.setCurrentCell(i, 0)

def train_delete(w:mainGraphWindow):
    """
    2019.07.06。
    测试删除车次引发的窗口更新操作情况。
    """
    # w.trainWidget.trainTable.setCurrentCell(12,0)
    w.currentDockWidget.setVisible(False)
    w.interactiveTimetableDockWidget.setVisible(True)

    cProfile.run('cmds(w)',
                 filename='profile/4.pstat',
                 )

def test_stats():
    app = QtWidgets.QApplication(sys.argv)
    w = mainGraphWindow('source/京沪线上局段20190410.json')
    train_delete(w)

    p = pstats.Stats('profile/3.pstat')
    p.strip_dirs()
    p.sort_stats('tottime').print_stats()

    p = pstats.Stats('profile/4.pstat')
    p.strip_dirs()
    p.sort_stats('cumulative').print_stats()


if __name__ == '__main__':
    from train_graph.circuitDiagram import Graph,CircuitDiagram
    app = QtWidgets.QApplication(sys.argv)
    graph = Graph()
    graph.loadGraph('source/成贵客专线四川段F-交路图测试.json')
    circuit = graph._circuits[2]
    widget = CircuitDiagram(graph,circuit)
    widget.show()
    app.exec_()


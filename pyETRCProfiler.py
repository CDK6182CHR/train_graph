from train_graph.mainGraphWindow import mainGraphWindow
import cProfile
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
import sys,pstats

def cmds(w: mainGraphWindow):
    for i in range(100):
        w.trainWidget.trainTable.setCurrentCell(i, 0)

def test_change_current_train(w:mainGraphWindow):
    """
    2019.07.06。
    测试删除车次引发的窗口更新操作情况。
    """
    # w.trainWidget.trainTable.setCurrentCell(12,0)
    w.currentDockWidget.setVisible(True)
    w.interactiveTimetableDockWidget.setVisible(False)

    cProfile.run('cmds(w)',
                 filename='profile/13.pstat',
                 )

def test_stats():
    app = QtWidgets.QApplication(sys.argv)
    w = mainGraphWindow('source/京沪线上局段20190410.json')
    # train_delete(w)

    p = pstats.Stats('profile/3.pstat')
    p.strip_dirs()
    p.sort_stats('tottime').print_stats()

    p = pstats.Stats('profile/4.pstat')
    p.strip_dirs()
    p.sort_stats('cumulative').print_stats()

def test_interval_trains(w:mainGraphWindow):
    # w._interval_count()
    cProfile.run('w._interval_count()',filename='profile/7.pstat')

def test_ruler_widget_refresh(w:mainGraphWindow):
    # w.rulerWidget.setData()
    cProfile.run('w.rulerWidget.setData()',
                 filename='profile/8.pstat'
                 )

def test_event_list(w:mainGraphWindow):
    train = w.graph.trainFromCheci('K849')
    w.GraphWidget._line_selected(train.firstItem())
    cProfile.run('w.GraphWidget.listTrainEvent()',
                 filename='profile/9.pstat'
                 )

event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress,QtCore.QPoint(879, 407),Qt.LeftButton,
                              Qt.NoButton,Qt.NoModifier)
def test_select_line(w:mainGraphWindow):
    # w.GraphWidget.mousePressEvent(event)
    w.trainDockWidget.setVisible(True)
    cProfile.run('w.GraphWidget.mousePressEvent(event)',
                 filename='profile/10.pstat'
                 )

def test_refresh_docks(w:mainGraphWindow):
    w._refreshDockWidgets()
    cProfile.run('w._refreshDockWidgets()',
                 filename='profile/15.pstat'
                 )

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = mainGraphWindow('source/京广线广铁段20190105.json')
    test_refresh_docks(w)

    p = pstats.Stats('profile/15.pstat')
    p.strip_dirs()
    p.sort_stats('cumulative').print_stats()




# -*- coding: utf-8 -*-
# @Time    : 2019/1/25 13:15
# @Author  : llc
# @File    : widget_list.py

from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QWidget, QSizePolicy, QLabel, QHBoxLayout, QPushButton, QTabBar, QTabWidget, QGridLayout, \
    QFrame, QSpacerItem, QToolButton


class BaseWidget(QWidget):
    def __init__(self, *args):
        super(BaseWidget, self).__init__(*args)
        # self.setMouseTracking(True)


class CornerButton(QPushButton):
    def __init__(self, *args):
        super(CornerButton, self).__init__(*args)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setIconSize(QSize(10, 10))
        self.setFixedSize(10, 10)


# class TitleButton(QPushButton):
#     def __init__(self, *args):
#         super(TitleButton, self).__init__(*args)
#         # _font = QFont("Webdings")
#         # _font.setPointSize(12)
#         # self.setFont(_font)
#         self.setMinimumSize(45, 30)
#         self.setMouseTracking(True)


# class TitleWidget(QPushButton):
#     def __init__(self, *args):
#         super(TitleWidget, self).__init__(*args)
#         self.setMinimumSize(25, 30)
#         self.setMouseTracking(True)


class MenuWidget(QWidget):
    def __init__(self, *args):
        super(MenuWidget, self).__init__(*args)
        self.setMouseTracking(True)

    def _set_height(self, height):
        self.setFixedHeight(height)

    _height = pyqtProperty(int, fset=_set_height)


class TabBar(QTabBar):
    def __init__(self, *args):
        super(TabBar, self).__init__(*args)
        self.setMouseTracking(True)


# class TitleBar(QWidget):
#     """
#     顶上的标题栏。
#     """
#     def __init__(self, parent=None):
#         super(TitleBar, self).__init__(parent)
#         raise Exception("depressed!")
#
#         self.title = 'no title'
#
#         self._init_ui()
#         self.setMouseTracking(True)
#
#         font = QFont('Webdings')
#
#         # close
#         self.button_close = TitleButton('r')
#         self.button_close.setFont(font)
#         self.button_close.setObjectName('ButtonClose')
#         self._r_hl.insertWidget(0, self.button_close)
#         # max
#         self.button_max = TitleButton('1')
#         self.button_max.setFont(font)
#         self.button_max.setObjectName('ButtonMax')
#         self._r_hl.insertWidget(0, self.button_max)
#         # min
#         self.button_min = TitleButton('0')
#         self.button_min.setFont(font)
#         self.button_min.setObjectName('ButtonMin')
#         self._r_hl.insertWidget(0, self.button_min)
#
#     def _init_ui(self):
#         hl = QHBoxLayout(self)
#         hl.setContentsMargins(0, 0, 0, 0)
#         hl.setSpacing(0)
#         l_widget = BaseWidget()
#         self._l_hl = QHBoxLayout(l_widget)
#         self._l_hl.setContentsMargins(0, 0, 0, 0)
#         self._l_hl.setSpacing(0)
#         hl.addWidget(l_widget)
#         hl.setContentsMargins(0, 0, 0, 0)
#         self._label_title = QLabel(self.title)
#         self._label_title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
#         self._label_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
#         hl.addWidget(self._label_title)
#         r_widget = BaseWidget()
#         self._r_hl = QHBoxLayout(r_widget)
#         self._r_hl.setContentsMargins(0, 0, 0, 0)
#         self._r_hl.setSpacing(0)
#         hl.addWidget(r_widget)
#
#     def set_title(self, title:str):
#         self.title = title
#         self._label_title.setText(self.title)
#
#     def add_widget(self, icon:str, left=True):
#         widget = TitleWidget()
#         widget.setIcon(QIcon(icon))
#         if left:
#             self._l_hl.insertWidget(-1, widget)
#         else:
#             self._r_hl.insertWidget(0, widget)
#
#     def mouseDoubleClickEvent(self, QMouseEvent):
#         super(TitleBar, self).mouseDoubleClickEvent(QMouseEvent)
#         self.button_max.click()


class MenuBar(QTabWidget):
    def __init__(self, parent=None):
        super(MenuBar, self).__init__(parent)

        tabbar = TabBar(parent)
        self.setTabBar(tabbar)
        self._init_ui()
        self.setMinimumHeight(125)
        self.setMouseTracking(True)

    def _set_height(self, height):
        self.setFixedHeight(height)

    _height = pyqtProperty(int, fset=_set_height)

    def _init_ui(self):
        font = QFont('Webdings')

        self._drop = False
        self._corner = CornerButton('5')
        self._corner.setObjectName('BUttonCorner')
        self._corner.setFont(font)
        self.setCornerWidget(self._corner, Qt.BottomRightCorner)
        self._corner.clicked.connect(self._corner_clicked)
        self.currentChanged.connect(self._current_changed)

    def _corner_clicked(self):
        # self._ani = QPropertyAnimation(self, b'_height')
        # self._ani.setDuration(100)

        if self._drop:  # 当前是否展开的状况
            self._corner.setText('5')
            self._drop = False
            # self._ani.setStartValue(30)
            # self._ani.setEndValue(125)
            self._set_height(125)
        else:
            self._corner.setText('6')
            self._drop = True
            # self._ani.setStartValue(125)
            # self._ani.setEndValue(30)
            self._set_height(30)
        # self._ani.start()

    def _current_changed(self, index):
        pass
        # tab_text = self.tabText(index)
        # menu = self.findChild(MenuWidget, tab_text)
        # self._ani1 = QPropertyAnimation(menu, b'_height')
        # self._ani1.setDuration(500)
        # self._ani1.setStartValue(0)
        # self._ani1.setEndValue(95)
        # self._ani1.start()

    def add_menu(self, p_str)->MenuWidget:
        p_str = f"  {p_str}  "
        menu = MenuWidget()
        menu.setObjectName(p_str)
        self.addTab(menu, p_str)
        self._hl = QHBoxLayout(menu)
        self._hl.setObjectName(p_str)
        self._hl.setContentsMargins(0, 0, 0, 0)
        self._hl.setSpacing(0)
        hs = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._hl.addItem(hs)
        return menu

    def add_group(self, p_str, menu)->'GroupWidget':
        group = GroupWidget(p_str, menu)
        group.setObjectName('group')
        insert_index = len(menu.findChildren(GroupWidget, 'group')) - 1
        self._hl.insertWidget(insert_index, group)
        return group


class GroupWidget(QWidget):
    def __init__(self, p_str, parent=None):
        super(GroupWidget, self).__init__(parent)
        self._title = p_str
        self._init_ui()
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.setMouseTracking(True)

    def _init_ui(self):
        font = QFont('Wingdings')

        self._gl = QGridLayout(self)
        self._gl.setContentsMargins(3, 3, 3, 3)
        self._gl.setSpacing(1)
        label = QLabel(self._title)
        label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self._gl.addWidget(label, 1, 0, 1, 1)
        line = QFrame(self)
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Raised)
        self._gl.addWidget(line, 0, 2, 2, 1)
        self.corner = CornerButton('y')
        self.corner.setObjectName('BUttonCorner')
        self.corner.setFont(font)
        self._gl.addWidget(self.corner, 1, 1, 1, 1)

    def add_widget(self, widget):
        self._gl.addWidget(widget, 0, 0, 1, 2)


class PEToolButton(QToolButton):
    def __init__(self,parent=None):
        super(PEToolButton, self).__init__(parent)
        self.setStyleSheet("""
                    QToolButton{
                        border-style:solid;
                        background:white;
                    }
                    QToolButton:hover{
                        background:rgb(220,220,220);
                    }
                    QToolButton:pressed,QToolButton:checked{
                        background:rgb(180,180,180);
                    }
                """)

# -*- coding: utf-8 -*-
# @Time    : 2019/1/25 13:15
# @Author  : llc
# @File    : widget_list.py

from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QWidget, QSizePolicy, QLabel, QHBoxLayout, QPushButton, QTabBar, QTabWidget, QGridLayout, \
    QFrame, QSpacerItem, QToolButton, QAction


class BaseWidget(QWidget):
    def __init__(self, *args):
        super(BaseWidget, self).__init__(*args)
        # self.setMouseTracking(True)


class CornerButton(QPushButton):
    def __init__(self, *args):
        super(CornerButton, self).__init__(*args)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setIconSize(QSize(10, 10))
        self.setFixedSize(30, 20)


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


class MenuBar(QTabWidget):
    ExpandHeight = 125
    HiddenHeight = 30

    def __init__(self, parent=None):
        super(MenuBar, self).__init__(parent)

        tabbar = TabBar(parent)
        self.setTabBar(tabbar)
        self._init_ui()
        self.setMinimumHeight(125)
        self.setMouseTracking(True)
        self.tabBarClicked.connect(self._tab_clicked)

    def _set_height(self, height):
        self.setFixedHeight(height)

    _height = pyqtProperty(int, fset=_set_height)

    def _init_ui(self):
        font = QFont('Webdings')

        self._drop = False
        self._corner = CornerButton('5')
        self._corner.setObjectName('BUttonCorner')
        self._corner.setFont(font)
        self.setCornerWidget(self._corner, Qt.TopRightCorner)
        self._corner.clicked.connect(self._corner_clicked)
        self.currentChanged.connect(self._current_changed)

    def expand(self):
        self._corner.setText('5')
        self._drop = False
        self._set_height(self.ExpandHeight)

    def shrink(self):
        self._corner.setText('6')
        self._drop = True
        self._set_height(self.HiddenHeight)

    def _corner_clicked(self):
        # self._ani = QPropertyAnimation(self, b'_height')
        # self._ani.setDuration(100)

        if self._drop:  # 当前是否展开的状况
            self.expand()
        else:
            self.shrink()
        # self._ani.start()

    def _tab_clicked(self):
        if self._drop:
            self.expand()

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

    def add_group(self, p_str, menu, *, use_corner=False)->'GroupWidget':
        group = GroupWidget(p_str, menu, useConer=use_corner)
        group.setObjectName('group')
        insert_index = len(menu.findChildren(GroupWidget, 'group')) - 1
        self._hl.insertWidget(insert_index, group)
        return group


class GroupWidget(QWidget):
    def __init__(self, p_str, parent=None, *, useConer=False):
        super(GroupWidget, self).__init__(parent)
        self._title = p_str
        self.useCorner = useConer
        self._init_ui()
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.setMouseTracking(True)

    LabelFont = QFont('SimSun',8)

    def _init_ui(self):
        font = QFont('Wingdings')

        self._gl = QGridLayout(self)  # type:QGridLayout
        self._gl.setContentsMargins(3, 3, 3, 3)
        self._gl.setSpacing(1)
        label = QLabel(self._title)
        label.setFont(self.LabelFont)
        label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        line = QFrame(self)
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Raised)
        line.setFixedWidth(10)
        self._gl.addWidget(line, 0, 2, 2, 1)
        if self.useCorner:
            self._gl.addWidget(label, 1, 0, 1, 1, Qt.AlignCenter)
            self.corner = CornerButton('')  # 原来是y
            self.corner.setFont(font)
            self._gl.addWidget(self.corner, 1, 1, 1, 1)
        else:
            self._gl.addWidget(label, 1, 0, 1, 2, Qt.AlignCenter)

    def add_widget(self, widget):
        self._gl.addWidget(widget, 0, 0, 1, 2)

    def addWidget(self, widget, row:int, column:int, rowSpan:int=1,columnSpan:int=2):
        """
        void	addWidget(QWidget *widget, int row, int column, Qt::Alignment alignment = Qt::Alignment())
void	addWidget(QWidget *widget, int fromRow, int fromColumn, int rowSpan, int columnSpan, Qt::Alignment alignment = Qt::Alignment())
        """
        self._gl.addWidget(widget,row,column,rowSpan,columnSpan)

    def add_layout(self,layout):
        self._gl.addLayout(layout,0,0,1,2)

    def set_corner_menu(self, menu):
        if self.useCorner:
            self.corner.setMenu(menu)


class PEToolButton(QToolButton):
    def __init__(self, text:str=None, icon:QIcon=None, action:QAction=None,
                 parent=None,*,large=False):
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
        if action:
            self.setDefaultAction(action)
        if text:
            self.setText(text)
        if icon:
            self.setIcon(icon)
        # self.setMinimumWidth(40)
        if large:
            size: QSize = QSize(40, 40)
            self.setIconSize(size)
            self.setFixedHeight(70)
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        else:
            self.setFixedHeight(30)
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)


class PEDockButton(PEToolButton):
    def __init__(self, showText:str, dockName:str, icon:QIcon, dock, parent=None,
                 *,large=True):
        super(PEDockButton, self).__init__(showText,icon,parent,large=large)
        self.dockName = dockName
        self.setCheckable(True)
        self.dock = dock
        self.clicked.connect(dock.setVisible)


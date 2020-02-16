# -*- coding: utf-8 -*-
# @Time    : 2019/4/12 10:20
# @Author  : llc
# @File    : frameless_window.py
"""
Depressed!
"""

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QEnterEvent
from PyQt5.QtWidgets import QMainWindow


class RibbonMainWindow(QMainWindow):
    def __init__(self):
        super(RibbonMainWindow, self).__init__()
        self.margin = 3  # 边界宽度
        self.__top_drag = False
        self.__bottom_drag = False
        self.__left_drag = False
        self.__right_drag = False
        self.__bottom_left_drag = False
        self.__bottom_right_drag = False
        self.__top_left_drag = False
        self.__top_right_drag = False
        self.__start_point = None
        self.setMouseTracking(True)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowFlags(
        #                     # Qt.Dialog |
        #                     # Qt.FramelessWindowHint |
        #                     Qt.WindowSystemMenuHint
        #                     # Qt.WindowMinMaxButtonsHint
        # )

    def mousePressEvent(self, event):
        self.__start_point = event.globalPos()
        self._pos = self.pos()
        self._width = self.width()
        self._height = self.height()
        if (event.button() == Qt.LeftButton) and (event.pos() in self._t_rect):
            # 上
            self.__top_drag = True
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._b_rect):
            # 下
            self.__bottom_drag = True
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._l_rect):
            # 左
            self.__left_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._r_rect):
            # 右
            self.__right_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._bl_rect):
            # 左下
            self.__bottom_left_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._br_rect):
            # 右下
            self.__bottom_right_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._tl_rect):
            # 左上
            self.__top_left_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._tr_rect):
            # 右上
            self.__top_right_drag = True
            event.accept()
        elif event.button() == Qt.LeftButton:
            # 移动
            event.accept()

    def mouseMoveEvent(self, event):
        if event.pos() in self._t_rect:
            # 上
            self.setCursor(Qt.SizeVerCursor)
        elif event.pos() in self._b_rect:
            # 下
            self.setCursor(Qt.SizeVerCursor)
        elif event.pos() in self._l_rect:
            # 左
            self.setCursor(Qt.SizeHorCursor)
        elif event.pos() in self._r_rect:
            # 右
            self.setCursor(Qt.SizeHorCursor)
        elif event.pos() in self._bl_rect:
            # 左下
            self.setCursor(Qt.SizeBDiagCursor)
        elif event.pos() in self._br_rect:
            # 右下
            self.setCursor(Qt.SizeFDiagCursor)
        elif event.pos() in self._tl_rect:
            # 左上
            self.setCursor(Qt.SizeFDiagCursor)
        elif event.pos() in self._tr_rect:
            # 右上
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        if not self.__start_point:
            return
        elif Qt.LeftButton and self.__top_drag:
            # 上
            diff_y = event.globalPos().y() - self.__start_point.y()
            if diff_y > 0 and self.height() == self.minimumHeight():
                return
            self.setGeometry(self.pos().x(), self._pos.y() + diff_y, self.width(), self._height - diff_y)
            event.accept()
        elif Qt.LeftButton and self.__bottom_drag:
            # 下
            self.resize(self.width(), event.pos().y())
            event.accept()
        elif Qt.LeftButton and self.__left_drag:
            # 左
            diff_x = event.globalPos().x() - self.__start_point.x()
            if diff_x > 0 and self.width() == self.minimumWidth():
                return
            self.setGeometry(self._pos.x() + diff_x, self.pos().y(), self._width - diff_x, self.height())
            event.accept()
        elif Qt.LeftButton and self.__right_drag:
            # 右
            self.resize(event.pos().x(), self.height())
            event.accept()
        elif Qt.LeftButton and self.__bottom_left_drag:
            # 左下
            diff_x = event.globalPos().x() - self.__start_point.x()
            diff_y = event.globalPos().y() - self.__start_point.y()
            if diff_x > 0 and self.width() == self.minimumWidth():
                return
            if diff_y < 0 and self.height() == self.minimumHeight():
                return
            self.setGeometry(self._pos.x() + diff_x, self.pos().y(), self._width - diff_x, self._height + diff_y)
            event.accept()
        elif Qt.LeftButton and self.__bottom_right_drag:
            # 右下
            self.resize(event.pos().x(), event.pos().y())
            event.accept()
        elif Qt.LeftButton and self.__top_left_drag:
            # 左上
            diff_x = event.globalPos().x() - self.__start_point.x()
            diff_y = event.globalPos().y() - self.__start_point.y()
            if diff_x > 0 and self.width() == self.minimumWidth():
                return
            if diff_y < 0 and self.height() == self.minimumHeight():
                return
            self.setGeometry(self._pos.x() + diff_x, self._pos.y() + diff_y, self._width - diff_x,
                             self._height - diff_y)
            event.accept()
        elif Qt.LeftButton and self.__top_right_drag:
            # 右上
            diff_x = event.globalPos().x() - self.__start_point.x()
            diff_y = event.globalPos().y() - self.__start_point.y()
            if diff_x > 0 and self.width() == self.minimumWidth():
                return
            if diff_y < 0 and self.height() == self.minimumHeight():
                return
            self.setGeometry(self.pos().x(), self._pos.y() + diff_y, self._width + diff_x,
                             self._height - diff_y)
            event.accept()
        elif event.buttons() == Qt.LeftButton and self.__start_point:
            # 移动
            diff_x = event.globalPos() - self.__start_point
            self.move(self._pos + diff_x)
            self.__get_rect()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.__top_drag = False
        self.__bottom_drag = False
        self.__left_drag = False
        self.__right_drag = False
        self.__bottom_left_drag = False
        self.__bottom_right_drag = False
        self.__top_left_drag = False
        self.__top_right_drag = False
        self.__start_point = None
        event.accept()

    def resizeEvent(self, event):
        super(RibbonMainWindow, self).resizeEvent(event)
        self.__get_rect()

    def __get_rect(self):
        width, height = self.width(), self.height()
        margin = self.margin * 2
        self._t_rect = [QPoint(x, y) for x in range(margin, width - margin) for y in range(0, margin)]
        self._b_rect = [QPoint(x, y) for x in range(margin, width - margin) for y in
                        range(height - margin, height)]
        self._l_rect = [QPoint(x, y) for x in range(0, margin) for y in range(margin, height - margin)]
        self._r_rect = [QPoint(x, y) for x in range(width - margin, width) for y in
                        range(margin, height - margin)]
        self._bl_rect = [QPoint(x, y) for x in range(0, margin) for y in range(height - margin, height)]
        self._br_rect = [QPoint(x, y) for x in range(width - margin, width) for y in
                         range(height - margin, height)]
        self._tl_rect = [QPoint(x, y) for x in range(0, margin) for y in range(0, margin)]
        self._tr_rect = [QPoint(x, y) for x in range(width - margin, width) for y in range(0, margin)]

    def leaveEvent(self, event):
        super(RibbonMainWindow, self).leaveEvent(event)
        self.setCursor(Qt.ArrowCursor)

    def eventFilter(self, obj, event):
        if not isinstance(obj, QMainWindow) and isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)

        return QMainWindow.eventFilter(self, obj, event)

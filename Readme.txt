************************
直接运行本项目源代码需要以下环境支持：
Python 3.6及以上；
PyQt5（本项目使用5.10版本开发，对其他版本兼容情况未知）
xlwt
xlrd
xpinyin

************************
本项目目前可直接运行的文件
mainGraphWindow.py （主程序文件）
lineDB.py （独立运行线路数据库维护功能）

************************
项目模块说明：
1. 命名为*Widget.py的模块都是某一部分子窗口，往往是停靠面板的类定义。
2. train, line, ruler, graph, forbid是本项目的数据类，用于保存运行图的数据。
3. mainGraphWindow.py是主程序；GraphicWidget.py是程序的核心绘图部分的实现。
4. 其他模块：utility.py是本项目中一些常用的小函数定义；rulerPaint.py是标尺排图向导的实现；thread.py是部分与界面分离的业务代码实现；checi3.py是车次处理的模块；trainItem是绘图部分列车对应运行线部分的封装；trainFilter.py是通用列车筛选器。
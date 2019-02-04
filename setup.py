from distutils.core import setup

# 定义发布的包文件的信息
setup(
name = "train_graph",  # 发布的包文件名称
version = "1.3.0",   # 发布的包的版本序号
description = "train_graph",  # 发布包的描述信息
author = "mxy",   # 发布包的作者信息
author_email = "mxy0268@outlook.com",  # 作者联系邮箱信息
py_modules = ['checi3','currentWidget','detectWidget',
              'direction','forbid','forbidWidget',
              'graph','GraphicWidget','intervalWidget',
              'line','lineDB','lineWidget','mainGraphWindow',
              'main_window','ReadRulerSkleton',
              'ruler','rulerPaint','rulerWidget',
              'stationvisualize','thread','train','trainFilter',
              'trainItem','trainWidget',
              'utility','__init__',], requires=['PyQt5']  # 发布的包中的模块文件列表
)

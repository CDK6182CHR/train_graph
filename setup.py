from distutils.core import setup
from setuptools import find_packages

# 定义发布的包文件的信息
setup(
name = "train_graph_tools",  # 发布的包文件名称
version = "2.3.3",   # 发布的包的版本序号
description = "train_graph_tools",  # 发布包的描述信息
author = "xep",   # 发布包的作者信息
author_email = "mxy0268@qq.com",  # 作者联系邮箱信息
#py_modules = ['checi3',
#              'connect2',
#              'direction',
#              'utility',
#              '__init__',],  # 发布的包中的模块文件列表
packages = find_packages(where='.',
                         include=('train_graph',
                                  'train_graph.linedb',
                                  'train_graph.data',
                                  'train_graph.circuitwidgets',
                                  )),  # 必填
      package_dir = {'':'.',
                     'linedb':'./train_graph',
                     'data':'./train_graph',
                     'circuitwidgets':'./train_graph',
                     },         # 必填
      requires = ['PyQt5','xlwt','xlrd','xpinyin']

)

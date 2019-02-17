from distutils.core import setup
from setuptools import find_packages

# 定义发布的包文件的信息
setup(
name = "train_graph_tools",  # 发布的包文件名称
version = "1.4.0-20190216",   # 发布的包的版本序号
description = "train_graph_tools",  # 发布包的描述信息
author = "mxy",   # 发布包的作者信息
author_email = "mxy0268@outlook.com",  # 作者联系邮箱信息
#py_modules = ['checi3',
#              'connect2',
#              'direction',
#              'utility',
#              '__init__',],  # 发布的包中的模块文件列表
packages = find_packages(where='.',
                         include=('train_graph',)),  # 必填
      package_dir = {'':'.'},         # 必填

)

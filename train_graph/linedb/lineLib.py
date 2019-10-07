"""
2019.10.07新增
线路数据库的模型。
不可接触Graph类。
本类对View域开放，是直接接口，继承category，是最外层的包装。
理论上要单实例运行。
主要增加了文件名等项目。
"""
import json
from ..line import Line
from .category import Category

class LineLib(Category):
    def __init__(self,filename=''):
        super(LineLib, self).__init__()
        self.filename=filename

    def getFilename(self)->str:
        return self.filename

    def setFilename(self,filename:str):
        self.filename=filename

    def loadLib(self,filename):
        """
        利用内置filename，读取json文件。
        """
        self.filename=filename
        with open(self.filename,encoding='utf-8',errors='ignore') as fp:
            data = json.load(fp)
            self.parse(data)

    def saveLib(self,filename=''):
        """
        暂定加上filename参数时为另存。
        """
        if filename:
            self.filename=filename
        with open(self.filename,'w',encoding='utf-8',errors='ignore') as fp:
            json.dump(self.outInfo(),fp,ensure_ascii=False)

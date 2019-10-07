"""
2019.10.07新增。
对应一“类”线路数据。数据结构为广义表，成员可以是Line或Category。
是Python基础dict的封装和扩展。
"""
from ..line import Line

class Category(dict):
    def __init__(self,name='',data=None):
        super(Category, self).__init__()
        self.name=name  # 按道理这个没用
        if data is not None:
            self.parse(data=data)

    @staticmethod
    def isLineDict(dct:dict):
        """
        判断是否是一条线路的数据。
        判断标准为，是否同时具有stations和name两个字段，且数据类型为list和str
        """
        return isinstance(dct.get('name',None),str) \
               and isinstance(dct.get('stations',None),list)

    def parse(self,data:dict):
        """
        解析数据。传入分类下的一套数据字典，解析。
        """
        for name,dct in data.items():
            if Category.isLineDict(dct):
                line=Line(origin=dct)
                self[name]=line
            else:
                cat=Category(name,dct)
                self[name]=cat

    def outInfo(self)->dict:
        """
        返回json数据，此过程递归到Line为止。
        """
        dct = {}
        for name,data in self.items():
            dct[name]=data.outInfo()
        return dct

    def searchLineName(self,name:str)->dict:
        result = {}
        for name,data in self.items():
            if isinstance(data,Line):
                if name in data.name:
                    result[name]=data
            elif isinstance(data,Category):
                result.update(data.searchLineName(name))
        return result

    def searchStation(self,station:str)->dict:
        result={}
        for name,data in self.items():
            if isinstance(data,Line):
                if data.stationExisted(name):
                    result[name]=data
            elif isinstance(data,Category):
                result.update(data.searchStation(station))
        return result

    def lineByNameStrict(self,name:str)->Line:
        """
        返回严格匹配的线名对应的Line对象。如果不存在，返回None。
        """
        for _,data in self.items():
            if isinstance(data,Line):
                if name==data.name:
                    return data
            elif isinstance(data,Category):
                rec=data.lineByNameStrict(name)
                if rec is not None:
                    return rec
        return None

    def firstLine(self)->Line:
        for name,data in self.items():
            if isinstance(data,Line):
                return data
            elif isinstance(data,Category):
                return data.firstLine()
        return Line()







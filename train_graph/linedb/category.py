"""
2019.10.07新增。
对应一“类”线路数据。数据结构为广义表，成员可以是Line或Category。
是Python基础dict的封装和扩展。
"""
from ..line import Line

class Category(dict):
    def __init__(self,name='',data=None,parent=None):
        super(Category, self).__init__()
        self.parent = parent
        self.name=name  # 按道理这个没用
        if data is not None:
            self.parse(data=data)

    def setName(self,name):
        oldName = self.name
        self.name = name
        if isinstance(self.parent,Category):
            del self.parent[oldName]
            self.parent[name]=self

    def setParent(self,parent):
        self.parent=parent

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
        把所有的Category放在最前面。
        """
        line_dct = {}
        for name,dct in data.items():
            if Category.isLineDict(dct):
                line=Line(origin=dct)
                line_dct[line.name]=line
                line.setParent(self)
            else:
                cat=Category(name,dct,parent=self)
                self[name]=cat
        self.update(line_dct)

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
        for _,data in self.items():
            if isinstance(data,Line):
                if name in data.name:
                    result[data.name]=data
            elif isinstance(data,Category):
                result.update(data.searchLineName(name))
        return result

    def searchStation(self,station:str)->dict:
        result={}
        for name,data in self.items():
            if isinstance(data,Line):
                if data.stationExisted(station):
                    result[name]=data
            elif isinstance(data,Category):
                result.update(data.searchStation(station))
        return result

    def nameExisted(self, name:str,ignore=None)->bool:
        """
        返回严格匹配的线名对应的Line或者Category对象是否存在。
        """
        for _,data in self.items():
            if isinstance(data,Line):
                if name==data.name and data is not ignore:
                    return True
            elif isinstance(data,Category):
                if name==data.name and data is not ignore:
                    return True
                if data.nameExisted(name,ignore):
                    return True
        return False

    def parentFromName(self,name:str):
        """
        返回name指向名称的父对象。
        """
        if self.get(name,None) is not None:
            return self
        for _,t in self.items():
            if isinstance(t,Category):
                return t.parentFromName(name)
        return None

    def firstLine(self)->Line:
        for name,data in self.items():
            if isinstance(data,Line):
                return data
            elif isinstance(data,Category):
                return data.firstLine()
        return Line()

    def delLine(self,line:Line)->bool:
        """
        保证只用删除一次即可。
        """
        for name,data in self.items():
            if isinstance(data,Category):
                if data.delLine(line):
                    return True
            elif isinstance(data,Line):
                if data is line:
                    del self[name]
                    return True
        return False

    def delChildCategory(self,cat)->bool:
        for name,data in self.copy().items():
            if isinstance(data,Category):
                if data is cat:
                    del self[name]
                    return True
                else:
                    self.delChildCategory(data)
        return False

    def addCategory(self,category):
        """
        按自动生成的名字添加新分类，并返回对象
        """
        category.parent=self
        self[category.name]=category

    def addLine(self,line):
        self[line.name] = line
        line.setParent(self)

    def merge(self,checker,category)->(int,int):
        """
        将category中所有元素导入当前层次。
        如果名称冲突，则跳过。如果冲突的是分类名，则整个分类被忽略。
        返回成功导入的【线路】总数和被忽略的线路总数。
        """
        cnt = 0
        cntIgnore = 0
        for name,data in category.items():
            if isinstance(data,Line):
                if not checker.nameExisted(name):
                    self[name]=data
                    cnt+=1
                else:
                    cntIgnore+=1
            elif isinstance(data,Category):
                # 递归！
                if not checker.nameExisted(name):
                    self[name]=Category(name)
                    cnt+=self[name].merge(data)
                else:
                    cntIgnore+=category.lineCount()
        return cnt,cntIgnore

    def lineCount(self)->int:
        """
        递归地返回线路总数。
        """
        cnt = 0
        for name,data in self.items():
            if isinstance(data,Category):
                try:
                    cnt+=data.lineCount()
                except RecursionError:
                    print("recursion Error!")
            else:
                cnt+=1
        return cnt

    def moveDrops(self,obj):
        """
        将line或category移动到本类的管理下。
        line和category具有相同的接口。
        """
        print("moveDrops",obj.name)
        parent = obj.parent
        print("parent is",parent.name)
        name = obj.name
        if parent is not None:
            # 删除父类引用
            del parent[name]
        self[name]=obj
        obj.setParent(self)








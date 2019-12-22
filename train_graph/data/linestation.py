"""
2019.12.22新增，线路中的站结点
"""

class LineStation(dict):
    def __init__(self,an=None):
        if an is None:
            super(LineStation, self).__init__()
        else:
            super(LineStation, self).__init__(an)

    def counterStr(self)->str:
        """
        返回对里程字符串。
        """
        counter=self.setdefault('counter',None)
        if counter is not None:
            return f"{counter:.3f}"
        return ''

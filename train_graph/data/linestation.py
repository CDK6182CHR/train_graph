"""
2019.12.22新增，线路中的站结点
2020.01.23注记：上下行判定，对里程相关的：
1. 定义A站到B站是下行区间，当且仅当A站的里程licheng字段小于B站的licheng字段。这就是说，即使是上下行分设站中的下行站，也必须保证其正里程（下行里程）具有合理的数值。
2. 一般情况下，反向里程的计算仅仅考虑两端点的值，不考虑中间站的对里程。
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

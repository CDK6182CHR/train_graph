"""
车次类修订。引入split()方法，对完整车次分段。允许包含括号的复车次。
生成文件名车次，将所有“/”换为“-”。
除一位0在首位外，字母均必须在开头（括号内除外），即允许0K9484，但不允许00K9484，也不允许1K9484。
将整个车次拆分成一个列表。

3.0修订说明：车次类扩展。设置Train类，包含一个车次在表格上的所有信息，以车次为唯一识别。其中车次是
Checi类的实例。
使用字典表示时刻表信息，格式：
车站：（到点，开点）

车站列信息决不允许空格。
"""
from direction import judge_direction
from collections import OrderedDict
from utility import split_checi,judge_type,isKeche

class Checi():
    def __init__(self,l1,l2=''):
        self.full = str(l1) + str(l2)
        #print(self.full)
        chaifen = split_checi(self.full)

        #非复用车次
        if len(chaifen) == 2:
            if int(chaifen[1]) % 2 == 0:
                self.up = chaifen[0]+chaifen[1]
                self.down = ''
            else:
                self.down = chaifen[0]+chaifen[1]
                self.up = ''
        #复用车次，仍然只考虑前两个
        else:
            if int(chaifen[1]) % 2 == 0:
                self.up = chaifen[0]+chaifen[1]
                self.down = self.up[:len(self.up)-len(chaifen[2])]+chaifen[2]
            else:
                self.down = chaifen[0] + chaifen[1]
                self.up = self.down[:len(self.down) - len(chaifen[2])] + chaifen[2]
        self.filename = ''
        for s in self.full:
            if s == '/':
                self.filename += '-'
            else:
                self.filename += s
        self.type = 'NULL'
        self.type = judge_type(chaifen=chaifen)
        self.keche = isKeche(self.type)
        print(chaifen,self.type)

class Train():
    def __init__(self,checi1,checi2,stations,times,sfz='',zdz='',type='',sfzdGiven=False):
        self.checi = Checi(checi1,checi2)
        self.stations = []
        for station in stations:
            if station.strip():
                self.stations.append(station.strip())
        self.sfz = sfz
        self.zdz = zdz
        self.type = type
        if self.type == '':
            self.type = self.checi.type
        self.keche = isKeche(self.type)
        colv = times
        for i in range(0,len(colv)):
            try:
                colv[i] = colv[i].strip()
            except AttributeError:
                colv[i] = str(int(colv[i])).strip()

        while len(colv) != 2*len(stations):
            if len(colv) > 2*len(stations):
                colv.pop()
            if len(colv) < 2*len(stations):
                colv.append('')

        #上下行判断
        tuple = judge_direction(times)
        if tuple[1] == -1:
            print("Direction judge error in",self.checi.full)
            return
        if tuple[1] <= 2:
            self.exist = False
            self.down = False
            return
        else:
            self.exist = True
        self.down = tuple[0]

        #上行时刻表直接反序，全部变为下行
        if not self.down:
            colv.reverse()
            self.stations.reverse()

        #时刻表规格化  第一轮：去除空格
        for row in range(0, len(colv)):
            cell = colv[row].strip()
            if cell == '':
                # 始发站处理
                try:
                    if colv[row + 1] and row % 2 == 0:
                        #表明是始发站
                        if not sfzdGiven:
                            self.sfz=stations[int((row+1)/2)]
                            print("始发站",stations[int((row+1)/2)])
                        colv[row] = colv[row + 1]
                        continue
                    else:
                        continue
                except IndexError:
                    continue
            if cell == '...':
                try:
                    cell = colv[row + 1]
                except IndexError:
                    print("\"...\"transfer error")

            if cell == '--':
                #终到站处理
                if not sfzdGiven:
                    self.zdz=stations[int(row/2)]
                    print("终到站",stations[int(row/2)])
                cell = colv[row - 1]
            colv[row] = cell

        #第二轮：填充省略小时数
        for row in range(0,len(colv)):
            cell = colv[row]
            if cell == '':
                    continue
            if ':' not in cell:
                t = row - 1
                while colv[t] == '':
                    t -= 1
                cell = colv[t].split(':')[0] + ':' + cell

            cells = cell.split(':')
            if len(cells[0]) == 1:
                cell = '0' + cell
            if len(cells[1]) == 2:
                cell += ':00'
            else:
                cell = cell[:-2]+':'+cell[-2:]
            colv[row] = cell

        #第三轮遍历，从车站入手规格化，使用字典保存时刻表信息

        self.timetable = OrderedDict()
        for i,s in enumerate(self.stations):
            #*2 *2+1
            if colv[i*2] and colv[i*2+1] and '--' not in colv[i*2] and '--' not in colv[i*2+1]:
                self.timetable[s] = (colv[i*2],colv[i*2+1])

class OnlineTrain():
    """
    爬虫所需车次类，相比表格所需车次类更为简洁。
    """
    def __init__(self,checi,down,sfz="",zdz=""):
        self.down = down
        self.checi = checi
        self.sfz = sfz
        self.zdz = zdz
        self.timetable = OrderedDict()

    def add_station(self,sfz,zdz,station,arrive,depart):
        if not self.sfz:
            self.sfz = sfz
        if not self.zdz:
            self.zdz = zdz
        self.timetable[station] = (arrive,depart)

    def check(self):
        if self.timetable:
            return True
        else:
            return False

class ReadTrain():
    """
    阅读既有运行图文件中车次的类
    """
    def __init__(self,checi,sfz,zdz):
        self.checi = Checi(checi)
        self.sfz = sfz
        self.zdz = zdz
        self.timetable = OrderedDict()

    def add_station(self,station,arrive,depart):
        self.timetable[station] = (arrive,depart)

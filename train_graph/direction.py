"""
封装上下行判断函数。接收一列数据（不包含列首），返回是否下行的数据（Bool）。
True 下行
False 上行
返回格式tuple:（方向，非空单元格数）
"""
def judge_direction(colv):
    judged=False
    un_blank=0
    for row in range(0,len(colv)):
        cell = colv[row].strip()
        if cell:
            un_blank += 1
        # 上下行的通过判据
        if cell == '...' and judged == False:
            if row % 2 == 0:
                down=True
            else:
                down=False
            judged = True

        # 上下行的终到判据
        if cell == '--' and judged == False:
            if row % 2 == 0:
                down=False
            else:
                down=True
            judged = True

        # 上下行的完整时刻判据和始发判据
        if ':' in cell and judged == False:
            if row % 2 == 1:
                cell0 = colv[row - 1].strip()
                if cell0 == '':
                    down=True  # 下行始发车
                    judged = True
                if cell0 not in ['...', '']:
                    if ':' not in cell0:
                        down=False
                        judged = True
                    else:
                        hour = int(cell.split(':')[0])
                        hour0 = int(cell0.split(':')[0])
                        if hour < hour0 and abs(hour0 - hour) <= 2:
                            down=False
                            judged = True
                        elif hour > hour0 and abs(hour0 - hour) <= 2:
                            down=True
                            judged = True
            else:
                try:
                    cell0 = colv[row + 1].strip()
                except IndexError:
                    print("IndexError in finding cell 0")
                    return (True,-1)
                if cell0 == '':
                    down=False  # 上行始发车
                    judged = True
                if cell0 not in ['...', '']:
                    if ':' not in cell0:
                        down=True
                        judged = True
                    else:
                        hour = int(cell.split(':')[0])
                        hour0 = int(cell0.split(':')[0])
                        if hour > hour0 and hour * hour0 and abs(hour0 - hour) <= 2:
                            down=False
                            judged = True
                        elif hour < hour0 and hour * hour0 and abs(hour0 - hour) <= 2:
                            down = True
                            judged = True
    if un_blank >= 3:
        try:
            return (down,un_blank)
        except NameError:
            return (True,un_blank)
    else:
        try:
            return (down,un_blank)
        except NameError:
            return (True,un_blank)

def judge_order_by_direction(trainraw1,trainraw2,method):
    """连接顺序的上下行判据。返回是否交换顺序bool值"""
    if method == 0:
        if trainraw1.down:
            change = False
        else:
            change = True

    elif method == 1:
        if trainraw1.down:
            change = True
        else:
            change = False

    else:
        if trainraw1.down:
            change = False
        else:
            change = True

    return change

def judge_order_by_station(trainraw1,trainraw2):
    """通过重复站名所在的位置判定顺序"""
    count = 0
    for i,s in trainraw2.timetable.items():
        count += 1
        if i in list(trainraw1.timetable.keys()):
            break
    if count <= len(list(trainraw2.timetable.keys())) * 0.2 or count < 2: #2018.08.02修改，去掉<=的=
        return False
    else:
        return True
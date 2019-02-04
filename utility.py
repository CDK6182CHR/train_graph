"""
列车运行图相关 工具函数库
"""
import re
import json
from datetime import datetime

def split_checi(checi):
    """
    拆分车次为列表格式，从checi3构造函数中独立出来
    """
    letter = -1
    for i, s in enumerate(checi):
        if s == '0':
            continue
        try:
            int(s)
        except ValueError:
            pass
        else:
            letter = i - 1  # 记录了索引为多少的位数是最后一位开头字母
            break
    if letter == -1:
        chaifen = ['']
    else:
        chaifen = [checi[:letter + 1]]
    all_num = checi[letter + 1:]

    if '(' in all_num:
        chaifen += all_num.split('(')[0].split('/')
    elif '（' in all_num:
        chaifen += all_num.split('（')[0].split('/')
    elif '[' in all_num:
        chaifen += all_num.split('[')[0].split('/')
    else:
        chaifen += all_num.split('(')[0].split('/')

    # 清除末尾的字母，如3257B
    for i, s in enumerate(chaifen):
        if i > 0:
            flag = False
            for t in ['(', '（', '[']:
                if t in s:
                    flag = True
                    break

            if not flag:
                chaifen[i] = re.findall("(\d+)", s)[0]


    return chaifen


def isKeche(type: str):
    keche_types = (
        '高速', "动车", '城际', '动车组',
        '直达特快', '特快', '快速', "临客",
        '普快', '普客', '通勤', '旅游',
        '动检', "客车底", "确认车", "路用", "动检车",
    )
    if type in keche_types:
        return True
    else:
        return False


def judge_type(checi: str = '', chaifen: list = None):
    if chaifen is None:
        chaifen = split_checi(checi)
    chedi = False
    head = chaifen[0]
    number = int(chaifen[1])
    if '0' in head:
        chedi = True
        head = head.replace('0', '')

    if not head:
        # 纯数字的情况
        if number < 10000:
            keche = True
            if number < 6000:
                type = '普快'
            elif number < 7500:
                type = '普客'
            else:
                type = '通勤'
        else:
            keche = False
            type = '非客车'

    else:
        if head == 'X':
            keche = False
            if number < 200:
                type = '特快行包'
            else:
                type = '行包'

        else:
            keche = True
            if head == 'G':
                type = '高速'
            elif head == 'D':
                type = "动车"
            elif head == 'C':
                type = "城际"
            elif head == 'DJ':
                type = "动检"
            elif head == 'Z':
                type = '直达特快'
            elif head == 'T':
                type = '特快'
            elif head == 'K':
                type = '快速'
            elif head == 'Y':
                type = '旅游'
            else:
                type = '未知'

    if chedi:
        if keche:
            type = '客车底'
        else:
            type = '货车底'
    return type


def del_trains(trains, stations, del_station=False, keche_only=False):
    if not stations:
        return

    in_trains = []
    del_list = []
    for i, train in enumerate(trains):
        in_num = 0
        del_sts = []
        for st in train.timetable.keys():
            del_sts.append(st)
            if st in stations:
                in_num += 1
            if in_num >= 2:
                break
        # end for station
        if del_station:
            for st in del_sts:
                del train.timetable[st]

        if in_num >= 2:
            # in_trains.append(train)
            pass
        else:
            print("删除车次：", train.checi.full)
            del_list.append(i)

        if keche_only and (train.keche == False and train.type != '特快行包') and i not in del_list:
            print("删除车次：", train.checi.full, train.type)
            del_list.append(i)

    # end for train
    del_list.reverse()
    for i in del_list:
        del trains[i]

    return


def lines_to_json():
    """
    change line datas from .trc to .json
    :return:
    """
    from os import walk
    lines = {}

    filenames = list(walk('lines'))[0][2]
    for file in filenames:
        line_name = file[:-4]
        dict = {
            "name": line_name,
            "rulers": [],
            "stations": [],
        }
        fp = open('lines/' + file, 'r', encoding='utf-8', errors='ignore')
        for i, s in enumerate(fp):
            s = s.strip()
            if i <= 2:
                continue
            if not s:
                continue

            try:
                st = {
                    "zhanming": s.split(',')[0],
                    "licheng": int(s.split(',')[1]),
                    "dengji": int(s.split(',')[2])
                }
            except IndexError:
                print(s, file)
            dict["stations"].append(st)
        lines[line_name] = dict
        fp.close()

    out = open('source/lines.json', 'w', encoding='utf-8')
    json.dump(lines, out, ensure_ascii=False)
    out.close()

def stationEqual(st1: str, st2: str, strict=False):
    """
    比较两站名是否相同，支持域解析符
    """
    if st1 == st2:
        return True

    if not strict:
        if ('::' in st1) != ('::' in st2) and st1.split('::')[0] == st2.split('::')[0]:
            #仅一侧有域解析符才能模糊匹配
            return True
    return False

def strToTime(src:str):
    """
    将字符串转换为datetime.datetime对象并返回。支持两种格式："%H:%M"；"%H:%M:%S"。
    用于代替库函数datetime.striptime，后者效率有点低。
    """
    digits = map(int,src.split(':'))
    return datetime(1900,1,1,*digits)


if __name__ == '__main__':
    lines_to_json()

"""
发布为egg包时，将.Timetable_new变为相对引用
"""
import os
for a in os.scandir('.'):
    if not a.is_dir() and '.py' in a.name and a.name != 'make_egg.py':
        print(a.name)
        with open(a.name,encoding='utf-8',errors='ignore') as fp:
            c = fp.read().replace('Timetable_new','.Timetable_new')
            c = c.replace('..Timetable_new','.Timetable_new')
        with open(a.name,'w',encoding='utf-8',errors='ignore') as fp:
            fp.write(c)

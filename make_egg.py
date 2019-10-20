"""
发布为egg包时，将.Timetable_new变为相对引用
"""
import os
for x,y,z in os.walk('.'):
    for a in z:
        if '.py' in a and a != 'make_egg.py':
            print(a)
            f = x+'/'+a
            with open(f,encoding='utf-8',errors='ignore') as fp:
                c = fp.read().replace('Timetable_new','.Timetable_new')
                c = c.replace('..Timetable_new','.Timetable_new')
            with open(f,'w',encoding='utf-8',errors='ignore') as fp:
                fp.write(c)

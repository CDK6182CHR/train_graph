@echo off
echo pyETRC���ص��԰汾�������
echo 2020.02.17���°汾��������PyQt5�⣬����ᵼ�²���ԭ��ĵ������
@echo on
python -m nuitka --exe --recurse-all main.py --mingw64 --windows-icon=D:/Python/train_graph/icon.ico --recurse-not-to=openpyxl  --recurse-not-to=PyQt5
pause


@echo off
echo pyETRC本地调试版本编译程序
echo 2020.02.17更新版本。不编译PyQt5库，因其会导致不明原因的导入错误。
@echo on
python -m nuitka --exe --recurse-all main.py --mingw64 --windows-icon=D:/Python/train_graph/icon.ico --recurse-not-to=openpyxl  --recurse-not-to=PyQt5
pause


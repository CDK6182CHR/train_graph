@echo off
echo Running debug...
python -m nuitka --exe --recurse-all main.py --mingw --icon=train_graph/icon.ico --recurse-not-to=openpyxl

echo Running release...
python -m nuitka --exe --recurse-all main.py --mingw --plugin-enable=qt-plugins --standalone --windows-icon=D:\Python\train_graph\icon.ico --recurse-not-to=openpyxl

rem  --windows-disable-console  不显示控制台，暂不启用

pause
@echo off
echo Running debug...
python -m nuitka --exe --recurse-all main.py --mingw --icon=train_graph/icon.ico --recurse-not-to=openpyxl

echo Running release...
python -m nuitka --exe --recurse-all main.py --mingw --windows-disable-console --plugin-enable=qt-plugins --standalone --icon=train_graph/icon.ico --recurse-not-to=openpyxl

pause
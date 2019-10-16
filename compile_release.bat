rem copy "..\Timetable_new\checi3.py" "checi3.py"
rem copy "..\Timetable_new\utility.py" "utility.py"
rem copy "..\Timetable_new\direction.py" "direction.py"
python -m nuitka --exe --recurse-all main.py --mingw --windows-disable-console --plugin-enable=qt-plugins --standalone --icon=train_graph/icon.ico --recurse-not-to=openpyxl
pause
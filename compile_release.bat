rem copy "..\Timetable_new\checi3.py" "checi3.py"
rem copy "..\Timetable_new\utility.py" "utility.py"
rem copy "..\Timetable_new\direction.py" "direction.py"
python -m nuitka --exe --recurse-all main.py --mingw --plugin-enable=qt-plugins --standalone --windows-icon=D:\Python\train_graph\icon.ico --recurse-not-to=openpyxl
pause
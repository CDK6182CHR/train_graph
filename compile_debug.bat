rem copy "..\Timetable_new\checi3.pyd" "checi3.pyd"
rem copy "..\Timetable_new\utility.pyd" "utility.pyd"
rem copy "..\Timetable_new\direction.py" "direction.py"
python -m nuitka --exe --recurse-all main.py --mingw --windows-icon=D:/Python/train_graph/icon.ico --recurse-not-to=openpyxl
pause


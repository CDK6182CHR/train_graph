@echo off
echo pyETRC standalone compile script
echo 2020.2.17
echo use experimenetal feature [pefile] to reduce size of output file.
@echo on
python -m nuitka --exe --recurse-all main.py --mingw64 --plugin-enable=qt-plugins --standalone --windows-icon=D:\Python\train_graph\icon.ico --recurse-not-to=openpyxl --experimental=use_pefile 
pause
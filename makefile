# 构建pyETRC发行版

NUITKA = python3 -m nuitka

MAIN_SCRIPT = main.py
LOCAL_OUT = main.exe
WIN64_OUT = main.dist/main.exe
EGG_DIR = ..\TempRelease\pyETRC-egg
EGG_OUT = $(EGG_DIR)\pyETRC.egg

NOTE_FILE = ReleaseNote.pdf
LIST_FILE = docs\简明功能表.xlsx

WIN64_DIR = ..\TempRelease\pyETRC-win64 V3.1

SOURCE =  $(wildcard train_graph/*/*.py) 
SOURCE += $(wildcard train_graph/*.py)

LOCAL_FLAGS = --exe --recurse-all --mingw64 --windows-icon=D:/Python/train_graph/icon.ico --recurse-not-to=openpyxl  --recurse-not-to=PyQt5
WIN64_FLAGS = --exe --recurse-all --mingw64 --plugin-enable=qt-plugins --standalone --windows-icon=D:\Python\train_graph\icon.ico --recurse-not-to=openpyxl --experimental=use_pefile 

.PHONY: all
all: $(LOCAL_OUT) win64_install egg_install
	echo "build finished"
	
.PHONY: local
local: $(LOCAL_OUT)
	echo "local"

.PHONY: egg
egg: $(EGG_OUT)
	echo egg version

# 本地调试版本
$(LOCAL_OUT) : $(SOURCE)
	echo building pyETRC local debug version
	$(NUITKA) $(LOCAL_FLAGS) $(MAIN_SCRIPT)
	
# win64发行版
$(WIN64_OUT) : $(SOURCE)
	echo building pyETRC win64 release version
	$(NUITKA) $(WIN64_FLAGS) $(MAIN_SCRIPT)


# egg版，直接在目标目录构建
$(EGG_OUT) : $(SOURCE)
	echo building pyETRC egg release version
	xcopy train_graph $(EGG_DIR)\train_graph /Y
# del /s/q $(EGG_DIR)\train_graph\__pycache__
# rmdir $(EGG_DIR)\train_graph\__pycache__
	7z a $(EGG_DIR)\tmp.zip $(EGG_DIR)\train_graph $(EGG_DIR)\Timetable_new $(EGG_DIR)\__main__.py
	move $(EGG_DIR)\tmp.zip $(EGG_OUT)

.IGNORE: win64_install
.PHONY: win64_install
win64_install : $(NOTE_FILE) $(WIN64_OUT) 
	echo installing win64 version
	copy main.dist "$(WIN64_DIR)\requests" /Y
	copy $(NOTE_FILE) "$(WIN64_DIR)" /Y
	copy $(LIST_FILE) "$(WIN64_DIR)" /Y
	explorer "$(WIN64_DIR)"

.IGNORE : egg_install
.PHONY: egg_install
egg_install : $(NOTE_FILE) $(EGG_OUT)
	echo installing egg version
	copy $(NOTE_FILE) $(EGG_DIR) /Y
	copy $(LIST_FILE) $(EGG_DIR) /Y
	explorer "$(EGG_DIR)"
	
.PHONY: clean
clean:
	del main.dist\*
	del main.build\*
	del main.exe

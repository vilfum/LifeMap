@echo off
echo Fixing paths and creating launcher...
echo.

echo 1. Creating simple launcher (start_eng.bat)...
echo @echo off > start_eng.bat
echo "D:\Python\python.exe" "D:\КартаЖизни\main.py" >> start_eng.bat
echo pause >> start_eng.bat

echo 2. Creating test Python script...
echo import sys > test_python.py
echo print("Python version:", sys.version) >> test_python.py
echo print("Python path:", sys.executable) >> test_python.py
echo input("Press Enter to exit...") >> test_python.py

echo 3. Testing Python...
"D:\Python\python.exe" test_python.py

echo.
echo If you see Python version above, everything is OK!
echo Now you can use start_eng.bat to launch the program.
pause
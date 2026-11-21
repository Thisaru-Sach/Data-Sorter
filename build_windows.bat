@echo off
REM Run from the project folder on Windows.
REM Uses "python -m" so it works even when Device Guard blocks pip.exe / pyinstaller.exe.
if not exist venv python -m venv venv
call venv\Scripts\activate
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --windowed --name DataSorter main.py
echo.
echo Done. Your app is: dist\DataSorter\DataSorter.exe
pause
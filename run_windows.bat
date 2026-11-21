@echo off
REM Double-click to start Data Sorter without building an .exe.
REM First run sets up a virtual environment automatically (needs Python installed).
cd /d "%~dp0"
if not exist venv\Scripts\pythonw.exe (
    echo Setting up Data Sorter for the first time, please wait...
    python -m venv venv
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Setup failed. See the messages above.
        pause
        exit /b 1
    )
)
start "" venv\Scripts\pythonw.exe main.py

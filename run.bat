@echo off
rem Starts the game on Windows (the Windows version of run.sh).
rem Double-click it, or run it from any folder.
rem
rem Before starting, it makes sure the libraries are installed:
rem   - creates the .venv folder if it does not exist yet
rem   - installs requirements.txt the first time, and again whenever
rem     requirements.txt changes (e.g. after a git pull that added a library)

rem Go to the folder this file is in, so assets/ and the .task model are found.
cd /d "%~dp0"

if exist .venv\Scripts\python.exe goto venv_ready
echo Creating the Python environment (.venv)...
rem "py" is the Python launcher that the python.org installer adds.
rem If it is missing, try "python" instead.
py -m venv .venv 2>nul || python -m venv .venv
if errorlevel 1 (
    echo Could not create .venv. Install Python from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" in the installer.
    pause
    exit /b 1
)
:venv_ready

rem .venv\installed-requirements.txt is a copy of requirements.txt from the last
rem successful install. "fc" compares the two; if they differ (or the copy is
rem missing), something new needs installing.
fc /b requirements.txt .venv\installed-requirements.txt >nul 2>nul
if not errorlevel 1 goto installed
echo Installing libraries from requirements.txt...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo Installing the libraries failed. Check your internet connection and try again.
    echo If MediaPipe has no package for your Python version, install Python 3.12,
    echo delete the .venv folder and run this file again.
    pause
    exit /b 1
)
copy /y requirements.txt .venv\installed-requirements.txt >nul
:installed

.venv\Scripts\python.exe main.py
rem Keep the window open if the game crashed, so the error can be read.
if errorlevel 1 pause

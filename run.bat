@echo off
REM Starts the game on Windows. Double-click this file, or type  run.bat
REM in a terminal opened in this folder. (The Linux version is run.sh.)
REM
REM Before starting, it makes sure the libraries are installed:
REM   - creates the .venv folder if it does not exist yet
REM   - installs requirements.txt the first time, and again whenever
REM     requirements.txt changes (e.g. after a git pull that added a library)

REM Work from the folder this file is in, wherever it was started from.
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto check_libraries

echo Creating the Python environment .venv ...
REM "py" is the Python launcher that comes with Python from python.org.
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" goto no_python

REM MediaPipe only exists for 64-bit Python.
.venv\Scripts\python -c "import struct, sys; sys.exit(struct.calcsize('P') != 8)"
if errorlevel 1 goto python_32bit

:check_libraries
REM .venv\installed-requirements.txt is a copy of requirements.txt from the
REM last successful install. If the two differ, something new needs installing.
fc /b requirements.txt .venv\installed-requirements.txt >nul 2>nul
if not errorlevel 1 goto start_game

echo Installing libraries from requirements.txt, this can take a few minutes...
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 goto install_failed
copy /y requirements.txt .venv\installed-requirements.txt >nul

:start_game
.venv\Scripts\python main.py
REM If the game crashed, keep the window open so the error can be read.
if errorlevel 1 pause
exit /b

:no_python
echo.
echo Could not create .venv because Python was not found.
echo Install 64-bit Python 3 from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" in the installer. Then run this again.
pause
exit /b 1

:python_32bit
echo.
echo Your Python is 32-bit, but MediaPipe needs 64-bit Python.
echo Install the 64-bit version from https://www.python.org/downloads/
echo and then run this again.
rmdir /s /q .venv
pause
exit /b 1

:install_failed
echo.
echo Installing the libraries failed. Check your internet connection and try again.
pause
exit /b 1

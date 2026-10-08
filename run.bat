@echo off
setlocal
REM Starts the game on Windows. Double-click this file, or type  run.bat
REM in a terminal opened in this folder. (The Linux version is run.sh.)
REM
REM It sets everything up by itself, so it works on a computer without Python:
REM   1. Finds a usable Python (64-bit, 3.10 to 3.14: MediaPipe needs that).
REM   2. If there is none, installs Python 3.14 for this user only (no admin
REM      password): with winget if Windows has it, otherwise downloaded from
REM      python.org. This needs the internet and takes a few minutes, once.
REM   3. Makes the .venv folder and installs requirements.txt into it, the
REM      first time and again whenever requirements.txt changes.
REM   4. Starts the game.

REM Work from the folder this file is in, wherever it was started from.
cd /d "%~dp0"

set "PYVER=3.14.0"
set "PYURL=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe"
REM Where a per-user Python 3.14 is installed (by winget or the python.org installer).
set "LOCALPY=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"

REM An existing .venv that still works: straight to the libraries.
if not exist ".venv\Scripts\python.exe" goto find_python
call :try_python ".venv\Scripts\python.exe" && goto check_libraries
echo The .venv folder does not work any more; making it again...
rmdir /s /q .venv

:find_python
REM "py" is the Python launcher that comes with Python from python.org.
call :try_python py -3.14 && goto make_venv
call :try_python py -3.13 && goto make_venv
call :try_python py -3.12 && goto make_venv
call :try_python python && goto make_venv
call :try_python "%LOCALPY%" && goto make_venv

echo.
echo No usable Python found. Installing Python %PYVER% for you
echo (only for this user, no admin needed). This takes a few minutes...
where winget >nul 2>nul
if errorlevel 1 goto download_python
winget install -e --id Python.Python.3.14 --scope user --silent --accept-package-agreements --accept-source-agreements
call :try_python "%LOCALPY%" && goto make_venv
call :try_python py -3.14 && goto make_venv

:download_python
echo Downloading Python %PYVER% from python.org ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing -Uri '%PYURL%' -OutFile '%TEMP%\python-%PYVER%-installer.exe'"
if not exist "%TEMP%\python-%PYVER%-installer.exe" goto no_python
echo Installing Python %PYVER% ...
"%TEMP%\python-%PYVER%-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0
del "%TEMP%\python-%PYVER%-installer.exe" >nul 2>nul
call :try_python "%LOCALPY%" && goto make_venv
goto no_python

:make_venv
echo Creating the Python environment .venv with %PY% ...
%PY% -m venv .venv
if not exist ".venv\Scripts\python.exe" goto no_python

:check_libraries
REM .venv\installed-requirements.txt is a copy of requirements.txt from the
REM last successful install. If the two differ, something new needs installing.
fc /b requirements.txt .venv\installed-requirements.txt >nul 2>nul
if not errorlevel 1 goto start_game

echo Installing libraries from requirements.txt, this can take a few minutes...
.venv\Scripts\python -m pip install --upgrade pip
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
echo Python could not be found or installed automatically.
echo Install 64-bit Python 3.14 from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" in the installer. Then run this again.
pause
exit /b 1

:install_failed
echo.
echo Installing the libraries failed. Check your internet connection and try again.
pause
exit /b 1

REM ---------------------------------------------------------------------------
REM :try_python <command>  - is this a Python we can use? If yes, PY is set to
REM it and the answer is "yes" (errorlevel 0). It must run (the Microsoft Store
REM "python" shortcut does not), be 64-bit and be 3.10 to 3.14 (MediaPipe).
:try_python
%* -c "import struct, sys; sys.exit(0 if struct.calcsize('P') == 8 and (3, 10) <= sys.version_info[:2] <= (3, 14) else 1)" >nul 2>nul
if errorlevel 1 exit /b 1
set PY=%*
exit /b 0

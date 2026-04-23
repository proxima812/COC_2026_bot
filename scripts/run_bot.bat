@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
set "TELEGRAM_CONTROL_BACKEND=%TELEGRAM_CONTROL_BACKEND%"
if "%TELEGRAM_CONTROL_BACKEND%"=="" set "TELEGRAM_CONTROL_BACKEND=aiogram"
set "TELEGRAM_UI_MODE=%TELEGRAM_UI_MODE%"
if "%TELEGRAM_UI_MODE%"=="" set "TELEGRAM_UI_MODE=default"
if /I "%~1"=="-test" set "TELEGRAM_UI_MODE=test"
if /I "%~1"=="--test" set "TELEGRAM_UI_MODE=test"
set "BLUESTACKS_EXE=%BLUESTACKS_EXE%"
if "%BLUESTACKS_EXE%"=="" set "BLUESTACKS_EXE=C:\Program Files\BlueStacks_nxt\HD-Player.exe"
if not exist "%BLUESTACKS_EXE%" set "BLUESTACKS_EXE=C:\Program Files\BlueStacks\HD-Player.exe"
set "ADB_BIN=%ADB_BIN%"
if "%ADB_BIN%"=="" set "ADB_BIN=C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
if not exist "%ADB_BIN%" set "ADB_BIN=C:\Program Files\BlueStacks\HD-Adb.exe"
set "COC_PACKAGE=com.supercell.clashofclans"

where python >nul 2>nul
if errorlevel 1 (
  echo [run bot] error: python not found
  exit /b 1
)

if exist "%BLUESTACKS_EXE%" (
  tasklist /FI "IMAGENAME eq HD-Player.exe" | find /I "HD-Player.exe" >nul
  if errorlevel 1 (
    echo [run bot] starting BlueStacks...
    start "" "%BLUESTACKS_EXE%"
    timeout /t 10 /nobreak >nul
  ) else (
    echo [run bot] BlueStacks is already running
  )
)

if exist "%ADB_BIN%" (
  "%ADB_BIN%" start-server >nul 2>nul
  "%ADB_BIN%" connect 127.0.0.1:5555 >nul 2>nul
  "%ADB_BIN%" shell monkey -p %COC_PACKAGE% -c android.intent.category.LAUNCHER 1 >nul 2>nul
)

cd /d "%PROJECT_DIR%"
if /I "%TELEGRAM_CONTROL_BACKEND%"=="legacy" (
  python telegram_control.py
) else (
  python telegram_control_aiogram.py
)

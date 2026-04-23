@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
where python >nul 2>nul
if errorlevel 1 (
  echo [run farm] error: python not found
  exit /b 1
)

cd /d "%PROJECT_DIR%"
python bot.py

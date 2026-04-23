@echo off
setlocal

for %%P in (python.exe pythonw.exe) do (
  taskkill /FI "IMAGENAME eq %%P" /FI "WINDOWTITLE eq *telegram_control_aiogram.py*" /T /F >nul 2>nul
  taskkill /FI "IMAGENAME eq %%P" /FI "WINDOWTITLE eq *telegram_control.py*" /T /F >nul 2>nul
  taskkill /FI "IMAGENAME eq %%P" /FI "WINDOWTITLE eq *bot.py*" /T /F >nul 2>nul
)

for /f "tokens=2" %%I in ('wmic process where "CommandLine like '%%telegram_control_aiogram.py%%' or CommandLine like '%%telegram_control.py%%' or CommandLine like '%%bot.py%%'" get ProcessId /value 2^>nul ^| find "="') do (
  taskkill /PID %%I /T /F >nul 2>nul
)

echo [stop] bot processes stopped

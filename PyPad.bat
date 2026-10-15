@echo off
rem PyPad starten - Windows
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -u pypad.py
) else (
  python -u pypad.py
)
pause

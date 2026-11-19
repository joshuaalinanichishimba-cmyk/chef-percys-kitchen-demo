@echo off
setlocal
cd /d "%~dp0kitchen-app\backend" || goto setup_error
if not exist ".venv\Scripts\python.exe" goto setup_error
".venv\Scripts\python.exe" start_local.py
if errorlevel 1 pause
exit /b
:setup_error
echo The Python environment is missing. Open kitchen-app\README.md for setup.
pause
exit /b 1

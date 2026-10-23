@echo off
chcp 65001 > nul
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe manage_autostart.py install
) else (
    python manage_autostart.py install
)
echo.
pause

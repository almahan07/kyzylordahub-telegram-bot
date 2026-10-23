@echo off
chcp 65001 > nul
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe manage_autostart.py uninstall
) else (
    python manage_autostart.py uninstall
)
echo.
pause

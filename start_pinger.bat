@echo off
chcp 65001 > nul
title Render 24/7 Keep-Alive Автобот
cd /d "%~dp0"

echo ========================================================
echo 🚀 Render 24/7 Keep-Alive Авто-пингерді іске қосу
echo ========================================================
echo.

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe render_pinger.py
) else (
    python render_pinger.py
)

pause

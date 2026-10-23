@echo off
chcp 65001 > nul
title Kyzylorda Hub Telegram Bot
echo ========================================================
echo Kyzylorda Hub Telegram боты іске қосылуда...
echo ========================================================
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py
) else (
    echo [ҚАТЕ] venv табылмады! python -m venv venv орындаңыз.
    pause
)
pause

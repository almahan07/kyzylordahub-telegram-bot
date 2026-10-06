@echo off
chcp 65001 > nul
title Kyzylorda Hub Telegram Bot
echo Kyzylorda Hub боты іске қосылуда...
cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py
pause

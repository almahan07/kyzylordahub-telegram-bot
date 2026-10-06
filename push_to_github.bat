@echo off
chcp 65001 > nul
echo ========================================================
echo GitHub-қа кодты жүктеу (Push)
echo ========================================================
cd /d "%~dp0"

echo 1. GitHub репозиторийі тексерілуде...
git branch -M main
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ⚠️ Егер қате шықса, алдымен мына сілтемеден жаңа репозиторий ашыңыз:
    echo 👉 https://github.com/new
    echo Repository name: kyzylordahub-telegram-bot
    echo Содан кейін осы файлды қайта басыңыз!
) else (
    echo.
    echo ✅ Код GitHub-қа сәтті жүктелді!
)

echo.
pause

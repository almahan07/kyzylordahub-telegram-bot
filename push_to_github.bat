@echo off
chcp 65001 > nul
echo ========================================================
echo GitHub-қа кодты жүктеу (Push)
echo ========================================================
cd /d "%~dp0"

echo 1. Өзгерістерді индекске қосу (git add)...
git add .

echo 2. Жаңа коммит жасау (git commit)...
git commit -m "Add Render 24/7 keep-alive autobot and GitHub Actions" 2>nul || echo Жаңа өзгерістер жоқ немесе коммит жасалды.

echo 3. GitHub-қа жіберу (git push)...
echo (Егер GitHub терезесі немесе браузер ашылса, «Sign in with your browser» басыңыз)
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

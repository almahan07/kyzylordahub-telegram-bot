@echo off
chcp 65001 > nul
echo ========================================================
echo Kyzylorda Hub ботын Windows Автозагрузкасына қосу...
echo ========================================================

set SCRIPT_DIR=%~dp0
set VBS_PATH=%SCRIPT_DIR%start_bot_hidden.vbs
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT=%STARTUP_DIR%\KyzylordaHubBot.lnk

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%VBS_PATH%\"'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Save()"

if exist "%SHORTCUT%" (
    echo.
    echo [OK] Сәтті қосылды! Енді компьютер әр қосылғанда бот артқы фонда үндемей автоматты түрде іске қосылып тұрады.
) else (
    echo.
    echo [ҚАТЕ] Жарлық жасау мүмкін болмады.
)

echo.
pause

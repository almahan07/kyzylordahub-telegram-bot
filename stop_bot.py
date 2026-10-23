import os
import sys
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def stop():
    print("=" * 60)
    print("🛑 Kyzylorda Hub ботын тоқтату...")
    print("=" * 60)

    # PowerShell арқылы main.py орындап жатқан python/pythonw процестерін тауып жабу
    cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match \'main\\.py\' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host $_.ProcessId }"'
    try:
        res = subprocess.check_output(cmd, shell=True, text=True, errors="ignore").strip()
        if res:
            pids = res.split()
            print(f"✅ Бот процесі сәтті тоқтатылды! (PID: {', '.join(pids)})")
        else:
            print("ℹ️ Қосулы тұрған бот процесі табылмады.")
    except Exception as e:
        print(f"Қате: {e}")

if __name__ == "__main__":
    stop()

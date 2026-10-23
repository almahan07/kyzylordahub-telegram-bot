import os
import sys
import asyncio
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

async def check_telegram():
    if not BOT_TOKEN:
        print("❌ .env файлында BOT_TOKEN көрсетілмеген!")
        return

    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                if data.get("ok"):
                    bot = data["result"]
                    print(f"✅ Telegram байланысы: СӘТТІ (@{bot.get('username')}, {bot.get('first_name')})")
                else:
                    print(f"❌ Telegram қатесі: {data.get('description')}")
        except Exception as e:
            print(f"❌ Telegram серверіне қосылу қатесі: {e}")

        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                if data.get("ok"):
                    res = data["result"]
                    pending = res.get("pending_update_count", 0)
                    webhook_url = res.get("url", "")
                    if webhook_url:
                        print(f"⚠️ Белсенді Webhook бар: {webhook_url}")
                    else:
                        print(f"ℹ️ Режим: Long Polling (Күтіп тұрған хабарламалар саны: {pending})")
        except Exception:
            pass

def check_process():
    import subprocess
    cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \\"name like \'python%\'\\" | Select-Object ProcessId, CommandLine"'
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, encoding="utf-8", errors="ignore")
        found = False
        for line in out.splitlines():
            if "main.py" in line:
                found = True
                print(f"🟢 БОТ ПРОЦЕССІ ҚОСУЛЫ ТҰР (Жұмыс істеп жатыр)")
                break
        if not found:
            print("🔴 БОТ ТОҚТАП ТҰР (Процесс қосылмаған)")
    except Exception:
        print("ℹ️ Процестерді тексеру мүмкін болмады.")

    startup_lnk = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "KyzylordaHubBot.lnk"
    if startup_lnk.exists():
        print("🟢 Автозагрузка: ҚОСУЛЫ (ноут қосылғанда бот автоматты іске қосылады)")
    else:
        print("🟡 Автозагрузка: ӨШІРУЛІ (орнату үшін install_autostart.bat басыңыз)")

def main():
    print("=" * 60)
    print("🔍 Kyzylorda Hub Telegram Bot - Күйін тексеру (Status)")
    print("=" * 60)
    check_process()
    print("-" * 60)
    asyncio.run(check_telegram())
    print("=" * 60)

if __name__ == "__main__":
    main()

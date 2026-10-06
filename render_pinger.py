"""
Kyzylorda Hub Telegram Bot - Render 24/7 Keep-Alive Автобот.
Бұл скрипт Render.com сайтындағы ботты ұйықтатпай (sleep mode),
24/7 үздіксіз жұмыс істету үшін әр 5 минут сайын /health адресіне сұраныс жібереді.
"""

import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# Windows жүйесінде UTF-8 таңбалары қатесіз шығуы үшін
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Render қызметінің сілтемесі
DEFAULT_URL = "https://kyzylordahub-telegram-bot-1.onrender.com/health"
TARGET_URL = os.getenv("RENDER_URL", DEFAULT_URL)

# Пинг аралығы (секундпен) - 5 минут = 300 секунд
INTERVAL_SECONDS = int(os.getenv("PING_INTERVAL", "300"))


def ping_render(url: str) -> bool:
    """Render адресіне GET сұранысын жіберу."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_time = time.time()
    
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KyzylordaHub-KeepAlive-Bot/1.0",
            "Accept": "application/json",
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            status_code = response.getcode()
            elapsed_ms = int((time.time() - start_time) * 1000)
            print(f"[{now_str}] ✅ ПИНГ СӘТТІ | Код: {status_code} | Уақыт: {elapsed_ms}ms | URL: {url}")
            return True
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        print(f"[{now_str}] ⚠️ HTTP ҚАТЕ | Код: {e.code} | Уақыт: {elapsed_ms}ms | Хабарлама: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"[{now_str}] ❌ БАЙЛАНЫС ҚАТЕСІ | {e.reason}")
        return False
    except Exception as e:
        print(f"[{now_str}] ❌ КҮТПЕГЕН ҚАТЕ | {e}")
        return False


def main() -> None:
    print("=" * 65)
    print("🚀 Kyzylorda Hub Telegram Bot - Render 24/7 Авто-пингер")
    print(f"📍 Нысана: {TARGET_URL}")
    print(f"⏱️ Пинг аралығы: {INTERVAL_SECONDS // 60} минут ({INTERVAL_SECONDS} секунд)")
    print("=" * 65)
    print("Автобот жұмысын бастады. Тоқтату үшін Ctrl+C басыңыз...\n")

    counter = 1
    while True:
        print(f"--- [#{counter} Тексеру] ---")
        ping_render(TARGET_URL)
        counter += 1
        
        minutes = INTERVAL_SECONDS // 60
        print(f"Келесі тексеру {minutes} минуттан кейін...\n")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Авто-пингер қолданушы пәрменімен тоқтатылды.")

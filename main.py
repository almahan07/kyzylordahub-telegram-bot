import asyncio
import logging
import os
import sys

# Windows жүйесінде қазақша әріптер мен UTF-8 таңбалары қатесіз шығуы үшін
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, ADMIN_IDS, RENDER_EXTERNAL_URL
import database as db
from handlers import main_router

BASE_DIR = Path(__file__).resolve().parent

# Логирование баптауы (файлға және мүмкін болса консольге жазу)
log_handlers: list[logging.Handler] = [
    logging.FileHandler(BASE_DIR / "bot.log", encoding="utf-8")
]
if sys.stdout is not None:
    log_handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger("kyzylordahub_bot")


async def setup_bot_commands(bot: Bot) -> None:
    """Telegram қосымшасындағы меню командаларын орнату."""
    commands = [
        BotCommand(command="start", description="Басты мәзір / Промокод алу"),
        BotCommand(command="id", description="Өз Telegram ID-іңізді білу"),
    ]
    await bot.set_my_commands(commands)


# =========================================================================
# Render.com Free Web Service үшін Health-Check веб-сервері
# UptimeRobot осы сілтемені пингтеп, боттың 24/7 ұйықтамауын қамтамасыз етеді
# =========================================================================

import json

async def handle_health_check(request: web.Request) -> web.Response:
    """Веб-сервердің басты парақшасы."""
    return web.json_response({
        "status": "healthy",
        "service": "Kyzylorda Hub Telegram Bot",
        "bot": "@KYZYLORDAHUB_BOT",
        "message": "Бот белсенді жұмыс істеп тұр! 🚀"
    }, dumps=lambda obj: json.dumps(obj, ensure_ascii=False))


async def start_web_server() -> web.AppRunner | None:
    """Жеңіл веб-серверді белгіленген портта іске қосу."""
    port = int(os.getenv("PORT", "8080"))
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    app.router.add_get("/health", handle_health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    try:
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Health-check веб-сервері 0.0.0.0:{port} портында қосылды.")
        return runner
    except Exception as e:
        logger.warning(f"Веб-серверді 0.0.0.0:{port} портында іске қосу мүмкін болмады (ескерту): {e}")
        try:
            await runner.cleanup()
        except Exception:
            pass
        return None


async def keep_alive_ping_task(url: str, interval: int = 300) -> None:
    """Render 15 минуттан кейін ұйықтап қалмауы үшін өзінің сыртқы адресіне сұраныс жіберіп отыру (5 минут сайын)."""
    if not url:
        return
    ping_url = url.rstrip("/")
    if not ping_url.endswith("/health"):
        ping_url += "/health"

    # Бот пен веб-сервер толық оталып алуы үшін алғашқы 60 секунд күту
    await asyncio.sleep(60)
    logger.info(f"🚀 [Keep-Alive] Авто-пингер қосылды: {ping_url} (әр {interval // 60} мин сайын)")

    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(ping_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status == 200:
                            logger.info(f"✅ [Keep-Alive] Render сәтті пингтелді (код 200): {ping_url}")
                        else:
                            logger.warning(f"⚠️ [Keep-Alive] Пинг жауабы (код {resp.status}): {ping_url}")
                except Exception as e:
                    logger.warning(f"⚠️ [Keep-Alive] Пинг ескертуі: {e}")
                await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("[Keep-Alive] Авто-пингер тоқтатылды.")
    except Exception as e:
        logger.error(f"[Keep-Alive] Қате: {e}")


async def main() -> None:
    """Ботты баптап, іске қосу негізгі функциясы."""
    if not BOT_TOKEN:
        logger.critical(
            "ҚАТЕ: BOT_TOKEN табылмады! .env файлын тексеріңіз немесе токенді енгізіңіз."
        )
        sys.exit(1)

    logger.info("Деректер базасы тексерілуде...")
    await db.init_db()

    # Health-check веб-серверін іске қосу (Render үшін)
    web_runner = await start_web_server()

    # Render 24/7 ұйықтамауы үшін авто-пингер тапсырмасын қосу
    ping_task = None
    if RENDER_EXTERNAL_URL:
        ping_task = asyncio.create_task(keep_alive_ping_task(RENDER_EXTERNAL_URL, interval=300))

    # Бот пен Диспетчерді инициализациялау
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Роутерлерді тіркеу
    dp.include_router(main_router)

    # Меню командаларын қосу
    await setup_bot_commands(bot)

    if ADMIN_IDS:
        logger.info(f"Тіркелген админ ID-лері: {ADMIN_IDS}")

    # Бот туралы мәлімет алу
    bot_info = await bot.get_me()
    logger.info(f"Бот сәтті қосылды: @{bot_info.username} (ID: {bot_info.id})")

    # Вебхукты өшіріп, ескірген жаңартуларды тазалап поллингті бастау
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        if ping_task and not ping_task.done():
            ping_task.cancel()
        await bot.session.close()
        if web_runner:
            await web_runner.cleanup()
        logger.info("Бот жұмысын аяқтады.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот тоқтатылды.")

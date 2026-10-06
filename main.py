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

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, ADMIN_IDS
import database as db
from handlers import main_router

# Логирование баптауы
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
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

async def handle_health_check(request: web.Request) -> web.Response:
    """Веб-сервердің басты парақшасы."""
    return web.json_response({
        "status": "healthy",
        "service": "Kyzylorda Hub Telegram Bot",
        "bot": "@KYZYLORDAHUB_BOT",
        "message": "Бот белсенді жұмыс істеп тұр! 🚀"
    })


async def start_web_server() -> web.AppRunner:
    """Жеңіл веб-серверді белгіленген портта іске қосу."""
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    app.router.add_get("/health", handle_health_check)

    port = int(os.getenv("PORT", "8080"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check веб-сервері 0.0.0.0:{port} портында қосылды.")
    return runner


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

    # Ескі жаңартуларды тазалап, поллингті бастау
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await web_runner.cleanup()
        logger.info("Бот жұмысын аяқтады.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот тоқтатылды.")

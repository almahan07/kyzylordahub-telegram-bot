import asyncio
import logging
import sys

# Windows жүйесінде қазақша әріптер мен UTF-8 таңбалары қатесіз шығуы үшін
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
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
logger = logging.getLogger("antigraffiti_bot")


async def setup_bot_commands(bot: Bot) -> None:
    """Telegram қосымшасындағы меню командаларын орнату."""
    commands = [
        BotCommand(command="start", description="Басты мәзір / Промокод алу"),
        BotCommand(command="id", description="Өз Telegram ID-іңізді білу"),
    ]
    await bot.set_my_commands(commands)


async def main() -> None:
    """Ботты баптап, іске қосу негізгі функциясы."""
    if not BOT_TOKEN:
        logger.critical(
            "ҚАТЕ: BOT_TOKEN табылмады! .env файлын тексеріңіз немесе токенді енгізіңіз."
        )
        sys.exit(1)

    logger.info("Деректер базасы тексерілуде...")
    await db.init_db()

    # Бот пен Диспетчерді инициализациялау
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Роутерлерді тіркеу
    dp.include_router(main_router)

    # Меню командаларын қосу
    await setup_bot_commands(bot)

    # Админдер бар ма, соны логқа шығару
    if ADMIN_IDS:
        logger.info(f"Тіркелген админ ID-лері: {ADMIN_IDS}")
    else:
        logger.warning(
            "ЕСКЕРТУ: .env файлында ADMIN_IDS көрсетілмеген! Админ командалары жұмыс істемеуі мүмкін."
        )

    # Бот туралы мәлімет алу
    bot_info = await bot.get_me()
    logger.info(f"Бот сәтті қосылды: @{bot_info.username} (ID: {bot_info.id})")

    # Ескі жаңартуларды тазалап (drop_pending_updates), поллингті бастау
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот жұмысын аяқтады.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот тоқтатылды.")

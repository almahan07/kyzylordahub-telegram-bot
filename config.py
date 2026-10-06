import os
from pathlib import Path
from dotenv import load_dotenv

# Жоба каталогындағы .env файлын жүктеу
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Telegram бот токені
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Админ ID-лері тізімі
def _parse_admin_ids(ids_str: str) -> list[int]:
    result = []
    for item in ids_str.split(","):
        cleaned = item.strip()
        if cleaned.isdigit():
            result.append(int(cleaned))
    return result

ADMIN_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

# Instagram сілтемесі
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://www.instagram.com/kyzylordahub/")

# Курс өтетін негізгі платформа (Astana Hub)
COURSE_PLATFORM_URL = os.getenv("COURSE_PLATFORM_URL", "https://edu.astanahub.com/")

# Деректер базасы файлы
DB_NAME = os.getenv("DB_NAME", "antigraffiti.db")
DB_PATH = BASE_DIR / DB_NAME

# Render сыртқы сілтемесі (24/7 ұйықтамауы үшін)
RENDER_EXTERNAL_URL = os.getenv(
    "RENDER_EXTERNAL_URL",
    "https://kyzylordahub-telegram-bot-1.onrender.com"
)

# =========================================================================
# Kyzylorda Hub курстары мен промокодтары (Google Sheets дерегі бойынша)
# =========================================================================
COURSES: dict[str, dict] = {
    "course_nlc": {
        "title": "No Code / Low Code School",
        "code": "KYZYLORDA-HUB-NLC",
        "url": "https://edu.astanahub.com/courses/8d83f744-1846-43ea-bc2a-1b8a37084a2e",
        "limit": 100,
    },
    "course_sa": {
        "title": "Startup Academy",
        "code": "KYZYLORDA-HUB-SA",
        "url": "https://edu.astanahub.com/courses/cc946059-304e-450a-895b-e671db651cba",
        "limit": 100,
    },
    "course_ss": {
        "title": "Startup School",
        "code": "KYZYLORDA-HUB-SS",
        "url": "https://edu.astanahub.com/courses/f2159fbf-0ecf-43cb-9376-b7efc6fc7df5",
        "limit": 100,
    },
    "course_fs": {
        "title": "Freelance School",
        "code": "KYZYLORDA-HUB-FS",
        "url": "https://edu.astanahub.com/courses/3dcbfff1-1a89-4c9b-a2c3-c58c0425ac6d",
        "limit": 100,
    },
    "course_pe": {
        "title": "Prompt Engineering",
        "code": "KYZYLORDA-HUB-PE",
        "url": "https://edu.astanahub.com/courses/74b6914d-7e3b-4f52-b0ae-8f989e2294a7",
        "limit": 100,
    },
    "course_bc": {
        "title": "Beta Career",
        "code": "KYZYLORDA-HUB-BC",
        "url": "https://edu.astanahub.com/courses/c9d1629b-f2c2-40b8-9097-c92623ced30d",
        "limit": 100,
    },
}


def is_admin(user_id: int) -> bool:
    """Пайдаланушының админ екенін тексеру."""
    return user_id in ADMIN_IDS


def get_course_title(course_key: str) -> str:
    """Курс кілті бойынша толық атауын қайтару."""
    if course_key in COURSES:
        return COURSES[course_key]["title"]
    return course_key


def get_course_url(course_key: str) -> str:
    """Курс кілті бойынша оның edu.astanahub.com сайтындағы нақты сілтемесін қайтару."""
    if course_key in COURSES:
        return COURSES[course_key].get("url", COURSE_PLATFORM_URL)
    return COURSE_PLATFORM_URL


def get_course_code(course_key: str) -> str:
    """Курс кілті бойынша әдепкі промокодын қайтару."""
    if course_key in COURSES:
        return COURSES[course_key].get("code", "")
    return ""


def get_course_limit(course_key: str) -> int:
    """Курс лимитін қайтару (100)."""
    if course_key in COURSES:
        return COURSES[course_key].get("limit", 100)
    return 100

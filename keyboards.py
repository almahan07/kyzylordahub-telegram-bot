from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import COURSES, INSTAGRAM_URL, get_course_url


def get_courses_keyboard(claimed_keys: Optional[List[str]] = None) -> InlineKeyboardMarkup:
    """
    Kyzylorda Hub курстарының Inline батырмалары.
    claimed_keys берілсе, алынған курстар ✅ белгісімен көрсетіледі.
    """
    if claimed_keys is None:
        claimed_keys = []

    buttons = []
    icons = {
        "course_nlc": "💻",
        "course_sa": "🚀",
        "course_ss": "🎓",
        "course_fs": "💼",
        "course_pe": "🤖",
        "course_bc": "📈",
    }
    for course_key, data in COURSES.items():
        if course_key in claimed_keys:
            text = f"✅ {data['title']} (Алғансыз)"
        else:
            icon = icons.get(course_key, "📚")
            text = f"{icon} {data['title']}"

        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"select_course:{course_key}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subscribe_keyboard(course_key: str) -> InlineKeyboardMarkup:
    """Instagram-ға жазылу және промокод алу батырмалары."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📸 Instagram-ға өту (@kyzylordahub)",
                url=INSTAGRAM_URL
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Тіркелдім (Промокод алу)",
                callback_data=f"confirm_sub:{course_key}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Курстар тізіміне оралу",
                callback_data="back_to_courses"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админге арналған жылдам батырмалар."""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Статистика (/stats)", callback_data="admin_stats"),
            InlineKeyboardButton(text="📥 Промокод жүктеу (/upload)", callback_data="admin_upload"),
        ],
        [
            InlineKeyboardButton(text="📢 Хабарлама тарату (/broadcast)", callback_data="admin_broadcast"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Әрекетті тоқтату / бас тарту батырмасы."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Бас тарту", callback_data="cancel_action")
            ]
        ]
    )


def get_promocode_keyboard(course_key: str) -> InlineKeyboardMarkup:
    """
    Промокод алғанда шығатын батырмалар:
    1) edu.astanahub.com сайтындағы курсқа өту
    2) Басқа курстарға да промокод алу мүмкіндігі!
    """
    url = get_course_url(course_key)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Курсқа өту (edu.astanahub.com)",
                    url=url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Басқа курстарға промокод алу",
                    callback_data="back_to_courses",
                )
            ]
        ]
    )

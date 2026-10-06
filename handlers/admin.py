import csv
import io
import logging
from typing import List, Tuple
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from config import ADMIN_IDS, COURSES, is_admin, get_course_title, get_course_code
import database as db
import texts
from states import AdminUploadStates, AdminBroadcastStates
from keyboards import get_admin_keyboard, get_cancel_keyboard

logger = logging.getLogger(__name__)

router = Router(name="admin_router")


def format_courses_info() -> str:
    """Админге арналған курс кодтары тізімін құрастыру."""
    lines = []
    for key, data in COURSES.items():
        lines.append(f"• <code>{key}</code> — {data['title']} (Промокод: <code>{data['code']}</code>)")
    return "\n".join(lines)


# =========================================================================
# Бас тарту (/cancel) өңдеушісі
# =========================================================================

@router.message(Command("cancel"))
async def handle_cancel_cmd(message: Message, state: FSMContext) -> None:
    """Команда арқылы кез келген әрекеттен бас тарту."""
    if not is_admin(message.from_user.id):
        return
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Қазір белсенді әрекет жоқ.")
        return
    await state.clear()
    await message.answer(texts.ACTION_CANCELLED)


@router.callback_query(F.data == "cancel_action")
async def handle_cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Батырма арқылы әрекеттен бас тарту."""
    await callback.answer()
    await state.clear()
    if callback.message:
        await callback.message.edit_text(texts.ACTION_CANCELLED)


# =========================================================================
# Админ панелі (/admin)
# =========================================================================

@router.message(Command("admin"))
async def handle_admin_panel(message: Message) -> None:
    """Админ панелін шақыру."""
    if not is_admin(message.from_user.id):
        await message.answer(texts.ONLY_ADMINS)
        return
    await message.answer(texts.ADMIN_PANEL_TEXT, reply_markup=get_admin_keyboard(), parse_mode="HTML")


# =========================================================================
# Статистика (/stats)
# =========================================================================

async def send_stats_report(target: Message) -> None:
    """Статистика есебін құрастырып жіберу."""
    stats = await db.get_stats()
    text = texts.STATS_HEADER

    for course_key, data in stats["courses"].items():
        text += texts.STATS_COURSE_ITEM.format(
            course_title=get_course_title(course_key),
            code=get_course_code(course_key),
            total=data["total"],
            used=data["used"],
            available=data["available"],
        )

    text += texts.STATS_FOOTER.format(
        total_users=stats["total_users"],
        grand_total=stats["grand_total"],
        grand_used=stats["grand_used"],
        grand_available=stats["grand_available"],
    )

    await target.answer(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


@router.message(Command("stats"))
async def handle_stats_cmd(message: Message) -> None:
    """Статистика командасы."""
    if not is_admin(message.from_user.id):
        await message.answer(texts.ONLY_ADMINS)
        return
    await send_stats_report(message)


@router.callback_query(F.data == "admin_stats")
async def handle_stats_callback(callback: CallbackQuery) -> None:
    """Батырма арқылы статистиканы көру."""
    if not is_admin(callback.from_user.id):
        await callback.answer(texts.ONLY_ADMINS, show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await send_stats_report(callback.message)


# =========================================================================
# Промокодтарды жүктеу (/upload)
# =========================================================================

@router.message(Command("upload"))
async def handle_upload_cmd(message: Message, state: FSMContext) -> None:
    """Промокод файлын жүктеу командасы."""
    if not is_admin(message.from_user.id):
        await message.answer(texts.ONLY_ADMINS)
        return

    await state.set_state(AdminUploadStates.waiting_for_file)
    text = texts.UPLOAD_INSTRUCTION.format(courses_info=format_courses_info())
    await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "admin_upload")
async def handle_upload_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Батырма арқылы жүктеуді бастау."""
    if not is_admin(callback.from_user.id):
        await callback.answer(texts.ONLY_ADMINS, show_alert=True)
        return
    await callback.answer()
    await state.set_state(AdminUploadStates.waiting_for_file)
    text = texts.UPLOAD_INSTRUCTION.format(courses_info=format_courses_info())
    if callback.message:
        await callback.message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


def parse_promocodes_content(content: str) -> Tuple[List[Tuple[str, str]], int]:
    """
    CSV немесе мәтіндік файл мазмұнын талдау.
    Қолдау көрсетілетін форматтар:
    1) course_1,PROMO123
    2) course_1;PROMO123
    3) 1,PROMO123 (автоматты түрде course_1 болады)
    Қайтарады: (valid_items, error_rows_count)
    """
    valid_items: List[Tuple[str, str]] = []
    error_count = 0

    lines = content.strip().splitlines()
    for line_idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Бөлгішті анықтау (үтір, нүктелі үтір, қос нүкте немесе табуляция)
        parts = None
        for delimiter in [",", ";", "\t", ":"]:
            if delimiter in line:
                split_res = [p.strip() for p in line.split(delimiter, 1)]
                if len(split_res) == 2:
                    parts = split_res
                    break

        if not parts:
            error_count += 1
            continue

        raw_course, raw_code = parts[0], parts[1]

        # Бірінші жол Header болса (course, code) өткізіп жіберу
        if line_idx == 0 and raw_course.lower() in ["course", "course_id", "курс"] and raw_code.lower() in ["promocode", "code", "промокод"]:
            continue

        # Курс кілтін нормализациялау
        course_key = raw_course.lower()
        mapping = {
            "1": "course_nlc", "nlc": "course_nlc", "course_1": "course_nlc", "course_nlc": "course_nlc",
            "2": "course_sa", "sa": "course_sa", "course_2": "course_sa", "course_sa": "course_sa",
            "3": "course_ss", "ss": "course_ss", "course_3": "course_ss", "course_ss": "course_ss",
            "4": "course_fs", "fs": "course_fs", "course_4": "course_fs", "course_fs": "course_fs",
            "5": "course_pe", "pe": "course_pe", "course_5": "course_pe", "course_pe": "course_pe",
            "6": "course_bc", "bc": "course_bc", "course_6": "course_bc", "course_bc": "course_bc",
        }
        if course_key in mapping:
            course_key = mapping[course_key]

        # Жарамды курстар тізімінде бар ма тексереміз
        if course_key in COURSES and raw_code:
            valid_items.append((course_key, raw_code))
        else:
            error_count += 1

    return valid_items, error_count


@router.message(AdminUploadStates.waiting_for_file, F.document)
async def handle_document_upload(message: Message, state: FSMContext, bot: Bot) -> None:
    """Жүктелген файлды қабылдау және өңдеу."""
    document = message.document
    if not document:
        await message.answer("Файлды құжат (Document) ретінде жіберіңіз.")
        return

    # Файл көлемін тексеру (макс 10 МБ)
    if document.file_size and document.file_size > 10 * 1024 * 1024:
        await message.answer("Файл көлемі тым үлкен (максимум 10 MB).")
        return

    await message.answer("⏳ Файл жүктеліп жатыр, өңдеу басталды...")

    try:
        file_io = io.BytesIO()
        await bot.download(document, destination=file_io)
        file_bytes = file_io.getvalue()

        # Кодтауды (encoding) анықтау: utf-8 немесе cp1251
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("cp1251", errors="ignore")

        items, errors = parse_promocodes_content(content)

        if not items:
            await message.answer(texts.UPLOAD_NO_VALID_DATA)
            await state.clear()
            return

        added, duplicates = await db.add_promocodes(items)

        await message.answer(
            texts.UPLOAD_SUCCESS.format(
                added=added,
                duplicates=duplicates,
                errors=errors,
            ),
            parse_mode="HTML",
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Файлды өңдеу кезінде қате орын алды: {e}", exc_info=True)
        await message.answer(texts.UPLOAD_FILE_ERROR.format(error=str(e)), parse_mode="HTML")
        await state.clear()


@router.message(AdminUploadStates.waiting_for_file)
async def handle_upload_invalid_type(message: Message) -> None:
    """Егер файл орнына мәтін немесе басқа медиа жіберілсе."""
    await message.answer(
        "Файлды құжат (Document) түрінде жіберіңіз (.csv немесе .txt).\n"
        "Тоқтату үшін: /cancel",
        reply_markup=get_cancel_keyboard(),
    )


# =========================================================================
# Хабарлама тарату (/broadcast)
# =========================================================================

@router.message(Command("broadcast"))
async def handle_broadcast_cmd(message: Message, state: FSMContext) -> None:
    """Барлық пайдаланушыларға хабарлама тарату командасы."""
    if not is_admin(message.from_user.id):
        await message.answer(texts.ONLY_ADMINS)
        return

    await state.set_state(AdminBroadcastStates.waiting_for_message)
    await message.answer(texts.BROADCAST_INSTRUCTION, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "admin_broadcast")
async def handle_broadcast_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Батырма арқылы хабарлама таратуды бастау."""
    if not is_admin(callback.from_user.id):
        await callback.answer(texts.ONLY_ADMINS, show_alert=True)
        return
    await callback.answer()
    await state.set_state(AdminBroadcastStates.waiting_for_message)
    if callback.message:
        await callback.message.answer(
            texts.BROADCAST_INSTRUCTION,
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )


@router.message(AdminBroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot) -> None:
    """Таратылатын хабарламаны барлық қолданушыларға жолдау."""
    await state.clear()
    status_msg = await message.answer(texts.BROADCAST_STARTING)

    user_ids = await db.get_all_user_ids()
    total = len(user_ids)
    success = 0
    failed = 0

    for uid in user_ids:
        try:
            await message.copy_to(chat_id=uid)
            success += 1
        except TelegramAPIError as e:
            logger.warning(f"Пайдаланушыға ({uid}) хабар жіберілмеді: {e}")
            failed += 1

    await status_msg.edit_text(
        texts.BROADCAST_FINISHED.format(total=total, success=success, failed=failed),
        parse_mode="HTML",
    )

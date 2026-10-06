import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramAPIError

from config import INSTAGRAM_URL, ADMIN_IDS, get_course_title, get_course_url
import database as db
import texts
from keyboards import get_courses_keyboard, get_subscribe_keyboard, get_promocode_keyboard

logger = logging.getLogger(__name__)

router = Router(name="user_router")


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """
    /start командасын өңдеу.
    Пайдаланушы бірнеше курсқа промокод ала алады.
    Егер бұрын алған промокодтары болса, оларды тізімдеп көрсетеді
    және басқа курстарға да промокод алуды ұсынады.
    """
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Құрметті пайдаланушы"

    try:
        claimed_courses = await db.get_user_claimed_courses(user_id)
        claimed_keys = [c["course"] for c in claimed_courses]

        if claimed_courses:
            history_lines = []
            for c in claimed_courses:
                c_title = get_course_title(c["course"])
                history_lines.append(f"• <b>{c_title}</b>: <code>{c['promocode']}</code>")

            history_text = "\n".join(history_lines)
            text = texts.START_WITH_HISTORY.format(
                name=first_name,
                history_list=history_text,
            )
        else:
            text = texts.START_WELCOME.format(name=first_name)

        await message.answer(
            text,
            reply_markup=get_courses_keyboard(claimed_keys=claimed_keys),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"/start өңдеу кезінде қате: {e}", exc_info=True)
        await message.answer("Жүйеде уақытша қате орын алды. Қайта көріңіз.")


@router.message(F.text.in_(["/myid", "/id"]))
async def handle_my_id(message: Message) -> None:
    """Пайдаланушының өзінің Telegram ID-ін анықтау үшін көмекші команда."""
    user_id = message.from_user.id
    await message.answer(
        f"🆔 <b>Сіздің Telegram ID:</b> <code>{user_id}</code>\n\n"
        f"<i>Админ құқығын алу үшін осы ID-ді <code>.env</code> файлындағы <code>ADMIN_IDS=...</code> қатарына қойыңыз.</i>",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("select_course:"))
async def handle_select_course(callback: CallbackQuery) -> None:
    """
    Пайдаланушы курсты таңдаған кездегі логика.
    Егер дәл осы курсқа бұрын алған болса — оның промокодын көрсетеді.
    Егер әлі алмаған болса — Instagram шартын көрсетеді.
    """
    await callback.answer()
    user_id = callback.from_user.id
    course_key = callback.data.split(":", 1)[1]
    course_title = get_course_title(course_key)
    course_url = get_course_url(course_key)

    # Дәл осы курсқа бұрын промокод алған ба тексереміз
    existing_claim = await db.get_user_course_promo(user_id, course_key)
    if existing_claim:
        text = texts.ALREADY_REGISTERED_COURSE.format(
            course_title=course_title,
            promocode=existing_claim["promocode"],
            created_at=existing_claim["created_at"],
            course_url=course_url,
        )
        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=get_promocode_keyboard(course_key),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        return

    text = texts.SUBSCRIBE_REQUIRED.format(
        course_title=course_title,
        instagram_url=INSTAGRAM_URL,
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_subscribe_keyboard(course_key),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


@router.callback_query(F.data == "back_to_courses")
async def handle_back_to_courses(callback: CallbackQuery) -> None:
    """Курстар тізіміне қайта оралу (қайта таңдау немесе басқа курс алу)."""
    await callback.answer()
    user_id = callback.from_user.id
    claimed_courses = await db.get_user_claimed_courses(user_id)
    claimed_keys = [c["course"] for c in claimed_courses]

    if callback.message:
        await callback.message.edit_text(
            texts.CHOOSE_COURSE_AGAIN,
            reply_markup=get_courses_keyboard(claimed_keys=claimed_keys),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("confirm_sub:"))
async def handle_confirm_sub(callback: CallbackQuery) -> None:
    """
    'Тіркелдім' батырмасын басқанда:
    Таңдалған курсқа промокод беру.
    """
    await callback.answer()
    user_id = callback.from_user.id
    username = callback.from_user.username
    course_key = callback.data.split(":", 1)[1]
    course_title = get_course_title(course_key)
    course_url = get_course_url(course_key)

    try:
        success, promo, error_type = await db.claim_promocode(
            user_id=user_id,
            username=username,
            course_key=course_key,
        )

        if success and promo:
            # Сәтті берілді
            text = texts.PROMOCODE_SUCCESS.format(
                course_title=course_title,
                promocode=promo,
                course_url=course_url,
            )
            if callback.message:
                await callback.message.edit_text(
                    text,
                    reply_markup=get_promocode_keyboard(course_key),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )

        elif error_type == "already_claimed":
            # Дәл осы курсқа бұрын алып қойған
            existing = await db.get_user_course_promo(user_id, course_key)
            prev_promo = existing["promocode"] if existing else promo
            prev_date = existing["created_at"] if existing else "бұрын"

            text = texts.ALREADY_REGISTERED_COURSE.format(
                course_title=course_title,
                promocode=prev_promo,
                created_at=prev_date,
                course_url=course_url,
            )
            if callback.message:
                await callback.message.edit_text(
                    text,
                    reply_markup=get_promocode_keyboard(course_key),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )

        elif error_type == "out_of_stock":
            # Бұл курстың промокоды/лимиті таусылды
            if callback.message:
                await callback.message.edit_text(texts.OUT_OF_PROMOCODES, parse_mode="HTML")

            # Барлық админдерге дабыл жіберу
            alert_text = texts.ADMIN_ALERT_OUT_OF_PROMOCODES.format(
                course_title=course_title,
                course_key=course_key,
                username=username or "көрсетілмеген",
                user_id=user_id,
            )
            for admin_id in ADMIN_IDS:
                try:
                    await callback.bot.send_message(
                        chat_id=admin_id,
                        text=alert_text,
                        parse_mode="HTML",
                    )
                except TelegramAPIError as admin_err:
                    logger.warning(f"Админге ({admin_id}) ескерту жіберу мүмкін болмады: {admin_err}")

    except Exception as e:
        logger.error(f"Промокод беру барысында қате: {e}", exc_info=True)
        if callback.message:
            await callback.message.answer("Кешіріңіз, жүйеде қате орын алды. Қайта көріңіз.")

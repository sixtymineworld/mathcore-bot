import html
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, MenuButtonWebApp, Message, WebAppInfo

from app.bot.keyboards.inline import (
    get_grades_keyboard,
    get_home_keyboard,
    get_leaderboard_grades_keyboard,
    get_leaderboard_keyboard,
    get_profile_keyboard,
    get_subjects_keyboard,
    get_topics_keyboard,
    get_webapp_url,
)
from app.bot.states.user_state import UserState
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = Router(name="common")


async def update_user_chat_menu(bot: Bot, chat_id: int, tg_id: int) -> None:
    """Оновлює персональну кнопку меню в чаті із прямим токеном сесії користувача."""
    url = get_webapp_url(tg_id)
    if url:
        try:
            await bot.set_chat_menu_button(
                chat_id=chat_id,
                menu_button=MenuButtonWebApp(
                    text="застосунок",
                    web_app=WebAppInfo(url=url),
                ),
            )
        except Exception as e:
            logger.debug("не вдалося оновити menu button для чату %s: %s", chat_id, e)


def format_profile_message(profile: dict, safe_name: str, footer_hint: str) -> str:
    """Форматує картку профілю користувача."""
    return (
        f"<b>профіль: {safe_name}</b>\n"
        f"клас: {profile['grade']}\n"
        f"рівень: {profile['rank']}\n"
        f"набрано балів: <b>{profile.get('points', 0)}</b>\n\n"
        "<b>успішність:</b>\n"
        f"розв'язано завдань: {profile['solved_unique']}\n"
        f"точність: {profile['accuracy']}% {profile['progress_bar']}\n"
        f"всього спроб: {profile['total_attempts']}\n\n"
        "<b>активність:</b>\n"
        f"сьогодні розв'язано: {profile['today_solved']}\n"
        f"серія правильних відповідей: {profile['streak']}\n"
        f"з нами: {profile['days_registered']} дн.\n\n"
        f"<i>{footer_hint}</i>"
    )


def format_leaderboard_message(data: dict, safe_name: str, grade: int) -> str:
    """Форматує повідомлення рейтингу найкращих учнів класу."""
    top_users = data.get("top_users", [])
    if not top_users:
        return (
            f"<b>топ найкращих учнів ({grade} клас):</b>\n\n"
            "список лідерів для цього класу ще формується!\n"
            "розв'яжи завдання першим, щоб зайняти 1 місце в рейтингу свого класу."
        )

    lines = [f"<b>топ найкращих учнів ({grade} клас):</b>\n"]
    for u in top_users[:10]:
        user_name = html.escape(u.get("first_name") or "учень").lower()
        marker = " (ти)" if u.get("is_current_user") else ""
        lines.append(
            f"<b>{u['rank']}. {user_name}</b> — <b>{u['points']}</b> б. ({u['solved_tasks']} задач){marker}"
        )

    curr_rank = data.get("current_user_rank", 0)
    curr_pts = data.get("current_user_points", 0)
    curr_solved = data.get("current_user_solved", 0)

    lines.append("\n━━━━━━━━━━━━━━━━━━")
    if curr_rank > 0:
        lines.append(f"твоя позиція серед {grade} класу: <b>#{curr_rank}</b> · <b>{curr_pts}</b> б. ({curr_solved} задач)")
    else:
        lines.append(f"твоя позиція: ще не в рейтингу {grade} класу (розв'яжи завдання для нарахування балів)")

    return "\n".join(lines)


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """Обробник /start: реєструє або відновлює збережену сесію користувача."""
    tg_user = message.from_user
    if not tg_user:
        return

    if message.bot:
        await update_user_chat_menu(message.bot, message.chat.id, tg_user.id)

    existing_user = await TaskService.get_user_by_tg_id(tg_user.id)
    await TaskService.upsert_user(
        tg_id=tg_user.id,
        first_name=tg_user.first_name,
        username=tg_user.username,
    )

    safe_name = html.escape(tg_user.first_name)

    if existing_user and existing_user.grade:
        grade = existing_user.grade
        profile = await TaskService.get_user_profile(tg_user.id)
        welcome_text = (
            f"з поверненням, <b>{safe_name}</b>!\n\n"
            f"твоя сесія активна: <b>{grade} клас</b> · статус: <b>{profile.get('rank', 'дослідник')}</b>.\n"
            f"розв'язано завдань: <b>{profile.get('solved_unique', 0)}</b>.\n\n"
            "продовжуй навчання, відкривай міні-застосунок або переходь до списку тем:"
        )
        await state.set_state(UserState.viewing_topics)
        await message.answer(text=welcome_text, reply_markup=get_home_keyboard(grade, tg_id=tg_user.id))
        return

    welcome_text = (
        f"привіт, <b>{safe_name}</b>!\n\n"
        "вітаємо тебе в <b>mathcore</b> — твого інтерактивного "
        "аі-помічника зі шкільної математики!\n\n"
        "тут ти можеш тренуватись розв'язувати задачі, отримувати покрокові "
        "підказки від штучного інтелекту та легко опановувати складні теми.\n\n"
        "<b>вибери свій клас</b>, щоб налаштувати навчальну програму:"
    )
    await state.set_state(UserState.selecting_grade)
    await message.answer(text=welcome_text, reply_markup=get_grades_keyboard(tg_id=tg_user.id))


@router.callback_query(F.data.startswith("grade:"))
async def handle_grade_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробник CallbackQuery вибору класу."""
    if not callback.data or not callback.message:
        return

    try:
        grade = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("помилка обробки вибору класу.", show_alert=True)
        return

    tg_user = callback.from_user
    await TaskService.upsert_user(
        tg_id=tg_user.id,
        first_name=tg_user.first_name,
        username=tg_user.username,
        grade=grade,
    )
    if callback.bot and callback.message:
        await update_user_chat_menu(callback.bot, callback.message.chat.id, tg_user.id)
    await callback.answer(f"обрано {grade} клас")

    if grade >= 7:
        text = (
            f"<b>твій вибір: {grade} клас!</b>\n\n"
            "у 7–11 класах математика розділена на два предмети: <b>алгебру</b> та <b>геометрію</b>.\n"
            "вибери предмет, щоб відкрити його розділи:"
        )
        reply_markup = get_subjects_keyboard(grade, tg_id=tg_user.id)
    else:
        topics = await TaskService.get_topics_by_grade(grade)
        if topics:
            text = (
                f"<b>твій вибір: {grade} клас!</b>\n\n"
                "ось доступні навчальні розділи та теми за програмою.\n"
                "вибери тему, щоб розпочати тренування:"
            )
            reply_markup = get_topics_keyboard(topics, grade, tg_id=tg_user.id)
        else:
            text = (
                f"<b>твій вибір: {grade} клас!</b>\n\n"
                "для цього класу навчальні матеріали якраз наповнюються.\n"
                "ти можеш обрати інший клас нижче:"
            )
            reply_markup = get_grades_keyboard(tg_id=tg_user.id)

    await state.set_state(UserState.viewing_topics)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("subject:"))
async def handle_subject_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробник вибору предмета для 7-11 класів."""
    if not callback.data or not callback.message:
        return

    try:
        parts = callback.data.split(":")
        grade, subject = int(parts[1]), parts[2]
    except (IndexError, ValueError):
        await callback.answer("помилка вибору предмета.", show_alert=True)
        return

    tg_user = callback.from_user
    topics = await TaskService.get_topics_by_grade(grade, subject=subject)
    await state.set_state(UserState.viewing_topics)
    await callback.answer(f"обрано: {subject}")

    sections: dict[str, list[str]] = {}
    for t in topics:
        sections.setdefault(t.section, []).append(t.title)

    sections_text = "\n\n".join(
        f"<b>{sec}:</b>\n  • " + "\n  • ".join(titles) for sec, titles in sections.items()
    )

    text = f"<b>{grade} клас · {subject}</b>\n\n{sections_text}\n\nвибери тему для тренування нижче:"
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_topics_keyboard(topics, grade, subject=subject, tg_id=tg_user.id),
        )


@router.callback_query(F.data == "change_grade")
async def handle_change_grade(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка для зміни обраного класу."""
    tg_user = callback.from_user
    await callback.answer()
    await state.set_state(UserState.selecting_grade)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="<b>вибери свій клас</b> для налаштування програми:",
            reply_markup=get_grades_keyboard(tg_id=tg_user.id),
        )


@router.message(Command("topics", "menu"))
async def handle_topics_command(message: Message, state: FSMContext) -> None:
    """Команда /topics або /menu для швидкого доступу до списку тем."""
    tg_user = message.from_user
    if not tg_user:
        return

    if message.bot:
        await update_user_chat_menu(message.bot, message.chat.id, tg_user.id)

    user = await TaskService.get_user_by_tg_id(tg_user.id)
    if not user or not user.grade:
        await message.answer("спочатку вибери свій клас через команду /start.")
        return

    topics = await TaskService.get_topics_by_grade(user.grade)
    await state.set_state(UserState.viewing_topics)
    await message.answer(
        text=f"<b>навчальні теми для {user.grade} класу:</b>\nвибери тему для тренування:",
        reply_markup=get_topics_keyboard(topics, user.grade, tg_id=tg_user.id),
    )


@router.message(Command("stats", "profile"))
async def handle_stats_command(message: Message) -> None:
    """Команда /stats або /profile для перегляду успішності."""
    tg_user = message.from_user
    if not tg_user:
        return

    if message.bot:
        await update_user_chat_menu(message.bot, message.chat.id, tg_user.id)

    profile = await TaskService.get_user_profile(tg_user.id)
    if not profile["grade"]:
        await message.answer("спочатку вибери свій клас через команду /start.")
        return

    safe_name = html.escape(profile["first_name"] or tg_user.first_name or "учень").lower()
    text = format_profile_message(profile, safe_name, "продовжуй тренуватись через /topics")
    await message.answer(text=text, reply_markup=get_profile_keyboard(profile["grade"], tg_id=tg_user.id))


@router.callback_query(F.data.in_({"my_profile", "my_stats"}))
async def handle_profile_callback(callback: CallbackQuery) -> None:
    """Кнопка 'профіль та успішність' з меню тем."""
    tg_user = callback.from_user
    profile = await TaskService.get_user_profile(tg_user.id)
    await callback.answer()

    if not profile["grade"]:
        await callback.answer("спочатку вибери клас", show_alert=True)
        return

    safe_name = html.escape(profile["first_name"] or tg_user.first_name or "учень").lower()
    text = format_profile_message(profile, safe_name, "вибирай тему та покращуй результат:")
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=get_profile_keyboard(profile["grade"], tg_id=tg_user.id))


@router.message(Command("top", "leaderboard"))
async def handle_leaderboard_command(message: Message) -> None:
    """Команда /top або /leaderboard для перегляду рейтингу учнів за класом."""
    tg_user = message.from_user
    if not tg_user:
        return

    if message.bot:
        await update_user_chat_menu(message.bot, message.chat.id, tg_user.id)

    user = await TaskService.get_user_by_tg_id(tg_user.id)
    grade = user.grade if user and user.grade else 7
    data = await TaskService.get_leaderboard(current_tg_id=tg_user.id, grade=grade, limit=10)
    safe_name = html.escape(tg_user.first_name).lower()
    text = format_leaderboard_message(data, safe_name, grade)
    await message.answer(text=text, reply_markup=get_leaderboard_keyboard(grade, tg_id=tg_user.id))


@router.callback_query(F.data.startswith("lb_grade:"))
async def handle_leaderboard_grade_callback(callback: CallbackQuery) -> None:
    """Перегляд рейтингу для обраного класу."""
    tg_user = callback.from_user
    try:
        grade = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        grade = 7

    data = await TaskService.get_leaderboard(current_tg_id=tg_user.id, grade=grade, limit=10)
    safe_name = html.escape(tg_user.first_name).lower()
    text = format_leaderboard_message(data, safe_name, grade)
    await callback.answer(f"топ для {grade} класу")
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=get_leaderboard_keyboard(grade, tg_id=tg_user.id))


@router.callback_query(F.data.startswith("lb_select_grade"))
async def handle_select_leaderboard_grade(callback: CallbackQuery) -> None:
    """Вибір класу для перегляду рейтингу."""
    try:
        current_grade = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        current_grade = 7

    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text="<b>вибери клас</b> для перегляду рейтингу:",
            reply_markup=get_leaderboard_grades_keyboard(current_grade),
        )


@router.callback_query(F.data == "leaderboard")
async def handle_leaderboard_callback(callback: CallbackQuery) -> None:
    """Кнопка 'топ учнів' (за замовчуванням клас користувача)."""
    tg_user = callback.from_user
    user = await TaskService.get_user_by_tg_id(tg_user.id)
    grade = user.grade if user and user.grade else 7
    data = await TaskService.get_leaderboard(current_tg_id=tg_user.id, grade=grade, limit=10)
    safe_name = html.escape(tg_user.first_name).lower()
    text = format_leaderboard_message(data, safe_name, grade)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=get_leaderboard_keyboard(grade, tg_id=tg_user.id))

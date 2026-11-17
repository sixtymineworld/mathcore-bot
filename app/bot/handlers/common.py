import html
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.inline import (
    get_grades_keyboard,
    get_profile_keyboard,
    get_stats_keyboard,
    get_subjects_keyboard,
    get_topics_keyboard,
)
from app.bot.states.user_state import UserState
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = Router(name="common")


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """Обробник команди /start.

    Реєструє або оновлює користувача в базі даних та пропонує обрати клас.
    """
    logger.info("Отримано команду /start від користувача: %s", message.from_user.id if message.from_user else "unknown")
    tg_user = message.from_user
    if not tg_user:
        return

    # Збереження/оновлення користувача в базі даних через сервіс
    await TaskService.upsert_user(
        tg_id=tg_user.id,
        first_name=tg_user.first_name,
        username=tg_user.username,
    )

    safe_name = html.escape(tg_user.first_name)
    welcome_text = (
        f"привіт, <b>{safe_name}</b>!\n\n"
        "вітаємо тебе в <b>mathcore</b> — твого інтерактивного "
        "аі-помічника зі шкільної математики!\n\n"
        "тут ти можеш тренуватись розв'язувати задачі, отримувати покрокові "
        "підказки від штучного інтелекту та легко опановувати складні теми.\n\n"
        "<b>вибери свій клас</b>, щоб налаштувати навчальну програму:"
    )

    await state.set_state(UserState.selecting_grade)
    await message.answer(
        text=welcome_text,
        reply_markup=get_grades_keyboard(),
    )


@router.callback_query(F.data.startswith("grade:"))
async def handle_grade_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробник CallbackQuery вибору класу.

    Оновлює клас користувача та одразу відкриває список тем для цього класу.
    """
    if not callback.data or not callback.message:
        return

    try:
        grade = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("Помилка обробки вибору класу.", show_alert=True)
        return

    tg_user = callback.from_user

    # Оновлення класу користувача в базі даних
    await TaskService.upsert_user(
        tg_id=tg_user.id,
        first_name=tg_user.first_name,
        username=tg_user.username,
        grade=grade,
    )
    logger.info("Користувач tg_id=%s обрав %s клас", tg_user.id, grade)

    await callback.answer(f"обрано {grade} клас")

    # Якщо клас 7-11, пропонуємо обрати предмет (алгебра або геометрія)
    if grade >= 7:
        text = (
            f"<b>твій вибір: {grade} клас!</b>\n\n"
            "у 7–11 класах математика розділена на два предмети: <b>алгебру</b> та <b>геометрію</b>.\n"
            "вибери предмет, щоб відкрити його розділи:"
        )
        reply_markup = get_subjects_keyboard(grade)
    else:
        # Завантаження тем для початкової та середньої школи (1-6 класи)
        topics = await TaskService.get_topics_by_grade(grade)
        if topics:
            text = (
                f"<b>твій вибір: {grade} клас!</b>\n\n"
                "ось доступні навчальні розділи та теми за програмою.\n"
                "вибери тему, щоб розпочати тренування:"
            )
            reply_markup = get_topics_keyboard(topics, grade)
        else:
            text = (
                f"<b>твій вибір: {grade} клас!</b>\n\n"
                "для цього класу навчальні матеріали якраз наповнюються.\n"
                "ти можеш обрати інший клас за допомогою кнопки нижче:"
            )
            reply_markup = get_grades_keyboard()

    await state.set_state(UserState.viewing_topics)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
        )


@router.callback_query(F.data.startswith("subject:"))
async def handle_subject_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробник вибору предмета (алгебра або геометрія) для 7-11 класів."""
    if not callback.data or not callback.message:
        return

    try:
        parts = callback.data.split(":")
        grade = int(parts[1])
        subject = parts[2]
    except (IndexError, ValueError):
        await callback.answer("помилка вибору предмета.", show_alert=True)
        return

    topics = await TaskService.get_topics_by_grade(grade, subject=subject)
    await state.set_state(UserState.viewing_topics)
    await callback.answer(f"обрано: {subject}")

    # Групуємо теми за розділами для охайного списку
    sections: dict[str, list[str]] = {}
    for t in topics:
        sections.setdefault(t.section, []).append(t.title)

    sections_lines = []
    for sec, titles in sections.items():
        bullet_list = "\n  • ".join(titles)
        sections_lines.append(f"<b>{sec}:</b>\n  • {bullet_list}")

    sections_text = "\n\n".join(sections_lines)

    text = (
        f"<b>{grade} клас · {subject}</b>\n\n"
        f"{sections_text}\n\n"
        "вибери тему для тренування на кнопках нижче:"
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_topics_keyboard(topics, grade, subject=subject),
        )


@router.callback_query(F.data == "change_grade")
async def handle_change_grade(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка для зміни обраного класу."""
    await callback.answer()
    await state.set_state(UserState.selecting_grade)

    text = "<b>вибери свій клас</b> для налаштування програми:"
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_grades_keyboard(),
        )


@router.message(Command("topics", "menu"))
async def handle_topics_command(message: Message, state: FSMContext) -> None:
    """Команда /topics або /menu для швидкого доступу до списку тем."""
    tg_user = message.from_user
    if not tg_user:
        return

    user = await TaskService.get_user_by_tg_id(tg_user.id)
    if not user or not user.grade:
        await message.answer(
            "будь ласка, спочатку оберіть свій клас за допомогою команди /start."
        )
        return

    topics = await TaskService.get_topics_by_grade(user.grade)
    await state.set_state(UserState.viewing_topics)

    await message.answer(
        text=f"<b>навчальні теми для {user.grade} класу:</b>\nвиберіть тему для тренування:",
        reply_markup=get_topics_keyboard(topics, user.grade),
    )


@router.message(Command("stats", "profile"))
async def handle_stats_command(message: Message) -> None:
    """Команда /stats або /profile для перегляду успішності та активності."""
    tg_user = message.from_user
    if not tg_user:
        return

    profile = await TaskService.get_user_profile(tg_user.id)
    if not profile["grade"]:
        await message.answer("спочатку вибери свій клас через команду /start.")
        return

    safe_name = html.escape(profile["first_name"] or tg_user.first_name or "учень").lower()
    text = (
        f"<b>профіль: {safe_name}</b>\n"
        f"клас: {profile['grade']}\n"
        f"рівень: {profile['rank']}\n\n"
        "<b>успішність:</b>\n"
        f"розв'язано завдань: {profile['solved_unique']}\n"
        f"точність: {profile['accuracy']}% {profile['progress_bar']}\n"
        f"всього спроб: {profile['total_attempts']}\n\n"
        "<b>активність:</b>\n"
        f"сьогодні розв'язано: {profile['today_solved']}\n"
        f"серія правильних відповідей: {profile['streak']}\n"
        f"з нами: {profile['days_registered']} дн.\n\n"
        "<i>продовжуй тренуватись через /topics</i>"
    )
    await message.answer(
        text=text,
        reply_markup=get_profile_keyboard(profile["grade"]),
    )


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
    text = (
        f"<b>профіль: {safe_name}</b>\n"
        f"клас: {profile['grade']}\n"
        f"рівень: {profile['rank']}\n\n"
        "<b>успішність:</b>\n"
        f"розв'язано завдань: {profile['solved_unique']}\n"
        f"точність: {profile['accuracy']}% {profile['progress_bar']}\n"
        f"всього спроб: {profile['total_attempts']}\n\n"
        "<b>активність:</b>\n"
        f"сьогодні розв'язано: {profile['today_solved']}\n"
        f"серія правильних відповідей: {profile['streak']}\n"
        f"з нами: {profile['days_registered']} дн.\n\n"
        "<i>вибирай тему та покращуй результат:</i>"
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_profile_keyboard(profile["grade"]),
        )

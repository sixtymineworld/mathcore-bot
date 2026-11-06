import html
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.inline import get_grades_keyboard, get_topics_keyboard
from app.bot.states.user_state import UserState
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = Router(name="common")


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """Обробник команди /start.

    Реєструє або оновлює користувача в базі даних та пропонує обрати клас.
    """
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
        f"👋 Привіт, <b>{safe_name}</b>!\n\n"
        "Ласкаво просимо до <b>mathcore</b> — твого інтерактивного "
        "AI-помічника зі шкільної математики! 📐\n\n"
        "Тут ти можеш тренуватись розв'язувати задачі, отримувати покрокові "
        "підказки від штучного інтелекту та легко опановувати складні теми.\n\n"
        "👇 <b>Обери свій клас</b>, щоб налаштувати навчальну програму:"
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

    await callback.answer(f"Обрано {grade} клас! ✅")

    # Завантаження тем для обраного класу
    topics = await TaskService.get_topics_by_grade(grade)

    if topics:
        text = (
            f"🎓 <b>Твій вибір: {grade} клас!</b>\n\n"
            "Ось доступні навчальні теми за шкільною програмою.\n"
            "Обери тему, щоб розпочати тренування:"
        )
        reply_markup = get_topics_keyboard(topics, grade)
    else:
        text = (
            f"🎓 <b>Твій вибір: {grade} клас!</b>\n\n"
            "Для цього класу навчальні матеріали якраз наповнюються.\n"
            "Ти можеш обрати інший клас за допомогою кнопки нижче:"
        )
        reply_markup = get_grades_keyboard()

    await state.set_state(UserState.viewing_topics)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
        )


@router.callback_query(F.data == "change_grade")
async def handle_change_grade(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка для зміни обраного класу."""
    await callback.answer()
    await state.set_state(UserState.selecting_grade)

    text = "👇 <b>Обери свій клас</b> для налаштування програми:"
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
            "Будь ласка, спочатку оберіть свій клас за допомогою команди /start."
        )
        return

    topics = await TaskService.get_topics_by_grade(user.grade)
    await state.set_state(UserState.viewing_topics)

    await message.answer(
        text=f"📚 <b>Навчальні теми для {user.grade} класу:</b>\nОберіть тему для тренування:",
        reply_markup=get_topics_keyboard(topics, user.grade),
    )

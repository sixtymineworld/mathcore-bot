import html
import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.bot.keyboards.inline import get_grades_keyboard
from app.bot.states.user_state import UserState
from app.db.base import get_session
from app.db.models import User

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

    # Збереження/оновлення користувача в базі даних
    async with get_session() as session:
        stmt = select(User).where(User.tg_id == tg_user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if db_user is None:
            db_user = User(
                tg_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                grade=None,
            )
            session.add(db_user)
            logger.info("Створено нового користувача: tg_id=%s", tg_user.id)
        else:
            db_user.username = tg_user.username
            db_user.first_name = tg_user.first_name
            logger.info("Оновлено дані користувача: tg_id=%s", tg_user.id)

        await session.commit()

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

    Оновлює вибраний клас користувача в базі даних та підтверджує вибір.
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
    async with get_session() as session:
        stmt = select(User).where(User.tg_id == tg_user.id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if db_user:
            db_user.grade = grade
            db_user.username = tg_user.username
            db_user.first_name = tg_user.first_name
        else:
            db_user = User(
                tg_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                grade=grade,
            )
            session.add(db_user)

        await session.commit()
        logger.info(
            "Користувач tg_id=%s обрав %s клас",
            tg_user.id,
            grade,
        )

    await callback.answer(f"Обрано {grade} клас! ✅")

    success_text = (
        f"🎓 <b>Твій вибір збережено: {grade} клас!</b>\n\n"
        "Чудово! Навчальну програму та складність завдань налаштовано "
        "відповідно до твого рівня.\n\n"
        "🤖 Незабаром тут з'являться інтерактивні завдання, генерація "
        "прикладів від AI та інтерфейс <b>Telegram Mini App (TMA)</b>.\n\n"
        "<i>💡 Якщо ти перейдеш у наступний клас або захочеш повторити "
        "попередній матеріал — просто надішли команду /start знову.</i>"
    )

    await state.clear()

    # Оновлюємо поточне повідомлення з інлайн-кнопками
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=success_text,
            reply_markup=None,
        )

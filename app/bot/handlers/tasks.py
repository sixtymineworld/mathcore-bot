import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.inline import get_task_keyboard, get_topics_keyboard
from app.bot.states.user_state import UserState
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = Router(name="tasks")


def format_difficulty(level: int) -> str:
    """Форматує рівень складності у вигляді зірочок."""
    return "⭐" * max(1, min(level, 3))


@router.callback_query(F.data.startswith("topics_list:"))
async def handle_back_to_topics(callback: CallbackQuery, state: FSMContext) -> None:
    """Повернення до списку тем для вказаного класу."""
    if not callback.data or not callback.message:
        return

    try:
        grade = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("Помилка навігації.", show_alert=True)
        return

    topics = await TaskService.get_topics_by_grade(grade)
    await state.set_state(UserState.viewing_topics)
    await callback.answer()

    text = f"📚 <b>Навчальні теми для {grade} класу:</b>\nОберіть тему для тренування:"
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_topics_keyboard(topics, grade),
        )


@router.callback_query(F.data.startswith("topic:"))
async def handle_topic_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробник вибору конкретної теми. Відкриває перше завдання теми."""
    if not callback.data or not callback.message:
        return

    try:
        topic_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("Помилка вибору теми.", show_alert=True)
        return

    topic = await TaskService.get_topic_by_id(topic_id)
    if not topic:
        await callback.answer("Тему не знайдено.", show_alert=True)
        return

    tasks = await TaskService.get_tasks_by_topic(topic_id)
    if not tasks:
        await callback.answer("Завдання для цієї теми ще готуються!", show_alert=True)
        return

    first_task = tasks[0]
    await callback.answer()

    stars = format_difficulty(first_task.difficulty)
    text = (
        f"📖 <b>Тема:</b> {topic.title}\n"
        f"🎯 <b>Завдання:</b> {first_task.title} (Складність: {stars})\n\n"
        f"{first_task.question_text}\n\n"
        "<i>Натисніть кнопку нижче, щоб дати відповідь або отримати підказку від AI:</i>"
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_task_keyboard(
                task_id=first_task.id,
                topic_id=topic.id,
                grade=topic.grade,
            ),
        )


@router.callback_query(F.data.startswith("task:"))
async def handle_task_view(callback: CallbackQuery, state: FSMContext) -> None:
    """Відображення конкретного завдання за task_id."""
    if not callback.data or not callback.message:
        return

    try:
        task_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("Помилка відкриття завдання.", show_alert=True)
        return

    task = await TaskService.get_task_by_id(task_id)
    if not task:
        await callback.answer("Завдання не знайдено.", show_alert=True)
        return

    topic = await TaskService.get_topic_by_id(task.topic_id)
    grade = topic.grade if topic else 5
    topic_title = topic.title if topic else "Математика"

    await callback.answer()

    stars = format_difficulty(task.difficulty)
    text = (
        f"📖 <b>Тема:</b> {topic_title}\n"
        f"🎯 <b>Завдання:</b> {task.title} (Складність: {stars})\n\n"
        f"{task.question_text}\n\n"
        "<i>Натисніть кнопку нижче, щоб дати відповідь або отримати підказку від AI:</i>"
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            reply_markup=get_task_keyboard(
                task_id=task.id,
                topic_id=task.topic_id,
                grade=grade,
            ),
        )

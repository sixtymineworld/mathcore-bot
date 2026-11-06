import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.inline import (
    get_task_keyboard,
    get_task_navigation_keyboard,
    get_topics_keyboard,
)
from app.bot.states.user_state import UserState
from app.services.ai_checker import get_ai_checker
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = Router(name="tasks")


def format_difficulty(level: int) -> str:
    """Форматує рівень складності."""
    return f"{max(1, min(level, 3))}/3"


@router.callback_query(F.data.startswith("topics_list:"))
async def handle_back_to_topics(callback: CallbackQuery, state: FSMContext) -> None:
    """Повернення до списку тем для вказаного класу."""
    if not callback.data or not callback.message:
        return

    try:
        grade = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("помилка навігації.", show_alert=True)
        return

    topics = await TaskService.get_topics_by_grade(grade)
    await state.set_state(UserState.viewing_topics)
    await callback.answer()

    text = f"<b>навчальні теми для {grade} класу:</b>\nвибери тему для тренування:"
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
        await callback.answer("помилка вибору теми.", show_alert=True)
        return

    topic = await TaskService.get_topic_by_id(topic_id)
    if not topic:
        await callback.answer("тему не знайдено.", show_alert=True)
        return

    tasks = await TaskService.get_tasks_by_topic(topic_id)
    if not tasks:
        await callback.answer("завдання для цієї теми ще готуються!", show_alert=True)
        return

    first_task = tasks[0]
    await callback.answer()

    stars = format_difficulty(first_task.difficulty)
    text = (
        f"<b>тема:</b> {topic.title}\n"
        f"<b>завдання:</b> {first_task.title} (складність: {stars})\n\n"
        f"{first_task.question_text}\n\n"
        "<i>вибирай дію нижче:</i>"
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
        await callback.answer("помилка відкриття завдання.", show_alert=True)
        return

    task = await TaskService.get_task_by_id(task_id)
    if not task:
        await callback.answer("завдання не знайдено.", show_alert=True)
        return

    topic = await TaskService.get_topic_by_id(task.topic_id)
    grade = topic.grade if topic else 5
    topic_title = topic.title if topic else "математика"

    await callback.answer()

    stars = format_difficulty(task.difficulty)
    text = (
        f"<b>тема:</b> {topic_title}\n"
        f"<b>завдання:</b> {task.title} (складність: {stars})\n\n"
        f"{task.question_text}\n\n"
        "<i>вибирай дію нижче:</i>"
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


@router.callback_query(F.data.startswith("solve:"))
async def handle_solve_task(callback: CallbackQuery, state: FSMContext) -> None:
    """Переводить користувача в стан очікування відповіді на завдання."""
    if not callback.data or not callback.message:
        return

    try:
        task_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("помилка ініціалізації розв'язку.", show_alert=True)
        return

    task = await TaskService.get_task_by_id(task_id)
    if not task:
        await callback.answer("завдання не знайдено.", show_alert=True)
        return

    await state.update_data(current_task_id=task_id)
    await state.set_state(UserState.solving_task)
    await callback.answer()

    prompt_text = (
        f"<b>розв'язуємо:</b> {task.title}\n\n"
        f"{task.question_text}\n\n"
        "надішли свою відповідь повідомленням нижче:\n"
        "<i>(наприклад: <code>4</code>, <code>5/7</code> або <code>30</code>)</i>"
    )

    if isinstance(callback.message, Message):
        await callback.message.answer(text=prompt_text)


@router.callback_query(F.data.startswith("hint:"))
async def handle_hint_task(callback: CallbackQuery) -> None:
    """Надає користувачу підказку до поточного завдання через AI-сервіс."""
    if not callback.data or not callback.message:
        return

    try:
        task_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("помилка отримання підказки.", show_alert=True)
        return

    task = await TaskService.get_task_by_id(task_id)
    if not task:
        await callback.answer("завдання не знайдено.", show_alert=True)
        return

    topic = await TaskService.get_topic_by_id(task.topic_id)
    grade = topic.grade if topic else 5

    ai_checker = get_ai_checker()
    hint_text = await ai_checker.get_hint(
        task_question=task.question_text,
        grade=grade,
        custom_hint=task.solution_hint,
    )

    await callback.answer("підказку згенеровано")
    if isinstance(callback.message, Message):
        await callback.message.answer(text=hint_text)


@router.message(UserState.solving_task, F.text)
async def handle_user_answer(message: Message, state: FSMContext) -> None:
    """Обробляє надіслану учнем відповідь, перевіряє її через AI та повертає результат."""
    if not message.text:
        return

    data = await state.get_data()
    task_id = data.get("current_task_id")

    if not task_id:
        await message.answer(
            "не вдалося визначити поточне завдання. вибери тему заново через /topics."
        )
        await state.clear()
        return

    task = await TaskService.get_task_by_id(task_id)
    if not task:
        await message.answer("завдання не знайдено в базі даних.")
        await state.clear()
        return

    topic = await TaskService.get_topic_by_id(task.topic_id)
    grade = topic.grade if topic else 5

    ai_checker = get_ai_checker()
    result = await ai_checker.check_solution(
        task_question=task.question_text,
        user_answer=message.text,
        correct_answer=task.correct_answer,
        grade=grade,
    )

    next_task = await TaskService.get_next_task(
        topic_id=task.topic_id,
        current_task_id=task.id,
    )

    reply_markup = get_task_navigation_keyboard(
        next_task_id=next_task.id if next_task else None,
        current_task_id=task.id,
        topic_id=task.topic_id,
        grade=grade,
        is_correct=result.is_correct,
    )

    if result.is_correct:
        response_text = (
            f"{result.feedback}\n\n"
            f"<i>{result.detailed_solution}</i>\n\n"
            "що робимо далі? вибирай дію нижче:"
        )
    else:
        response_text = (
            f"{result.feedback}\n\n"
            "спробуй ще раз або візьми підказку:"
        )

    await state.clear()
    await message.answer(
        text=response_text,
        reply_markup=reply_markup,
    )

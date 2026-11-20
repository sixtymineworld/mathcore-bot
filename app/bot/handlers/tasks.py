import json
import logging
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.inline import (
    get_subjects_keyboard,
    get_task_keyboard,
    get_task_navigation_keyboard,
    get_topics_keyboard,
)
from app.bot.states.user_state import UserState
from app.services.ai_checker import get_ai_checker
from app.services.task_service import TaskService

if TYPE_CHECKING:
    from app.db.models import Task

logger = logging.getLogger(__name__)
router = Router(name="tasks")


def render_task_view(
    task: "Task",
    topic_title: str,
    grade: int,
    tg_id: int | None = None,
) -> tuple[str, object]:
    """Формує текст повідомлення та клавіатуру для перегляду завдання."""
    stars = f"{max(1, min(task.difficulty, 3))}/3"
    nmt_badge = " [формат нмт]" if task.is_nmt else ""
    quiz_badge = " [квіз]" if task.is_quiz else ""
    diagram_notice = (
        "\n<i>(до цього завдання є креслення — відкрий його у веб-додатку нижче)</i>\n"
        if task.diagram_svg
        else ""
    )

    quiz_options_text = ""
    if task.is_quiz and task.options:
        letters = ["а", "б", "в", "г", "д"]
        opts_lines = [f"<b>{letters[i]})</b> {opt}" for i, opt in enumerate(task.options[:4])]
        quiz_options_text = "\n\n<b>варіанти відповідей:</b>\n" + "\n".join(opts_lines)

    text = (
        f"<b>тема:</b> {topic_title}\n"
        f"<b>завдання:</b> {task.title}{nmt_badge}{quiz_badge} (складність: {stars})\n\n"
        f"{task.question_text}\n"
        f"{quiz_options_text}"
        f"{diagram_notice}\n"
        "<i>вибирай дію нижче:</i>"
    )
    keyboard = get_task_keyboard(
        task_id=task.id,
        topic_id=task.topic_id,
        grade=grade,
        has_diagram=bool(task.diagram_svg),
        tg_id=tg_id,
        is_quiz=task.is_quiz,
        options=task.options,
    )
    return text, keyboard


async def generate_and_show_task(callback: CallbackQuery, topic_id: int) -> None:
    """Генерує за темою нове завдання та показує його учневі."""
    topic = await TaskService.get_topic_by_id(topic_id)
    if not topic:
        await callback.answer("тему не знайдено.", show_alert=True)
        return

    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("<i>генерую нове завдання за темою...</i>")

    ai_checker = get_ai_checker()
    generated = await ai_checker.generate_task(grade=topic.grade, topic=topic.title)

    options_json = (
        json.dumps(generated.options, ensure_ascii=False)
        if (generated.is_quiz and generated.options)
        else None
    )

    task = await TaskService.create_generated_task(
        topic_id=topic.id,
        title=generated.title,
        question_text=generated.question,
        solution_hint=generated.hint,
        correct_answer=generated.correct_answer,
        difficulty=generated.difficulty,
        diagram_svg=generated.diagram_svg,
        is_nmt=generated.is_nmt,
        detailed_solution=generated.detailed_solution,
        is_quiz=generated.is_quiz,
        options_json=options_json,
    )

    text, markup = render_task_view(task, topic.title, topic.grade, tg_id=callback.from_user.id)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=markup)


@router.callback_query(F.data.startswith("topics_list:"))
async def handle_back_to_topics(callback: CallbackQuery, state: FSMContext) -> None:
    """Повернення до списку тем або предметів для вказаного класу."""
    if not callback.data or not callback.message:
        return

    try:
        grade = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("помилка навігації.", show_alert=True)
        return

    await state.set_state(UserState.viewing_topics)
    await callback.answer()
    tg_id = callback.from_user.id

    if grade >= 7:
        text = f"<b>{grade} клас</b>\n\nвибери предмет (алгебра або геометрія), щоб відкрити його розділи:"
        reply_markup = get_subjects_keyboard(grade, tg_id=tg_id)
    else:
        topics = await TaskService.get_topics_by_grade(grade)
        text = f"<b>навчальні розділи та теми для {grade} класу:</b>\nвибери тему для тренування:"
        reply_markup = get_topics_keyboard(topics, grade, tg_id=tg_id)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("topic:"))
async def handle_topic_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробник вибору теми: генерує завдання за темою."""
    if not callback.data:
        return
    try:
        topic_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("помилка вибору теми.", show_alert=True)
        return
    await generate_and_show_task(callback, topic_id)


@router.callback_query(F.data.startswith("new_task:"))
async def handle_generate_another_task(callback: CallbackQuery, state: FSMContext) -> None:
    """Генерує ще одне завдання за поточною темою."""
    if not callback.data:
        return
    try:
        topic_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("помилка генерації завдання.", show_alert=True)
        return
    await state.clear()
    await generate_and_show_task(callback, topic_id)


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
    text, markup = render_task_view(task, topic_title, grade, tg_id=callback.from_user.id)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=markup)


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
    if not message.text or not message.from_user:
        return

    data = await state.get_data()
    task_id = data.get("current_task_id")
    if not task_id:
        await message.answer("не вдалося визначити поточне завдання. вибери тему заново через /topics.")
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

    await TaskService.record_task_attempt(
        tg_id=message.from_user.id,
        task_id=task.id,
        is_correct=result.is_correct,
        user_answer=message.text,
    )

    next_task = await TaskService.get_next_task(topic_id=task.topic_id, current_task_id=task.id)
    reply_markup = get_task_navigation_keyboard(
        next_task_id=next_task.id if next_task else None,
        current_task_id=task.id,
        topic_id=task.topic_id,
        grade=grade,
        is_correct=result.is_correct,
    )

    if result.is_correct:
        response_text = f"{result.feedback}\n\n<i>{result.detailed_solution}</i>\n\nщо робимо далі? вибирай дію нижче:"
    else:
        response_text = f"{result.feedback}\n\nспробуй ще раз або візьми підказку:"

    await state.clear()
    await message.answer(text=response_text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("quiz_ans:"))
async def handle_quiz_answer(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробник вибору варіанта відповіді у квізі безпосередньо з інлайн-кнопок."""
    if not callback.data or not callback.message:
        return

    parts = callback.data.split(":", 3)
    if len(parts) < 4:
        await callback.answer("помилка вибору варіанту.", show_alert=True)
        return

    try:
        task_id = int(parts[1])
    except ValueError:
        await callback.answer("помилка номера завдання.", show_alert=True)
        return

    letter = parts[2]
    selected_option = parts[3]

    task = await TaskService.get_task_by_id(task_id)
    if not task:
        await callback.answer("завдання не знайдено.", show_alert=True)
        return

    topic = await TaskService.get_topic_by_id(task.topic_id)
    grade = topic.grade if topic else 5

    await callback.answer(f"обрано {letter}")

    # Миттєва перевірка для квізу (без очікування мережевого виклику AI)
    user_norm = selected_option.strip().lower()
    corr_norm = (task.correct_answer or "").strip().lower()
    let_norm = letter.strip().lower()

    is_correct = (user_norm == corr_norm or let_norm == corr_norm)
    if not is_correct and task.options:
        letters = ["а", "б", "в", "г"]
        for idx, opt in enumerate(task.options):
            if idx < len(letters):
                opt_letter = letters[idx]
                opt_norm = opt.strip().lower()
                if corr_norm in (opt_norm, opt_letter) and (user_norm == opt_norm or let_norm == opt_letter):
                    is_correct = True
                    break

    await TaskService.record_task_attempt(
        tg_id=callback.from_user.id,
        task_id=task.id,
        is_correct=is_correct,
        user_answer=selected_option,
    )

    next_task = await TaskService.get_next_task(topic_id=task.topic_id, current_task_id=task.id)

    status_header = (
        "<b>правильно!</b>"
        if is_correct
        else f"<b>неправильно.</b> твій вибір: <b>{letter}) {selected_option}</b>"
    )

    feedback_text = (
        "відповідь правильна! молодець, точний розв'язок."
        if is_correct
        else f"на жаль, вибір помилковий. правильна відповідь: {task.correct_answer}."
    )

    sol_text = task.detailed_solution or task.solution_hint or f"правильна відповідь: {task.correct_answer}."
    response_text = (
        f"{status_header}\n\n"
        f"{feedback_text}\n\n"
        f"<b>покроковий розв'язок:</b>\n{sol_text}\n\n"
        "що робимо далі? вибирай дію нижче:"
    )

    reply_markup = get_task_navigation_keyboard(
        next_task_id=next_task.id if next_task else None,
        current_task_id=task.id,
        topic_id=task.topic_id,
        grade=grade,
        is_correct=is_correct,
    )

    await state.clear()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=response_text, reply_markup=reply_markup)

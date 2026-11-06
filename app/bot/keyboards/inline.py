from typing import TYPE_CHECKING
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

if TYPE_CHECKING:
    from app.db.models import Topic


def get_grades_keyboard() -> InlineKeyboardMarkup:
    """Генерує інлайн-клавіатуру для вибору класу (1–11 класи).

    Розташування: сітка по 4 кнопки в рядку (4, 4, 3).
    Формат callback_data: 'grade:{number}'.
    """
    builder = InlineKeyboardBuilder()

    for grade in range(1, 12):
        builder.button(
            text=f"{grade} клас",
            callback_data=f"grade:{grade}",
        )

    builder.adjust(4, 4, 3)
    return builder.as_markup()


def get_topics_keyboard(topics: list["Topic"], grade: int) -> InlineKeyboardMarkup:
    """Генерує клавіатуру списку тем для обраного класу."""
    builder = InlineKeyboardBuilder()

    for topic in topics:
        builder.button(
            text=topic.title,
            callback_data=f"topic:{topic.id}",
        )

    # Кнопка для зміни класу
    builder.button(
        text="🔄 Змінити клас",
        callback_data="change_grade",
    )

    # Розташування: кожна тема на окремому рядку
    builder.adjust(1)
    return builder.as_markup()


def get_task_keyboard(task_id: int, topic_id: int, grade: int) -> InlineKeyboardMarkup:
    """Генерує кнопки дій для перегляду завдання."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✍️ Відповісти",
        callback_data=f"solve:{task_id}",
    )
    builder.button(
        text="💡 Підказка",
        callback_data=f"hint:{task_id}",
    )
    builder.button(
        text="🔙 До списку тем",
        callback_data=f"topics_list:{grade}",
    )

    # Дві кнопки дій в один рядок, повернення в окремий рядок
    builder.adjust(2, 1)
    return builder.as_markup()

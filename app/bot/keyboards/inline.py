from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


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

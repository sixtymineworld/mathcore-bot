from typing import TYPE_CHECKING
from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings

if TYPE_CHECKING:
    from app.db.models import Topic


def _add_webapp_button(builder: InlineKeyboardBuilder) -> None:
    if settings.WEB_APP_URL:
        builder.button(text="відкрити застосунок", web_app=WebAppInfo(url=settings.WEB_APP_URL))


def get_grades_keyboard() -> InlineKeyboardMarkup:
    """Генерує інлайн-клавіатуру для вибору класу (1–11 класи)."""
    builder = InlineKeyboardBuilder()
    for grade in range(1, 12):
        builder.button(text=f"{grade} клас", callback_data=f"grade:{grade}")
    if settings.WEB_APP_URL:
        _add_webapp_button(builder)
        builder.adjust(4, 4, 3, 1)
    else:
        builder.adjust(4, 4, 3)
    return builder.as_markup()


def get_home_keyboard(grade: int) -> InlineKeyboardMarkup:
    """Генерує головне меню для поверненого користувача зі збереженою сесією."""
    builder = InlineKeyboardBuilder()
    _add_webapp_button(builder)
    builder.button(text=f"навчальні теми ({grade} клас)", callback_data=f"topics_list:{grade}")
    builder.button(text="профіль та успішність", callback_data="my_profile")
    builder.button(text="змінити клас", callback_data="change_grade")
    return builder.adjust(1).as_markup()


def get_subjects_keyboard(grade: int) -> InlineKeyboardMarkup:
    """Генерує клавіатуру вибору предмета (алгебра / геометрія) для 7–11 класів."""
    builder = InlineKeyboardBuilder()
    builder.button(text="алгебра", callback_data=f"subject:{grade}:алгебра")
    builder.button(text="геометрія", callback_data=f"subject:{grade}:геометрія")
    _add_webapp_button(builder)
    builder.button(text="змінити клас", callback_data="change_grade")
    return builder.adjust(2, 1, 1).as_markup() if settings.WEB_APP_URL else builder.adjust(2, 1).as_markup()


def get_topics_keyboard(
    topics: list["Topic"],
    grade: int,
    subject: str | None = None,
) -> InlineKeyboardMarkup:
    """Генерує клавіатуру списку тем для обраного класу."""
    builder = InlineKeyboardBuilder()
    for topic in topics:
        builder.button(text=topic.title, callback_data=f"topic:{topic.id}")

    if grade >= 7 and subject:
        other_subj = "геометрія" if subject == "алгебра" else "алгебра"
        builder.button(text=f"перейти до: {other_subj}", callback_data=f"subject:{grade}:{other_subj}")

    _add_webapp_button(builder)
    builder.button(text="профіль та успішність", callback_data="my_profile")
    builder.button(text="змінити клас", callback_data="change_grade")
    return builder.adjust(1).as_markup()


def get_profile_keyboard(grade: int | None = None) -> InlineKeyboardMarkup:
    """Генерує кнопки для екрана профілю."""
    builder = InlineKeyboardBuilder()
    _add_webapp_button(builder)
    if grade:
        builder.button(text="до списку тем", callback_data=f"topics_list:{grade}")
    builder.button(text="змінити клас", callback_data="change_grade")
    return builder.adjust(1).as_markup()


get_stats_keyboard = get_profile_keyboard


def get_task_keyboard(
    task_id: int,
    topic_id: int,
    grade: int,
    has_diagram: bool = False,
) -> InlineKeyboardMarkup:
    """Генерує кнопки дій для перегляду завдання."""
    builder = InlineKeyboardBuilder()
    if has_diagram and settings.WEB_APP_URL:
        builder.button(text="відкрити з малюнком у додатку", web_app=WebAppInfo(url=settings.WEB_APP_URL))
    builder.button(text="дати відповідь", callback_data=f"solve:{task_id}")
    builder.button(text="підказка", callback_data=f"hint:{task_id}")
    builder.button(text="нова задача з цієї теми", callback_data=f"new_task:{topic_id}")
    builder.button(text="до списку інших тем", callback_data=f"topics_list:{grade}")

    layout = (1, 2, 1, 1) if (has_diagram and settings.WEB_APP_URL) else (2, 1, 1)
    return builder.adjust(*layout).as_markup()


def get_task_navigation_keyboard(
    next_task_id: int | None,
    current_task_id: int,
    topic_id: int,
    grade: int,
    is_correct: bool,
) -> InlineKeyboardMarkup:
    """Клавіатура після перевірки розв'язку."""
    builder = InlineKeyboardBuilder()
    if not is_correct:
        builder.button(text="спробувати ще раз", callback_data=f"solve:{current_task_id}")
        builder.button(text="отримати підказку", callback_data=f"hint:{current_task_id}")
    builder.button(text="нова задача з цієї теми", callback_data=f"new_task:{topic_id}")
    if next_task_id is not None:
        builder.button(text="наступне завдання", callback_data=f"task:{next_task_id}")
    builder.button(text="до списку інших тем", callback_data=f"topics_list:{grade}")
    return builder.adjust(1).as_markup()

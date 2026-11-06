from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    """FSM стани користувача mathcore."""

    selecting_grade = State()
    viewing_topics = State()
    solving_task = State()
    waiting_ai_question = State()

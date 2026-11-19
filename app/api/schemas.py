from pydantic import BaseModel, ConfigDict, Field


class UserProfileResponse(BaseModel):
    """Схема профілю та успішності користувача."""

    tg_id: int = Field(description="Telegram ID користувача")
    first_name: str = Field(description="Ім'я користувача")
    grade: int | None = Field(default=None, description="Клас навчання (1–11)")
    total_attempts: int = Field(default=0, description="Загальна кількість спроб")
    solved_unique: int = Field(default=0, description="Кількість унікальних розв'язаних задач")
    accuracy: int = Field(default=0, description="Точність відповідей у відсотках")
    today_attempts: int = Field(default=0, description="Спроб за сьогодні")
    today_solved: int = Field(default=0, description="Розв'язано задач за сьогодні")
    streak: int = Field(default=0, description="Поточна серія правильних відповідей")
    days_registered: int = Field(default=1, description="Днів у mathcore")
    rank: str = Field(default="початківець", description="Рівень майстерності")
    progress_bar: str = Field(default="[□□□□□□□□]", description="Текстовий прогрес-бар")


class UpdateGradeRequest(BaseModel):
    """Запит на зміну класу користувача."""

    grade: int = Field(ge=1, le=11, description="Клас навчання від 1 до 11")


class TopicResponse(BaseModel):
    """Схема навчальної теми."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    grade: int
    subject: str = "математика"
    section: str = "загальний розділ"
    order_num: int
    tasks_count: int = 0


class TaskResponse(BaseModel):
    """Схема математичного завдання для клієнта."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    title: str
    question_text: str
    difficulty: int
    diagram_svg: str | None = None
    is_nmt: bool = False
    is_solved: bool = False
    detailed_solution: str | None = None


class CheckAnswerRequest(BaseModel):
    """Запит на перевірку відповіді."""

    answer: str = Field(min_length=1, max_length=500, description="Відповідь учня")


class CheckAnswerResponse(BaseModel):
    """Результат перевірки відповіді від AI."""

    is_correct: bool = Field(description="Чи є відповідь правильною")
    explanation: str = Field(description="Пояснення або коментар AI")
    user_answer: str = Field(description="Оригінальна відповідь учня")
    detailed_solution: str | None = Field(default=None, description="Покроковий розв'язок задачі")


class HintResponse(BaseModel):
    """Підказка до завдання."""

    task_id: int
    hint: str


class GenerateTaskResponse(BaseModel):
    """Згенероване завдання."""

    task: TaskResponse
    message: str

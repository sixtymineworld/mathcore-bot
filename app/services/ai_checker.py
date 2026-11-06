from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AICheckResult:
    """Результат аналізу відповіді учня моделлю штучного інтелекту."""

    is_correct: bool
    feedback: str
    detailed_solution: str | None = None
    confidence_score: float = 1.0


@dataclass
class GeneratedTask:
    """Згенероване штучним інтелектом навчальне завдання."""

    grade: int
    topic: str
    question: str
    hint: str
    correct_answer: str


class BaseAIChecker(ABC):
    """Абстрактний інтерфейс для AI-сервісу перевірки математичних розв'язків.

    Дозволяє без змін у бізнес-логіці підключати різних провайдерів LLM
    (OpenAI GPT-4o, Google Gemini, Anthropic Claude, локальні моделі через vLLM/Ollama).
    """

    @abstractmethod
    async def check_solution(
        self,
        task_question: str,
        user_answer: str,
        correct_answer: str,
        grade: int,
    ) -> AICheckResult:
        """Перевіряє правильність відповіді учня та повертає педагогічний фідбек.

        :param task_question: Текст умови задачі.
        :param user_answer: Відповідь або хід розв'язку учня.
        :param correct_answer: Еталонна відповідь.
        :param grade: Клас навчання (1–11) для адаптації мови пояснення.
        :return: Об'єкт AICheckResult з результатом та коментарем.
        """
        pass

    @abstractmethod
    async def get_hint(
        self,
        task_question: str,
        grade: int,
    ) -> str:
        """Генерує підказку або наводить на наступний крок без розкриття повної відповіді.

        :param task_question: Текст умови задачі.
        :param grade: Клас навчання.
        :return: Текст підказки.
        """
        pass

    @abstractmethod
    async def generate_task(
        self,
        grade: int,
        topic: str,
    ) -> GeneratedTask:
        """Генерує нове унікальне математичне завдання за класом і темою.

        :param grade: Клас навчання (1–11).
        :param topic: Назва теми (наприклад, "Квадратні рівняння").
        :return: Згенероване завдання.
        """
        pass


class MockAIChecker(BaseAIChecker):
    """Заглушка (Mock) AI-сервісу для локальної розробки та тестування.

    Імітує роботу LLM, дозволяючи тестувати логіку бота без використання
    платних API-ключів або підключення до зовнішніх сервісів.
    """

    async def check_solution(
        self,
        task_question: str,
        user_answer: str,
        correct_answer: str,
        grade: int,
    ) -> AICheckResult:
        normalized_user = user_answer.strip().replace(",", ".").lower()
        normalized_correct = correct_answer.strip().replace(",", ".").lower()

        is_correct = normalized_user == normalized_correct

        if is_correct:
            feedback = (
                f"🎉 Чудова робота! Відповідь <b>{user_answer}</b> абсолютно правильна.\n"
                f"Ти відмінно засвоїв матеріал для {grade} класу."
            )
        else:
            feedback = (
                f"🤔 Схоже, у розрахунках є неточність. Твоя відповідь: <b>{user_answer}</b>.\n"
                f"Спробуй ще раз або скористайся підказкою, щоб знайти правильний шлях!"
            )

        return AICheckResult(
            is_correct=is_correct,
            feedback=feedback,
            detailed_solution=f"Еталонна відповідь: {correct_answer}.",
            confidence_score=1.0,
        )

    async def get_hint(
        self,
        task_question: str,
        grade: int,
    ) -> str:
        return (
            f"💡 <b>Підказка для {grade} класу:</b>\n"
            "Уважно перечитай умову задачі, виділи відомі величини та запиши формулу, "
            "яка пов'язує їх із шуканим значенням."
        )

    async def generate_task(
        self,
        grade: int,
        topic: str,
    ) -> GeneratedTask:
        return GeneratedTask(
            grade=grade,
            topic=topic,
            question="Розв'яжіть рівняння: 2x + 6 = 14",
            hint="Перенеси відомі доданки в праву частину, змінивши знак на протилежний.",
            correct_answer="4",
        )


def get_ai_checker() -> BaseAIChecker:
    """Фабрика для отримання екземпляра AI-сервісу.

    У майбутньому тут можна перемикати імплементацію на основі конфігурації
    (наприклад, повертати OpenAIChecker, GeminiChecker тощо).
    """
    return MockAIChecker()

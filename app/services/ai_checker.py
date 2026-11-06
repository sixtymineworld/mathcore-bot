from abc import ABC, abstractmethod
from dataclasses import dataclass
import re


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
        """Перевіряє правильність відповіді учня та повертає педагогічний фідбек."""
        pass

    @abstractmethod
    async def get_hint(
        self,
        task_question: str,
        grade: int,
        custom_hint: str | None = None,
    ) -> str:
        """Генерує підказку або наводить на наступний крок без розкриття повної відповіді."""
        pass

    @abstractmethod
    async def generate_task(
        self,
        grade: int,
        topic: str,
    ) -> GeneratedTask:
        """Генерує нове унікальне математичне завдання за класом і темою."""
        pass


class MockAIChecker(BaseAIChecker):
    """Заглушка (Mock) AI-сервісу для локальної розробки та тестування.

    Імітує роботу LLM, дозволяючи тестувати логіку бота без використання
    платних API-ключів або підключення до зовнішніх сервісів.
    """

    @staticmethod
    def _normalize(answer: str) -> str:
        """Нормалізація математичної відповіді для точного порівняння."""
        ans = answer.strip().replace(",", ".").lower()
        # Прибираємо префікси "x =", "х =", "y =", "d =" тощо
        ans = re.sub(r"^[a-zA-Zа-яА-ЯіІїЇєЄ]\s*=\s*", "", ans)
        # Прибираємо зайві пробіли навколо знаків ділення (для дробів a / b)
        ans = re.sub(r"\s*/\s*", "/", ans)
        return ans.strip()

    async def check_solution(
        self,
        task_question: str,
        user_answer: str,
        correct_answer: str,
        grade: int,
    ) -> AICheckResult:
        normalized_user = self._normalize(user_answer)
        normalized_correct = self._normalize(correct_answer)

        is_correct = normalized_user == normalized_correct

        if is_correct:
            feedback = (
                f"🎉 <b>Чудова робота!</b> Відповідь <code>{user_answer.strip()}</code> абсолютно правильна.\n"
                f"Ти чудово володієш темою для {grade} класу."
            )
        else:
            feedback = (
                f"🤔 Схоже, у розрахунках є помилка. Твоя відповідь: <code>{user_answer.strip()}</code>.\n"
                "Спробуй ще раз перевірити проміжні кроки або скористайся підказкою!"
            )

        return AICheckResult(
            is_correct=is_correct,
            feedback=feedback,
            detailed_solution=f"Еталонна відповідь: <b>{correct_answer}</b>.",
            confidence_score=1.0,
        )

    async def get_hint(
        self,
        task_question: str,
        grade: int,
        custom_hint: str | None = None,
    ) -> str:
        if custom_hint:
            return (
                f"💡 <b>Підказка від AI ({grade} клас):</b>\n\n"
                f"{custom_hint}"
            )

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
    """Фабрика для отримання екземпляра AI-сервісу."""
    return MockAIChecker()

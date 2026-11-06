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
    """Абстрактний інтерфейс для AI-сервісу перевірки математичних розв'язків."""

    @abstractmethod
    async def check_solution(
        self,
        task_question: str,
        user_answer: str,
        correct_answer: str,
        grade: int,
    ) -> AICheckResult:
        pass

    @abstractmethod
    async def get_hint(
        self,
        task_question: str,
        grade: int,
        custom_hint: str | None = None,
    ) -> str:
        pass

    @abstractmethod
    async def generate_task(
        self,
        grade: int,
        topic: str,
    ) -> GeneratedTask:
        pass


class MockAIChecker(BaseAIChecker):
    """Заглушка (Mock) AI-сервісу для локальної розробки та тестування."""

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
                f"чудова робота! відповідь <code>{user_answer.strip()}</code> абсолютно правильна.\n"
                f"ти чудово володієш темою для {grade} класу."
            )
        else:
            feedback = (
                f"схоже, у розрахунках є помилка. твоя відповідь: <code>{user_answer.strip()}</code>.\n"
                "перевір проміжні кроки або скористайся підказкою!"
            )

        return AICheckResult(
            is_correct=is_correct,
            feedback=feedback,
            detailed_solution=f"еталонна відповідь: <b>{correct_answer}</b>.",
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
                f"<b>підказка ({grade} клас):</b>\n\n"
                f"{custom_hint}"
            )

        return (
            f"<b>підказка ({grade} клас):</b>\n\n"
            "уважно перечитай умову задачі, виділи відомі величини та запиши формулу, "
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
            question="розв'яжіть рівняння: 2x + 6 = 14",
            hint="перенеси відомі доданки в праву частину, змінивши знак на протилежний.",
            correct_answer="4",
        )


def get_ai_checker() -> BaseAIChecker:
    """Фабрика для отримання екземпляра AI-сервісу."""
    return MockAIChecker()

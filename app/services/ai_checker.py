from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import logging
import random
import re

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


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
    title: str
    question: str
    hint: str
    correct_answer: str
    difficulty: int = 1


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
        """Процедурна генерація випадкових навчальних завдань відповідно до обраної теми."""
        top_lower = topic.lower()

        # 1. Лінійні рівняння (7 клас)
        if "рівнян" in top_lower and "квадрат" not in top_lower:
            x = random.randint(2, 12)
            a = random.randint(2, 6)
            b = random.randint(1, 25)
            c = a * x + b
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="лінійне рівняння",
                question=f"розв'яжіть рівняння:\n\n<b>{a}x + {b} = {c}</b>\nзнайдіть <b>x</b>.",
                hint="перенеси відомий доданок у праву частину зі зміною знака, зведи до ax = b, звідки x = b / a.",
                correct_answer=str(x),
                difficulty=1,
            )

        # 2. Звичайні дроби (5 клас)
        if "дроб" in top_lower:
            denom = random.choice([7, 9, 11, 13, 15, 17])
            n1 = random.randint(1, denom - 3)
            n2 = random.randint(1, denom - n1 - 1)
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="додавання дробів",
                question=f"знайдіть суму дробів:\n\n<b>{n1}/{denom} + {n2}/{denom} = ?</b>\n<i>(відповідь запишіть у вигляді a/b)</i>",
                hint="формула додавання дробів з однаковими знаменниками: a/c + b/c = (a + b)/c.",
                correct_answer=f"{n1 + n2}/{denom}",
                difficulty=1,
            )

        # 3. Відсотки та пропорції (6 клас)
        if "відсот" in top_lower or "пропорц" in top_lower:
            p = random.choice([10, 20, 25, 50])
            base = random.choice([60, 80, 120, 140, 180, 240, 300])
            ans = int(base * p / 100)
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="знаходження відсотка",
                question=f"знайдіть <b>{p}%</b> від числа <b>{base}</b>.",
                hint="перетвори відсотки у дріб або скористайся правилом: b = a * (p / 100).",
                correct_answer=str(ans),
                difficulty=1,
            )

        # 4. Теорема Піфагора (8 клас)
        if "піфагор" in top_lower:
            triples = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17)]
            t = random.choice(triples)
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="пошук гіпотенузи",
                question=f"катети прямокутного трикутника дорівнюють <b>{t[0]} см</b> і <b>{t[1]} см</b>.\nзнайдіть гіпотенузу (введіть лише число).",
                hint="теорема піфагора: c² = a² + b², де c — шукана гіпотенуза.",
                correct_answer=str(t[2]),
                difficulty=2,
            )

        # 5. Квадратні корені (8 клас)
        if "корен" in top_lower:
            nums = [(16, 4), (25, 5), (36, 6), (49, 7), (64, 8), (81, 9), (100, 10), (144, 12)]
            pair = random.sample(nums, 2)
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="обчислення коренів",
                question=f"обчисліть:\n\n<b>√({pair[0][0]}) + √({pair[1][0]}) = ?</b>",
                hint="знайди корінь з кожного числа окремо (√a = b означає, що b² = a), а потім додай результати.",
                correct_answer=str(pair[0][1] + pair[1][1]),
                difficulty=1,
            )

        # 6. Квадратні рівняння / дискримінант (9 клас)
        if "квадратн" in top_lower or "дискримінант" in top_lower:
            r1, r2 = random.choice([(1, 2), (2, 3), (1, 4), (3, 4), (-1, 3), (-2, 4)])
            b_val = -(r1 + r2)
            c_val = r1 * r2
            sign_b = f"- {-b_val}" if b_val < 0 else f"+ {b_val}"
            sign_c = f"- {-c_val}" if c_val < 0 else f"+ {c_val}"
            d_val = b_val**2 - 4 * c_val
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="дискримінант",
                question=f"знайдіть дискримінант <b>D</b> для квадратного рівняння:\n\n<b>x² {sign_b}x {sign_c} = 0</b>",
                hint="формула дискримінанта для ax² + bx + c = 0: D = b² - 4ac. визнач свої a, b, c і порахуй.",
                correct_answer=str(d_val),
                difficulty=2,
            )

        # 7. Базовий генератор для арифметики та інших тем
        v1 = random.randint(100, 400)
        v2 = random.randint(50, 300)
        v3 = random.randint(20, 90)
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="обчислення виразу",
            question=f"обчисліть значення виразу:\n\n<b>{v1} + {v2} - {v3} = ?</b>",
            hint="згадай черговість дій: додавання та віднімання виконуються по черзі зліва направо.",
            correct_answer=str(v1 + v2 - v3),
            difficulty=1,
        )


class GeminiAIChecker(BaseAIChecker):
    """Інтеграція з Google Gemini API для інтелектуального аналізу відповідей та генерації підказок."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )
        self.mock_fallback = MockAIChecker()

    async def _generate_content(
        self,
        prompt: str,
        json_mode: bool = False,
        temperature: float = 0.2,
    ) -> str | None:
        """Виконує асинхронний запит до Google Gemini REST API."""
        url = f"{self.base_url}?key={self.api_key}"
        payload: dict = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
            },
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                    else:
                        error_text = await resp.text()
                        logger.error("Gemini API помилка (HTTP %s): %s", resp.status, error_text)
        except Exception as e:
            logger.error("Виняток при зверненні до Gemini API: %s", e)

        return None

    async def check_solution(
        self,
        task_question: str,
        user_answer: str,
        correct_answer: str,
        grade: int,
    ) -> AICheckResult:
        prompt = (
            "ти — персональний інтерактивний репетитор зі шкільної математики (1–11 класи) в україні.\n"
            "твій стиль спілкування: доброзичливий, сучасний, лаконічний, виключно маленькими літерами (lowercase).\n\n"
            f"завдання для учня ({grade} клас):\n"
            f"умова: {task_question}\n"
            f"еталонна правильна відповідь: {correct_answer}\n"
            f"відповідь учня: {user_answer}\n\n"
            "інструкція:\n"
            "1. перевір, чи відповідь учня правильна або математично еквівалентна еталонній (дроби, форми запису тощо).\n"
            "2. якщо відповідь неправильна — зрозумій причину неточності (помилка знаку, дії тощо), "
            "але НЕ розкривай одразу фінальну відповідь у полі feedback!\n"
            "3. у полі detailed_solution напиши короткий хід правильного розв'язку.\n\n"
            "відповідь надай суворо валідним JSON форматом:\n"
            "{\n"
            '  "is_correct": true,\n'
            '  "feedback": "короткий фідбек учню маленькими літерами",\n'
            '  "detailed_solution": "еталонний розв\'язок маленькими літерами"\n'
            "}"
        )

        raw_response = await self._generate_content(prompt, json_mode=True, temperature=0.1)
        if raw_response:
            try:
                parsed = json.loads(raw_response)
                return AICheckResult(
                    is_correct=bool(parsed.get("is_correct", False)),
                    feedback=str(parsed.get("feedback", "")).lower(),
                    detailed_solution=str(
                        parsed.get(
                            "detailed_solution",
                            f"еталонна відповідь: <b>{correct_answer}</b>.",
                        )
                    ).lower(),
                    confidence_score=0.95,
                )
            except json.JSONDecodeError:
                logger.warning("не вдалося розпарсити JSON від Gemini: %s", raw_response)

        # Резервний фолбек на детермінований чекер при відсутності зв'язку
        return await self.mock_fallback.check_solution(
            task_question=task_question,
            user_answer=user_answer,
            correct_answer=correct_answer,
            grade=grade,
        )

    async def get_hint(
        self,
        task_question: str,
        grade: int,
        custom_hint: str | None = None,
    ) -> str:
        prompt = (
            f"ти — розумний педагогічний ментор з математики для учня {grade} класу.\n"
            "твій стиль спілкування: виключно маленькими літерами (lowercase), лаконічний, доброзичливий.\n\n"
            f"умова завдання: {task_question}\n"
            f"{'напрямок думки: ' + custom_hint if custom_hint else ''}\n\n"
            "суворі правила для підказки:\n"
            "1. ти МОЖЕШ і маєш показати відповідну загальну формулу або тотожність (наприклад: c² = a² + b², D = b² - 4ac, a/c + b/c = (a+b)/c тощо).\n"
            "2. КАТЕГОРИЧНО ЗАБОРОНЕНО підставляти конкретні числа із задачі у формулу!\n"
            "3. КАТЕГОРИЧНО ЗАБОРОНЕНО виконувати проміжні обчислення чи розкривати кінцеву відповідь.\n"
            "4. підказка має бути короткою (1-2 речення): покажи формулу чи правило і спонукай учня підставити числа самостійно.\n"
            "поверни лише текст самої підказки."
        )

        response = await self._generate_content(prompt, json_mode=False, temperature=0.3)
        if response:
            clean_text = response.replace("```", "").strip().lower()
            return f"<b>підказка ({grade} клас):</b>\n\n{clean_text}"

        return await self.mock_fallback.get_hint(
            task_question=task_question,
            grade=grade,
            custom_hint=custom_hint,
        )

    async def generate_task(
        self,
        grade: int,
        topic: str,
    ) -> GeneratedTask:
        prompt = (
            f"ти — розумний генератор завдань зі шкільної математики для {grade} класу за українською програмою.\n"
            f"обрана тема: {topic}\n"
            "твій стиль: виключно маленькими літерами (lowercase), лаконічний.\n\n"
            "завдання:\n"
            "згенеруй одне нове, унікальне та цікаве завдання строго за цією темою для учня цього класу.\n"
            "правила:\n"
            "1. умова має бути чіткою, лаконічною, з ключовими числами або рівнянням у тегах <b>...</b>.\n"
            "2. відповідь має бути однозначною та простою для введення учнем (наприклад: 4, 5/7, 30 тощо).\n"
            "3. підказка має показувати загальну формулу або правило, але БЕЗ підстановки чисел і БЕЗ розкриття відповіді!\n"
            "4. складність: від 1 до 3.\n\n"
            "відповідь надай суворо валідним JSON форматом:\n"
            "{\n"
            '  "title": "коротка назва завдання",\n'
            '  "question": "текст умови завдання",\n'
            '  "hint": "загальна формула або правило",\n'
            '  "correct_answer": "точна коротка відповідь",\n'
            '  "difficulty": 1\n'
            "}"
        )

        raw = await self._generate_content(prompt, json_mode=True, temperature=0.7)
        if raw:
            try:
                parsed = json.loads(raw)
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title=str(parsed.get("title", "завдання")).lower(),
                    question=str(parsed["question"]).lower(),
                    hint=str(parsed.get("hint", "скористайся відповідним правилом або формулою.")).lower(),
                    correct_answer=str(parsed["correct_answer"]).lower().strip(),
                    difficulty=int(parsed.get("difficulty", 1)),
                )
            except Exception as e:
                logger.warning("помилка парсингу згенерованої задачі: %s", e)

        return await self.mock_fallback.generate_task(grade=grade, topic=topic)


def get_ai_checker() -> BaseAIChecker:
    """Фабрика для отримання екземпляра AI-сервісу.

    Якщо вказано GEMINI_API_KEY — використовується справжній Gemini API,
    інакше — надійний детермінований MockAIChecker.
    """
    if settings.GEMINI_API_KEY:
        return GeminiAIChecker(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
        )
    return MockAIChecker()

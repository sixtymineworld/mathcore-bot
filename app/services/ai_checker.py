from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import logging
import random
import re

import aiohttp

from app.config import settings
from app.services.svg_diagrams import (
    diagram_box_prism,
    diagram_circle_tangents,
    diagram_cylinder,
    diagram_derivative_tangent,
    diagram_function_roots,
    diagram_quadrangular_pyramid,
    diagram_rhombus_diagonals,
    diagram_right_trapezoid,
    diagram_right_triangle_altitude,
    diagram_vectors,
)

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
    diagram_svg: str | None = None
    is_nmt: bool = False
    detailed_solution: str | None = None


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
        # Прибираємо префікси "x =", "х =", "y =", "d =", "s =", "v =" тощо
        ans = re.sub(r"^[a-zA-Zа-яА-ЯіІїЇєЄ_]+\s*=\s*", "", ans)
        # Прибираємо зайві пробіли навколо знаків ділення (для дробів a / b)
        ans = re.sub(r"\s*/\s*", "/", ans)
        # Очищуємо нулі наприкінці десяткового дробу (наприклад 1.50 -> 1.5)
        if "." in ans:
            try:
                float_val = float(ans)
                if float_val.is_integer():
                    return str(int(float_val))
                return f"{float_val:.4g}".rstrip(".")
            except ValueError:
                pass
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
                f"ти чудово володієш темою{' для підготовки до нмт' if grade >= 10 else f' для {grade} класу'}."
            )
        else:
            feedback = (
                f"відповідь <code>{user_answer.strip()}</code> поки що не зійшлася з еталоном.\n"
                "перевір уважно свої проміжні обчислення або натисни 'підказка'!"
            )

        detailed = (
            f"правильна відповідь: <b>{correct_answer}</b>.\n"
            "якщо виникають труднощі, переглянь покроковий хід міркувань."
        )

        return AICheckResult(
            is_correct=is_correct,
            feedback=feedback,
            detailed_solution=detailed,
        )

    async def get_hint(
        self,
        task_question: str,
        grade: int,
        custom_hint: str | None = None,
    ) -> str:
        if custom_hint:
            return f"<b>підказка ({grade} клас):</b>\n\n{custom_hint}"
        return (
            f"<b>підказка ({grade} клас):</b>\n\n"
            "пригадай базову формулу або алгоритм для цієї теми та уважно виконай обчислення крок за кроком."
        )

    async def generate_task(
        self,
        grade: int,
        topic: str,
    ) -> GeneratedTask:
        """Процедурна генерація завдань за програмою О. Істера та геометрії з рисунками."""
        geom_task = _generate_geometry_task(grade, topic)
        if geom_task:
            return geom_task
        return _generate_school_task(grade, topic)


def _generate_geometry_task(grade: int, topic: str) -> GeneratedTask | None:
    """Генерація задач з геометрії та векторної графіки SVG."""
    top_lower = topic.lower()

    if "трапец" in top_lower:
        bc = random.choice([6, 7, 8, 9])
        ad = bc + 5
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="прямокутна трапеція",
            question=(
                f"на рисунку зображено прямокутну трапецію <b>ABCD</b> (AD ∥ BC, ∠A = 90°).\n"
                f"відомо, що менша основа <b>BC = {bc}</b>, похила бічна сторона <b>CD = 10</b>, а гострий кут <b>∠D = 60°</b>.\n\n"
                "знайдіть довжину більшої основи <b>AD</b>."
            ),
            hint="у прямокутному трикутнику CHD катет HD = CD · cos(60°) = 5. більша основа AD = BC + HD.",
            correct_answer=str(ad),
            difficulty=2,
            diagram_svg=diagram_right_trapezoid(bc=bc, cd=10, angle_d=60),
            detailed_solution=f"1. чотирикутник ABCH — прямокутник, AH = BC = {bc}.\n2. HD = 10 · 0.5 = 5.\n3. AD = {bc} + 5 = {ad}.\nвідповідь: {ad}.",
        )

    if "висот" in top_lower or ("трикутн" in top_lower and grade >= 8):
        ad_val, db_val, cd_val = random.choice([(9, 16, 12), (4, 9, 6), (16, 25, 20), (1, 16, 4)])
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="висота прямокутного трикутника",
            question=(
                "на рисунку зображено прямокутний трикутник <b>ABC</b> (∠C = 90°).\n"
                f"висота CD ділить гіпотенузу на проекції <b>AD = {ad_val}</b> та <b>DB = {db_val}</b>.\n\n"
                "знайдіть довжину висоти <b>CD</b>."
            ),
            hint="квадрат висоти дорівнює добутку проекцій катетів: CD² = AD · DB.",
            correct_answer=str(cd_val),
            difficulty=2,
            diagram_svg=diagram_right_triangle_altitude(ad=ad_val, db=db_val, cd=cd_val),
            detailed_solution=f"1. CD² = {ad_val} · {db_val} = {ad_val * db_val}.\n2. CD = {cd_val}.\nвідповідь: {cd_val}.",
        )

    if "дотичн" in top_lower or "коло" in top_lower:
        r_val = random.choice([6, 8, 10, 12])
        dist_val = 2 * r_val
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="дотичні до кола з однієї точки",
            question=(
                "на рисунку зображено коло з центром у точці <b>O</b>.\n"
                f"з точки M проведено дві дотичні (кут між ними 60°), радіус <b>r = {r_val}</b>.\n\n"
                "знайдіть відстань від точки M до центра кола <b>MO</b>."
            ),
            hint="бісектриса ділить кут навпіл (30°). катет проти кута 30° дорівнює половині гіпотенузи: MO = 2 · r.",
            correct_answer=str(dist_val),
            difficulty=2,
            diagram_svg=diagram_circle_tangents(r=r_val, angle_m=60, dist=dist_val),
            detailed_solution=f"1. ∠AMO = 30°.\n2. у прямокутному трикутнику MAO: MO = 2 · OA = 2 · {r_val} = {dist_val}.\nвідповідь: {dist_val}.",
        )

    if "пірамід" in top_lower:
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="правильна чотирикутна піраміда",
            question="на рисунку зображено правильну чотирикутну піраміду зі стороною основи 12 та висотою 8.\nобчисліть площу повної поверхні піраміди.",
            hint="S_осн = a², апофема = √(h² + (a/2)²), S_біч = 1/2 · P · апофема, S_повн = S_біч + S_осн.",
            correct_answer="384",
            difficulty=3,
            is_nmt=True,
            diagram_svg=diagram_quadrangular_pyramid(base_a=12, height=8, apothem=10),
            detailed_solution="1. S_осн = 144.\n2. апофема = 10.\n3. S_біч = 240.\n4. S_повн = 384.\nвідповідь: 384.",
        )

    if "циліндр" in top_lower:
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="циліндр та осьовий переріз",
            question="на рисунку зображено циліндр, осьовим перерізом якого є квадрат із діагоналлю 8√2.\nобчисліть значення виразу V / π.",
            hint="висота h = 8, радіус r = 4. V = π · r² · h.",
            correct_answer="128",
            difficulty=3,
            is_nmt=True,
            diagram_svg=diagram_cylinder(d=8, h=8),
            detailed_solution="1. h = 8, r = 4.\n2. V = π · 16 · 8 = 128π.\nвідповідь: 128.",
        )

    if "паралелепіпед" in top_lower or "призм" in top_lower:
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="прямокутний паралелепіпед",
            question="на рисунку зображено прямокутний паралелепіпед зі сторонами основи 3 і 4 та кутом нахилу діагоналі 45°.\nобчисліть об'єм V.",
            hint="діагональ основи d = √(3² + 4²) = 5. висота h = d = 5. об'єм V = a · b · h.",
            correct_answer="60",
            difficulty=3,
            is_nmt=True,
            diagram_svg=diagram_box_prism(a=3, b=4, angle=45),
            detailed_solution="1. d = 5, h = 5.\n2. V = 3 · 4 · 5 = 60.\nвідповідь: 60.",
        )

    if "похідн" in top_lower:
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="геометричний зміст похідної",
            question="на рисунку зображено графік функції y = f(x) та дотичну, що проходить через A(-2; -1) та B(2; 5).\nзнайдіть значення похідної f'(x₀).",
            hint="значення похідної дорівнює кутовому коефіцієнту дотичної: k = (y₂ - y₁) / (x₂ - x₁).",
            correct_answer="1.5",
            difficulty=2,
            diagram_svg=diagram_derivative_tangent(),
            detailed_solution="1. k = (5 - (-1)) / (2 - (-2)) = 6 / 4 = 1.5.\nвідповідь: 1.5.",
        )

    if "вектор" in top_lower or "координат" in top_lower:
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="скалярний добуток векторів",
            question="на рисунку зображено вектори a⃗(3; 4) та b⃗(6; -2).\nзнайдіть скалярний добуток векторів a⃗ · b⃗.",
            hint="формула скалярного добутку: a⃗ · b⃗ = x₁ · x₂ + y₁ · y₂.",
            correct_answer="10",
            difficulty=2,
            diagram_svg=diagram_vectors(),
            detailed_solution="1. a⃗ · b⃗ = 3 · 6 + 4 · (-2) = 18 - 8 = 10.\nвідповідь: 10.",
        )

    if "ромб" in top_lower or "чотирикутн" in top_lower:
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="діагоналі та периметр ромба",
            question="на рисунку зображено ромб ABCD з діагоналями AC = 24 та BD = 10.\nобчисліть периметр P ромба.",
            hint="сторона a = √((d₁/2)² + (d₂/2)²). периметр P = 4a.",
            correct_answer="52",
            difficulty=2,
            diagram_svg=diagram_rhombus_diagonals(d1=24, d2=10, side=13),
            detailed_solution="1. a = √(12² + 5²) = 13.\n2. P = 4 · 13 = 52.\nвідповідь: 52.",
        )

    if "графік" in top_lower:
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="кількість коренів за графіком",
            question="на рисунку зображено графік функції y = f(x).\nвизначте кількість дійсних коренів рівняння f(x) = 1.",
            hint="знайди кількість точок перетину графіка функції з горизонтальною прямою y = 1.",
            correct_answer="3",
            difficulty=2,
            diagram_svg=diagram_function_roots(),
            detailed_solution="пряма y = 1 перетинає графік рівно у трьох точках.\nвідповідь: 3.",
        )

    return None


def _generate_school_task(grade: int, topic: str) -> GeneratedTask:
    """Генерація типових навчальних задач за підручниками О. Істера."""
    top_lower = topic.lower()

    if grade == 1:
        if "порівнян" in top_lower:
            n1 = random.randint(1, 9)
            n2 = random.randint(1, 9)
            while n2 == n1:
                n2 = random.randint(1, 9)
            ans = max(n1, n2)
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="порівняння чисел",
                question=f"яке число більше: <b>{n1}</b> чи <b>{n2}</b>? (введіть більше число).",
                hint="порівняй два числа: більше те, яке стоїть правіше на числовому промені.",
                correct_answer=str(ans),
                difficulty=1,
                detailed_solution=f"число {ans} є більшим.\nвідповідь: {ans}.",
            )
        if "фігур" in top_lower or "трикутн" in top_lower:
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="геометричні фігури",
                question="скільки сторін має геометрична фігура <b>трикутник</b>?",
                hint="згадай назву фігури: вона має стільки ж сторін, скільки й кутів.",
                correct_answer="3",
                difficulty=1,
                detailed_solution="трикутник має 3 сторони.\nвідповідь: 3.",
            )
        n1 = random.randint(1, 7)
        n2 = random.randint(1, 10 - n1)
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="додавання у межах 10",
            question=f"обчисліть значення суми:\n\n<b>{n1} + {n2} = ?</b>",
            hint="об'єднай обидва числа на числовому ряду.",
            correct_answer=str(n1 + n2),
            difficulty=1,
            detailed_solution=f"{n1} + {n2} = {n1 + n2}.\nвідповідь: {n1 + n2}.",
        )

    if grade == 2:
        n1 = random.randint(12, 65)
        n2 = random.randint(5, 30)
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="додавання в межах 100",
            question=f"обчисліть значення виразу:\n\n<b>{n1} + {n2} = ?</b>",
            hint="додай десятки до десятків, а одиниці до одиниць.",
            correct_answer=str(n1 + n2),
            difficulty=1,
            detailed_solution=f"{n1} + {n2} = {n1 + n2}.\nвідповідь: {n1 + n2}.",
        )

    if grade == 3:
        f1 = random.randint(2, 9)
        f2 = random.randint(2, 9)
        prod = f1 * f2
        if "ділен" in top_lower:
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="табличне ділення",
                question=f"обчисліть значення частки:\n\n<b>{prod} : {f1} = ?</b>",
                hint="згадай таблицю множення: яке число при множенні на дільник дає ділене.",
                correct_answer=str(f2),
                difficulty=1,
                detailed_solution=f"{prod} : {f1} = {f2}.\nвідповідь: {f2}.",
            )
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="табличне множення",
            question=f"обчисліть значення добутку:\n\n<b>{f1} · {f2} = ?</b>",
            hint="пригадай таблицю множення.",
            correct_answer=str(prod),
            difficulty=1,
            detailed_solution=f"{f1} · {f2} = {prod}.\nвідповідь: {prod}.",
        )

    if grade == 4:
        a = random.randint(15, 80)
        b = random.randint(4, 9)
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="множення чисел",
            question=f"обчисліть добуток:\n\n<b>{a} · {b} = ?</b>",
            hint="розклади число на десятки та одиниці й помнож кожну частину.",
            correct_answer=str(a * b),
            difficulty=1,
            detailed_solution=f"{a} · {b} = {a * b}.\nвідповідь: {a * b}.",
        )

    if grade in (5, 6):
        if "відсот" in top_lower:
            pct = random.choice([10, 20, 25, 50])
            base = random.choice([80, 120, 200, 300, 400])
            ans = int(base * pct / 100)
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="відсоток від числа",
                question=f"знайдіть <b>{pct}%</b> від числа <b>{base}</b>.",
                hint="перетвори відсоток у дріб та помнож на дане число.",
                correct_answer=str(ans),
                difficulty=1,
                detailed_solution=f"{base} · {pct/100:.2g} = {ans}.\nвідповідь: {ans}.",
            )
        denom = random.choice([5, 7, 9, 11])
        n1 = random.randint(1, denom - 2)
        n2 = random.randint(1, denom - n1)
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="додавання звичайних дробів",
            question=f"обчисліть суму дробів:\n\n<b>{n1}/{denom} + {n2}/{denom} = ?</b>\n(у відповідь запишіть тільки чисельник отриманого дробу)",
            hint="знаменник залишається без змін, чисельники додаються.",
            correct_answer=str(n1 + n2),
            difficulty=1,
            detailed_solution=f"чисельник: {n1} + {n2} = {n1 + n2}.\nвідповідь: {n1 + n2}.",
        )

    if "рівнян" in top_lower and "порівнян" not in top_lower and grade >= 6:
        x = random.randint(2, 12)
        a = random.randint(2, 6)
        b = random.randint(1, 20)
        c = a * x + b
        return GeneratedTask(
            grade=grade,
            topic=topic,
            title="лінійне рівняння",
            question=f"розв'яжіть рівняння:\n\n<b>{a}x + {b} = {c}</b>\nзнайдіть <b>x</b>.",
            hint="перенеси число в праву частину та поділи на коефіцієнт біля x.",
            correct_answer=str(x),
            difficulty=1,
            detailed_solution=f"1. {a}x = {c - b}.\n2. x = {x}.\nвідповідь: {x}.",
        )

    # Базовий випадок для арифметичних обчислень
    v1 = random.randint(50, 200)
    v2 = random.randint(10, 90)
    v3 = random.randint(5, 40)
    ans = v1 + v2 - v3
    return GeneratedTask(
        grade=grade,
        topic=topic,
        title="обчислення виразу",
        question=f"обчисліть значення виразу:\n\n<b>{v1} + {v2} - {v3} = ?</b>",
        hint="виконай дії по черзі зліва направо.",
        correct_answer=str(ans),
        difficulty=1,
        detailed_solution=f"1. {v1} + {v2} = {v1 + v2}.\n2. {v1 + v2} - {v3} = {ans}.\nвідповідь: {ans}.",
    )


class GeminiAIChecker(BaseAIChecker):
    """Інтеграція з високошвидкісною моделлю Google Gemini для аналізу відповідей та генерації завдань за програмою О. Істера."""

    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite"):
        self.api_key = api_key
        self.model = model
        self.backup_model = "gemini-flash-lite-latest"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.mock_fallback = MockAIChecker()

    async def _generate_content(
        self,
        prompt: str,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> str | None:
        headers = {"Content-Type": "application/json"}
        generation_config: dict[str, object] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }

        # Спроба з основною моделлю, а при необхідності — зі швидкою запасною моделлю
        models_to_try = [self.model]
        if self.backup_model and self.backup_model != self.model:
            models_to_try.append(self.backup_model)

        for mod in models_to_try:
            url = f"{self.base_url}/{mod}:generateContent?key={self.api_key}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    return str(parts[0].get("text", ""))
                        else:
                            error_text = await resp.text()
                            logger.warning(
                                "Помилка Gemini API [%s, HTTP %s]: %s",
                                mod,
                                resp.status,
                                error_text[:200],
                            )
            except Exception as e:
                logger.warning("Виняток при запиті до Gemini API [%s]: %s", mod, e)

        return None

    async def check_solution(
        self,
        task_question: str,
        user_answer: str,
        correct_answer: str,
        grade: int,
    ) -> AICheckResult:
        prompt = (
            f"ти — уважний та доброзичливий вчитель математики за програмою О. Істера ({grade} клас).\n"
            "твій стиль: виключно маленькими літерами (lowercase), чіткий, підтримуючий.\n\n"
            f"завдання для учня ({grade} клас):\n"
            f"умова: {task_question}\n"
            f"еталонна відповідь: {correct_answer}\n"
            f"відповідь учня: {user_answer}\n\n"
            "інструкція:\n"
            "1. перевір, чи відповідь учня правильна або математично еквівалентна еталонній "
            "(враховуй коми та крапки в десяткових дробах, пробіли тощо).\n"
            "2. якщо відповідь правильна: коротко похвали учня.\n"
            "3. якщо відповідь неправильна: доброзичливо поясни суть помилки, але НЕ видавай одразу готову відповідь у полі feedback!\n"
            "4. у detailed_solution напиши покроковий хід розв'язання.\n\n"
            "відповідь надай суворо валідним JSON форматом:\n"
            "{\n"
            '  "is_correct": true,\n'
            '  "feedback": "короткий фідбек маленькими літерами",\n'
            '  "detailed_solution": "покроковий розв\'язок маленькими літерами"\n'
            "}"
        )

        raw_response = await self._generate_content(prompt, json_mode=True, temperature=0.1, max_tokens=500)
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
            f"ти — вчитель-наставник з математики за підручниками О. Істера ({grade} клас).\n"
            "твій стиль спілкування: виключно маленькими літерами (lowercase), лаконічний.\n\n"
            f"умова завдання: {task_question}\n"
            f"{'напрямок думки: ' + custom_hint if custom_hint else ''}\n\n"
            "суворі правила для підказки:\n"
            "1. нагадай базове правило, алгоритм чи формулу з підручника О. Істера.\n"
            "2. КАТЕГОРИЧНО ЗАБОРОНЕНО підставляти числа із задачі або виконувати обчислення за учня!\n"
            "3. КАТЕГОРИЧНО ЗАБОРОНЕНО розкривати кінцеву відповідь.\n"
            "4. довжина підказки: 1-2 короткі речення.\n"
            "поверни лише текст самої підказки."
        )

        response = await self._generate_content(prompt, json_mode=False, temperature=0.2, max_tokens=250)
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
        has_geometry_need = grade >= 7 and any(
            w in topic.lower()
            for w in [
                "геометр",
                "трикутн",
                "чотирикутн",
                "трапец",
                "коло",
                "графік",
                "вектор",
                "пірамід",
                "стереометр",
                "циліндр",
                "призм",
            ]
        )

        geom_instruction = (
            "для цієї геометричної теми створи валідний лаконічний SVG-малюнок (diagram_svg) з viewBox='0 0 380 230'.\n"
            if has_geometry_need
            else "малюнок diagram_svg НЕ потрібен, встанови значення null.\n"
        )

        is_nmt_spec = "true якщо це задача формату НМТ для 10-11 класів, інакше false" if grade >= 10 else "false"

        prompt = (
            f"ти — досвідчений викладач математики за підручниками О. С. Істера для {grade} класу в україні.\n"
            f"обрана тема: {topic}\n"
            "твій стиль: виключно маленькими літерами (lowercase), чіткий, зрозумілий учневі.\n\n"
            "завдання:\n"
            f"склади одне типове практичне завдання для {grade} класу за матеріалом та стилем підручника О. Істера "
            f"за темою «{topic}» (це може бути приклад на обчислення, рівняння, властивість чи класична текстова задача з підручника).\n"
            f"завдання має суворо відповідати рівню складності {grade} класу (не ускладнюй штучно до формату тестів НМТ для молодших чи середніх класів).\n"
            f"{geom_instruction}\n"
            "вимоги до завдання:\n"
            "1. умова (question): чітка, лаконічна, без довгих передмов.\n"
            "2. відповідь (correct_answer): ОДНЕ число (ціле або десятковий дріб через крапку чи кому, наприклад: 12, 4.5, -7, 180), щоб учень міг швидко ввести його з клавіатури.\n"
            "3. підказка (hint): формула чи правило БЕЗ підстановки чисел і без розкриття відповіді.\n"
            "4. покроковий розв'язок (detailed_solution): розгорнуте коротке пояснення дій.\n"
            "5. складність: від 1 до 2 для звичайних вправ підручника, 3 для підвищеної складності.\n"
            f"6. is_nmt: {is_nmt_spec}.\n\n"
            "відповідь надай суворо валідним JSON форматом:\n"
            "{\n"
            '  "title": "коротка назва вправи",\n'
            '  "question": "текст умови завдання",\n'
            '  "hint": "підказка",\n'
            '  "correct_answer": "числове значення",\n'
            '  "difficulty": 1,\n'
            f'  "is_nmt": false,\n'
            '  "diagram_svg": null,\n'
            '  "detailed_solution": "покроковий розв\'язок"\n'
            "}"
        )

        raw = await self._generate_content(prompt, json_mode=True, temperature=0.5, max_tokens=800)
        if raw:
            try:
                parsed = json.loads(raw)
                diagram_svg = parsed.get("diagram_svg")
                if isinstance(diagram_svg, str) and not diagram_svg.strip().startswith("<svg"):
                    diagram_svg = None

                is_nmt = bool(parsed.get("is_nmt", False)) and grade >= 10

                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title=str(parsed.get("title", "завдання")).lower(),
                    question=str(parsed["question"]).lower(),
                    hint=str(parsed.get("hint", "скористайся правилом або формулою з підручника.")).lower(),
                    correct_answer=str(parsed["correct_answer"]).lower().strip(),
                    difficulty=int(parsed.get("difficulty", 1)),
                    diagram_svg=diagram_svg,
                    is_nmt=is_nmt,
                    detailed_solution=parsed.get("detailed_solution"),
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

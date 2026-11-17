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
        """Процедурна генерація завдань, включаючи повноцінні задачі формату НМТ з рисунками."""
        top_lower = topic.lower()

        # --- 1. НМТ: Планіметрія (трапеція, висота трикутника, коло та дотичні) ---
        if (
            "планіметрія" in top_lower
            or "трапец" in top_lower
            or "дотичн" in top_lower
            or ("трикутн" in top_lower and grade >= 9)
        ):
            sub = random.choice(["трапеція", "трикутник_висота", "дотичні"])
            if "трапец" in top_lower:
                sub = "трапеція"
            elif "висот" in top_lower or "трикутн" in top_lower:
                sub = "трикутник_висота"
            elif "дотичн" in top_lower or "коло" in top_lower:
                sub = "дотичні"

            if sub == "трапеція":
                bc = random.choice([6, 7, 8, 9])
                cd = 10
                angle = 60
                ad = bc + 5  # cd * cos(60) = 5
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="прямокутна трапеція та основа",
                    question=(
                        f"на рисунку зображено прямокутну трапецію <b>ABCD</b> (AD ∥ BC, ∠A = 90°).\n"
                        f"з вершини кута C опущено висоту <b>CH</b> на більшу основу AD.\n"
                        f"відомо, що менша основа <b>BC = {bc}</b>, похила бічна сторона <b>CD = {cd}</b>, "
                        f"а гострий кут <b>∠D = {angle}°</b>.\n\n"
                        "знайдіть довжину більшої основи <b>AD</b>."
                    ),
                    hint=(
                        "використай властивості прямокутного трикутника CHD: "
                        "катет HD = CD · cos(∠D). чотирикутник ABCH є прямокутником, "
                        "тому AH = BC. більша основа AD = AH + HD."
                    ),
                    correct_answer=str(ad),
                    difficulty=3,
                    is_nmt=True,
                    diagram_svg=diagram_right_trapezoid(bc=bc, cd=cd, angle_d=angle),
                    detailed_solution=(
                        f"1. чотирикутник ABCH є прямокутником, отже AH = BC = {bc}.\n"
                        f"2. у трикутнику CHD: HD = CD · cos(60°) = {cd} · 0.5 = 5.\n"
                        f"3. основа AD = AH + HD = {bc} + 5 = {ad}.\n"
                        f"відповідь: {ad}."
                    ),
                )
            elif sub == "трикутник_висота":
                pairs = [(9, 16, 12), (4, 9, 6), (16, 25, 20), (1, 16, 4)]
                ad_val, db_val, cd_val = random.choice(pairs)
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="висота прямокутного трикутника",
                    question=(
                        "на рисунку зображено прямокутний трикутник <b>ABC</b> (∠C = 90°).\n"
                        "з вершини прямого кута до гіпотенузи AB проведено висоту <b>CD</b>.\n"
                        f"проекція катета AC на гіпотенузу дорівнює <b>AD = {ad_val}</b>, "
                        f"а проекція катета BC дорівнює <b>DB = {db_val}</b>.\n\n"
                        "знайдіть довжину висоти <b>CD</b>."
                    ),
                    hint="метричне співвідношення у прямокутному трикутнику: квадрат висоти дорівнює добутку проекцій катетів CD² = AD · DB.",
                    correct_answer=str(cd_val),
                    difficulty=3,
                    is_nmt=True,
                    diagram_svg=diagram_right_triangle_altitude(ad=ad_val, db=db_val, cd=cd_val),
                    detailed_solution=(
                        f"1. за метричними співвідношеннями: CD² = AD · DB = {ad_val} · {db_val} = {ad_val * db_val}.\n"
                        f"2. отже, CD = √{ad_val * db_val} = {cd_val}.\n"
                        f"відповідь: {cd_val}."
                    ),
                )
            else:
                r_val = random.choice([6, 8, 10, 12])
                dist_val = 2 * r_val
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="дотичні до кола з однієї точки",
                    question=(
                        "на рисунку зображено коло з центром у точці <b>O</b>.\n"
                        "з точки <b>M</b>, що лежить поза колом, проведено дві дотичні <b>MA</b> і <b>MB</b> (A і B — точки дотику).\n"
                        f"кут між дотичними <b>∠AMB = 60°</b>, а радіус кола <b>r = {r_val}</b>.\n\n"
                        "знайдіть відстань від точки M до центра кола O (довжину відрізка <b>MO</b>)."
                    ),
                    hint="відрізок MO є бісектрисою кута між дотичними (∠AMO = 30°). у прямокутному трикутнику MAO радіус OA = MO / 2.",
                    correct_answer=str(dist_val),
                    difficulty=3,
                    is_nmt=True,
                    diagram_svg=diagram_circle_tangents(r=r_val, angle_m=60, dist=dist_val),
                    detailed_solution=(
                        f"1. відрізок MO ділить кут навпіл: ∠AMO = 60° / 2 = 30°.\n"
                        f"2. у прямокутному трикутнику MAO катет OA лежить проти кута 30°:\n"
                        f"   OA = MO / 2  ⟹  MO = 2 · OA = 2 · {r_val} = {dist_val}.\n"
                        f"відповідь: {dist_val}."
                    ),
                )

        # --- 2. НМТ: Стереометрія (піраміда, циліндр, паралелепіпед) ---
        if (
            "стереометрія" in top_lower
            or "пірамід" in top_lower
            or "циліндр" in top_lower
            or "паралелепіпед" in top_lower
            or "призм" in top_lower
        ):
            sub = random.choice(["піраміда", "циліндр", "паралелепіпед"])
            if "пірамід" in top_lower:
                sub = "піраміда"
            elif "циліндр" in top_lower:
                sub = "циліндр"
            elif "паралелепіпед" in top_lower or "призм" in top_lower:
                sub = "паралелепіпед"

            if sub == "піраміда":
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="правильна чотирикутна піраміда",
                    question=(
                        "на рисунку зображено правильну чотирикутну піраміду <b>SABCD</b>.\n"
                        "сторона основи піраміди <b>AB = 12</b>, а висота <b>SO = 8</b>.\n"
                        "відрізок <b>SK</b> — апофема піраміди.\n\n"
                        "обчисліть площу повної поверхні цієї піраміди <b>S_повн</b>."
                    ),
                    hint="1) S_осн = a². 2) апофема SK = √(SO² + (a/2)²). 3) S_біч = 1/2 · P_осн · SK. 4) S_повн = S_біч + S_осн.",
                    correct_answer="384",
                    difficulty=3,
                    is_nmt=True,
                    diagram_svg=diagram_quadrangular_pyramid(base_a=12, height=8, apothem=10),
                    detailed_solution=(
                        "1. площа основи квадрата: S_осн = 12² = 144.\n"
                        "2. відстань від центра до сторони: OK = 12 / 2 = 6.\n"
                        "3. апофема SK = √(8² + 6²) = √100 = 10.\n"
                        "4. площа бічної поверхні: S_біч = (1/2) · (4 · 12) · 10 = 240.\n"
                        "5. повна площа: S_повн = 240 + 144 = 384.\n"
                        "відповідь: 384."
                    ),
                )
            elif sub == "циліндр":
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="циліндр та його осьовий переріз",
                    question=(
                        "на рисунку зображено циліндр, осьовим перерізом якого є квадрат <b>ABCD</b> "
                        "з діагоналлю <b>AC = 8√2</b>.\n\n"
                        "обчисліть об'єм <b>V</b> цього циліндра. у відповідь запишіть значення виразу <b>V / π</b>."
                    ),
                    hint="сторона квадрата a = d / √2. висота циліндра h = a, радіус r = a / 2. формула об'єму: V = π · r² · h.",
                    correct_answer="128",
                    difficulty=3,
                    is_nmt=True,
                    diagram_svg=diagram_cylinder(d=8, h=8),
                    detailed_solution=(
                        "1. сторона осьового перерізу: a = (8√2) / √2 = 8.\n"
                        "2. висота h = 8, радіус r = 8 / 2 = 4.\n"
                        "3. об'єм V = π · 4² · 8 = 128π  ⟹  V / π = 128.\n"
                        "відповідь: 128."
                    ),
                )
            else:
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="прямокутний паралелепіпед",
                    question=(
                        "на рисунку зображено прямокутний паралелепіпед <b>ABCDA₁B₁C₁D₁</b>.\n"
                        "сторони основи дорівнюють <b>AB = 3</b>, <b>AD = 4</b>.\n"
                        "діагональ паралелепіпеда <b>BD₁</b> утворює з площиною основи кут <b>45°</b>.\n\n"
                        "обчисліть об'єм <b>V</b> цього паралелепіпеда."
                    ),
                    hint="діагональ основи BD = √(AB² + AD²). оскільки кут нахилу 45°, висота DD₁ = BD. об'єм V = a · b · h.",
                    correct_answer="60",
                    difficulty=3,
                    is_nmt=True,
                    diagram_svg=diagram_box_prism(a=3, b=4, angle=45),
                    detailed_solution=(
                        "1. діагональ прямокутної основи: BD = √(3² + 4²) = 5.\n"
                        "2. у трикутнику D₁DB кут 45°, тому висота DD₁ = BD = 5.\n"
                        "3. об'єм V = 3 · 4 · 5 = 60.\n"
                        "відповідь: 60."
                    ),
                )

        # --- 7. НМТ: Функції та графіки (Кількість коренів) ---
        if "графік" in top_lower or "функці" in top_lower and "похідн" not in top_lower:
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="кількість коренів за графіком",
                question=(
                    "на рисунку зображено графік неперервної функції <b>y = f(x)</b>, "
                    "визначеної на проміжку [-4; 5].\n\n"
                    "користуючись рисунком, визначте кількість дійсних коренів рівняння <b>f(x) = 1</b> на цьому проміжку."
                ),
                hint="знайди кількість спільних точок перетину між графіком кривої та прямою y = 1.",
                correct_answer="3",
                difficulty=2,
                is_nmt=True,
                diagram_svg=diagram_function_roots(),
                detailed_solution=(
                    "1. рівняння f(x) = 1 графічно відповідає перетину y = f(x) та прямої y = 1.\n"
                    "2. пряма y = 1 перетинає графік рівно у трьох точках.\n"
                    "відповідь: 3."
                ),
            )

        # --- 8. НМТ: Геометричний зміст похідної ---
        if "похідн" in top_lower:
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="геометричний зміст похідної",
                question=(
                    "на рисунку зображено графік функції <b>y = f(x)</b> та дотичну до нього в точці з абсцисою <b>x₀</b>.\n"
                    "дотична проходить через вузли координатної сітки: <b>A(-2; -1)</b> та <b>B(2; 5)</b>.\n\n"
                    "знайдіть значення похідної <b>f'(x₀)</b>. у відповідь запишіть десятковий дріб (наприклад 1.5)."
                ),
                hint="значення похідної в точці дотику дорівнює кутовому коефіцієнту дотичної: f'(x₀) = k = (y₂ - y₁) / (x₂ - x₁).",
                correct_answer="1.5",
                difficulty=3,
                is_nmt=True,
                diagram_svg=diagram_derivative_tangent(),
                detailed_solution=(
                    "1. кутовий коефіцієнт дотичної: k = (5 - (-1)) / (2 - (-2)) = 6 / 4 = 1.5.\n"
                    "2. за геометричним змістом похідної: f'(x₀) = k = 1.5.\n"
                    "відповідь: 1.5."
                ),
            )

        # --- 9. НМТ: Вектори та координати ---
        if "вектор" in top_lower or "координат" in top_lower:
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="скалярний добуток векторів",
                question=(
                    "на рисунку в прямокутній системі координат зображено вектори <b>a⃗</b> та <b>b⃗</b>, "
                    "початки яких збігаються з початком O(0; 0).\n"
                    "кінець a⃗ лежить у точці A(3; 4), а кінець b⃗ — у точці B(6; -2).\n\n"
                    "знайдіть скалярний добуток векторів <b>a⃗ · b⃗</b>."
                ),
                hint="формула скалярного добутку векторів: a⃗ · b⃗ = x₁ · x₂ + y₁ · y₂.",
                correct_answer="10",
                difficulty=2,
                is_nmt=True,
                diagram_svg=diagram_vectors(),
                detailed_solution=(
                    "1. координати векторів: a⃗ = (3; 4), b⃗ = (6; -2).\n"
                    "2. a⃗ · b⃗ = 3 · 6 + 4 · (-2) = 18 - 8 = 10.\n"
                    "відповідь: 10."
                ),
            )

        # --- 10. НМТ: Чотирикутники (Ромб) ---
        if "ромб" in top_lower or "чотирикутн" in top_lower:
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="діагоналі та периметр ромба",
                question=(
                    "на рисунку зображено ромб <b>ABCD</b>, діагоналі якого перетинаються в точці O.\n"
                    "довжини діагоналей ромба дорівнюють <b>AC = 24</b> та <b>BD = 10</b>.\n\n"
                    "обчисліть периметр <b>P</b> цього ромба."
                ),
                hint="діагоналі ромба перпендикулярні й діляться навпіл: AO = AC/2, BO = BD/2. сторона a = √(AO² + BO²). периметр P = 4a.",
                correct_answer="52",
                difficulty=3,
                is_nmt=True,
                diagram_svg=diagram_rhombus_diagonals(d1=24, d2=10, side=13),
                detailed_solution=(
                    "1. половини діагоналей: AO = 12, BO = 5.\n"
                    "2. сторона ромба за теоремою Піфагора: AB = √(12² + 5²) = √169 = 13.\n"
                    "3. периметр P = 4 · 13 = 52.\n"
                    "відповідь: 52."
                ),
            )

        # 11. Лінійні рівняння (7 клас)
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

        # 12. Базовий генератор для арифметики та інших тем
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
    """Інтеграція з Google Gemini API для інтелектуального аналізу відповідей та генерації завдань НМТ."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.mock_fallback = MockAIChecker()

    async def _generate_content(
        self,
        prompt: str,
        json_mode: bool = False,
        temperature: float = 0.2,
    ) -> str | None:
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        generation_config: dict[str, object] = {
            "temperature": temperature,
            "maxOutputTokens": 2048,
        }

        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": generation_config,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=20),
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
                        logger.error(
                            "Помилка Gemini API [HTTP %s]: %s",
                            resp.status,
                            error_text,
                        )
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
            "ти — інтерактивний репетитор з математики для підготовки до НМТ та шкільної програми в україні.\n"
            "твій стиль спілкування: доброзичливий, сучасний, лаконічний, виключно маленькими літерами (lowercase).\n\n"
            f"завдання для учня ({grade} клас / формат нмт):\n"
            f"умова: {task_question}\n"
            f"еталонна правильна відповідь: {correct_answer}\n"
            f"відповідь учня: {user_answer}\n\n"
            "інструкція:\n"
            "1. перевір, чи відповідь учня правильна або математично еквівалентна еталонній "
            "(враховуй коми та крапки в десяткових дробах, скорочені дроби, форми запису тощо).\n"
            "2. якщо відповідь неправильна — зрозумій причину неточності (помилка знаку, дії тощо), "
            "але НЕ розкривай одразу фінальну відповідь у полі feedback!\n"
            "3. у полі detailed_solution напиши покроковий хід розв'язку задачі.\n\n"
            "відповідь надай суворо валідним JSON форматом:\n"
            "{\n"
            '  "is_correct": true,\n'
            '  "feedback": "короткий фідбек учню маленькими літерами",\n'
            '  "detailed_solution": "покроковий розв\'язок маленькими літерами"\n'
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
            f"ти — розумний педагогічний ментор з математики для підготовки до НМТ ({grade} клас).\n"
            "твій стиль спілкування: виключно маленькими літерами (lowercase), лаконічний, доброзичливий.\n\n"
            f"умова завдання: {task_question}\n"
            f"{'напрямок думки: ' + custom_hint if custom_hint else ''}\n\n"
            "суворі правила для підказки:\n"
            "1. покажи загальну формулу або геометричну властивість.\n"
            "2. КАТЕГОРИЧНО ЗАБОРОНЕНО підставляти конкретні числа із задачі у формулу!\n"
            "3. КАТЕГОРИЧНО ЗАБОРОНЕНО розкривати кінцеву відповідь.\n"
            "4. підказка має бути короткою (1-2 речення).\n"
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
            f"ти — професійний укладач завдань з математики для НМТ та шкільної програми для {grade} класу в україні.\n"
            f"обрана тема: {topic}\n"
            "твій стиль: виключно маленькими літерами (lowercase), чіткий, академічний.\n\n"
            "завдання:\n"
            "згенеруй повноцінне прикладне завдання у форматі НМТ (Національного мультипредметного тесту) або програми високого рівня (2-3 логічні кроки).\n"
            "якщо тема стосується геометрії (планіметрія, стереометрія) або графіків функцій/векторів — ОБОВ'ЯЗКОВО сформуй валідний SVG-малюнок (diagram_svg)!\n\n"
            "вимоги до SVG (diagram_svg):\n"
            "- viewBox='0 0 380 230' xmlns='http://www.w3.org/2000/svg' class='math-diagram-svg'.\n"
            "- фон: <rect x='8' y='8' width='364' height='214' rx='12' fill='#ebd6c1' stroke='#d6b99d' stroke-width='1.5'/>\n"
            "- основні лінії stroke='#4d301a' stroke-width='2.2', пунктири для висот/осей stroke-dasharray='4,4'.\n"
            "- підписи вершин (A, B, C, D...): fill='#4d301a' font-family='Libertinus Sans, serif' font-size='16' font-weight='700'.\n\n"
            "правила для умови (question):\n"
            "1. чіткий опис рисунка ('на рисунку зображено...').\n"
            "2. відповідь (correct_answer) має бути ОДНИМ числом (ціле число або десятковий дріб, наприклад: 12, 1.5, 384, 52), щоб учень міг записати його в бланк відповідей.\n"
            "3. підказка (hint): формула та хід думки БЕЗ підстановки чисел.\n"
            "4. покроковий розв'язок (detailed_solution): розгорнуте пояснення кожного кроку.\n"
            "5. складність: від 2 до 3.\n\n"
            "відповідь надай суворо валідним JSON форматом:\n"
            "{\n"
            '  "title": "коротка назва завдання",\n'
            '  "question": "текст умови завдання",\n'
            '  "hint": "формула або правило",\n'
            '  "correct_answer": "числове значення",\n'
            '  "difficulty": 3,\n'
            '  "is_nmt": true,\n'
            '  "diagram_svg": "<svg viewBox=\\"0 0 380 230\\" ...>...</svg>",\n'
            '  "detailed_solution": "покроковий розв\'язок"\n'
            "}"
        )

        raw = await self._generate_content(prompt, json_mode=True, temperature=0.7)
        if raw:
            try:
                parsed = json.loads(raw)
                diagram_svg = parsed.get("diagram_svg")
                if isinstance(diagram_svg, str) and not diagram_svg.strip().startswith("<svg"):
                    diagram_svg = None

                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title=str(parsed.get("title", "завдання")).lower(),
                    question=str(parsed["question"]).lower(),
                    hint=str(parsed.get("hint", "скористайся відповідним правилом або формулою.")).lower(),
                    correct_answer=str(parsed["correct_answer"]).lower().strip(),
                    difficulty=int(parsed.get("difficulty", 2)),
                    diagram_svg=diagram_svg,
                    is_nmt=bool(parsed.get("is_nmt", True if grade >= 10 else False)),
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

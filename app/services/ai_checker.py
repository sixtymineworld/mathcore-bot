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
        if "рівнян" in top_lower and "порівнян" not in top_lower and "квадрат" not in top_lower and grade >= 6:
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

        # 12. Шкільна арифметика для молодших і середніх класів
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
                    hint="порівняй два числа на числовому промені: більше те, яке стоїть правіше.",
                    correct_answer=str(ans),
                    difficulty=1,
                    detailed_solution=f"число {ans} є більшим за інше число.\nвідповідь: {ans}.",
                )
            if "фігур" in top_lower or "трикутн" in top_lower or "прямокутн" in top_lower:
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="геометричні фігури",
                    question="скільки сторін має геометрична фігура <b>трикутник</b>?",
                    hint="згадай назву фігури: вона має стільки ж сторін, скільки й кутів.",
                    correct_answer="3",
                    difficulty=1,
                    detailed_solution="трикутник має 3 сторони та 3 вершини.\nвідповідь: 3.",
                )
            n1 = random.randint(1, 7)
            n2 = random.randint(1, 10 - n1)
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="додавання у межах 10",
                question=f"обчисліть значення суми:\n\n<b>{n1} + {n2} = ?</b>",
                hint="об'єднай обидва доданки разом на числовому промені.",
                correct_answer=str(n1 + n2),
                difficulty=1,
                detailed_solution=f"додаємо числа: {n1} + {n2} = {n1 + n2}.\nвідповідь: {n1 + n2}.",
            )

        if grade == 2:
            n1 = random.randint(12, 65)
            n2 = random.randint(5, 30)
            if random.random() < 0.5:
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="додавання в межах 100",
                    question=f"обчисліть значення виразу:\n\n<b>{n1} + {n2} = ?</b>",
                    hint="додай десятки до десятків, а одиниці до одиниць.",
                    correct_answer=str(n1 + n2),
                    difficulty=1,
                    detailed_solution=f"1. {n1} + {n2} = {n1 + n2}.\nвідповідь: {n1 + n2}.",
                )
            top_n = n1 + n2
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="віднімання в межах 100",
                question=f"обчисліть значення виразу:\n\n<b>{top_n} - {n2} = ?</b>",
                hint="відніми від зменшуваного від'ємник порозрядно.",
                correct_answer=str(n1),
                difficulty=1,
                detailed_solution=f"1. {top_n} - {n2} = {n1}.\nвідповідь: {n1}.",
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
                    detailed_solution=f"оскільки {f1} · {f2} = {prod}, то {prod} : {f1} = {f2}.\nвідповідь: {f2}.",
                )
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="табличне множення",
                question=f"обчисліть значення добутку:\n\n<b>{f1} · {f2} = ?</b>",
                hint="пригадай відповідний рядок таблиці множення.",
                correct_answer=str(prod),
                difficulty=1,
                detailed_solution=f"множимо числа: {f1} · {f2} = {prod}.\nвідповідь: {prod}.",
            )

        if grade == 4:
            a = random.randint(15, 80)
            b = random.randint(4, 9)
            return GeneratedTask(
                grade=grade,
                topic=topic,
                title="множення багатоцифрових чисел",
                question=f"обчисліть добуток:\n\n<b>{a} · {b} = ?</b>",
                hint="розклади двоцифрове число на десятки та одиниці й помнож кожну частину окремо.",
                correct_answer=str(a * b),
                difficulty=1,
                detailed_solution=f"1. {a} · {b} = {a * b}.\nвідповідь: {a * b}.",
            )

        if grade in (5, 6):
            if "відсот" in top_lower:
                pct = random.choice([10, 20, 25, 50])
                base = random.choice([80, 120, 200, 300, 400])
                ans = int(base * pct / 100)
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="знаходження відсотка від числа",
                    question=f"знайдіть <b>{pct}%</b> від числа <b>{base}</b>.",
                    hint="щоб знайти відсоток від числа, перетвори відсотки у десятковий дріб та помнож на дане число.",
                    correct_answer=str(ans),
                    difficulty=1,
                    detailed_solution=f"1. {pct}% = {pct/100:.2g}.\n2. {base} · {pct/100:.2g} = {ans}.\nвідповідь: {ans}.",
                )
            if "дріб" in top_lower:
                denom = random.choice([5, 7, 9, 11, 13])
                num1 = random.randint(1, denom - 2)
                num2 = random.randint(1, denom - num1)
                return GeneratedTask(
                    grade=grade,
                    topic=topic,
                    title="додавання звичайних дробів",
                    question=f"обчисліть суму дробів з однаковими знаменниками:\n\n<b>{num1}/{denom} + {num2}/{denom} = ?</b>\n(у відповідь запишіть тільки чисельник отриманого дробу)",
                    hint="при додаванні дробів з однаковими знаменниками знаменник залишають без змін, а чисельники додають.",
                    correct_answer=str(num1 + num2),
                    difficulty=1,
                    detailed_solution=f"додаємо чисельники: {num1} + {num2} = {num1 + num2}, знаменник {denom}.\nчисельник дорівнює: {num1 + num2}.\nвідповідь: {num1 + num2}.",
                )

        # 13. Базовий генератор для арифметики та інших тем
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

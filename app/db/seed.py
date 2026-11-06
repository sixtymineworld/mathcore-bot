import logging
from sqlalchemy import select

from app.db.base import get_session
from app.db.models import Task, Topic

logger = logging.getLogger(__name__)

INITIAL_CURRICULUM = [
    # --- 5 клас ---
    {
        "grade": 5,
        "title": "🔢 Натуральні числа та дії з ними",
        "description": "Додавання, віднімання, множення та ділення натуральних чисел.",
        "order_num": 1,
        "tasks": [
            {
                "title": "Обчислення виразу",
                "question_text": "Обчисліть значення виразу:\n\n<b>145 + 328 - 113 = ?</b>",
                "solution_hint": "Спочатку виконай додавання: 145 + 328 = 473, потім відніми 113.",
                "correct_answer": "360",
                "difficulty": 1,
            },
            {
                "title": "Ділення з остачею",
                "question_text": "Знайдіть остачу від ділення числа <b>47</b> на <b>5</b>.",
                "solution_hint": "Згадай: 47 = 5 * 9 + остача. Яке число залишилось?",
                "correct_answer": "2",
                "difficulty": 1,
            },
        ],
    },
    {
        "grade": 5,
        "title": "🍰 Звичайні дроби",
        "description": "Поняття дробу, правильні та неправильні дроби.",
        "order_num": 2,
        "tasks": [
            {
                "title": "Додавання дробів з однаковими знаменниками",
                "question_text": "Знайдіть суму дробів:\n\n<b>2/7 + 3/7 = ?</b>\n<i>(відповідь запишіть у вигляді a/b)</i>",
                "solution_hint": "Якщо знаменники однакові, знаменник залишається тим самим, а чисельники додаються: (2 + 3)/7.",
                "correct_answer": "5/7",
                "difficulty": 1,
            },
        ],
    },
    # --- 6 клас ---
    {
        "grade": 6,
        "title": "⚖️ Пропорції та відсотки",
        "description": "Основна властивість пропорції, знаходження відсотків від числа.",
        "order_num": 1,
        "tasks": [
            {
                "title": "Знаходження відсотка від числа",
                "question_text": "Знайдіть <b>20%</b> від числа <b>150</b>.",
                "solution_hint": "20% — це 0.2 або 20/100. Помнож 150 на 0.2 або поділи на 5.",
                "correct_answer": "30",
                "difficulty": 1,
            },
            {
                "title": "Основна властивість пропорції",
                "question_text": "Розв'яжіть пропорцію:\n\n<b>x / 6 = 10 / 15</b>\nЗнайдіть <b>x</b>.",
                "solution_hint": "Добуток крайніх членів дорівнює добутку середніх: 15 * x = 6 * 10.",
                "correct_answer": "4",
                "difficulty": 2,
            },
        ],
    },
    # --- 7 клас ---
    {
        "grade": 7,
        "title": "⚡ Лінійні рівняння з однією змінною",
        "description": "Розв'язування лінійних рівнянь та текстових задач за їх допомогою.",
        "order_num": 1,
        "tasks": [
            {
                "title": "Просте лінійне рівняння",
                "question_text": "Розв'яжіть рівняння:\n\n<b>3x - 7 = 14</b>\nЗнайдіть <b>x</b>.",
                "solution_hint": "Перенеси -7 вправо з протилежним знаком: 3x = 14 + 7, тобто 3x = 21.",
                "correct_answer": "7",
                "difficulty": 1,
            },
            {
                "title": "Рівняння з дужками",
                "question_text": "Розв'яжіть рівняння:\n\n<b>2(x + 3) = 18</b>\nЗнайдіть <b>x</b>.",
                "solution_hint": "Розкрий дужки: 2x + 6 = 18, або одразу поділи обидві частини на 2: x + 3 = 9.",
                "correct_answer": "6",
                "difficulty": 2,
            },
        ],
    },
    {
        "grade": 7,
        "title": "📐 Трикутники та їх властивості",
        "description": "Сума кутів трикутника, рівнобедрений та прямокутний трикутник.",
        "order_num": 2,
        "tasks": [
            {
                "title": "Сума кутів трикутника",
                "question_text": "У трикутнику два кути дорівнюють <b>50°</b> та <b>60°</b>.\nЗнайдіть третій кут (у градусах, введіть лише число).",
                "solution_hint": "Сума кутів будь-якого трикутника на площині дорівнює 180°.",
                "correct_answer": "70",
                "difficulty": 1,
            },
        ],
    },
    # --- 8 клас ---
    {
        "grade": 8,
        "title": "🔲 Квадратні корені та дійсні числа",
        "description": "Арифметичний квадратний корінь та його властивості.",
        "order_num": 1,
        "tasks": [
            {
                "title": "Арифметичний корінь",
                "question_text": "Обчисліть:\n\n<b>√(144) + √(25) = ?</b>",
                "solution_hint": "√(144) = 12, √(25) = 5. Додай ці два значення.",
                "correct_answer": "17",
                "difficulty": 1,
            },
        ],
    },
    {
        "grade": 8,
        "title": "🔺 Теорема Піфагора",
        "description": "Зв'язок між сторонами у прямокутному трикутнику.",
        "order_num": 2,
        "tasks": [
            {
                "title": "Пошук гіпотенузи",
                "question_text": "Катети прямокутного трикутника дорівнюють <b>6 см</b> і <b>8 см</b>.\nЗнайдіть гіпотенузу (введіть лише число).",
                "solution_hint": "За теоремою Піфагора: c² = a² + b² = 6² + 8² = 36 + 64 = 100. Звідси c = √100.",
                "correct_answer": "10",
                "difficulty": 2,
            },
        ],
    },
    # --- 9 клас ---
    {
        "grade": 9,
        "title": "🎯 Квадратні рівняння та теорема Вієта",
        "description": "Дискримінант, формули коренів та властивості коренів.",
        "order_num": 1,
        "tasks": [
            {
                "title": "Дискримінант",
                "question_text": "Знайдіть дискримінант <b>D</b> для квадратного рівняння:\n\n<b>x² - 5x + 6 = 0</b>",
                "solution_hint": "Формула дискримінанта: D = b² - 4ac. Тут a=1, b=-5, c=6. D = (-5)² - 4*1*6.",
                "correct_answer": "1",
                "difficulty": 1,
            },
        ],
    },
    # --- 10-11 класи ---
    {
        "grade": 10,
        "title": "📈 Тригонометричні функції",
        "description": "Синус, косинус, тангенс та основні тригонометричні тотожності.",
        "order_num": 1,
        "tasks": [
            {
                "title": "Основна тригонометрична тотожність",
                "question_text": "Обчисліть значення виразу:\n\n<b>sin²(35°) + cos²(35°) = ?</b>",
                "solution_hint": "Основна тотожність: sin²(α) + cos²(α) завжди дорівнює одному сталому числу для будь-якого кута α.",
                "correct_answer": "1",
                "difficulty": 1,
            },
        ],
    },
    {
        "grade": 11,
        "title": "📉 Похідна та її застосування",
        "description": "Правила диференціювання та геометричний зміст похідної.",
        "order_num": 1,
        "tasks": [
            {
                "title": "Похідна степеневої функції",
                "question_text": "Знайдіть значення похідної функції <b>f(x) = x³</b> у точці <b>x = 2</b>.",
                "solution_hint": "Похідна f'(x) = 3x². Підстав x = 2: 3 * (2)².",
                "correct_answer": "12",
                "difficulty": 2,
            },
        ],
    },
]


async def seed_initial_data() -> None:
    """Заповнює базу даних початковими темами та задачами, якщо вони ще відсутні."""
    async with get_session() as session:
        # Перевіряємо, чи база вже містить теми
        stmt = select(Topic).limit(1)
        result = await session.execute(stmt)
        existing_topic = result.scalar_one_or_none()

        if existing_topic is not None:
            logger.info("Початкові дані вже існують у базі, сідінг пропущено.")
            return

        logger.info("Початок наповнення бази навчальними матеріалами...")

        for topic_data in INITIAL_CURRICULUM:
            tasks_data = topic_data.get("tasks", [])
            topic = Topic(
                grade=topic_data["grade"],
                title=topic_data["title"],
                description=topic_data.get("description"),
                order_num=topic_data["order_num"],
            )
            session.add(topic)
            await session.flush()  # Отримуємо topic.id для зв'язку із завданнями

            for task_data in tasks_data:
                task = Task(
                    topic_id=topic.id,
                    title=task_data["title"],
                    question_text=task_data["question_text"],
                    solution_hint=task_data.get("solution_hint"),
                    correct_answer=task_data["correct_answer"],
                    difficulty=task_data.get("difficulty", 1),
                )
                session.add(task)

        await session.commit()
        logger.info("Базу даних успішно наповнено навчальними темами та задачами!")

import logging
from sqlalchemy import delete, select

from app.db.base import get_session
from app.db.models import Task, Topic

logger = logging.getLogger(__name__)

INITIAL_CURRICULUM = [
    # --- 5 клас ---
    {
        "grade": 5,
        "title": "натуральні числа та дії з ними",
        "description": "додавання, віднімання, множення та ділення натуральних чисел.",
        "order_num": 1,
        "tasks": [
            {
                "title": "обчислення виразу",
                "question_text": "обчисліть значення виразу:\n\n<b>145 + 328 - 113 = ?</b>",
                "solution_hint": "згадай черговість дій: додавання та віднімання виконуються по черзі зліва направо.",
                "correct_answer": "360",
                "difficulty": 1,
            },
            {
                "title": "ділення з остачею",
                "question_text": "знайдіть остачу від ділення числа <b>47</b> на <b>5</b>.",
                "solution_hint": "подумай, яке найближче менше число ділиться на 5 без остачі, та знайди різницю з 47.",
                "correct_answer": "2",
                "difficulty": 1,
            },
        ],
    },
    {
        "grade": 5,
        "title": "звичайні дроби",
        "description": "поняття дробу, правильні та неправильні дроби.",
        "order_num": 2,
        "tasks": [
            {
                "title": "додавання дробів з однаковими знаменниками",
                "question_text": "знайдіть суму дробів:\n\n<b>2/7 + 3/7 = ?</b>\n<i>(відповідь запишіть у вигляді a/b)</i>",
                "solution_hint": "формула додавання дробів з однаковими знаменниками: a/c + b/c = (a + b)/c.",
                "correct_answer": "5/7",
                "difficulty": 1,
            },
        ],
    },
    # --- 6 клас ---
    {
        "grade": 6,
        "title": "пропорції та відсотки",
        "description": "основна властивість пропорції, знаходження відсотків від числа.",
        "order_num": 1,
        "tasks": [
            {
                "title": "знаходження відсотка від числа",
                "question_text": "знайдіть <b>20%</b> від числа <b>150</b>.",
                "solution_hint": "перетвори відсотки у дріб або скористайся правилом: b = a * (p / 100).",
                "correct_answer": "30",
                "difficulty": 1,
            },
            {
                "title": "основна властивість пропорції",
                "question_text": "розв'яжіть пропорцію:\n\n<b>x / 6 = 10 / 15</b>\nзнайдіть <b>x</b>.",
                "solution_hint": "для пропорції a/b = c/d діє формула: a * d = b * c. підстав свої члени виразу.",
                "correct_answer": "4",
                "difficulty": 2,
            },
        ],
    },
    # --- 7 клас ---
    {
        "grade": 7,
        "title": "лінійні рівняння з однією змінною",
        "description": "розв'язування лінійних рівнянь та текстових задач за їх допомогою.",
        "order_num": 1,
        "tasks": [
            {
                "title": "просте лінійне рівняння",
                "question_text": "розв'яжіть рівняння:\n\n<b>3x - 7 = 14</b>\nзнайдіть <b>x</b>.",
                "solution_hint": "перенеси відомий доданок у праву частину зі зміною знака, зведи до вигляду ax = b, звідки x = b / a.",
                "correct_answer": "7",
                "difficulty": 1,
            },
            {
                "title": "рівняння з дужками",
                "question_text": "розв'яжіть рівняння:\n\n<b>2(x + 3) = 18</b>\nзнайдіть <b>x</b>.",
                "solution_hint": "розподільна властивість: a(b + c) = ab + ac, або одразу поділи обидві частини рівняння на коефіцієнт a.",
                "correct_answer": "6",
                "difficulty": 2,
            },
        ],
    },
    {
        "grade": 7,
        "title": "трикутники та їх властивості",
        "description": "сума кутів трикутника, рівнобедрений та прямокутний трикутник.",
        "order_num": 2,
        "tasks": [
            {
                "title": "сума кутів трикутника",
                "question_text": "у трикутнику два кути дорівнюють <b>50°</b> та <b>60°</b>.\nзнайдіть третій кут (введіть лише число).",
                "solution_hint": "теорема про суму кутів трикутника: ∠a + ∠b + ∠c = 180°.",
                "correct_answer": "70",
                "difficulty": 1,
            },
        ],
    },
    # --- 8 клас ---
    {
        "grade": 8,
        "title": "квадратні корені та дійсні числа",
        "description": "арифметичний квадратний корінь та його властивості.",
        "order_num": 1,
        "tasks": [
            {
                "title": "арифметичний корінь",
                "question_text": "обчисліть:\n\n<b>√(144) + √(25) = ?</b>",
                "solution_hint": "знайди корінь з кожного числа окремо (√a = b означає, що b² = a), а потім додай результати.",
                "correct_answer": "17",
                "difficulty": 1,
            },
        ],
    },
    {
        "grade": 8,
        "title": "теорема піфагора",
        "description": "зв'язок між сторонами у прямокутному трикутнику.",
        "order_num": 2,
        "tasks": [
            {
                "title": "пошук гіпотенузи",
                "question_text": "катети прямокутного трикутника дорівнюють <b>6 см</b> і <b>8 см</b>.\nзнайдіть гіпотенузу (введіть лише число).",
                "solution_hint": "теорема піфагора: c² = a² + b², де c — шукана гіпотенуза, a та b — катети.",
                "correct_answer": "10",
                "difficulty": 2,
            },
        ],
    },
    # --- 9 клас ---
    {
        "grade": 9,
        "title": "квадратні рівняння та теорема вієта",
        "description": "дискримінант, формули коренів та властивості коренів.",
        "order_num": 1,
        "tasks": [
            {
                "title": "дискримінант",
                "question_text": "знайдіть дискримінант <b>D</b> для квадратного рівняння:\n\n<b>x² - 5x + 6 = 0</b>",
                "solution_hint": "формула дискримінанта для ax² + bx + c = 0: D = b² - 4ac. визнач свої a, b, c і порахуй.",
                "correct_answer": "1",
                "difficulty": 1,
            },
        ],
    },
    # --- 10-11 класи ---
    {
        "grade": 10,
        "title": "тригонометричні функції",
        "description": "синус, косинус, тангенс та основні тригонометричні тотожності.",
        "order_num": 1,
        "tasks": [
            {
                "title": "основна тригонометрична тотожність",
                "question_text": "обчисліть значення виразу:\n\n<b>sin²(35°) + cos²(35°) = ?</b>",
                "solution_hint": "основна тригонометрична тотожність: sin²(α) + cos²(α) = 1 для будь-якого кута α.",
                "correct_answer": "1",
                "difficulty": 1,
            },
        ],
    },
    {
        "grade": 11,
        "title": "похідна та її застосування",
        "description": "правила диференціювання та геометричний зміст похідної.",
        "order_num": 1,
        "tasks": [
            {
                "title": "похідна степеневої функції",
                "question_text": "знайдіть значення похідної функції <b>f(x) = x³</b> у точці <b>x = 2</b>.",
                "solution_hint": "формула похідної степеневої функції: (xⁿ)' = n * xⁿ⁻¹. знайди загальний вираз і підстав значення точки.",
                "correct_answer": "12",
                "difficulty": 2,
            },
        ],
    },
]


async def seed_initial_data() -> None:
    """Заповнює або оновлює навчальні теми та задачі за єдиним стилем."""
    async with get_session() as session:
        # Очищуємо старі теми та завдання, щоб синхронізувати з актуальним стилем
        await session.execute(delete(Task))
        await session.execute(delete(Topic))
        await session.commit()

        logger.info("Синхронізація навчальних матеріалів у базі даних...")

        for topic_data in INITIAL_CURRICULUM:
            tasks_data = topic_data.get("tasks", [])
            topic = Topic(
                grade=topic_data["grade"],
                title=topic_data["title"],
                description=topic_data.get("description"),
                order_num=topic_data["order_num"],
            )
            session.add(topic)
            await session.flush()

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

import logging
from sqlalchemy import delete, func, select

from app.db.base import get_session
from app.db.curriculum import INITIAL_CURRICULUM
from app.db.models import Task, Topic, UserTaskAttempt

logger = logging.getLogger(__name__)


async def seed_initial_data() -> None:
    """Заповнює або оновлює навчальну програму за підручниками О. С. Істера (1–11 класи)."""
    async with get_session() as session:
        # Перевірка кількості наявних тем
        stmt = select(func.count(Topic.id))
        count = (await session.execute(stmt)).scalar() or 0

        # Перевірка: чи завантажені вже оновлені педагогічні підказки (без готових відповідей)
        sample_task = (
            await session.execute(
                select(Task).where(Task.title == "лічба предметів зліва і справа")
            )
        ).scalar_one_or_none()
        needs_refresh = sample_task is not None and (
            "4 + 3" in (sample_task.solution_hint or "")
            or "відповідь" in (sample_task.solution_hint or "")
        )

        # Якщо програма вже містить повний набір тем з актуальними підказками, сід не потрібен
        if count >= len(INITIAL_CURRICULUM) and not needs_refresh:
            logger.info("навчальну програму вже завантажено (%d тем).", count)
            return

        # Якщо база містить застарілий набір або старі підказки, оновлюємо
        if count > 0:
            logger.info(
                "оновлення програми: очищення застарілих матеріалів (%d тем) для імпорту якісних підказок...",
                count,
            )
            await session.execute(delete(UserTaskAttempt))
            await session.execute(delete(Task))
            await session.execute(delete(Topic))
            await session.flush()

        logger.info(
            "синхронізація повної структурованої програми О. С. Істера (%d тем для 1–11 класів)...",
            len(INITIAL_CURRICULUM),
        )

        for topic_data in INITIAL_CURRICULUM:
            tasks_data = topic_data.get("tasks", [])
            topic = Topic(
                grade=topic_data["grade"],
                subject=topic_data.get("subject", "математика"),
                section=topic_data.get("section", "загальний розділ"),
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
                    diagram_svg=task_data.get("diagram_svg"),
                    is_nmt=task_data.get("is_nmt", False),
                    detailed_solution=task_data.get("detailed_solution"),
                )
                session.add(task)

        await session.commit()
        logger.info(
            "базу даних успішно оновлено: %d тем із новими методичними підказками!",
            len(INITIAL_CURRICULUM),
        )

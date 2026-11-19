import logging
from sqlalchemy import delete, func, select

from app.db.base import get_session
from app.db.curriculum.loader import load_curriculum
from app.db.models import Task, Topic, UserTaskAttempt

logger = logging.getLogger(__name__)


async def seed_initial_data() -> None:
    """Заповнює або синхронізує навчальну програму з JSON-фікстур (data/curriculum/)."""
    curriculum = load_curriculum()
    if not curriculum:
        logger.warning("навчальна програма порожня, перевірте файли в data/curriculum/")
        return

    async with get_session() as session:
        stmt = select(func.count(Topic.id))
        count = (await session.execute(stmt)).scalar() or 0

        # Якщо кількість тем відповідає JSON-файлам і зразок актуальний, сід не потрібен
        sample_task = (
            await session.execute(
                select(Task).where(Task.title == "лічба предметів зліва і справа")
            )
        ).scalar_one_or_none()
        needs_refresh = sample_task is not None and (
            "4 + 3" in (sample_task.solution_hint or "")
            or "відповідь" in (sample_task.solution_hint or "")
        )

        if count == len(curriculum) and not needs_refresh:
            logger.info("навчальну програму з JSON вже синхронізовано (%d тем).", count)
            return

        if count > 0:
            logger.info(
                "оновлення навчальної програми (%d тем -> %d тем з JSON)...",
                count,
                len(curriculum),
            )
            await session.execute(delete(UserTaskAttempt))
            await session.execute(delete(Task))
            await session.execute(delete(Topic))
            await session.flush()

        logger.info(
            "імпорт структурованої програми з JSON (%d тем для 1–11 класів)...",
            len(curriculum),
        )

        for topic_data in curriculum:
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
            "базу даних успішно синхронізовано з JSON: %d тем та їх завдань!",
            len(curriculum),
        )

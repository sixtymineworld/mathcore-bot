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

        # Перевірка наявності застарілих статичних завдань з минулих релізів
        has_legacy_static_tasks = (
            await session.execute(
                select(Task.id).where(Task.title == "лічба предметів зліва і справа").limit(1)
            )
        ).scalar_one_or_none() is not None

        if count == len(curriculum) and not has_legacy_static_tasks:
            logger.info("навчальну програму з JSON вже синхронізовано (%d тем).", count)
            return

        if count > 0 or has_legacy_static_tasks:
            logger.info(
                "оновлення структури навчальної програми (%d тем -> %d тем з JSON)...",
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
            topic = Topic(
                grade=topic_data["grade"],
                subject=topic_data.get("subject", "математика"),
                section=topic_data.get("section", "загальний розділ"),
                title=topic_data["title"],
                description=topic_data.get("description"),
                order_num=topic_data["order_num"],
            )
            session.add(topic)

        await session.commit()
        logger.info(
            "базу даних успішно синхронізовано: %d тем (завдання генеруються виключно динамічно)!",
            len(curriculum),
        )

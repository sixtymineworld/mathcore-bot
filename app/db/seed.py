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
        count = (await session.execute(select(func.count(Topic.id)))).scalar() or 0
        if count == len(curriculum):
            logger.info("навчальну програму з JSON вже синхронізовано (%d тем).", count)
            return

        if count > 0:
            logger.info("оновлення структури навчальної програми (%d -> %d тем)...", count, len(curriculum))
            await session.execute(delete(UserTaskAttempt))
            await session.execute(delete(Task))
            await session.execute(delete(Topic))
            await session.flush()

        logger.info("імпорт структурованої програми (%d тем для 1–11 класів)...", len(curriculum))
        for t in curriculum:
            session.add(Topic(
                grade=t["grade"],
                subject=t.get("subject", "математика"),
                section=t.get("section", "загальний розділ"),
                title=t["title"],
                description=t.get("description"),
                order_num=t["order_num"],
            ))

        await session.commit()
        logger.info("базу даних успішно синхронізовано: %d тем!", len(curriculum))

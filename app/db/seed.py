import logging
from sqlalchemy import delete, func, select

from app.db.base import get_session
from app.db.curriculum.loader import load_curriculum
from app.db.models import Task, Topic, UserTaskAttempt

logger = logging.getLogger(__name__)


async def seed_initial_data() -> None:
    """Заповнює або синхронізує навчальну програму з JSON-фікстур без видалення даних користувачів."""
    curriculum = load_curriculum()
    if not curriculum:
        logger.warning("навчальна програма порожня, перевірте файли в data/curriculum/")
        return

    async with get_session() as session:
        # Отримуємо наявні теми за (grade, title)
        existing_res = await session.execute(select(Topic.grade, Topic.title))
        existing_set = {(row[0], row[1]) for row in existing_res.all()}

        new_topics = []
        for t in curriculum:
            key = (t["grade"], t["title"])
            if key not in existing_set:
                new_topics.append(Topic(
                    grade=t["grade"],
                    subject=t.get("subject", "математика"),
                    section=t.get("section", "загальний розділ"),
                    title=t["title"],
                    description=t.get("description"),
                    order_num=t["order_num"],
                ))
                existing_set.add(key)

        if new_topics:
            session.add_all(new_topics)
            await session.commit()
            logger.info("синхронізація: додано %d нових тем до програми.", len(new_topics))
        else:
            logger.info("навчальну програму вже повністю синхронізовано (%d тем).", len(existing_set))

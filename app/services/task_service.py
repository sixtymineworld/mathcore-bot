import logging
from sqlalchemy import select

from app.db.base import get_session
from app.db.models import Task, Topic, User

logger = logging.getLogger(__name__)


class TaskService:
    """Сервіс для роботи з навчальними темами, завданнями та профілями користувачів."""

    @staticmethod
    async def get_topics_by_grade(grade: int) -> list[Topic]:
        """Повертає список тем для вказаного класу, відсортованих за порядком."""
        async with get_session() as session:
            stmt = (
                select(Topic)
                .where(Topic.grade == grade)
                .order_by(Topic.order_num, Topic.id)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_topic_by_id(topic_id: int) -> Topic | None:
        """Отримує тему за її ID."""
        async with get_session() as session:
            stmt = select(Topic).where(Topic.id == topic_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_tasks_by_topic(topic_id: int) -> list[Task]:
        """Повертає список усіх завдань для певної теми."""
        async with get_session() as session:
            stmt = (
                select(Task)
                .where(Task.topic_id == topic_id)
                .order_by(Task.difficulty, Task.id)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_task_by_id(task_id: int) -> Task | None:
        """Отримує завдання за його ID."""
        async with get_session() as session:
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_next_task(topic_id: int, current_task_id: int) -> Task | None:
        """Знаходить наступне завдання в темі після поточного."""
        async with get_session() as session:
            # Шукаємо перше завдання цієї ж теми з більшим ID
            stmt = (
                select(Task)
                .where(Task.topic_id == topic_id, Task.id > current_task_id)
                .order_by(Task.id)
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_tg_id(tg_id: int) -> User | None:
        """Отримує користувача за його Telegram ID."""
        async with get_session() as session:
            stmt = select(User).where(User.tg_id == tg_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def upsert_user(
        tg_id: int,
        first_name: str,
        username: str | None = None,
        grade: int | None = None,
    ) -> User:
        """Створює нового користувача або оновлює дані наявного."""
        async with get_session() as session:
            stmt = select(User).where(User.tg_id == tg_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()

            if db_user is None:
                db_user = User(
                    tg_id=tg_id,
                    username=username,
                    first_name=first_name,
                    grade=grade,
                )
                session.add(db_user)
            else:
                db_user.first_name = first_name
                db_user.username = username
                if grade is not None:
                    db_user.grade = grade

            await session.commit()
            await session.refresh(db_user)
            return db_user

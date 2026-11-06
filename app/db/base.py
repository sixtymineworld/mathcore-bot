import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Базовий декларативний клас SQLAlchemy 2.0 для всіх моделей."""
    pass


# Створення асинхронного рушія для MySQL через asyncmy
async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Фабрика асинхронних сесій
async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронний контекстний менеджер для роботи із сесією бази даних."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Ініціалізація бази даних: створення всіх зареєстрованих таблиць."""
    # Імпорт моделей для реєстрації метаданих у Base
    import app.db.models  # noqa: F401

    logger.info("Ініціалізація таблиць бази даних...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблиці бази даних успішно перевірені/створені.")

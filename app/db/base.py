import asyncio
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


# Налаштування параметрів підключення для різних типів баз даних
_engine_kwargs = {
    "echo": settings.DB_ECHO,
}
if "sqlite" in settings.DATABASE_URL:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_recycle"] = 3600

# Створення асинхронного рушія SQLAlchemy 2.0
async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    **_engine_kwargs,
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


_db_init_lock = asyncio.Lock()
_db_initialized = False


async def init_db() -> None:
    """Ініціалізація бази даних: створення таблиць та наповнення початковими даними."""
    global _db_initialized
    if _db_initialized:
        return

    async with _db_init_lock:
        if _db_initialized:
            return

        # Імпорт моделей для реєстрації метаданих у Base
        import app.db.models  # noqa: F401
        from app.db.seed import seed_initial_data

        logger.info("Ініціалізація таблиць бази даних...")
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Таблиці бази даних успішно перевірені/створені.")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("Таблиці бази даних вже існують: %s", e)
            else:
                raise

        # Заповнюємо початковими темами та задачами
        await seed_initial_data()
        _db_initialized = True

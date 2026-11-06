import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import common_router, tasks_router
from app.config import settings
from app.db.base import async_engine, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("mathcore")


async def on_startup(bot: Bot) -> None:
    """Хук запуску: ініціалізація бази даних та перевірка зв'язку з Telegram API."""
    logger.info("Ініціалізація компонентів mathcore...")
    await init_db()

    bot_info = await bot.get_me()
    logger.info(
        "Бот успішно запущений: @%s [ID: %s]",
        bot_info.username,
        bot_info.id,
    )


async def on_shutdown(bot: Bot) -> None:
    """Хук зупинки: коректне закриття з'єднань з базою даних."""
    logger.info("Завершення роботи mathcore (graceful shutdown)...")
    await async_engine.dispose()
    logger.info("Пул з'єднань з базою даних закрито.")


async def main() -> None:
    """Головна точка входу для запуску Telegram-бота mathcore."""
    if not settings.BOT_TOKEN:
        logger.error(
            "Помилка: BOT_TOKEN не встановлено! "
            "Скопіюйте файл .env.example у .env та вкажіть дійсний токен Telegram бота."
        )
        return

    # Ініціалізація бота з HTML форматуванням за замовчуванням
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Ініціалізація диспетчера зі сховищем FSM у пам'яті
    dp = Dispatcher(storage=MemoryStorage())

    # Реєстрація обробників життєвого циклу
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Реєстрація роутерів
    dp.include_router(common_router)
    dp.include_router(tasks_router)

    try:
        # Пропуск накопичених оновлень та старт polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Початок отримання оновлень (polling)...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        # Закриття клієнтської сесії бота
        await bot.session.close()
        logger.info("Сесію бота закрито.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Роботу бота примусово зупинено користувачем.")

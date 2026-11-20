import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo
import uvicorn

from app.api.app import app as fastapi_app
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
    """Хук запуску: налаштування команд та кнопки застосунку."""
    bot_info = await bot.get_me()
    logger.info("бот запущено: @%s [id: %s]", bot_info.username, bot_info.id)

    await bot.set_my_commands([
        BotCommand(command="topics", description="список навчальних тем"),
        BotCommand(command="top", description="топ найкращих учнів"),
        BotCommand(command="profile", description="профіль та успішність"),
        BotCommand(command="start", description="вибір класу та головне меню"),
    ])

    if settings.WEB_APP_URL:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="застосунок",
                    web_app=WebAppInfo(url=settings.WEB_APP_URL),
                )
            )
            logger.info("меню webapp: %s", settings.WEB_APP_URL)
        except Exception as e:
            logger.warning("не вдалося встановити кнопку меню webapp: %s", e)


async def on_shutdown(bot: Bot) -> None:
    """Хук зупинки: коректне закриття з'єднань з базою даних."""
    await async_engine.dispose()
    logger.info("пул з'єднань з базою даних закрито.")


async def main() -> None:
    """Головна точка входу для запуску Telegram-бота та API mathcore."""
    if not settings.BOT_TOKEN:
        logger.error("bot_token не встановлено у .env!")
        return

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_router(common_router)
    dp.include_router(tasks_router)

    server = None
    try:
        await init_db()
        await bot.delete_webhook(drop_pending_updates=True)

        config = uvicorn.Config(
            app=fastapi_app,
            host=settings.WEB_HOST,
            port=settings.WEB_PORT,
            log_level="info",
        )
        server = uvicorn.Server(config)
        logger.info("веб-сервер api: http://%s:%s", settings.WEB_HOST, settings.WEB_PORT)

        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            server.serve(),
        )
    finally:
        if server:
            server.should_exit = True
        await bot.session.close()
        logger.info("сесію бота закрито.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("роботу бота зупинено.")

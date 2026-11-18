import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import api_router
from app.config import settings
from app.db.base import init_db

logger = logging.getLogger("mathcore.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Життєвий цикл застосунку: ініціалізація бази даних при запуску."""
    logger.info("Ініціалізація бази даних для FastAPI...")
    await init_db()
    yield


def create_app() -> FastAPI:
    """Створює та налаштовує екземпляр застосунку FastAPI для mathcore."""
    app = FastAPI(
        title="mathcore API",
        description="REST API для Telegram Mini App та інтерактивного навчання mathcore",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Налаштування CORS для Telegram Mini App та локальної розробки
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Підключення маршрутів API
    app.include_router(api_router, prefix="/api/v1")

    @app.middleware("http")
    async def add_no_cache_headers(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/app"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    @app.get("/health", tags=["Система"], summary="Перевірка стану працездатності")
    async def health_check() -> dict:
        """Перевірка доступності сервісу."""
        return {
            "status": "ok",
            "service": "mathcore-api",
            "debug": settings.DEBUG,
        }

    # Монтування статичних файлів фронтенду TMA (якщо каталог існує)
    static_dir = Path(__file__).resolve().parent.parent / "web" / "static"
    if static_dir.exists():
        app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="static_tma")
        logger.info("Статичні файли TMA змонтовано на /app з каталогу: %s", static_dir)

        from fastapi.responses import RedirectResponse

        @app.get("/", include_in_schema=False)
        async def root_redirect():
            return RedirectResponse(url="/app/")

    return app


app = create_app()

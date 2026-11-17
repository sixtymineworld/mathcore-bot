from pydantic import AliasChoices, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфігурація застосунку mathcore на базі Pydantic Settings v2."""

    # Налаштування Telegram бота
    BOT_TOKEN: str = Field(default="", description="Telegram Bot API Token")

    # Налаштування MySQL
    DB_HOST: str = Field(default="localhost", description="Хост бази даних MySQL")
    DB_PORT: int = Field(default=3306, description="Порт бази даних MySQL")
    DB_USER: str = Field(default="root", description="Користувач MySQL")
    DB_PASSWORD: str = Field(default="", description="Пароль користувача MySQL")
    DB_NAME: str = Field(default="mathcore", description="Назва бази даних MySQL")
    DB_ECHO: bool = Field(default=False, description="Логування SQL-запитів")

    # Налаштування AI (Google Gemini)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash", description="Назва моделі Gemini")

    # Налаштування Web API / Telegram Mini App
    WEB_HOST: str = Field(default="0.0.0.0", description="Хост для запуску FastAPI")
    WEB_PORT: int = Field(default=8000, validation_alias=AliasChoices("PORT", "WEB_PORT"), description="Порт для запуску FastAPI")
    WEB_APP_URL: str = Field(default="", description="Публічний URL веб-додатку (TMA)")
    DEBUG: bool = Field(default=True, description="Режим налагодження (для тестування без Telegram)")

    # Прямий рядок підключення до БД (Render, PostgreSQL, SQLite тощо)
    CUSTOM_DATABASE_URL: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "DB_URL", "CUSTOM_DATABASE_URL"),
        description="Прямий DSN для БД",
    )

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Асинхронний DSN для SQLAlchemy (підтримує MySQL, PostgreSQL, SQLite)."""
        if self.CUSTOM_DATABASE_URL:
            url = self.CUSTOM_DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("mysql://") and "+asyncmy" not in url:
                url = url.replace("mysql://", "mysql+asyncmy://", 1)
            elif url.startswith("sqlite://") and "+aiosqlite" not in url:
                url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            return url

        return (
            f"mysql+asyncmy://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

from pydantic import Field, computed_field
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

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Асинхронний DSN для SQLAlchemy з драйвером asyncmy та кодуванням utf8mb4."""
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

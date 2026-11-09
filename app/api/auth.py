import hashlib
import hmac
import json
import logging
import urllib.parse
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from pydantic import BaseModel

from app.config import settings
from app.services.task_service import TaskService

logger = logging.getLogger("mathcore.auth")


class AuthenticatedUser(BaseModel):
    """Модель авторизованого користувача з Telegram Mini App."""

    tg_id: int
    first_name: str
    username: str | None = None


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """Перевіряє валідність рядка initData від Telegram WebApp за алгоритмом HMAC-SHA256."""
    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed_data:
            return None

        received_hash = parsed_data.pop("hash")
        # Сортування ключів за алфавітом
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items(), key=lambda item: item[0])
        )

        # Секретний ключ = HMAC-SHA256("WebAppData", bot_token)
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        # Розрахунок хешу від рядка даних
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if hmac.compare_digest(calculated_hash, received_hash):
            return parsed_data
        return None
    except Exception as e:
        logger.warning("Помилка парсингу Telegram initData: %s", e)
        return None


async def get_current_user(
    authorization: Annotated[str | None, Header(description="Заголовок 'tma <initData>'")] = None,
    init_data_query: Annotated[str | None, Query(alias="initData", description="initData як query param")] = None,
    dev_user_id: Annotated[int | None, Header(alias="X-Dev-User-Id", description="ID для розробки (тільки при DEBUG=True)")] = None,
) -> AuthenticatedUser:
    """FastAPI Dependency для перевірки авторизації користувача Telegram Mini App."""
    init_data = None
    if authorization:
        if authorization.lower().startswith("tma "):
            init_data = authorization[4:].strip()
        else:
            init_data = authorization.strip()
    elif init_data_query:
        init_data = init_data_query

    # Перевірка Telegram initData
    if init_data:
        validated_data = validate_telegram_init_data(init_data, settings.BOT_TOKEN)
        if validated_data and "user" in validated_data:
            try:
                user_dict = json.loads(validated_data["user"])
                tg_id = user_dict.get("id")
                first_name = user_dict.get("first_name", "учень")
                username = user_dict.get("username")

                if tg_id:
                    # Синхронізація або створення користувача в базі даних
                    await TaskService.upsert_user(
                        tg_id=tg_id,
                        first_name=first_name,
                        username=username,
                    )
                    return AuthenticatedUser(
                        tg_id=tg_id,
                        first_name=first_name,
                        username=username,
                    )
            except Exception as e:
                logger.error("Помилка розбору об'єкта user з initData: %s", e)

    # Режим розробки / локального тестування через Swagger /docs
    if settings.DEBUG:
        test_tg_id = dev_user_id or 99999999
        test_user = await TaskService.get_user_by_tg_id(test_tg_id)
        if not test_user:
            await TaskService.upsert_user(
                tg_id=test_tg_id,
                first_name="тестовий учень",
                username="test_user",
                grade=7,
            )
        return AuthenticatedUser(
            tg_id=test_tg_id,
            first_name=test_user.first_name if test_user else "тестовий учень",
            username=test_user.username if test_user else "test_user",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недійсні або відсутні облікові дані Telegram Mini App",
    )

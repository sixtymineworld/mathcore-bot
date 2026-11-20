import hashlib
import hmac
import json
import logging
import urllib.parse
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.config import settings
from app.services.task_service import TaskService

logger = logging.getLogger("mathcore.auth")


class AuthenticatedUser(BaseModel):
    """Модель авторизованого користувача з Telegram Mini App."""

    tg_id: int
    first_name: str
    username: str | None = None


def create_session_token(tg_id: int) -> str:
    """Генерує криптографічно підписаний токен сесії на базі BOT_TOKEN."""
    secret = (settings.BOT_TOKEN or "mathcore-session-secret-key").encode("utf-8")
    sig = hmac.new(secret, str(tg_id).encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{tg_id}:{sig}"


def set_session_cookie(response: Response, tg_id: int) -> str:
    """Генерує токен сесії, записує cookie на 1 рік та встановлює заголовок X-Session-Token."""
    token = create_session_token(tg_id)
    try:
        response.set_cookie(
            key="mathcore_session",
            value=token,
            max_age=31536000,
            path="/",
            samesite="lax",
            secure=False,
            httponly=False,
        )
    except Exception:
        pass
    response.headers["X-Session-Token"] = token
    return token


def verify_session_token(token: str | None) -> int | None:
    """Перевіряє підпис токена сесії та повертає tg_id користувача."""
    if not token:
        return None
    token = token.strip().strip('"').strip("'")
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if ":" not in token:
        return None
    try:
        tg_id_str, sig = token.split(":", 1)
        tg_id = int(tg_id_str)
        secret = (settings.BOT_TOKEN or "mathcore-session-secret-key").encode("utf-8")
        expected_sig = hmac.new(secret, str(tg_id).encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        if hmac.compare_digest(sig, expected_sig):
            return tg_id
    except Exception as e:
        logger.warning("Помилка перевірки токена сесії: %s", e)
    return None


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
    response: Response,
    authorization: Annotated[str | None, Header(description="Заголовок 'tma <initData>' або 'Bearer <token>'")] = None,
    init_data_query: Annotated[str | None, Query(alias="initData", description="initData як query param")] = None,
    token_query: Annotated[str | None, Query(alias="token", description="Токен сесії у query param")] = None,
    session_token_query: Annotated[str | None, Query(alias="session_token", description="Токен сесії у query param")] = None,
    tg_id_query: Annotated[int | None, Query(alias="tg_id", description="Telegram ID у query param")] = None,
    session_token_header: Annotated[str | None, Header(alias="X-Session-Token", description="Токен сесії")] = None,
    session_cookie: Annotated[str | None, Cookie(alias="mathcore_session", description="Кукі сесії")] = None,
    init_data_cookie: Annotated[str | None, Cookie(alias="mathcore_init_data", description="Кукі initData")] = None,
    dev_user_id: Annotated[int | None, Header(alias="X-Dev-User-Id", description="ID для розробки (тільки при DEBUG=True)")] = None,
) -> AuthenticatedUser:
    """FastAPI Dependency для перевірки авторизації користувача через Telegram WebApp, токен сесії або кукі."""
    # 1. Пріоритетна перевірка рядка Telegram initData (активна сесія з клієнта Telegram)
    init_data = None
    if authorization:
        if authorization.lower().startswith("tma "):
            init_data = authorization[4:].strip()
        elif "hash=" in authorization:
            init_data = authorization.strip()
    elif init_data_query:
        init_data = init_data_query
    elif init_data_cookie:
        init_data = urllib.parse.unquote(init_data_cookie).strip()

    if init_data:
        validated_data = validate_telegram_init_data(init_data, settings.BOT_TOKEN)
        if validated_data and "user" in validated_data:
            try:
                user_dict = json.loads(validated_data["user"])
                tg_id = user_dict.get("id")
                first_name = user_dict.get("first_name", "учень")
                username = user_dict.get("username")

                if tg_id:
                    user = await TaskService.upsert_user(
                        tg_id=tg_id,
                        first_name=first_name,
                        username=username,
                    )
                    set_session_cookie(response, tg_id)
                    return AuthenticatedUser(
                        tg_id=user.tg_id,
                        first_name=user.first_name,
                        username=user.username,
                    )
            except Exception as e:
                logger.error("Помилка розбору об'єкта user з initData: %s", e)

    # 2. Перевірка підписаного токена сесії (Query param, Header, Cookie або Bearer Auth)
    bearer_token = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer_token = authorization[7:].strip()

    token_candidate = (
        token_query
        or session_token_query
        or session_token_header
        or bearer_token
        or session_cookie
    )

    if token_candidate:
        token_clean = urllib.parse.unquote(token_candidate).strip()
        tg_id = verify_session_token(token_clean)
        if tg_id:
            user = await TaskService.get_user_by_tg_id(tg_id)
            if user:
                set_session_cookie(response, user.tg_id)
                return AuthenticatedUser(
                    tg_id=user.tg_id,
                    first_name=user.first_name,
                    username=user.username,
                )
            # Якщо користувач валідно підписаний ключем бота, але ще відсутній у базі
            new_user = await TaskService.upsert_user(
                tg_id=tg_id,
                first_name="учень",
                grade=7,
            )
            set_session_cookie(response, new_user.tg_id)
            return AuthenticatedUser(
                tg_id=new_user.tg_id,
                first_name=new_user.first_name,
                username=new_user.username,
            )

    # 3. Режим розробки / налагодження: підтримка прямого tg_id або fallback
    if settings.DEBUG:
        test_tg_id = tg_id_query or dev_user_id or 1351269080
        test_user = await TaskService.get_user_by_tg_id(test_tg_id)
        if not test_user:
            test_user = await TaskService.upsert_user(
                tg_id=test_tg_id,
                first_name="дімаssik" if test_tg_id == 1351269080 else "тестовий учень",
                username="test_user",
                grade=11 if test_tg_id == 1351269080 else 7,
            )
        set_session_cookie(response, test_tg_id)
        return AuthenticatedUser(
            tg_id=test_tg_id,
            first_name=test_user.first_name if test_user else "учень",
            username=test_user.username if test_user else "test_user",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недійсні або відсутні облікові дані Telegram Mini App",
    )

from typing import Annotated

from fastapi import APIRouter, Cookie, Header, HTTPException, Query, status

from app.api.auth import verify_session_token
from app.api.schemas import TopicResponse
from app.config import settings
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/grades", response_model=list[int], summary="Список доступних класів")
async def get_grades() -> list[int]:
    """Повертає список доступних класів шкільної програми (1–11)."""
    return list(range(1, 12))


@router.get("/grade/{grade}", response_model=list[TopicResponse], summary="Список тем для вказаного класу")
async def get_topics_by_grade(
    grade: int,
    subject: str | None = None,
    tg_id: Annotated[int | None, Query(description="Telegram ID учня")] = None,
    session_token: Annotated[str | None, Query(description="Токен сесії")] = None,
    token: Annotated[str | None, Query(description="Токен сесії")] = None,
    authorization: Annotated[str | None, Header(description="Заголовок авторизації")] = None,
    session_cookie: Annotated[str | None, Cookie(alias="mathcore_session")] = None,
) -> list[TopicResponse]:
    """Повертає теми з математики для вказаного класу з персональним прогресом розв'язання учнем."""
    if not 1 <= grade <= 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Клас повинен бути в діапазоні від 1 до 11",
        )

    resolved_tg_id = tg_id
    if not resolved_tg_id:
        tok = session_token or token or session_cookie
        if tok:
            resolved_tg_id = verify_session_token(tok)
        elif authorization and authorization.lower().startswith("bearer "):
            resolved_tg_id = verify_session_token(authorization[7:].strip())

    if not resolved_tg_id and settings.DEBUG:
        resolved_tg_id = 1351269080

    topics_data = await TaskService.get_topics_with_progress(grade, subject=subject, tg_id=resolved_tg_id)
    return [TopicResponse(**t) for t in topics_data]


@router.get("/{topic_id}", response_model=TopicResponse, summary="Отримати деталі теми")
async def get_topic_by_id(
    topic_id: int,
) -> TopicResponse:
    """Повертає інформацію про конкретну навчальну тему за ID."""
    topic = await TaskService.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тему не знайдено",
        )
    return TopicResponse.model_validate(topic)

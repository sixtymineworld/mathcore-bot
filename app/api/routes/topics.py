from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import AuthenticatedUser, get_current_user
from app.api.schemas import TopicResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/grades", response_model=list[int], summary="Список доступних класів")
async def get_grades() -> list[int]:
    """Повертає список доступних класів шкільної програми (1–11)."""
    return list(range(1, 12))


@router.get("/grade/{grade}", response_model=list[TopicResponse], summary="Список тем для вказаного класу")
async def get_topics_by_grade(
    grade: int,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> list[TopicResponse]:
    """Повертає теми з математики для вказаного класу (1–11)."""
    if grade < 1 or grade > 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Клас повинен бути в діапазоні від 1 до 11",
        )

    topics = await TaskService.get_topics_by_grade(grade)
    return [
        TopicResponse(
            id=topic.id,
            title=topic.title,
            description=topic.description,
            grade=topic.grade,
            order_num=topic.order_num,
        )
        for topic in topics
    ]


@router.get("/{topic_id}", response_model=TopicResponse, summary="Отримати деталі теми")
async def get_topic_by_id(
    topic_id: int,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> TopicResponse:
    """Повертає інформацію про конкретну навчальну тему за ID."""
    topic = await TaskService.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тему не знайдено",
        )

    return TopicResponse(
        id=topic.id,
        title=topic.title,
        description=topic.description,
        grade=topic.grade,
        order_num=topic.order_num,
    )

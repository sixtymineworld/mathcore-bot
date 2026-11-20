from fastapi import APIRouter, Depends, Query

from app.api.auth import AuthenticatedUser, get_current_user
from app.api.schemas import LeaderboardResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=LeaderboardResponse, summary="Отримати топ найкращих учнів класу")
async def get_leaderboard(
    grade: int | None = Query(default=None, ge=1, le=11, description="Клас для перегляду рейтингу (1–11)"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> LeaderboardResponse:
    """Повертає рейтинг учнів за набраними балами серед обраного класу та позицію поточного користувача."""
    target_grade = grade
    if target_grade is None:
        db_user = await TaskService.get_user_by_tg_id(user.tg_id)
        target_grade = db_user.grade if db_user and db_user.grade else 7

    data = await TaskService.get_leaderboard(current_tg_id=user.tg_id, grade=target_grade, limit=50)
    return LeaderboardResponse(
        grade=target_grade,
        top_users=data["top_users"],
        current_user_rank=data["current_user_rank"],
        current_user_points=data["current_user_points"],
        current_user_solved=data["current_user_solved"],
        total_participants=data["total_participants"],
    )

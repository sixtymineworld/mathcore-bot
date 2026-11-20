from fastapi import APIRouter, Depends

from app.api.auth import AuthenticatedUser, get_current_user
from app.api.schemas import LeaderboardResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=LeaderboardResponse, summary="Отримати топ найкращих учнів")
async def get_leaderboard(
    user: AuthenticatedUser = Depends(get_current_user),
) -> LeaderboardResponse:
    """Повертає рейтинг учнів за набраними балами та позицію поточного користувача."""
    data = await TaskService.get_leaderboard(current_tg_id=user.tg_id, limit=50)
    return LeaderboardResponse(
        top_users=data["top_users"],
        current_user_rank=data["current_user_rank"],
        current_user_points=data["current_user_points"],
        current_user_solved=data["current_user_solved"],
        total_participants=data["total_participants"],
    )

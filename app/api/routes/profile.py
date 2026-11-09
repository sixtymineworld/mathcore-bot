from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import AuthenticatedUser, get_current_user
from app.api.schemas import UpdateGradeRequest, UserProfileResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=UserProfileResponse, summary="Отримати профіль поточного користувача")
async def get_my_profile(
    user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfileResponse:
    """Повертає повну інформацію про успішність, ранг, активність та поточний клас учня."""
    profile_data = await TaskService.get_user_profile(user.tg_id)
    return UserProfileResponse(
        tg_id=user.tg_id,
        first_name=profile_data.get("first_name") or user.first_name,
        grade=profile_data.get("grade"),
        total_attempts=profile_data.get("total_attempts", 0),
        solved_unique=profile_data.get("solved_unique", 0),
        accuracy=profile_data.get("accuracy", 0),
        today_attempts=profile_data.get("today_attempts", 0),
        today_solved=profile_data.get("today_solved", 0),
        streak=profile_data.get("streak", 0),
        days_registered=profile_data.get("days_registered", 1),
        rank=profile_data.get("rank", "початківець"),
        progress_bar=profile_data.get("progress_bar", "[□□□□□□□□]"),
    )


@router.patch("/grade", response_model=UserProfileResponse, summary="Оновити клас навчання користувача")
async def update_my_grade(
    payload: UpdateGradeRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfileResponse:
    """Змінює клас навчання користувача (1–11) для налаштування програми."""
    await TaskService.upsert_user(
        tg_id=user.tg_id,
        first_name=user.first_name,
        username=user.username,
        grade=payload.grade,
    )
    return await get_my_profile(user=user)

from fastapi import APIRouter, Depends, Response

from app.api.auth import AuthenticatedUser, get_current_user, set_session_cookie
from app.api.schemas import UpdateGradeRequest, UserProfileResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=UserProfileResponse, summary="Отримати профіль поточного користувача")
async def get_my_profile(
    response: Response,
    user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfileResponse:
    """Повертає інформацію про успішність та активність учня і продовжує сесію в кукі."""
    set_session_cookie(response, user.tg_id)
    profile = await TaskService.get_user_profile(user.tg_id)
    return UserProfileResponse(
        tg_id=user.tg_id,
        first_name=profile.get("first_name") or user.first_name,
        grade=profile.get("grade"),
        total_attempts=profile.get("total_attempts", 0),
        solved_unique=profile.get("solved_unique", 0),
        accuracy=profile.get("accuracy", 0),
        today_attempts=profile.get("today_attempts", 0),
        today_solved=profile.get("today_solved", 0),
        streak=profile.get("streak", 0),
        days_registered=profile.get("days_registered", 1),
        rank=profile.get("rank", "початківець"),
        progress_bar=profile.get("progress_bar", "[□□□□□□□□]"),
    )


@router.patch("/grade", response_model=UserProfileResponse, summary="Оновити клас навчання користувача")
async def update_my_grade(
    payload: UpdateGradeRequest,
    response: Response,
    user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfileResponse:
    """Змінює клас навчання користувача (1–11) для налаштування програми."""
    await TaskService.upsert_user(
        tg_id=user.tg_id,
        first_name=user.first_name,
        username=user.username,
        grade=payload.grade,
    )
    return await get_my_profile(response=response, user=user)


@router.post("/session", summary="Синхронізація сесії та збереження кукі")
async def sync_session(
    response: Response,
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Створює довговічну сесію, встановлює кукі та повертає статус користувача."""
    token = set_session_cookie(response, user.tg_id)
    profile = await TaskService.get_user_profile(user.tg_id)
    return {
        "ok": True,
        "tg_id": user.tg_id,
        "first_name": user.first_name,
        "grade": profile.get("grade"),
        "session_token": token,
    }

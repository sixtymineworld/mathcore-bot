from fastapi import APIRouter

from app.api.routes.leaderboard import router as leaderboard_router
from app.api.routes.profile import router as profile_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.topics import router as topics_router

api_router = APIRouter()
api_router.include_router(profile_router, prefix="/profile", tags=["Профіль"])
api_router.include_router(topics_router, prefix="/topics", tags=["Теми"])
api_router.include_router(leaderboard_router, prefix="/leaderboard", tags=["Лідерборд"])
api_router.include_router(tasks_router, tags=["Завдання"])

__all__ = ["api_router"]

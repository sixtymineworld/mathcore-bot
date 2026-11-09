import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import AuthenticatedUser, get_current_user
from app.api.schemas import (
    CheckAnswerRequest,
    CheckAnswerResponse,
    GenerateTaskResponse,
    HintResponse,
    TaskResponse,
)
from app.services.ai_checker import get_ai_checker
from app.services.task_service import TaskService

logger = logging.getLogger("mathcore.api.tasks")
router = APIRouter()


@router.get(
    "/topics/{topic_id}/tasks",
    response_model=list[TaskResponse],
    summary="Отримати список завдань у темі",
)
async def get_tasks_by_topic(
    topic_id: int,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> list[TaskResponse]:
    """Повертає список математичних завдань для вказаної теми."""
    topic = await TaskService.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тему не знайдено",
        )

    tasks = await TaskService.get_tasks_by_topic(topic_id)
    return [
        TaskResponse(
            id=task.id,
            topic_id=task.topic_id,
            title=task.title,
            question_text=task.question_text,
            difficulty=task.difficulty,
        )
        for task in tasks
    ]


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Отримати завдання за ID",
)
async def get_task_by_id(
    task_id: int,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> TaskResponse:
    """Повертає математичне завдання за його ідентифікатором."""
    task = await TaskService.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Завдання не знайдено",
        )

    return TaskResponse(
        id=task.id,
        topic_id=task.topic_id,
        title=task.title,
        question_text=task.question_text,
        difficulty=task.difficulty,
    )


@router.get(
    "/tasks/{task_id}/hint",
    response_model=HintResponse,
    summary="Отримати підказку до завдання",
)
async def get_task_hint(
    task_id: int,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> HintResponse:
    """Повертає загальну формулу або методичну підказку без спойлерів обчислень."""
    task = await TaskService.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Завдання не знайдено",
        )

    hint = task.solution_hint or "спробуй пригадати базове правило або формулу для цієї теми."
    return HintResponse(task_id=task.id, hint=hint)


@router.post(
    "/tasks/{task_id}/check",
    response_model=CheckAnswerResponse,
    summary="Перевірити розв'язок учня за допомогою AI",
)
async def check_task_solution(
    task_id: int,
    payload: CheckAnswerRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> CheckAnswerResponse:
    """Перевіряє відповідь учня за допомогою Gemini AI та зберігає спробу в аналітику."""
    task = await TaskService.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Завдання не знайдено",
        )

    topic = await TaskService.get_topic_by_id(task.topic_id)
    grade = topic.grade if topic else 7

    ai_checker = get_ai_checker()
    result = await ai_checker.check_solution(
        task_question=task.question_text,
        user_answer=payload.answer,
        correct_answer=task.correct_answer,
        grade=grade,
    )

    # Зберігаємо результат спроби в базу даних для аналітики успішності
    await TaskService.record_task_attempt(
        tg_id=user.tg_id,
        task_id=task.id,
        is_correct=result.is_correct,
        user_answer=payload.answer,
    )

    return CheckAnswerResponse(
        is_correct=result.is_correct,
        explanation=result.feedback,
        user_answer=payload.answer,
    )


@router.post(
    "/topics/{topic_id}/generate",
    response_model=GenerateTaskResponse,
    summary="Згенерувати нову унікальну задачу за обраною темою",
)
async def generate_new_task(
    topic_id: int,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> GenerateTaskResponse:
    """Генерує за допомогою AI нове завдання суворо за темою та зберігає його в базу."""
    topic = await TaskService.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тему не знайдено",
        )

    ai_checker = get_ai_checker()
    generated = await ai_checker.generate_task(
        grade=topic.grade,
        topic=topic.title,
    )

    created_task = await TaskService.create_generated_task(
        topic_id=topic.id,
        title=generated.title,
        question_text=generated.question,
        solution_hint=generated.hint,
        correct_answer=generated.correct_answer,
        difficulty=generated.difficulty,
    )

    return GenerateTaskResponse(
        task=TaskResponse(
            id=created_task.id,
            topic_id=created_task.topic_id,
            title=created_task.title,
            question_text=created_task.question_text,
            difficulty=created_task.difficulty,
        ),
        message=f"завдання згенеровано за темою '{topic.title}'",
    )

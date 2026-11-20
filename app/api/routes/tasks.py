import json
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
    user: AuthenticatedUser = Depends(get_current_user),
) -> list[TaskResponse]:
    """Повертає список математичних завдань для вказаної теми з персональним статусом розв'язання."""
    topic = await TaskService.get_topic_by_id(topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тему не знайдено")
    tasks = await TaskService.get_topic_tasks_for_user(topic_id, tg_id=user.tg_id)
    return [TaskResponse(**t) for t in tasks]


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено")
    return TaskResponse.model_validate(task)


@router.get(
    "/tasks/{task_id}/hint",
    response_model=HintResponse,
    summary="Отримати підказку до завдання",
)
async def get_task_hint(
    task_id: int,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> HintResponse:
    """Повертає формулу або підказку без спойлерів обчислень."""
    task = await TaskService.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено")
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
    """Перевіряє відповідь учня за допомогою AI або миттєво для квізів та зберігає спробу в аналітику."""
    task = await TaskService.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено")

    topic = await TaskService.get_topic_by_id(task.topic_id)
    grade = topic.grade if topic else 7

    # Миттєва перевірка для квізів (0 мс затримки, без очікування виклику AI)
    if task.is_quiz and task.correct_answer:
        user_norm = payload.answer.strip().lower()
        corr_norm = task.correct_answer.strip().lower()

        is_correct = (user_norm == corr_norm)
        if not is_correct and task.options:
            letters = ["а", "б", "в", "г"]
            for idx, opt in enumerate(task.options):
                if idx < len(letters):
                    opt_letter = letters[idx]
                    opt_norm = opt.strip().lower()
                    if corr_norm in (opt_norm, opt_letter) and user_norm in (opt_norm, opt_letter):
                        is_correct = True
                        break

        feedback = (
            "відповідь правильна! молодець, обрано точний варіант."
            if is_correct
            else f"на жаль, вибір неправильний. правильна відповідь: {task.correct_answer}."
        )

        await TaskService.record_task_attempt(
            tg_id=user.tg_id,
            task_id=task.id,
            is_correct=is_correct,
            user_answer=payload.answer,
        )

        return CheckAnswerResponse(
            is_correct=is_correct,
            explanation=feedback,
            user_answer=payload.answer,
            detailed_solution=task.detailed_solution or task.solution_hint,
            correct_answer=task.correct_answer,
        )

    # Для складніших відкритих завдань використовуємо AI перевірку
    ai_checker = get_ai_checker()
    result = await ai_checker.check_solution(
        task_question=task.question_text,
        user_answer=payload.answer,
        correct_answer=task.correct_answer,
        grade=grade,
    )

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
        detailed_solution=result.detailed_solution or task.detailed_solution,
        correct_answer=task.correct_answer,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тему не знайдено")

    ai_checker = get_ai_checker()
    generated = await ai_checker.generate_task(grade=topic.grade, topic=topic.title)

    options_json = (
        json.dumps(generated.options, ensure_ascii=False)
        if (generated.is_quiz and generated.options)
        else None
    )

    created_task = await TaskService.create_generated_task(
        topic_id=topic.id,
        title=generated.title,
        question_text=generated.question,
        solution_hint=generated.hint,
        correct_answer=generated.correct_answer,
        difficulty=generated.difficulty,
        diagram_svg=generated.diagram_svg,
        is_nmt=generated.is_nmt,
        detailed_solution=generated.detailed_solution,
        is_quiz=generated.is_quiz,
        options_json=options_json,
    )

    return GenerateTaskResponse(
        task=TaskResponse.model_validate(created_task),
        message=f"завдання згенеровано за темою '{topic.title}'",
    )

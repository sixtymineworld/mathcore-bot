from datetime import datetime
import logging
from sqlalchemy import func, select

from app.db.base import get_session
from app.db.models import Task, Topic, User, UserTaskAttempt

logger = logging.getLogger(__name__)


class TaskService:
    """Сервіс для роботи з навчальними темами, завданнями та профілями користувачів."""

    @staticmethod
    async def get_topics_by_grade(grade: int, subject: str | None = None) -> list[Topic]:
        """Повертає список тем для вказаного класу (з можливим фільтром за предметом), відсортованих за порядком."""
        async with get_session() as session:
            stmt = select(Topic).where(Topic.grade == grade)
            if subject:
                stmt = stmt.where(Topic.subject == subject.strip().lower())
            stmt = stmt.order_by(Topic.order_num, Topic.id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_topic_by_id(topic_id: int) -> Topic | None:
        """Отримує тему за її ID."""
        async with get_session() as session:
            stmt = select(Topic).where(Topic.id == topic_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_tasks_by_topic(topic_id: int) -> list[Task]:
        """Повертає список усіх завдань для певної теми."""
        async with get_session() as session:
            stmt = (
                select(Task)
                .where(Task.topic_id == topic_id)
                .order_by(Task.difficulty, Task.id)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def get_task_by_id(task_id: int) -> Task | None:
        """Отримує завдання за його ID."""
        async with get_session() as session:
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def create_generated_task(
        topic_id: int,
        title: str,
        question_text: str,
        solution_hint: str,
        correct_answer: str,
        difficulty: int = 1,
        diagram_svg: str | None = None,
        is_nmt: bool = False,
        detailed_solution: str | None = None,
    ) -> Task:
        """Створює та зберігає згенероване завдання в базі даних."""
        async with get_session() as session:
            task = Task(
                topic_id=topic_id,
                title=title,
                question_text=question_text,
                solution_hint=solution_hint,
                correct_answer=correct_answer,
                difficulty=difficulty,
                diagram_svg=diagram_svg,
                is_nmt=is_nmt,
                detailed_solution=detailed_solution,
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    @staticmethod
    async def get_next_task(topic_id: int, current_task_id: int) -> Task | None:
        """Знаходить наступне завдання в темі після поточного."""
        async with get_session() as session:
            # Шукаємо перше завдання цієї ж теми з більшим ID
            stmt = (
                select(Task)
                .where(Task.topic_id == topic_id, Task.id > current_task_id)
                .order_by(Task.id)
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_tg_id(tg_id: int) -> User | None:
        """Отримує користувача за його Telegram ID."""
        async with get_session() as session:
            stmt = select(User).where(User.tg_id == tg_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def upsert_user(
        tg_id: int,
        first_name: str,
        username: str | None = None,
        grade: int | None = None,
    ) -> User:
        """Створює нового користувача або оновлює дані наявного."""
        async with get_session() as session:
            stmt = select(User).where(User.tg_id == tg_id)
            result = await session.execute(stmt)
            db_user = result.scalar_one_or_none()

            if db_user is None:
                db_user = User(
                    tg_id=tg_id,
                    username=username,
                    first_name=first_name,
                    grade=grade,
                )
                session.add(db_user)
            else:
                db_user.first_name = first_name
                db_user.username = username
                if grade is not None:
                    db_user.grade = grade

            await session.commit()
            await session.refresh(db_user)
            return db_user

    @staticmethod
    async def record_task_attempt(
        tg_id: int,
        task_id: int,
        is_correct: bool,
        user_answer: str,
    ) -> UserTaskAttempt | None:
        """Зберігає результат спроби розв'язання завдання учнем."""
        async with get_session() as session:
            stmt = select(User).where(User.tg_id == tg_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return None

            attempt = UserTaskAttempt(
                user_id=user.id,
                task_id=task_id,
                is_correct=is_correct,
                user_answer=user_answer[:255],
            )
            session.add(attempt)
            await session.commit()
            return attempt

    @staticmethod
    def _make_progress_bar(percent: int, length: int = 8) -> str:
        """Створює текстовий мінімалістичний прогрес-бар."""
        filled = round(length * max(0, min(percent, 100)) / 100)
        return f"[{'■' * filled}{'□' * (length - filled)}]"

    @staticmethod
    def _calculate_rank(solved_count: int) -> str:
        """Визначає рівень майстерності учня за кількістю розв'язаних завдань."""
        if solved_count < 3:
            return "початківець"
        elif solved_count < 8:
            return "дослідник"
        elif solved_count < 15:
            return "практик"
        elif solved_count < 25:
            return "знавець"
        return "майстер математики"

    @staticmethod
    async def get_user_profile(tg_id: int) -> dict:
        """Повертає детальний профіль користувача: успішність, активність, серії та ранг."""
        async with get_session() as session:
            stmt = select(User).where(User.tg_id == tg_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return {
                    "grade": None,
                    "first_name": "",
                    "total_attempts": 0,
                    "solved_unique": 0,
                    "accuracy": 0,
                    "today_attempts": 0,
                    "today_solved": 0,
                    "streak": 0,
                    "days_registered": 1,
                    "rank": "початківець",
                    "progress_bar": "[□□□□□□□□]",
                }

            now = datetime.now()
            start_of_today = datetime(now.year, now.month, now.day, 0, 0, 0)
            days_registered = max(1, (now.date() - user.created_at.date()).days + 1)

            # Загальна кількість спроб
            attempts_stmt = select(func.count(UserTaskAttempt.id)).where(
                UserTaskAttempt.user_id == user.id
            )
            total_attempts = (await session.execute(attempts_stmt)).scalar() or 0

            # Кількість розв'язаних унікальних завдань
            solved_stmt = select(
                func.count(func.distinct(UserTaskAttempt.task_id))
            ).where(
                UserTaskAttempt.user_id == user.id,
                UserTaskAttempt.is_correct.is_(True),
            )
            solved_unique = (await session.execute(solved_stmt)).scalar() or 0

            # Кількість правильних спроб для розрахунку точності
            correct_attempts_stmt = select(func.count(UserTaskAttempt.id)).where(
                UserTaskAttempt.user_id == user.id,
                UserTaskAttempt.is_correct.is_(True),
            )
            correct_attempts = (
                await session.execute(correct_attempts_stmt)
            ).scalar() or 0

            accuracy = (
                round((correct_attempts / total_attempts) * 100)
                if total_attempts > 0
                else 0
            )

            # Активність за сьогодні
            today_attempts_stmt = select(func.count(UserTaskAttempt.id)).where(
                UserTaskAttempt.user_id == user.id,
                UserTaskAttempt.created_at >= start_of_today,
            )
            today_attempts = (await session.execute(today_attempts_stmt)).scalar() or 0

            today_solved_stmt = select(func.count(func.distinct(UserTaskAttempt.task_id))).where(
                UserTaskAttempt.user_id == user.id,
                UserTaskAttempt.is_correct.is_(True),
                UserTaskAttempt.created_at >= start_of_today,
            )
            today_solved = (await session.execute(today_solved_stmt)).scalar() or 0

            # Поточна серія правильних відповідей підряд
            recent_stmt = (
                select(UserTaskAttempt.is_correct)
                .where(UserTaskAttempt.user_id == user.id)
                .order_by(UserTaskAttempt.created_at.desc(), UserTaskAttempt.id.desc())
                .limit(20)
            )
            recent_results = (await session.execute(recent_stmt)).scalars().all()
            streak = 0
            for is_corr in recent_results:
                if is_corr:
                    streak += 1
                else:
                    break

            rank = TaskService._calculate_rank(solved_unique)
            progress_bar = TaskService._make_progress_bar(accuracy)

            return {
                "grade": user.grade,
                "first_name": user.first_name,
                "total_attempts": total_attempts,
                "solved_unique": solved_unique,
                "accuracy": accuracy,
                "today_attempts": today_attempts,
                "today_solved": today_solved,
                "streak": streak,
                "days_registered": days_registered,
                "rank": rank,
                "progress_bar": progress_bar,
            }

    # Для зворотної сумісності
    get_user_stats = get_user_profile

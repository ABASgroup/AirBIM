from uuid import UUID
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base import BaseRepository
from sqlalchemy.orm import selectinload
from models.task import Task, TaskStatus, TaskStep


class TaskRepository(BaseRepository[Task]):
    """Repository class for CRUD operations with Task model."""
    _model = Task

    @classmethod
    async def get_by_workspace_id(
        cls,
        workspace_id: UUID,
        session: AsyncSession,
        statuses: list[TaskStatus] | None,
    ) -> Sequence[Task]:
        stmt = select(cls._model).where(
            cls._model.workspace_id == workspace_id)
        if statuses:
            stmt = stmt.where(cls._model.status.in_(statuses))
        result = await session.execute(stmt)
        return result.scalars().all()


class TaskStepRepository(BaseRepository[TaskStep]):
    """Repository class for CRUD operations with TaskStep model."""
    _model = TaskStep

    @classmethod
    async def get_by_task_id(
        cls,
        task_id: UUID,
        session: AsyncSession,
    ) -> Sequence[TaskStep]:
        """Get all task steps belonging to a task."""
        stmt = select(cls._model).where(
            cls._model.task_id == task_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_by_step_task_id(
        cls,
        step_task_id: str,
        session: AsyncSession,
    ) -> TaskStep | None:
        """Get task with the associated step task ID (for example, celery task ID)."""
        stmt = select(cls._model).where(
            cls._model.step_task_id == step_task_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_finished_steps_by_task_id(
        cls,
        task_id: UUID,
        session: AsyncSession,
    ) -> Sequence[TaskStep]:
        """Get all finished task steps belonging to a task."""
        stmt = select(cls._model).where(
            cls._model.task_id == task_id,
            cls._model.finished_at.isnot(None)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

from uuid import UUID
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base import BaseRepository
from sqlalchemy.orm import selectinload
from models.task import Task, TaskStatus


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

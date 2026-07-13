import uuid
from .base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.project import Project


class ProjectRepository(BaseRepository[Project]):
    """Repository class for CRUD operations with Project model."""
    _model = Project

    @classmethod
    async def get_by_workspace_id(
        cls,
        workspace_id: uuid.UUID,
        session: AsyncSession
    ):
        """Get projects related to some workspace using its ID"""
        result = await session.execute(
            select(cls._model)
            .options(selectinload(cls._model.bim))
            .where(cls._model.workspace_id == workspace_id)
        )
        return result.scalars().all()

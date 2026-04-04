from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base import BaseRepository
from sqlalchemy.orm import selectinload
from models.stage import Stage


class StageRepository(BaseRepository[Stage]):
    """Repository class for CRUD operations with Stage model."""
    _model = Stage

    @classmethod
    async def get_by_project_id(
        cls,
        project_id: int,
        session: AsyncSession
    ):
        """Get stages related to some project using its ID."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.project_id == project_id)
        )
        return result.scalars().all()

    @classmethod
    async def get_by_id_with_project(
        cls,
        stage_id: int,
        session: AsyncSession
    ):
        """
        Modification that loads stage's project.
        
        Use to avoid N+1 problem when you require project with a stage.
        """
        result = await session.execute(
            select(cls._model)
            .options(selectinload(cls._model.project))
            .where(cls._model.id == stage_id)
        )
        return result.scalar_one_or_none()
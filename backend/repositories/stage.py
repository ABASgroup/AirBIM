import uuid
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
        project_id: uuid.UUID,
        session: AsyncSession
    ):
        """Get stages related to some project using its ID."""
        result = await session.execute(
            select(cls._model)
            .options(
                selectinload(cls._model.point_cloud),
                selectinload(cls._model.project)
            )
            .where(cls._model.project_id == project_id)
        )
        return result.scalars().all()

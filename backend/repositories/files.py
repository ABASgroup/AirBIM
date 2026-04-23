import uuid
from datetime import datetime, timedelta, time
from typing import TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.file import File, Bim, PointCloud, FileStatus
from .base import BaseRepository


class FileRepository(BaseRepository[File]):
    """Repository class for CRUD operations with File model."""
    _model = File

    @classmethod
    async def get_by_key(
        cls,
        key: str,
        session: AsyncSession
    ) -> File | None:
        """Get file by the key."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.key == key)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def update_status(
        cls,
        file: File,
        status: FileStatus,
        session: AsyncSession
    ):
        """Set new status for the file."""
        file.status = status

        await session.flush()
        await session.refresh(file)
        return file

    @classmethod
    async def get_file_by_metadata(
        cls,
        filename: str,
        content_type: str,
        size: int,
        session: AsyncSession
    ):
        """Get a very specific file by its metadata."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.filename == filename)
            .where(cls._model.size == size)
            .where(cls._model.content_type == content_type)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_status(
        cls,
        status: FileStatus,
        session: AsyncSession
    ):
        """Get all files with the specified status."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.status == status)
        )
        return result.scalars().all()


class BimRepository(BaseRepository[Bim]):
    """Repository class for CRUD operations with Bim model."""
    _model = Bim

    @classmethod
    async def get_by_project_id(
        cls,
        project_id: uuid.UUID,
        session: AsyncSession
    ):
        """Get BIM by project ID."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.project_id == project_id)
        )
        return result.scalar_one_or_none()


class PointCloudRepository(BaseRepository[PointCloud]):
    """Repository class for CRUD operations with PointCloud model."""
    _model = PointCloud

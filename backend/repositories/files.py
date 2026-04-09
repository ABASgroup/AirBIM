from typing import TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from models.files import BimFile, PointCloudFile, FileStatus, File
from sqlalchemy import select
from .base import BaseRepository


# type parameter for File children
ModelT = TypeVar("ModelT", bound=File)


class BaseFileRepository(BaseRepository[ModelT]):
    """
    Base repository for file models.

    This class is not meant to be used directly. It provides common methods for file repositories.
    """

    @classmethod
    async def update_status(
        cls,
        file: ModelT,
        status: FileStatus,
        session: AsyncSession
    ):
        """Set new status for the file."""
        file.status = status

        await session.flush()
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


class BimFileRepository(BaseFileRepository[BimFile]):
    """Repository class for CRUD operations with BimFile model."""
    _model = BimFile


class PointCloudFileRepository(BaseFileRepository[PointCloudFile]):
    """Repository class for CRUD operations with PointCloudFile model."""
    _model = PointCloudFile

from .base import BaseCRUD
from sqlalchemy.ext.asyncio import AsyncSession
from models.files import BimFile, PointCloudFile, FileStatus
from sqlalchemy import select, delete


class BimFileCRUD(BaseCRUD[BimFile]):
    """DAO class for CRUD operations with BimFile model."""
    _model = BimFile


class PointCloudFileCRUD(BaseCRUD[PointCloudFile]):
    """DAO class for CRUD operations with PointCloudFile model."""
    _model = PointCloudFile

    @classmethod
    async def update_status(
        cls,
        file: PointCloudFile,
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

from uuid import UUID
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from models.file import (
    File,
    BIM,
    PointCloud,
    FileStatus,
    PointCloudConverted,
)
from .base import BaseRepository


class FileRepository(BaseRepository[File]):
    """Repository class for CRUD operations with File model."""
    _model = File

    @classmethod
    async def get_all_keys(
        cls,
        session: AsyncSession
    ) -> Sequence[str]:
        """Get all file keys in the database."""
        result = await session.execute(
            select(cls._model.key)
        )

        found_keys = result.scalars().all()

        return found_keys

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
        stmt = select(cls._model).where(cls._model.filename == filename).where(
            cls._model.size == size).where(cls._model.content_type == content_type)

        result = await session.execute(stmt)
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


class BIMRepository(BaseRepository[BIM]):
    """Repository class for CRUD operations with BIM model."""
    _model = BIM

    @classmethod
    async def get_by_project_id(
        cls,
        project_id: UUID,
        session: AsyncSession
    ):
        """Get BIM by project ID."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.project_id == project_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_file_id(
        cls,
        file_id: UUID,
        session: AsyncSession
    ):
        """Get BIM by file ID."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.file_id == file_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def set_point_cloud(
        cls,
        bim: BIM,
        point_cloud_id: UUID,
        session: AsyncSession
    ):
        """Set connection to the converted BIM in a point cloud form."""
        bim.point_cloud_id = point_cloud_id

        await session.flush()
        return bim


class PointCloudRepository(BaseRepository[PointCloud]):
    """Repository class for CRUD operations with PointCloud model."""
    _model = PointCloud

    @classmethod
    async def get_by_file_id(
        cls,
        file_id: UUID,
        session: AsyncSession
    ):
        """Get PointCloud by file ID."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.file_id == file_id)
        )
        return result.scalar_one_or_none()


class PointCloudConvertedRepository(BaseRepository[PointCloudConverted]):
    """Repository class for CRUD operations with PointCloudConverted model."""
    _model = PointCloudConverted

    @classmethod
    async def get_by_point_cloud_id(
        cls,
        point_cloud_id: UUID,
        session: AsyncSession
    ):
        """Get files with point cloud ID."""
        result = await session.execute(
            select(cls._model).options(
                selectinload(cls._model.file)
            ).where(cls._model.point_cloud_id == point_cloud_id)
        )
        return result.scalars().all()

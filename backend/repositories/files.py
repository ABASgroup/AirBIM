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
    RecordingResult,
    ResultPhoto
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
        """Get all files using their keys."""
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
            select(cls._model)
            .where(cls._model.point_cloud_id == point_cloud_id)
        )
        return result.scalars().all()


class RecordingResultRepository(BaseRepository[RecordingResult]):
    """Repository class for CRUD operations with RecordingResult model."""
    _model = RecordingResult

    @classmethod
    async def add_photos(
        cls,
        recording_result: RecordingResult,
        photo_files: list[File],
        session: AsyncSession
    ):
        """Add photos to the result.

        Args:
            recording_result (`RecordingResult`): the result you need to pass a list of photos
            photo_files (`list[File]`): a list of photo files for this recording result
            session (`AsyncSession`): an asynchronous database session
        """
        for photo in photo_files:
            entry = ResultPhoto(
                result_id=recording_result.id, file_id=photo.id)
            session.add(instance=entry)

        await session.flush()

    @classmethod
    async def get_photos(
        cls,
        recording_result: RecordingResult,
        session: AsyncSession
    ) -> Sequence[File] | None:
        """Get photo files related to the result.

        Args:
            recording_result (`RecordingResult`): the result for which you require photos.
            session (`AsyncSession`): an asynchronous database session
        """
        result = await session.execute(
            select(ResultPhoto)
            .where(ResultPhoto.result_id == recording_result.id)
            .options(selectinload(ResultPhoto.file))
        )

        photos = result.scalars().all()

        if len(photos) == 0:
            return None

        files = [photo.file for photo in photos]

        return files

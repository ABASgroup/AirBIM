from uuid import UUID
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from models.file import (
    File,
    ResultPhoto
)
from models.recording_result import RecordingResult
from .base import BaseRepository


class RecordingResultRepository(BaseRepository[RecordingResult]):
    """Repository class for CRUD operations with RecordingResult model."""
    _model = RecordingResult

    @classmethod
    async def get_by_project_id(cls, project_id: UUID, session: AsyncSession) -> Sequence[RecordingResult]:
        """Get all recording results for a given project."""
        result = await session.execute(
            select(cls._model).where(cls._model.project_id == project_id)
        )
        recording_results = result.scalars().all()
        return recording_results

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
    async def add_excel_report(
        cls,
        recording_result: RecordingResult,
        report: File,
        session: AsyncSession
    ):
        """Add excel report to the result.

        Args:
            recording_result (`RecordingResult`): the result you need to pass a list of photos
            report (`File`): an .xlsx file of the report
            session (`AsyncSession`): an asynchronous database session
        """
        recording_result.xlsx_report_id = report.id

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

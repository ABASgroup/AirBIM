"""Service layer logic for recording results."""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.exceptions import NotFoundError
from repositories.recording_result import RecordingResultRepository
from schemas.recording_result import (
    RecordingResultModel,
)
from schemas.file import FileModel
from models.recording_result import RecordingResult
from services.file import FileService


class RecordingResultService:
    @classmethod
    async def get_recording_results_for_project(cls, project_id: UUID, session: AsyncSession) -> list[RecordingResult]:
        """Get all recording results for a given project."""
        results = await RecordingResultRepository.get_by_project_id(project_id, session=session)

        return list(results)

    @classmethod
    async def get_recording_result(cls, recording_result_id: UUID, session: AsyncSession) -> RecordingResult:
        """Get all recording results for a given project."""
        result = await RecordingResultRepository.get_by_id(recording_result_id, session=session)

        if result is None:
            raise NotFoundError("No recording result with this ID.")

        result = await RecordingResultRepository.refresh(
            result,
            relations=["project", "pdf_report", "xlsx_report"],
            session=session
        )

        return result

    @classmethod
    async def create_recording_result(
        cls,
        results_data: RecordingResultModel,
        session: AsyncSession
    ) -> RecordingResult:
        """Create a new results record in the database."""
        recording_result = await RecordingResultRepository.create(results_data, session=session)
        return recording_result

    @classmethod
    async def create_excel_report(
        cls,
        recording_result_id: UUID,
        report_file_data: FileModel,
        session: AsyncSession
    ):
        """Create `.xlsx` report for the recording result."""
        result = await cls.get_recording_result(recording_result_id, session)

        file = await FileService.create_file(report_file_data, session)

        await RecordingResultRepository.add_excel_report(result, file, session)

    @classmethod
    async def create_pdf_report(
        cls,
        recording_result_id: UUID,
        report_file_data: FileModel,
        session: AsyncSession,
        photos_file_data: list[FileModel] | None = None,
    ):
        """
        Create `.pdf` report for the recording result.

        Optionally add photos to the report if you need to save them in the database.
        """
        result = await cls.get_recording_result(recording_result_id, session)

        file = await FileService.create_file(report_file_data, session)

        if photos_file_data and len(photos_file_data) > 0:
            photos = []
            for photo_data in photos_file_data:
                photo = await FileService.create_file(photo_data, session)
                photos.append(photo)
            await RecordingResultRepository.add_photos(result, photos, session)
        else:
            photos = None

        await RecordingResultRepository.add_pdf_report(result, file, session)

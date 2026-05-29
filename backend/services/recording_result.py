"""Service layer logic for recording results."""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.recording_result import RecordingResultRepository
from schemas.recording_result import (
    RecordingResultModel,
)
from models.recording_result import RecordingResult

from infrastructure.storage import Storage


class RecordingResultService:
    @classmethod
    async def get_recording_results_for_project(cls, project_id: UUID, session: AsyncSession) -> list[RecordingResult]:
        """Get all recording results for a given project."""
        results = await RecordingResultRepository.get_by_project_id(project_id, session=session)

        return list(results)

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
    async def add_photos_to_result(
        cls,
        recording_result_id: UUID,
        session: AsyncSession
    ):
        pass

    @classmethod
    async def save_result_reports(cls):
        pass

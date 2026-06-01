import uuid
from fastapi import APIRouter, Depends
from services import project as project_service
from services.recording_result import RecordingResultService
from schemas.project import ProjectResponse
from core.roles import Permission
from core.dependencies import (
    get_database_uow,
    DatabaseSessionUOW
)
from api.dependencies import require_recording_result_permission
from tasks.default import create_recording_result_excel_report

router = APIRouter(
    prefix="/recording_results/{recording_result_id}",
    tags=["project recording results"]
)


@router.get(
    "/excel",
    response_model=ProjectResponse,
)
async def get_excel_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    TEST ONLY.

    Get excel report on recording result.
    """
    async with uow:
        recording_result = await RecordingResultService.get_recording_result(
            recording_result_id,
            session=uow.session,
        )
        project = await project_service.get_project(recording_result.project_id, session=uow.session)
    return project


@router.post(
    "/excel",
    response_model=ProjectResponse,
)
async def generate_excel_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    TEST ONLY.

    Generate excel report on recording result.
    """
    return create_recording_result_excel_report.delay(recording_result_id)


@router.get(
    "/pdf",
    response_model=ProjectResponse,
)
async def get_pdf_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    TEST ONLY.

    Get PDF report on recording result.
    """
    async with uow:
        recording_result = await RecordingResultService.get_recording_result(
            recording_result_id,
            session=uow.session,
        )
        project = await project_service.get_project(recording_result.project_id, session=uow.session)
    return project


@router.post(
    "/pdf",
    response_model=ProjectResponse,
)
async def generate_pdf_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    TEST ONLY.

    Generate PDF report on recording result.
    """

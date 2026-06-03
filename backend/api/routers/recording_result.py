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
from tasks.processing import create_recording_result_pdf_report

router = APIRouter(
    prefix="/recording_results/{recording_result_id}",
    tags=["recording results"]
)


@router.get(
    "/excel",
    response_model=ProjectResponse,
)
async def get_excel_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    pass


@router.get(
    "/pdf",
    response_model=ProjectResponse,
)
async def get_pdf_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    pass


@router.delete(
    "",
    response_model=ProjectResponse,
)
async def delete_recording_result(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    Delete recording result.

    All relevant data will be lost (reports, photos, point cloud, etc.).

    Requires permission.
    """
    pass


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


@router.post(
    "/pdf",
    response_model=ProjectResponse,
)
async def generate_pdf_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    TEST ONLY.

    Generate PDF report on recording result.
    """
    return create_recording_result_pdf_report.delay(recording_result_id)

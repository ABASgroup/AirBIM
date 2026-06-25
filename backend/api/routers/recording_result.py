import uuid
from fastapi import APIRouter, Depends
from infrastructure.storage import Storage
from core.exceptions import NotFoundError
from core.dependencies import get_storage
from services.recording_result import RecordingResultService
from services.file import FileService
from schemas.file import FileResponse
from schemas.recording_result import RecordingResultResponse
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
    "",
    response_model=RecordingResultResponse,
    dependencies=[
        Depends(require_recording_result_permission(
            Permission.RECORDING_RESULT_VIEW))],
)
async def get_recording_result(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    Get the recording result you need.

    Requires permission.
    """
    async with uow:
        result = await RecordingResultService.get_recording_result(recording_result_id, uow.session)
    return result


@router.delete(
    "",
    response_model=RecordingResultResponse,
    dependencies=[
        Depends(require_recording_result_permission(
            Permission.RECORDING_RESULT_VIEW))],
)
async def delete_recording_result(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    Delete recording result.

    All relevant data will be lost (reports, photos, point cloud, etc.).

    Requires permission.
    """
    async with uow:
        result = await RecordingResultService.delete_recording_result(recording_result_id, uow.session)
    return result


@router.get(
    "/excel",
    response_model=FileResponse,
    dependencies=[
        Depends(require_recording_result_permission(
            Permission.RECORDING_RESULT_VIEW))],
)
async def get_excel_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    Get **Excel** report on the recording result you need.

    Provides report file data.

    You can use it to download file on request.

    Requires permission.
    """
    async with uow:
        report = await RecordingResultService.get_excel_report(recording_result_id, uow.session)
    return report


@router.get(
    "/pdf",
    response_model=FileResponse,
    dependencies=[
        Depends(require_recording_result_permission(
            Permission.RECORDING_RESULT_VIEW))],
)
async def get_pdf_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    Get **PDF** report on the recording result you need.

    Provides report file data and URL to download the report.

    Requires permission.
    """
    async with uow:
        report = await RecordingResultService.get_pdf_report(recording_result_id, uow.session)
    return report


@router.post(
    "/excel",
)
async def generate_excel_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    TEST ONLY.

    Generate excel report on recording result.
    """
    return create_recording_result_excel_report.delay(recording_result_id)


@router.post(
    "/pdf",
)
async def generate_pdf_report(recording_result_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    TEST ONLY.

    Generate PDF report on recording result.
    """
    return create_recording_result_pdf_report.delay(recording_result_id)

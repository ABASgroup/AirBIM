from sqlalchemy.ext.asyncio import AsyncSession
from schemas.stage import StagePublic
from storage import Storage
from schemas.files import FileUploadRequest, FileLinkPublic
from services import stage as stage_service
from services.file import FileService
from roles import Permission
from fastapi import APIRouter, Depends

from dependencies import (
    get_db_session,
    require_stage_permission,
    get_storage
)

from roles import Permission


router = APIRouter(prefix="/stage", tags=["project stages"])


@router.get(
    "/{stage_id}",
    response_model=StagePublic,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_VIEW))],
)
async def get_stage(stage_id: int, session: AsyncSession = Depends(get_db_session)):
    stage = await stage_service.get_stage(stage_id, session=session)
    return stage


@router.delete(
    "/{stage_id}",
    response_model=StagePublic,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_DELETE))],
)
async def delete_project(
    stage_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    stage = await stage_service.delete_stage(stage_id, session=session)
    return stage


@router.post(
    "/{stage_id}/files/point_cloud/upload",
    response_model=FileLinkPublic,
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_DOWNLOAD))],
)
async def get_point_cloud_upload_link(
    project_id: int,
    file_data: FileUploadRequest,
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to upload file.

    Use this link to upload file.

    Requires permission.
    """
    url = FileService.generate_file_upload_link(
        project_id, file_data, storage=storage)

    link_data = FileLinkPublic(
        project_id=project_id,
        presigned_url=url,
        filename=file_data.filename
    )

    return link_data

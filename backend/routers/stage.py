import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.stage import StagePublic
from storage import Storage
from schemas.files import (
    FileLinkResponse,
    FileUploadConfirmRequest,
    FileUploadLinkRequest,
    PointCloudFileResponse,
)
from services import stage as stage_service
from services.file import FileService
from roles import Permission

from dependencies import (
    get_db_session,
    require_stage_permission,
    get_storage
)


router = APIRouter(prefix="/stages", tags=["project stages"])


@router.get(
    "/{stage_id}",
    response_model=StagePublic,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_VIEW))],
)
async def get_stage(stage_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    stage = await stage_service.get_stage(stage_id, session=session)
    return stage


@router.delete(
    "/{stage_id}",
    response_model=StagePublic,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_DELETE))],
)
async def delete_stage(
    stage_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    storage: Storage = Depends(get_storage)
):
    """
    Delete stage and all related data and files.

    Requires permission.
    """
    stage = await stage_service.delete_stage(stage_id, session=session, storage=storage)
    return stage


@router.post(
    "/{stage_id}/files/point_clouds/upload",
    response_model=FileLinkResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_UPLOAD_CLOUDS))],
)
async def get_point_cloud_upload_link(
    stage_id: uuid.UUID,
    file_data: FileUploadLinkRequest,
    session: AsyncSession = Depends(get_db_session),
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to upload file.

    Use this link to upload file.

    Requires permission.
    """
    stage = await stage_service.get_stage_with_project(stage_id, session=session)

    url, key = await FileService.generate_point_cloud_upload_link(
        stage.project.workspace_id,
        stage.project.id,
        stage.id,
        file_data,
        storage=storage,
        session=session
    )

    link_data = FileLinkResponse(
        key=key,
        url=url,
        filename=file_data.filename,
        size=file_data.size,
        content_type=file_data.content_type
    )

    return link_data


@router.post(
    "/{stage_id}/files/point_clouds/confirm",
    response_model=PointCloudFileResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_UPLOAD_CLOUDS))],
)
async def confirm_point_cloud_upload(
    stage_id: uuid.UUID,
    file_data: FileUploadConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
    storage: Storage = Depends(get_storage)
):
    """
    Confirm finishing uploading a point cloud file.

    You can't confirm file upload if file is not uploaded.

    Requires permission.
    """
    file = await FileService.confirm_point_cloud_upload(
        stage_id,
        file_data,
        storage=storage,
        session=session
    )

    return file

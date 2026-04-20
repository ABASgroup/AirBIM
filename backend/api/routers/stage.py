import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.storage import Storage
from schemas.files import (
    FileLinkResponse,
    FileUploadConfirmRequest,
    FileUploadLinkRequest,
    PointCloudFileResponse,
)
from schemas.stage import StageResponse
from services import stage as stage_service
from services.file import FileService
from core.roles import Permission

from core.dependencies import (
    get_database_uow,
    get_storage,
    DatabaseSessionUOW
)
from api.dependencies import (
    require_stage_permission
)

router = APIRouter(prefix="/stages", tags=["project stages"])


@router.get(
    "/{stage_id}",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_VIEW))],
)
async def get_stage(stage_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    async with uow:
        stage = await stage_service.get_stage(stage_id, session=uow.session)
    return stage


@router.delete(
    "/{stage_id}",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_DELETE))],
)
async def delete_stage(
    stage_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Delete stage and all related data and files.

    Requires permission.
    """
    async with uow:
        stage = await stage_service.delete_stage(stage_id, session=uow.session, storage=storage)
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
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to upload point cloud file.

    Use this link to upload file.

    Requires permission.
    """
    async with uow:
        stage = await stage_service.get_stage_with_project(stage_id, session=uow.session)

        url, key = await FileService.generate_point_cloud_upload_link(
            stage.project.workspace_id,
            stage.project.id,
            stage.id,
            file_data,
            storage=storage,
            session=uow.session
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
    file_data: FileUploadConfirmRequest,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Confirm finishing uploading a point cloud file.

    You can't confirm file upload if file is not uploaded.

    Requires permission.
    """
    async with uow:
        file = await FileService.confirm_point_cloud_upload(
            file_data,
            session=uow.session,
            storage=storage
        )

    return file

import uuid
from fastapi import APIRouter, Depends
from infrastructure.storage import Storage
from schemas.stage import StageResponse
from schemas.files import (
    FileDataRequest,
    FileLinkResponse,
)
from services import stage as stage_service
from services import project as project_service
from core.roles import Permission

from core.dependencies import (
    get_database_uow,
    get_storage,
    DatabaseSessionUOW
)
from api.dependencies import (
    require_stage_permission
)

from services.file import FileService

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
    "/{stage_id}/clouds/upload",
    response_model=FileLinkResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_UPLOAD))],
)
async def get_point_cloud_upload_link(
    stage_id: uuid.UUID,
    file_data: FileDataRequest,
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
            stage=stage,
            file_data=file_data,
            session=uow.session,
            storage=storage
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
    "/{stage_id}/clouds/{point_cloud_id}/converted",
    response_model=FileLinkResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_DOWNLOAD))],
)
async def get_converted_point_cloud_download_link(
    stage_id: uuid.UUID,
    point_cloud_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary links to download a converted point cloud file.

    You get multiple links to download all files.

    Converted clouds are required for efficient visualization via Potree.

    Requires permission.
    """
    async with uow:
        url, key = await FileService.generate_bim_upload_link(
            project=project,
            file_data=file_data,
            session=uow.session,
            storage=storage
        )

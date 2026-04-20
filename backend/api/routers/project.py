import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.storage import Storage
from services import project as project_service
from services import stage as stage_service
from services.file import FileService
from schemas.project import ProjectResponse, ProjectUpdate
from schemas.stage import StageModel, StageResponse
from schemas.files import (
    FileUploadLinkRequest,
    FileUploadConfirmRequest,
    FileLinkResponse,
    BIMFileResponse
)
from core.roles import Permission
from core.dependencies import (
    get_database_uow,
    get_storage,
    DatabaseSessionUOW
)

from api.dependencies import require_project_permission

router = APIRouter(prefix="/projects", tags=["workspace projects"])


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_VIEW))],
)
async def get_project(project_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    """
    Get project information.

    Requires permission.
    """
    async with uow:
        project = await project_service.get_project(project_id, session=uow.session)
    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_EDIT))],
)
async def update_project(
    project_id: uuid.UUID,
    project_data: ProjectUpdate,
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Update project information.

    Requires permission.
    """
    async with uow:
        project = await project_service.update_project(
            project_id, project_data, session=uow.session
        )
    return project


@router.delete(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_DELETE))],
)
async def delete_project(
    project_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Delete project and all related data and files.

    Requires permission.
    """
    async with uow:
        project = await project_service.delete_project(project_id, session=uow.session, storage=storage)
    return project


@router.get(
    "/{project_id}/stages",
    response_model=list[StageResponse],
    dependencies=[
        Depends(require_project_permission(Permission.STAGE_VIEW))],
)
async def get_project_stages(
    project_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Get all stages related to the project.

    Requires permission.
    """
    async with uow:
        stages = await stage_service.get_project_stages(
            project_id, session=uow.session
        )
    return stages


@router.post(
    "/{project_id}/stages",
    response_model=StageResponse,
    dependencies=[
        Depends(require_project_permission(Permission.STAGE_CREATE))],
)
async def create_stage(
    project_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Create new stage related to the project.

    Requires permission.
    """
    stage_data_db = StageModel(project_id=project_id)
    async with uow:
        stage = await stage_service.create_stage(stage_data_db, session=uow.session)
    return stage


@router.post(
    "/{project_id}/files/bim/upload",
    response_model=FileLinkResponse,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_UPLOAD_BIM))],
)
async def get_bim_upload_link(
    project_id: uuid.UUID,
    file_data: FileUploadLinkRequest,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to upload BIM file.

    Use this link to upload file.

    Requires permission.
    """
    async with uow:
        project = await project_service.get_project(project_id, session=uow.session)

        url, key = await FileService.generate_bim_upload_link(
            project_id=project_id,
            workspace_id=project.workspace_id,
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
    "/{project_id}/files/bim/confirm",
    response_model=BIMFileResponse,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_UPLOAD_BIM))],
)
async def confirm_bim_upload(
    file_data: FileUploadConfirmRequest,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Confirm finishing uploading a BIM file.

    You can't confirm file upload if file is not uploaded.

    Requires permission.
    """
    async with uow:
        file = await FileService.confirm_bim_upload(
            file_data=file_data,
            session=uow.session,
            storage=storage
        )

    return file


@router.delete(
    "/{project_id}/files/bim",
    response_model=BIMFileResponse,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_DELETE_BIM))],
)
async def delete_bim_file(
    project_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Delete project's BIM file.

    This action deletes file from the storage and removes record from the database.

    Be cautious, related reports, point clouds will become irrelevant without the BIM file.

    Requires permission.
    """
    async with uow:
        file = await FileService.delete_bim_file(
            project_id=project_id,
            session=uow.session,
            storage=storage
        )

    return file


@router.post(
    "/{project_id}/files/bim/download",
    response_model=FileLinkResponse,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_DOWNLOAD))],
)
async def get_bim_download_link(
    project_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to download BIM file.

    Use this link to download file.

    Requires permission.
    """
    async with uow:
        url, file = await FileService.generate_bim_download_link(
            project_id=project_id,
            session=uow.session,
            storage=storage
        )

    link_data = FileLinkResponse(
        key=file.key,
        url=url,
        filename=file.filename,
        size=file.size,
        content_type=file.content_type
    )

    return link_data

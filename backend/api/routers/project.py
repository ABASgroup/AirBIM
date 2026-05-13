import uuid
from fastapi import APIRouter, Depends
from infrastructure.storage import Storage
from services import project as project_service
from services import stage as stage_service
from services.file import FileService
from schemas.project import ProjectResponse, ProjectUpdate
from schemas.stage import StageModel, StageResponse
from schemas.files import (
    FileDataRequest,
    FileLinkResponse,
    BIMResponse,
    FileModel
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
        project = await project_service.delete_project(
            project_id,
            session=uow.session,
            storage=storage
        )
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
    "/{project_id}/bim/upload",
    response_model=FileLinkResponse,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_UPLOAD))],
)
async def get_bim_upload_link(
    project_id: uuid.UUID,
    file_data: FileDataRequest,
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
        key = FileService.create_file_key(
            filename=file_data.filename
        )

        url, file = await FileService.generate_bim_upload_link(
            project_id=project.id,
            file_data=FileModel(**file_data.model_dump(), key=key),
            session=uow.session,
            storage=storage
        )

    response_data = FileLinkResponse.model_validate(file, from_attributes=True)
    response_data.url = url

    return response_data


@router.get(
    "/{project_id}/bim",
    response_model=BIMResponse,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_VIEW))],
)
async def get_project_bim(
    project_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Get project's BIM file.

    Provides metadata about the BIM.

    Requires permission.
    """
    async with uow:
        project = await project_service.get_project(project_id, session=uow.session)
        bim = project.bim

    return bim

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from storage import Storage
from services import project as project_service
from services import stage as stage_service
from schemas.project import ProjectResponse, ProjectUpdate
from schemas.stage import StageModel, StagePublic
from roles import Permission
from dependencies import (
    get_db_session,
    require_project_permission,
    get_storage
)


router = APIRouter(prefix="/projects", tags=["workspace projects"])


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_VIEW))],
)
async def get_project(project_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    """
    Get project information.

    Requires permission.
    """
    project = await project_service.get_project(project_id, session=session)
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
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update project information.

    Requires permission.
    """
    project = await project_service.update_project(
        project_id, project_data, session=session
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
    session: AsyncSession = Depends(get_db_session),
    storage: Storage = Depends(get_storage)
):
    """
    Delete project and all related data and files.

    Requires permission.
    """
    project = await project_service.delete_project(project_id, session=session, storage=storage)
    return project


@router.get(
    "/{project_id}/stages",
    response_model=list[StagePublic],
    dependencies=[
        Depends(require_project_permission(Permission.STAGE_VIEW))],
)
async def get_project_stages(
    project_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)
):
    """
    Get all stages related to the project.
    
    Requires permission.
    """
    stages = await stage_service.get_project_stages(
        project_id, session=session
    )
    return stages


@router.post(
    "/{project_id}/stages",
    response_model=StagePublic,
    dependencies=[
        Depends(require_project_permission(Permission.STAGE_CREATE))],
)
async def create_stage(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create new stage related to the project.
    
    Requires permission.
    """
    stage_data_db = StageModel(project_id=project_id)
    stage = await stage_service.create_stage(stage_data_db, session=session)
    return stage

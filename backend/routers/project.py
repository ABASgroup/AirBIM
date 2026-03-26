from services import project as project_service
from services import stage as stage_service

from schemas.project import ProjectPublic, ProjectUpdate
from schemas.stage import StageCreate, StagePublic

from roles import Permission
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import (
    get_db_session,
    require_project_permission
)

from roles import Permission


router = APIRouter(prefix="/project", tags=["workspace projects"])


@router.get(
    "/{project_id}",
    response_model=ProjectPublic,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_VIEW))],
)
async def get_project(project_id: int, session: AsyncSession = Depends(get_db_session)):
    project = await project_service.get_project(project_id, session=session)
    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectPublic,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_EDIT))],
)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    project = await project_service.update_project(
        project_id, project_data, session=session
    )
    return project


@router.delete(
    "/{project_id}",
    response_model=ProjectPublic,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_DELETE))],
)
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    project = await project_service.delete_project(project_id, session=session)
    return project


@router.get(
    "/{project_id}/stage",
    response_model=list[StagePublic],
    dependencies=[
        Depends(require_project_permission(Permission.STAGE_VIEW))],
)
async def get_project_stages(
    project_id: int, session: AsyncSession = Depends(get_db_session)
):
    """Get all stages related to the project."""
    stages = await stage_service.get_project_stages(
        project_id, session=session
    )
    return stages


@router.post(
    "/{project_id}/stage",
    response_model=StagePublic,
    dependencies=[
        Depends(require_project_permission(Permission.STAGE_CREATE))],
)
async def create_stage(
    project_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    stage_data_db = StageCreate(project_id=project_id)
    stage = await stage_service.create_stage(stage_data_db, session=session)
    return stage

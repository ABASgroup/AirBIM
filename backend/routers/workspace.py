from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db_session, get_current_user_id
from schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate
from services import project as project_service

router = APIRouter(prefix="/workspace",
                   tags=["workspaces, projects, memberships"])


@router.post("/projects", response_model=ProjectPublic)
async def create_project(
    project_data: ProjectCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    project = await project_service.create_project(project_data, session=session)
    return project


@router.get("/{workspace_id}/projects", response_model=list[ProjectPublic])
async def get_workspace_projects(
    workspace_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    """Get all projects related to the workspace"""
    projects = await project_service.get_workspace_projects(workspace_id, session=session)
    return projects


@router.get("/{workspace_id}/projects/{project_id}", response_model=ProjectPublic)
async def get_project(
    workspace_id: int,
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    project = await project_service.get_project(project_id, session=session)
    return project


@router.patch("/{workspace_id}/projects/{project_id}", response_model=ProjectPublic)
async def update_project(
    workspace_id: int,
    project_id: int,
    project_data: ProjectUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    project = await project_service.update_project(project_id, project_data, session=session)
    return project


@router.delete("/{workspace_id}/projects/{project_id}", response_model=ProjectPublic)
async def delete_project(
    workspace_id: int,
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    project = await project_service.delete_project(project_id, session=session)
    return project

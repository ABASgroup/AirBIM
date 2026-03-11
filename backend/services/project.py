"""Service layer logic for Project."""
from sqlalchemy.ext.asyncio import AsyncSession
from crud.project import ProjectCRUD
from crud.workspace import WorkspaceCRUD
from models.project import Project
from schemas.project import ProjectCreate, ProjectUpdate


async def get_project(project_id: int, session: AsyncSession) -> Project:
    """Get project using its ID"""
    try:
        project = await ProjectCRUD.get_by_id(project_id, session=session)
        return project
    except Exception as exc:
        raise Exception from exc


async def get_workspace_projects(workspace_id: int, session: AsyncSession) -> list[Project]:
    """Get all projects related to the workspace"""
    try:
        projects = await ProjectCRUD.get_by_workspace_id(workspace_id, session=session)
        return list(projects)
    except Exception as exc:
        raise Exception from exc


async def create_project(project_data: ProjectCreate, session: AsyncSession) -> Project:
    """
    Create a new project for the workspace.
    """
    try:
        project = await ProjectCRUD.create(project_data, session=session)
        await session.commit()
        return project
    except Exception as exc:
        await session.rollback()
        raise Exception from exc


async def update_project(project_id: int, project_data: ProjectUpdate, session: AsyncSession) -> Project:
    """Update information about project using its ID"""
    try:
        project = await ProjectCRUD.update_by_id(project_id, project_data, session=session)
        await session.commit()
        return project
    except Exception as exc:
        await session.rollback()
        raise Exception from exc


async def delete_project(project_id: int, session: AsyncSession) -> Project:
    """Delete project using its ID"""
    try:
        project = await ProjectCRUD.delete_by_id(project_id, session=session)
        await session.commit()
        return project
    except Exception as exc:
        await session.rollback()
        raise Exception from exc

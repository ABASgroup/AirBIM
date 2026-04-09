"""Service layer logic for Project."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from storage import Storage
from exceptions.exceptions import NotFoundError
from repositories.project import ProjectRepository
from models.project import Project
from schemas.project import ProjectModel, ProjectUpdate

from services.file import FileService


async def get_project(project_id: uuid.UUID, session: AsyncSession) -> Project:
    """Get project using its ID"""
    project = await ProjectRepository.get_by_id(project_id, session=session)

    if project is None:
        raise NotFoundError("No project with this ID")

    return project


async def get_workspace_projects(workspace_id: uuid.UUID, session: AsyncSession) -> list[Project]:
    """Get all projects related to the workspace"""
    projects = await ProjectRepository.get_by_workspace_id(workspace_id, session=session)
    projects = list(projects)

    return projects


async def create_project(project_data: ProjectModel, session: AsyncSession) -> Project:
    """
    Create a new project for the workspace.
    """
    try:
        project = await ProjectRepository.create(project_data, session=session)
        await session.commit()
        return project
    except Exception:
        await session.rollback()
        raise


async def update_project(project_id: uuid.UUID, project_data: ProjectUpdate, session: AsyncSession) -> Project:
    """Update information about project using its ID"""
    try:
        project = await ProjectRepository.update_by_id(project_id, project_data, session=session)
        await session.commit()
        return project
    except AttributeError as exc:
        await session.rollback()
        raise NotFoundError("Project was not found") from exc
    except Exception:
        await session.rollback()
        raise


async def delete_project(project_id: uuid.UUID, session: AsyncSession, storage: Storage) -> Project:
    """
    Delete project using its ID.

    Make sure to check permission.
    """
    try:
        project = await ProjectRepository.get_by_id(project_id, session=session)

        if project is None:
            raise NotFoundError("Project was not found.")

        # clear project files first
        FileService.clear_project_files(
            project.workspace_id, project.id, storage)

        # drop entry and related entries
        await ProjectRepository.delete(project, session=session)

        await session.commit()
        return project
    except Exception:
        await session.rollback()
        raise

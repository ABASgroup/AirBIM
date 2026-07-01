"""Service layer logic for Project."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from core.exceptions import NotFoundError
from repositories.project import ProjectRepository
from models.project import Project
from schemas.project import ProjectModel, ProjectUpdate


class ProjectService:
    @classmethod
    async def get_project(cls, project_id: uuid.UUID, session: AsyncSession) -> Project:
        """Get project using its ID."""
        project = await ProjectRepository.get_by_id(project_id, relations=["bim", "stages"], session=session)

        if project is None:
            raise NotFoundError("No project with such ID.")

        return project

    @classmethod
    async def get_workspace_projects(cls, workspace_id: uuid.UUID, session: AsyncSession) -> list[Project]:
        """Get all projects related to the workspace"""
        projects = await ProjectRepository.get_by_workspace_id(workspace_id, session=session)
        projects = list(projects)
        return projects

    @classmethod
    async def create_project(cls, project_data: ProjectModel, session: AsyncSession) -> Project:
        """Create a new project for the workspace."""
        project = await ProjectRepository.create(project_data.model_dump(exclude_unset=True), session=session)
        return project

    @classmethod
    async def update_project(cls, project_id: uuid.UUID, project_data: ProjectUpdate, session: AsyncSession) -> Project:
        """Update information about project using its ID."""
        project = await cls.get_project(project_id, session=session)
        project = await ProjectRepository.update(project, project_data.model_dump(exclude_unset=True), session=session)
        return project

    @classmethod
    async def delete_project(cls, project_id: uuid.UUID, session: AsyncSession) -> Project:
        """
        Delete project using its ID.

        Make sure to check permission.
        """
        project = await cls.get_project(project_id, session=session)
        await ProjectRepository.delete(project, session=session)

        return project

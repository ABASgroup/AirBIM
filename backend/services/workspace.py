"""Service layer logic for Workspace."""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.workspace import WorkspaceRepository
from repositories.membership import MembershipRepository
from core.exceptions import NotFoundError, ProhibitedWorkspaceActionError
from models.workspace import WorkspaceType, Workspace
from schemas.workspace import WorkspaceModel, WorkspaceUpdate
from .project import ProjectService


class WorkspaceService:
    @classmethod
    async def get_workspace(cls, workspace_id: UUID, session: AsyncSession):
        """Get workspace using its ID"""
        workspace = await WorkspaceRepository.get_by_id(workspace_id, session=session)

        if workspace is None:
            raise NotFoundError("Workspace was not found")

        return workspace

    @classmethod
    async def get_user_workspaces(cls, user_id: UUID, session: AsyncSession) -> list[Workspace]:
        """Get all workspaces where the user is a member"""
        memberships = await MembershipRepository.get_all_user_memberships(user_id, session=session)

        # extract all workspace IDs
        workspace_ids = [membership.workspace_id for membership in memberships]

        # get workspaces
        workspaces = await WorkspaceRepository.get_by_ids(workspace_ids, session)
        return list(workspaces)

    @classmethod
    async def create_workspace(cls, workspace_data: WorkspaceModel, session: AsyncSession):
        """
        Create a new workspace
        """
        workspace = await WorkspaceRepository.create(workspace_data.model_dump(exclude_unset=True), session=session)
        return workspace

    @classmethod
    async def update_workspace(
        cls,
        workspace_id: UUID,
        workspace_data: WorkspaceUpdate,
        session: AsyncSession
    ):
        try:
            workspace = await cls.get_workspace(workspace_id, session=session)
            workspace = await WorkspaceRepository.update(
                workspace,
                workspace_data.model_dump(exclude_unset=True),
                session=session
            )

            return workspace
        except AttributeError as exc:
            raise NotFoundError("Workspace was not found") from exc

    @classmethod
    async def delete_team_workspace(cls, workspace_id: UUID, session: AsyncSession):
        """
        Delete team workspace using its id.

        You can't delete personal workspace no matter what.
        """
        workspace = await cls.get_workspace(workspace_id, session=session)

        # check type
        if workspace.type != WorkspaceType.TEAM:
            raise ProhibitedWorkspaceActionError("deleting personal workspace")

        # it's team workspace, deletion is safe
        await WorkspaceRepository.delete(workspace, session=session)
        return workspace

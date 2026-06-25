"""Service layer logic for Workspace."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.storage import Storage
from repositories.workspace import WorkspaceRepository
from repositories.membership import MembershipRepository
from core.exceptions import NotFoundError, ProhibitedWorkspaceActionError
from models.workspace import WorkspaceType, Workspace
from schemas.workspace import WorkspaceModel


async def get_workspace(workspace_id: uuid.UUID, session: AsyncSession):
    """Get workspace using its ID"""
    workspace = await WorkspaceRepository.get_by_id(workspace_id, session=session)

    if workspace is None:
        raise NotFoundError("Workspace was not found")

    return workspace


async def get_user_workspaces(user_id: uuid.UUID, session: AsyncSession) -> list[Workspace]:
    """Get all workspaces where the user is a member"""
    memberships = await MembershipRepository.get_all_user_memberships(user_id, session=session)

    # extract all workspace IDs
    workspace_ids = [membership.workspace_id for membership in memberships]

    # get workspaces
    workspaces = []
    for workspace_id in workspace_ids:
        workspace = await WorkspaceRepository.get_by_id(workspace_id, session=session)
        workspaces.append(workspace)
    return workspaces


async def create_workspace(workspace_data: WorkspaceModel, session: AsyncSession):
    """
    Create a new workspace
    """
    workspace = await WorkspaceRepository.create(workspace_data.model_dump(exclude_unset=True), session=session)
    return workspace


async def delete_team_workspace(workspace_id: uuid.UUID, session: AsyncSession):
    """
    Delete team workspace using its id.

    You can't delete personal workspace no matter what.
    """
    workspace = await WorkspaceRepository.get_by_id(workspace_id, session=session)

    if workspace is None:
        raise NotFoundError("Workspace was not found")

    # check type
    if workspace.type != WorkspaceType.TEAM:
        raise ProhibitedWorkspaceActionError("deleting personal workspace")

    # it's team workspace, deletion is safe
    await WorkspaceRepository.delete(workspace, session=session)
    return workspace

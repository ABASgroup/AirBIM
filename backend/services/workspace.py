"""Service layer logic for Workspace."""
from sqlalchemy.ext.asyncio import AsyncSession
from crud.workspace import WorkspaceCRUD
from crud.membership import MembershipCRUD
from exceptions.exceptions import NotFoundError, ProhibitedWorkspaceAction
from models.workspace import WorkspaceType, Workspace
from schemas.workspace import WorkspaceCreate


async def get_workspace(workspace_id: int, session: AsyncSession):
    """Get workspace using its ID"""
    workspace = await WorkspaceCRUD.get_by_id(workspace_id, session=session)
    return workspace


async def get_user_workspaces(user_id: int, session: AsyncSession) -> list[Workspace]:
    """Get all workspaces where the user is a member"""
    try:
        memberships = await MembershipCRUD.get_all_user_memberships(user_id, session=session)

        # extract all workspace IDs
        workspace_ids = [membership.workspace_id for membership in memberships]

        # get workspaces
        workspaces = []
        for workspace_id in workspace_ids:
            workspace = await WorkspaceCRUD.get_by_id(workspace_id, session=session)
            workspaces.append(workspace)
        return workspaces
    except Exception:
        await session.rollback()
        raise


async def create_workspace(workspace_data: WorkspaceCreate, session: AsyncSession):
    """
    Create a new workspace
    """
    try:
        workspace = await WorkspaceCRUD.create(workspace_data, session=session)
        await session.commit()
        return workspace
    except Exception:
        await session.rollback()
        raise


async def delete_team_workspace(workspace_id, session: AsyncSession):
    """
    Delete team workspace using its id

    You can't delete personal workspace no matter what
    """
    try:
        workspace = await WorkspaceCRUD.get_by_id(workspace_id, session=session)

        if workspace is None:
            raise NotFoundError("Workspace was not found")

        # check type
        if workspace.type != WorkspaceType.TEAM:
            raise ProhibitedWorkspaceAction("deleting personal workspace")

        # it's team workspace, deletion is safe
        await WorkspaceCRUD.delete(workspace, session=session)
        await session.commit()
        return workspace
    except Exception:
        await session.rollback()
        raise

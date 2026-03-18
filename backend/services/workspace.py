"""Service layer logic for Workspace."""
from sqlalchemy.ext.asyncio import AsyncSession
from crud.workspace import WorkspaceCRUD
from exceptions.exceptions import NotFoundError, ProhibitedWorkspaceAction
from models.workspace import WorkspaceType
from schemas.workspace import WorkspaceCreate


async def get_workspace(workspace_id: int, session: AsyncSession):
    """Get workspace using its ID"""
    project = await WorkspaceCRUD.get_by_id(workspace_id, session=session)
    return project


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

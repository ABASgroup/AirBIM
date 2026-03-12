"""Service layer logic for Workspace."""
from sqlalchemy.ext.asyncio import AsyncSession
from crud.workspace import WorkspaceCRUD
from models.workspace import Workspace, WorkspaceType
from schemas.workspace import WorkspaceCreate


async def get_workspace(workspace_id: int, session: AsyncSession):
    """Get workspace using its ID"""
    try:
        project = await WorkspaceCRUD.get_by_id(workspace_id, session=session)
        return project
    except Exception as exc:
        raise Exception from exc


async def create_workspace(workspace_data: WorkspaceCreate, session: AsyncSession):
    """
    Create a new workspace
    """
    try:
        workspace = await WorkspaceCRUD.create(workspace_data, session=session)
        await session.commit()
        return workspace
    except Exception as exc:
        await session.rollback()
        raise Exception from exc


async def delete_team_workspace(workspace_id, session: AsyncSession):
    """
    Delete team workspace using its id

    You can't delete personal workspace no matter what
    """
    try:
        workspace = await WorkspaceCRUD.get_by_id(workspace_id, session=session)

        # check type
        if workspace.type != WorkspaceType.TEAM:
            raise ValueError("Personal workspace can't be deleted")

        # it's team workspace, deletion is safe
        await WorkspaceCRUD.delete(workspace, session=session)
        await session.commit()
        return workspace
    except Exception as exc:
        await session.rollback()
        raise Exception from exc

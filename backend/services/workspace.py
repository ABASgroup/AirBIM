"""Service layer logic for Workspace."""
from sqlalchemy.ext.asyncio import AsyncSession
from crud.workspace import WorkspaceCRUD
from models.workspace import Workspace
from schemas.workspace import WorkspaceCreate


async def create_workspace(workspace_data: WorkspaceCreate, session: AsyncSession) -> Workspace:
    """
    Create a new workspace.
    """
    try:
        workspace = await WorkspaceCRUD.create(workspace_data, session=session)
        await session.commit()
        return workspace
    except Exception as exc:
        await session.rollback()
        raise Exception from exc

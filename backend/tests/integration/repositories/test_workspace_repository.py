"""Tests for Workspace Repository."""
import pytest

from repositories.workspace import WorkspaceRepository
from schemas.workspace import WorkspaceModel, WorkspaceType


@pytest.mark.asyncio
async def test_workspace_repository_create(db_session):
    """Test workspace creation."""
    workspace = await WorkspaceRepository.create(
        WorkspaceModel(name="Test workspace",
                       type=WorkspaceType.TEAM).model_dump(exclude_unset=True),
        session=db_session,
    )

    assert workspace.id is not None
    assert workspace.name == "Test workspace"

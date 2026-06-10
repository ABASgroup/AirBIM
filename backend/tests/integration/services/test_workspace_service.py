"""Tests for Workspace Service."""
import pytest

from core.exceptions import NotFoundError, ProhibitedWorkspaceActionError
from core.roles import Role
from schemas.workspace import WorkspaceModel, WorkspaceType
from services.workspace import get_workspace, get_user_workspaces, create_workspace, delete_team_workspace

from tests.helpers import create_test_workspace, create_test_user, create_test_membership


@pytest.mark.asyncio
async def test_create_and_get_workspace(db_session):
    """Service should return workspace by its ID."""
    workspace_data = WorkspaceModel(
        name="Test Workspace", type=WorkspaceType.TEAM)

    workspace = await create_workspace(workspace_data, session=db_session)

    assert workspace.id is not None
    assert workspace.name == "Test Workspace"

    retrieved_workspace = await get_workspace(workspace.id, session=db_session)

    assert retrieved_workspace is not None
    assert retrieved_workspace.id == workspace.id
    assert retrieved_workspace.name == workspace.name


@pytest.mark.asyncio
async def test_get_user_workspaces(db_session):
    """Service should return all workspaces where user is a member."""
    workspace1 = await create_test_workspace(db_session)
    workspace2 = await create_test_workspace(db_session)
    user = await create_test_user(db_session)
    _ = await create_test_membership(db_session, workspace_id=workspace1.id, user_id=user.id, role=Role.MEMBER)

    workspaces = await get_user_workspaces(user.id, session=db_session)
    assert len(workspaces) == 1
    assert workspace1 in workspaces

    _ = await create_test_membership(db_session, workspace_id=workspace2.id, user_id=user.id, role=Role.OWNER)

    workspaces = await get_user_workspaces(user.id, session=db_session)
    assert len(workspaces) == 2
    assert workspace1 in workspaces
    assert workspace2 in workspaces


@pytest.mark.asyncio
async def test_delete_team_workspace(db_session):
    """Service should delete team workspace."""
    workspace = await create_test_workspace(db_session)

    await delete_team_workspace(workspace.id, session=db_session)

    with pytest.raises(NotFoundError):
        await get_workspace(workspace.id, session=db_session)

    with pytest.raises(NotFoundError):
        await delete_team_workspace(workspace.id, session=db_session)


@pytest.mark.asyncio
async def test_delete_personal_workspace(db_session):
    """Service should not allow deleting personal workspace."""
    workspace = await create_test_workspace(db_session, workspace_type=WorkspaceType.PERSONAL)

    with pytest.raises(ProhibitedWorkspaceActionError):
        await delete_team_workspace(workspace.id, session=db_session)

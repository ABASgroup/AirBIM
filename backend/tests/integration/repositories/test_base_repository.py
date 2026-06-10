"""Tests for the base repository (on example of a model that uses it)."""

import uuid

import pytest

from repositories.workspace import WorkspaceRepository

from tests.helpers import create_test_workspace, create_test_project


@pytest.mark.asyncio
async def test_base_repository_create(db_session):
    """Test the 'create' method of the base repository."""
    workspace = await create_test_workspace(db_session)
    assert workspace is not None
    assert workspace.id is not None
    assert workspace.created_at is not None
    assert workspace.updated_at is not None


@pytest.mark.asyncio
async def test_base_repository_get_all(db_session):
    """Test the 'get_all' method of the base repository."""
    workspace1 = await create_test_workspace(db_session)

    workspaces = await WorkspaceRepository.get_all(session=db_session)
    assert len(workspaces) == 1
    assert workspace1 in workspaces

    workspace2 = await create_test_workspace(db_session)
    workspace3 = await create_test_workspace(db_session)

    workspaces = await WorkspaceRepository.get_all(session=db_session)
    assert len(workspaces) == 3
    assert workspace1 in workspaces
    assert workspace2 in workspaces
    assert workspace3 in workspaces


@pytest.mark.asyncio
async def test_base_repository_get_by_id(db_session):
    """Test the 'get_by_id' method of the base repository."""
    workspace = await create_test_workspace(db_session)

    found_workspace = await WorkspaceRepository.get_by_id(
        workspace.id, session=db_session
    )
    assert found_workspace is not None
    assert found_workspace.id == workspace.id

    not_found_workspace = await WorkspaceRepository.get_by_id(
        uuid.uuid4(), session=db_session
    )
    assert not_found_workspace is None


@pytest.mark.asyncio
async def test_base_repository_update_by_id(db_session):
    """Test the 'update_by_id' method of the base repository."""
    workspace = await create_test_workspace(db_session)

    updated_workspace = await WorkspaceRepository.update_by_id(
        workspace.id, {"name": "Updated workspace name"}, session=db_session
    )

    assert updated_workspace is not None
    assert updated_workspace.id == workspace.id
    assert updated_workspace.name == "Updated workspace name"
    assert updated_workspace.created_at == workspace.created_at


@pytest.mark.asyncio
async def test_base_repository_delete(db_session):
    """Test the 'delete' method of the base repository."""
    workspace = await create_test_workspace(db_session)

    deleted_workspace = await WorkspaceRepository.delete(workspace, session=db_session)
    assert deleted_workspace is not None
    assert deleted_workspace.id == workspace.id

    found_workspace = await WorkspaceRepository.get_by_id(
        workspace.id, session=db_session
    )
    assert found_workspace is None


@pytest.mark.asyncio
async def test_base_repository_delete_by_id(db_session):
    """Test the 'delete_by_id' method of the base repository."""
    workspace = await create_test_workspace(db_session)

    deleted_workspace = await WorkspaceRepository.delete_by_id(
        workspace.id, session=db_session
    )
    assert deleted_workspace is not None
    assert deleted_workspace.id == workspace.id

    found_workspace = await WorkspaceRepository.get_by_id(
        workspace.id, session=db_session
    )
    assert found_workspace is None


@pytest.mark.asyncio
async def test_base_repository_refresh(db_session):
    """Test the 'refresh' method of the base repository."""
    workspace = await create_test_workspace(db_session)

    project1 = await create_test_project(db_session, workspace.id)

    _ = await WorkspaceRepository.refresh(
        workspace, session=db_session, relations=["projects"]
    )

    assert workspace.projects is not None
    assert len(workspace.projects) == 1
    assert project1 in workspace.projects

    project2 = await create_test_project(db_session, workspace.id)

    # Before refresh, the workspace should still have only the first project in its projects list
    assert workspace.projects is not None
    assert len(workspace.projects) == 1
    assert project2 not in workspace.projects

    _ = await WorkspaceRepository.refresh(
        workspace, session=db_session, relations=["projects"]
    )

    assert workspace.projects is not None
    assert len(workspace.projects) == 2
    assert project1 in workspace.projects
    assert project2 in workspace.projects

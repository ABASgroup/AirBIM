"""Tests for Project Service."""
import uuid

import pytest

from core.exceptions import NotFoundError
from schemas.project import ProjectModel, ProjectUpdate
from services.project import get_project, get_workspace_projects, create_project, update_project, delete_project

from tests.helpers import create_test_workspace, create_test_project


@pytest.mark.asyncio
async def test_create_project(db_session):
    """Service should create project."""
    workspace = await create_test_workspace(db_session)

    project_data = ProjectModel(
        name="Test Project",
        workspace_id=workspace.id,
        description="Test description"
    )
    project = await create_project(project_data, session=db_session)

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.workspace_id == workspace.id
    assert project.description == "Test description"


@pytest.mark.asyncio
async def test_get_project(db_session):
    """Service should return project by ID."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)

    fetched_project = await get_project(project.id, session=db_session)

    assert fetched_project.id == project.id
    assert fetched_project.name == project.name
    assert fetched_project.workspace_id == workspace.id
    assert fetched_project.description == project.description


@pytest.mark.asyncio
async def test_get_nonexistent_project(db_session):
    """Service should raise NotFoundError for non-existent project."""
    non_existent_id = uuid.uuid4()

    with pytest.raises(NotFoundError):
        await get_project(non_existent_id, session=db_session)


@pytest.mark.asyncio
async def test_get_workspace_projects(db_session):
    """Service should return all projects for workspace."""
    workspace = await create_test_workspace(db_session)
    project1 = await create_test_project(db_session, workspace_id=workspace.id)
    project2 = await create_test_project(db_session, workspace_id=workspace.id)

    projects = await get_workspace_projects(workspace.id, session=db_session)

    assert len(projects) == 2
    assert project1 in projects
    assert project2 in projects


@pytest.mark.asyncio
async def test_update_project(db_session):
    """Service should update project."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)

    update_data = ProjectUpdate(
        name="Updated Project", description="Updated description")
    updated_project = await update_project(project.id, update_data, session=db_session)

    assert updated_project.id == project.id
    assert updated_project.name == "Updated Project"
    assert updated_project.description == "Updated description"


@pytest.mark.asyncio
async def test_delete_project(db_session, storage):
    """Service should delete project."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)

    deleted_project = await delete_project(project.id, session=db_session, storage=storage)

    assert deleted_project.id == project.id

    with pytest.raises(NotFoundError):
        await get_project(project.id, session=db_session)

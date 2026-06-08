import pytest

from repositories.project import ProjectRepository
from schemas.project import ProjectModel
from tests.helpers import create_test_workspace


@pytest.mark.asyncio
async def test_project_repository_create_and_get_by_workspace_id(db_session):
    """Test creating a project and retrieving it by workspace ID."""
    # Create a workspace
    workspace = await create_test_workspace(db_session)

    # Create a project in the workspace
    project_data = ProjectModel(
        workspace_id=workspace.id,
        name="Test Project",
        description="A project for testing"
    ).model_dump(exclude_unset=True)
    created_project = await ProjectRepository.create(project_data, db_session)

    # Retrieve projects by workspace ID
    projects = await ProjectRepository.get_by_workspace_id(workspace.id, db_session)

    # Assertions
    assert len(projects) == 1
    assert projects[0].id == created_project.id
    assert projects[0].name == "Test Project"
    assert projects[0].description == "A project for testing"

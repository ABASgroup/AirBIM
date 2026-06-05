"""Tests for Stage Service."""
import pytest

from core.exceptions import NotFoundError
from schemas.stage import StageModel
from services.stage import get_stage, get_stage_with_project, get_project_stages, create_stage, delete_stage

from tests.helpers import create_test_workspace, create_test_project


@pytest.mark.asyncio
async def test_create_stage(db_session):
    """Service should create stage."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    stage_data = StageModel(
        project_id=project.id,
    )

    stage = await create_stage(stage_data, session=db_session)

    assert stage.id is not None
    assert stage.project_id == project.id


@pytest.mark.asyncio
async def test_get_stage(db_session):
    """Service should return stage by its ID."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    stage_data = StageModel(
        project_id=project.id,
    )
    stage = await create_stage(stage_data, session=db_session)

    retrieved_stage = await get_stage(stage.id, session=db_session)

    assert retrieved_stage is not None
    assert retrieved_stage.id == stage.id
    assert retrieved_stage.project_id == project.id


@pytest.mark.asyncio
async def test_get_stage_with_project(db_session):
    """Service should return stage with project by stage ID."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    stage_data = StageModel(
        project_id=project.id,
    )
    stage = await create_stage(stage_data, session=db_session)

    retrieved_stage = await get_stage_with_project(stage.id, session=db_session)

    assert retrieved_stage is not None
    assert retrieved_stage.id == stage.id
    assert retrieved_stage.project_id == project.id
    assert retrieved_stage.project is not None
    assert retrieved_stage.project.id == project.id


@pytest.mark.asyncio
async def test_get_project_stages(db_session):
    """Service should return all stages related to the project."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    stage_data = StageModel(
        project_id=project.id,
    )
    stage1 = await create_stage(stage_data, session=db_session)
    stage2 = await create_stage(stage_data, session=db_session)

    stages = await get_project_stages(project.id, session=db_session)

    assert len(stages) == 2
    assert stage1 in stages
    assert stage2 in stages


@pytest.mark.asyncio
async def test_get_project_stages_no_stages(db_session):
    """Service should raise NotFoundError if project doesn't have stages."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)

    with pytest.raises(NotFoundError):
        await get_project_stages(project.id, session=db_session)


@pytest.mark.asyncio
async def test_delete_stage(db_session, storage):
    """Service should delete stage."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    stage_data = StageModel(
        project_id=project.id,
    )
    stage = await create_stage(stage_data, session=db_session)

    deleted_stage = await delete_stage(stage.id, session=db_session, storage=storage)

    assert deleted_stage is not None
    assert deleted_stage.id == stage.id

    with pytest.raises(NotFoundError):
        await get_stage(stage.id, session=db_session)

    with pytest.raises(NotFoundError):
        await delete_stage(stage.id, session=db_session, storage=storage)

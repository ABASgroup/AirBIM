"""Tests for Stage Repository."""
from datetime import datetime, timezone
import uuid

import pytest

from repositories.stage import StageRepository
from schemas.stage import StageModel
from tests.helpers import create_test_workspace, create_test_project


@pytest.mark.asyncio
async def test_stage_repository_create_and_get_by_id(db_session):
    """Test stage creation and fetching by stage ID and project ID."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)

    test_data = datetime(2000, 1, 1, tzinfo=timezone.utc)
    stage_data = StageModel(
        project_id=project.id,
        start_date=test_data
    ).model_dump(exclude_unset=True)

    created_stage = await StageRepository.create(stage_data, session=db_session)
    assert created_stage.id is not None
    assert created_stage.project_id == project.id

    fetched_stage_by_id = await StageRepository.get_by_id_with_project(created_stage.id, session=db_session)
    assert fetched_stage_by_id is not None
    assert fetched_stage_by_id.id == created_stage.id
    assert fetched_stage_by_id.project is not None
    assert fetched_stage_by_id.project.id == project.id


@pytest.mark.asyncio
async def test_stage_repository_get_by_project_id(db_session):
    """Test fetching stages by project ID."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)

    test_data = datetime(2000, 1, 1, tzinfo=timezone.utc)
    stage_data = StageModel(
        project_id=project.id,
        start_date=test_data
    ).model_dump(exclude_unset=True)

    created_stage_1 = await StageRepository.create(stage_data, session=db_session)
    created_stage_2 = await StageRepository.create(stage_data, session=db_session)

    fetched_stages = await StageRepository.get_by_project_id(project.id, session=db_session)
    assert len(fetched_stages) == 2
    for stage in (created_stage_1, created_stage_2):
        assert any(fetched_stage.id ==
                   stage.id for fetched_stage in fetched_stages)


@pytest.mark.asyncio
async def test_stage_repository_get_by_id_with_project_nonexistent(db_session):
    """Test fetching stage by ID that does not exist."""
    fetched_stage = await StageRepository.get_by_id_with_project(
        stage_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        session=db_session,
    )
    assert fetched_stage is None

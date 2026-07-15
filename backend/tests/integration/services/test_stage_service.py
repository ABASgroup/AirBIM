"""Tests for Stage Service."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError

from infrastructure.storage import Storage

from schemas.stage import StageModel

from services.stage import StageService
from tests.helpers import create_test_project, create_test_workspace


@pytest.mark.asyncio
async def test_create_stage(db_session: AsyncSession) -> None:
    """Service should create stage."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    test_data = datetime(2000, 1, 1, tzinfo=timezone.utc)
    stage_data = StageModel(project_id=project.id, start_date=test_data)

    stage = await StageService.create_stage(stage_data, session=db_session)

    assert stage.id is not None
    assert stage.project_id == project.id


@pytest.mark.asyncio
async def test_get_stage(db_session: AsyncSession) -> None:
    """Service should return stage by its ID."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    test_data = datetime(2000, 1, 1, tzinfo=timezone.utc)
    stage_data = StageModel(project_id=project.id, start_date=test_data)
    stage = await StageService.create_stage(stage_data, session=db_session)

    retrieved_stage = await StageService.get_stage(stage.id, session=db_session)

    assert retrieved_stage is not None
    assert retrieved_stage.id == stage.id
    assert retrieved_stage.project_id == project.id


@pytest.mark.asyncio
async def test_get_project_stages(db_session: AsyncSession) -> None:
    """Service should return all stages related to the project."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    test_data = datetime(2000, 1, 1, tzinfo=timezone.utc)
    stage_data = StageModel(project_id=project.id, start_date=test_data)
    stage1 = await StageService.create_stage(stage_data, session=db_session)
    stage2 = await StageService.create_stage(stage_data, session=db_session)

    stages = await StageService.get_project_stages(project.id, session=db_session)

    assert len(stages) == 2
    assert stage1 in stages
    assert stage2 in stages


@pytest.mark.asyncio
async def test_get_project_stages_no_stages(db_session: AsyncSession) -> None:
    """Service should raise NotFoundError if project doesn't have stages."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    stages = await StageService.get_project_stages(project.id, session=db_session)
    assert len(stages) == 0


@pytest.mark.asyncio
async def test_delete_stage(db_session: AsyncSession, storage: Storage) -> None:
    """Service should delete stage."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    test_data = datetime(2000, 1, 1, tzinfo=timezone.utc)
    stage_data = StageModel(project_id=project.id, start_date=test_data)
    stage = await StageService.create_stage(stage_data, session=db_session)

    deleted_stage = await StageService.delete_stage(stage.id, session=db_session)

    assert deleted_stage is not None
    assert deleted_stage.id == stage.id

    with pytest.raises(NotFoundError):
        await StageService.get_stage(stage.id, session=db_session)

    with pytest.raises(NotFoundError):
        await StageService.delete_stage(stage.id, session=db_session)

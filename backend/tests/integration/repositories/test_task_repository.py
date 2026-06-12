"""Tests for Task Repository."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.task import TaskRepository

from schemas.task import TaskModel, TaskType

from tests.helpers import create_test_workspace


@pytest.mark.asyncio
async def test_task_repository_create(db_session: AsyncSession) -> None:
    """Test task creation."""
    workspace = await create_test_workspace(db_session)
    task = await TaskRepository.create(
        TaskModel(
            entity_id=uuid.uuid4(),
            entity_type="test_entity",
            workspace_id=workspace.id,
            type=TaskType.CHECKING_PROGRESS,
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    assert task.id is not None
    assert task.entity_type == "test_entity"
    assert task.type == TaskType.CHECKING_PROGRESS

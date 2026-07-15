"""Tests for Task Service."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError

from schemas.task import TaskModel, TaskStatus, TaskType

from services.task import TaskService

from tests.helpers import create_test_workspace


@pytest.mark.asyncio
async def test_create_task(db_session: AsyncSession) -> None:
    """Service should create task."""
    workspace = await create_test_workspace(db_session)
    task_data = TaskModel(
        entity_id=uuid.uuid4(),
        entity_type="test_entity",
        workspace_id=workspace.id,
        type=TaskType.CHECKING_PROGRESS,
    )

    task = await TaskService.create_task(task_data, session=db_session)

    assert task.id is not None
    assert task.entity_id == task_data.entity_id
    assert task.entity_type == task_data.entity_type
    assert task.type == task_data.type


@pytest.mark.asyncio
async def test_start_task(db_session: AsyncSession) -> None:
    """Service should start task."""
    workspace = await create_test_workspace(db_session)
    task_data = TaskModel(
        entity_id=uuid.uuid4(),
        entity_type="test_entity",
        workspace_id=workspace.id,
        type=TaskType.CHECKING_PROGRESS,
    )

    task = await TaskService.create_task(task_data, session=db_session)

    started_task = await TaskService.start_task(
        task.id, session=db_session
    )

    assert started_task.status == TaskStatus.STARTED


@pytest.mark.asyncio
async def test_get_task(db_session: AsyncSession) -> None:
    """Service should return task by its ID."""
    workspace = await create_test_workspace(db_session)
    task_data = TaskModel(
        entity_id=uuid.uuid4(),
        entity_type="test_entity",
        workspace_id=workspace.id,
        type=TaskType.CHECKING_PROGRESS,
    )

    task = await TaskService.create_task(task_data, session=db_session)

    retrieved_task = await TaskService.get_task(task.id, session=db_session)

    assert retrieved_task is not None
    assert retrieved_task.id == task.id
    assert retrieved_task.entity_id == task.entity_id
    assert retrieved_task.entity_type == task.entity_type
    assert retrieved_task.type == task.type


@pytest.mark.asyncio
async def test_get_nonexistent_task(db_session: AsyncSession) -> None:
    """Service should raise NotFoundError if task does not exist."""
    non_existent_task_id = uuid.uuid4()

    with pytest.raises(NotFoundError):
        await TaskService.get_task(non_existent_task_id, session=db_session)


@pytest.mark.asyncio
async def test_update_task_progress(db_session: AsyncSession) -> None:
    """Service should update task progress."""
    workspace = await create_test_workspace(db_session)
    task_data = TaskModel(
        entity_id=uuid.uuid4(),
        entity_type="test_entity",
        workspace_id=workspace.id,
        type=TaskType.CHECKING_PROGRESS,
    )

    task = await TaskService.create_task(task_data, session=db_session)
    assert task.progress == 0

    task = await TaskService.update_task_progress(
        task.id, progress=50, session=db_session
    )
    assert task.progress == 50


@pytest.mark.asyncio
async def test_update_task_status(db_session: AsyncSession) -> None:
    """Service should update task status."""
    workspace = await create_test_workspace(db_session)
    task_data = TaskModel(
        entity_id=uuid.uuid4(),
        entity_type="test_entity",
        workspace_id=workspace.id,
        type=TaskType.CHECKING_PROGRESS,
        status=TaskStatus.PENDING,
    )

    task = await TaskService.create_task(task_data, session=db_session)
    assert task.status == TaskStatus.PENDING

    task = await TaskService.update_task_status(
        task.id, status=TaskStatus.SUCCEEDED, session=db_session
    )
    assert task.status == TaskStatus.SUCCEEDED

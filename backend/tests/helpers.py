"""Shared helper functions for unit, integration and API tests."""

import asyncio
from collections.abc import Callable, Coroutine
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import Role

from models.file import BIM, File, PointCloud
from models.membership import Membership
from models.project import Project
from models.recording_result import RecordingResult
from models.stage import Stage
from models.task import Task
from models.user import User
from models.workspace import Workspace

from repositories.files import BIMRepository, FileRepository, PointCloudRepository
from repositories.membership import MembershipRepository
from repositories.project import ProjectRepository
from repositories.recording_result import RecordingResultRepository
from repositories.stage import StageRepository
from repositories.task import TaskRepository
from repositories.user import UserRepository
from repositories.workspace import WorkspaceRepository

from schemas.file import BIMModel, FileModel, PointCloudModel
from schemas.membership import MembershipModel
from schemas.project import ProjectModel
from schemas.recording_result import RecordingResultModel, RecordingResultType
from schemas.stage import StageModel
from schemas.task import TaskModel, TaskType
from schemas.user import UserModel
from schemas.workspace import WorkspaceModel, WorkspaceType

from services.file import FileService


async def create_test_workspace(
    db_session: AsyncSession,
    workspace_type: WorkspaceType = WorkspaceType.TEAM,
) -> Workspace:
    """Create workspace required by files.workspace_id foreign key."""
    return await WorkspaceRepository.create(
        WorkspaceModel(
            name="Repository files workspace", type=workspace_type
        ).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_project(db_session: AsyncSession, workspace_id: UUID) -> Project:
    """Create project required by BIM.project_id foreign key."""
    return await ProjectRepository.create(
        ProjectModel(
            name="Repository files project",
            description="Project for testing files repository",
            workspace_id=workspace_id,
        ).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_stage(
    db_session: AsyncSession,
    project_id: UUID,
    start_date: AwareDatetime = datetime(2000, 1, 1, tzinfo=timezone.utc),
) -> Stage:
    """Create stage required by File.stage_id foreign key."""
    return await StageRepository.create(
        StageModel(project_id=project_id, start_date=start_date).model_dump(
            exclude_unset=True
        ),
        session=db_session,
    )


async def create_test_file(
    db_session: AsyncSession,
    workspace_id: UUID,
    file_path: Path,
) -> File:
    """Create file required by PointCloud.file_id foreign key."""
    return await FileRepository.create(
        FileModel(
            workspace_id=workspace_id,
            **FileService.collect_file_data(file_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_point_cloud(
    db_session: AsyncSession, file_id: UUID
) -> PointCloud:
    """Create point cloud required by RecordingResult.point_cloud_id foreign key."""
    return await PointCloudRepository.create(
        PointCloudModel(file_id=file_id).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_bim(
    db_session: AsyncSession,
    project_id: UUID,
    file_id: UUID,
) -> BIM:
    """Create bim required by RecordingResult.bim foreign key."""
    return await BIMRepository.create(
        BIMModel(project_id=project_id, file_id=file_id).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_user(
    db_session: AsyncSession,
    email: str = "test@test.com",
    username: str = "testuser",
    password_hashed: str = "hashed-password",
) -> User:
    """Create a user for testing."""
    return await UserRepository.create(
        UserModel(
            email=email,
            username=username,
            password_hashed=password_hashed,
        ).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_membership(
    db_session: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
    role: Role,
) -> Membership:
    """Create a membership for testing."""
    return await MembershipRepository.create(
        MembershipModel(
            workspace_id=workspace_id, user_id=user_id, role=role
        ).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_recording_result(
    db_session: AsyncSession,
    project_id: UUID,
    point_cloud_id: UUID,
    data: dict[str, Any],
    recording_type: RecordingResultType = RecordingResultType.PROGRESS,
) -> RecordingResult:
    """Create a recording result for testing."""
    return await RecordingResultRepository.create(
        RecordingResultModel(
            project_id=project_id,
            point_cloud_id=point_cloud_id,
            data=data,
            type=recording_type,
        ).model_dump(exclude_unset=True),
        db_session,
    )


async def create_test_task(
    db_session: AsyncSession,
    workspace_id: UUID,
    entity_id: UUID,
    task_type: TaskType,
) -> Task:
    """Create a celery task for testing."""
    return await TaskRepository.create(
        TaskModel(
            entity_id=entity_id,
            entity_type="test",
            workspace_id=workspace_id,
            type=task_type,
        ).model_dump(exclude_unset=True),
        db_session,
    )


async def wait_until(
    assertion: Callable[[], Coroutine[Any, Any, None]],
    timeout: float = 30.0,
    interval: float = 0.5,
) -> None:
    """Poll async assertion until it succeeds or timeout expires."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    last_error: AssertionError | None = None

    while loop.time() < deadline:
        try:
            await assertion()
            return
        except AssertionError as exc:
            last_error = exc
            await asyncio.sleep(interval)

    if last_error is not None:
        raise last_error
    raise AssertionError("Condition was not satisfied before timeout")

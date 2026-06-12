"""Shared helpers specifically for API integration tests."""

import asyncio
from collections.abc import Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import InviteableRole, Permission, Role, get_role_permissions

from infrastructure.storage import Storage

from models.file import File, PointCloud
from models.project import Project
from models.recording_result import RecordingResult
from models.stage import Stage

from repositories.files import PointCloudRepository

from schemas.file import FileModel, PointCloudModel
from schemas.recording_result import RecordingResultType
from schemas.workspace import WorkspaceType

from services.file import FileService
from services.recording_result import RecordingResultService

from tests.helpers import (
    create_test_file,
    create_test_point_cloud,
    create_test_project,
    create_test_recording_result,
    create_test_stage,
)


def role_has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_role_permissions(role)


async def gather_responses(
    awaitables: list[Coroutine[Any, Any, Response]],
) -> list[Response]:
    """Gather responses from a list of awaitables."""
    return await asyncio.gather(*awaitables)


@dataclass(frozen=True)
class RegisteredUser:
    """User created through the public registration API."""

    access_token: str
    username: str
    email: str

    @property
    def headers(self) -> dict[str, str]:
        """Get headers for authentication."""
        return {"Authorization": f"Bearer {self.access_token}"}


async def register_user_via_api(
    api_client: AsyncClient,
    *,
    username: str | None = None,
    email: str | None = None,
    password: str = "super-secret",
    workspace_name: str = "Personal Workspace",
) -> RegisteredUser:
    """Register a user and return auth data from the API response."""
    suffix = uuid4().hex[:8]
    resolved_username = username or f"api-user-{suffix}"
    resolved_email = email or f"api-user-{suffix}@example.com"

    response = await api_client.post(
        "/auth/register",
        json={
            "username": resolved_username,
            "email": resolved_email,
            "password": password,
            "workspace_name": workspace_name,
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return RegisteredUser(
        access_token=token,
        username=resolved_username,
        email=resolved_email,
    )


async def get_user_workspaces_via_api(
    api_client: AsyncClient,
    headers: dict[str, str],
) -> list[dict[str, Any]]:
    """Get the user's workspaces through the API."""
    response = await api_client.get("/workspaces/my", headers=headers)
    assert response.status_code == 200
    return response.json()


async def get_personal_workspace_via_api(
    api_client: AsyncClient,
    headers: dict[str, str],
) -> dict[str, Any]:
    """Get the user's personal workspace through the API."""
    workspaces = await get_user_workspaces_via_api(api_client, headers)
    personal_workspaces = [
        workspace
        for workspace in workspaces
        if workspace["type"] == WorkspaceType.PERSONAL.value
    ]
    assert len(personal_workspaces) == 1
    return personal_workspaces[0]


async def create_team_workspace_via_api(
    api_client: AsyncClient,
    headers: dict[str, str],
    name: str = "Team Workspace",
) -> dict[str, Any]:
    """Create a team workspace through the API and return the response body."""
    response = await api_client.post(
        "/workspaces",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


async def create_project_via_api(
    api_client: AsyncClient,
    workspace_id: UUID,
    headers: dict[str, str],
    *,
    name: str = "API Test Project",
    description: str = "Project created via workspace API",
) -> dict[str, Any]:
    """Create a project in the specified workspace through the API."""
    response = await api_client.post(
        f"/workspaces/{workspace_id}/projects",
        json={"name": name, "description": description},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


async def setup_project_in_workspace(
    db_session: AsyncSession,
    workspace_id: UUID,
) -> Project:
    """Create a project and auto commit it to the database."""
    project = await create_test_project(db_session, workspace_id)
    await db_session.commit()
    return project


async def setup_stage_in_project(
    db_session: AsyncSession,
    project_id: UUID,
    **stage_kwargs: Any,
) -> Stage:
    """Create a stage and auto commit it to the database."""
    stage = await create_test_stage(db_session, project_id, **stage_kwargs)
    await db_session.commit()
    return stage


async def setup_recording_result_in_project(
    db_session: AsyncSession,
    workspace_id: UUID,
    project_id: UUID,
    point_cloud_file_path: Path,
    *,
    data: dict[str, Any] | None = None,
    recording_type: RecordingResultType = RecordingResultType.PLAN_FACT,
) -> RecordingResult:
    """Create a recording result with an associated point cloud."""
    file = await create_test_file(db_session, workspace_id, point_cloud_file_path)
    point_cloud = await create_test_point_cloud(db_session, file.id)
    recording_result = await create_test_recording_result(
        db_session,
        project_id,
        point_cloud.id,
        data or {"example": "data"},
        recording_type,
    )
    await db_session.commit()
    return recording_result


async def setup_recording_result_with_reports(
    db_session: AsyncSession,
    workspace_id: UUID,
    project_id: UUID,
    point_cloud_file_path: Path,
    xlsx_file_path: Path,
    pdf_file_path: Path,
) -> RecordingResult:
    """Create a recording result with excel and pdf reports attached."""
    recording_result = await setup_recording_result_in_project(
        db_session,
        workspace_id,
        project_id,
        point_cloud_file_path,
    )
    await RecordingResultService.create_excel_report(
        recording_result.id,
        FileModel(
            workspace_id=workspace_id,
            **FileService.collect_file_data(xlsx_file_path),
        ),
        session=db_session,
    )
    await RecordingResultService.create_pdf_report(
        recording_result.id,
        FileModel(
            workspace_id=workspace_id,
            **FileService.collect_file_data(pdf_file_path),
        ),
        session=db_session,
    )
    await db_session.commit()
    return recording_result


async def create_invite_link_via_api(
    api_client: AsyncClient,
    workspace_id: UUID,
    headers: dict[str, str],
    role: InviteableRole = InviteableRole.MEMBER,
) -> dict[str, Any]:
    """Create invite link through workspace API and return response body."""
    response = await api_client.post(
        f"/workspaces/{workspace_id}/invites",
        json={"role": role.value},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


async def setup_pending_file_in_storage(
    db_session: AsyncSession,
    storage: Storage,
    workspace_id: UUID,
    file_path: Path,
) -> File:
    """Create a file record with pending status, upload the file to storage and commit it."""
    file = await create_test_file(db_session, workspace_id, file_path)
    with file_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, file.key)
    await db_session.commit()
    return file


async def setup_point_cloud_with_stage(
    db_session: AsyncSession,
    workspace_id: UUID,
    file_path: Path,
) -> tuple[PointCloud, File]:
    """Create and auto commit a stage, file and point cloud linked to that file."""
    project = await create_test_project(db_session, workspace_id)
    stage = await create_test_stage(db_session, project.id)
    file = await create_test_file(db_session, workspace_id, file_path)
    point_cloud = await PointCloudRepository.create(
        PointCloudModel(file_id=file.id, stage_id=stage.id).model_dump(
            exclude_unset=True
        ),
        session=db_session,
    )
    await db_session.commit()
    return point_cloud, file


async def setup_point_cloud_with_converted_file(
    db_session: AsyncSession,
    storage: Storage,
    workspace_id: UUID,
    point_cloud_file_path: Path,
    converted_file_path: Path,
) -> tuple[PointCloud, File]:
    """Create and auto commit a stage, file and point cloud linked to that file,
    then save converted file for that point cloud."""
    point_cloud, _ = await setup_point_cloud_with_stage(
        db_session, workspace_id, point_cloud_file_path
    )
    await FileService.save_converted_point_cloud_file(
        point_cloud.id,
        FileModel(
            workspace_id=workspace_id,
            **FileService.collect_file_data(converted_file_path),
        ),
        session=db_session,
    )
    converted_files = await FileService.get_converted_point_cloud_files(
        point_cloud.id, session=db_session
    )
    converted_file = converted_files[0]
    with converted_file_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, converted_file.key)
    await db_session.commit()
    return point_cloud, converted_file

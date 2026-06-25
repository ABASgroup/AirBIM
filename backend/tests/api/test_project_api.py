"""API integration tests for project endpoints."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import Permission, Role
from core.security import create_access_token

from infrastructure.database import session_maker
from infrastructure.storage import Storage

from repositories.project import ProjectRepository

from schemas.file import FileStatus, PointCloudType
from schemas.project import ProjectStatus
from schemas.recording_result import RecordingResultType
from schemas.task import TaskType

from services.file import FileService
from services.recording_result import RecordingResultService

from tests.api.conftest import AuthContext
from tests.api.helpers import (
    gather_responses,
    role_has_permission,
    setup_project_in_workspace,
)
from tests.helpers import (
    create_test_bim,
    create_test_file,
    create_test_membership,
    create_test_point_cloud,
    create_test_stage,
    create_test_user,
    create_test_workspace,
    wait_until,
)


STAGE_PAYLOAD = {
    "name": "Foundation",
    "description": "Ground works",
    "start_date": "2000-01-01T00:00:00+00:00",
}

LATER_STAGE_PAYLOAD = {
    "name": "Structure",
    "description": "Main structure",
    "start_date": "2000-06-01T00:00:00+00:00",
}


# ---------------------------------------------------------------------------
# Role-based access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_project_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /projects/{id} should require PROJECT_VIEW permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )

    response = await api_client.get(
        f"/projects/{project.id}",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.PROJECT_VIEW):
        assert response.status_code == 200
        assert response.json()["id"] == str(project.id)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_project_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
) -> None:
    """PATCH /projects/{id} should require PROJECT_EDIT permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )

    response = await api_client.patch(
        f"/projects/{project.id}",
        json={"name": "Updated name"},
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.PROJECT_EDIT):
        assert response.status_code == 200
        assert response.json()["name"] == "Updated name"
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_project_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
) -> None:
    """DELETE /projects/{id} should require PROJECT_DELETE permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )

    response = await api_client.delete(
        f"/projects/{project.id}",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.PROJECT_DELETE):
        assert response.status_code == 200
        assert response.json()["id"] == str(project.id)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_stages_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /projects/{id}/stages should require STAGE_VIEW permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )

    response = await api_client.get(
        f"/projects/{project.id}/stages",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.STAGE_VIEW):
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_stage_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
) -> None:
    """POST /projects/{id}/stages should require STAGE_CREATE permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )

    response = await api_client.post(
        f"/projects/{project.id}/stages",
        json=STAGE_PAYLOAD,
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.STAGE_CREATE):
        assert response.status_code == 200
        assert response.json()["project_id"] == str(project.id)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_bim_upload_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    test_building_ifc_path: Path,
) -> None:
    """POST /projects/{id}/bim/upload should require FILES_UPLOAD permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    file_meta = FileService.collect_file_data(test_building_ifc_path)

    response = await api_client.post(
        f"/projects/{project.id}/bim/upload",
        json={
            "filename": file_meta["filename"],
            "content_type": file_meta["content_type"],
            "size": file_meta["size"],
        },
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.FILES_UPLOAD):
        assert response.status_code == 200
        assert response.json()["file"]["status"] == FileStatus.PENDING.value
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_bim_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    test_building_ifc_path: Path,
) -> None:
    """GET /projects/{id}/bim should require FILES_VIEW permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    file = await create_test_file(
        db_session, auth_context_with_role.workspace_id, test_building_ifc_path
    )
    await create_test_bim(db_session, project.id, file.id)
    await db_session.commit()

    response = await api_client.get(
        f"/projects/{project.id}/bim",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.FILES_VIEW):
        assert response.status_code == 200
        assert response.json()["project_id"] == str(project.id)
    else:
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Functional tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_project_returns_project_data(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /projects/{id} should return project metadata."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)

    response = await api_client.get(
        f"/projects/{project.id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(project.id)
    assert body["workspace_id"] == str(auth_context.workspace_id)
    assert body["name"] == project.name
    assert body["status"] == ProjectStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_update_project_updates_fields(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """PATCH /projects/{id} should persist updated project fields."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    project_id = project.id

    response = await api_client.patch(
        f"/projects/{project_id}",
        json={
            "name": "Renamed project",
            "description": "Updated description",
        },
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed project"
    assert body["description"] == "Updated description"

    db_session.expire_all()
    saved_project = await ProjectRepository.get_by_id(project_id, session=db_session)
    assert saved_project is not None
    assert saved_project.name == "Renamed project"


@pytest.mark.asyncio
async def test_delete_project_removes_project(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """DELETE /projects/{id} should remove the project record."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    project_id = project.id

    response = await api_client.delete(
        f"/projects/{project_id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(project_id)

    get_response = await api_client.get(
        f"/projects/{project_id}",
        headers=auth_context.headers,
    )
    assert get_response.status_code == 404

    db_session.expire_all()
    assert await ProjectRepository.get_by_id(project_id, session=db_session) is None


@pytest.mark.asyncio
async def test_get_stages_returns_empty_list_for_new_project(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /projects/{id}/stages should return an empty list when no stages exist."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)

    response = await api_client.get(
        f"/projects/{project.id}/stages",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_stage_adds_stage_to_project(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """POST /projects/{id}/stages should create a stage linked to the project."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)

    response = await api_client.post(
        f"/projects/{project.id}/stages",
        json=STAGE_PAYLOAD,
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == str(project.id)
    assert body["name"] == STAGE_PAYLOAD["name"]
    assert body["description"] == STAGE_PAYLOAD["description"]

    list_response = await api_client.get(
        f"/projects/{project.id}/stages",
        headers=auth_context.headers,
    )
    stages = list_response.json()
    assert len(stages) == 1
    assert stages[0]["id"] == body["id"]


@pytest.mark.asyncio
async def test_bim_upload_returns_presigned_url_and_pending_file(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_ifc_path: Path,
) -> None:
    """POST /projects/{id}/bim/upload should create a pending file and upload URL."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    file_meta = FileService.collect_file_data(test_building_ifc_path)

    response = await api_client.post(
        f"/projects/{project.id}/bim/upload",
        json={
            "filename": file_meta["filename"],
            "content_type": file_meta["content_type"],
            "size": file_meta["size"],
        },
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["file"]["status"] == FileStatus.PENDING.value
    assert body["file"]["workspace_id"] == str(auth_context.workspace_id)
    assert isinstance(body["url"], str)
    assert body["url"].startswith("http")


@pytest.mark.asyncio
async def test_get_bim_returns_bim_metadata(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_ifc_path: Path,
) -> None:
    """GET /projects/{id}/bim should return BIM metadata with nested file."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    file = await create_test_file(
        db_session, auth_context.workspace_id, test_building_ifc_path
    )
    bim = await create_test_bim(db_session, project.id, file.id)
    await db_session.commit()

    response = await api_client.get(
        f"/projects/{project.id}/bim",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(bim.id)
    assert body["project_id"] == str(project.id)
    assert body["file"]["id"] == str(file.id)
    assert body["file"]["filename"] == file.filename


@pytest.mark.asyncio
async def test_get_results_returns_empty_list_for_new_project(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /projects/{id}/results should return an empty list when no results exist."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)

    response = await api_client.get(
        f"/projects/{project.id}/results",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_check_stage_progress(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_building_shifted_laz_path: Path,
    storage: Storage,
) -> None:
    """POST /projects/{id}/stages/progress should run task and complete it"""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    stage_before = await create_test_stage(
        db_session, project.id, datetime(2000, 1, 1, tzinfo=timezone.utc)
    )
    file_before = await create_test_file(
        db_session, auth_context.workspace_id, test_building_laz_path
    )
    point_cloud_before = await create_test_point_cloud(db_session, file_before.id)
    point_cloud_before.stage_id = stage_before.id
    point_cloud_before.type = PointCloudType.SCAN
    file_before.key = FileService.create_file_key(test_building_laz_path.name)
    storage.upload_file_locally(file_before.key, str(test_building_laz_path))

    stage_after = await create_test_stage(
        db_session, project.id, datetime(2000, 1, 1, tzinfo=timezone.utc)
    )
    file_after = await create_test_file(
        db_session, auth_context.workspace_id, test_building_shifted_laz_path
    )
    point_cloud_after = await create_test_point_cloud(db_session, file_after.id)
    point_cloud_after.stage_id = stage_after.id
    point_cloud_after.type = PointCloudType.SCAN
    file_after.key = FileService.create_file_key(test_building_shifted_laz_path.name)
    storage.upload_file_locally(file_after.key, str(test_building_shifted_laz_path))

    await db_session.commit()

    response = await api_client.post(
        f"/projects/{project.id}/stages/progress",
        params={
            "stage_1_id": str(stage_before.id),
            "stage_2_id": str(stage_after.id),
            "tolerance": 0.05,
        },
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == TaskType.CHECKING_PROGRESS.value
    assert body["entity_id"] == str(project.id)
    assert body["workspace_id"] == str(auth_context.workspace_id)

    async def assert_scan_and_plan_comparison_generated() -> None:
        async with session_maker() as session:
            recording_result = (
                await RecordingResultService.get_recording_results_for_project(
                    project.id, session
                )
            )
            assert len(recording_result) != 0
            assert recording_result[0].point_cloud_id is not None
            assert recording_result[0].type == RecordingResultType.PROGRESS

            result_point_cloud = await FileService.get_point_cloud(
                recording_result[0].point_cloud_id, db_session
            )
            assert result_point_cloud.type == PointCloudType.RECORDING
            assert result_point_cloud.file_id is not None
            assert result_point_cloud.file.key is not None
            assert result_point_cloud.file.filename.endswith(".laz")
            assert result_point_cloud.file.size > 0
            assert storage.file_exists(result_point_cloud.file.key)

    await wait_until(assert_scan_and_plan_comparison_generated)


@pytest.mark.asyncio
async def test_project_endpoints_return_401_without_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
    test_building_ifc_path: Path,
) -> None:
    """Protected project endpoints should reject unauthenticated requests."""
    workspace = await create_test_workspace(db_session)
    project = await setup_project_in_workspace(db_session, workspace.id)
    file_meta = FileService.collect_file_data(test_building_ifc_path)

    protected_requests = [
        api_client.get(f"/projects/{project.id}"),
        api_client.patch(f"/projects/{project.id}", json={"name": "x"}),
        api_client.delete(f"/projects/{project.id}"),
        api_client.get(f"/projects/{project.id}/stages"),
        api_client.post(f"/projects/{project.id}/stages", json=STAGE_PAYLOAD),
        api_client.post(
            f"/projects/{project.id}/bim/upload",
            json={
                "filename": file_meta["filename"],
                "content_type": file_meta["content_type"],
                "size": file_meta["size"],
            },
        ),
        api_client.get(f"/projects/{project.id}/bim"),
        api_client.get(f"/projects/{project.id}/results"),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_project_endpoints_return_403_for_non_member(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Protected project endpoints should reject users outside the project workspace."""
    owner_workspace = await create_test_workspace(db_session)
    project = await setup_project_in_workspace(db_session, owner_workspace.id)

    other_workspace = await create_test_workspace(db_session)
    outsider = await create_test_user(
        db_session,
        email="project-outsider@example.com",
        username="project-outsider",
    )
    await create_test_membership(
        db_session, other_workspace.id, outsider.id, Role.OWNER
    )
    await db_session.commit()

    outsider_headers = {"Authorization": f"Bearer {create_access_token(outsider.id)}"}

    protected_requests = [
        api_client.get(f"/projects/{project.id}", headers=outsider_headers),
        api_client.patch(
            f"/projects/{project.id}", json={"name": "x"}, headers=outsider_headers
        ),
        api_client.delete(f"/projects/{project.id}", headers=outsider_headers),
        api_client.get(f"/projects/{project.id}/stages", headers=outsider_headers),
        api_client.post(
            f"/projects/{project.id}/stages",
            json=STAGE_PAYLOAD,
            headers=outsider_headers,
        ),
        api_client.post(
            f"/projects/{project.id}/bim/upload",
            json={"test": "test"},
            headers=outsider_headers,
        ),
        api_client.get(f"/projects/{project.id}/bim", headers=outsider_headers),
        api_client.get(f"/projects/{project.id}/results", headers=outsider_headers),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_project_endpoints_returns_404_for_unknown_id(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Protected project endpoints should return 404 for a non-existent project."""

    protected_requests = [
        api_client.get(f"/projects/{uuid4()}", headers=auth_context.headers),
        api_client.patch(
            f"/projects/{uuid4()}", json={"name": "x"}, headers=auth_context.headers
        ),
        api_client.delete(f"/projects/{uuid4()}", headers=auth_context.headers),
        api_client.get(f"/projects/{uuid4()}/stages", headers=auth_context.headers),
        api_client.post(
            f"/projects/{uuid4()}/stages",
            json=STAGE_PAYLOAD,
            headers=auth_context.headers,
        ),
        api_client.post(
            f"/projects/{uuid4()}/bim/upload",
            json={"test": "test"},
            headers=auth_context.headers,
        ),
        api_client.get(f"/projects/{uuid4()}/bim", headers=auth_context.headers),
        api_client.get(f"/projects/{uuid4()}/results", headers=auth_context.headers),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 404

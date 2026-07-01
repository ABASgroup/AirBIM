"""API integration tests for stage endpoints."""

from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import Permission, Role
from core.security import create_access_token

from infrastructure.database import session_maker
from infrastructure.storage import Storage

from repositories.stage import StageRepository

from schemas.file import FileStatus, PointCloudType
from schemas.recording_result import RecordingResultType
from schemas.task import TaskStatus, TaskType

from services.file import BIMRepository, FileService
from services.recording_result import RecordingResultService
from services.task import TaskService

from tests.api.conftest import AuthContext
from tests.api.helpers import (
    gather_responses,
    role_has_permission,
    setup_project_in_workspace,
    setup_stage_in_project,
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


# ---------------------------------------------------------------------------
# Role-based access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_stage_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /stages/{id} should require STAGE_VIEW permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    stage = await setup_stage_in_project(db_session, project.id)

    response = await api_client.get(
        f"/stages/{stage.id}",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.STAGE_VIEW):
        assert response.status_code == 200
        assert response.json()["id"] == str(stage.id)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_stage_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
) -> None:
    """DELETE /stages/{id} should require STAGE_DELETE permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    stage = await setup_stage_in_project(db_session, project.id)

    response = await api_client.delete(
        f"/stages/{stage.id}",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.STAGE_DELETE):
        assert response.status_code == 200
        assert response.json()["id"] == str(stage.id)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_point_cloud_upload_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """POST /stages/{id}/clouds/upload should require FILES_UPLOAD permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    stage = await setup_stage_in_project(db_session, project.id)
    file_meta = FileService.collect_file_data(test_building_laz_path)

    response = await api_client.post(
        f"/stages/{stage.id}/clouds/upload",
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


# ---------------------------------------------------------------------------
# Functional tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_stage_returns_stage_data(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """GET /stages/{id} should return stage metadata."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    stage = await setup_stage_in_project(db_session, project.id)

    response = await api_client.get(
        f"/stages/{stage.id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(stage.id)
    assert body["project_id"] == str(project.id)
    assert body["point_cloud_id"] is None


@pytest.mark.asyncio
async def test_delete_stage_removes_stage(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
) -> None:
    """DELETE /stages/{id} should remove the stage record."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    stage = await setup_stage_in_project(db_session, project.id)
    stage_id = stage.id

    response = await api_client.delete(
        f"/stages/{stage_id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(stage_id)

    get_response = await api_client.get(
        f"/stages/{stage_id}",
        headers=auth_context.headers,
    )
    assert get_response.status_code == 404

    db_session.expire_all()
    assert await StageRepository.get_by_id(stage_id, session=db_session) is None


@pytest.mark.asyncio
async def test_point_cloud_upload_returns_presigned_url_and_pending_file(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """POST /stages/{id}/clouds/upload should create pending file and upload URL."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    stage = await setup_stage_in_project(db_session, project.id)
    file_meta = FileService.collect_file_data(test_building_laz_path)

    response = await api_client.post(
        f"/stages/{stage.id}/clouds/upload",
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
async def test_compare_stage_scan_and_plan(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_laz_path: Path,
    test_building_shifted_laz_path: Path,
) -> None:
    """POST /stages/{id}/compare should do plan-fact comparison task."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    file_plan = await create_test_file(
        db_session, auth_context.workspace_id, test_building_laz_path
    )

    bim = await create_test_bim(db_session, project.id, file_plan.id)
    point_cloud_plan = await create_test_point_cloud(db_session, file_plan.id)
    bim = await BIMRepository.set_point_cloud(bim, point_cloud_plan.id, db_session)
    point_cloud_plan.type = PointCloudType.PLAN
    file_plan.key = FileService.create_file_key(test_building_laz_path.name)

    await db_session.commit()
    storage.upload_file_locally(file_plan.key, str(test_building_laz_path))

    stage = await create_test_stage(db_session, project.id)
    file_scan = await create_test_file(
        db_session, auth_context.workspace_id, test_building_shifted_laz_path
    )
    point_cloud_scan = await create_test_point_cloud(db_session, file_scan.id)
    point_cloud_scan.stage_id = stage.id
    point_cloud_scan.type = PointCloudType.SCAN
    file_scan.key = FileService.create_file_key(test_building_shifted_laz_path.name)

    await db_session.commit()
    storage.upload_file_locally(file_scan.key, str(test_building_shifted_laz_path))

    response = await api_client.post(
        f"/stages/{stage.id}/compare",
        params={"tolerance": 0.05},
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == TaskType.COMPARING_PLAN_FACT.value
    assert body["entity_id"] == str(stage.id)
    assert body["workspace_id"] == str(auth_context.workspace_id)

    async def assert_compare_complited() -> None:
        async with session_maker() as session:
            task = await TaskService.get_task(body["id"], session=session)
            assert task is not None
            assert task.status == TaskStatus.SUCCEEDED

            recording_result = (
                await RecordingResultService.get_recording_results_for_project(
                    project.id, session
                )
            )
            assert len(recording_result) != 0
            assert recording_result[0].point_cloud_id is not None
            assert recording_result[0].xlsx_report_id is not None
            assert recording_result[0].pdf_report_id is not None
            assert recording_result[0].type == RecordingResultType.PLAN_FACT

            result_point_cloud = await FileService.get_point_cloud(
                recording_result[0].point_cloud_id, session=session
            )
            assert result_point_cloud.type == PointCloudType.RECORDING
            assert result_point_cloud.file_id is not None
            assert result_point_cloud.file.key is not None
            assert result_point_cloud.file.filename.endswith(".laz")
            assert result_point_cloud.file.size > 0
            assert storage.file_exists(result_point_cloud.file.key)

            xlsx_report = await FileService.get_file(
                recording_result[0].xlsx_report_id, session=session
            )
            assert xlsx_report is not None
            assert xlsx_report.filename.endswith(".xlsx")
            assert xlsx_report.size > 0
            assert storage.file_exists(xlsx_report.key)

            pdf_report = await FileService.get_file(
                recording_result[0].pdf_report_id, session=session
            )
            assert pdf_report is not None
            assert pdf_report.filename.endswith(".pdf")
            assert pdf_report.size > 0
            assert storage.file_exists(pdf_report.key)

            converted_files = await FileService.get_converted_point_cloud_files(
                result_point_cloud.id, session=session
            )
            assert len(converted_files) >= 4

    await wait_until(assert_compare_complited, timeout=60)


@pytest.mark.asyncio
async def test_stage_endpoints_return_401_without_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """Protected stage endpoints should reject unauthenticated requests."""
    workspace = await create_test_workspace(db_session)
    project = await setup_project_in_workspace(db_session, workspace.id)
    stage = await setup_stage_in_project(db_session, project.id)
    file_meta = FileService.collect_file_data(test_building_laz_path)

    protected_requests = [
        api_client.get(f"/stages/{stage.id}"),
        api_client.delete(f"/stages/{stage.id}"),
        api_client.post(
            f"/stages/{stage.id}/clouds/upload",
            json={
                "filename": file_meta["filename"],
                "content_type": file_meta["content_type"],
                "size": file_meta["size"],
            },
        ),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_stage_endpoints_return_403_for_non_member(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Protected stage endpoints should reject users outside the workspace."""
    owner_workspace = await create_test_workspace(db_session)
    project = await setup_project_in_workspace(db_session, owner_workspace.id)
    stage = await setup_stage_in_project(db_session, project.id)

    other_workspace = await create_test_workspace(db_session)
    outsider = await create_test_user(
        db_session,
        email="stage-outsider@example.com",
        username="stage-outsider",
    )
    await create_test_membership(
        db_session, other_workspace.id, outsider.id, Role.OWNER
    )
    await db_session.commit()

    outsider_headers = {"Authorization": f"Bearer {create_access_token(outsider.id)}"}

    protected_requests = [
        api_client.get(f"/stages/{stage.id}", headers=outsider_headers),
        api_client.delete(f"/stages/{stage.id}", headers=outsider_headers),
        api_client.post(f"/stages/{stage.id}/clouds/upload", headers=outsider_headers),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_stage_endpoints_returns_404_for_unknown_id(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Protected stage endpoints should return 404 for a non-existent stage."""
    protected_requests = [
        api_client.get(f"/stages/{uuid4()}", headers=auth_context.headers),
        api_client.delete(f"/stages/{uuid4()}", headers=auth_context.headers),
        api_client.post(
            f"/stages/{uuid4()}/clouds/upload", headers=auth_context.headers
        ),
        api_client.post(f"/stages/{uuid4()}/compare", headers=auth_context.headers),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 404

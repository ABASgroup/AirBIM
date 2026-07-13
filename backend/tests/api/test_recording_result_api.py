"""API integration tests for recording result endpoints."""

from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import Permission, Role
from core.security import create_access_token

from main import app

from repositories.recording_result import RecordingResultRepository

from schemas.recording_result import RecordingResultType

from tests.api.conftest import AuthContext
from tests.api.helpers import (
    gather_responses,
    role_has_permission,
    setup_project_in_workspace,
    setup_recording_result_in_project,
    setup_recording_result_with_reports,
)
from tests.helpers import (
    create_test_membership,
    create_test_user,
    create_test_workspace,
)


# ---------------------------------------------------------------------------
# Role-based access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_recording_result_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """GET /recording_results/{id} should require RECORDING_RESULT_VIEW permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    recording_result = await setup_recording_result_in_project(
        db_session,
        auth_context_with_role.workspace_id,
        project.id,
        test_building_laz_path,
    )

    response = await api_client.get(
        f"/recording_results/{recording_result.id}",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(
        auth_context_with_role.role, Permission.RECORDING_RESULT_VIEW
    ):
        assert response.status_code == 200
        assert response.json()["id"] == str(recording_result.id)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_recording_result_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """DELETE /recording_results/{id} currently checks RECORDING_RESULT_VIEW permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    recording_result = await setup_recording_result_in_project(
        db_session,
        auth_context_with_role.workspace_id,
        project.id,
        test_building_laz_path,
    )

    response = await api_client.delete(
        f"/recording_results/{recording_result.id}",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(
        auth_context_with_role.role, Permission.RECORDING_RESULT_VIEW
    ):
        assert response.status_code == 200
        assert response.json()["id"] == str(recording_result.id)
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_excel_report_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_report_xlsx_path: Path,
    test_report_pdf_path: Path,
) -> None:
    """GET /recording_results/{id}/excel should require RECORDING_RESULT_VIEW permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    recording_result = await setup_recording_result_with_reports(
        db_session,
        auth_context_with_role.workspace_id,
        project.id,
        test_building_laz_path,
        test_report_xlsx_path,
        test_report_pdf_path,
    )

    response = await api_client.get(
        f"/recording_results/{recording_result.id}/excel",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(
        auth_context_with_role.role, Permission.RECORDING_RESULT_VIEW
    ):
        assert response.status_code == 200
        assert response.json()["filename"].endswith(".xlsx")
    else:
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_pdf_report_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_report_xlsx_path: Path,
    test_report_pdf_path: Path,
) -> None:
    """GET /recording_results/{id}/pdf should require RECORDING_RESULT_VIEW permission."""
    project = await setup_project_in_workspace(
        db_session, auth_context_with_role.workspace_id
    )
    recording_result = await setup_recording_result_with_reports(
        db_session,
        auth_context_with_role.workspace_id,
        project.id,
        test_building_laz_path,
        test_report_xlsx_path,
        test_report_pdf_path,
    )

    response = await api_client.get(
        f"/recording_results/{recording_result.id}/pdf",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(
        auth_context_with_role.role, Permission.RECORDING_RESULT_VIEW
    ):
        assert response.status_code == 200
        assert response.json()["filename"].endswith(".pdf")
    else:
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Functional tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_recording_result_returns_data(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """GET /recording_results/{id} should return recording result metadata."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    recording_result = await setup_recording_result_in_project(
        db_session,
        auth_context.workspace_id,
        project.id,
        test_building_laz_path,
        data={"progress": 42},
        recording_type=RecordingResultType.PLAN_FACT,
    )

    response = await api_client.get(
        f"/recording_results/{recording_result.id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(recording_result.id)
    assert body["project_id"] == str(project.id)
    assert body["type"] == RecordingResultType.PLAN_FACT.value
    assert body["data"] == {"progress": 42}
    assert body["point_cloud_id"] is not None


@pytest.mark.asyncio
async def test_delete_recording_result_removes_record(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """DELETE /recording_results/{id} should remove the recording result."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    recording_result = await setup_recording_result_in_project(
        db_session,
        auth_context.workspace_id,
        project.id,
        test_building_laz_path,
    )
    recording_result_id = recording_result.id

    response = await api_client.delete(
        f"/recording_results/{recording_result_id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(recording_result_id)

    get_response = await api_client.get(
        f"/recording_results/{recording_result_id}",
        headers=auth_context.headers,
    )
    assert get_response.status_code == 404

    db_session.expire_all()
    assert (
        await RecordingResultRepository.get_by_id(
            recording_result_id, session=db_session
        )
        is None
    )


@pytest.mark.asyncio
async def test_get_excel_report_returns_file_metadata(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_report_xlsx_path: Path,
    test_report_pdf_path: Path,
) -> None:
    """GET /recording_results/{id}/excel should return excel report file metadata."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    recording_result = await setup_recording_result_with_reports(
        db_session,
        auth_context.workspace_id,
        project.id,
        test_building_laz_path,
        test_report_xlsx_path,
        test_report_pdf_path,
    )

    response = await api_client.get(
        f"/recording_results/{recording_result.id}/excel",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == test_report_xlsx_path.name
    assert body["workspace_id"] == str(auth_context.workspace_id)
    assert body["size"] == test_report_xlsx_path.stat().st_size


@pytest.mark.asyncio
async def test_get_pdf_report_returns_file_metadata(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_report_xlsx_path: Path,
    test_report_pdf_path: Path,
) -> None:
    """GET /recording_results/{id}/pdf should return pdf report file metadata."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    recording_result = await setup_recording_result_with_reports(
        db_session,
        auth_context.workspace_id,
        project.id,
        test_building_laz_path,
        test_report_xlsx_path,
        test_report_pdf_path,
    )

    response = await api_client.get(
        f"/recording_results/{recording_result.id}/pdf",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == test_report_pdf_path.name
    assert body["workspace_id"] == str(auth_context.workspace_id)
    assert body["size"] == test_report_pdf_path.stat().st_size


@pytest.mark.asyncio
async def test_get_excel_report_returns_404_when_missing(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """GET /recording_results/{id}/excel should return 404 when report is absent."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    recording_result = await setup_recording_result_in_project(
        db_session,
        auth_context.workspace_id,
        project.id,
        test_building_laz_path,
    )

    response = await api_client.get(
        f"/recording_results/{recording_result.id}/excel",
        headers=auth_context.headers,
    )

    assert response.status_code == 404
    assert "excel report" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_get_pdf_report_returns_404_when_missing(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """GET /recording_results/{id}/pdf should return 404 when report is absent."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    recording_result = await setup_recording_result_in_project(
        db_session,
        auth_context.workspace_id,
        project.id,
        test_building_laz_path,
    )

    response = await api_client.get(
        f"/recording_results/{recording_result.id}/pdf",
        headers=auth_context.headers,
    )

    assert response.status_code == 404
    assert "pdf report" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_recording_result_endpoints_return_401_without_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_report_xlsx_path: Path,
    test_report_pdf_path: Path,
) -> None:
    """Protected recording result endpoints should reject unauthenticated requests."""
    workspace = await create_test_workspace(db_session)
    project = await setup_project_in_workspace(db_session, workspace.id)
    recording_result = await setup_recording_result_with_reports(
        db_session,
        workspace.id,
        project.id,
        test_building_laz_path,
        test_report_xlsx_path,
        test_report_pdf_path,
    )

    protected_requests = [
        api_client.get(f"/recording_results/{recording_result.id}"),
        api_client.delete(f"/recording_results/{recording_result.id}"),
        api_client.get(f"/recording_results/{recording_result.id}/excel"),
        api_client.get(f"/recording_results/{recording_result.id}/pdf"),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_recording_result_endpoints_return_403_for_non_member(
    api_client: AsyncClient,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """Protected recording result endpoints should reject users outside the workspace."""
    owner_workspace = await create_test_workspace(db_session)
    project = await setup_project_in_workspace(db_session, owner_workspace.id)
    recording_result = await setup_recording_result_in_project(
        db_session,
        owner_workspace.id,
        project.id,
        test_building_laz_path,
    )

    other_workspace = await create_test_workspace(db_session)
    outsider = await create_test_user(
        db_session,
        email="recording-outsider@example.com",
        username="recording-outsider",
    )
    await create_test_membership(
        db_session, other_workspace.id, outsider.id, Role.OWNER
    )
    await db_session.commit()

    outsider_headers = {
        "Authorization": f"Bearer {create_access_token(outsider.id)}"}

    protected_requests = [
        api_client.get(
            f"/recording_results/{recording_result.id}", headers=outsider_headers
        ),
        api_client.delete(
            f"/recording_results/{recording_result.id}", headers=outsider_headers
        ),
        api_client.get(
            f"/recording_results/{recording_result.id}/excel", headers=outsider_headers
        ),
        api_client.get(
            f"/recording_results/{recording_result.id}/pdf", headers=outsider_headers
        ),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 403
        assert "membership" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_get_recording_result_returns_404_for_unknown_id(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Protected recording result endpoints should return 404 for a non-existent result."""

    protected_requests = [
        api_client.get(
            f"/recording_results/{uuid4()}", headers=auth_context.headers),
        api_client.delete(
            f"/recording_results/{uuid4()}", headers=auth_context.headers
        ),
        api_client.get(
            f"/recording_results/{uuid4()}/excel", headers=auth_context.headers
        ),
        api_client.get(
            f"/recording_results/{uuid4()}/pdf", headers=auth_context.headers
        ),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 404

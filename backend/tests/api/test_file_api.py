"""API integration tests for files endpoints."""

from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.roles import Permission, Role
from core.security import create_access_token

from infrastructure.database import session_maker
from infrastructure.storage import Storage

from repositories.files import FileRepository

from schemas.file import FileDataRequest, FileStatus, PointCloudType
from schemas.task import TaskType

from services.file import FileService

from tests.api.conftest import AuthContext
from tests.api.helpers import (
    gather_responses,
    role_has_permission,
    setup_pending_file_in_storage,
    setup_point_cloud_with_converted_file,
    setup_point_cloud_with_stage,
    setup_project_in_workspace,
)
from tests.helpers import (
    create_test_bim,
    create_test_file,
    create_test_membership,
    create_test_user,
    create_test_workspace,
    wait_until,
)


@pytest.mark.asyncio
async def test_confirm_upload_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Confirm upload should require FILES_UPLOAD permission."""
    file = await setup_pending_file_in_storage(
        db_session,
        storage,
        auth_context_with_role.workspace_id,
        test_building_ifc_path,
    )

    response = await api_client.post(
        f"/files/{file.id}/confirm",
        json={
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
        },
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.FILES_UPLOAD):
        assert response.status_code == 200
        body = response.json()
        file_data = body.get("file", body)
        assert file_data["id"] == str(file.id)
        assert file_data["status"] == FileStatus.UPLOADED.value
    else:
        assert response.status_code == 403
        assert "permission" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_delete_file_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Delete file should require FILES_DELETE permission."""
    file = await setup_pending_file_in_storage(
        db_session,
        storage,
        auth_context_with_role.workspace_id,
        test_building_ifc_path,
    )

    response = await api_client.delete(
        f"/files/{file.id}",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.FILES_DELETE):
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(file.id)
    else:
        assert response.status_code == 403
        assert "permission" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_get_download_link_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Download link endpoint should require FILES_DOWNLOAD permission."""
    file = await setup_pending_file_in_storage(
        db_session,
        storage,
        auth_context_with_role.workspace_id,
        test_building_ifc_path,
    )

    response = await api_client.post(
        f"/files/{file.id}/download",
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.FILES_DOWNLOAD):
        assert response.status_code == 200
        body = response.json()
        assert body["file"]["id"] == str(file.id)
        assert isinstance(body["url"], str)
        assert body["url"]
    else:
        assert response.status_code == 403
        assert "permission" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_get_point_cloud_respects_role_permissions(
    api_client: AsyncClient,
    auth_context_with_role: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """Point cloud info endpoint should require FILES_VIEW permission."""
    point_cloud, file = await setup_point_cloud_with_stage(
        db_session,
        auth_context_with_role.workspace_id,
        test_building_laz_path,
    )

    response = await api_client.post(
        f"/files/point_clouds/{point_cloud.id}",
        params={"file_id": str(file.id)},
        headers=auth_context_with_role.headers,
    )

    if role_has_permission(auth_context_with_role.role, Permission.FILES_VIEW):
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(point_cloud.id)
        assert body["file"]["id"] == str(file.id)
    else:
        assert response.status_code == 403
        assert "permission" in response.json().get("message", "").lower()


# ---------------------------------------------------------------------------
# Functional tests (endpoint behaviour with storage and database)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_upload_marks_file_as_uploaded_in_db(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Confirm should verify storage object and persist uploaded status."""
    file = await setup_pending_file_in_storage(
        db_session, storage, auth_context.workspace_id, test_building_ifc_path
    )
    file_id = file.id
    file_key = file.key

    response = await api_client.post(
        f"/files/{file_id}/confirm",
        json={
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
        },
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    file_data = body.get("file", body)
    assert file_data["status"] == FileStatus.UPLOADED.value

    db_session.expire_all()
    saved_file = await FileRepository.get_by_id(file_id, session=db_session)
    assert saved_file is not None
    assert saved_file.status.value == FileStatus.UPLOADED.value
    assert storage.file_exists(file_key)


@pytest.mark.asyncio
async def test_confirm_upload_returns_404_when_object_missing_in_storage(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_ifc_path: Path,
) -> None:
    """Confirm should fail when DB record exists but storage object is absent."""
    file = await create_test_file(
        db_session, auth_context.workspace_id, test_building_ifc_path
    )
    await db_session.commit()

    response = await api_client.post(
        f"/files/{file.id}/confirm",
        json={
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
        },
        headers=auth_context.headers,
    )

    assert response.status_code == 404
    assert "not found" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_confirm_upload_returns_401_for_mismatched_metadata(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Confirm should reject metadata that does not match the DB record."""
    file = await setup_pending_file_in_storage(
        db_session, storage, auth_context.workspace_id, test_building_ifc_path
    )

    response = await api_client.post(
        f"/files/{file.id}/confirm",
        json={
            "filename": "wrong-name.ifc",
            "content_type": file.content_type,
            "size": file.size,
        },
        headers=auth_context.headers,
    )

    assert response.status_code == 401

    saved_file = await FileRepository.get_by_id(file.id, session=db_session)
    assert saved_file is not None
    assert saved_file.status.value == FileStatus.PENDING.value


@pytest.mark.asyncio
async def test_confirm_upload_returns_409_when_file_already_uploaded(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Confirm should not allow confirming the same file twice."""
    file = await setup_pending_file_in_storage(
        db_session, storage, auth_context.workspace_id, test_building_ifc_path
    )
    payload = {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
    }

    first_response = await api_client.post(
        f"/files/{file.id}/confirm",
        json=payload,
        headers=auth_context.headers,
    )
    assert first_response.status_code == 200

    second_response = await api_client.post(
        f"/files/{file.id}/confirm",
        json=payload,
        headers=auth_context.headers,
    )

    assert second_response.status_code == 409
    assert "already exist" in second_response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_confirm_upload_for_point_cloud_do_conversion_task(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_laz_path: Path,
) -> None:
    """Confirm for a point cloud file should start conversion task and finish it successfully"""
    point_cloud, file = await setup_point_cloud_with_stage(
        db_session, auth_context.workspace_id, test_building_laz_path
    )
    with test_building_laz_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, file.key)
    await db_session.commit()

    response = await api_client.post(
        f"/files/{file.id}/confirm",
        json={
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
        },
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["file"]["id"] == str(file.id)
    assert body["file"]["status"] == FileStatus.UPLOADED.value
    assert body["task"]["type"] == TaskType.CONVERTING_POINT_CLOUD.value
    assert body["task"]["entity_id"] == str(point_cloud.id)

    async def assert_file_converted() -> None:
        async with session_maker() as session:

            converted_files = await FileService.get_converted_point_cloud_files(
                point_cloud.id, session=session
            )
            assert len(converted_files) >= 4

            files_dict = {file.filename: file for file in converted_files}

            required_files = ["log.txt", "metadata.json", "octree.bin", "hierarchy.bin"]
            for req_file in required_files:
                assert (
                    req_file in files_dict
                ), f"Missing required Potree file: {req_file}"

    await wait_until(assert_file_converted)


@pytest.mark.asyncio
async def test_confirm_upload_for_bim_do_conversion_task(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Confirm for a BIM file should start conversion task and finish it successfully."""
    project = await setup_project_in_workspace(db_session, auth_context.workspace_id)
    file = await create_test_file(
        db_session, auth_context.workspace_id, test_building_ifc_path
    )
    bim = await create_test_bim(db_session, project.id, file.id)

    file.key = FileService.create_file_key(test_building_ifc_path.name)
    storage.upload_file_locally(file.key, str(test_building_ifc_path))
    await db_session.commit()

    response = await api_client.post(
        f"/files/{file.id}/confirm",
        json={
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
        },
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["file"]["id"] == str(file.id)
    assert body["file"]["status"] == FileStatus.UPLOADED.value
    assert body["task"]["type"] == TaskType.CONVERTING_BIM.value
    assert body["task"]["entity_id"] == str(bim.id)

    project_id = project.id
    file_id = file.id

    async def assert_bim_converted_to_point_cloud() -> None:
        async with session_maker() as session:
            converted_bim = await FileService.get_bim_by_project_id(project_id, session)
            assert converted_bim.point_cloud_id is not None
            assert converted_bim.file_id == file_id

            point_cloud = await FileService.get_point_cloud(
                converted_bim.point_cloud_id, session
            )
            assert point_cloud.file_id is not None
            assert point_cloud.type == PointCloudType.PLAN

            point_cloud_file = await FileService.get_file(point_cloud.file_id, session)
            assert point_cloud_file.size > 0
            assert point_cloud_file.status == FileStatus.UPLOADED
            assert point_cloud_file.key is not None
            assert point_cloud_file.filename is not None
            assert point_cloud_file.filename.endswith(".laz")
            assert storage.file_exists(point_cloud_file.key)

            assert converted_bim.preview_file_id is not None
            preview_file = await FileService.get_file(converted_bim.preview_file_id, session)
            assert preview_file.size > 0
            assert preview_file.content_type.startswith("image/")
            assert storage.file_exists(preview_file.key)

    await wait_until(assert_bim_converted_to_point_cloud)


@pytest.mark.asyncio
async def test_delete_file_removes_record_and_storage_object(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Delete should remove the file from both database and storage."""
    file = await setup_pending_file_in_storage(
        db_session, storage, auth_context.workspace_id, test_building_ifc_path
    )
    file_id = file.id
    file_key = file.key
    assert storage.file_exists(file_key)

    response = await api_client.delete(
        f"/files/{file_id}",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(file_id)
    assert not storage.file_exists(file_key)
    db_session.expire_all()
    assert await FileRepository.get_by_id(file_id, session=db_session) is None


@pytest.mark.asyncio
async def test_delete_file_returns_404_for_unknown_file(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Delete should return 404 when file id does not exist."""
    response = await api_client.delete(
        f"/files/{uuid4()}",
        headers=auth_context.headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_download_link_returns_presigned_url_and_metadata(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Download endpoint should return file metadata and a non-empty presigned URL."""
    file = await setup_pending_file_in_storage(
        db_session, storage, auth_context.workspace_id, test_building_ifc_path
    )

    response = await api_client.post(
        f"/files/{file.id}/download",
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["file"]["id"] == str(file.id)
    assert body["file"]["filename"] == file.filename
    assert body["file"]["key"] == file.key
    assert isinstance(body["url"], str)
    assert body["url"].startswith("http")
    assert file.key in body["url"] or "X-Amz" in body["url"]


@pytest.mark.asyncio
async def test_get_download_link_returns_404_for_unknown_file(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Download should return 404 when file id does not exist."""
    response = await api_client.post(
        f"/files/{uuid4()}/download",
        headers=auth_context.headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_point_cloud_returns_nested_file_data(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
) -> None:
    """Point cloud endpoint should return point cloud with nested file metadata."""
    point_cloud, file = await setup_point_cloud_with_stage(
        db_session, auth_context.workspace_id, test_building_laz_path
    )

    response = await api_client.post(
        f"/files/point_clouds/{point_cloud.id}",
        params={"file_id": str(file.id)},
        headers=auth_context.headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(point_cloud.id)
    assert body["stage_id"] == str(point_cloud.stage_id)
    assert body["type"] == point_cloud.type.value
    assert body["file"]["id"] == str(file.id)
    assert body["file"]["filename"] == file.filename
    assert body["file"]["workspace_id"] == str(auth_context.workspace_id)


@pytest.mark.asyncio
async def test_get_point_cloud_returns_404_for_unknown_id(
    api_client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    """Point cloud endpoint should return 404 for unknown point cloud id."""
    response = await api_client.post(
        f"/files/point_clouds/{uuid4()}",
        params={"file_id": str(uuid4())},
        headers=auth_context.headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_pointcloud_file_returns_bytes_matching_storage(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_laz_path: Path,
    test_building_shifted_laz_path: Path,
) -> None:
    """Streaming endpoint should return the same bytes as stored in S3."""
    point_cloud, converted_file = await setup_point_cloud_with_converted_file(
        db_session,
        storage,
        auth_context.workspace_id,
        test_building_laz_path,
        test_building_shifted_laz_path,
    )
    expected_content = storage.download_file_object(converted_file.key).read()

    response = await api_client.get(
        f"/files/point_clouds/{point_cloud.id}/{converted_file.filename}",
        params={"file_id": str(converted_file.id)},
        headers=auth_context.headers,
    )
    assert response.status_code == 200
    assert response.content == expected_content
    assert response.headers.get("accept-ranges") == "bytes"


@pytest.mark.asyncio
async def test_get_pointcloud_file_supports_range_requests(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    storage: Storage,
    test_building_laz_path: Path,
    test_building_shifted_laz_path: Path,
) -> None:
    """Streaming endpoint should honour HTTP Range and return partial content."""
    point_cloud, converted_file = await setup_point_cloud_with_converted_file(
        db_session,
        storage,
        auth_context.workspace_id,
        test_building_laz_path,
        test_building_shifted_laz_path,
    )
    expected_prefix = storage.download_file_object(converted_file.key).read(128)

    headers = auth_context.headers
    headers["Range"] = "bytes=0-127"

    response = await api_client.get(
        f"/files/point_clouds/{point_cloud.id}/{converted_file.filename}",
        params={"file_id": str(converted_file.id)},
        headers=headers,
    )

    assert response.status_code == 206
    assert response.content == expected_prefix
    assert response.headers.get("content-range") is not None


@pytest.mark.asyncio
async def test_get_pointcloud_file_returns_404_for_unknown_filename(
    api_client: AsyncClient,
    auth_context: AuthContext,
    db_session: AsyncSession,
    test_building_laz_path: Path,
    storage: Storage,
) -> None:
    """Streaming endpoint should return 404 when filename is not linked to point cloud."""
    point_cloud, _ = await setup_point_cloud_with_stage(
        db_session, auth_context.workspace_id, test_building_laz_path
    )

    storage.upload_file_locally(point_cloud.file.key, str(test_building_laz_path))

    response = await api_client.get(
        f"/files/point_clouds/{point_cloud.id}/missing-file.bin",
        params={"file_id": str(uuid4())},
        headers=auth_context.headers,
    )

    assert response.status_code == 404
    assert "not found" in response.json().get("message", "").lower()


@pytest.mark.asyncio
async def test_file_endpoints_return_401_without_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
    test_building_ifc_path: Path,
) -> None:
    """Protected file endpoints should reject unauthenticated requests."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(db_session, workspace.id, test_building_ifc_path)
    await db_session.commit()

    protected_requests = [
        api_client.post(
            f"/files/{file.id}/confirm",
            json=FileDataRequest(
                filename=file.filename,
                content_type=file.content_type,
                size=file.size,
            ).model_dump(),
        ),
        api_client.delete(f"/files/{file.id}"),
        api_client.post(f"/files/{file.id}/download"),
        api_client.post(
            f"/files/point_clouds/{uuid4()}",
            params={"file_id": str(file.id)},
        ),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_file_endpoints_return_403_for_non_member(
    api_client: AsyncClient,
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
) -> None:
    """Protected file endpoints should reject users outside file workspace."""
    owner_workspace = await create_test_workspace(db_session)
    file = await setup_pending_file_in_storage(
        db_session, storage, owner_workspace.id, test_building_ifc_path
    )

    other_workspace = await create_test_workspace(db_session)
    outsider = await create_test_user(
        db_session,
        email="outsider@example.com",
        username="outsider",
    )
    await create_test_membership(
        db_session, other_workspace.id, outsider.id, Role.OWNER
    )
    await db_session.commit()

    outsider_headers = {"Authorization": f"Bearer {create_access_token(outsider.id)}"}

    response = await api_client.post(
        f"/files/{file.id}/download",
        headers=outsider_headers,
    )

    protected_requests = [
        api_client.post(
            f"/files/{file.id}/confirm",
            json=FileDataRequest(
                filename=file.filename,
                content_type=file.content_type,
                size=file.size,
            ).model_dump(),
            headers=outsider_headers,
        ),
        api_client.delete(f"/files/{file.id}", headers=outsider_headers),
        api_client.post(f"/files/{file.id}/download", headers=outsider_headers),
        api_client.post(
            f"/files/point_clouds/{uuid4()}",
            params={"file_id": str(file.id)},
            headers=outsider_headers,
        ),
    ]

    for response in await gather_responses(list(protected_requests)):
        assert response.status_code == 403 or response.status_code == 422

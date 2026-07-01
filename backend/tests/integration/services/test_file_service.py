"""Tests for File Service."""

from datetime import timedelta
from pathlib import Path
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import InvalidFileMetaDataError, NotFoundError

from infrastructure.storage import Storage

from repositories.files import (
    BIMRepository,
    FileRepository,
    PointCloudConvertedRepository,
    PointCloudRepository,
)

from schemas.file import (
    BIMModel,
    FileDataRequest,
    FileModel,
    FileStatus,
    PointCloudType,
)

from services.file import FileService

from tests.helpers import (
    create_test_bim,
    create_test_file,
    create_test_point_cloud,
    create_test_project,
    create_test_stage,
    create_test_workspace,
)


@pytest.mark.asyncio
async def test_create_file_key(test_building_ifc_path: Path) -> None:
    """Service should create a unique file key based on filename."""
    key = FileService.create_file_key(test_building_ifc_path.name)
    assert key.endswith(f"/{test_building_ifc_path.name}")


@pytest.mark.asyncio
async def test_clean_up_files(
    db_session: AsyncSession,
    storage: Storage,
    test_building_ifc_path: Path,
    test_building_laz_path: Path,
) -> None:
    """Service should delete orphan files and files pending for too long."""
    workspace = await create_test_workspace(db_session)

    # Create not an orphan file that should not be deleted
    # (has field in DB with status UPLOADED and object in storage)
    uploaded_file = await create_test_file(
        db_session, workspace.id, file_path=test_building_ifc_path
    )
    with test_building_ifc_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, uploaded_file.key)
    await FileService.confirm_file_upload(
        uploaded_file.id,
        FileDataRequest(
            filename=uploaded_file.filename,
            content_type=uploaded_file.content_type,
            size=uploaded_file.size,
        ),
        storage=storage,
        session=db_session,
    )
    assert uploaded_file.status == FileStatus.UPLOADED
    assert (
        await FileRepository.get_by_id(uploaded_file.id, session=db_session) is not None
    )
    assert storage.file_exists(uploaded_file.key) is True

    # Create a file with PENDING status that should be deleted
    # (has field in DB but object is not uploaded to storage, and it's PENDING for more than 1 day)
    old_pending_file = await create_test_file(
        db_session, workspace.id, file_path=test_building_laz_path
    )
    old_pending_file.created_at = old_pending_file.created_at - \
        timedelta(days=2)
    assert old_pending_file.status == FileStatus.PENDING
    assert (
        await FileRepository.get_by_id(old_pending_file.id, session=db_session)
        is not None
    )
    assert storage.file_exists(old_pending_file.key) is False

    # Create a file with Pending status that should not be deleted
    # (has field in DB but object is not uploaded to storage, but it's PENDING for less than 1 day)
    recent_pending_file = await create_test_file(
        db_session, workspace.id, file_path=test_building_laz_path
    )
    assert recent_pending_file.created_at > old_pending_file.created_at
    assert recent_pending_file.status == FileStatus.PENDING
    assert (
        await FileRepository.get_by_id(recent_pending_file.id, session=db_session)
        is not None
    )
    assert storage.file_exists(recent_pending_file.key) is False

    # Create an orphan file that should be deleted
    # (has object in storage but no DB record)
    orphan_key = FileService.create_file_key("orphan-file.laz")
    with test_building_laz_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, orphan_key)
    assert storage.file_exists(orphan_key) is True
    assert await FileRepository.get_by_key(orphan_key, session=db_session) is None

    deleted_count = await FileService.clean_up_files(
        storage=storage,
        session=db_session,
        pending_for_limit=timedelta(days=1),
    )

    assert deleted_count == 2, "Should delete both old pending file and orphan file"

    assert (
        await FileRepository.get_by_id(uploaded_file.id, session=db_session) is not None
    )
    assert storage.file_exists(uploaded_file.key) is True

    assert (
        await FileRepository.get_by_id(recent_pending_file.id, session=db_session)
        is not None
    )
    assert storage.file_exists(recent_pending_file.key) is False

    assert (
        await FileRepository.get_by_id(old_pending_file.id, session=db_session) is None
    )
    assert storage.file_exists(orphan_key) is False


@pytest.mark.asyncio
async def test_check_file_meta(
    db_session: AsyncSession, test_building_ifc_path: Path
) -> None:
    """Service should check if file metadata matches the actual file in storage."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_ifc_path
    )

    # # Correct metadata should pass
    FileService.check_file_meta(
        file=file,
        content_type="application/x-ifc",
        size=test_building_ifc_path.stat().st_size,
        filename=test_building_ifc_path.name,
    )

    # Incorrect filename should fail
    with pytest.raises(InvalidFileMetaDataError):
        FileService.check_file_meta(
            file=file,
            filename="wrong-name.ifc",
            content_type="application/x-ifc",
            size=test_building_ifc_path.stat().st_size,
        )

    # Incorrect content type should fail
    with pytest.raises(InvalidFileMetaDataError):
        FileService.check_file_meta(
            file=file,
            filename=test_building_ifc_path.name,
            content_type="wrong/type",
            size=test_building_ifc_path.stat().st_size,
        )

    # Incorrect size should fail
    with pytest.raises(InvalidFileMetaDataError):
        FileService.check_file_meta(
            file=file,
            filename=test_building_ifc_path.name,
            content_type="application/x-ifc",
            size=test_building_ifc_path.stat().st_size + 1,
        )


@pytest.mark.asyncio
async def test_delete_file_removes_db_entry_and_storage_object(
    db_session: AsyncSession, storage: Storage, test_building_ifc_path: Path
) -> None:
    """Service should delete file from storage and remove database record."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_ifc_path
    )

    with test_building_ifc_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, file.key)

    deleted_file = await FileService.delete_file(
        file.id,
        session=db_session,
        storage=storage,
    )

    assert deleted_file.id == file.id
    assert storage.file_exists(file.key) is False
    assert await FileRepository.get_by_id(file.id, session=db_session) is None


@pytest.mark.asyncio
async def test_collect_file_data_reads_fixture_metadata(
    test_building_ifc_path: Path,
) -> None:
    """Service should collect filename, size, key and content type from a local file."""
    file_data = FileService.collect_file_data(test_building_ifc_path)

    assert file_data["filename"] == test_building_ifc_path.name
    assert file_data["size"] == test_building_ifc_path.stat().st_size
    assert file_data["key"].endswith(f"/{test_building_ifc_path.name}")
    assert file_data["content_type"] == "application/x-ifc"


@pytest.mark.asyncio
async def test_generate_file_download_link_returns_presigned_url(
    db_session: AsyncSession, storage: Storage, test_building_ifc_path: Path
) -> None:
    """Service should generate a download link for an existing file."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_ifc_path
    )

    with test_building_ifc_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, file.key)

    link = await FileService.generate_file_download_link(
        file.id,
        session=db_session,
        storage=storage,
    )

    assert isinstance(link, str)
    assert file.key in link


@pytest.mark.asyncio
async def test_generate_file_download_link_raises_for_missing_file(
    db_session: AsyncSession, storage: Storage
) -> None:
    """Service should raise if download link requested for non-existent file."""
    with pytest.raises(NotFoundError):
        await FileService.generate_file_download_link(
            uuid.uuid4(),
            session=db_session,
            storage=storage,
        )


@pytest.mark.asyncio
async def test_confirm_file_upload_marks_file_as_uploaded(
    db_session: AsyncSession, storage: Storage, test_building_laz_path: Path
) -> None:
    """Service should verify uploaded object and mark file as uploaded."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )

    with test_building_laz_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, file.key)

    confirmed_file = await FileService.confirm_file_upload(
        file.id,
        FileDataRequest(
            filename=file.filename,
            content_type=file.content_type,
            size=file.size,
        ),
        storage=storage,
        session=db_session,
    )

    assert confirmed_file.status == FileStatus.UPLOADED
    saved_file = await FileRepository.get_by_id(file.id, session=db_session)
    assert saved_file is not None
    assert saved_file.status == FileStatus.UPLOADED


@pytest.mark.asyncio
async def test_confirm_file_upload_raises_for_invalid_metadata(
    db_session: AsyncSession, storage: Storage, test_building_laz_path: Path
) -> None:
    """Service should reject upload confirmation if metadata does not match DB record."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )

    with test_building_laz_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, file.key)

    with pytest.raises(InvalidFileMetaDataError):
        await FileService.confirm_file_upload(
            file.id,
            FileDataRequest(
                filename="wrong-name.laz",
                content_type=file.content_type,
                size=file.size,
            ),
            storage=storage,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_confirm_file_upload_raises_if_storage_object_missing(
    db_session: AsyncSession, storage: Storage, test_building_shifted_laz_path: Path
) -> None:
    """Service should fail if DB record exists but object was not uploaded to storage."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_shifted_laz_path
    )

    with pytest.raises(NotFoundError):
        await FileService.confirm_file_upload(
            file.id,
            FileDataRequest(
                filename=file.filename,
                content_type=file.content_type,
                size=file.size,
            ),
            storage=storage,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_create_and_get_file(
    db_session: AsyncSession, test_building_ifc_path: Path
) -> None:
    """Service should create file record in DB."""
    workspace = await create_test_workspace(db_session)

    file = await FileService.create_file(
        file_data=FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ),
        session=db_session,
    )

    assert file.id is not None
    assert file.filename == test_building_ifc_path.name
    assert file.size == test_building_ifc_path.stat().st_size
    assert file.content_type == "application/x-ifc"

    file = await FileService.get_file(file.id, session=db_session)
    assert file is not None
    assert file.id == file.id
    assert file.filename == test_building_ifc_path.name
    assert file.size == test_building_ifc_path.stat().st_size
    assert file.content_type == "application/x-ifc"


@pytest.mark.asyncio
async def test_get_file_raises_for_nonexistent_id(db_session: AsyncSession) -> None:
    """Service should raise if file with given ID does not exist."""
    with pytest.raises(NotFoundError):
        await FileService.get_file(uuid.uuid4(), session=db_session)


@pytest.mark.asyncio
async def test_get_point_cloud_by_id_and_file_id(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Service should return point cloud with given ID and file ID."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    retrieved_point_cloud = await FileService.get_point_cloud(
        point_cloud.id,
        session=db_session,
    )
    assert retrieved_point_cloud is not None
    assert retrieved_point_cloud.id == point_cloud.id
    assert retrieved_point_cloud.file_id == file.id

    retrieved_point_cloud = await FileService.get_point_cloud_by_file_id(
        file.id,
        session=db_session,
    )
    assert retrieved_point_cloud is not None
    assert retrieved_point_cloud.id == point_cloud.id
    assert retrieved_point_cloud.file_id == file.id


@pytest.mark.asyncio
async def test_get_point_cloud_raises_for_nonexistent_id(
    db_session: AsyncSession,
) -> None:
    """Service should raise if point cloud with given ID does not exist."""
    with pytest.raises(NotFoundError):
        await FileService.get_point_cloud(uuid.uuid4(), session=db_session)

    assert (
        await FileService.get_point_cloud_by_file_id(uuid.uuid4(), session=db_session)
        is None
    )


@pytest.mark.asyncio
async def test_get_bim_by_id_and_file_id_and_project_id(
    db_session: AsyncSession, test_building_ifc_path: Path
) -> None:
    """Service should return BIM with given ID and file ID."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_ifc_path
    )
    bim = await create_test_bim(db_session, project_id=project.id, file_id=file.id)

    retrieved_bim = await FileService.get_bim(
        bim.id,
        session=db_session,
    )
    assert retrieved_bim is not None
    assert retrieved_bim.id == bim.id
    assert retrieved_bim.file_id == file.id

    retrieved_bim = await FileService.get_bim_by_file_id(
        file.id,
        session=db_session,
    )
    assert retrieved_bim is not None
    assert retrieved_bim.id == bim.id
    assert retrieved_bim.file_id == file.id

    retrieved_bim = await FileService.get_bim_by_project_id(
        project.id,
        session=db_session,
    )
    assert retrieved_bim is not None
    assert retrieved_bim.id == bim.id
    assert retrieved_bim.project_id == project.id


@pytest.mark.asyncio
async def test_get_bim_raises_for_nonexistent_id(db_session: AsyncSession) -> None:
    """Service should raise if BIM with given ID does not exist."""
    with pytest.raises(NotFoundError):
        await FileService.get_bim(uuid.uuid4(), session=db_session)

    with pytest.raises(NotFoundError):
        await FileService.get_bim_by_file_id(uuid.uuid4(), session=db_session)

    with pytest.raises(NotFoundError):
        await FileService.get_bim_by_project_id(uuid.uuid4(), session=db_session)


@pytest.mark.asyncio
async def test_generate_bim_upload_link(
    db_session: AsyncSession, storage: Storage, test_building_ifc_path: Path
) -> None:
    """Service should generate upload link for BIM file."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)

    link, file = await FileService.generate_bim_upload_link(
        project.id,
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ),
        session=db_session,
        storage=storage,
    )

    assert isinstance(link, str)
    storage_port = storage._external_client.meta.endpoint_url.split(
        ":")[-1]  # pylint: disable=protected-access
    assert link.startswith(f"http://localhost:{storage_port}") or link.startswith(
        f"https://localhost:{storage_port}"
    )
    assert file.filename == test_building_ifc_path.name
    assert file.size == test_building_ifc_path.stat().st_size
    assert file.content_type == "application/x-ifc"


@pytest.mark.asyncio
async def test_generate_point_cloud_upload_link(
    db_session: AsyncSession, storage: Storage, test_building_laz_path: Path
) -> None:
    """Service should generate upload link for point cloud file."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    stage = await create_test_stage(db_session, project_id=project.id)

    link, file = await FileService.generate_point_cloud_upload_link(
        stage_id=stage.id,
        file_data=FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        storage=storage,
        session=db_session,
    )

    assert isinstance(link, str)
    storage_port = storage._external_client.meta.endpoint_url.split(
        ":")[-1]  # pylint: disable=protected-access
    assert link.startswith(f"http://localhost:{storage_port}") or link.startswith(
        f"https://localhost:{storage_port}"
    )
    assert file.filename == test_building_laz_path.name
    assert file.size == test_building_laz_path.stat().st_size
    assert file.content_type == "application/octet-stream"


@pytest.mark.asyncio
async def test_save_converted_bim_file_creates_plan_point_cloud(
    db_session: AsyncSession, test_building_ifc_path: Path, test_building_laz_path: Path
) -> None:
    """Service should save converted BIM output and attach created plan point cloud to BIM."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_ifc_path
    )
    bim = await create_test_bim(db_session, project_id=project.id, file_id=file.id)

    await FileService.save_converted_bim_file(
        bim.id,
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        session=db_session,
    )

    saved_bim = await BIMRepository.get_by_id(bim.id, session=db_session)
    assert saved_bim is not None
    assert saved_bim.point_cloud_id is not None

    point_cloud = await PointCloudRepository.get_by_id(
        saved_bim.point_cloud_id, session=db_session
    )
    assert point_cloud is not None
    assert point_cloud.type == PointCloudType.PLAN


@pytest.mark.asyncio
async def test_save_and_get_converted_point_cloud_files(
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_report_xlsx_path: Path,
    test_report_pdf_path: Path,
) -> None:
    """Service should save converted point cloud file and create relation record."""
    workspace = await create_test_workspace(db_session)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    await FileService.save_converted_point_cloud_file(
        point_cloud.id,
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_report_xlsx_path),
        ),
        session=db_session,
    )

    await FileService.save_converted_point_cloud_file(
        point_cloud.id,
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_report_pdf_path),
        ),
        session=db_session,
    )

    files = await PointCloudConvertedRepository.get_by_point_cloud_id(
        point_cloud.id,
        session=db_session,
    )
    assert len(files) == 2, "Should have two converted files for the point cloud"

    converted_files = await FileService.get_converted_point_cloud_files(
        point_cloud.id,
        session=db_session,
    )
    assert converted_files is not None
    assert (
        len(converted_files) == 2
    ), "Should return two converted files for the point cloud"
    assert set(f.id for f in converted_files) == set(f.file_id for f in files)


@pytest.mark.asyncio
async def test_create_point_cloud_creates_cloud_and_file(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Service should create point cloud entry together with its file."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    stage = await create_test_stage(db_session, project_id=project.id)

    point_cloud, file = await FileService.create_point_cloud(
        point_cloud_type=PointCloudType.SCAN,
        file_data=FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        session=db_session,
        stage_id=stage.id,
    )

    assert point_cloud.id is not None
    assert point_cloud.stage_id == stage.id
    assert point_cloud.file_id == file.id
    assert file.workspace_id == workspace.id


@pytest.mark.asyncio
async def test_create_bim_creates_bim_and_file(
    db_session: AsyncSession, test_building_ifc_path: Path
) -> None:
    """Service should create BIM entry together with its file."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)

    bim, file = await FileService.create_bim(
        bim_data=BIMModel(project_id=project.id, file_id=uuid.uuid4()),
        file_data=FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ),
        session=db_session,
    )

    assert bim.id is not None
    assert bim.project_id == project.id
    assert bim.file_id == file.id

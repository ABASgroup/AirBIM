"""Tests for File Service."""
from datetime import timedelta
import uuid

import pytest

from core.exceptions import InvalidFileMetaDataError, NotFoundError
from models.file import FileStatus, PointCloudType
from models.project import ProjectStatus
from models.workspace import WorkspaceType
from repositories.files import BIMRepository, FileRepository, PointCloudConvertedRepository, PointCloudRepository
from repositories.project import ProjectRepository
from repositories.workspace import WorkspaceRepository
from schemas.file import BIMModel, FileDataRequest, FileModel, PointCloudModel
from schemas.project import ProjectModel
from schemas.stage import StageModel
from schemas.workspace import WorkspaceModel
from services.file import FileService
from services.stage import create_stage


async def _create_workspace_project_stage(db_session):
    """Create minimal related entities required for file service tests."""
    workspace = await WorkspaceRepository.create(
        WorkspaceModel(name="Files workspace", type=WorkspaceType.TEAM),
        session=db_session,
    )
    project = await ProjectRepository.create(
        ProjectModel(
            workspace_id=workspace.id,
            name="Files project",
            description="Project for file tests",
            status=ProjectStatus.ACTIVE,
        ),
        session=db_session,
    )
    stage = await create_stage(
        StageModel(project_id=project.id),
        session=db_session,
    )
    return workspace, project, stage


@pytest.mark.asyncio
async def test_collect_file_data_reads_fixture_metadata(test_building_ifc_path):
    """Service should collect filename, size, key and content type from a local file."""
    file_data = FileService.collect_file_data(test_building_ifc_path)

    assert file_data["filename"] == test_building_ifc_path.name
    assert file_data["size"] == test_building_ifc_path.stat().st_size
    assert file_data["key"].endswith(f"/{test_building_ifc_path.name}")
    assert file_data["content_type"] == "application/x-ifc"


@pytest.mark.asyncio
async def test_create_file_persists_pending_file(db_session, test_building_laz_path):
    """Service should create a pending file entry in the database."""
    workspace, _, _ = await _create_workspace_project_stage(db_session)

    file = await FileService.create_file(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        session=db_session,
    )

    assert file.id is not None
    assert file.workspace_id == workspace.id
    assert file.status == FileStatus.PENDING


@pytest.mark.asyncio
async def test_generate_file_download_link_returns_presigned_url(db_session, storage, test_building_ifc_path):
    """Service should generate a download link for an existing file."""
    workspace, _, _ = await _create_workspace_project_stage(db_session)
    file = await FileService.create_file(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ),
        session=db_session,
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
async def test_generate_file_download_link_raises_for_missing_file(db_session, storage):
    """Service should raise if download link requested for non-existent file."""
    with pytest.raises(NotFoundError, match="File is not found"):
        await FileService.generate_file_download_link(
            uuid.uuid4(),
            session=db_session,
            storage=storage,
        )


@pytest.mark.asyncio
async def test_confirm_file_upload_marks_file_as_uploaded(db_session, storage, test_building_laz_path):
    """Service should verify uploaded object and mark file as uploaded."""
    workspace, _, _ = await _create_workspace_project_stage(db_session)
    file = await FileService.create_file(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        session=db_session,
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
async def test_confirm_file_upload_raises_for_invalid_metadata(db_session, storage, test_building_laz_path):
    """Service should reject upload confirmation if metadata does not match DB record."""
    workspace, _, _ = await _create_workspace_project_stage(db_session)
    file = await FileService.create_file(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        session=db_session,
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
async def test_confirm_file_upload_raises_if_storage_object_missing(db_session, storage, test_building_shifted_laz_path):
    """Service should fail if DB record exists but object was not uploaded to storage."""
    workspace, _, _ = await _create_workspace_project_stage(db_session)
    file = await FileService.create_file(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_shifted_laz_path),
        ),
        session=db_session,
    )

    with pytest.raises(NotFoundError, match="not uploaded to the storage"):
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
async def test_delete_file_removes_db_entry_and_storage_object(db_session, storage, test_building_ifc_path):
    """Service should delete file from storage and remove database record."""
    workspace, _, _ = await _create_workspace_project_stage(db_session)
    file = await FileService.create_file(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ),
        session=db_session,
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
async def test_clean_up_files_removes_old_pending_and_orphan_storage_files(db_session, storage, test_building_laz_path):
    """Service should clean both stale pending DB files and orphan files in storage."""
    workspace, _, _ = await _create_workspace_project_stage(db_session)
    pending_file = await FileService.create_file(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        session=db_session,
    )

    pending_file.created_at = pending_file.created_at - timedelta(days=2)
    await db_session.flush()

    orphan_key = FileService.create_file_key("orphan-file.laz")
    with test_building_laz_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, orphan_key)

    deleted_count = await FileService.clean_up_files(
        storage=storage,
        session=db_session,
        pending_for_limit=timedelta(hours=1),
    )

    assert deleted_count == 2
    assert await FileRepository.get_by_id(pending_file.id, session=db_session) is None
    assert storage.file_exists(orphan_key) is False


@pytest.mark.asyncio
async def test_create_point_cloud_creates_cloud_and_file(db_session, test_building_laz_path):
    """Service should create point cloud entry together with its file."""
    workspace, _, stage = await _create_workspace_project_stage(db_session)

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
async def test_create_bim_creates_bim_and_file(db_session, test_building_ifc_path):
    """Service should create BIM entry together with its file."""
    workspace, project, _ = await _create_workspace_project_stage(db_session)

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


@pytest.mark.asyncio
async def test_save_converted_point_cloud_file_creates_related_records(db_session, test_building_laz_path, test_building_shifted_laz_path):
    """Service should save converted point cloud file and create relation record."""
    workspace, _, stage = await _create_workspace_project_stage(db_session)
    point_cloud, _ = await FileService.create_point_cloud(
        point_cloud_type=PointCloudType.SCAN,
        file_data=FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        session=db_session,
        stage_id=stage.id,
    )

    await FileService.save_converted_point_cloud_file(
        point_cloud.id,
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_shifted_laz_path),
        ),
        session=db_session,
    )

    records = await PointCloudConvertedRepository.get_by_point_cloud_id(
        point_cloud.id,
        session=db_session,
    )
    assert len(records) == 1

    converted_files = await FileService.get_converted_point_cloud_files(
        point_cloud.id,
        session=db_session,
    )
    assert len(converted_files) == 1
    assert converted_files[0].filename == test_building_shifted_laz_path.name


@pytest.mark.asyncio
async def test_save_converted_bim_file_creates_plan_point_cloud(db_session, test_building_ifc_path, test_building_laz_path):
    """Service should save converted BIM output and attach created plan point cloud to BIM."""
    workspace, project, _ = await _create_workspace_project_stage(db_session)
    bim, _ = await FileService.create_bim(
        bim_data=BIMModel(project_id=project.id, file_id=uuid.uuid4()),
        file_data=FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ),
        session=db_session,
    )

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

    point_cloud = await PointCloudRepository.get_by_id(saved_bim.point_cloud_id, session=db_session)
    assert point_cloud is not None
    assert point_cloud.type == PointCloudType.PLAN
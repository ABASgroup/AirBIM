"""Tests for file-related repositories."""
import pytest

from models.file import FileStatus
from models.workspace import WorkspaceType
from repositories.files import FileRepository
from repositories.workspace import WorkspaceRepository
from schemas.file import FileModel
from schemas.workspace import WorkspaceModel
from services.file import FileService


async def _create_workspace(db_session):
    """Create workspace required by files.workspace_id foreign key."""
    return await WorkspaceRepository.create(
        WorkspaceModel(name="Repository files workspace", type=WorkspaceType.TEAM),
        session=db_session,
    )


@pytest.mark.asyncio
async def test_file_repository_create_and_get_by_key(db_session, test_building_ifc_path):
    """Repository should persist file entry and fetch it back by key."""
    workspace = await _create_workspace(db_session)
    file_payload = FileService.collect_file_data(test_building_ifc_path)
    file_data = FileModel(
        workspace_id=workspace.id,
        **file_payload,
    )

    created_file = await FileRepository.create(file_data, session=db_session)
    assert created_file.id is not None
    assert created_file.status == FileStatus.PENDING

    fetched_file = await FileRepository.get_by_key(created_file.key, session=db_session)
    assert fetched_file is not None
    assert fetched_file.id == created_file.id
    assert fetched_file.filename == test_building_ifc_path.name
    assert fetched_file.size == test_building_ifc_path.stat().st_size


@pytest.mark.asyncio
async def test_file_repository_get_file_by_metadata(db_session, test_building_laz_path):
    """Repository should fetch file by exact metadata."""
    workspace = await _create_workspace(db_session)
    file_payload = FileService.collect_file_data(test_building_laz_path)
    file_data = FileModel(
        workspace_id=workspace.id,
        **file_payload,
    )

    created_file = await FileRepository.create(file_data, session=db_session)

    fetched_file = await FileRepository.get_file_by_metadata(
        filename=created_file.filename,
        content_type=created_file.content_type,
        size=created_file.size,
        session=db_session,
    )

    assert fetched_file is not None
    assert fetched_file.id == created_file.id
    assert fetched_file.key == created_file.key


@pytest.mark.asyncio
async def test_file_repository_update_status(db_session, test_building_shifted_laz_path):
    """Repository should update file status in place."""
    workspace = await _create_workspace(db_session)
    file_payload = FileService.collect_file_data(test_building_shifted_laz_path)
    file_data = FileModel(
        workspace_id=workspace.id,
        **file_payload,
    )

    created_file = await FileRepository.create(file_data, session=db_session)
    assert created_file.status == FileStatus.PENDING

    updated_file = await FileRepository.update_status(
        created_file,
        FileStatus.UPLOADED,
        session=db_session,
    )

    assert updated_file.status == FileStatus.UPLOADED

    fetched_file = await FileRepository.get_by_id(created_file.id, session=db_session)
    assert fetched_file is not None
    assert fetched_file.status == FileStatus.UPLOADED


@pytest.mark.asyncio
async def test_file_repository_get_by_status_returns_matching_files(db_session, test_building_ifc_path, test_building_laz_path):
    """Repository should return files filtered by status."""
    workspace = await _create_workspace(db_session)
    first_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ),
        session=db_session,
    )
    second_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ),
        session=db_session,
    )

    await FileRepository.update_status(second_file, FileStatus.UPLOADED, session=db_session)

    pending_files = await FileRepository.get_by_status(FileStatus.PENDING, session=db_session)
    uploaded_files = await FileRepository.get_by_status(FileStatus.UPLOADED, session=db_session)

    assert [file.id for file in pending_files] == [first_file.id]
    assert [file.id for file in uploaded_files] == [second_file.id]

"""Tests for file-related repositories."""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.file import FileStatus

from repositories.files import (
    BIMRepository,
    FileRepository,
    PointCloudConvertedRepository,
    PointCloudRepository,
)

from schemas.file import (
    BIMModel,
    FileModel,
    PointCloudConvertedModel,
    PointCloudModel,
)

from services.file import FileService

from tests.helpers import create_test_project, create_test_workspace


@pytest.mark.asyncio
async def test_file_repository_create_and_get_by_key(
    db_session: AsyncSession, test_building_ifc_path: Path
) -> None:
    """Repository should persist file entry and fetch it back by key."""
    workspace = await create_test_workspace(db_session)
    file_payload = FileService.collect_file_data(test_building_ifc_path)
    file_data = FileModel(
        workspace_id=workspace.id,
        **file_payload,
    ).model_dump(exclude_unset=True)

    created_file = await FileRepository.create(file_data, session=db_session)
    assert created_file.id is not None
    assert created_file.status == FileStatus.PENDING

    fetched_file = await FileRepository.get_by_key(created_file.key, session=db_session)
    assert fetched_file is not None
    assert fetched_file.id == created_file.id
    assert fetched_file.filename == test_building_ifc_path.name
    assert fetched_file.size == test_building_ifc_path.stat().st_size


@pytest.mark.asyncio
async def test_file_repository_get_file_by_metadata(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Repository should fetch file by exact metadata."""
    workspace = await create_test_workspace(db_session)
    file_payload = FileService.collect_file_data(test_building_laz_path)
    file_data = FileModel(
        workspace_id=workspace.id,
        **file_payload,
    ).model_dump(exclude_unset=True)

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
async def test_file_repository_update_status(
    db_session: AsyncSession, test_building_shifted_laz_path: Path
) -> None:
    """Repository should update file status in place."""
    workspace = await create_test_workspace(db_session)
    file_payload = FileService.collect_file_data(test_building_shifted_laz_path)
    file_data = FileModel(
        workspace_id=workspace.id,
        **file_payload,
    ).model_dump(exclude_unset=True)

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
async def test_file_repository_get_by_status_returns_matching_files(
    db_session: AsyncSession, test_building_ifc_path: Path, test_building_laz_path: Path
) -> None:
    """Repository should return files filtered by status."""
    workspace = await create_test_workspace(db_session)
    first_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )
    second_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    await FileRepository.update_status(
        second_file, FileStatus.UPLOADED, session=db_session
    )

    pending_files = await FileRepository.get_by_status(
        FileStatus.PENDING, session=db_session
    )
    uploaded_files = await FileRepository.get_by_status(
        FileStatus.UPLOADED, session=db_session
    )

    assert [file.id for file in pending_files] == [first_file.id]
    assert [file.id for file in uploaded_files] == [second_file.id]


@pytest.mark.asyncio
async def test_file_repository_get_all_keys_returns_all_file_keys(
    db_session: AsyncSession, test_building_ifc_path: Path, test_building_laz_path: Path
) -> None:
    """Repository should return all file keys."""
    workspace = await create_test_workspace(db_session)
    first_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )
    second_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    all_keys = await FileRepository.get_all_keys(session=db_session)

    assert set(all_keys) == {first_file.key, second_file.key}


@pytest.mark.asyncio
async def test_file_repository_create_persists_pending_file(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Service should create a pending file entry in the database."""
    workspace = await create_test_workspace(db_session)

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
async def test_bim_repository_create_and_get_by_project_and_file_id(
    db_session: AsyncSession, test_building_ifc_path: Path
) -> None:
    """Repository should return all file keys."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace.id)

    bim_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    bim = BIMModel(
        project_id=project.id,
        file_id=bim_file.id,
    ).model_dump(exclude_unset=True)

    created_bim = await BIMRepository.create(bim, session=db_session)
    assert created_bim.id is not None, "Created BIM should have an id"
    assert (
        created_bim.project_id == project.id
    ), "BIM should be created with correct project_id"
    assert (
        created_bim.file_id == bim_file.id
    ), "BIM should be created with correct project_id and file_id"

    fetched_bim = await BIMRepository.get_by_project_id(project.id, session=db_session)
    assert fetched_bim is not None, "BIM should be fetched by project_id"
    assert (
        fetched_bim.id == created_bim.id
    ), "Fetched BIM should have the same id as created"

    fetched_bim = await BIMRepository.get_by_file_id(bim_file.id, session=db_session)
    assert fetched_bim is not None, "BIM should be fetched by file_id"
    assert (
        fetched_bim.id == created_bim.id
    ), "Fetched BIM should have the same id as created"


@pytest.mark.asyncio
async def test_bim_repository_set_point_cloud(
    db_session: AsyncSession, test_building_ifc_path: Path, test_building_laz_path: Path
) -> None:
    """Repository should set point cloud for BIM."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace.id)

    point_cloud_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    bim_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_ifc_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    point_cloud = PointCloudModel(
        file_id=point_cloud_file.id,
    ).model_dump(exclude_unset=True)

    bim = BIMModel(
        project_id=project.id,
        file_id=bim_file.id,
    ).model_dump(exclude_unset=True)

    created_point_cloud = await PointCloudRepository.create(
        point_cloud, session=db_session
    )
    created_bim = await BIMRepository.create(bim, session=db_session)

    updated_bim = await BIMRepository.set_point_cloud(
        created_bim, created_point_cloud.id, session=db_session
    )
    assert (
        updated_bim.point_cloud_id == created_point_cloud.id
    ), "BIM should be updated with correct point cloud id"

    fetched_bim = await BIMRepository.get_by_project_id(project.id, session=db_session)
    assert fetched_bim is not None, "BIM should be fetched by project_id"
    assert (
        fetched_bim.point_cloud_id == created_point_cloud.id
    ), "Fetched BIM should have the same point cloud id as updated"


@pytest.mark.asyncio
async def test_point_cloud_repository_create_get_by_file_id(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Repository should fetch point cloud by file ID."""
    workspace = await create_test_workspace(db_session)

    point_cloud_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    point_cloud = PointCloudModel(
        file_id=point_cloud_file.id,
    ).model_dump(exclude_unset=True)

    created_point_cloud = await PointCloudRepository.create(
        point_cloud, session=db_session
    )
    assert created_point_cloud.id is not None, "Created point cloud should have an id"
    assert (
        created_point_cloud.file_id == point_cloud_file.id
    ), "Point cloud should be created with correct file_id"

    fetched_point_cloud = await PointCloudRepository.get_by_file_id(
        point_cloud_file.id, session=db_session
    )
    assert fetched_point_cloud is not None, "Point cloud should be fetched by file_id"
    assert (
        fetched_point_cloud.id == created_point_cloud.id
    ), "Fetched point cloud should have the same id as created"


@pytest.mark.asyncio
async def test_point_cloud_converted_repository_create_and_get_by_point_cloud_id(
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_building_shifted_laz_path: Path,
) -> None:
    """Repository should create point cloud converted entry and fetch it by point cloud ID."""
    workspace = await create_test_workspace(db_session)

    point_cloud_file = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    point_cloud = PointCloudModel(
        file_id=point_cloud_file.id,
    ).model_dump(exclude_unset=True)

    created_point_cloud = await PointCloudRepository.create(
        point_cloud, session=db_session
    )

    converted_file_1 = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_laz_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )
    converted_file_2 = await FileRepository.create(
        FileModel(
            workspace_id=workspace.id,
            **FileService.collect_file_data(test_building_shifted_laz_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )

    for converted_file in [converted_file_1, converted_file_2]:
        point_cloud_converted = PointCloudConvertedModel(
            point_cloud_id=created_point_cloud.id,
            file_id=converted_file.id,
        ).model_dump(exclude_unset=True)

        created_converted = await PointCloudConvertedRepository.create(
            point_cloud_converted, session=db_session
        )
        assert (
            created_converted.id is not None
        ), "Created point cloud converted should have an id"
        assert (
            created_converted.point_cloud_id == created_point_cloud.id
        ), "Point cloud converted should be created with correct point cloud id"
        assert (
            created_converted.file_id == converted_file.id
        ), "Point cloud converted should be created with correct file id"

    fetched_converted = await PointCloudConvertedRepository.get_by_point_cloud_id(
        created_point_cloud.id, session=db_session
    )
    assert (
        len(fetched_converted) == 2
    ), "There should be 2 converted point clouds fetched by point cloud id as 2 were created"
    for converted in fetched_converted:
        assert (
            converted is not None
        ), "Point cloud converted should be fetched by point cloud id"
        assert (
            converted.point_cloud_id == created_point_cloud.id
        ), "Fetched point cloud converted should have the same point cloud id as created"

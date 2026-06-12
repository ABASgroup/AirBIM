"""Tests for Recording result Repository."""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.recording_result import RecordingResultRepository

from schemas.recording_result import RecordingResultModel, RecordingResultType

from tests.helpers import (
    create_test_file,
    create_test_point_cloud,
    create_test_project,
    create_test_workspace,
)


@pytest.mark.asyncio
async def test_recording_result_repository_create(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Test the creation of a recording result."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace.id)

    point_cloud_file = await create_test_file(
        db_session, workspace.id, test_building_laz_path
    )

    created_point_cloud = await create_test_point_cloud(db_session, point_cloud_file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"key": "value"},
        type=RecordingResultType.PROGRESS,
        point_cloud_id=created_point_cloud.id,
    ).model_dump(exclude_unset=True)

    recording_result = await RecordingResultRepository.create(
        recording_result_data, db_session
    )

    assert recording_result is not None
    assert recording_result.project_id == project.id
    assert recording_result.type == RecordingResultType.PROGRESS
    assert recording_result.point_cloud_id == created_point_cloud.id


@pytest.mark.asyncio
async def test_recording_result_repository_get_by_project_id(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Test getting recording results by project id."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace.id)

    point_cloud_file = await create_test_file(
        db_session, workspace.id, test_building_laz_path
    )
    created_point_cloud = await create_test_point_cloud(db_session, point_cloud_file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"key": "value"},
        point_cloud_id=created_point_cloud.id,
        type=RecordingResultType.PROGRESS,
    ).model_dump(exclude_unset=True)

    created_result = await RecordingResultRepository.create(
        recording_result_data, db_session
    )

    results = await RecordingResultRepository.get_by_project_id(project.id, db_session)

    assert len(results) == 1
    assert results[0].id == created_result.id
    assert results[0].project_id == project.id
    assert results[0].type == RecordingResultType.PROGRESS


@pytest.mark.asyncio
async def test_recording_result_repository_add_and_get_photos(
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_photo_1_jpg_path: Path,
    test_photo_2_jpg_path: Path,
) -> None:
    """Test adding photos to a recording result."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace.id)

    point_cloud_file = await create_test_file(
        db_session, workspace.id, test_building_laz_path
    )
    created_point_cloud = await create_test_point_cloud(db_session, point_cloud_file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"key": "value"},
        point_cloud_id=created_point_cloud.id,
        type=RecordingResultType.PROGRESS,
    ).model_dump(exclude_unset=True)

    recording_result = await RecordingResultRepository.create(
        recording_result_data, db_session
    )

    photo_file_1 = await create_test_file(
        db_session, workspace.id, test_photo_1_jpg_path
    )
    photo_file_2 = await create_test_file(
        db_session, workspace.id, test_photo_2_jpg_path
    )

    await RecordingResultRepository.add_photos(
        recording_result, [photo_file_1, photo_file_2], db_session
    )

    photos = await RecordingResultRepository.get_photos(recording_result, db_session)

    assert photos is not None
    assert len(photos) == 2
    assert any(photo.id == photo_file_1.id for photo in photos)
    assert any(photo.id == photo_file_2.id for photo in photos)


@pytest.mark.asyncio
async def test_recording_result_repository_add_pdf_report(
    db_session: AsyncSession, test_building_laz_path: Path, test_report_pdf_path: Path
) -> None:
    """Test adding a PDF report to a recording result."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace.id)

    point_cloud_file = await create_test_file(
        db_session, workspace.id, test_building_laz_path
    )

    created_point_cloud = await create_test_point_cloud(db_session, point_cloud_file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"key": "value"},
        point_cloud_id=created_point_cloud.id,
        type=RecordingResultType.PROGRESS,
    ).model_dump(exclude_unset=True)

    recording_result = await RecordingResultRepository.create(
        recording_result_data, db_session
    )

    pdf_report_file = await create_test_file(
        db_session, workspace.id, test_report_pdf_path
    )

    await RecordingResultRepository.add_pdf_report(
        recording_result, pdf_report_file, db_session
    )

    assert recording_result.pdf_report_id == pdf_report_file.id


@pytest.mark.asyncio
async def test_recording_result_repository_add_excel_report(
    db_session: AsyncSession, test_building_laz_path: Path, test_report_xlsx_path: Path
) -> None:
    """Test adding an Excel report to a recording result."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace.id)

    point_cloud_file = await create_test_file(
        db_session, workspace.id, test_building_laz_path
    )
    created_point_cloud = await create_test_point_cloud(db_session, point_cloud_file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"key": "value"},
        point_cloud_id=created_point_cloud.id,
        type=RecordingResultType.PROGRESS,
    ).model_dump(exclude_unset=True)

    recording_result = await RecordingResultRepository.create(
        recording_result_data, db_session
    )

    excel_report_file = await create_test_file(
        db_session, workspace.id, test_report_xlsx_path
    )

    await RecordingResultRepository.add_excel_report(
        recording_result, excel_report_file, db_session
    )

    assert recording_result.xlsx_report_id == excel_report_file.id

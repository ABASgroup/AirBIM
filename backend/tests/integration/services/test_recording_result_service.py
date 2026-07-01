"""Tests for Recording result Service."""

from pathlib import Path
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError

from schemas.file import FileModel
from schemas.recording_result import RecordingResultModel, RecordingResultType

from services.file import FileService
from services.recording_result import RecordingResultService

from tests.helpers import (
    create_test_file,
    create_test_point_cloud,
    create_test_project,
    create_test_workspace,
)


@pytest.mark.asyncio
async def test_create_recording_result(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Service should create recording result."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"example": "data"},
        point_cloud_id=point_cloud.id,
        type=RecordingResultType.PLAN_FACT,
    )
    recording_result = await RecordingResultService.create_recording_result(
        recording_result_data, session=db_session
    )

    assert recording_result.id is not None
    assert recording_result.project_id == project.id
    assert recording_result.point_cloud_id == point_cloud.id
    assert recording_result.type == RecordingResultType.PLAN_FACT


@pytest.mark.asyncio
async def test_get_recording_result_for_project(
    db_session: AsyncSession,
    test_building_laz_path: Path,
    test_building_shifted_laz_path: Path,
) -> None:
    """Service should return recording results for project."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"example": "data"},
        point_cloud_id=point_cloud.id,
        type=RecordingResultType.PLAN_FACT,
    )
    created_result_1 = await RecordingResultService.create_recording_result(
        recording_result_data, session=db_session
    )

    results = await RecordingResultService.get_recording_results_for_project(
        project.id, session=db_session
    )

    assert len(results) == 1
    assert created_result_1 in results

    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_shifted_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"example": "data"},
        point_cloud_id=point_cloud.id,
        type=RecordingResultType.PLAN_FACT,
    )
    created_result_2 = await RecordingResultService.create_recording_result(
        recording_result_data, session=db_session
    )

    results = await RecordingResultService.get_recording_results_for_project(
        project.id, session=db_session
    )

    assert len(results) == 2
    assert created_result_1 in results
    assert created_result_2 in results


@pytest.mark.asyncio
async def test_get_recording_result(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Service should return recording result by id."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"example": "data"},
        point_cloud_id=point_cloud.id,
        type=RecordingResultType.PLAN_FACT,
    )
    created_result = await RecordingResultService.create_recording_result(
        recording_result_data, session=db_session
    )

    result = await RecordingResultService.get_recording_result(
        created_result.id, session=db_session
    )

    assert result == created_result


@pytest.mark.asyncio
async def test_get_nonexistent_recording_result(db_session: AsyncSession) -> None:
    """Service should raise NotFoundError if recording result does not exist."""
    with pytest.raises(NotFoundError):
        await RecordingResultService.get_recording_result(
            uuid.uuid4(), session=db_session
        )


@pytest.mark.asyncio
async def test_delete_recording_result(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Service should delete recording result."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"example": "data"},
        point_cloud_id=point_cloud.id,
        type=RecordingResultType.PLAN_FACT,
    )
    created_result = await RecordingResultService.create_recording_result(
        recording_result_data, session=db_session
    )

    deleted_result = await RecordingResultService.delete_recording_result(
        created_result.id, session=db_session
    )

    assert deleted_result == created_result

    with pytest.raises(NotFoundError):
        await RecordingResultService.get_recording_result(
            created_result.id, session=db_session
        )


@pytest.mark.asyncio
async def test_create_and_get_excel_report(
    db_session: AsyncSession, test_building_laz_path: Path, test_report_xlsx_path: Path
) -> None:
    """Service should create and return excel report for recording result."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"example": "data"},
        point_cloud_id=point_cloud.id,
        type=RecordingResultType.PLAN_FACT,
    )
    created_result = await RecordingResultService.create_recording_result(
        recording_result_data, session=db_session
    )

    file_payload = FileService.collect_file_data(test_report_xlsx_path)
    report_file_data = FileModel(
        workspace_id=workspace.id,
        **file_payload,
    )
    await RecordingResultService.create_excel_report(
        created_result.id, report_file_data, session=db_session
    )

    result = await RecordingResultService.get_recording_result(
        created_result.id, session=db_session
    )

    assert result.xlsx_report is not None
    assert result.xlsx_report.filename == test_report_xlsx_path.name


@pytest.mark.asyncio
async def test_get_nonexistent_excel_report(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Service should raise NotFoundError if recording result doesn't exist when creating report."""
    with pytest.raises(NotFoundError):
        file_payload = FileService.collect_file_data(test_building_laz_path)
        report_file_data = FileModel(
            workspace_id=uuid.uuid4(),
            **file_payload,
        )
        await RecordingResultService.create_excel_report(
            uuid.uuid4(), report_file_data, session=db_session
        )


@pytest.mark.asyncio
async def test_create_and_get_pdf_report(
    db_session: AsyncSession, test_building_laz_path: Path, test_report_pdf_path: Path
) -> None:
    """Service should create and return PDF report for recording result."""
    workspace = await create_test_workspace(db_session)
    project = await create_test_project(db_session, workspace_id=workspace.id)
    file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    point_cloud = await create_test_point_cloud(db_session, file_id=file.id)

    recording_result_data = RecordingResultModel(
        project_id=project.id,
        data={"example": "data"},
        point_cloud_id=point_cloud.id,
        type=RecordingResultType.PLAN_FACT,
    )
    created_result = await RecordingResultService.create_recording_result(
        recording_result_data, session=db_session
    )

    file_payload = FileService.collect_file_data(test_report_pdf_path)
    report_file_data = FileModel(
        workspace_id=workspace.id,
        **file_payload,
    )
    await RecordingResultService.create_pdf_report(
        created_result.id, report_file_data, session=db_session
    )

    result = await RecordingResultService.get_recording_result(
        created_result.id, session=db_session
    )

    assert result.pdf_report is not None
    assert result.pdf_report.filename == test_report_pdf_path.name


@pytest.mark.asyncio
async def test_get_nonexistent_pdf_report(
    db_session: AsyncSession, test_building_laz_path: Path
) -> None:
    """Service should raise NotFoundError if recording result doesn't exist when creating report."""
    with pytest.raises(NotFoundError):
        file_payload = FileService.collect_file_data(test_building_laz_path)
        report_file_data = FileModel(
            workspace_id=uuid.uuid4(),
            **file_payload,
        )
        await RecordingResultService.create_pdf_report(
            uuid.uuid4(), report_file_data, session=db_session
        )

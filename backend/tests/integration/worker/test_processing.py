"""Integration tests for Celery processing worker tasks."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import session_maker
from infrastructure.storage import Storage

from models.workspace import WorkspaceType

from repositories.files import BIMRepository, FileRepository
from repositories.recording_result import RecordingResultRepository

from schemas.file import FileStatus, PointCloudType
from schemas.recording_result import RecordingResultType
from schemas.task import TaskType

from services.file import FileService
from services.recording_result import RecordingResultService

from tasks.processing import (
    check_progress,
    compare_scan_and_plan,
    convert_bim_to_point_cloud,
    create_recording_result_pdf_report,
    generate_bim_preview,
)

from tests.helpers import (
    create_test_bim,
    create_test_file,
    create_test_point_cloud,
    create_test_project,
    create_test_recording_result,
    create_test_stage,
    create_test_task,
    create_test_workspace,
    wait_until,
)


@pytest.mark.asyncio
async def test_convert_bim_to_point_cloud(
    db_session: AsyncSession, storage: Storage, test_building_ifc_path: Path
) -> None:
    """Processing worker should generate point cloud (LAZ) from BIM (IFC) file."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.TEAM
    )
    project = await create_test_project(db_session, workspace.id)
    file = await create_test_file(db_session, workspace.id, test_building_ifc_path)
    bim = await create_test_bim(db_session, project.id, file.id)

    bim_file_key = FileService.create_file_key(test_building_ifc_path.name)
    file.key = bim_file_key
    storage.upload_file_locally(bim_file_key, str(test_building_ifc_path))

    created_task = await create_test_task(
        db_session,
        workspace_id=workspace.id,
        entity_id=bim.id,
        task_type=TaskType.CONVERTING_BIM,
    )

    await db_session.commit()

    convert_bim_to_point_cloud.delay(  # pyright: ignore[reportFunctionMemberAccess]
        bim.id, created_task.id
    )

    async def assert_converted_bim_generated() -> None:
        async with session_maker() as session:
            new_bim = await FileService.get_bim_by_project_id(project.id, session)
            assert new_bim.point_cloud_id is not None
            assert new_bim.file_id == file.id

            point_cloud = await FileService.get_point_cloud(
                new_bim.point_cloud_id, session
            )
            assert point_cloud.file_id is not None
            assert point_cloud.type == PointCloudType.PLAN

            point_cloud_file = await FileService.get_file(point_cloud.file_id, session)
            assert point_cloud_file.size > 0
            assert point_cloud_file.status == FileStatus.UPLOADED
            assert point_cloud_file.key is not None
            assert point_cloud_file.filename is not None
            assert point_cloud_file.filename.endswith("laz")

            assert storage.file_exists(point_cloud_file.key)

    await wait_until(assert_converted_bim_generated)


@pytest.mark.asyncio
async def test_generate_bim_preview(
    db_session: AsyncSession, storage: Storage, test_building_ifc_path: Path
) -> None:
    """Processing worker should generate preview image from BIM (IFC) file."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.TEAM
    )
    project = await create_test_project(db_session, workspace.id)
    file = await create_test_file(db_session, workspace.id, test_building_ifc_path)
    bim = await create_test_bim(db_session, project.id, file.id)

    bim_file_key = FileService.create_file_key(test_building_ifc_path.name)
    file.key = bim_file_key
    storage.upload_file_locally(bim_file_key, str(test_building_ifc_path))

    await db_session.commit()

    generate_bim_preview.delay(bim.id)  # pyright: ignore[reportFunctionMemberAccess]

    async def assert_preview_generated() -> None:
        async with session_maker() as session:
            updated_bim = await FileService.get_bim_by_project_id(
                project.id, session
            )
            assert updated_bim.preview_file_id is not None
            preview_file = await FileService.get_file(
                updated_bim.preview_file_id, session
            )
            assert preview_file.size > 0
            assert preview_file.status == FileStatus.UPLOADED
            assert preview_file.content_type.startswith("image/")
            assert storage.file_exists(preview_file.key)

    await wait_until(assert_preview_generated)


@pytest.mark.asyncio
async def test_compare_scan_and_plan(
    db_session: AsyncSession,
    storage: Storage,
    test_building_laz_path: Path,
    test_building_shifted_laz_path: Path,
) -> None:
    """Processing worker should generate point cloud from scan and plan comparison."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.TEAM
    )
    project = await create_test_project(db_session, workspace.id)
    file_plan = await create_test_file(db_session, workspace.id, test_building_laz_path)

    bim = await create_test_bim(db_session, project.id, file_plan.id)
    point_cloud_plan = await create_test_point_cloud(db_session, file_plan.id)
    bim = await BIMRepository.set_point_cloud(bim, point_cloud_plan.id, db_session)
    point_cloud_plan.type = PointCloudType.PLAN
    file_plan.key = FileService.create_file_key(test_building_laz_path.name)

    await db_session.commit()
    storage.upload_file_locally(file_plan.key, str(test_building_laz_path))

    stage = await create_test_stage(db_session, project.id)
    file_scan = await create_test_file(
        db_session, workspace.id, test_building_shifted_laz_path
    )
    point_cloud_scan = await create_test_point_cloud(db_session, file_scan.id)
    point_cloud_scan.stage_id = stage.id
    point_cloud_scan.type = PointCloudType.SCAN
    file_scan.key = FileService.create_file_key(test_building_shifted_laz_path.name)

    await db_session.commit()
    storage.upload_file_locally(file_scan.key, str(test_building_shifted_laz_path))

    created_task = await create_test_task(
        db_session,
        workspace_id=workspace.id,
        entity_id=stage.id,
        task_type=TaskType.COMPARING_PLAN_FACT,
    )

    await db_session.commit()

    compare_scan_and_plan.delay(  # pyright: ignore[reportFunctionMemberAccess]
        stage.id, created_task.id
    )

    async def assert_scan_and_plan_comparison_generated() -> None:
        async with session_maker() as session:
            recording_result = (
                await RecordingResultService.get_recording_results_for_project(
                    project.id, session
                )
            )
            assert len(recording_result) != 0
            assert recording_result[0].point_cloud_id is not None
            assert recording_result[0].type == RecordingResultType.PLAN_FACT

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
async def test_check_progress(
    db_session: AsyncSession,
    storage: Storage,
    test_building_laz_path: Path,
    test_building_shifted_laz_path: Path,
) -> None:
    """Processing worker should generate point cloud from check progress."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.TEAM
    )
    project = await create_test_project(db_session, workspace.id)

    stage_before = await create_test_stage(
        db_session, project.id, datetime(2000, 1, 1, tzinfo=timezone.utc)
    )
    file_before = await create_test_file(
        db_session, workspace.id, test_building_laz_path
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
        db_session, workspace.id, test_building_shifted_laz_path
    )
    point_cloud_after = await create_test_point_cloud(db_session, file_after.id)
    point_cloud_after.stage_id = stage_after.id
    point_cloud_after.type = PointCloudType.SCAN
    file_after.key = FileService.create_file_key(test_building_shifted_laz_path.name)
    storage.upload_file_locally(file_after.key, str(test_building_shifted_laz_path))

    created_task = await create_test_task(
        db_session,
        workspace_id=workspace.id,
        entity_id=project.id,
        task_type=TaskType.CHECKING_PROGRESS,
    )

    await db_session.commit()

    check_progress.delay(  # pyright: ignore[reportFunctionMemberAccess]
        stage_before.id, stage_after.id, created_task.id
    )

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
async def test_create_recording_result_pdf_report(
    db_session: AsyncSession,
    storage: Storage,
    test_building_laz_path: Path,
    test_photo_1_jpg_path: Path,
    test_photo_2_jpg_path: Path,
) -> None:
    """Default worker should generate and store pdf report for recording result."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.TEAM
    )
    project = await create_test_project(db_session, workspace.id)
    file = await create_test_file(db_session, workspace.id, test_building_laz_path)
    file.key = FileService.create_file_key(test_building_laz_path.name)
    storage.upload_file_locally(file.key, str(test_building_laz_path))
    point_cloud = await create_test_point_cloud(db_session, file.id)

    test_data = {
        "key1": "value",
        "key2": 123,
        "key3": [1, 2, 3],
    }

    recording_type = RecordingResultType.PROGRESS

    recording_result = await create_test_recording_result(
        db_session,
        project.id,
        point_cloud.id,
        data=test_data,
        recording_type=recording_type,
    )

    photo_file_1 = await create_test_file(
        db_session, workspace.id, test_photo_1_jpg_path
    )
    photo_file_1.key = FileService.create_file_key(test_photo_1_jpg_path.name)
    storage.upload_file_locally(photo_file_1.key, str(test_photo_1_jpg_path))

    photo_file_2 = await create_test_file(
        db_session, workspace.id, test_photo_2_jpg_path
    )
    photo_file_2.key = FileService.create_file_key(test_photo_2_jpg_path.name)
    storage.upload_file_locally(photo_file_2.key, str(test_photo_2_jpg_path))

    await RecordingResultRepository.add_photos(
        recording_result, photo_files=[photo_file_1, photo_file_2], session=db_session
    )

    created_task = await create_test_task(
        db_session,
        workspace_id=workspace.id,
        entity_id=point_cloud.id,
        task_type=TaskType.CHECKING_PROGRESS,
    )

    await db_session.commit()

    create_recording_result_pdf_report.delay(  # pyright: ignore[reportFunctionMemberAccess]
        recording_result.id, created_task.id
    )

    async def assert_report_generated() -> None:
        async with session_maker() as session:
            record = await RecordingResultRepository.get_by_id(
                recording_result.id, session, relations=["pdf_report"]
            )
            assert record is not None
            assert record.pdf_report is not None

            pdf_file = await FileRepository.get_by_id(record.pdf_report_id, session)
            assert pdf_file is not None
            assert pdf_file.filename is not None
            assert pdf_file.filename.endswith(recording_type + "_report.pdf")
            assert pdf_file.key.endswith(".pdf")
            assert pdf_file.size > 0
            assert pdf_file.status == FileStatus.UPLOADED
            assert storage.file_exists(pdf_file.key)

    await wait_until(assert_report_generated)

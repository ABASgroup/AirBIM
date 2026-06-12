"""Integration tests for Celery default worker tasks."""

from datetime import timedelta
from pathlib import Path
import uuid

import openpyxl
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import session_maker
from infrastructure.storage import Storage

from models.workspace import WorkspaceType

from repositories.files import FileRepository
from repositories.recording_result import RecordingResultRepository

from schemas.file import FileStatus
from schemas.recording_result import RecordingResultType
from schemas.task import TaskType

from tasks.default import clean_up_files, create_recording_result_excel_report

from tests.helpers import (
    create_test_file,
    create_test_point_cloud,
    create_test_project,
    create_test_recording_result,
    create_test_task,
    create_test_workspace,
    wait_until,
)


@pytest.mark.asyncio
async def test_clean_up_files_task_removes_stale_db_file_and_orphan_storage_file(
    db_session: AsyncSession, storage: Storage, test_building_laz_path: Path
) -> None:
    """Default worker should remove stale pending DB files and orphan objects from storage."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.TEAM
    )
    stale_file = await create_test_file(
        db_session, workspace_id=workspace.id, file_path=test_building_laz_path
    )
    stale_file.created_at = stale_file.created_at - timedelta(days=2)
    await db_session.commit()

    orphan_key = f"{uuid.uuid4()}/{test_building_laz_path.name}"
    with test_building_laz_path.open("rb") as file_obj:
        storage.upload_file_object(file_obj, orphan_key)

    assert storage.file_exists(orphan_key)

    clean_up_files.delay()  # pyright: ignore[reportFunctionMemberAccess]

    async def assert_cleanup_completed() -> None:
        async with session_maker() as session:
            db_file = await FileRepository.get_by_id(stale_file.id, session=session)
            assert db_file is None

        assert storage.file_exists(orphan_key) is False
        assert storage.file_exists(stale_file.key) is False

    await wait_until(assert_cleanup_completed)

    async with session_maker() as session:
        assert not await FileRepository.get_all(session=session)


@pytest.mark.asyncio
async def test_create_recording_result_excel_report(
    db_session: AsyncSession,
    storage: Storage,
    test_building_laz_path: Path,
    tmp_path: Path,
) -> None:
    """Default worker should generate and store excel report for recording result."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.TEAM
    )
    project = await create_test_project(db_session, workspace.id)
    file = await create_test_file(db_session, workspace.id, test_building_laz_path)
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

    created_task = await create_test_task(
        db_session,
        workspace_id=workspace.id,
        entity_id=point_cloud.id,
        task_type=TaskType.CHECKING_PROGRESS,
    )

    await db_session.commit()

    create_recording_result_excel_report.delay(  # pyright: ignore[reportFunctionMemberAccess]
        recording_result.id, created_task.id
    )

    async def assert_report_generated() -> None:
        async with session_maker() as session:
            record = await RecordingResultRepository.get_by_id(
                recording_result.id, session
            )
            assert record is not None
            assert record.xlsx_report is not None

            excel_file = await FileRepository.get_by_id(record.xlsx_report_id, session)
            assert excel_file is not None
            assert excel_file.filename is not None
            assert excel_file.filename.endswith(recording_type + "_report.xlsx")
            assert excel_file.key.endswith(".xlsx")
            assert excel_file.size > 0
            assert excel_file.status == FileStatus.UPLOADED
            assert storage.file_exists(excel_file.key)

            test_excel_path = tmp_path / excel_file.filename
            storage.download_file_locally(excel_file.key, str(test_excel_path))

            workbook = openpyxl.load_workbook(test_excel_path, data_only=True)
            sheet = workbook.active
            assert sheet is not None
            for col in sheet.iter_cols(values_only=True):
                assert len(col) == 2
                assert test_data.get(str(col[0])) is not None
                assert str(test_data.get(str(col[0]))).strip("[]") == str(col[1])

    await wait_until(assert_report_generated)

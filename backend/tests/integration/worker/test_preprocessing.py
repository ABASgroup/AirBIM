"""Integration tests for Celery preprocessing worker tasks."""

import json

import aiofiles
import pytest

from infrastructure.database import session_maker

from models.workspace import WorkspaceType

from schemas.task import TaskType

from services.file import FileService

from tasks.preprocessing import convert_point_cloud_task

from tests.helpers import (
    create_test_file,
    create_test_point_cloud,
    create_test_task,
    create_test_workspace,
    wait_until,
)


@pytest.mark.asyncio
async def test_convert_point_cloud(
    db_session, storage, test_building_laz_path, tmp_path
):
    """Preprocessing worker should generate potree files from LAZ for visualization."""
    workspace = await create_test_workspace(
        db_session, workspace_type=WorkspaceType.TEAM
    )
    file = await create_test_file(db_session, workspace.id, test_building_laz_path)
    point_cloud = await create_test_point_cloud(db_session, file.id)

    point_cloud_file_key = FileService.create_file_key(test_building_laz_path.name)
    file.key = point_cloud_file_key
    storage.upload_file_locally(point_cloud_file_key, test_building_laz_path)

    created_task = await create_test_task(
        db_session,
        workspace_id=workspace.id,
        entity_id=point_cloud.id,
        task_type=TaskType.CONVERTING_POINT_CLOUD,
    )

    await db_session.commit()

    convert_point_cloud_task.delay(point_cloud.id, created_task.id)

    async def assert_converted_point_cloud_generated():
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

            assert files_dict["octree.bin"].size > 0, "octree.bin is empty"
            assert files_dict["hierarchy.bin"].size > 0, "hierarchy.bin is empty"
            assert files_dict["metadata.json"].size > 0, "metadata.json is empty"

            path_to_metadata_json = tmp_path / "metadata.json"
            storage.download_file_locally(
                files_dict["metadata.json"].key, path_to_metadata_json
            )
            async with aiofiles.open(
                path_to_metadata_json, mode="r", encoding="utf-8"
            ) as f:
                content = await f.read()
                metadata = json.loads(content)
            assert "points" in metadata, "metadata.json is missing 'pointsCount'"
            assert (
                metadata["points"] > 0
            ), "Potree converted 0 points. Source file might be corrupted."
            assert (
                "hierarchy" in metadata
            ), "metadata.json is missing hierarchy definition"

    await wait_until(assert_converted_point_cloud_generated)

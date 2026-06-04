import uuid
import tempfile
import os
from models.file import FileStatus
from models.task import TaskStatus
from core.dependencies import get_database_uow, get_storage
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.file import FileService
from services.task import TaskService
from schemas.file import FileModel
from utils.convert import convert_point_cloud
from utils.files import (
    get_all_dir_files,
    clean_path
)


# heavy tasks with long duration must never use database transaction for far too long
# use short transactions
# save artifacts

class ConverterTask(celery_app.Task):
    queue = 'converter'


@celery_app.task(base=ConverterTask, bind=True)
def convert_point_cloud_task(
    self,
    point_cloud_id: uuid.UUID,
    task_id: uuid.UUID,
):
    """Converts point cloud into Potree format."""
    storage = get_storage()

    async def run_task():
        async with get_database_uow() as uow:
            # get task that is being executed
            task = await TaskService.get_task(task_id, session=uow.session)
            # check if it's a step in a process
            current_progress = task.progress
            if current_progress == 0:
                await TaskService.start_task(
                    task_id,
                    celery_task_id=self.request.id,
                    session=uow.session
                )

            # get point cloud
            point_cloud = await FileService.get_point_cloud(point_cloud_id, session=uow.session)
            # check if we already have converted files
            converted_files = await FileService.get_converted_point_cloud_files(point_cloud_id, session=uow.session)
            if len(converted_files):
                # false start up, no actions required
                # don't waste the resources
                print("ALREADY CONVERTED")
                return
            point_cloud_file = await FileService.get_file(point_cloud.file_id, session=uow.session)

            if current_progress == 0:
                current_progress = 50
            else:
                current_progress = 75

            await TaskService.update_task_progress(
                task_id,
                progress=current_progress,
                session=uow.session
            )

        # all in temp_dir will be deleted after its done
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = clean_path(os.path.join(
                tmp_dir, point_cloud_file.filename))
            output_path = clean_path(tmp_dir)

            # download point cloud file
            storage.download_file_locally(
                point_cloud_file.key,
                save_path=str(file_path)
            )

            # convert it and save stated save path
            output_path = convert_point_cloud(
                file_path=str(file_path),
                output_path=str(output_path)
            )

            # all files in the output dir
            file_dir = get_all_dir_files(output_path)

            files: list[FileModel] = []

            for file in file_dir:
                # collect file info
                file_info = FileService.collect_file_data(file)
                # upload to the storage
                storage.upload_file_locally(
                    file_info["key"], str(file_info["path"]))

                # make models
                file_data = FileModel(
                    filename=file_info["filename"],
                    key=file_info["key"],
                    size=file_info["size"],
                    content_type=file_info["content_type"],
                    status=FileStatus.UPLOADED,
                    workspace_id=point_cloud_file.workspace_id
                )

                files.append(file_data)

            # persist converted files and finish task in one short transaction
            async with get_database_uow() as uow:
                for data in files:
                    await FileService.save_converted_point_cloud_file(
                        point_cloud_id,
                        file_data=data,
                        session=uow.session
                    )

                await TaskService.update_task_progress(
                    task_id,
                    progress=100,
                    session=uow.session
                )
                await TaskService.update_task_status(
                    task_id,
                    status=TaskStatus.SUCCEEDED,
                    session=uow.session
                )

    try:
        run_async(run_task())
    except Exception:
        async def mark_failed():
            async with get_database_uow() as uow:
                await TaskService.update_task_status(
                    task_id,
                    status=TaskStatus.FAILED,
                    session=uow.session
                )

        run_async(mark_failed())
        raise

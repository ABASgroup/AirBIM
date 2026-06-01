import os
from uuid import UUID
import tempfile
from models.file import FileStatus
from schemas.file import FileModel
from utils.files import clean_path
from services.recording_result import RecordingResultService
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.file import FileService
from core.dependencies import get_database_uow, get_storage
from utils.report_generation import generate_excel_report


class DefaultTask(celery_app.Task):
    queue = 'default'


@celery_app.task(base=DefaultTask, ignore_result=True)
def clean_up_files():
    """Cleans up files from the storage and the database periodically."""
    async def run_task():
        uow = get_database_uow()
        async with uow:
            files_deleted = await FileService.clean_up_files(
                storage=get_storage(),
                session=uow.session
            )
        return files_deleted
    files_deleted = run_async(run_task())
    # temporary no logger
    print(f"FILE CLEAN UP: FILES DELETED - {files_deleted}")


@celery_app.task(base=DefaultTask)
def create_recording_result_excel_report(recording_result_id: UUID):
    """
    Generates .xlxs report for the recording result and stores it.

    The following report will contain data from the recording result.
    """
    storage = get_storage()

    async def run_task():
        async with get_database_uow() as uow:
            # get result
            recording_result = await RecordingResultService.get_recording_result(
                recording_result_id,
                session=uow.session
            )

            workspace_id = recording_result.project.workspace_id

            # get data
            # it is dict, for real
            data = recording_result.data

        # title for the report
        title = f"{recording_result.type} report".capitalize().replace("_", " ")

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = clean_path(os.path.join(tmp_dir, f"report.xlsx"))

            # generate data
            generate_excel_report(title, data, file_path)

            # collect file data
            file_info = FileService.collect_file_data(file_path)

            # upload to the storage
            storage.upload_file_locally(file_info["key"], str(file_path))

        # save file in the database
        async with get_database_uow() as uow:
            file_data = FileModel(
                filename=file_info["filename"],
                key=file_info["key"],
                size=file_info["size"],
                content_type=file_info["content_type"],
                status=FileStatus.UPLOADED,
                workspace_id=workspace_id
            )
            await RecordingResultService.create_excel_report(
                recording_result_id,
                file_data,
                uow.session
            )
    run_async(run_task())

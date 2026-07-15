import os
from uuid import UUID
import tempfile
from models.file import FileStatus
from models.recording_result import RecordingResultType
from schemas.file import FileModel
from services.recording_result import RecordingResultService
from services.file import FileService
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from core.dependencies import get_database_uow, get_storage
from utils.report_generation import (
    extract_report_sections,
    generate_excel_report,
    translate_recording_result_type,
)
from utils.files import clean_path
from .base_task import BaseCeleryTask


class DefaultTask(BaseCeleryTask):
    abstract = True
    queue = 'default'


@celery_app.task(ignore_result=True)
def clean_up_files(*args, **kwargs) -> str:
    """
    MAINTENANCE TASK: do not use BaseCeleryTask class here, because this is a simple periodic celery task.

    Cleans up files from the storage and the database periodically.

    Define the period in scheduler.

    Returns:
        str: message with the amount of deleted files
    """
    async def run_task():
        uow = get_database_uow()
        async with uow:
            files_deleted = await FileService.clean_up_files(
                storage=get_storage(),
                session=uow.session
            )
        return files_deleted
    files_deleted = run_async(run_task())
    message = f"FILE CLEAN UP: FILES DELETED - {files_deleted}"
    return message


@celery_app.task(
    base=DefaultTask,
)
def create_recording_result_excel_report(recording_result_id: UUID, *args, **kwargs) -> UUID:
    """
    Generates .xlsx report for the recording result and stores it.

    The following report will contain data from the recording result.

    Returns:
        UUID: recording result ID
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
            data = dict(recording_result.data)

            section_specs = {
                "Сведения о проекте": [
                    ("project_name", "Название"),
                    ("project_description", "Описание"),
                ],
            }

            if recording_result.type == RecordingResultType.PROGRESS:
                section_specs.update({
                    "Старый этап": [
                        ("old_stage_name", "Название"),
                        ("old_stage_description", "Описание"),
                        ("old_stage_start_date", "Дата начала"),
                    ],
                    "Новый этап": [
                        ("new_stage_name", "Название"),
                        ("new_stage_description", "Описание"),
                        ("new_stage_start_date", "Дата начала"),
                    ],
                })
            else:
                section_specs.update({
                    "Этап": [
                        ("stage_name", "Название"),
                        ("stage_description", "Описание"),
                        ("stage_start_date", "Дата начала"),
                    ],
                })

            sections, data = extract_report_sections(data, section_specs)

        # title for the report
        title = translate_recording_result_type(recording_result.type)

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = clean_path(os.path.join(
                tmp_dir, f"{recording_result.type}_report.xlsx"))

            # generate report
            generate_excel_report(title, data, file_path, sections=sections)

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
        return recording_result_id
    return run_async(run_task())

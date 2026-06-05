import uuid
from fastapi import APIRouter, Depends
from celery import chain
from core.exceptions import NotFoundError
from infrastructure.storage import Storage
from schemas.stage import StageResponse
from schemas.file import (
    FileDataRequest,
    FileLinkResponse,
    FileModel,
    FileResponse,
)
from schemas.task import TaskModel, TaskResponse
from models.task import TaskType
from services import stage as stage_service
from services.file import FileService
from services.task import TaskService
from core.roles import Permission
from core.dependencies import (
    get_database_uow,
    get_storage,
    DatabaseSessionUOW
)
from api.dependencies import (
    require_stage_permission
)
from tasks.preprocessing import convert_point_cloud_task
from tasks.processing import compare_scan_and_plan, create_recording_result_pdf_report
from tasks.default import create_recording_result_excel_report


router = APIRouter(prefix="/stages/{stage_id}", tags=["project stages"])


@router.get(
    "",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_VIEW))],
)
async def get_stage(stage_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    async with uow:
        stage = await stage_service.get_stage(stage_id, session=uow.session)
    return stage


@router.delete(
    "",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_DELETE))],
)
async def delete_stage(
    stage_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Delete stage and all related data and files.

    Requires permission.
    """
    async with uow:
        stage = await stage_service.delete_stage(stage_id, session=uow.session, storage=storage)
    return stage


@router.post(
    "/clouds/upload",
    response_model=FileLinkResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_UPLOAD))],
)
async def get_point_cloud_upload_link(
    stage_id: uuid.UUID,
    file_data: FileDataRequest,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to upload point cloud file.

    Use this link to upload file.

    Requires permission.
    """
    async with uow:
        stage = await stage_service.get_stage_with_project(stage_id, session=uow.session)
        key = FileService.create_file_key(
            filename=file_data.filename
        )
        url, file = await FileService.generate_point_cloud_upload_link(
            stage_id=stage.id,
            file_data=FileModel(**file_data.model_dump(), key=key,
                                workspace_id=stage.project.workspace_id),
            session=uow.session,
            storage=storage
        )

    response_data = FileLinkResponse(
        file=FileResponse.model_validate(file, from_attributes=True),
        url=url
    )

    return response_data


@router.post(
    "/clouds/converted",
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_DOWNLOAD))],
)
async def get_converted_point_cloud_download_links(
    stage_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
) -> list[str]:
    """
    Get a temporary links to download a converted point cloud file.

    You get multiple links to download for each file.

    Converted clouds are required for efficient visualization via Potree.

    Requires permission.
    """
    async with uow:
        stage = await stage_service.get_stage(stage_id, session=uow.session)
        point_cloud = stage.point_cloud

        if point_cloud is None:
            raise NotFoundError("The stage has no point cloud.")

        files = await FileService.get_converted_point_cloud_files(point_cloud.id, session=uow.session)

    if len(files) == 0:
        raise NotFoundError(
            "No converted files found: point cloud is not yet converted?")

    links = []

    for file in files:
        links.append(storage.get_download_link(file.key))

    return links


@router.post(
    "/compare",
    response_model=TaskResponse
)
async def compare_stage_scan_and_project_plan(
    stage_id: uuid.UUID,
    tolerance: float = 0.05,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Start comparing plan and fact process.

    This long running task will compare your project's plan (BIM) 
    and stage fact (real scan in point cloud).

    The results will be saved and also represented in reports you can access on finish.

    Returns the task of a process you can track later.

    Requires permission.
    """
    async with uow:
        stage = await stage_service.get_stage_with_project(stage_id, session=uow.session)

        task_data = TaskModel(
            entity_id=stage_id,
            entity_type="stage",
            workspace_id=stage.project.workspace_id,
            type=TaskType.COMPARING_PLAN_FACT,
        )
        created_task = await TaskService.create_task(task_data, session=uow.session)

    created_task_id = created_task.id

    # the process is about both comparing and making reports
    # plus converting the cloud we need to
    pipeline = chain(
        compare_scan_and_plan.s(
            task_id=created_task_id, stage_id=stage_id, tolerance=tolerance),
        create_recording_result_excel_report.s(
            task_id=created_task_id),
        create_recording_result_pdf_report.s(
            task_id=created_task_id),
        convert_point_cloud_task.s(task_id=created_task_id)
    )

    task_result = pipeline.apply_async()

    return created_task


@router.post(
    "/progress",
    response_model=TaskResponse
)
async def check_stage_progress(
    stage_id: uuid.UUID,
    tolerance: float = 0.05,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    return "empty"


@router.post(
    "/clouds/{point_cloud_id}/convert",
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_DOWNLOAD))],
)
async def convert_point_cloud(
    stage_id: uuid.UUID,
    point_cloud_id: uuid.UUID,
):
    """TEST ONLY."""
    task = convert_point_cloud_task.delay(point_cloud_id)  # type: ignore
    return f"started: {task.id}"

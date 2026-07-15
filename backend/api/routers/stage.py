import uuid
from fastapi import APIRouter, Depends
from celery import chain
from infrastructure.storage import Storage
from schemas.stage import StageResponse, StageUpdate
from schemas.file import (
    FileDataRequest,
    FileLinkResponse,
    FileModel,
    FileResponse,
    RawScanCleanRequest,
)
from schemas.task import TaskModel, TaskResponse
from models.task import TaskType
from services.stage import StageService
from services.file import FileService
from services.task import TaskService
from core.exceptions import NotFoundError
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
from tasks.processing import (
    compare_scan_and_plan,
    create_recording_result_pdf_report,
    clean_raw_scan_task,
)
from tasks.default import create_recording_result_excel_report
from utils.pointcloud import validate_crop_within_bounds


router = APIRouter(prefix="/stages/{stage_id}", tags=["project stages"])


@router.get(
    "",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_VIEW))],
)
async def get_stage(stage_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    async with uow:
        stage = await StageService.get_stage(stage_id, session=uow.session)
    response = StageResponse(
        id=stage.id,
        created_at=stage.created_at,
        updated_at=stage.updated_at,
        project_id=stage.project_id,
        name=stage.name,
        description=stage.description,
        start_date=stage.start_date,
        point_cloud_id=stage.point_cloud.id if stage.point_cloud else None,
    )
    return response


@router.delete(
    "",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_DELETE))],
)
async def delete_stage(
    stage_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Delete stage and all related data and files.

    Requires permission.
    """
    async with uow:
        stage = await StageService.delete_stage(stage_id, session=uow.session)
    return stage


@router.patch(
    "",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_EDIT))],
)
async def edit_stage(
    stage_id: uuid.UUID,
    stage_data: StageUpdate,
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Edit stage data.

    Requires permission.
    """
    async with uow:
        stage = await StageService.update_stage(stage_id, stage_data, session=uow.session)
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
        stage = await StageService.get_stage(stage_id, session=uow.session)
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
    "/clouds/clean",
    response_model=TaskResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.FILES_UPLOAD))],
)
async def clean_stage_point_cloud(
    stage_id: uuid.UUID,
    clean_data: RawScanCleanRequest,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage),
):
    """
    Clean/crop uploaded stage scan (clean_raw_scan) then convert to Potree.

    Crop bounds must stay within the file's XYZ extent when provided.
    """
    async with uow:
        stage = await StageService.get_stage(stage_id, session=uow.session)
        if stage.point_cloud is None:
            raise NotFoundError("Stage has no point cloud.")

        point_cloud = await FileService.get_point_cloud(
            stage.point_cloud.id, session=uow.session
        )
        point_cloud_file = point_cloud.file

        min_xyz, max_xyz = FileService.get_point_cloud_bounds_from_storage(
            point_cloud_file.key, storage
        )
        validate_crop_within_bounds(
            clean_data.crop_min_xyz,
            clean_data.crop_max_xyz,
            min_xyz,
            max_xyz,
        )

        task_data = TaskModel(
            entity_id=point_cloud.id,
            entity_type="point_cloud",
            workspace_id=stage.project.workspace_id,
            type=TaskType.CONVERTING_POINT_CLOUD,
        )
        created_task = await TaskService.create_task(task_data, session=uow.session)

    config_dict = clean_data.model_dump()
    pipeline = chain(
        # type: ignore[attr-defined]
        clean_raw_scan_task.s(
            point_cloud_id=point_cloud.id,
            task_id=created_task.id,
            config=config_dict,
        ),
        # type: ignore[attr-defined]
        convert_point_cloud_task.s(task_id=created_task.id),
    )
    pipeline.apply_async()

    return created_task


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
        stage = await StageService.get_stage(stage_id, session=uow.session)

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

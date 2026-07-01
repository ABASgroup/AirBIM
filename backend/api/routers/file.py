import uuid
from celery import chain
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from core.exceptions import NotFoundError
from core.roles import Permission
from core.dependencies import (
    get_database_uow,
    get_storage,
    DatabaseSessionUOW
)
from infrastructure.storage import Storage
from models.task import TaskType
from services.file import FileService
from services.task import TaskService
from tasks.processing import convert_bim_to_point_cloud
from tasks.preprocessing import convert_point_cloud_task
from schemas.file import (
    FileDataRequest,
    FileLinkResponse,
    FileResponse,
    FileTaskResponse,
    PointCloudResponse
)
from schemas.task import TaskResponse, TaskModel
from api.dependencies import require_file_permission

router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "/{file_id}/confirm",
    response_model=FileResponse | FileTaskResponse,
    dependencies=[
        Depends(require_file_permission(Permission.FILES_UPLOAD))],
)
async def confirm_upload(
    file_id: uuid.UUID,
    file_data: FileDataRequest,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Confirm finishing uploading a file.

    You can't confirm file upload if file is not uploaded.
    """
    bim_id: uuid.UUID | None = None
    point_cloud_id: uuid.UUID | None = None
    created_task_id: uuid.UUID | None = None

    async with uow:
        file = await FileService.confirm_file_upload(
            file_id=file_id,
            file_data=file_data,
            session=uow.session,
            storage=storage,
        )

        bim = await FileService.get_bim_by_file_id(
            file_id=file.id,
            session=uow.session
        )
        if bim and bim.point_cloud_id is None:
            bim_id = bim.id

        point_cloud = await FileService.get_point_cloud_by_file_id(
            file_id=file.id,
            session=uow.session
        )
        if point_cloud:
            point_cloud_id = point_cloud.id

        # if it's BIM - create one task for the full conversion pipeline
        if bim_id is not None:
            task_data = TaskModel(
                entity_id=bim_id,
                entity_type="bim",
                workspace_id=file.workspace_id,
                type=TaskType.CONVERTING_BIM,
            )
            created_task = await TaskService.create_task(task_data, session=uow.session)
            created_task_id = created_task.id

        # if it's a point cloud - create one task for point cloud conversion
        elif point_cloud_id is not None:
            task_data = TaskModel(
                entity_id=point_cloud_id,
                entity_type="point_cloud",
                workspace_id=file.workspace_id,
                type=TaskType.CONVERTING_POINT_CLOUD,
            )
            created_task = await TaskService.create_task(task_data, session=uow.session)
            created_task_id = created_task.id
        # else - no task is needed

    if bim_id is not None and created_task_id is not None:
        pipeline = chain(
            # type: ignore[attr-defined]
            convert_bim_to_point_cloud.s(
                bim_id=bim_id, task_id=created_task_id),
            # type: ignore[attr-defined]
            convert_point_cloud_task.s(task_id=created_task_id),
        )
        task_result = pipeline.apply_async()

    elif point_cloud_id is not None and created_task_id is not None:
        task_result = convert_point_cloud_task.delay(  # type: ignore[attr-defined]
            point_cloud_id=point_cloud_id,
            task_id=created_task_id,
        )

    if created_task_id is not None:
        response = FileTaskResponse(
            file=FileResponse.model_validate(file, from_attributes=True),
            task=TaskResponse.model_validate(
                created_task, from_attributes=True)
        )
    else:
        response = FileResponse.model_validate(file, from_attributes=True)

    return response


@router.delete(
    "/{file_id}",
    response_model=FileResponse,
    dependencies=[
        Depends(require_file_permission(Permission.FILES_DELETE))],
)
async def delete_file(
    file_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Delete the file.

    This action deletes the file from the storage and removes the record from the database.

    Be cautious, related data will become irrelevant and will be deleted.

    Requires permission.
    """
    async with uow:
        deleted_file = await FileService.delete_file(
            file_id=file_id,
            session=uow.session,
            storage=storage
        )

    return deleted_file


@router.post(
    "/{file_id}/download",
    response_model=FileLinkResponse,
    dependencies=[
        Depends(require_file_permission(Permission.FILES_DOWNLOAD))],
)
async def get_download_link(
    file_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to download a file.

    Use this link to download the file.

    Requires permission.
    """
    async with uow:
        file = await FileService.get_file(
            file_id=file_id,
            session=uow.session
        )
        url = await FileService.generate_file_download_link(
            file_id=file_id,
            session=uow.session,
            storage=storage
        )

    response_data = FileLinkResponse(
        file=FileResponse.model_validate(file, from_attributes=True),
        url=url
    )
    return response_data


@router.post(
    "/point_clouds/{point_cloud_id}",
    response_model=PointCloudResponse,
    dependencies=[
        Depends(require_file_permission(Permission.FILES_VIEW))],
)
async def get_point_cloud(
    point_cloud_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Get point cloud information.

    Requires permission.
    """
    async with uow:
        point_cloud = await FileService.get_point_cloud(point_cloud_id, session=uow.session)

    return point_cloud


# TODO : Add Permission.FILES_VIEW dependency to the endpoint and add file_id param to the api call in frontend
# > frontend/src/pages/PotreeScenePage.jsx::"const metadataUrl = `/api/files/point_clouds/${targetItem.pointCloudId}/metadata.json`;"
@router.get(
    "/point_clouds/{point_cloud_id}/{filename}",
    # dependencies=[
    #     Depends(require_file_permission(Permission.FILES_VIEW))],
)
async def get_point_cloud_file(
    point_cloud_id: uuid.UUID,
    filename: str,
    request: Request,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Get a specific file of the converted point cloud by its filename.
    
    You may need it for PotreeConverter in order to visualize the point cloud.

    Gives access to a file from point cloud conversion.
    """
    async with uow:
        await FileService.get_point_cloud(point_cloud_id, session=uow.session)
        files = await FileService.get_converted_point_cloud_files(point_cloud_id, session=uow.session)

    target_file = next(
        (file for file in files if file.filename == filename), None)
    if target_file is None:
        raise NotFoundError(
            f"File '{filename}' not found for this point cloud")

    range_header = request.headers.get("range")
    s3_response = storage.get_object(
        target_file.key, range_header=range_header)

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": target_file.content_type or "application/octet-stream",
    }

    content_length = s3_response.get("ContentLength")
    if content_length is not None:
        headers["Content-Length"] = str(content_length)

    content_range = s3_response.get("ContentRange")
    if content_range:
        headers["Content-Range"] = content_range

    status_code = 206 if range_header else 200

    return StreamingResponse(
        s3_response["Body"].iter_chunks(chunk_size=64 * 1024),
        status_code=status_code,
        headers=headers,
    )

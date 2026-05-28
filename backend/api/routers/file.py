import uuid
from fastapi import APIRouter, Depends
from infrastructure.storage import Storage
from services.file import FileService
from tasks.processing import convert_bim_to_point_cloud
from schemas.file import (
    FileDataRequest,
    FileLinkResponse,
    BIMResponse,
    FileResponse
)
from core.roles import Permission
from core.dependencies import (
    get_database_uow,
    get_storage,
    DatabaseSessionUOW
)

from api.dependencies import require_file_permission

router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "/{file_id}/confirm",
    response_model=FileResponse,
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
    async with uow:
        file = await FileService.confirm_file_upload(
            file_id=file_id,
            file_data=file_data,
            session=uow.session,
            storage=storage
        )

        bim = await FileService.get_bim_by_file_id(
            file_id=file.id,
            session=uow.session
        )
        if bim and bim.point_cloud_id is None:
            bim_id = bim.id

    # if it's BIM - run the conversion
    if bim_id is not None:
        convert_bim_to_point_cloud.delay(bim_id)  # type: ignore

    return file


@router.delete(
    "/{file_id}",
    response_model=BIMResponse,
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

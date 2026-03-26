from storage import Storage
from roles import Permission
from fastapi import APIRouter, Depends

from dependencies import (
    require_project_permission,
    get_storage
)

from roles import Permission

from schemas.files import FileLinkPublic, FileUploadRequest

from services.files import FileService


router = APIRouter(prefix="/file", tags=["files"])


@router.post(
    "/{stage_id}/files/confirm/point_cloud",
    response_model=FileLinkPublic,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_DOWNLOAD))],
)
async def confirm_point_cloud_upload(
    stage_id: int,
    file_data: FileUploadRequest,
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to download file.

    Use this link to download file.

    Requires permission.
    """
    url = FileService.generate_file_upload_link(
        stage_id, file_data, storage=storage)

    link_data = FileLinkPublic(
        project_id=stage_id,
        presigned_url=url,
        filename=file_data.filename
    )

    return link_data

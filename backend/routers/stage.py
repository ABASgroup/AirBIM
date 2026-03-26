from storage import Storage
from services import project as project_service
from schemas.stage import StageCreate, StagePublic
from roles import Permission
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import (
    get_db_session,
    require_project_permission,
    get_storage
)

from roles import Permission

from schemas.files import FileLinkPublic, FileUploadRequest

from services.files import FileService


router = APIRouter(prefix="/stage", tags=["project stages"])


@router.post(
    "/{project_id}/files/upload",
    response_model=FileLinkPublic,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_DOWNLOAD))],
)
async def get_file_upload_link(
    project_id: int,
    file_data: FileUploadRequest,
    storage: Storage = Depends(get_storage)
):
    """
    Get a temporary link to download file.

    Use this link to download file.

    Requires permission.
    """
    url = FileService.generate_file_upload_link(
        project_id, file_data, storage=storage)

    link_data = FileLinkPublic(
        project_id=project_id,
        presigned_url=url,
        filename=file_data.filename
    )

    return link_data

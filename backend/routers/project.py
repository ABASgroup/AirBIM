from services import project as project_service
from schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate
from roles import Permission
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import (
    get_db_session,
    require_project_permission
)
from roles import Role, get_role_permissions, Permission

from models.membership import Membership
from models.workspace import WorkspaceType

from schemas.files import FileLinkPublic, FileUploadRequest


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectPublic,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_CREATE))],
)
async def create_project(
    project_data: ProjectCreate, session: AsyncSession = Depends(get_db_session)
):
    project = await project_service.create_project(project_data, session=session)
    return project


@router.get(
    "/{project_id}",
    response_model=ProjectPublic,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_VIEW))],
)
async def get_project(project_id: int, session: AsyncSession = Depends(get_db_session)):
    project = await project_service.get_project(project_id, session=session)
    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectPublic,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_EDIT))],
)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    project = await project_service.update_project(
        project_id, project_data, session=session
    )
    return project


@router.delete(
    "/{project_id}",
    response_model=ProjectPublic,
    dependencies=[
        Depends(require_project_permission(Permission.PROJECT_DELETE))],
)
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    project = await project_service.delete_project(project_id, session=session)
    return project


@router.post(
    "/{project_id}/files/download",
    response_model=FileLinkPublic,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_DOWNLOAD))],
)
async def get_file_download_link(
    project_id: int,
    file_data: FileUploadRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a temporary link to download file.

    Use this link to download file.

    Requires permission.
    """


@router.post(
    "/{project_id}/files/upload/confirm",
    response_model=FileLinkPublic,
    dependencies=[
        Depends(require_project_permission(Permission.FILES_UPLOAD_CLOUDS))],
)
async def confirm_point_cloud_upload(
    project_id: int,
    file_data: FileUploadRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a temporary link to upload point cloud.

    Use this when you've finished uploading file.

    Requires permission.
    """

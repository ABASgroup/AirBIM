from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db_session, get_current_user_id, require_membership_permission
from roles import get_role_permissions, Permission
from schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate
from schemas.membership import MembershipPermissionsPublic
from services import project as project_service
from services import membership as membership_service

router = APIRouter(prefix="/workspace",
                   tags=["workspaces, projects, memberships"])


@router.get("/{workspace_id}/access",response_model=MembershipPermissionsPublic)
async def access(
    workspace_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get current user access, including permissions and role in the workspace
    """
    membership = await membership_service.get_membership(user_id, workspace_id, session=session)
    permissions = get_role_permissions(membership.role)
    print(permissions)
    return MembershipPermissionsPublic(
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        permissions=permissions
    )


@router.post(
    "/projects",
    response_model=ProjectPublic,
    dependencies=[Depends(require_membership_permission(Permission.PROJECT_CREATE))]
)
async def create_project(project_data: ProjectCreate, session: AsyncSession = Depends(get_db_session)):
    project = await project_service.create_project(project_data, session=session)
    return project


@router.get(
    "/{workspace_id}/projects",
    response_model=list[ProjectPublic],
    dependencies=[Depends(require_membership_permission(Permission.PROJECT_VIEW))]
)
async def get_workspace_projects(workspace_id: int, session: AsyncSession = Depends(get_db_session)):
    """Get all projects related to the workspace"""
    projects = await project_service.get_workspace_projects(workspace_id, session=session)
    return projects


@router.get(
    "/{workspace_id}/projects/{project_id}",
    response_model=ProjectPublic,
    dependencies=[Depends(require_membership_permission(Permission.PROJECT_VIEW))]
)
async def get_project(project_id: int, session: AsyncSession = Depends(get_db_session)):
    project = await project_service.get_project(project_id, session=session)
    return project


@router.patch(
    "/{workspace_id}/projects/{project_id}",
    response_model=ProjectPublic,
    dependencies=[Depends(require_membership_permission(Permission.PROJECT_EDIT))]
)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    project = await project_service.update_project(project_id, project_data, session=session)
    return project


@router.delete(
    "/{workspace_id}/projects/{project_id}",
    response_model=ProjectPublic,
    dependencies=[Depends(require_membership_permission(Permission.PROJECT_DELETE))]
)
async def delete_project(project_id: int, session: AsyncSession = Depends(get_db_session),):
    project = await project_service.delete_project(project_id, session=session)
    return project

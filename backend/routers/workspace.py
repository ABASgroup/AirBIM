from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from storage import Storage
from dependencies import (
    get_db_session,
    get_current_user_id,
    get_storage,
    require_workspace_permission,
)
from roles import Role, get_role_permissions, Permission

from models.membership import Membership
from models.workspace import WorkspaceType

from schemas.invite_link import InviteLinkRequest, InviteLinkPublic
from schemas.project import ProjectCreate, ProjectCreateRequest, ProjectPublic
from schemas.workspace import WorkspaceCreate, WorkspaceCreateRequest, WorkspacePublic
from schemas.membership import (
    MembershipPermissionsPublic,
    MembershipCreate,
    MembershipPublic,
    MembershipUserPublic
)

from services import project as project_service
from services import membership as membership_service
from services import workspace as workspace_service
from services import invite_link as invite_link_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/{workspace_id}/access", response_model=MembershipPermissionsPublic)
async def access(
    workspace_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get current user access, including permissions and role in the workspace.
    
    Use if you need to specify permissions.
    """
    membership = await membership_service.get_membership(
        user_id, workspace_id, session=session
    )

    permissions = get_role_permissions(membership.role)
    return MembershipPermissionsPublic(
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        permissions=permissions,
    )


@router.get(
    "/{workspace_id}/memberships/",
    response_model=list[MembershipUserPublic],
    dependencies=[
        Depends(require_workspace_permission(Permission.MEMBERS_VIEW))],
)
async def get_workspace_members(
    workspace_id: int, session: AsyncSession = Depends(get_db_session)
):
    """
    Get all workspace members.

    Permission required.
    """
    memberships = await membership_service.get_workspace_members(
        workspace_id, session=session
    )
    return memberships


@router.delete(
    "/{workspace_id}/memberships/{user_id}",
    response_model=MembershipPublic,
    dependencies=[
        Depends(require_workspace_permission(Permission.MEMBERS_REMOVE))],
)
async def remove_user_from_workspace(
    workspace_id: int, user_id: int, session: AsyncSession = Depends(get_db_session)
):
    """
    Remove user from the workspace

    - Permission required
    - You can't remove the owner from his own workspace
    """
    removed_membership = await membership_service.delete_membership(
        user_id, workspace_id, session=session
    )
    return removed_membership


@router.get("/my", response_model=list[WorkspacePublic])
async def get_user_workspaces(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get all workspaces where current user is the member.

    - Personal workspace
    - Team workspaces
    """
    workspaces = await workspace_service.get_user_workspaces(user_id, session=session)
    return workspaces


@router.get(
    "/{workspace_id}",
    response_model=WorkspacePublic,
    dependencies=[Depends(require_workspace_permission(
        Permission.WORKSPACE_VIEW))],
)
async def get_workspace(
    workspace_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get all workspace data.
    """
    workspaces = await workspace_service.get_workspace(workspace_id, session=session)
    return workspaces


@router.post("", response_model=WorkspacePublic)
async def create_workspace(
    workspace_data: WorkspaceCreateRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Creates a new workspace, making current user its owner"""
    workspace = WorkspaceCreate(
        name=workspace_data.name, type=WorkspaceType.TEAM)
    workspace = await workspace_service.create_workspace(workspace, session)

    # current user is the owner
    membership = MembershipCreate(
        workspace_id=workspace.id, user_id=user_id, role=Role.OWNER
    )
    await membership_service.create_membership(membership, session)

    return workspace


@router.delete(
    "/{workspace_id}",
    response_model=WorkspacePublic,
    dependencies=[Depends(require_workspace_permission(
        Permission.WORKSPACE_DELETE))],
)
async def delete_team_workspace(
    workspace_id: int,
    session: AsyncSession = Depends(get_db_session),
    storage: Storage = Depends(get_storage)
):
    """
    Delete workspace and all related data and files.

    You can't delete personal workspace.

    Requires permission.
    """
    workspace = await workspace_service.delete_team_workspace(
        workspace_id,
        session=session,
        storage=storage
    )
    return workspace


@router.post("/{workspace_id}/invites", response_model=InviteLinkPublic)
async def get_invite_link(
    workspace_id: int,
    link_data: InviteLinkRequest,
    membership: Membership = Depends(
        require_workspace_permission(Permission.PROJECT_CREATE)
    ),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get invite link for the workspace associated with that role

    Use if you need a new link
    """
    link = await invite_link_service.generate_invite_link(
        workspace_id, membership.user_id, link_data.role, session=session
    )
    return link


@router.post(
    "/{workspace_id}/invites/revoke",
    dependencies=[
        Depends(require_workspace_permission(
            Permission.MEMBERS_INVITE_REFRESH))
    ],
)
async def revoke_invite_links(
    workspace_id: int, session: AsyncSession = Depends(get_db_session)
):
    """
    Revoke invite links for the workspace

    Old links (created before call) will become obsolete and invalid
    """
    await invite_link_service.revoke_links(workspace_id, session=session)


@router.get(
    "/{workspace_id}/projects",
    response_model=list[ProjectPublic],
    dependencies=[
        Depends(require_workspace_permission(Permission.PROJECT_VIEW))],
)
async def get_workspace_projects(
    workspace_id: int, session: AsyncSession = Depends(get_db_session)
):
    """Get all projects related to the workspace"""
    projects = await project_service.get_workspace_projects(
        workspace_id, session=session
    )
    return projects


@router.post(
    "/{workspace_id}/projects",
    response_model=ProjectPublic,
    dependencies=[
        Depends(require_workspace_permission(Permission.PROJECT_CREATE))],
)
async def create_project(
    workspace_id: int,
    project_data: ProjectCreateRequest,
    session: AsyncSession = Depends(get_db_session)
):
    project_data_db = ProjectCreate(workspace_id=workspace_id,
                                    name=project_data.name,
                                    description=project_data.description)
    project = await project_service.create_project(project_data_db, session=session)
    return project

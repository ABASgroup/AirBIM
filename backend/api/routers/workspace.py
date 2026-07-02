import uuid
from fastapi import APIRouter, Depends
from core.dependencies import (
    get_database_uow,
    DatabaseSessionUOW
)
from core.roles import Role, get_role_permissions, Permission
from api.dependencies import require_workspace_permission, get_current_user_id
from models.membership import Membership
from models.workspace import WorkspaceType
from models.task import TaskStatus
from schemas.invite_link import InviteLinkRequest, NewInviteLinkResponse
from schemas.project import ProjectModel, ProjectCreateRequest, ProjectResponse
from schemas.user import UserResponse
from schemas.workspace import (
    WorkspaceModel,
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceUpdate
)
from schemas.membership import (
    MembershipPermissionsResponse,
    MembershipModel,
    MembershipResponse,
    MembershipUserResponse
)
from schemas.task import TaskResponse
from services.project import ProjectService
from services import membership as membership_service
from services.workspace import WorkspaceService
from services import invite_link as invite_link_service
from services.task import TaskService


router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/{workspace_id}/access", response_model=MembershipPermissionsResponse)
async def access(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Get current user access, including permissions and role in the workspace.

    Use if you need to specify permissions.

    If user is not a member of the workspace, returns an error.

    Requires permission.
    """
    async with uow:
        membership = await membership_service.get_membership(
            user_id, workspace_id, session=uow.session
        )

    permissions = get_role_permissions(membership.role)
    return MembershipPermissionsResponse(
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        permissions=permissions,
        id=membership.id,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )


@router.get(
    "/{workspace_id}/memberships/",
    response_model=list[MembershipUserResponse],
    dependencies=[
        Depends(require_workspace_permission(Permission.MEMBERS_VIEW))],
)
async def get_workspace_members(
    workspace_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Get all workspace members.

    Requires permission.
    """
    async with uow:
        memberships = await membership_service.get_workspace_members(
            workspace_id, session=uow.session
        )
    return memberships


@router.delete(
    "/{workspace_id}/memberships/{user_id}",
    response_model=MembershipResponse,
    dependencies=[
        Depends(require_workspace_permission(Permission.MEMBERS_REMOVE))],
)
async def remove_user_from_workspace(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Remove user from the workspace.

    You can't remove the owner from his own workspace.

    Requires permission.
    """
    async with uow:
        removed_membership = await membership_service.delete_membership(
            user_id, workspace_id, session=uow.session
        )
    return removed_membership


@router.patch(
    "/{workspace_id}/memberships/{user_id}/role",
    response_model=MembershipResponse,
)
async def change_user_role(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    role: Role,
    editor: Membership = Depends(
        require_workspace_permission(Permission.MEMBERS_EDIT_ROLE)),
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Change user role in the workspace.

    Requires permission.
    """
    async with uow:
        membership = await membership_service.change_user_role(
            editor_id=editor.user_id,
            user_id=user_id,
            workspace_id=workspace_id,
            new_role=role,
            session=uow.session
        )
    return membership


@router.get("/my", response_model=list[WorkspaceResponse])
async def get_user_workspaces(
    user_id: uuid.UUID = Depends(get_current_user_id),
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Get all workspaces where current user is the member.

    Includes all types:
    - Personal workspace
    - Team workspaces
    """
    async with uow:
        workspaces = await WorkspaceService.get_user_workspaces(user_id, session=uow.session)
    return workspaces


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    dependencies=[Depends(require_workspace_permission(
        Permission.WORKSPACE_VIEW))],
)
async def get_workspace(
    workspace_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Get all workspace data.

    Requires permission.
    """
    async with uow:
        workspaces = await WorkspaceService.get_workspace(workspace_id, session=uow.session)
    return workspaces


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_data: WorkspaceCreateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Creates a new workspace, making current user its owner.

    You can create only team workspace, personal 
    workspace is created automatically during registration.

    Requires permission.
    """
    async with uow:
        workspace = WorkspaceModel(
            name=workspace_data.name, type=WorkspaceType.TEAM)
        workspace = await WorkspaceService.create_workspace(workspace, uow.session)

        # current user is the owner
        membership = MembershipModel(
            workspace_id=workspace.id, user_id=user_id, role=Role.OWNER
        )
        await membership_service.create_membership(membership, uow.session)

    return workspace


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    dependencies=[Depends(require_workspace_permission(
                  Permission.WORKSPACE_EDIT))]
)
async def edit_workspace(
    workspace_id: uuid.UUID,
    workspace_data: WorkspaceUpdate,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Edit the workspace.

    Requires permission.
    """
    async with uow:
        workspace = await WorkspaceService.update_workspace(workspace_id, workspace_data, uow.session)

    return workspace


@router.delete(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    dependencies=[Depends(require_workspace_permission(
        Permission.WORKSPACE_DELETE))],
)
async def delete_team_workspace(
    workspace_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow)
):
    """
    Delete workspace and all related data and files.

    You can't delete personal workspace.

    Requires permission.
    """
    async with uow:
        workspace = await WorkspaceService.delete_team_workspace(
            workspace_id,
            session=uow.session
        )
    return workspace


@router.post("/{workspace_id}/invites", response_model=NewInviteLinkResponse)
async def get_invite_link(
    workspace_id: uuid.UUID,
    link_data: InviteLinkRequest,
    membership: Membership = Depends(
        require_workspace_permission(Permission.MEMBERS_INVITE)
    ),
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Get invite link for the workspace associated with that role.

    Use if you need a new link.

    Always save token from the response, otherwise it will be lost.

    Requires permission.
    """
    async with uow:
        link, token = await invite_link_service.generate_invite_link(
            workspace_id, membership.user_id, link_data.role, session=uow.session
        )
    return NewInviteLinkResponse(
        token=token,
        workspace=WorkspaceResponse.model_validate(
            link.workspace, from_attributes=True),
        created_by=UserResponse.model_validate(
            link.created_by, from_attributes=True),
        expires_at=link.expires_at,
    )


@router.post(
    "/{workspace_id}/invites/revoke",
    dependencies=[
        Depends(require_workspace_permission(
            Permission.MEMBERS_INVITE_REFRESH))
    ],
)
async def revoke_invite_links(
    workspace_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Revoke invite links for the workspace.

    Old links (created before the call) will become obsolete and invalid.

    Requires permission.
    """
    async with uow:
        await invite_link_service.revoke_links(workspace_id, session=uow.session)


@router.get(
    "/{workspace_id}/projects",
    response_model=list[ProjectResponse],
    dependencies=[
        Depends(require_workspace_permission(Permission.PROJECT_VIEW))],
)
async def get_workspace_projects(
    workspace_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Get all projects related to the workspace.

    Requires permission.
    """
    async with uow:
        projects = await ProjectService.get_workspace_projects(
            workspace_id, session=uow.session
        )
    return projects


@router.post(
    "/{workspace_id}/projects",
    response_model=ProjectResponse,
    dependencies=[
        Depends(require_workspace_permission(Permission.PROJECT_CREATE))],
)
async def create_project(
    workspace_id: uuid.UUID,
    project_data: ProjectCreateRequest,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Create project in this workspace.

    Requires permission.
    """
    async with uow:
        project_data_db = ProjectModel(workspace_id=workspace_id,
                                       name=project_data.name,
                                       description=project_data.description)
        project = await ProjectService.create_project(project_data_db, session=uow.session)
    return project


@router.get(
    "/{workspace_id}/tasks",
    response_model=list[TaskResponse],
    dependencies=[
        Depends(require_workspace_permission(Permission.WORKSPACE_VIEW))],
)
async def get_workspace_tasks(
    workspace_id: uuid.UUID,
    statuses: list[TaskStatus] | None = None,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Get all tasks related to this workspace.

    You can choose which statuses are to be filtered.

    Requires permission.
    """
    async with uow:
        tasks = await TaskService.get_tasks_by_workspace_id(workspace_id, statuses, uow.session)

    return tasks

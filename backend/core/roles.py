import enum


class Role(enum.StrEnum):
    """User roles in workspaces"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class InviteableRole(enum.StrEnum):
    """Roles that can have invite links"""
    VIEWER = "viewer"
    MEMBER = "member"


class Permission(enum.StrEnum):
    """
    Permissions stated in the app.

    Registry of all permissions.

    For granular control check in code.
    """
    # workspace management
    WORKSPACE_VIEW = "workspace:view"
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_EDIT = "workspace:edit"
    # member management
    MEMBERS_VIEW = "members:view"
    MEMBERS_INVITE = "members:invite"
    MEMBERS_INVITE_REFRESH = "members:invite:refresh"
    MEMBERS_REMOVE = "members:remove"
    MEMBERS_EDIT_ROLE = "members:edit_role"
    # projects
    PROJECT_VIEW = "projects:view"
    PROJECT_CREATE = "projects:create"
    PROJECT_EDIT = "projects:edit"
    PROJECT_DELETE = "projects:delete"
    # stages
    STAGE_VIEW = "stage:view"
    STAGE_CREATE = "stage:create"
    STAGE_EDIT = "stage:edit"
    STAGE_DELETE = "stage:delete"
    # recording results
    RECORDING_RESULT_VIEW = "recording_result:view"
    RECORDING_RESULT_DELETE = "recording_result:delete"
    # files
    FILES_VIEW = "files:view"
    FILES_DOWNLOAD = "files:download"
    FILES_UPLOAD = "files:upload"
    FILES_DELETE = "files:delete"
    # tasks
    TASKS_START = "tasks:start"


# assign permissions here
__viewer_permissions = [
    Permission.WORKSPACE_VIEW,
    Permission.PROJECT_VIEW,
    Permission.STAGE_VIEW,
    Permission.FILES_VIEW,
    Permission.FILES_DOWNLOAD,
    Permission.RECORDING_RESULT_VIEW
]

__member_permissions = [
    Permission.PROJECT_EDIT,
    Permission.STAGE_CREATE,
    Permission.STAGE_EDIT,
    Permission.FILES_UPLOAD,
    Permission.FILES_DOWNLOAD,
    Permission.MEMBERS_INVITE,
    Permission.MEMBERS_VIEW,
    Permission.RECORDING_RESULT_DELETE,
    Permission.TASKS_START,
]
__member_permissions.extend(__viewer_permissions)

__admin_permissions = [
    Permission.PROJECT_CREATE,
    Permission.PROJECT_DELETE,
    Permission.STAGE_DELETE,
    Permission.FILES_DELETE,
    Permission.MEMBERS_REMOVE,
    Permission.MEMBERS_EDIT_ROLE,
    Permission.MEMBERS_VIEW,
    Permission.TASKS_START,
]
__admin_permissions.extend(__member_permissions)

ROLE_PERMISSIONS = {
    Role.VIEWER: __viewer_permissions,
    Role.MEMBER: __member_permissions,
    Role.ADMIN: __admin_permissions,
    # all rights to the owner, no matter what
    Role.OWNER: [member.value for member in Permission],
}


def get_role_permissions(role: Role) -> list[Permission]:
    """Get permissions for some role."""
    return ROLE_PERMISSIONS[role]

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
    """
    # workspace management
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_EDIT = "workspace:edit"
    # member management
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
    # files
    FILES_DOWNLOAD = "files:download"
    FILES_UPLOAD_BIM = "files:upload:bim"
    FILES_UPLOAD_CLOUDS = "files:upload:clouds"
    FILES_DELETE_BIM = "files:delete:bim"
    FILES_DELETE_CLOUDS = "files:delete:clouds"


# assign permissions here
ROLE_PERMISSIONS = {
    Role.VIEWER: [
        Permission.PROJECT_VIEW,
        Permission.STAGE_VIEW,
        Permission.FILES_DOWNLOAD,
    ],
    Role.MEMBER: [
        Permission.PROJECT_VIEW,
        Permission.PROJECT_EDIT,
        Permission.STAGE_VIEW,
        Permission.STAGE_CREATE,
        Permission.STAGE_EDIT,
        Permission.FILES_UPLOAD_CLOUDS,
        Permission.FILES_DOWNLOAD,
        Permission.MEMBERS_INVITE,
    ],
    Role.ADMIN: [
        Permission.PROJECT_VIEW,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_EDIT,
        Permission.PROJECT_DELETE,
        Permission.STAGE_VIEW,
        Permission.STAGE_CREATE,
        Permission.STAGE_EDIT,
        Permission.STAGE_DELETE,
        Permission.FILES_UPLOAD_CLOUDS,
        Permission.FILES_UPLOAD_BIM,
        Permission.FILES_DOWNLOAD,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_REMOVE,
        Permission.MEMBERS_EDIT_ROLE,
        Permission.WORKSPACE_EDIT,
    ],
    # all rights to the owner, no matter what
    Role.OWNER: [member.value for member in Permission],
}


def get_role_permissions(role: Role) -> list[Permission]:
    """Get permissions for some role."""
    return ROLE_PERMISSIONS[role]

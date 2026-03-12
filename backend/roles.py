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
    """Permissions stated in the app"""
    # projects
    PROJECT_VIEW = "projects:view"
    PROJECT_CREATE = "projects:create"
    PROJECT_EDIT = "projects:edit"
    PROJECT_DELETE = "projects:delete"
    # files
    FILES_UPLOAD_BIM = "files:upload:bim"
    FILES_UPLOAD_CLOUDS = "files:upload:clouds"
    # member management
    MEMBERS_INVITE = "members:invite"
    MEMBERS_REMOVE = "members:remove"
    MEMBERS_EDIT_ROLE = "members:edit_role"
    # workspace management
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_EDIT = "workspace:edit"


ROLE_PERMISSIONS = {
    Role.VIEWER: (
        Permission.PROJECT_VIEW,
    ),
    Role.MEMBER: (
        Permission.PROJECT_VIEW,
        Permission.PROJECT_EDIT,
        Permission.FILES_UPLOAD_CLOUDS,
        Permission.MEMBERS_INVITE
    ),
    Role.ADMIN: (
        Permission.PROJECT_VIEW,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_EDIT,
        Permission.PROJECT_DELETE,
        Permission.FILES_UPLOAD_CLOUDS,
        Permission.FILES_UPLOAD_BIM,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_REMOVE,
        Permission.MEMBERS_EDIT_ROLE,
        Permission.WORKSPACE_EDIT
    ),
    # all rights to the owner, no matter what
    Role.OWNER: [member.value for member in Permission],
}


def get_role_permissions(role: Role) -> tuple[Permission]:
    """Get permissions for some role"""
    return ROLE_PERMISSIONS[role]

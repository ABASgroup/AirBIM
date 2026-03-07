from pydantic import BaseModel
from roles import Role, Permission


class MembershipCreate(BaseModel):
    workspace_id: int
    user_id: int
    role: Role = Role.MEMBER


class MembershipPermissionsPublic(BaseModel):
    workspace_id: int
    user_id: int
    role: Role
    permissions: tuple[Permission]

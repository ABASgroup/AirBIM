from pydantic import BaseModel
from roles import Role, Permission


class MembershipCreate(BaseModel):
    workspace_id: int
    user_id: int
    role: Role = Role.MEMBER


class MembershipPublic(BaseModel):
    """API Response schema"""
    workspace_id: int
    user_id: int
    role: Role


class MembershipPermissionsPublic(BaseModel):
    """API Response schema"""
    workspace_id: int
    user_id: int
    role: Role
    permissions: list[Permission]

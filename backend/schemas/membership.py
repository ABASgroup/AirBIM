from pydantic import BaseModel
from .user import UserPublic
from roles import Role, Permission
from datetime import datetime


class MembershipCreate(BaseModel):
    workspace_id: int
    user_id: int
    role: Role = Role.MEMBER


class MembershipPublic(BaseModel):
    """API Response schema"""
    workspace_id: int
    user_id: int
    role: Role


class MembershipUserPublic(BaseModel):
    """API Response schema"""
    user: UserPublic
    role: Role
    workspace_id: int

class MembershipPermissionsPublic(BaseModel):
    """API Response schema"""
    workspace_id: int
    user_id: int
    role: Role
    permissions: list[Permission]

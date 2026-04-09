import uuid
from pydantic import BaseModel
from roles import Permission, Role
from .base import Response
from .user import UserResponse


class MembershipModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: Role = Role.MEMBER


class MembershipPublic(Response):
    """API Response schema."""
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: Role


class MembershipUserResponse(Response):
    """
    API Response schema.

    Contains user information in addition to membership info.
    """
    user: UserResponse
    role: Role
    workspace_id:  uuid.UUID


class MembershipPermissionsResponse(Response):
    """
    API Response schema.

    Contains specified permissions in addition to membership 
    info according to the user's role.
    """
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: Role
    permissions: list[Permission]

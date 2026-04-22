import uuid
from datetime import datetime
from pydantic import BaseModel
from core.roles import InviteableRole, Role
from schemas.workspace import WorkspaceResponse
from schemas.user import UserResponse


class InviteLinkRequest(BaseModel):
    role: InviteableRole


class InviteLinkModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    token_hashed: str
    workspace_id: uuid.UUID
    creator_id: uuid.UUID
    role: Role
    expires_at: datetime | None = None


class NewInviteLinkResponse(BaseModel):
    """API Response schema."""
    token: str
    workspace: WorkspaceResponse
    created_by: UserResponse
    expires_at: datetime | None = None


class InviteLinkResponse(BaseModel):
    """API Response schema."""
    workspace: WorkspaceResponse
    created_by: UserResponse
    expires_at: datetime | None = None

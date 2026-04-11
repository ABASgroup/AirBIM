import uuid
from datetime import datetime
from pydantic import BaseModel
from core.roles import InviteableRole, Role


class InviteLinkRequest(BaseModel):
    role: InviteableRole


class InviteLinkModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    token_hashed: str
    workspace_id: uuid.UUID
    creator_id: uuid.UUID
    role: Role
    expires_at: datetime | None = None


class InviteLinkResponse(BaseModel):
    """API Response schema."""
    token: str
    workspace_id: uuid.UUID
    role: InviteableRole
    expires_at: datetime | None = None

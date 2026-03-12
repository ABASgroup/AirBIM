from pydantic import BaseModel
from roles import InviteableRole, Role
from datetime import datetime


class InviteLinkRequest(BaseModel):
    role: InviteableRole


class InviteLinkCreate(BaseModel):
    token_hashed: str
    workspace_id: int
    role: Role
    expires_at: datetime | None = None


class InviteLinkPublic(BaseModel):
    token: str
    workspace_id: int
    role: InviteableRole
    expires_at: datetime | None = None

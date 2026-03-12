from pydantic import BaseModel
from roles import InviteableRole, Role


class InviteLinkRequest(BaseModel):
    role: InviteableRole


class InviteLinkCreate(BaseModel):
    token_hashed: str
    workspace_id: int
    role: Role


class InviteLinkPublic(BaseModel):
    token: str
    workspace_id: int
    role: InviteableRole

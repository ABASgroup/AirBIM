from pydantic import BaseModel
from models.membership import Role


class MembershipCreate(BaseModel):
    workspace_id: int
    user_id: int
    role: Role = Role.MEMBER

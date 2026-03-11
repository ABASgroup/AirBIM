from pydantic import BaseModel
from models.workspace import WorkspaceType


class WorkspaceCreate(BaseModel):
    name: str
    type: WorkspaceType = WorkspaceType.PERSONAL

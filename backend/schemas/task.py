from uuid import UUID
from pydantic import BaseModel, field_validator, AwareDatetime
from models.task import TaskType, TaskStatus
from .base import Response


class TaskModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    entity_id: UUID
    entity_type: str
    meta: str | None = None
    steps: int = 1
    workspace_id: UUID
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING


class TaskUpdateModel(BaseModel):
    """Schema for updating task."""
    progress: float | None = None
    status: TaskStatus | None = None
    finished_at: AwareDatetime | None = None
    meta: str | None = None

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, value: float | None) -> float | None:
        if value is not None and not (0 <= value <= 100):
            raise ValueError("Progress must be in range from 0 to 100.")
        return value


class TaskResponse(Response):
    """API Response schema."""
    workspace_id: UUID
    progress: float
    type: TaskType
    status: TaskStatus
    entity_id: UUID
    entity_type: str
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    meta: str | None = None


class TaskStepModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    name: str
    task_id: UUID
    step_task_id: str
    started_at: AwareDatetime


class TaskStepUpdateModel(BaseModel):
    """Schema for updating task."""
    name: str | None = None
    finished_at: AwareDatetime | None = None

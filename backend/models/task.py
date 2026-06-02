from uuid import UUID
import enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum, ForeignKey
from .base import BaseModel


class TaskStatus(enum.StrEnum):
    """
    Task statuses.

    Represent current state of a task.
    """
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskType(enum.StrEnum):
    """
    Task types.

    Represent what work or process a task executes.
    """
    CHECKING_PROGRESS = "checking progress"
    COMPARING_PLAN_FACT = "comparing plan fact"


class Task(BaseModel):
    __tablename__ = "tasks"

    celery_task_id: Mapped[UUID]

    workspace_id: Mapped["UUID"] = mapped_column(
        ForeignKey("workspaces.id"))

    progress: Mapped[int] = mapped_column(default=0, nullable=True)

    type: Mapped[TaskType] = mapped_column(
        Enum(TaskStatus, name="task_type", create_constraint=True),
        nullable=False
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", create_constraint=True),
        nullable=False,
        default=TaskStatus.STARTED
    )

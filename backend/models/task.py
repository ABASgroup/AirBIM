from datetime import datetime
from uuid import UUID
import enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Enum, ForeignKey, func
from .base import BaseModel


class TaskStatus(enum.StrEnum):
    """
    Task statuses.

    Represent current state of a task.
    """
    PENDING = "pending"
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskType(enum.StrEnum):
    """
    Task types.

    Represent what work or process a task executes.
    """
    CHECKING_PROGRESS = "checking progress"
    COMPARING_PLAN_FACT = "comparing plan fact"
    CONVERTING_BIM = "converting bim"
    CONVERTING_POINT_CLOUD = "converting point cloud"


class Task(BaseModel):
    """
    A task is a long-running process that 
    can be executed asynchronously and tracked for progress and status.

    A task is bound to its workspace and some entity where it is executed. For example, a task can be bound to a project or a model.
    """
    __tablename__ = "tasks"

    workspace_id: Mapped["UUID"] = mapped_column(
        ForeignKey("workspaces.id"))

    entity_id: Mapped["UUID"] = mapped_column(
        nullable=False
    )

    entity_type: Mapped[str] = mapped_column(
        nullable=False
    )

    progress: Mapped[float] = mapped_column(default=0.0, nullable=True)

    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type", create_constraint=True),
        nullable=False
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", create_constraint=True),
        nullable=False,
        default=TaskStatus.STARTED
    )

    steps: Mapped[int] = mapped_column(default=1, nullable=False)

    meta: Mapped[str | None] = mapped_column(
        nullable=True
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


class TaskStep(BaseModel):
    """
    A single task step in execution process.

    For example, a celery task in a chain of tasks: it is defined with a step task ID.

    This model allows to control the whole task step by step.
    """
    __tablename__ = "task_steps"

    task_id: Mapped["UUID"] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )

    step_task_id: Mapped[str | None] = mapped_column(
        unique=True, nullable=True)

    name: Mapped[str] = mapped_column(
        nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

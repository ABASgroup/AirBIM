from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, ForeignKey
from .base import BaseModel
import enum


class ProjectStatus(enum.StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(BaseModel):
    __tablename__ = "projects"

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    workspace: Mapped["Workspace"] = relationship(
        back_populates="projects", cascade="delete")

    name: Mapped["str"] = mapped_column(nullable=False)
    description: Mapped["str"]

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_statuses", create_constraint=True),
        nullable=False,
        default=ProjectStatus.ACTIVE
    )

import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, ForeignKey
from .base import BaseModel
import enum


class ProjectStatus(enum.StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(BaseModel):
    __tablename__ = "projects"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"))
    workspace: Mapped["Workspace"] = relationship(back_populates="projects")

    name: Mapped["str"] = mapped_column(nullable=False)
    description: Mapped["str"]

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_statuses", create_constraint=True),
        nullable=False,
        default=ProjectStatus.ACTIVE
    )

    stages: Mapped[list["Stage"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    bim: Mapped["BIM"] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

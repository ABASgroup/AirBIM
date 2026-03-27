from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, ForeignKey
from .base import BaseModel
import enum


class ProjectStatus(enum.StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(BaseModel):
    __tablename__ = "projects"

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"))
    workspace: Mapped["Workspace"] = relationship(back_populates="projects")

    name: Mapped["str"] = mapped_column(nullable=False)
    description: Mapped["str"]

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_statuses", create_constraint=True),
        nullable=False,
        default=ProjectStatus.ACTIVE
    )

    bim_files: Mapped[list["BimFile"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    point_cloud_files: Mapped[list["PointCloudFile"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

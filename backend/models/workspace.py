from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import Enum
from .base import BaseModel
import enum


class WorkspaceType(enum.StrEnum):
    PERSONAL = "personal"
    TEAM = "team"


class Workspace(BaseModel):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan")

    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    
    projects: Mapped[list["Project"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )

    type: Mapped[WorkspaceType] = mapped_column(
        Enum(WorkspaceType, name="workspace_types", create_constraint=True),
        nullable=False,
        default=WorkspaceType.PERSONAL
    )

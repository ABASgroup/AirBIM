import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum
from datetime import datetime
from core.roles import Role
from .base import BaseModel


class InviteLink(BaseModel):
    __tablename__ = "invite_links"

    token_hashed: Mapped[str] = mapped_column(index=True, unique=True)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"))
    workspace: Mapped["Workspace"] = relationship(
        back_populates="invite_links")

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="roles", create_constraint=True),
        nullable=False,
        default=Role.MEMBER
    )

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by: Mapped["User"] = relationship(
        back_populates="invite_links"
    )

    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

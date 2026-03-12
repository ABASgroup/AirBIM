from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum
from datetime import datetime
from roles import Role
from .base import BaseModel


class InviteLink(BaseModel):
    __tablename__ = "invite_links"

    token_hashed: Mapped[str] = mapped_column(index=True, unique=True)

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    workspace: Mapped["Workspace"] = relationship(
        back_populates="invite_links", cascade="delete")

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="roles", create_constraint=True),
        nullable=False,
        default=Role.MEMBER
    )

    inviter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    inviter: Mapped["User"] = relationship(
        back_populates="invite_links"
    )

    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

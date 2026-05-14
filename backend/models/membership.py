import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from .base import BaseModel
from core.roles import Role


class Membership(BaseModel):
    __tablename__ = "memberships"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"))
    workspace: Mapped["Workspace"] = relationship(
        back_populates="memberships")

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    user: Mapped["User"] = relationship(
        back_populates="memberships"
    )

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="roles", create_constraint=True),
        nullable=False,
        default=Role.OWNER
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'workspace_id',
                         name='unique_user_per_workspace'),
    )

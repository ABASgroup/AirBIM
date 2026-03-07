from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, ForeignKey
from .base import BaseModel
from roles import Role


class Membership(BaseModel):
    __tablename__ = "memberships"

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    workspace: Mapped["Workspace"] = relationship(
        back_populates="memberships", cascade="delete")

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    user: Mapped["User"] = relationship(
        back_populates="memberships"
    )

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="roles", create_constraint=True),
        nullable=False,
        default=Role.OWNER
    )

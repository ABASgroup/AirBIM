from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import datetime
from .base import BaseModel


class Invitation(BaseModel):
    __tablename__ = "invitations"

    token_hashed: Mapped[str] = mapped_column()

    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    workspace: Mapped["Workspace"] = relationship(
        back_populates="invitations", cascade="delete")

    expires_at: Mapped[datetime] = mapped_column(nullable=False)

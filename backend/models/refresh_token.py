from datetime import datetime
import uuid
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class RefreshToken(BaseModel):
    """Tokens used to refresh access tokens."""
    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

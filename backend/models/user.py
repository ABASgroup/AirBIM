from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from .membership import Membership
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str]
    email: Mapped[str]
    password_hashed: Mapped[str] = mapped_column(String(128), nullable=False)

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

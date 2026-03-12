from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password_hashed: Mapped[str] = mapped_column(String(128), nullable=False)

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    invite_links: Mapped[list["InviteLink"]] = relationship(
        back_populates="created_by", cascade="all, delete-orphan"
    )

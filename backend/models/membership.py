from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, Enum, ForeignKey
from .company import Company
from .base import BaseModel
from .user import User
import enum


class Roles(enum.StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Membership(BaseModel):
    __tablename__ = "memberships"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    company: Mapped["Company"] = relationship(
        back_populates="memberships", cascade="delete")

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    user: Mapped["User"] = relationship(
        back_populates="memberships"
    )

    role = Column(Enum(Roles), nullable=False, default=Roles.MEMBER)

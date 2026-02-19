from sqlalchemy.orm import Mapped, relationship, mapped_column
from .membership import Membership
from .base import BaseModel


class Company(BaseModel):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="company", cascade="all, delete-orphan")

    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from .base import BaseModel


class Invitation(BaseModel):
    __tablename__ = "invitations"

    token: Mapped[str] = mapped_column()

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    company: Mapped["Company"] = relationship(
        back_populates="invitations", cascade="delete")

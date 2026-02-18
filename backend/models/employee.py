from .company import Company
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String


class Employee(BaseModel):
    __tablename__ = "employees"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    company: Mapped["Company"] = relationship(back_populates="employees", cascade="delete")

    username: Mapped[str]
    email: Mapped[str]
    password_hashed: Mapped[str] = mapped_column(String(128), nullable=False)

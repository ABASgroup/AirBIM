from sqlalchemy.orm import Mapped
from .base import BaseModel


class Company(BaseModel):
    __tablename__ = "companies"

    name: Mapped[str]

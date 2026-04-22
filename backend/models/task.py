import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum
from datetime import datetime
from core.roles import Role
from .base import BaseModel


class Task(BaseModel):
    __tablename__ = "tasks"

import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from .base import BaseModel


class Stage(BaseModel):
    __tablename__ = "stages"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="stages")
    point_cloud: Mapped["PointCloud"] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

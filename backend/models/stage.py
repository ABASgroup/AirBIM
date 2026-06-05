from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey
from .base import BaseModel


class Stage(BaseModel):
    __tablename__ = "stages"

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))

    name: Mapped["str"] = mapped_column(nullable=True)
    description: Mapped["str"] = mapped_column(nullable=True)

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    project: Mapped["Project"] = relationship(back_populates="stages")
    point_cloud: Mapped["PointCloud"] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

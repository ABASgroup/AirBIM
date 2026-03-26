from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from .base import BaseModel


class BimFile(BaseModel):
    __tablename__ = "bim_files"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="bim_files")

    path: Mapped["str"] = mapped_column(nullable=False)
    extension: Mapped["str"] = mapped_column(nullable=False)
    size: Mapped["int"] = mapped_column(nullable=False)


class PointCloudFile(BaseModel):
    __tablename__ = "point_cloud_files"

    stage_id: Mapped[int] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"))
    stage: Mapped["Stage"] = relationship(
        back_populates="point_cloud_files")

    path: Mapped["str"] = mapped_column(nullable=False)
    extension: Mapped["str"] = mapped_column(nullable=False)
    size: Mapped["int"] = mapped_column(nullable=False)

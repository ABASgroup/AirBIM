from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum
from enum import StrEnum
from .base import BaseModel


class FileStatus(StrEnum):
    UPLOADED = "uploaded"
    PENDING = "pending"


class File(BaseModel):
    """
    Represents every single file in the storage without extra specification.

    Every single file model you create must have relation to this model (one to one).
    """
    __tablename__ = "files"

    filename: Mapped["str"] = mapped_column(nullable=False)
    key: Mapped["str"] = mapped_column(nullable=False, unique=True)
    extension: Mapped["str"] = mapped_column(nullable=False)
    size: Mapped["int"] = mapped_column(nullable=False)

    status: Mapped[FileStatus] = mapped_column(
        Enum(FileStatus, name="file_statuses", create_constraint=True),
        nullable=False,
        default=FileStatus.PENDING
    )


class BimFile(BaseModel):
    __tablename__ = "bim_files"

    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), unique=True)
    file: Mapped["File"] = relationship(
        back_populates="bim_file", cascade="all, delete")

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="bim_files")


class PointCloudFile(BaseModel):
    __tablename__ = "point_cloud_files"

    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), unique=True)
    file: Mapped["File"] = relationship(
        back_populates="point_cloud", cascade="all, delete")

    stage_id: Mapped[int] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"))
    stage: Mapped["Stage"] = relationship(
        back_populates="point_cloud_files")

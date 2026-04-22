import uuid
from enum import StrEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum
from .base import BaseModel


class FileStatus(StrEnum):
    UPLOADED = "uploaded"
    PENDING = "pending"


class File(BaseModel):
    """
    Represents every single file in the storage without extra specification.
    """
    __abstract__ = True

    filename: Mapped["str"] = mapped_column(nullable=False)
    key: Mapped["str"] = mapped_column(nullable=False, unique=True)
    content_type: Mapped["str"] = mapped_column(nullable=False)
    size: Mapped["int"] = mapped_column(nullable=False)

    status: Mapped[FileStatus] = mapped_column(
        Enum(FileStatus, name="file_statuses", create_constraint=True),
        nullable=False,
        default=FileStatus.PENDING
    )


class BimFile(File):
    __tablename__ = "bim_files"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="bim_files")


class PointCloudFile(File):
    __tablename__ = "point_cloud_files"

    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"))
    stage: Mapped["Stage"] = relationship(
        back_populates="point_cloud_files")

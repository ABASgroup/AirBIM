import uuid
from typing import Optional
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
    __tablename__ = "files"

    filename: Mapped["str"] = mapped_column(nullable=False)
    key: Mapped["str"] = mapped_column(nullable=False, unique=True)
    content_type: Mapped["str"] = mapped_column(nullable=False)
    size: Mapped["int"] = mapped_column(nullable=False)

    status: Mapped[FileStatus] = mapped_column(
        Enum(FileStatus, name="file_statuses", create_constraint=True),
        nullable=False,
        default=FileStatus.PENDING
    )

    workspace_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("workspaces.id"))


class PointCloud(BaseModel):
    __tablename__ = "point_clouds"

    stage_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"))
    stage: Mapped["Stage"] = relationship(
        back_populates="point_clouds")

    converted_file_links: Mapped[list["PointCloudConverted"]] = relationship(
        back_populates="point_cloud",
        cascade="all, delete-orphan"
    )

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    file: Mapped["File"] = relationship(
        cascade="all, delete",
        passive_deletes=True
    )

    bim: Mapped[Optional["Bim"]] = relationship(
        back_populates="point_cloud", uselist=False)


class PointCloudConverted(BaseModel):
    __tablename__ = "point_cloud_converted"

    point_cloud_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("point_clouds.id", ondelete="CASCADE")
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE")
    )
    point_cloud: Mapped["PointCloud"] = relationship(
        back_populates="converted_file_links")
    file: Mapped["File"] = relationship(
        cascade="all, delete"
    )


class Bim(BaseModel):
    __tablename__ = "bims"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="bim")

    point_cloud_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("point_clouds.id", ondelete="SET NULL"),
        nullable=True,
        unique=True
    )
    point_cloud: Mapped[Optional["PointCloud"]] = relationship(
        "PointCloud",
        back_populates="bim"
    )

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    file: Mapped["File"] = relationship(
        cascade="all, delete",
        passive_deletes=True
    )

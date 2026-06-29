"""Various file models in the system."""
from uuid import UUID
from typing import Optional
from enum import StrEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum, CheckConstraint
from .base import BaseModel


class FileStatus(StrEnum):
    """
    Statuses of files in the system.

    - Pending files are not uploaded yet
    - In progress files are being processed (e.g. converting, recording processing, etc.)
    - Uploaded files are ready to be used
    """
    UPLOADED = "uploaded"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"


class PointCloudType(StrEnum):
    """
    Types of point clouds in the system.

    - Plan type is for point clouds that represent project's BIM (e.g. converted)
    - Scan type is for real scans of a project, actual scanning
    - Recording type is for point clouds that are results of recording processing (e.g. comparison of plan and scan, progress, etc.)
    """
    PLAN = "plan"
    SCAN = "scan"
    RECORDING = "recording"


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

    workspace_id: Mapped["UUID"] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )


class PointCloud(BaseModel):
    """
    Represents a point cloud file in the system. 
    Point clouds can be of different types (plan, scan, recording)
    and can be associated with a stage.
    """
    __tablename__ = "point_clouds"

    stage_id: Mapped["UUID"] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=True
    )
    stage: Mapped["Stage"] = relationship(
        back_populates="point_cloud")

    converted_files: Mapped[list["PointCloudConverted"]] = relationship(
        back_populates="point_cloud",
        cascade="all, delete-orphan"
    )

    type: Mapped[PointCloudType] = mapped_column(
        Enum(PointCloudType, name="point_cloud_types", create_constraint=True),
        nullable=False,
        default=PointCloudType.SCAN
    )

    file_id: Mapped["UUID"] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    file: Mapped["File"] = relationship(
        cascade="all, delete",
        passive_deletes=True,
        lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "(type = 'scan' AND stage_id IS NOT NULL) OR "
            "(type = 'plan' AND stage_id IS NULL) OR "
            "(type = 'recording' AND stage_id IS NULL)",
            name="ck_point_cloud_kind_stage"
        ),
    )


class PointCloudConverted(BaseModel):
    """
    Converted point cloud files that are associated with a point cloud. 
    These files are generated from the original point cloud 
    file and can be used for visualization.
    """
    __tablename__ = "point_cloud_converted"

    point_cloud_id: Mapped["UUID"] = mapped_column(
        ForeignKey("point_clouds.id", ondelete="CASCADE")
    )
    file_id: Mapped["UUID"] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE")
    )
    point_cloud: Mapped["PointCloud"] = relationship(
        back_populates="converted_files")
    file: Mapped["File"] = relationship(
        cascade="all, delete"
    )


class BIM(BaseModel):
    """
    Building Information Model (BIM) file associated with a project.
    """
    __tablename__ = "bims"

    project_id: Mapped["UUID"] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="bim")

    point_cloud_id: Mapped["UUID"] = mapped_column(
        ForeignKey("point_clouds.id", ondelete="SET NULL"),
        nullable=True,
        unique=True
    )
    point_cloud: Mapped[Optional["PointCloud"]] = relationship()

    file_id: Mapped["UUID"] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    file: Mapped["File"] = relationship(
        cascade="all, delete",
        passive_deletes=True
    )


class ResultPhoto(BaseModel):
    """
    Photos of a recording result (e.g. photo of the actual progress).
    """
    __tablename__ = "result_photos"

    result_id: Mapped["UUID"] = mapped_column(
        ForeignKey("recording_results.id", ondelete="CASCADE"),
        primary_key=True
    )
    result: Mapped["RecordingResult"] = relationship(back_populates="photos")

    file_id: Mapped["UUID"] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True
    )
    file: Mapped["File"] = relationship(lazy="selectin")

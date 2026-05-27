import uuid
from typing import Optional
from enum import StrEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, ForeignKey, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel


class FileStatus(StrEnum):
    """
    Statuses of files in the system.

    - Pending files are not confirmed or not uploaded yet
    - Uploaded files are ready to be used
    """
    UPLOADED = "uploaded"
    PENDING = "pending"


class PointCloudType(StrEnum):
    """
    Types of point clouds in the system.

    - Plan type is for point clouds that represent project's BIM (e.g. converted)
    - Scan type is for real scans of a project, actual scanning
    """
    PLAN = "plan"
    SCAN = "scan"


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
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=True
    )
    stage: Mapped["Stage"] = relationship(
        back_populates="point_clouds")

    converted_files: Mapped[list["PointCloudConverted"]] = relationship(
        back_populates="point_cloud",
        cascade="all, delete-orphan"
    )

    type: Mapped[PointCloudType] = mapped_column(
        Enum(PointCloudType, name="point_cloud_types", create_constraint=True),
        nullable=False,
        default=PointCloudType.SCAN
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

    __table_args__ = (
        CheckConstraint(
            "(type = 'scan' AND stage_id IS NOT NULL) OR "
            "(type = 'plan' AND stage_id IS NULL)",
            name="ck_point_cloud_kind_stage"
        ),
    )


class PointCloudConverted(BaseModel):
    __tablename__ = "point_cloud_converted"

    point_cloud_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("point_clouds.id", ondelete="CASCADE")
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE")
    )
    point_cloud: Mapped["PointCloud"] = relationship(
        back_populates="converted_files")
    file: Mapped["File"] = relationship(
        cascade="all, delete"
    )


class BIM(BaseModel):
    __tablename__ = "bims"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="bim")

    point_cloud_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("point_clouds.id", ondelete="SET NULL"),
        nullable=True,
        unique=True
    )
    point_cloud: Mapped[Optional["PointCloud"]] = relationship()

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    file: Mapped["File"] = relationship(
        cascade="all, delete",
        passive_deletes=True
    )


class RecordingResultType(StrEnum):
    """
    Types of results in the system.

    - Progress type is for comparing two different real scans results
    - Plan fact type is for comparing a real scan and a project
    """
    PROGRESS = "progress"
    PLAN_FACT = "plan_fact"


class RecordingResult(BaseModel):
    __tablename__ = "recording_results"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(
        passive_deletes=True
    )

    data = Column(JSONB)

    pdf_report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=True,
        unique=True
    )
    pdf_report: Mapped["File"] = relationship(
        cascade="all, delete",
        passive_deletes=True
    )

    xlsx_report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=True,
        unique=True
    )
    xlsx_report: Mapped["File"] = relationship(
        cascade="all, delete",
        passive_deletes=True
    )

    photos_links: Mapped[list["ResultPhoto"]] = relationship(
        back_populates="result",
    )

    type: Mapped[PointCloudType] = mapped_column(
        Enum(RecordingResultType, name="recording_result_types",
             create_constraint=True),
        nullable=False
    )


class ResultPhoto(BaseModel):
    """Photos of a recording result (e.g. photo of the actual progress)."""
    __tablename__ = "result_photos"

    result_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recording_results.id", ondelete="CASCADE"),
        primary_key=True
    )
    result: Mapped["RecordingResult"] = relationship(back_populates="photos")

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True
    )
    file: Mapped["File"] = relationship(lazy="selectin")

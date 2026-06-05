from uuid import UUID
from typing import Optional
from enum import StrEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel


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

    project_id: Mapped["UUID"] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(
        passive_deletes=True
    )

    data = Column(JSONB)

    pdf_report_id: Mapped["UUID"] = mapped_column(
<<<<<<< HEAD
        ForeignKey("files.id", ondelete="CASCADE"),
=======
        ForeignKey("files.id"),
>>>>>>> backend
        nullable=True,
        unique=True
    )
    pdf_report: Mapped["File"] = relationship(
        foreign_keys=[pdf_report_id],
        cascade="all, delete",
<<<<<<< HEAD
        passive_deletes=True
    )

    xlsx_report_id: Mapped["UUID"] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
=======
        passive_deletes=True,
        lazy="selectin"
    )

    xlsx_report_id: Mapped["UUID"] = mapped_column(
        ForeignKey("files.id"),
>>>>>>> backend
        nullable=True,
        unique=True
    )
    xlsx_report: Mapped["File"] = relationship(
        foreign_keys=[xlsx_report_id],
        cascade="all, delete",
        passive_deletes=True,
<<<<<<< HEAD
=======
        lazy="selectin"
>>>>>>> backend
    )

    point_cloud_id: Mapped["UUID"] = mapped_column(
        ForeignKey("point_clouds.id", ondelete="SET NULL"),
<<<<<<< HEAD
        nullable=True,
        unique=True
    )
    point_cloud: Mapped[Optional["PointCloud"]] = relationship()

    photos: Mapped[list["ResultPhoto"]] = relationship(
        back_populates="result",
=======
        unique=True
    )
    point_cloud: Mapped["PointCloud"] = relationship(
        cascade="all, delete"
    )

    photos: Mapped[list["ResultPhoto"]] = relationship(
        back_populates="result",
        cascade="all, delete"
>>>>>>> backend
    )

    type: Mapped["RecordingResultType"] = mapped_column(
        Enum(RecordingResultType, name="recording_result_types",
             create_constraint=True),
        nullable=False
    )

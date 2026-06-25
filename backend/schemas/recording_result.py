from uuid import UUID
from pydantic import BaseModel
from models.recording_result import RecordingResultType
from .base import Response


class RecordingResultModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    project_id: UUID
    data: dict
    pdf_report_id: UUID | None = None
    xlsx_report_id: UUID | None = None
    point_cloud_id: UUID | None = None
    type: RecordingResultType


class RecordingResultResponse(Response):
    """API response schema."""
    project_id: UUID
    data: dict
    pdf_report_id: UUID | None = None
    xlsx_report_id: UUID | None = None
    point_cloud_id: UUID | None = None
    type: RecordingResultType

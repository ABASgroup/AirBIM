from uuid import UUID
from pydantic import BaseModel
from models.recording_result import RecordingResultType
<<<<<<< HEAD
from .file import FileResponse
=======
>>>>>>> backend
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
<<<<<<< HEAD
    pdf_report: FileResponse | None = None
    xlsx_report: FileResponse | None = None
    photos: list[FileResponse] | None = None
    point_cloud_id: UUID | None = None
    type: FileResponse
=======
    pdf_report_id: UUID | None = None
    xlsx_report_id: UUID | None = None
    point_cloud_id: UUID | None = None
    type: RecordingResultType
>>>>>>> backend

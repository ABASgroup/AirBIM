from uuid import UUID
from pydantic import BaseModel
from models.file import FileStatus, PointCloudType
from .base import Response


class FileDataRequest(BaseModel):
    filename: str
    content_type: str
    size: int


class FileModel(BaseModel):
    """Schema in DB. Use to create in db."""
    workspace_id: UUID
    filename: str
    key: str
    content_type: str
    size: int
    status: FileStatus = FileStatus.PENDING


class FileResponse(Response):
    """
    API response schema. 

    Use as a mixin for other file responses.
    """
    workspace_id: UUID
    filename: str
    content_type: str
    size: int
    key: str
    status: FileStatus


class FileLinkResponse(BaseModel):
    """
    API response schema.

    Universal response for any file presigned URL.
    """
    url: str
    file: FileResponse


class FileUpdate(BaseModel):
    """Update schema. Use to update in DB."""
    filename: str | None = None
    key: str | None = None
    content_type: str | None = None
    size: int | None = None
    status: FileStatus | None = None


class PointCloudModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    stage_id: UUID | None = None
    file_id: UUID
    type: PointCloudType = PointCloudType.SCAN


class PointCloudResponse(Response):
    """API response schema."""
    stage_id: UUID
    file: FileResponse


class PointCloudConvertedModel(BaseModel):
    """Schema in DB. Use to create in db."""
    point_cloud_id: UUID
    file_id: UUID


class BIMModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    project_id: UUID
    file_id: UUID


class BIMResponse(Response):
    """API response schema."""
    project_id: UUID
    file: FileResponse
    point_cloud_id: UUID | None = None

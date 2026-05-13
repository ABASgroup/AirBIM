import uuid
from pydantic import BaseModel
from models.file import FileStatus
from .base import Response


class FileDataRequest(BaseModel):
    filename: str
    content_type: str
    size: int


# file schemas
class FileResponse(Response):
    """
    API response schema. 

    Use as a mixin for other file responses.
    """
    filename: str
    content_type: str
    size: int
    key: str
    status: FileStatus


class FileLinkResponse(FileResponse):
    """
    API response schema.

    Universal response for any file presigned URL.
    """
    url: str


class FileModel(BaseModel):
    """Schema in DB. Use to create in db."""
    filename: str
    key: str
    content_type: str
    size: int
    status: FileStatus = FileStatus.PENDING


class FileUpdate(BaseModel):
    """Update schema. Use to update in DB."""
    filename: str | None = None
    key: str | None = None
    content_type: str | None = None
    size: int | None = None
    status: FileStatus | None = None


# schemas for point clouds
class PointCloudModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    stage_id: uuid.UUID
    file_id: uuid.UUID


class PointCloudResponse(Response):
    """API response schema."""
    stage_id: uuid.UUID
    file: FileResponse


class PointCloudConvertedModel(BaseModel):
    """Schema in DB. Use to create in db."""
    point_cloud_id: uuid.UUID
    file_id: uuid.UUID

# schemas for bims


class BIMModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    project_id: uuid.UUID
    file_id: uuid.UUID


class BIMResponse(Response):
    """API response schema."""
    project_id: uuid.UUID
    file: FileResponse

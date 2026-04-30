import uuid
from pydantic import BaseModel
from models.file import FileStatus
from .base import Response


# link schemas
class FileDataRequest(BaseModel):
    filename: str
    content_type: str
    size: int


class FileLinkResponse(BaseModel):
    """
    API response schema.

    Universal response for any file presigned URL.
    """
    key: str
    filename: str
    url: str
    size: int
    content_type: str


# file schemas
class FileResponse(Response):
    """
    API response schema. 

    Use as a mixin for other file responses.
    """
    filename: str
    content_type: str
    size: int
    status: FileStatus


class FileModel(BaseModel):
    """Schema in DB. Use to create in db."""
    filename: str
    key: str
    content_type: str
    size: int
    status: FileStatus = FileStatus.PENDING


# schemas for point clouds
class PointCloudModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    stage_id: uuid.UUID
    file_id: uuid.UUID


class PointCloudResponse(Response):
    """API response schema."""
    stage_id: uuid.UUID
    file: FileResponse


# schemas for bims
class BIMModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    project_id: uuid.UUID
    file_id: uuid.UUID


class BIMResponse(Response):
    """API response schema."""
    project_id: uuid.UUID
    file: FileResponse

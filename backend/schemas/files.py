import uuid
from datetime import datetime
from pydantic import BaseModel
from models.files import FileStatus
from .base import Response


# link schemas
class FileUploadLinkRequest(BaseModel):
    filename: str
    content_type: str
    size: int


class FileUploadConfirmRequest(BaseModel):
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
    created_at: datetime
    updated_at: datetime


class FileModel(BaseModel):
    """Schema in DB. Use as a mixin."""
    filename: str
    key: str
    content_type: str
    size: int
    status: FileStatus = FileStatus.PENDING


# schemas for point clouds
class PointCloudFileModel(FileModel):
    """Schema in DB. Use to create in DB."""
    stage_id: uuid.UUID


class PointCloudFileResponse(FileResponse):
    """API response schema."""
    stage_id: uuid.UUID


# schemas for bims
class BIMFileModel(FileModel):
    """Schema in DB. Use to create in DB."""
    project_id: uuid.UUID


class BIMFileResponse(FileResponse):
    """API response schema."""
    project_id: uuid.UUID

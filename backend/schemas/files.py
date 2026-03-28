from pydantic import BaseModel
from datetime import datetime
from models.files import FileStatus


# universal request schemas
class FileUploadLinkRequest(BaseModel):
    filename: str
    content_type: str
    size: int


class FileUploadConfirmRequest(BaseModel):
    filename: str
    content_type: str
    size: int


class FileLinkPublic(BaseModel):
    """API response schema."""
    key: str
    filename: str
    url: str
    size: int
    content_type: str


class FilePublic(BaseModel):
    """API response schema. Use as a mixin."""
    id: int
    filename: str
    content_type: str
    size: int
    status: FileStatus
    created_at: datetime


class FileCreate(BaseModel):
    """Create in DB schema. Use as a mixin."""
    filename: str
    key: str
    content_type: str
    size: int
    status: FileStatus = FileStatus.PENDING


# schemas for point clouds
class PointCloudFileCreate(FileCreate):
    """Create in DB schema."""
    stage_id: int


class PointCloudFilePublic(FilePublic):
    """API response schema."""
    stage_id: int

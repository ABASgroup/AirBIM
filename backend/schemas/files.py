from pydantic import BaseModel, model_validator


class FileUploadRequest(BaseModel):
    filename: str
    size: int


class FileDeleteRequest(BaseModel):
    filename: str


class FileLinkPublic(BaseModel):
    """API Response schema"""
    project_id: int
    presigned_url: str
    filename: str


class PointCloudCreate(BaseModel):
    """Create in DB schema"""
    project_id: int
    path: str
    extension: str
    size: int
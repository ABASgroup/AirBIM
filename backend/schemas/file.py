from uuid import UUID
from pydantic import BaseModel
from models.file import FileStatus, PointCloudType
from .base import Response
from .task import TaskResponse


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


class FileTaskResponse(BaseModel):
    """API response schema."""
    file: FileResponse
    task: TaskResponse


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
    type: PointCloudType


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
    preview_file_id: UUID | None = None


class PointCloudBounds(BaseModel):
    """Min/max XYZ of a LAS/LAZ file."""
    min_xyz: tuple[float, float, float]
    max_xyz: tuple[float, float, float]


class FilePointCloudConfirmResponse(BaseModel):
    """Confirm upload response for a stage scan point cloud."""
    file: FileResponse
    point_cloud_id: UUID
    bounds: PointCloudBounds


class RawScanCleanRequest(BaseModel):
    """
    Parameters for clean_raw_scan / RawScanPipelineConfig.

    All fields optional; omitted values use package defaults on the worker.
    """
    deduplicate_cell_m: float | None = 0.001
    poisson_sample_radius_m: float | None = None
    statistical_outlier: bool = True
    outlier_mean_k: int = 16
    outlier_multiplier: float = 2.5
    radius_outlier_radius_m: float | None = None
    radius_outlier_min_k: int = 4
    z_mad_k: float | None = None
    crop_min_xyz: tuple[float | None, float | None, float | None] | None = None
    crop_max_xyz: tuple[float | None, float | None, float | None] | None = None
    noise_class: int = 1
    compress_output: bool | None = None

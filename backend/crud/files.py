from .base import BaseCRUD
from models.files import File, BimFile, PointCloudFile


class FileCRUD(BaseCRUD[File]):
    """DAO class for CRUD operations with File model."""
    _model = File


class BimFileCRUD(BaseCRUD[BimFile]):
    """DAO class for CRUD operations with BimFile model."""
    _model = BimFile


class PointCloudFileCRUD(BaseCRUD[PointCloudFile]):
    """DAO class for CRUD operations with PointCloudFile model."""
    _model = PointCloudFile

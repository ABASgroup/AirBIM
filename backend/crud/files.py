from .base import BaseCRUD
from models.files import BimFile, PointCloudFile


class BimFileCRUD(BaseCRUD[BimFile]):
    """DAO class for CRUD operations with BimFile model."""
    _model = BimFile


class PointCloudFileCRUD(BaseCRUD[PointCloudFile]):
    """DAO class for CRUD operations with PointCloudFile model."""
    _model = PointCloudFile
